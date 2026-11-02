"""분석 2 보조 (CPU): 라벨 규약 θ = 0.91·roll − 5.5° 의 회전 방향 · 크기를 사람 시연에서 직접 확인.
같은 판 안에서 두 프레임 (닫힘 3 s 안, 큐브 검출 통과) 사이에 wrist_roll 이 많이 바뀌고 (|Δroll| ≥ 6°)
집게 끝 (FK) 이 거의 그대로인 (≤ 0.4 cm) 쌍 → 큐브는 탁자에서 그대로이므로 탁자 상대 위치도 그대로여야 한다.
  관측 영상 회전: rel 벡터 각도 변화 φ_obs = ∠rel₂ − ∠rel₁ (|rel| ≥ 0.5 cm 만)
  규약 기대: rel₂ = M(θ₂)⁻¹ M(θ₁) rel₁ → φ_exp
  기울기 φ_obs ~ φ_exp (1 = 규약 방향·크기 맞음, −1 = 반대)
기준점 (u*, v*) 이 회전축이 아니면 오차가 생긴다 — 기준점 대신 영상 중심 (320, 240) 을 쓴 값도 같이 낸다.
출력 c2_roll_rotation_check.json
"""
import json

import numpy as np
import pandas as pd

import ab_core as A
from ab_core import C


def ang(v):
    return np.degrees(np.arctan2(v[..., 1], v[..., 0]))


def wrap(a):
    return (a + 180) % 360 - 180


def main():
    L = pd.read_csv(A.D2 / "vision_probe/labels_v2.csv", low_memory=False)
    P = L[L.probe_ok.astype(bool)].copy()
    tip = A.tip_fn()
    J = P[["s_shoulder_pan", "s_shoulder_lift", "s_elbow_flex", "s_wrist_flex", "s_wrist_roll"]].values
    P["tx"], P["ty"] = tip(J).T
    res = {}
    for piv in ("ref", "center"):
        if piv == "ref":
            ru, rv = P.rel_u_cm.values, P.rel_v_cm.values
        else:
            ru, rv = (P.cu.values - 320) / P.pxcm.values, (P.cv.values - 240) / P.pxcm.values
        P["ru"], P["rv"] = ru, rv
        rows = []
        for e, g in P.groupby("ep"):
            g = g.sort_values("frame")
            v = g[["ru", "rv", "roll", "tx", "ty"]].values
            for i in range(len(v)):
                for j in range(i + 1, len(v)):
                    dr = v[j, 2] - v[i, 2]
                    if abs(dr) < 6 or np.hypot(v[j, 3] - v[i, 3], v[j, 4] - v[i, 4]) > 0.4:
                        continue
                    if np.hypot(*v[i, :2]) < 0.5 or np.hypot(*v[j, :2]) < 0.5:
                        continue
                    Q = np.linalg.solve(A.M_img2tab(v[j, 2]), A.M_img2tab(v[i, 2]))
                    pe = Q @ v[i, :2]
                    rows.append(dict(ep=e, droll=dr, phi_obs=wrap(ang(v[j, :2]) - ang(v[i, :2])), phi_exp=wrap(ang(pe) - ang(v[i, :2]))))
        D = pd.DataFrame(rows)
        if D.empty:
            res[piv] = {"n_pairs": 0}
            continue
        # 판마다 쌍 수가 달라서 판 평균 가중 회귀
        w = 1 / D.groupby("ep").ep.transform("size")
        sl = float((w * D.phi_obs * D.phi_exp).sum() / (w * D.phi_exp ** 2).sum())
        sl_roll = float((w * D.phi_obs * D.droll).sum() / (w * D.droll ** 2).sum())
        rng = np.random.default_rng(0)
        ue = D.ep.unique()
        bs = []
        for _ in range(1000):
            s = rng.choice(ue, len(ue))
            d = pd.concat([D[D.ep == x] for x in s])
            ww = 1 / d.groupby("ep").ep.transform("size")
            bs.append((ww * d.phi_obs * d.phi_exp).sum() / (ww * d.phi_exp ** 2).sum())
        res[piv] = dict(n_pairs=len(D), n_eps=int(D.ep.nunique()), slope_obs_on_exp=sl, ci=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
                        slope_obs_deg_per_roll_deg=sl_roll, sign_agree=float((np.sign(D.phi_obs) == np.sign(D.phi_exp)).mean()),
                        droll_absmed=float(D.droll.abs().median()))
        print(piv, res[piv], flush=True)
    json.dump(res, open(A.AB / "c2_roll_rotation_check.json", "w"), indent=1)


if __name__ == "__main__":
    main()
