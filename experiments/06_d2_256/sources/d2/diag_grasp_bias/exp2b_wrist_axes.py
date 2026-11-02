"""실험 2b: wrist 영상 축(u, v)이 탁자에서 어느 방향인지 사람 시연으로 맞추고(카메라 보정),
exp2 'pre' 의 wrist 큐브 이동 반응을 탁자 좌표(접선 tan · 반지름 rad) 이득 행렬 G 로 바꾼다. GPU 안 씀.

A (px/cm): 파지 1 s 전 ~ 닫힘 2 프레임 전, 큐브는 가만히 있고 집게 끝(FK)이 움직일 때 wrist 영상 큐브 중심 변화
           Δ(u,v)px = A · Δtip(tan, rad)cm  — 판마다 최소제곱.
큐브가 δc 움직이면 영상 변화 = −A δc. exp2 편집 Δimg 에 해당하는 큐브 이동 δc = −A⁻¹ Δimg.
G = (정책 집게 끝 반응) · (δc)⁻¹ — 이상적이면 단위행렬 (G_tt = 접선 따라가기 이득, G_rr = 반지름).
출력: exp2/wrist_axes.csv, 화면 요약. 사용: PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python exp2b_wrist_axes.py
"""
import json

import numpy as np
import pandas as pd

import common as C

fit = json.load(open(C.OUT / "fk_fit.json"))
Rm, tv = np.array(fit["R"]), np.array(fit["t"])


def tip(j5):
    p, _ = C.fk_xy(j5)
    return (Rm @ (p[:, :2] * 100).T).T + tv


def main():
    T = pd.read_csv(C.OUT / "grasp_train.csv")
    D = pd.read_csv(C.OUT / "exp2/rows_eval.csv")
    data = C.load_parquet(C.D2 / "dataset")
    cache = {}
    rows = []
    for e in sorted(D.ep.unique()):
        s, _ = data[e]
        gf = int(T.loc[e, "grasp_f"])
        x, y = T.loc[e, "cube_x"], T.loc[e, "cube_y"]
        ur = np.array([x, y]) - C.BASE
        ur /= np.linalg.norm(ur)
        ut = np.array([-ur[1], ur[0]])
        fr = C.frames(C.D2 / "dataset", e, "wrist", gf - 30, gf - 2, cache)
        P, I = [], []
        for k, img in enumerate(fr):
            b = C.blobs(C.red_mask(img), 200)
            if not b:
                continue
            a, (u, v), _, _ = max(b, key=lambda t: t[0])
            tp = tip(s[[gf - 30 + k], :5])[0]
            P.append([(tp - [x, y]) @ ut, (tp - [x, y]) @ ur])
            I.append([u, v])
        if len(P) < 10:
            continue
        P, I = np.array(P), np.array(I)
        X = np.column_stack([P, np.ones(len(P))])
        coef = np.linalg.lstsq(X, I, rcond=None)[0]      # (3,2): rows tan, rad, 1 ; cols u, v
        A = coef[:2].T                                    # 2×2: [u;v] per [tan, rad]
        span = np.ptp(P, axis=0)
        r2 = 1 - ((I - X @ coef) ** 2).sum(0) / ((I - I.mean(0)) ** 2).sum(0)
        # 정책 반응 (exp2 pre, wrist u/v ±1 cm 상당 px 이동)
        g = D[(D.ep == e) & (D.phase == "pre")].set_index("cond")
        if "wu+" not in g.index:
            continue
        pxcm = g.loc["wu+", "w_px_per_cm"]
        resp = np.array([[(g.loc["wu+", "tip_x"] - g.loc["wu-", "tip_x"]) / 2, (g.loc["wv+", "tip_x"] - g.loc["wv-", "tip_x"]) / 2],
                         [(g.loc["wu+", "tip_y"] - g.loc["wu-", "tip_y"]) / 2, (g.loc["wv+", "tip_y"] - g.loc["wv-", "tip_y"]) / 2]])
        resp = np.array([ut, ur]) @ resp                  # rows tan, rad ; cols per (pxcm px) shift in u, v
        dimg = np.eye(2) * pxcm                           # 편집한 영상 이동 (px), 열 = u, v
        dc = -np.linalg.solve(A, dimg)                    # 해당 큐브 이동 (cm, tan/rad), 열 = u, v
        G = resp @ np.linalg.inv(dc)
        rows.append(dict(ep=e, group=T.loc[e, "group"], n=len(P), span_tan=span[0], span_rad=span[1], r2_u=r2[0], r2_v=r2[1],
                         A_u_tan=A[0, 0], A_u_rad=A[0, 1], A_v_tan=A[1, 0], A_v_rad=A[1, 1], cond_A=np.linalg.cond(A),
                         G_tt=G[0, 0], G_tr=G[0, 1], G_rt=G[1, 0], G_rr=G[1, 1], roll_pre=s[gf - 30, 4]))
    W = pd.DataFrame(rows)
    W.to_csv(C.OUT / "exp2/wrist_axes.csv", index=False)
    good = W[(W.r2_u > 0.6) & (W.r2_v > 0.6) & (W.cond_A < 5)]
    print(f"episodes {len(W)}, well-conditioned A {len(good)}")
    print(good[["span_tan", "span_rad", "A_u_tan", "A_u_rad", "A_v_tan", "A_v_rad", "G_tt", "G_tr", "G_rt", "G_rr"]].median().round(2).to_string())
    for md, g in good.groupby(good.group.str[2]):
        print(md, "G_tt med %.2f IQR [%.2f, %.2f] | G_rr med %.2f IQR [%.2f, %.2f] (n %d)" % (
            g.G_tt.median(), g.G_tt.quantile(.25), g.G_tt.quantile(.75), g.G_rr.median(), g.G_rr.quantile(.25), g.G_rr.quantile(.75), len(g)))


def roll_model():
    """방법 2 (128편 모두): A 를 판마다 맞추지 않고, 잘 맞은 판에서 얻은 관계 'u 축 각도 ≈ 손목 roll − 5.5°' (u 는 반지름 쪽, v 는 접선 쪽)
    와 크기 w_px_per_cm(√넓이/2.5) 로 만든다. 그 뒤는 같은 계산 → G 행렬. 이상값 1."""
    import math
    T = pd.read_csv(C.OUT / "grasp_train.csv")
    D = pd.read_csv(C.OUT / "exp2/rows_eval.csv")
    W = pd.read_csv(C.OUT / "exp2/wrist_axes.csv")
    good = W[(W.r2_u > 0.6) & (W.r2_v > 0.6) & (W.cond_A < 5)]
    b1, b0 = np.polyfit(good.roll_pre, np.degrees(np.arctan2(good.A_u_tan, good.A_u_rad)), 1)
    sgn_v = np.sign(good.A_v_tan.median())       # v 축이 접선 + 쪽인지 − 쪽인지
    data = C.load_parquet(C.D2 / "dataset")
    rows = []
    for e in sorted(D.ep.unique()):
        g = D[(D.ep == e) & (D.phase == "pre")].set_index("cond")
        if "wu+" not in g.index:
            continue
        s, _ = data[e]
        gf = int(T.loc[e, "grasp_f"])
        x, y = T.loc[e, "cube_x"], T.loc[e, "cube_y"]
        ur = np.array([x, y]) - C.BASE
        ur /= np.linalg.norm(ur)
        ut = np.array([-ur[1], ur[0]])
        th = math.radians(b0 + b1 * s[gf - 30, 4])
        pxcm = g.loc["wu+", "w_px_per_cm"]
        # u 축 단위벡터 (tan, rad) = (sin th, cos th); v 축 = u 를 90° 돌린 것, 부호는 보정에서
        au = np.array([math.sin(th), math.cos(th)])
        av = sgn_v * np.array([math.cos(th), -math.sin(th)])
        A = pxcm * np.stack([au, av])            # rows u, v ; cols tan, rad
        resp = np.array([[(g.loc["wu+", "tip_x"] - g.loc["wu-", "tip_x"]) / 2, (g.loc["wv+", "tip_x"] - g.loc["wv-", "tip_x"]) / 2],
                         [(g.loc["wu+", "tip_y"] - g.loc["wu-", "tip_y"]) / 2, (g.loc["wv+", "tip_y"] - g.loc["wv-", "tip_y"]) / 2]])
        resp = np.array([ut, ur]) @ resp
        dc = -np.linalg.solve(A, np.eye(2) * pxcm)
        G = resp @ np.linalg.inv(dc)
        rows.append(dict(ep=e, group=T.loc[e, "group"], G_tt=G[0, 0], G_tr=G[0, 1], G_rt=G[1, 0], G_rr=G[1, 1]))
    R = pd.DataFrame(rows)
    R.to_csv(C.OUT / "exp2/wrist_gain_rollmodel.csv", index=False)
    print(f"roll model: u-angle = {b1:.2f}*roll + {b0:.1f}, v sign {sgn_v:+.0f}, n {len(R)}")
    rng = np.random.default_rng(0)
    for col in ("G_tt", "G_rr", "G_tr", "G_rt"):
        v = R[col].values
        bs = [np.median(v[rng.integers(0, len(v), len(v))]) for _ in range(2000)]
        print(f"  {col} median {np.median(v):.2f} [{np.percentile(bs, 2.5):.2f}, {np.percentile(bs, 97.5):.2f}]  "
              f"K {R[R.group.str[2] == 'K'][col].median():.2f}  R {R[R.group.str[2] == 'R'][col].median():.2f}")


if __name__ == "__main__":
    main()
    roll_model()
