"""2단계: d2 체크포인트를 오프라인으로 돌려 '큐브 위치 → 예측 방향' 이 조건화되는지 본다 (로봇·카메라 연결 없음).

근거: 학습 원격조종에서 팔이 움직이기 시작한 뒤 50 프레임(1.67 s, chunk 하나) 안에 pan 이 파지 때 값의 중앙 99% 까지 간다
      (grasp_table 확인, r = 0.996). 그래서 '움직이기 시작한 프레임 m' 관측으로 예측한 chunk 의 마지막 pan(index 49) 을
      정책이 고른 파지 방향으로 쓴다.

프로브 (결과는 probe_<이름>.csv):
  start     학습 256편: 그 판 m 프레임 관측 그대로 → 예측 pan vs 그 판 실제 파지 pan
  swap      T1 128편 안에서 무작위 짝 (A, B): state = A, 영상 = B (둘 다 / front 만 / wrist 만) → 예측 pan 을
            B 파지 pan · A 파지 pan 에 회귀 (영상을 따르는지, state 로 판을 기억해 따르는지)
  grid      합성: T1 m 프레임 front 중앙값(큐브 없는 배경) + 가장 가까운 학습 큐브 조각을 격자 위치에 붙임,
            wrist = 큐브 안 보이는 T1 판 wrist 중앙값, state = T1 m 프레임 state 중앙값 → 예측 pan vs 그 위치의 기대 pan
  pregrasp  학습 256편: 첫 파지 30 프레임 전 관측 그대로 → chunk index 30 관절 vs 실제 파지 관절 (Known/Random 마지막 맞춤 정확도, 학습 안 표본)
  eval      실물 평가 롤아웃 판의 m 프레임 관측 그대로 → 예측 pan vs 큐브 기대 pan, 실제 롤아웃 파지 pan
사용: PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python policy_probe.py [--probes start,swap,grid,pregrasp,eval] [--seeds 3] [--steps 5]
"""
import argparse
import json
import math
import time

import numpy as np
import pandas as pd

import common as C

CKPT = C.D2 / "train/32_20000/pi05_expert_bs32_20k/checkpoints/020000/pretrained_model"
TASK = "pick up the red cube and put it in the brown box"
IDX = 49  # chunk 마지막


def move_start(a, thr=2.0):
    mv = np.where(np.abs(a[:, :5] - a[0, :5]).max(1) > thr)[0]
    return int(mv[0]) if len(mv) else 0


class Probe:
    def __init__(self, steps, seeds):
        import torch
        from lerobot.policies.factory import make_pre_post_processors
        from lerobot.policies.pi05.modeling_pi05 import PI05Policy
        self.torch = torch
        self.policy = PI05Policy.from_pretrained(str(CKPT)).to("cuda").eval()
        self.policy.config.num_inference_steps = steps
        self.pre, self.post = make_pre_post_processors(self.policy.config, pretrained_path=str(CKPT),
                                                       preprocessor_overrides={"device_processor": {"device": "cuda"}})
        self.seeds = seeds

    def predict(self, front, wrist, state):
        """front/wrist (N,H,W,3) uint8, state (N,6) → chunk (seeds, N, 50, 6) 도(°)."""
        torch = self.torch
        outs = []
        for sd in range(self.seeds):
            torch.manual_seed(1000 + sd)
            batch = {
                "observation.images.front": torch.from_numpy(np.ascontiguousarray(front)).cuda().float().div(255).permute(0, 3, 1, 2),
                "observation.images.wrist": torch.from_numpy(np.ascontiguousarray(wrist)).cuda().float().div(255).permute(0, 3, 1, 2),
                "observation.state": torch.from_numpy(np.asarray(state, np.float32)).cuda(),
                "task": [TASK] * len(state),
            }
            with torch.inference_mode():
                b = self.pre(batch)
                act = self.policy.predict_action_chunk(b)
                act = self.post(act)
            outs.append(act.float().cpu().numpy())
        return np.stack(outs)

    def run(self, front, wrist, state, bs=8):
        res = []
        for i in range(0, len(state), bs):
            res.append(self.predict(front[i:i + bs], wrist[i:i + bs], state[i:i + bs]))
        return np.concatenate(res, axis=1)


def load_obs(ds, eps_frames, cache):
    F, W = [], []
    for e, f in eps_frames:
        F.append(C.frames(ds, e, "front", f, f, cache)[0])
        W.append(C.frames(ds, e, "wrist", f, f, cache)[0])
    return np.stack(F), np.stack(W)


def summarize(chunks):
    """(seeds,N,50,6) → pan index 49 평균·표준편차, 그리퍼."""
    pan = chunks[:, :, IDX, 0]
    return pan.mean(0), pan.std(0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probes", default="start,swap,grid,pregrasp,eval")
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--steps", type=int, default=5)
    ap.add_argument("--grid_step", type=float, default=3.0)
    args = ap.parse_args()
    probes = args.probes.split(",")
    cache = {}
    T = pd.read_csv(C.OUT / "grasp_train.csv")
    data = C.load_parquet(C.D2 / "dataset")
    m = {e: move_start(data[e][1]) for e in data}
    t0 = time.time()
    P = Probe(args.steps, args.seeds)
    print(f"model loaded {time.time() - t0:.0f}s", flush=True)
    meta = dict(ckpt=str(CKPT), steps=args.steps, seeds=args.seeds, idx=IDX)

    if "start" in probes:
        eps = list(range(256))
        F, W = load_obs(C.D2 / "dataset", [(e, m[e]) for e in eps], cache)
        S = np.stack([data[e][0][m[e]] for e in eps])
        ch = P.run(F, W, S)
        mu, sd = summarize(ch)
        df = T[["ep", "group", "K", "cube_x", "cube_y", "bearing", "range_cm", "pan_exp", "s_shoulder_pan"]].copy()
        df["m"] = [m[e] for e in eps]
        df["pred_pan"], df["pred_pan_sd"] = mu, sd
        df["pred_minus_human"] = df.pred_pan - df.s_shoulder_pan
        df["pred_minus_exp"] = df.pred_pan - df.pan_exp
        df.to_csv(C.OUT / "probe_start.csv", index=False)
        np.save(C.OUT / "probe_start_chunks.npy", ch.astype(np.float32))
        print("start done", time.time() - t0, flush=True)

    if "swap" in probes:
        rng = np.random.default_rng(7)
        t1 = [e for e in range(256) if T.loc[e, "task"] == "T1"]
        A = rng.permutation(t1)
        B = rng.permutation(t1)
        keep = [(a, b) for a, b in zip(A, B) if abs(T.loc[a, "s_shoulder_pan"] - T.loc[b, "s_shoulder_pan"]) > 15]
        FA, WA = load_obs(C.D2 / "dataset", [(a, m[a]) for a, _ in keep], cache)
        FB, WB = load_obs(C.D2 / "dataset", [(b, m[b]) for _, b in keep], cache)
        SA = np.stack([data[a][0][m[a]] for a, _ in keep])
        rows = []
        for mode, (Fx, Wx) in {"both": (FB, WB), "front_only": (FB, WA), "wrist_only": (FA, WB), "none": (FA, WA)}.items():
            mu, sd = summarize(P.run(Fx, Wx, SA))
            for i, (a, b) in enumerate(keep):
                rows.append(dict(mode=mode, A=a, B=b, pan_A=T.loc[a, "s_shoulder_pan"], pan_B=T.loc[b, "s_shoulder_pan"],
                                 group_A=T.loc[a, "group"], group_B=T.loc[b, "group"], pred_pan=mu[i], pred_pan_sd=sd[i]))
            print("swap", mode, time.time() - t0, flush=True)
        pd.DataFrame(rows).to_csv(C.OUT / "probe_swap.csv", index=False)

    if "grid" in probes:
        import cv2
        t1 = [e for e in range(256) if T.loc[e, "task"] == "T1"]
        F1, W1 = load_obs(C.D2 / "dataset", [(e, m[e]) for e in t1], cache)
        bg = np.median(F1, axis=0).astype(np.uint8)
        novis = [i for i, e in enumerate(t1) if not C.blobs(C.red_mask(W1[i]), 60)]
        wbg = np.median(W1[novis], axis=0).astype(np.uint8)
        S0 = np.median(np.stack([data[e][0][m[e]] for e in t1]), axis=0)
        # 큐브 조각: 학습 T1 판 front m 프레임의 빨강 덩어리 (그림자 포함하려고 6 px 넓힘)
        patches = []
        for i, e in enumerate(t1):
            mk = C.red_mask(F1[i])
            b = C.blobs(mk, 80)
            if not b:
                continue
            a, (u, v), li, lab = max(b, key=lambda t: t[0])
            blob = (lab == li).astype(np.uint8)
            blob = cv2.dilate(blob, np.ones((7, 7), np.uint8))
            ys, xs = np.nonzero(blob)
            patches.append(dict(x=T.loc[e, "cube_x"], y=T.loc[e, "cube_y"], u=u, v=v, ys=ys - int(round(v)), xs=xs - int(round(u)),
                                pix=F1[i][ys, xs]))
        # 격자: 학습 큐브 위치의 볼록 껍질 안 + 2 cm, grid_step 간격
        pts = np.array([[p["x"], p["y"]] for p in patches])
        hull = cv2.convexHull(pts.astype(np.float32))
        xs = np.arange(np.floor(pts[:, 0].min()) - 1, pts[:, 0].max() + 1.01, args.grid_step)
        ys = np.arange(np.floor(pts[:, 1].min()) - 1, pts[:, 1].max() + 1.01, args.grid_step)
        grid = [(x, y) for x in xs for y in ys if cv2.pointPolygonTest(hull, (float(x), float(y)), True) >= -2.0]
        Fg = []
        info = []
        for x, y in grid:
            k = int(np.argmin(np.hypot(pts[:, 0] - x, pts[:, 1] - y)))
            p = patches[k]
            u, v = C.cm_to_px(x, y)
            img = bg.copy()
            yy, xx = p["ys"] + int(round(v)), p["xs"] + int(round(u))
            ok = (yy >= 0) & (yy < img.shape[0]) & (xx >= 0) & (xx < img.shape[1])
            img[yy[ok], xx[ok]] = p["pix"][ok]
            Fg.append(img)
            info.append(dict(x=x, y=y, patch_from_cm=float(np.hypot(p["x"] - x, p["y"] - y))))
        Fg = np.stack(Fg)
        cv2.imwrite(str(C.OUT / "probe_grid_bg.jpg"), cv2.cvtColor(np.hstack([bg, Fg[len(Fg) // 2]]), cv2.COLOR_RGB2BGR))
        ch = P.run(Fg, np.repeat(wbg[None], len(Fg), 0), np.repeat(S0[None], len(Fg), 0))
        mu, sd = summarize(ch)
        known = C.load_known()
        rows = []
        for i, d in enumerate(info):
            x, y = d["x"], d["y"]
            dk = {k: math.hypot(x - v[0], y - v[1]) for k, v in known.items()}
            nk = min(dk, key=dk.get)
            dtr = float(np.min(np.hypot(T.cube_x - x, T.cube_y - y)))
            rows.append(dict(d, bearing=C.bearing(x, y), range_cm=C.rng(x, y), pan_exp=C.pan_expected(x, y),
                             pred_pan=mu[i], pred_pan_sd=sd[i], nearest_K=nk, nearest_K_cm=dk[nk],
                             K_pan_exp=C.pan_expected(*known[nk]), nearest_train_cm=dtr))
        g = pd.DataFrame(rows)
        g["pred_minus_exp"] = g.pred_pan - g.pan_exp
        g.to_csv(C.OUT / "probe_grid.csv", index=False)
        print("grid done", len(g), time.time() - t0, flush=True)

    if "pregrasp" in probes:
        # 학습 256편: 첫 파지 30 프레임(1 s) 전 관측 그대로 → chunk index 30 의 관절 vs 실제 파지 순간 관절, 그리퍼 닫힘 시점
        L = 30
        eps = list(range(256))
        fr = {e: max(0, int(T.loc[e, "grasp_f"]) - L) for e in eps}
        F, W = load_obs(C.D2 / "dataset", [(e, fr[e]) for e in eps], cache)
        S = np.stack([data[e][0][fr[e]] for e in eps])
        ch = P.run(F, W, S)
        mean = ch.mean(0)
        df = T[["ep", "group", "K", "cube_x", "cube_y", "pan_exp"]].copy()
        for i, j in enumerate(C.JOINTS):
            df[f"pred_{j}"] = mean[:, L, i]
            df[f"human_{j}"] = [data[e][0][int(T.loc[e, "grasp_f"]), i] for e in eps]
            df[f"err_{j}"] = df[f"pred_{j}"] - df[f"human_{j}"]
        df["pred_pan_sd"] = ch[:, :, L, 0].std(0)
        # 예측 그리퍼가 처음으로 '열린 값 − 35% 폭' 아래로 내려가는 chunk index (없으면 NaN)
        g = mean[:, :, 5]
        thr = g[:, :1] - 0.35 * np.maximum(1.0, g.max(1, keepdims=True) - g.min(1, keepdims=True))
        hit = g < thr
        df["pred_close_idx"] = np.where(hit.any(1), hit.argmax(1), np.nan)
        df.to_csv(C.OUT / "probe_pregrasp.csv", index=False)
        print("pregrasp done", time.time() - t0, flush=True)

    if "eval" in probes:
        rows = []
        E = pd.read_csv(C.OUT / "grasp_eval.csv")
        for ds in sorted((C.D2 / "eval/rollouts").glob("*/dataset")):
            ed = C.load_parquet(ds)
            for e, (s, a) in ed.items():
                me = move_start(a)
                F, W = load_obs(ds, [(e, me), (e, 0)], cache)
                S = np.stack([s[me], s[0]])
                mu, sd = summarize(P.run(F, W, S))
                ev = E[(E.run == ds.parent.name) & (E.ep == e)]
                x, y = ev.start_x.iloc[0], ev.start_y.iloc[0]
                pan_traj = a[:, 0]
                for tag, j in (("m", 0), ("f0", 1)):
                    rows.append(dict(run=ds.parent.name, ep=e, obs=tag, frame=me if tag == "m" else 0, cube_x=x, cube_y=y,
                                     pan_exp=C.pan_expected(x, y), pred_pan=mu[j], pred_pan_sd=sd[j],
                                     rollout_pan_at_obs_plus50=pan_traj[min(len(a) - 1, (me if tag == "m" else 0) + 50)],
                                     rollout_first_close_pan=ev.s_shoulder_pan.iloc[0], first_close_t=ev.t.iloc[0]))
        pd.DataFrame(rows).to_csv(C.OUT / "probe_eval.csv", index=False)
        print("eval done", time.time() - t0, flush=True)
    json.dump(meta, open(C.OUT / "probe_meta.json", "w"), indent=1)


if __name__ == "__main__":
    main()
