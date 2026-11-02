"""라벨 확정 + 위치·에피소드 분리 fold (CPU 만). 입력 labels.csv → labels_v2.csv, folds.json, split_check.json

라벨 (wrist 영상, 640×480 px 기준)
  카메라는 고정 집게(fixed jaw)에 붙어 있다: 오른쪽 손가락 끝은 열림과 관계없이 (368, 304) ± 측정잡음. 왼쪽(움직이는 집게) 끝만 열림에 따라 움직인다.
  → 집게 기준점은 영상에서 고정이다. '정렬된' 큐브 위치 u*(d), v*(d) 는 사람 시연 파지 1 s 전 ~ 파지 프레임에서 맞춘
    큐브 중심 = a + b / √넓이 (거리에 따른 시차) 로 둔다.
  rel_u_cm, rel_v_cm = (큐브 중심 − 기준점) / (√넓이 / 2.5)       ← 영상 좌표계 (roll 보정 전)
  tan_cm, rad_cm     = roll 회전 (θ = 0.91·roll − 5.5°, exp2b)     ← 탁자 좌표계 (roll 보정 후)
                       = 큐브 − 집게 (+ tan = 큐브가 집게보다 로봇 왼쪽, + rad = 로봇에서 더 멂). exp2b 의 A 는 (집게 − 큐브) → 영상이라 부호를 뒤집는다.
  검증 (label_validity): 사람 시연에서 이 라벨이 그 뒤 실제 좌우 이동(파지 pan − 지금 pan, cm 환산)을 얼마나 설명하는지
  사용 조건: 큐브 있음, 테두리 안 닿음, 넓이 ≥ 3000 px (멀어서 작은 것 제외), 닫힘 3 s 전 ~ 닫힘.
Fold (5개)
  Known: K 8곳을 2곳씩 4묶음 + 묶음 없음 1개 → fold 0–3 의 test 에 K 2곳씩
  Random: 큐브 위치 (x, y) k-means 5군집 → fold f 의 test 에 군집 f
  train 에서 빼는 것: test 판 + test 큐브 위치 3 cm 안에 큐브가 있던 판 (위치 완충)
  같은 판의 프레임은 한 쪽에만 들어간다 (판 단위로 나눔).
외부 test: d2 실물 평가 롤아웃 5판 (정책이 만든 상태, 새 위치) — 같은 라벨 규칙.
"""
import json
import math
from pathlib import Path

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path.home() / "so101_runs/main_k8/d2/diag_grasp_bias"))
import common as C  # noqa: E402

OUT = Path(__file__).resolve().parent
KPAIRS = [("K1", "K6"), ("K2", "K7"), ("K3", "K4"), ("K5", "K8")]
BUFFER_CM = 3.0
MIN_AREA = 3000


def kmeans(X, k, seed=0, it=100):
    rng = np.random.default_rng(seed)
    C = X[rng.choice(len(X), k, replace=False)]
    for _ in range(it):
        lab = np.argmin(((X[:, None] - C[None]) ** 2).sum(-1), 1)
        C2 = np.array([X[lab == j].mean(0) if (lab == j).any() else C[j] for j in range(k)])
        if np.allclose(C2, C):
            break
        C = C2
    return lab


def main():
    D = pd.read_csv(OUT / "labels.csv", low_memory=False)
    D["border"] = D.border.astype("boolean")
    use = D.cu.notna() & (D.border == False) & (D.carea >= MIN_AREA)  # noqa: E712
    D["pxcm"] = np.sqrt(D.carea) / 2.5
    ref = D[use & (D.t_to_close <= 1.0)]
    inv = 1 / np.sqrt(ref.carea)
    bu, bv = np.polyfit(inv, ref.cu, 1), np.polyfit(inv, ref.cv, 1)
    D["u_star"] = np.polyval(bu, 1 / np.sqrt(D.carea))
    D["v_star"] = np.polyval(bv, 1 / np.sqrt(D.carea))
    D["rel_u_cm"] = (D.cu - D.u_star) / D.pxcm
    D["rel_v_cm"] = (D.cv - D.v_star) / D.pxcm
    th = np.radians(-5.5 + 0.91 * D.roll)
    # u 축 → (sin θ, cos θ), v 축 → −(cos θ, −sin θ)   (exp2b roll_model 과 같은 규약)
    D["tan_cm"] = -(D.rel_u_cm * np.sin(th) - D.rel_v_cm * np.cos(th))
    D["rad_cm"] = -(D.rel_u_cm * np.cos(th) + D.rel_v_cm * np.sin(th))
    D["probe_ok"] = use & (D.t_to_close <= 3.0)
    # fold
    eps = D.groupby("ep").agg(group=("group", "first"), K=("K", "first"), x=("cube_x", "first"), y=("cube_y", "first")).reset_index()
    # K 는 좌표로 정한다 (grasp_train.csv 의 K 열은 layout_id 파싱 오류로 비어 있음): Known 판의 큐브가 K 중심 2 cm 안
    KN = C.load_known()
    def nearest(x, y):
        k = min(KN, key=lambda q: math.hypot(x - KN[q][0], y - KN[q][1]))
        return k if math.hypot(x - KN[k][0], y - KN[k][1]) <= 2.0 else ""
    eps["K"] = [nearest(x, y) if g.endswith("K") else "" for g, x, y in zip(eps.group, eps.x, eps.y)]
    D["K"] = D.ep.map(dict(zip(eps.ep, eps.K)))
    R = eps[eps.group.str.endswith("R")]
    rl = kmeans(R[["x", "y"]].values, 5)
    eps["rclu"] = -1
    eps.loc[R.index, "rclu"] = rl
    folds = []
    for f in range(5):
        test = eps[((eps.K != "") & eps.K.isin(KPAIRS[f] if f < 4 else ())) | (eps.rclu == f)]
        tp = test[["x", "y"]].values
        d = np.min(np.hypot(eps.x.values[:, None] - tp[None, :, 0], eps.y.values[:, None] - tp[None, :, 1]), 1)
        train = eps[(~eps.ep.isin(test.ep)) & (d > BUFFER_CM)]
        folds.append(dict(fold=f, test_eps=test.ep.tolist(), train_eps=train.ep.tolist(),
                          dropped_buffer=int(len(eps) - len(test) - len(train)), test_K=list(KPAIRS[f]) if f < 4 else [],
                          test_random_cluster=f))
    D.to_csv(OUT / "labels_v2.csv", index=False)
    json.dump(dict(ref_fit_u=bu.tolist(), ref_fit_v=bv.tolist(), buffer_cm=BUFFER_CM, min_area=MIN_AREA, folds=folds),
              open(OUT / "folds.json", "w"), indent=1)
    P = D[D.probe_ok]
    chk = dict(probe_frames=int(len(P)), probe_eps=int(P.ep.nunique()))
    for lo, hi in ((0, 1), (1, 2), (2, 3)):
        d = P[(P.t_to_close > lo - 1e-9) & (P.t_to_close <= hi)]
        chk[f"label_sd_{lo}_{hi}s"] = dict(n=len(d), rel_u=float(d.rel_u_cm.std()), rel_v=float(d.rel_v_cm.std()),
                                           tan=float(d.tan_cm.std()), rad=float(d.rad_cm.std()),
                                           abs_rel_u_p90=float(d.rel_u_cm.abs().quantile(.9)), abs_tan_p90=float(d.tan_cm.abs().quantile(.9)))
    chk["corr_rel_u_vs_tan"] = float(P[["rel_u_cm", "tan_cm"]].corr().iloc[0, 1])
    chk["corr_rel_v_vs_tan"] = float(P[["rel_v_cm", "tan_cm"]].corr().iloc[0, 1])
    chk["roll_sd_probe_frames"] = float(P.roll.std())
    for fo in folds:
        te = P[P.ep.isin(fo["test_eps"])]
        tr = P[P.ep.isin(fo["train_eps"])]
        chk[f"fold{fo['fold']}"] = dict(test_eps=len(fo["test_eps"]), train_eps=len(fo["train_eps"]), dropped=fo["dropped_buffer"],
                                       test_frames=len(te), train_frames=len(tr), overlap_eps=len(set(fo["test_eps"]) & set(fo["train_eps"])))
    T = pd.read_csv(C.OUT / "grasp_train.csv")[["ep", "s_shoulder_pan", "range_cm"]].rename(columns={"s_shoulder_pan": "pan_close"})
    V = P[P.t_to_close >= 0.5].merge(T, on="ep")
    V["future_lat_cm"] = -(V.pan_close - V.s_shoulder_pan) * np.pi / 180 * V.range_cm   # + = 앞으로 로봇 왼쪽으로 감
    for lo, hi in ((0.5, 1), (1, 2), (2, 3)):
        d = V[(V.t_to_close > lo) & (V.t_to_close <= hi)]
        X = np.column_stack([np.ones(len(d)), d.rel_u_cm, d.rel_v_cm])
        b = np.linalg.lstsq(X, d.future_lat_cm, rcond=None)[0]
        r2_img = 1 - ((d.future_lat_cm - X @ b) ** 2).sum() / ((d.future_lat_cm - d.future_lat_cm.mean()) ** 2).sum()
        ct = float(np.corrcoef(d.tan_cm, d.future_lat_cm)[0, 1])
        chk[f"label_validity_{lo}_{hi}s"] = dict(n=len(d), corr_tan=ct, r2_tan=ct ** 2, r2_image_uv_linear=float(r2_img),
                                                 future_lat_sd_cm=float(d.future_lat_cm.std()))
    chk["known_eps_per_K"] = eps[eps.K != ""].K.value_counts().sort_index().to_dict()
    chk["known_eps_unassigned"] = int(((eps.K == "") & eps.group.str.endswith("K")).sum())
    json.dump(chk, open(OUT / "split_check.json", "w"), indent=1)
    print(json.dumps(chk, indent=1))


if __name__ == "__main__":
    main()
