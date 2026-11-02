"""분석 5 (CPU): 학습 데이터(d2 256편)에 wrist roll × 큐브 상대 위치 조합이 얼마나 다양한가.
읽기만 함: vision_probe/labels_v2.csv (닫힘 3 s 전 ~ 닫힘, probe_ok 7,810 프레임), f1_features/meta.csv (평가 프레임),
f1_results/eval_label_qc.csv, d2 parquet (사람 집게 끝 이후 이동). 로봇·GPU 안 씀.

측정
  M1  roll 분포 (닫힘 1 s 전, 판 단위) · 판 안 roll 변화 (닫힘 3 s 전 → 닫힘)
  M2  roll 이 다른 변수로 얼마나 정해지는가: 판 단위 roll ~ 큐브 위치 (x, y) · 그룹 (5-fold CV R², kNN/선형)
  M3  칸 표: roll 15° 칸 × 탁자 접선 tan 0.5 cm 칸, 영상 축 각도 φ_img 45° 칸 — 칸마다 프레임 수 · 판 수
  M4  같은 탁자 tan 에서 영상 축 위치가 roll 에 따라 얼마나 달라지는가 (roll 조건부 매핑을 배울 재료):
      판 단위 회귀 rel_u, rel_v ~ tan, rad 에서 roll 이 더하는 설명력
  M5  사람 행동 대상: 50 프레임(1.67 s, chunk 길이) 뒤 집게 끝 접선 이동 ~ 영상 축 (rel_u, rel_v) vs roll 회전 (tan) — R², 기울기
  M6  평가 프레임 (조건 통과 303) 이웃 수: train 에서 |Δroll| ≤ 10°, |Δtan| ≤ 0.5, |Δrad| ≤ 0.5 cm 인 판 수
  M7  roll 토큰 자릿수 경계 (bin 9/10, 99/100 → −52.9°, −13.2°) 근처 (±2°) 프레임 비율, train vs eval
  M8  학습 프레임 구성: 판 길이 중 닫힘 3 s 전 ~ 닫힘, 시작 ~ 닫힘 3 s 전, 닫힘 뒤 비율 (분석 6 의 표본 가중 설계용)
출력: c5_coverage.json, c5_cells_*.csv, c5_eval_neighbors.csv
사용: PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python c5_coverage.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HOME = Path.home()
D2 = HOME / "so101_runs/main_k8/d2"
VP = D2 / "vision_probe"
OUT = D2 / "action_bottleneck"
sys.path.insert(0, str(D2 / "diag_grasp_bias"))
import common as C  # noqa: E402

FPS = 30
CHUNK = 50
Q01, Q99 = -57.01099, 55.163967          # d2 preprocessor roll q01/q99 (c3_state_path.json)


def tip_fn():
    fit = json.load(open(D2 / "diag_grasp_bias/fk_fit.json"))
    Rm, tv = np.array(fit["R"]), np.array(fit["t"])

    def tip(j5):
        p, _ = C.fk_xy(j5)
        return (Rm @ (p[:, :2] * 100).T).T + tv
    return tip


def cv_r2(X, y, k=5, seed=0, knn=None):
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(y))
    pred = np.zeros(len(y))
    for f in range(k):
        te = idx[f::k]
        tr = np.setdiff1d(idx, te)
        if knn:
            d = ((X[te, None, :] - X[None, tr, :]) ** 2).sum(-1)
            nn = np.argsort(d, 1)[:, :knn]
            pred[te] = y[tr][nn].mean(1)
        else:
            A = np.column_stack([X[tr], np.ones(len(tr))])
            w = np.linalg.lstsq(A, y[tr], rcond=None)[0]
            pred[te] = np.column_stack([X[te], np.ones(len(te))]) @ w
    return float(1 - ((y - pred) ** 2).sum() / ((y - y.mean()) ** 2).sum())


def lin_r2(X, y):
    A = np.column_stack([X, np.ones(len(y))])
    w = np.linalg.lstsq(A, y, rcond=None)[0]
    r = y - A @ w
    return float(1 - (r ** 2).sum() / ((y - y.mean()) ** 2).sum()), w


def main():
    res = {}
    L = pd.read_csv(VP / "labels_v2.csv")
    P = L[L.probe_ok].copy()
    P["phi_img"] = np.degrees(np.arctan2(P.rel_v_cm, P.rel_u_cm))
    T = pd.read_csv(D2 / "diag_grasp_bias/grasp_train.csv")
    data = C.load_parquet(D2 / "dataset")
    tip = tip_fn()

    # M1 판 단위 roll
    pre = P.loc[(P.t_to_close - 1.0).abs().groupby(P.ep).idxmin()]
    res["M1_roll_pre_1s"] = pre.roll.describe().round(2).to_dict()
    res["M1_roll_pre_by_group"] = pre.groupby("group").roll.describe()[["count", "mean", "std", "min", "max"]].round(1).to_dict("index")
    d_roll = []
    for e, g in P.groupby("ep"):
        g = g.sort_values("frame")
        d_roll.append(g.roll.iloc[-1] - g.roll.iloc[0])
    res["M1_roll_change_last3s_abs"] = pd.Series(np.abs(d_roll)).describe().round(2).to_dict()

    # M2 roll 을 위치 · 그룹으로 예측
    X = pre[["cube_x", "cube_y"]].values
    y = pre.roll.values
    G = pd.get_dummies(pre.group).values.astype(float)
    res["M2_roll_from_pos"] = dict(n_eps=len(pre), lin=cv_r2(X, y), knn5=cv_r2(X, y, knn=5),
                                   lin_pos_group=cv_r2(np.column_stack([X, G]), y))
    # 큐브 계획 각도 (layout.csv angles, 'K7:45' / 'K5:R30' → 45 / 30) — 면 정렬이면 90° 주기
    pos = C.d2_positions()
    yaw = {}
    for e, p in enumerate(pos):
        a = p["angles"].split(":")[-1].lstrip("R") if p["angles"] else ""
        yaw[e] = float(a) if a.lstrip("-").replace(".", "").isdigit() else np.nan
    pre = pre.assign(yaw=pre.ep.map(yaw))
    ok = pre.yaw.notna().values
    Y4 = np.column_stack([np.sin(np.radians(4 * pre.yaw[ok])), np.cos(np.radians(4 * pre.yaw[ok]))])
    res["M2_roll_from_yaw"] = dict(n_eps=int(ok.sum()), yaw_values=sorted(pre.yaw[ok].unique().tolist()),
                                   lin_yaw90=cv_r2(Y4, y[ok]), lin_yaw90_pos=cv_r2(np.column_stack([Y4, X[ok]]), y[ok]),
                                   lin_yaw_raw=cv_r2(pre.yaw[ok].values[:, None], y[ok]))

    # M3 칸 표
    rb = np.arange(-60, 61, 15)
    tb = np.arange(-2.5, 2.01, 0.5)
    pb = np.arange(-180, 181, 45)
    P["roll_bin"] = pd.cut(P.roll, rb)
    P["tan_bin"] = pd.cut(P.tan_cm, tb)
    P["phi_bin"] = pd.cut(P.phi_img, pb)
    near = P[P.t_to_close <= 1.5]
    for nm, col in (("tan", "tan_bin"), ("phi", "phi_bin")):
        ep_cnt = near.groupby(["roll_bin", col], observed=False).ep.nunique().unstack(fill_value=0)
        ep_cnt.to_csv(OUT / f"c5_cells_roll_x_{nm}_episodes.csv")
        fr_cnt = near.groupby(["roll_bin", col], observed=False).size().unstack(fill_value=0)
        fr_cnt.to_csv(OUT / f"c5_cells_roll_x_{nm}_frames.csv")
        res[f"M3_cells_{nm}"] = dict(n_cells=int(ep_cnt.size), cells_ge5eps=int((ep_cnt >= 5).values.sum()),
                                     cells_ge1ep=int((ep_cnt >= 1).values.sum()), table_eps=ep_cnt.astype(int).values.tolist(),
                                     rows=[str(i) for i in ep_cnt.index], cols=[str(c) for c in ep_cnt.columns])
    # 영상 축 오프셋 크기 분포
    mag = np.hypot(P.rel_u_cm, P.rel_v_cm)
    res["M3_offset_mag_cm"] = mag.describe(percentiles=[.5, .9, .99]).round(2).to_dict()

    # M4 영상 축 위치 ~ 탁자 위치 (+ roll)
    base = np.column_stack([P.tan_cm, P.rad_cm])
    # (tan, rad) 는 영상 축을 roll 로 돌려 정의했으므로 roll 을 넣은 R² 는 정의상 1 — roll 없이만 잰다
    res["M4_img_from_table_without_roll_r2"] = {c: lin_r2(base, P[c].values)[0] for c in ("rel_u_cm", "rel_v_cm")}
    res["M4_corr_roll_vs"] = {c: float(np.corrcoef(P.roll, P[c])[0, 1]) for c in ("rel_u_cm", "rel_v_cm", "tan_cm", "rad_cm", "phi_img")}

    # M5 사람 이후 이동 (집게 끝, 접선/반지름) ~ 영상 축 vs roll 회전
    fut = []
    for _, r in P.iterrows():
        s, _ = data[int(r.ep)]
        f0 = int(r.frame)
        f1 = min(f0 + CHUNK, f0 + int(round(r.t_to_close * FPS)), len(s) - 1)   # 닫힘 뒤(들어 올림)는 빼고
        x, y = r.cube_x, r.cube_y
        ur = np.array([x, y]) - C.BASE
        ur /= np.linalg.norm(ur)
        ut = np.array([-ur[1], ur[0]])
        tp = tip(s[[f0, f1], :5])
        d = tp[1] - tp[0]
        fut.append((d @ ut, d @ ur, (tp[0] - [x, y]) @ ut, (tp[0] - [x, y]) @ ur))
    F = np.array(fut)
    P["fut_tan"], P["fut_rad"], P["tip_tan"], P["tip_rad"] = F.T
    m5 = {}
    for lo, hi in ((0, 1), (1, 2), (2, 3), (0, 3)):
        d = P[(P.t_to_close > lo) & (P.t_to_close <= hi)] if lo else P[P.t_to_close <= hi]
        Ximg = d[["rel_u_cm", "rel_v_cm"]].values
        Xtab = d[["tan_cm", "rad_cm"]].values
        r_img, _ = lin_r2(Ximg, d.fut_tan.values)
        r_tab, w_tab = lin_r2(Xtab, d.fut_tan.values)
        r_img_rad, _ = lin_r2(Ximg, d.fut_rad.values)
        r_tab_rad, w_tab_rad = lin_r2(Xtab, d.fut_rad.values)
        m5[f"{lo}-{hi}s"] = dict(n=len(d), fut_tan_sd=float(d.fut_tan.std()), r2_tan_from_img=r_img, r2_tan_from_tab=r_tab,
                                 slope_tan_on_tan=float(w_tab[0]), r2_rad_from_img=r_img_rad, r2_rad_from_tab=r_tab_rad,
                                 slope_rad_on_rad=float(w_tab_rad[1]))
    res["M5_human_future_motion"] = m5

    # M6 평가 프레임 이웃
    M = pd.read_csv(VP / "f1_features/meta.csv")
    Ev = M[(M.src == "eval") & M.valid].reset_index(drop=True)
    qc = pd.read_csv(VP / "f1_results/eval_label_qc.csv")
    Ev = Ev.merge(qc, on="row", how="left")
    Ev = Ev[(Ev.carea >= 3000) & (~Ev.border.astype(bool))].copy()
    tr = P[["ep", "roll", "tan_cm", "rad_cm"]].values
    nb = []
    for _, r in Ev.iterrows():
        m = (np.abs(tr[:, 1] - r.roll) <= 10) & (np.abs(tr[:, 2] - r.tan_cm) <= 0.5) & (np.abs(tr[:, 3] - r.rad_cm) <= 0.5)
        m_img = (np.abs(P.roll.values - r.roll) <= 10) & (np.abs(P.rel_u_cm.values - r.rel_u_cm) <= 0.5) & (np.abs(P.rel_v_cm.values - r.rel_v_cm) <= 0.5)
        m_tab_only = (np.abs(tr[:, 2] - r.tan_cm) <= 0.5) & (np.abs(tr[:, 3] - r.rad_cm) <= 0.5)
        nb.append((len(np.unique(tr[m, 0])), len(np.unique(P.ep.values[m_img])), len(np.unique(tr[m_tab_only, 0]))))
    Ev["nb_eps_tab_roll"], Ev["nb_eps_img_roll"], Ev["nb_eps_tab_only"] = np.array(nb).T
    Ev[["row", "run", "event", "t_to_close", "roll", "rel_u_cm", "rel_v_cm", "tan_cm", "rad_cm", "nb_eps_tab_roll", "nb_eps_img_roll",
        "nb_eps_tab_only"]].to_csv(OUT / "c5_eval_neighbors.csv", index=False)
    res["M6_eval_neighbors"] = dict(n=len(Ev), roll_eval=Ev.roll.describe().round(1).to_dict(),
                                   frac_zero_tab_roll=float((Ev.nb_eps_tab_roll == 0).mean()),
                                   frac_zero_img_roll=float((Ev.nb_eps_img_roll == 0).mean()),
                                   frac_zero_tab_only=float((Ev.nb_eps_tab_only == 0).mean()),
                                   median_tab_roll=float(Ev.nb_eps_tab_roll.median()))
    # 같은 지표, train 끼리 (판 하나 빼고) 기준값
    rng = np.random.default_rng(0)
    smp = P.sample(500, random_state=0)
    nbt = []
    for _, r in smp.iterrows():
        o = tr[:, 0] != r.ep
        m = o & (np.abs(tr[:, 1] - r.roll) <= 10) & (np.abs(tr[:, 2] - r.tan_cm) <= 0.5) & (np.abs(tr[:, 3] - r.rad_cm) <= 0.5)
        nbt.append(len(np.unique(tr[m, 0])))
    nbt = np.array(nbt)
    res["M6_train_loo_neighbors"] = dict(n=500, frac_zero=float((nbt == 0).mean()), median=float(np.median(nbt)))
    del rng

    # M7 roll 토큰 자릿수 경계
    def bnd(r):
        b = [Q01 + 10 * (Q99 - Q01) / 256, Q01 + 100 * (Q99 - Q01) / 256]
        return float(np.mean(np.min(np.abs(np.asarray(r)[:, None] - np.array(b)[None]), 1) <= 2.0))
    res["M7_digit_boundary_deg"] = [Q01 + 10 * (Q99 - Q01) / 256, Q01 + 100 * (Q99 - Q01) / 256]
    res["M7_frac_within2deg"] = dict(train_probe=bnd(P.roll), train_pre=bnd(pre.roll), eval=bnd(Ev.roll))

    # M8 학습 프레임 구성
    tot = dict(before=0, pre3=0, after=0)
    for e, (s, _) in data.items():
        gf = int(T.loc[e, "grasp_f"])
        tot["pre3"] += min(gf, 3 * FPS)
        tot["before"] += max(gf - 3 * FPS, 0)
        tot["after"] += len(s) - gf
    n = sum(tot.values())
    res["M8_frame_share"] = {k: round(v / n, 4) for k, v in tot.items()} | {"n_frames": n}
    lens = np.array([len(s) for s, _ in data.values()])
    res["M8_episode_len_s"] = (pd.Series(lens / FPS).describe().round(1)).to_dict()

    json.dump(res, open(OUT / "c5_coverage.json", "w"), indent=1, ensure_ascii=False, default=str)
    for k, v in res.items():
        if k.startswith("M3_cells"):
            print(k, {kk: vv for kk, vv in v.items() if kk != "table_eps"})
            print(pd.DataFrame(v["table_eps"], index=v["rows"], columns=v["cols"]).to_string())
        else:
            print(k, json.dumps(v, ensure_ascii=False, default=str)[:900])


if __name__ == "__main__":
    main()
