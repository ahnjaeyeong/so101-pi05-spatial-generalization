"""분석 2 보조 (CPU): wrist 영상 속 큐브 모서리 각도로 '영상 회전 = k·Δroll (+ pan 항)' 을 확인 (회전 중심과 무관).
닫힘 3 s 안 probe_ok 프레임 (labels_v2) 의 wrist 영상에서 가장 큰 빨강 덩어리의 cv2.minAreaRect 각도 (90° 주기).
같은 판 안 쌍 (닫힘 전이라 큐브는 탁자에 정지): Δangle (90° 주기로 감음) ~ a·Δroll + b·Δpan (|Δ| ≤ 30° 쌍만, 감김 모호성 회피).
라벨 규약은 k = 0.91, 회전 방향은 M(θ₂)⁻¹M(θ₁) 의 각 부호 → 같은 부호 규약으로 비교 (exp_sign).
출력 c2c_cube_angle.json, c2c_angles.csv
"""
import json

import cv2
import numpy as np
import pandas as pd

import ab_core as A
from ab_core import C


def main():
    L = pd.read_csv(A.D2 / "vision_probe/labels_v2.csv", low_memory=False)
    P = L[L.probe_ok.astype(bool)].copy()
    cache = {}
    ang = []
    for e, g in P.groupby("ep"):
        f0, f1 = int(g.frame.min()), int(g.frame.max())
        W = C.frames(C.D2 / "dataset", int(e), "wrist", f0, f1, cache)
        for f in g.frame.values:
            i = int(f) - f0
            a = np.nan
            if i < len(W):
                b = C.blobs(C.red_mask(W[i]), 1000)
                if b:
                    _, _, li, lab = max(b, key=lambda t: t[0])
                    cnt, _ = cv2.findContours((lab == li).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    (_, _), (w, h), th = cv2.minAreaRect(max(cnt, key=cv2.contourArea))
                    a = th % 90.0
            ang.append(a)
    P["cube_ang"] = ang
    P[["ep", "frame", "t_to_close", "roll", "s_shoulder_pan", "cube_ang"]].to_csv(A.AB / "c2c_angles.csv", index=False)
    Q = A.M_img2tab(np.array([0.0, 10.0]))
    exp_dir = np.sign(np.degrees(np.arctan2(*(np.linalg.solve(Q[1], Q[0])[[1, 0], 0]))))
    rows = []
    for e, g in P.dropna(subset=["cube_ang"]).groupby("ep"):
        v = g.sort_values("frame")[["cube_ang", "roll", "s_shoulder_pan"]].values
        for i in range(0, len(v), 2):
            for j in range(i + 2, len(v), 2):
                da = (v[j, 0] - v[i, 0] + 45) % 90 - 45
                dr, dp = v[j, 1] - v[i, 1], v[j, 2] - v[i, 2]
                if abs(dr) <= 30 and abs(dp) <= 30 and (abs(dr) >= 4 or abs(dp) >= 4):
                    rows.append((e, da, dr, dp))
    D = np.array(rows)
    X = np.column_stack([D[:, 2], D[:, 3]])
    w = 1 / pd.Series(D[:, 0]).map(pd.Series(D[:, 0]).value_counts()).values
    def wls(Xm, y, w):
        Wt = np.sqrt(w)[:, None]
        return np.linalg.lstsq(Xm * Wt, y * Wt[:, 0], rcond=None)[0]
    coef = wls(X, D[:, 1], w)
    rng = np.random.default_rng(0)
    ue = np.unique(D[:, 0])
    bs = []
    for _ in range(500):
        s = rng.choice(ue, len(ue))
        idx = np.concatenate([np.where(D[:, 0] == x)[0] for x in s])
        bs.append(wls(X[idx], D[idx, 1], w[idx]))
    bs = np.array(bs)
    r = D[:, 1] - X @ coef
    res = dict(n_frames_angle=int(P.cube_ang.notna().sum()), n_pairs=len(D), n_eps=len(ue),
               coef_roll=float(coef[0]), coef_roll_ci=np.percentile(bs[:, 0], [2.5, 97.5]).tolist(),
               coef_pan=float(coef[1]), coef_pan_ci=np.percentile(bs[:, 1], [2.5, 97.5]).tolist(),
               resid_sd_deg=float(r.std()), label_model_k=0.91, label_model_dir_sign_for_plus_roll=float(exp_dir))
    json.dump(res, open(A.AB / "c2c_cube_angle.json", "w"), indent=1)
    print(res)


if __name__ == "__main__":
    main()
