"""오프라인 평가 (GPU, 로봇 · 카메라 연결 없음, 읽기만): 체크포인트 하나 → eval/<run>_<step>/.

단계 (모델은 한 번만 적재, ab_core.Engine — 고정 noise 은행 seed 1234, denoise 5 step):
  o3  칸 등급 · 구간별 in-sample flow loss (고정 seed, 같은 프레임 · 같은 batch 순서)          → o3_loss.csv
  o1  초기 접근: 학습 256 판 움직임 시작 관측 → chunk pan, 닫힘 1 s 전 관측 → chunk pan,
      front 합성 격자 (학습 큐브 볼록 껍질 1.5 cm 격자 + U1–U8) 시작 관측 → chunk pan               → o1.npz, o1_points.csv
  g1  roll 요인 실험 (action_bottleneck/g1_roll_factorial.py 그대로, T1 128 판 × 닫힘 2.5 · 1.5 · 1.0 s) + a1_g1_analyze.py → g1/, a1_g1*.{json,csv}
  g2  F1 프레임 (학습 probe 7,810 · d2 평가 롤아웃 558) 정책 chunk (g2_policy_frames.py 그대로) + S1 · S6 기울기   → g2/, s1s6.json
기존 스크립트 · d2 데이터 · 체크포인트는 수정하지 않는다 (모듈을 import 해 Engine 과 출력 폴더만 바꿔 끼움).
H (heldout) 는 아직 없음 → O1-H · O2-H 는 이 스크립트에 없다 (H 녹화 뒤 따로).
사용: PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python eval_run.py --run A0_s2001 --step 004000 [--stages o3,o1,g1,g2]
      --run d2 이면 d2 020000.
"""
import argparse
import gc
import importlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

SA = Path(__file__).resolve().parent
D2 = SA.parent
sys.path.insert(0, str(D2 / "action_bottleneck"))
sys.path.insert(0, str(D2 / "diag_grasp_bias"))
sys.path.insert(0, str(SA))
import ab_core as A  # noqa: E402
import common as C  # noqa: E402
import train_weighted as TW  # noqa: E402

D2_CKROOT = D2 / "train/32_20000/pi05_expert_bs32_20k/checkpoints"
FPS = 30
O3_SEEDS = (11, 12, 13, 14)
O3_BS = 16


def ck_root(run):
    return D2_CKROOT if run == "d2" else SA / "runs" / run / "checkpoints"


# ---------------- o3 ----------------
def o3_frames():
    """고정 프레임 목록 (처음 한 번 만들고 eval/o3_frames.csv 로 고정). 학습 데이터 = d2 (in-sample)."""
    p = SA / "eval/o3_frames.csv"
    if p.exists():
        return pd.read_csv(p)
    import glob
    F = pd.read_parquet(SA / "s1_frames.parquet")
    idx = pd.concat([pd.read_parquet(f, columns=["index", "episode_index", "frame_index"])
                     for f in sorted(glob.glob(str(D2 / "dataset/data/*/*.parquet")))])
    F = F.merge(idx, left_on=["ep", "frame"], right_on=["episode_index", "frame_index"])
    F["tier"] = np.select([F.n_cell >= 15, F.n_cell >= 5, F.n_cell >= 1, F.phase == "정렬"],
                          ["보통", "얇음", "희소", "정렬_칸없음"], F.phase)
    rng = np.random.default_rng(0)
    want = {"희소": 10 ** 6, "얇음": 300, "보통": 300, "정렬_칸없음": 200, "접근": 300, "닫힘 뒤": 300, "정지": 100}
    out = []
    for t, n in want.items():
        d = F[F.tier == t]
        if t == "희소":
            d = d.iloc[::2]                                  # 이웃 프레임 거의 같음 → 하나 건너
        elif len(d) > n:
            d = d.iloc[np.sort(rng.choice(len(d), n, replace=False))]
        out.append(d)
    S = pd.concat(out)[["index", "ep", "frame", "tier", "phase", "mode", "n_cell", "w_A0", "w_A1", "w_A2", "w_A2r"]]
    S = S.sample(frac=1, random_state=0).reset_index(drop=True)          # batch 마다 등급 섞기 (모든 체크포인트 같은 순서)
    p.parent.mkdir(exist_ok=True)
    S.to_csv(p, index=False)
    return S


def stage_o3(E, out, limit=None):
    import torch
    from lerobot.datasets.lerobot_dataset import LeRobotDataset
    from torch.utils.data import default_collate
    S = o3_frames()
    if limit:
        S = S.iloc[:limit]
    ds = LeRobotDataset("oxr/so101_k8_d2", root=str(D2 / "dataset"),
                        delta_timestamps={"action": [i / FPS for i in range(E.policy.config.chunk_size)]})
    pol = E.policy
    loss = np.zeros((len(S), len(O3_SEEDS)), np.float32)
    t0 = time.time()
    for b0 in range(0, len(S), O3_BS):
        items = [ds[int(i)] for i in S["index"].values[b0:b0 + O3_BS]]
        batch = default_collate(items)
        with torch.inference_mode():
            b = E.pre(batch)
            for k, s in enumerate(O3_SEEDS):
                torch.manual_seed(s * 100003 + b0)
                l, _ = pol.forward(b, reduction="none")
                loss[b0:b0 + len(items), k] = l.float().cpu().numpy()
        if b0 // O3_BS % 20 == 0:
            print(f"[o3] {b0 + len(items)}/{len(S)} {time.time() - t0:.0f}s", flush=True)
    S = S.assign(**{f"loss_s{s}": loss[:, k] for k, s in enumerate(O3_SEEDS)}, loss=loss.mean(1))
    S.to_csv(out / "o3_loss.csv", index=False)
    return dict(n=len(S), s=time.time() - t0, by_tier=S.groupby("tier").loss.mean().round(5).to_dict())


# ---------------- o1 ----------------
def build_points(T, F1, W1, S1, step_cm=1.5, extra=()):
    """diag probe_core.build_grid 와 같은 합성 (큐브 없는 front 중앙값 + 가장 가까운 학습 큐브 조각), 격자 간격 · 추가 점만 다름."""
    import cv2
    bg = np.median(F1, axis=0).astype(np.uint8)
    novis = [i for i in range(len(W1)) if not C.blobs(C.red_mask(W1[i]), 60)]
    wbg = np.median(W1[novis], axis=0).astype(np.uint8)
    S0 = np.median(S1, axis=0)
    patches = []
    for i in range(len(F1)):
        b = C.blobs(C.red_mask(F1[i]), 80)
        if not b:
            continue
        a, (u, v), li, lab = max(b, key=lambda t: t[0])
        blob = cv2.dilate((lab == li).astype(np.uint8), np.ones((7, 7), np.uint8))
        ys, xs = np.nonzero(blob)
        patches.append(dict(x=T["cube_x"][i], y=T["cube_y"][i], ys=ys - int(round(v)), xs=xs - int(round(u)), pix=F1[i][ys, xs]))
    pts = np.array([[p["x"], p["y"]] for p in patches])
    hull = cv2.convexHull(pts.astype(np.float32))
    xs = np.arange(np.floor(pts[:, 0].min()) - 1, pts[:, 0].max() + 1.01, step_cm)
    ys = np.arange(np.floor(pts[:, 1].min()) - 1, pts[:, 1].max() + 1.01, step_cm)
    grid = [(float(x), float(y), "grid") for x in xs for y in ys if cv2.pointPolygonTest(hull, (float(x), float(y)), True) >= -2.0]
    grid += [(float(x), float(y), nm) for nm, x, y in extra]
    Fg, info = [], []
    for x, y, nm in grid:
        k = int(np.argmin(np.hypot(pts[:, 0] - x, pts[:, 1] - y)))
        p = patches[k]
        u, v = C.cm_to_px(x, y)
        img = bg.copy()
        yy, xx = p["ys"] + int(round(v)), p["xs"] + int(round(u))
        ok = (yy >= 0) & (yy < img.shape[0]) & (xx >= 0) & (xx < img.shape[1])
        img[yy[ok], xx[ok]] = p["pix"][ok]
        Fg.append(img)
        info.append(dict(x=x, y=y, kind=nm, u=u, v=v))
    return np.stack(Fg), np.repeat(wbg[None], len(Fg), 0), np.repeat(S0[None], len(Fg), 0), info


def stage_o1(E, out):
    from policy_probe import load_obs, move_start
    T = pd.read_csv(C.OUT / "grasp_train.csv")
    data = C.load_parquet(C.D2 / "dataset")
    eps = list(range(256))
    m = [move_start(data[e][1]) for e in eps]
    pg = [max(0, int(T.loc[e, "grasp_f"]) - 30) for e in eps]
    cache = {}
    Fs, Ws = load_obs(C.D2 / "dataset", list(zip(eps, m)), cache)
    Ss = np.stack([data[e][0][m[i]] for i, e in enumerate(eps)])
    Fp, Wp = load_obs(C.D2 / "dataset", list(zip(eps, pg)), cache)
    Sp = np.stack([data[e][0][pg[i]] for i, e in enumerate(eps)])
    t1 = [i for i in eps if T.loc[i, "task"] == "T1"]
    U = pd.read_csv(SA / "s1_untrained_candidates.csv")
    Fg, Wg, Sg, info = build_points(T.loc[t1].reset_index(drop=True), Fs[t1], Ws[t1], Ss[t1], 1.5,
                                    [(r.id, r.x_cm, r.y_cm) for r in U.itertuples()])
    G = pd.DataFrame(info)
    G["d_train"] = [float(np.min(np.hypot(T.cube_x - x, T.cube_y - y))) for x, y in zip(G.x, G.y)]
    G.to_csv(out / "o1_points.csv", index=False)
    t0 = time.time()
    st = E.chunks(Fs, Ws, Ss)
    pr = E.chunks(Fp, Wp, Sp)
    gr = E.chunks(Fg, Wg, Sg)
    np.savez_compressed(out / "o1.npz", start=st.astype(np.float32), pregrasp=pr.astype(np.float32), grid=gr.astype(np.float32),
                        m=np.array(m), pg=np.array(pg))
    return dict(n_start=len(eps), n_points=len(G), n_novel_ge2=int((G.d_train >= 2).sum()), s=time.time() - t0)


# ---------------- g1 / g2 (기존 스크립트 그대로, Engine · 출력 폴더만) ----------------
def with_engine(E, fn):
    orig = A.Engine
    A.Engine = lambda *a, **k: E
    try:
        return fn()
    finally:
        A.Engine = orig


def stage_g1(E, out, smoke=False):
    G1 = importlib.import_module("g1_roll_factorial")
    argv = ["g1", "--out", str(out / "g1"), "--d4_ratio", "inf", "--device", E.device]
    if smoke:
        argv += ["--smoke", "--limit", "1"]
    old = sys.argv
    sys.argv = argv
    try:
        with_engine(E, G1.main)
    finally:
        sys.argv = old
    if smoke:
        return dict(smoke=True)
    old_ab = A.AB
    A.AB = out                                   # a1 이 load_g1() 로 out/g1 을 읽고 out/ 에 쓴다
    try:
        sys.modules.pop("a1_g1_analyze", None)
        A1 = importlib.import_module("a1_g1_analyze")
        A1.main()
    finally:
        A.AB = old_ab
    return json.load(open(out / "a1_g1.json"))


def stage_g2(E, out, smoke=False):
    G2 = importlib.import_module("g2_policy_frames")
    argv = ["g2", "--out", str(out / "g2"), "--d4_ratio", "inf", "--device", E.device]
    if smoke:
        argv += ["--limit", "1", "--n_noise", "1"]
    old = sys.argv
    sys.argv = argv
    try:
        with_engine(E, G2.main)
    finally:
        sys.argv = old
    return s1s6(out)


def s1s6(out):
    """action_bottleneck/a2_g2_analyze.py 의 S1 · S6 와 같은 계산 (S2–S5 는 뺌)."""
    sys.modules.pop("a2_g2_analyze", None)
    A2 = importlib.import_module("a2_g2_analyze")
    R = pd.read_csv(out / "g2/rows.csv")
    ch = np.load(out / "g2/chunks.npy").astype(np.float32).mean(0)
    tip = A.tip_fn()
    data, fut = {}, []
    for i, r in R.iterrows():
        if r.ds not in data:
            data[r.ds] = C.load_parquet(r.ds)
        s, a = data[r.ds][int(r.ep)]
        f0 = int(r.frame)
        h = int(min(50, max(1, round(r.t_to_close * FPS))))
        f1 = min(f0 + h, len(s) - 1)
        p0 = tip(s[f0, :5])[0]
        fut.append(np.concatenate([tip(a[f1, :5])[0] - p0, tip(ch[i, h - 1, :5])[0] - p0, [ch[i, h - 1, 0] - s[f0, 0], h]]))
    fut = np.array(fut)
    ut, ur = A2.axes(R.cube_x.values, R.cube_y.values)
    for nm, sl in (("hum_a", slice(0, 2)), ("pol", slice(2, 4))):
        R[f"{nm}_tan"] = (fut[:, sl] * ut).sum(1)
        R[f"{nm}_rad"] = (fut[:, sl] * ur).sum(1)
    R["pol_dpan"], R["h"] = fut[:, 4], fut[:, 5]
    res = {}
    Tr = R[R.src == "train"]
    for lo, hi in A2.PH:
        d = Tr[(Tr.t_to_close > lo) & (Tr.t_to_close <= hi)] if lo else Tr[Tr.t_to_close <= hi]
        row = dict(n=len(d))
        for who in ("hum_a", "pol"):
            for ax, j in (("tan", 0), ("rad", 1)):
                w, r2 = A2.slope_fit(d, f"{who}_{ax}")
                row[f"{who}_{ax}_slope"], row[f"{who}_{ax}_r2"] = float(w[j]), r2
        res[f"S1_{lo}-{hi}s"] = row
    Ev = R[R.src == "eval"].merge(pd.read_csv(A2.VP / "f1_results/eval_label_qc.csv"), on="row", how="left")
    Ev = Ev[(Ev.carea >= 3000) & (~Ev.border.astype(bool))]
    inr = Ev.tan_cm.between(-2.20, 1.46) & Ev.rad_cm.between(-3.96, 1.54)
    s6 = dict(n=len(Ev), n_in_range=int(inr.sum()))
    for nm, d in (("in_range", Ev[inr]), ("out_range", Ev[~inr])):
        if len(d) > 10:
            w, r2 = A2.slope_fit(d, "pol_tan")
            s6[nm] = dict(n=len(d), pol_tan_slope=float(w[0]), r2=r2, label_tan_absmed=float(d.tan_cm.abs().median()),
                          pol_tan_absmed=float(d.pol_tan.abs().median()))
    res["S6_eval"] = s6
    R.to_csv(out / "s1s6_rows.csv", index=False)
    json.dump(res, open(out / "s1s6.json", "w"), indent=1, default=float)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--step", default="004000")
    ap.add_argument("--stages", default="o3,o1,g1,g2")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--smoke", action="store_true", help="CPU 시험: o3 2 프레임, g1 · g2 1 판")
    ap.add_argument("--allow_training_running", action="store_true")
    args = ap.parse_args()
    if args.device == "cuda" and not args.allow_training_running and TW.training_processes():
        sys.exit(f"학습 프로세스 실행 중 {TW.training_processes()} — GPU 평가 안 함")
    step = "020000" if args.run == "d2" else args.step
    root = ck_root(args.run)
    if not (root / step / "pretrained_model/model.safetensors").exists():
        sys.exit(f"체크포인트 없음: {root / step}")
    out = SA / "eval" / (f"{args.run}_{step}" + ("_smoke" if args.smoke else ""))
    out.mkdir(parents=True, exist_ok=True)
    log = dict(run=args.run, step=step, ckpt=str(root / step), start=time.strftime("%F %T"), stages={})
    t0 = time.time()
    E = A.Engine(step, device=args.device, n_noise=4, ckpt_root=root)
    log["load_s"] = time.time() - t0
    for st in args.stages.split(","):
        ts = time.time()
        if st == "o3":
            r = stage_o3(E, out, limit=2 if args.smoke else None)
        elif st == "o1":
            r = stage_o1(E, out)
        elif st == "g1":
            r = stage_g1(E, out, smoke=args.smoke)
        elif st == "g2":
            r = stage_g2(E, out, smoke=args.smoke)
        else:
            raise SystemExit(f"모르는 단계 {st}")
        log["stages"][st] = dict(s=time.time() - ts, summary=r if st != "g1" else {k: r[k] for k in list(r)[:6]} if isinstance(r, dict) else r)
        json.dump(log, open(out / "eval_log.json", "w"), indent=1, default=str, ensure_ascii=False)
        print(f"[{st}] done {time.time() - ts:.0f}s", flush=True)
        gc.collect()
    log["end"] = time.strftime("%F %T")
    log["gpu_busy_s"] = E.gpu_busy_s
    json.dump(log, open(out / "eval_log.json", "w"), indent=1, default=str, ensure_ascii=False)
    (out / "DONE").write_text(log["end"] + "\n")


if __name__ == "__main__":
    main()
