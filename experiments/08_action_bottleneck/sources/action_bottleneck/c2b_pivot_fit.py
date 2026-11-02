"""분석 2 보조 (CPU): wrist 영상에서 roll 축의 투영점 (회전 중심 c, px) 과 회전 이득 k (영상 회전 각 = k·Δroll) 를 사람 시연에서 맞춘다.
쌍: 같은 판, 닫힘 3 s 안, |Δroll| ≥ 6°, 집게 끝 (FK) 이동 ≤ 0.4 cm (큐브 · 탁자 정지).
모형: p₂ − c = s·Rot(σ·k·Δroll)(p₁ − c), s = √(넓이₂/넓이₁) (거리 변화), σ = 라벨 규약의 회전 방향 (M(θ₂)⁻¹M(θ₁) 의 각 부호).
k 격자 (0.3–1.8) 마다 c 를 최소제곱 → 잔차 최소 k. 판 bootstrap.
출력 c2b_pivot_fit.json
"""
import json

import numpy as np
import pandas as pd

import ab_core as A


def rot(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s], [s, c]])


def pairs():
    L = pd.read_csv(A.D2 / "vision_probe/labels_v2.csv", low_memory=False)
    P = L[L.probe_ok.astype(bool)].copy()
    tip = A.tip_fn()
    J = P[["s_shoulder_pan", "s_shoulder_lift", "s_elbow_flex", "s_wrist_flex", "s_wrist_roll"]].values
    P["tx"], P["ty"] = tip(J).T
    out = []
    for e, g in P.groupby("ep"):
        v = g.sort_values("frame")[["cu", "cv", "carea", "roll", "tx", "ty"]].values
        for i in range(len(v)):
            for j in range(i + 1, len(v)):
                dr = v[j, 3] - v[i, 3]
                if abs(dr) >= 6 and np.hypot(v[j, 4] - v[i, 4], v[j, 5] - v[i, 5]) <= 0.4:
                    Q = np.linalg.solve(A.M_img2tab(v[j, 3]), A.M_img2tab(v[i, 3]))
                    sg = np.sign(np.arctan2(Q[1, 0], Q[0, 0]) * dr)
                    out.append((e, v[i, 0], v[i, 1], v[j, 0], v[j, 1], np.sqrt(v[j, 2] / v[i, 2]), dr, sg))
    return np.array(out)


def fit(D, k):
    rows, rhs = [], []
    for e, u1, v1, u2, v2, s, dr, sg in D:
        R = s * rot(np.radians(sg * k * dr))
        rows.append(np.eye(2) - R)
        rhs.append(np.array([u2, v2]) - R @ np.array([u1, v1]))
    Am, b = np.concatenate(rows), np.concatenate(rhs)
    c = np.linalg.lstsq(Am, b, rcond=None)[0]
    r = b - Am @ c
    return c, float(np.sqrt((r ** 2).mean()))


def best(D):
    ks = np.arange(0.3, 1.81, 0.05)
    fits = [fit(D, k) for k in ks]
    i = int(np.argmin([f[1] for f in fits]))
    return ks[i], fits[i][0], fits[i][1], {round(float(k), 2): f[1] for k, f in zip(ks, fits)}


def main():
    D = pairs()
    sg = D[:, 7]
    k, c, rmse, curve = best(D)
    _, rmse_ref = fit(D, 0.0)
    # 같은 k 에서 c 를 기준점 · 영상 중심으로 고정했을 때 잔차
    bu, bv = A.ref_point_fit()
    def fixed(c0):
        r = []
        for e, u1, v1, u2, v2, s, dr, g in D:
            R = s * rot(np.radians(g * k * dr))
            r.append(np.array([u2, v2]) - np.array(c0) - R @ (np.array([u1, v1]) - np.array(c0)))
        return float(np.sqrt((np.array(r) ** 2).mean()))
    a_med = 1 / np.sqrt(20000)
    ref_c = [float(np.polyval(bu, a_med)), float(np.polyval(bv, a_med))]
    rng = np.random.default_rng(0)
    eps = np.unique(D[:, 0])
    bs = []
    for _ in range(300):
        s = rng.choice(eps, len(eps))
        Db = np.concatenate([D[D[:, 0] == x] for x in s])
        kb, cb, _, _ = best(Db)
        bs.append([kb, cb[0], cb[1]])
    bs = np.array(bs)
    res = dict(n_pairs=len(D), n_eps=len(eps), sign_values=np.unique(sg).tolist(), k=float(k), pivot_uv=c.tolist(), rmse_px=rmse,
               rmse_no_rotation_px=rmse_ref, k_ci=np.percentile(bs[:, 0], [2.5, 97.5]).tolist(),
               pivot_u_ci=np.percentile(bs[:, 1], [2.5, 97.5]).tolist(), pivot_v_ci=np.percentile(bs[:, 2], [2.5, 97.5]).tolist(),
               rmse_pivot_ref_px=fixed(ref_c), ref_point_at_area20000=ref_c, rmse_pivot_center_px=fixed([320, 240]), rmse_by_k=curve)
    json.dump(res, open(A.AB / "c2b_pivot_fit.json", "w"), indent=1)
    print({kk: v for kk, v in res.items() if kk != "rmse_by_k"})


if __name__ == "__main__":
    main()
