#!/home/user/so101-env/bin/python
"""SG50 파인튜닝 오프라인 테스트 (GPU, 로봇 · 카메라 연결 없음) — 체크포인트마다 같은 관측 · 같은 noise 로 50 스텝 action chunk 를
다시 뽑아 사람 action (같은 프레임부터 50 개) 과 비교한다. 추론 엔진은 vd_20261103_01/scripts/v02_engine.Engine 을 수정 없이 씀
(num_inference_steps 5, RTC 설정 같음, prefix 없음 = 모델 그대로, noise = seed 2026 bank 앞 N 개). v_common.CKPT 만 이 프로세스 안에서 바꿈.

장면 묶음 (dataset 읽기만):
  A sg_train  : practice/sg50_pilot3 ep3–42 (학습에 씀, in-sample) — 판마다 6 장면
  B sg_other  : 학습에 안 쓴 SG50 판 — 예비3 removed_20261106_141910 (16 편, 예전 순서: 팬 → 손목 찾기 → 열기) + 예비2 ep0 · 1 · 3
                (같은 작업자 · 같은 S0 · 같은 자리 영역, 순서가 다름 → 진짜 held-out 아님)
  C d2        : d2 사람 판 32 편 (8 편마다) — 원래 작업 (쉬는 자세 시작) 유지 확인
장면 (판마다, sg_phase 정의): start (0) · pan_done (팬 정렬 끝) · pre_reach (큰 팔 뻗기 10 프레임 전) · descent (뻗기 ↔ 닫기 가운데) ·
  pre_close (닫기 10 프레임 전) · hold (닫기 20 프레임 뒤)
지표: 관절별 |예측 − 사람| 평균 (50 스텝 · 앞 10 스텝), noise 사이 표준편차, 그리퍼 판단 (chunk 안에서 그리퍼가 시작보다 +8 열림 / −8 닫힘 하는지,
  사람과 같은지).

  PYTHONDONTWRITEBYTECODE=1 nice -n 10 ~/so101-env/bin/python sg_offline_eval.py --out DIR --ckpt TAG=PATH [--ckpt ...] [--n 8] [--sets A,B,C] [--limit K] [--dry]
  → DIR/raw/<tag>/<set>.npz (pred (S,N,50,6), human (S,50,6), state (S,6), meta), DIR/states_<set>.csv, DIR/results.md · results.json
"""
import argparse
import glob
import hashlib
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
HOME = os.path.expanduser("~")
VD = os.path.join(HOME, "so101_runs/main_k8/d2/visual_dependency/vd_20261103_01/scripts")
J = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
SETS = {
    "A": [(os.path.join(HOME, "so101_runs/practice/sg50_pilot3/dataset"), list(range(3, 43)))],
    "B": [(os.path.join(HOME, "so101_runs/practice/sg50_pilot3/removed_20261106_141910/dataset"), None),
          (os.path.join(HOME, "so101_runs/practice/sg50_pilot2/dataset"), [0, 1, 3])],
    "C": [(os.path.join(HOME, "so101_runs/main_k8/d2/dataset"), list(range(0, 256, 8)))],
}
PHASES = ["start", "pan_done", "pre_reach", "descent", "pre_close", "hold"]


def _episodes(root):
    import pandas as pd

    return pd.concat([pd.read_parquet(p) for p in sorted(glob.glob(f"{root}/meta/episodes/*/*.parquet"))])


def _frames(root, info, er, cam, want):
    import av

    k = f"observation.images.{cam}"
    p = os.path.join(root, info["video_path"].format(video_key=k, chunk_index=int(er[f"videos/{k}/chunk_index"]), file_index=int(er[f"videos/{k}/file_index"])))
    t0 = float(er[f"videos/{k}/from_timestamp"])
    fps = info["fps"]
    want = sorted(set(want))
    out = {}
    c = av.open(p)
    try:
        s = c.streams.video[0]
        c.seek(max(0, int((t0 + want[0] / fps - 1.0) / float(s.time_base))), stream=s, backward=True)
        for f in c.decode(s):
            fi = int(round((float(f.pts * s.time_base) - t0) * fps))
            if fi in want and fi not in out:
                out[fi] = f.to_ndarray(format="rgb24")
            if fi > want[-1]:
                break
    finally:
        c.close()
    return out


def build_states(sets, limit=None):
    """[(set, root, ep, phase, frame, state(6), human(50,6), front, wrist)]"""
    import pandas as pd

    import sg_phase

    rows = []
    for name in sets:
        for root, eps in SETS[name]:
            if not os.path.isdir(root):
                print(f"  (없음) {root}")
                continue
            info = json.load(open(f"{root}/meta/info.json"))
            df = pd.concat([pd.read_parquet(p) for p in sorted(glob.glob(f"{root}/data/*/*.parquet"))])
            em = _episodes(root)
            ep_list = eps if eps is not None else sorted(int(e) for e in df.episode_index.unique())
            if limit:
                ep_list = ep_list[:limit]
            for ep in ep_list:
                e = df[df.episode_index == ep].sort_values("frame_index")
                st = np.stack(e["observation.state"].values).astype(np.float32)
                ac = np.stack(e["action"].values).astype(np.float32)
                n = len(st)
                r = sg_phase.analyze(st, ac, info["fps"])
                idx = r.get("_idx") or {}
                ci = idx.get("close")
                rm = np.where(st[:, 1] - st[0, 1] > 20)[0]
                ri = int(rm[0]) if len(rm) and (ci is None or rm[0] < ci) else None
                pts = {"start": 0, "pan_done": idx.get("pan_end") if idx.get("pan_end") is not None else min(30, n - 1)}
                if ri is not None:
                    pts["pre_reach"] = max(0, ri - 10)
                    if ci is not None:
                        pts["descent"] = (ri + ci) // 2
                if ci is not None:
                    pts["pre_close"] = max(0, ci - 10)
                    pts["hold"] = min(n - 1, ci + 20)
                er = em[em.episode_index == ep].iloc[0]
                fr = {cam: _frames(root, info, er, cam, list(pts.values())) for cam in ("front", "wrist")}
                for ph, fi in pts.items():
                    if fi not in fr["front"] or fi not in fr["wrist"]:
                        continue
                    h = ac[fi:fi + 50]
                    if len(h) < 50:
                        h = np.concatenate([h, np.repeat(h[-1:], 50 - len(h), 0)])
                    rows.append({"set": name, "root": root.replace(HOME, "~"), "ep": int(ep), "phase": ph, "frame": int(fi), "state": st[fi],
                                 "human": h, "front": fr["front"][fi], "wrist": fr["wrist"][fi]})
            print(f"  {name} {root.replace(HOME, '~')}: 판 {len(ep_list)} → 누적 장면 {len(rows)}", flush=True)
    return rows


def grip_decision(chunk, g0):
    """chunk (..., 50) gripper → +1 열림 (시작 + 8 넘음) · −1 닫힘 (시작 − 8 아래) · 0."""
    mx, mn = chunk.max(-1), chunk.min(-1)
    return np.where(mx > g0 + 8, 1, np.where(mn < g0 - 8, -1, 0))


def metrics(pred, human, state):
    """pred (S,N,50,6) human (S,50,6) → dict 배열 (장면별)."""
    err = np.abs(pred - human[:, None])  # S,N,50,6
    out = {"mae50": err.mean(axis=(1, 2)), "mae10": err[:, :, :10].mean(axis=(1, 2)), "spread": pred.std(axis=1).mean(axis=1)}
    g0 = state[:, 5]
    hd = grip_decision(human[:, :, 5], g0)
    pd_ = grip_decision(pred[:, :, :, 5], g0[:, None])
    out["grip_human"] = hd
    out["grip_agree"] = (pd_ == hd[:, None]).mean(axis=1)
    return out


def summarize(out_dir, tags, sets):
    import pandas as pd

    L = ["# SG50 파인튜닝 오프라인 테스트", "",
         f"- 만든 시각 {time.strftime('%Y-%m-%d %H:%M')} · `tools/sg_offline_eval.py` · 엔진 v02_engine (num_inference_steps 5, RTC 설정, prefix 없음), 같은 장면 · 같은 noise 로 체크포인트만 바꿈.",
         "- 오차 = |예측 action − 사람 action| 평균 (°, 그리퍼는 명령 단위), 50 스텝 전체 · 앞 10 스텝. 흔들림 = noise 사이 표준편차 평균. 그리퍼 판단 일치 = chunk 안 열림/닫힘/없음이 사람과 같은 비율.",
         "- A = 학습에 쓴 판 (in-sample). B = 학습에 안 쓴 SG50 판 (같은 작업자 · 예전 순서 — 진짜 held-out 아님). C = d2 사람 판 (원래 작업).", ""]
    res = {}
    for s in sets:
        T = []
        for tag in tags:
            f = os.path.join(out_dir, "raw", tag, f"{s}.npz")
            if not os.path.exists(f):
                continue
            z = np.load(f, allow_pickle=True)
            m = metrics(z["pred"], z["human"], z["state"])
            ph = z["phase"]
            for p in ["전체"] + PHASES:
                sel = np.ones(len(ph), bool) if p == "전체" else (ph == p)
                if not sel.any():
                    continue
                T.append({"ckpt": tag, "장면": p, "n": int(sel.sum()), "오차50": m["mae50"][sel].mean(0), "오차10": m["mae10"][sel].mean(0),
                          "흔들림": m["spread"][sel].mean(0), "그리퍼일치": float(m["grip_agree"][sel].mean())})
        if not T:
            continue
        res[s] = T
        L += [f"## 묶음 {s}", "", "| 체크포인트 | 장면 | n | 오차 50 (pan · lift · elbow · wflex · wroll · grip) | 오차 10 평균 | 흔들림 평균 | 그리퍼 판단 일치 |", "|---|---|---:|---|---:|---:|---:|"]
        for t in T:
            L.append(f"| {t['ckpt']} | {t['장면']} | {t['n']} | {' · '.join(f'{v:.1f}' for v in t['오차50'])} | {t['오차10'].mean():.2f} | {t['흔들림'].mean():.2f} | {t['그리퍼일치']:.0%} |")
        L.append("")
    with open(os.path.join(out_dir, "results.md"), "w") as f:
        f.write("\n".join(L) + "\n")
    json.dump({s: [{k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in t.items()} for t in T] for s, T in res.items()},
              open(os.path.join(out_dir, "results.json"), "w"), ensure_ascii=False, indent=1)
    print(f"→ {os.path.join(out_dir, 'results.md')}")


def sha16(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while b := f.read(1 << 24):
            h.update(b)
    return h.hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--ckpt", action="append", default=[], help="TAG=.../pretrained_model")
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--sets", default="A,B,C")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--dry", action="store_true", help="장면만 만들고 GPU 안 씀")
    ap.add_argument("--summarize", action="store_true")
    a = ap.parse_args()
    sets = a.sets.split(",")
    os.makedirs(a.out, exist_ok=True)
    tags = [c.split("=", 1)[0] for c in a.ckpt]
    if a.summarize:
        summarize(a.out, tags, sets)
        return 0
    t0 = time.time()
    rows = build_states(sets, a.limit)
    import pandas as pd

    for s in sets:
        pd.DataFrame([{k: r[k] for k in ("set", "root", "ep", "phase", "frame")} for r in rows if r["set"] == s]).to_csv(os.path.join(a.out, f"states_{s}.csv"), index=False)
    print(f"장면 {len(rows)} ({time.time() - t0:.0f} s)", flush=True)
    if a.dry:
        return 0
    sys.path.insert(0, VD)
    import v_common as V
    import v02_engine as E

    for c in a.ckpt:
        tag, path = c.split("=", 1)
        V.CKPT = __import__("pathlib").Path(path)  # 이 프로세스 안에서만
        t1 = time.time()
        eng = E.Engine(n_noise=a.n)
        for s in sets:
            R = [r for r in rows if r["set"] == s]
            if not R:
                continue
            pred = np.stack([eng.run(r["state"], [(r["front"], r["wrist"])])[0] for r in R]).astype(np.float32)
            d = os.path.join(a.out, "raw", tag)
            os.makedirs(d, exist_ok=True)
            np.savez_compressed(os.path.join(d, f"{s}.npz"), pred=pred, human=np.stack([r["human"] for r in R]), state=np.stack([r["state"] for r in R]),
                                phase=np.array([r["phase"] for r in R]), ep=np.array([r["ep"] for r in R]), root=np.array([r["root"] for r in R]))
            print(f"  {tag} {s}: {len(R)} 장면 · {time.time() - t1:.0f} s", flush=True)
        json.dump({"ckpt": path, "model_sha16": sha16(os.path.join(path, "model.safetensors")), "n_noise": a.n, "sec": round(time.time() - t1, 1)},
                  open(os.path.join(a.out, "raw", tag, "meta.json"), "w"), indent=1)
        del eng
        import torch

        torch.cuda.empty_cache()
    summarize(a.out, tags, sets)
    return 0


if __name__ == "__main__":
    sys.exit(main())
