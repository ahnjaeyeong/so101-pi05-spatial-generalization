#!/home/user/so101-env/bin/python
"""o1 (실물) + o2 (재추론) 결과 → 표 숫자 (CPU). → ../data/summary.json, 화면 출력."""
import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "..", "data")
J = ["pan", "lift", "elbow", "wflex", "wroll"]
JI = {j: i for i, j in enumerate(J)}
PAIRS = [("pan", "du"), ("wflex", "dv"), ("lift", "dv"), ("lift", "size"), ("elbow", "size")]
DE = {"du": 24 / 640, "dv": 16 / 480, "size": 1.04 - 0.96}   # o2 ± 영상 변화 (u±12 px, v±8 px, ×1.04/×0.96)
CI = {"du": (2, 3), "dv": (4, 5), "size": (6, 7)}


def human_map():
    """사람 창: 0.1 s Δ오차 ~ Δ관절 (영상 1 프레임 늦게, o1 에서 R² 가장 큼) 회귀 계수 = 관절 1° 당 오차 변화."""
    F = pd.read_csv(os.path.join(D, "frames_err.csv"))
    F = F[F.who == "human"]
    X, Y = [], []
    for ep, g in F.groupby("ep"):
        g = g.set_index("frame")
        s = set(g.index)
        for i in g.index:
            k = i + 3
            if k not in s or i - 1 not in s or k - 1 not in s:
                continue
            y = g.loc[k, ["du", "dv", "size"]].values.astype(float) - g.loc[i, ["du", "dv", "size"]].values.astype(float)
            if np.isnan(y).any() or g.loc[i, "edge"] == 1 or g.loc[k, "edge"] == 1:
                continue
            X.append(g.loc[k - 1, [f"st_{j}" for j in J]].values.astype(float) - g.loc[i - 1, [f"st_{j}" for j in J]].values.astype(float))
            Y.append(y)
    X, Y = np.array(X), np.array(Y)
    A = np.c_[X, np.ones(len(X))]
    out = {}
    for c, e in enumerate(("du", "dv", "size")):
        w, *_ = np.linalg.lstsq(A, Y[:, c], rcond=None)
        out[e] = {j: float(w[JI[j]]) for j in J}
    return out, len(X)


def main():
    z = np.load(os.path.join(D, "reinfer.npz"))
    meta = json.load(open(os.path.join(D, "reinfer_meta.json")))
    A, B, C = z["A"], z["B"], z["C"]              # A (n, K, 50, 6) · B (n, 50, 6) · C (n, 8, 50, 6)
    n = len(A)
    labs = np.array([m["lab"] for m in meta["chunks"]])
    hs = np.array([min(49, int(m["applied_delay"] or 0) + 20) for m in meta["chunks"]])
    cmap, nmap = human_map()
    S = {"n_chunks": int(n), "replay_maxdiff": {"median": float(np.median(z["replay"])), "max": float(np.max(z["replay"]))}, "human_map": cmap, "human_map_n": nmap}

    def at(X, h):
        return X[np.arange(n), ..., h, :] if X.ndim == 3 else None

    for where in ("h", "end"):
        idx = hs if where == "h" else np.full(n, 49)
        a = np.stack([A[i, :, idx[i], :5] for i in range(n)])      # (n, K, 5)
        b = np.stack([B[i, idx[i], :5] for i in range(n)])          # (n, 5)
        c = np.stack([C[i, :, idx[i], :5] for i in range(n)])       # (n, 8, 5)
        nsd = c.std(1)                                              # noise 퍼짐 (n, 5)
        r = {"noise_sd_med": {j: float(np.median(nsd[:, JI[j]])) for j in J},
             "wrist_prev_abs_med": {j: float(np.median(np.abs(a[:, 1, JI[j]] - a[:, 0, JI[j]]))) for j in J},
             "state_prev_abs_med": {j: float(np.median(np.abs(b[:, JI[j]] - a[:, 0, JI[j]]))) for j in J}, "pairs": {}}
        for j, e in PAIRS:
            p, m = CI[e]
            d = a[:, p, JI[j]] - a[:, m, JI[j]]                     # ± 흔들림 영상 → 명령 차 (°)
            g = d / DE[e]                                           # 이득 (° / 오차 단위)
            half = np.abs(d) / 2                                    # 흔들림 1 배 크기 영상 변화 → 명령 변화
            L = -g * cmap[e][j]                                     # 고리 이득 (+ = 바로잡는 쪽)
            r["pairs"][f"{j}~{e}"] = {"gain_med": float(np.median(g)), "gain_iqr": [float(np.percentile(g, 25)), float(np.percentile(g, 75))],
                                     "resp_half_med": float(np.median(half)), "resp_over_noise_med": float(np.median(half / np.maximum(nsd[:, JI[j]], 1e-6))),
                                     "frac_resp_gt_noise": float(np.mean(half > nsd[:, JI[j]])), "map_c": cmap[e][j], "loop_L_med": float(np.median(L)),
                                     "loop_L_iqr": [float(np.percentile(L, 25)), float(np.percentile(L, 75))],
                                     "by_lab": {l: float(np.median(g[labs == l])) for l in sorted(set(labs))}}
        S[where] = r
    json.dump(S, open(os.path.join(D, "summary.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: S[k] for k in ("n_chunks", "replay_maxdiff", "human_map_n")}, ensure_ascii=False))
    print("사람 매핑 (관절 1° 당 오차):", {e: {j: round(v, 4) for j, v in d.items()} for e, d in cmap.items()})
    for where in ("h", "end"):
        r = S[where]
        print(f"\n[{where}] noise sd", {j: round(v, 2) for j, v in r["noise_sd_med"].items()})
        print("  손목만 직전 chunk", {j: round(v, 2) for j, v in r["wrist_prev_abs_med"].items()})
        print("  관절값만 직전 chunk", {j: round(v, 2) for j, v in r["state_prev_abs_med"].items()})
        for k, v in r["pairs"].items():
            print(f"  {k}: 이득 {v['gain_med']:+.1f} [{v['gain_iqr'][0]:+.1f}, {v['gain_iqr'][1]:+.1f}] · 흔들림 1 배 반응 {v['resp_half_med']:.2f}° "
                  f"(noise 대비 {v['resp_over_noise_med']:.2f}, noise 넘는 비율 {v['frac_resp_gt_noise']:.2f}) · 매핑 {v['map_c']:+.4f} · 고리 L {v['loop_L_med']:+.3f} "
                  f"[{v['loop_L_iqr'][0]:+.3f}, {v['loop_L_iqr'][1]:+.3f}]")


if __name__ == "__main__":
    main()
