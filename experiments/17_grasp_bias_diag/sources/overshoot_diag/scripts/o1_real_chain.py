#!/home/user/so101-env/bin/python
"""L1 · L2 · L4 (CPU, 로봇 · 카메라 연결 없음, 원본 읽기만). 설계: ../00_design.md
  PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python o1_real_chain.py
→ ../data/real_chain.json · ../data/frames_err.csv · ../data/chunks_err.csv
"""
import glob
import json
import math
import os
import sys
import time

import av
import cv2
import numpy as np
import pandas as pd

TOOLS = os.path.expanduser("~/so101_runs/main_k8/r1_r2_collection/tools")
sys.path.insert(0, TOOLS)
os.environ["R12_CONFIG"] = os.path.expanduser("~/so101_runs/main_k8/r1_r2_collection/config/sg50.yaml")
import r12_common as rc  # noqa: E402
import sg_phase  # noqa: E402
import sg_sticker as ss  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data")
os.makedirs(OUT, exist_ok=True)
R = os.path.expanduser("~/so101_runs/main_k8/sgft01_real_eval/eval/rollouts/20261109_100345_10k_t01_02_03_04_05_06_07_08_ft_series")
P3 = rc.session_dir("practice/sg50_pilot3")
DIAG2DS = {1: 0, 2: 1, 3: 2, 5: 3, 6: 4, 7: 5, 8: 6, 9: 7}
LAB = ["K5", "U7", "K2", "K8a", "K8b", "HU7", "K4", "U1"]
VER = "P F F F F F P F".split()
J = ["pan", "lift", "elbow", "wflex", "wroll"]
WIN = 90
HP = 15
ref = next(r for r in ss.read_refs()["refs"].values() if r.get("name") == "닫기자리")
TOL = {"du": ref["tol"].get("u", 0.02), "dv": ref["tol"].get("v", 0.02), "size": ref["tol"].get("size", 0.05)}
PRM = ss.load_params()


def err_of(img):
    c = ss.target_compare(ss.detect(img, PRM), ref)
    if c is None:
        return dict(du=np.nan, dv=np.nan, size=np.nan, dangle=np.nan, edge=np.nan)
    return dict(du=c["du"], dv=c["dv"], size=c["size"], dangle=c["dangle"], edge=float(c["edge"]))


def load_ds(root):
    info = json.load(open(f"{root}/meta/info.json"))
    em = pd.concat([pd.read_parquet(p) for p in sorted(glob.glob(f"{root}/meta/episodes/*/*.parquet"))])
    df = pd.concat([pd.read_parquet(p) for p in sorted(glob.glob(f"{root}/data/*/*.parquet"))])
    return info, em, df


def frames(root, info, em, ep, want, cam="wrist"):
    er = em[em.episode_index == ep].iloc[0]
    k = f"observation.images.{cam}"
    p = f"{root}/" + info["video_path"].format(video_key=k, chunk_index=int(er[f"videos/{k}/chunk_index"]), file_index=int(er[f"videos/{k}/file_index"]))
    t0 = float(er[f"videos/{k}/from_timestamp"])
    want = set(want)
    hi = max(want)
    out = {}
    c = av.open(p)
    for f in c.decode(video=0):
        fi = int(round((float(f.pts * f.time_base) - t0) * 30))
        if fi in want and fi not in out:
            out[fi] = f.to_ndarray(format="rgb24")
        if fi > hi:
            break
    c.close()
    return out


def close_attempts(st, ac):
    g = ac[:, 5]
    g0 = np.median(g[:10])
    closes, hi, armed = [], g[0], False
    for k in range(len(g)):
        if g[k] > g0 + 8:
            armed = True
            hi = max(hi, g[k])
        if armed and g[k] < 0.7 * hi and hi > g0 + 8:
            closes.append(k)
            armed = False
            hi = g[k]
    held = [k for k in closes if k + 30 < len(st) and np.median(st[k + 20:k + 30, 5]) > 6]
    return closes, held


def window_mask(n, closes):
    m = np.zeros(n, bool)
    for k in closes:
        m[max(0, k - WIN):k] = True
    return m


def highpass(x):
    """x − 15 프레임 중심 이동평균 (NaN 은 2 프레임까지 선형 보간, 그보다 길면 NaN 유지)."""
    s = pd.Series(x).interpolate(limit=2, limit_area="inside")
    ma = s.rolling(HP, center=True, min_periods=HP).mean()
    return (s - ma).values


def segs(mask):
    out, i = [], 0
    while i < len(mask):
        if mask[i]:
            j = i
            while j < len(mask) and mask[j]:
                j += 1
            out.append((i, j))
            i = j
        else:
            i += 1
    return out


def crossings(e, tol):
    """허용 폭 밖 → 반대쪽 허용 폭 밖 (사이 NaN · 허용 안 은 건너뜀) 횟수."""
    side, n = 0, 0
    for v in e:
        if np.isnan(v) or abs(v) <= tol:
            continue
        s = 1 if v > 0 else -1
        if side and s != side:
            n += 1
        side = s
    return n


def per_window_stats(st, gi, E, mask, closes):
    """창마다: 관절 고역 RMS, 속도 부호 바뀜/s, goal 고역 RMS, 추종 오차, 오차 고역 sd, 지나침 수."""
    rows = []
    for a, b in segs(mask):
        L = b - a
        if L < 30:
            continue
        r = {"a": a, "b": b, "sec": L / 30, "close": int(b)}
        for j, nm in enumerate(J):
            hp = highpass(st[:, j])[a:b]
            r[f"rms_{nm}"] = float(np.sqrt(np.nanmean(hp ** 2)))
            v = np.diff(st[a:b, j])
            v = v[np.abs(v) > 0.05]
            r[f"flip_{nm}"] = float(np.sum(np.diff(np.sign(v)) != 0) / (L / 30))
            if gi is not None:
                hg = highpass(gi[:, j])[a:b]
                r[f"rms_goal_{nm}"] = float(np.sqrt(np.nanmean(hg ** 2)))
                r[f"track_{nm}"] = float(np.sqrt(np.nanmean((gi[a:b, j] - st[a:b, j]) ** 2)))
        for k in ("du", "dv", "size"):
            e = E[k][a:b]
            hp = highpass(E[k])[a:b]
            r[f"valid_{k}"] = float(np.mean(~np.isnan(e)))
            r[f"hpsd_{k}"] = float(np.nanstd(hp)) if np.sum(~np.isnan(hp)) > 10 else np.nan
            r[f"mean_{k}"] = float(np.nanmean(e)) if np.sum(~np.isnan(e)) else np.nan
            r[f"inside_{k}"] = float(np.nanmean(np.abs(e - (1 if k == "size" else 0)) <= TOL[k])) if np.sum(~np.isnan(e)) else np.nan
            if k != "size":
                r[f"cross_{k}"] = crossings(e, TOL[k])
        rows.append(r)
    return rows


def l2_pairs(st, E, mask, step=3):
    """0.1 s (3 프레임) 변화: Δ관절 (5) → Δdu · Δdv · Δsize."""
    X, Y = [], []
    idx = np.where(mask)[0]
    for i in idx:
        k = i + step
        if k >= len(st) or not mask[k]:
            continue
        y = [E[c][k] - E[c][i] for c in ("du", "dv", "size")]
        if np.any(np.isnan(y)) or E["edge"][i] == 1 or E["edge"][k] == 1:
            continue
        X.append(st[k, :5] - st[i, :5])
        Y.append(y)
    return np.array(X), np.array(Y)


def r2(X, Y):
    if len(X) < 20:
        return {}
    A = np.c_[X, np.ones(len(X))]
    out = {}
    for c, nm in enumerate(("du", "dv", "size")):
        w, *_ = np.linalg.lstsq(A, Y[:, c], rcond=None)
        res = Y[:, c] - A @ w
        out[nm] = {"r2": float(1 - res.var() / max(Y[:, c].var(), 1e-12)), "coef": [float(x) for x in w[:5]], "n": int(len(X))}
    return out


def main():
    t0 = time.time()
    info, em, df = load_ds(f"{R}/dataset")
    T = pd.read_csv(f"{R}/diag/ticks.csv")
    C = [json.loads(x) for x in open(f"{R}/diag/chunks.jsonl") if x.strip()]
    res = {"robot": {}, "human": {}, "tol": TOL}
    frows, crows, allX, allY = [], [], [], []
    for de, ep in DIAG2DS.items():
        e = df[df.episode_index == ep].sort_values("frame_index")
        st = np.stack(e["observation.state"].values).astype(float)
        ac = np.stack(e["action"].values).astype(float)
        tk = T[T.episode == de].reset_index(drop=True)
        assert len(tk) == len(st), (de, len(tk), len(st))
        gi = tk[[f"goal_in_{j}" for j in ("shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper")]].values.astype(float)
        sent = tk[[f"sent_{j}" for j in ("shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper")]].values.astype(float)
        closes, held = close_attempts(st, ac)
        mask = window_mask(len(st), closes)
        want = np.where(mask)[0]
        imgs = frames(f"{R}/dataset", info, em, ep, want) if len(want) else {}
        E = {k: np.full(len(st), np.nan) for k in ("du", "dv", "size", "dangle", "edge")}
        for i, im in imgs.items():
            for k, v in err_of(im).items():
                E[k][i] = v
        for i in want:
            frows.append(dict(who="robot", ep=ep, lab=LAB[ep], frame=int(i), **{k: E[k][i] for k in E}, **{f"st_{j}": st[i, n] for n, j in enumerate(J)},
                              **{f"goal_{j}": gi[i, n] for n, j in enumerate(J)}))
        W = per_window_stats(st, gi, E, mask, closes)
        clamp = float(np.mean(np.any(np.abs(sent[:, :5] - gi[:, :5]) > 1e-3, axis=1)[mask])) if mask.any() else np.nan
        X, Y = l2_pairs(st, E, mask)
        if len(X):
            allX.append(X)
            allY.append(Y)
        # chunk 관측 (정책이 실제로 본 손목 영상) 오차
        ch = [c for c in C if c["episode"] == de]
        tick0 = int(tk.tick.iloc[0])
        cerr = []
        for c in ch:
            fi = int(c["obs_tick"]) - tick0
            if fi < 0 or fi >= len(st) or not mask[fi]:
                continue
            im = cv2.cvtColor(cv2.imread(f"{R}/diag/obs/c{c['chunk_id']:05d}_wrist.png"), cv2.COLOR_BGR2RGB)
            er = err_of(im)
            z = np.load(f"{R}/diag/chunks/c{c['chunk_id']:05d}.npz")
            a = z["processed"]
            h = min(49, int(c.get("applied_delay") or 0) + 20)
            row = dict(ep=ep, lab=LAB[ep], chunk=c["chunk_id"], frame=fi, applied_delay=c.get("applied_delay"), **er,
                       **{f"obs_{j}": c["obs_state"][n] for n, j in enumerate(J)}, **{f"cmd_h_{j}": float(a[h, n] - c["obs_state"][n]) for n, j in enumerate(J)},
                       **{f"cmd_end_{j}": float(a[49, n] - c["obs_state"][n]) for n, j in enumerate(J)}, cmd_grip_min=float(a[:, 5].min()))
            cerr.append(row)
            crows.append(row)
        # chunk 관측 쌍 지나침
        pairs = {"du": [0, 0, 0], "dv": [0, 0, 0]}  # [쌍 수 (둘 다 허용 밖), 같은 쪽, 반대쪽 (지나침)]
        for p, q in zip(cerr, cerr[1:]):
            if q["frame"] - p["frame"] > 25:
                continue
            for k in ("du", "dv"):
                a1, a2 = p[k], q[k]
                if np.isnan(a1) or np.isnan(a2) or abs(a1) <= TOL[k] or abs(a2) <= TOL[k]:
                    continue
                pairs[k][0] += 1
                pairs[k][1 if np.sign(a1) == np.sign(a2) else 2] += 1
        res["robot"][LAB[ep]] = dict(verdict=VER[ep], n_close=len(closes), n_held=len(held), win_frames=int(mask.sum()), clamp_frac=clamp,
                                    windows=W, chunk_pairs=pairs, n_chunk_obs=len(cerr))
        print(f"robot {LAB[ep]} {VER[ep]} 닫기 {len(closes)} 창 {mask.sum()} 프레임 · chunk 관측 {len(cerr)} · {time.time() - t0:.0f}s", flush=True)
    Xr, Yr = (np.concatenate(allX), np.concatenate(allY)) if allX else (np.zeros((0, 5)), np.zeros((0, 3)))
    res["robot_l2"] = r2(Xr, Yr)
    # 사람 (예비3 ep3–42)
    info3, em3, d3 = load_ds(f"{P3}/dataset")
    hX, hY = [], []
    for ep in range(3, 43):
        e = d3[d3.episode_index == ep].sort_values("frame_index")
        st = np.stack(e["observation.state"].values).astype(float)
        ac = np.stack(e["action"].values).astype(float)
        ci = sg_phase.analyze(st, ac, 30)["_idx"]["close"]
        mask = window_mask(len(st), [ci])
        want = np.where(mask)[0]
        imgs = frames(f"{P3}/dataset", info3, em3, ep, want)
        E = {k: np.full(len(st), np.nan) for k in ("du", "dv", "size", "dangle", "edge")}
        for i, im in imgs.items():
            for k, v in err_of(im).items():
                E[k][i] = v
        for i in want:
            frows.append(dict(who="human", ep=ep, lab="H", frame=int(i), **{k: E[k][i] for k in E}, **{f"st_{j}": st[i, n] for n, j in enumerate(J)},
                              **{f"goal_{j}": ac[i, n] for n, j in enumerate(J)}))
        W = per_window_stats(st, ac, E, mask, [ci])
        # 사람: 20 프레임 간격 표본 쌍 (chunk 관측 간격과 같게)
        pairs = {"du": [0, 0, 0], "dv": [0, 0, 0]}
        ii = list(range(max(0, ci - WIN), ci, 20))
        for p, q in zip(ii, ii[1:]):
            for k in ("du", "dv"):
                a1, a2 = E[k][p], E[k][q]
                if np.isnan(a1) or np.isnan(a2) or abs(a1) <= TOL[k] or abs(a2) <= TOL[k]:
                    continue
                pairs[k][0] += 1
                pairs[k][1 if np.sign(a1) == np.sign(a2) else 2] += 1
        X, Y = l2_pairs(st, E, mask)
        if len(X):
            hX.append(X)
            hY.append(Y)
        res["human"][f"ep{ep}"] = dict(windows=W, chunk_pairs=pairs)
    print(f"사람 40 편 · {time.time() - t0:.0f}s", flush=True)
    res["human_l2"] = r2(np.concatenate(hX), np.concatenate(hY))
    pd.DataFrame(frows).to_csv(os.path.join(OUT, "frames_err.csv"), index=False)
    pd.DataFrame(crows).to_csv(os.path.join(OUT, "chunks_err.csv"), index=False)
    json.dump(res, open(os.path.join(OUT, "real_chain.json"), "w"), ensure_ascii=False, indent=1, default=float)
    print("O1_DONE", f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
