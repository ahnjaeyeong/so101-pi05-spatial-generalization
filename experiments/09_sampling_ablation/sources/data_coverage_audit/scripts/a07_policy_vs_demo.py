"""07 d2 정책 실물 실행 vs 사람 시연 (읽기만 함). 입력: d2/eval/rollouts/*/dataset (2 실행, 5판), diag_grasp_bias/grasp_eval.csv (닫힘 이벤트 · 큐브 위치),
action_bottleneck/c5_eval_neighbors.csv (평가 wrist 라벨 프레임), tables/a02_frames.parquet, a02_events.csv
출력 tables/a07_*.csv/json, _facts/07.md

정책 판의 큐브 위치 = front 시작 화면 추정 (grasp_eval start_x/y). 큐브 중심 기준 e_t, e_r (ac.tcp; 사람 파지 순간 바닥 SD 0.59 / 0.79 cm).
첫 닫힘 = close_events 첫 이벤트. 닫힘 성공 = 닫힘 뒤 5–20 프레임 그리퍼 state 중앙값 ≥ 5 (사람 256편 최소 11.3).
사람 기준 분포 = 256편 onset → 첫 파지, 같은 '첫 닫힘까지 남은 시간' 의 e_t, e_r, z, (pan − 기대 pan), roll − 필요 roll.
이탈 = 정책 프레임의 과제 상대 특징 (pan 오차 °/2.15, e_r cm/0.8, z cm/1, 시간 진행률) 이 사람 프레임 최근접 거리의 사람 판-빼기 99% 를 넘은 첫 시각.
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python a07_policy_vs_demo.py
"""
import glob
import json

import numpy as np
import pandas as pd

import ac

RUNS = sorted(glob.glob(str(ac.D2 / "eval/rollouts/2026*")))


def load_run(r):
    df = pd.concat([pd.read_parquet(f) for f in glob.glob(f"{r}/dataset/data/*/*.parquet")])
    out = {}
    for e, g in df.groupby("episode_index"):
        g = g.sort_values("frame_index")
        out[int(e)] = (np.stack(g["observation.state"].values).astype(float), np.stack(g["action"].values).astype(float))
    return out


def feats(s, cx, cy, c, on):
    """과제 상대 특징 (프레임별)."""
    P = ac.tcp(s)
    ut, ur = ac.axes(cx, cy)
    rel = P[:, :2] - [cx, cy]
    pan_exp = ac.PAN_SIGN * float(ac.bearing(cx, cy)) + ac.PAN_OFF
    prog = (np.arange(len(s)) - on) / max(1, c - on)
    return pd.DataFrame(dict(e_t=rel @ ut, e_r=rel @ ur, z=P[:, 2], pan_err=s[:, 0] - pan_exp, roll=s[:, 4], prog=prog,
                             t_to_close=(c - np.arange(len(s))) / ac.FPS))


def cover_times(pan, on, c, pan_exp):
    """onset 뒤 pan 이 필요 회전 (pan_exp − pan[on]) 의 50 / 90% 를 처음 넘긴 시간 (s). 필요 회전 < 5° 면 nan."""
    need = pan_exp - pan[on]
    if abs(need) < 5:
        return np.nan, np.nan
    frac = (pan[on:c + 1] - pan[on]) / need
    out = []
    for k in (0.5, 0.9):
        i = np.where(frac >= k)[0]
        out.append(i[0] / ac.FPS if len(i) else np.nan)
    return tuple(out)


def main():
    W = pd.read_parquet(ac.TAB / "a02_frames.parquet")
    E = pd.read_csv(ac.TAB / "a02_events.csv")
    T = pd.read_csv(ac.TAB / "a01_cube_table.csv")
    GE = pd.read_csv(ac.D2 / "diag_grasp_bias/grasp_eval.csv")
    out = {}
    # 사람 특징
    H = []
    for e in range(256):
        g = W[W.ep == e]
        s = g[[f"s_{j}" for j in ac.JOINTS]].values
        f = feats(s, T.cube_x[e], T.cube_y[e], int(E.grasp[e]), int(E.onset[e]))
        f["ep"] = e
        H.append(f.iloc[int(E.onset[e]):int(E.grasp[e]) + 1])
    H = pd.concat(H, ignore_index=True)
    sc = np.array([2.15, 0.8, 1.0, 0.25])
    cols = ["pan_err", "e_r", "z", "prog"]
    Hx = H[cols].values / sc
    # 사람 판-빼기 최근접 거리 (표본 3000 프레임)
    rs = np.random.default_rng(0)
    idx = rs.choice(len(H), 3000, replace=False)
    loo = []
    for i in idx:
        m = H.ep.values != H.ep.values[i]
        loo.append(np.sqrt(((Hx[m] - Hx[i]) ** 2).sum(1)).min())
    thr99 = float(np.percentile(loo, 99))
    thr95 = float(np.percentile(loo, 95))
    # 사람 시간별 분포 (첫 파지까지 남은 시간)
    band = H.assign(tb=(H.t_to_close * 2).round() / 2).groupby("tb").agg(e_t_p5=("e_t", lambda s: s.quantile(.05)), e_t_p50=("e_t", "median"),
                                                                       e_t_p95=("e_t", lambda s: s.quantile(.95)), pan_err_p5=("pan_err", lambda s: s.quantile(.05)),
                                                                       pan_err_p95=("pan_err", lambda s: s.quantile(.95)), z_p5=("z", lambda s: s.quantile(.05)),
                                                                       z_p95=("z", lambda s: s.quantile(.95)), n=("ep", "nunique"))
    band.to_csv(ac.TAB / "a07_human_band.csv")
    rows, trace = [], []
    for r in RUNS:
        run = r.split("/")[-1]
        D = load_run(r)
        for e, (s, a) in D.items():
            ge = GE[(GE.run == run) & (GE.ep == e)].sort_values("event")
            cx, cy = float(ge.start_x.iloc[0]), float(ge.start_y.iloc[0])
            g = s[:, 5]
            cev = ac.C.close_events(g)
            on = ac.onset(a[:, :5], 2.0) or 0
            c = cev[0] if cev else len(s) - 1
            holds = [float(np.median(g[k + 5:k + 21])) for k in cev]
            f = feats(s, cx, cy, c, on)
            Fx = f[cols].values / sc
            d = np.array([np.sqrt(((Hx - x) ** 2).sum(1)).min() for x in Fx[on:c + 1]])
            ex = np.where(d > thr99)[0]
            first_exit = on + int(ex[0]) if len(ex) else None
            pan = s[:, 0]
            pan_exp = ac.PAN_SIGN * float(ac.bearing(cx, cy)) + ac.PAN_OFF
            pm = np.where(np.abs(pan[on:c + 1] - pan[on]) > 1.0)[0]
            fpm = on + int(pm[0]) if len(pm) else on
            sub1 = ac.first_submovement(pan, fpm, c)
            dK = min(np.hypot(cx - kx, cy - ky) for kx, ky in ac.KNOWN.values())
            dtr = float(np.min(np.hypot(T.cube_x - cx, T.cube_y - cy)))
            # 이탈 시점의 특징
            fe = f.iloc[first_exit] if first_exit is not None else None
            t50, t90 = cover_times(pan, on, c, pan_exp)
            dh = np.hypot(f.e_t.values, f.e_r.values)
            imin = on + int(np.argmin(dh[on:c + 1]))
            rows.append(dict(run=run[16:], ep=e, pan_t50_s=t50, pan_t90_s=t90, min_dist_cm=dh[imin], min_dist_at_s=(imin - on) / ac.FPS, cube=f"({cx:.1f}, {cy:.1f})", dist_K=dK, dist_train=dtr, n_closes=len(cev),
                             first_close_hold=holds[0] if holds else np.nan, any_hold=bool(any(h >= 5 for h in holds)),
                             onset_s=on / ac.FPS, first_close_s=c / ac.FPS, approach_s=(c - on) / ac.FPS,
                             pan_needed=pan_exp - pan[on], pan_sub1=pan[sub1] - pan[on], pan_sub1_end_s=(sub1 - on) / ac.FPS,
                             pan_err_at_sub1=pan[sub1] - pan_exp, pan_err_at_close=pan[c] - pan_exp, e_t_close=f.e_t[c], e_r_close=f.e_r[c],
                             roll_close=s[c, 4], z_close=f.z[c],
                             exit_s_after_onset=(first_exit - on) / ac.FPS if first_exit is not None else np.nan,
                             exit_t_to_close=(c - first_exit) / ac.FPS if first_exit is not None else np.nan,
                             exit_pan_err=fe.pan_err if fe is not None else np.nan, exit_e_r=fe.e_r if fe is not None else np.nan,
                             exit_z=fe.z if fe is not None else np.nan, exit_prog=fe.prog if fe is not None else np.nan,
                             frac_frames_outside=float((d > thr99).mean())))
            tt = f.iloc[on:c + 1].copy()
            tt["run"], tt["ep"], tt["nn_dist"] = run, e, d
            trace.append(tt)
    R = pd.DataFrame(rows)
    TR = pd.concat(trace, ignore_index=True)
    TR.to_csv(ac.TAB / "a07_policy_trace.csv", index=False)
    R.to_csv(ac.TAB / "a07_policy_episodes.csv", index=False)
    # 사람 같은 지표 (비교)
    Hs = dict(pan_err_close_sd=float(np.std(E.pan_c - T.pan_expected)), pan_err_close_abs_p95=float(np.percentile(np.abs(E.pan_c - T.pan_expected), 95)),
              e_t_close_abs_p95=float(np.percentile(np.abs(E.e_t_c), 95)), sub1_err_abs_med=float(np.median(np.abs(E.pan_on + E.pan_sub1_amount - T.pan_expected))),
              sub1_err_abs_p95=float(np.percentile(np.abs(E.pan_on + E.pan_sub1_amount - T.pan_expected), 95)),
              approach_s_med=float(((E.grasp - E.onset) / ac.FPS).median()), approach_s_max=float(((E.grasp - E.onset) / ac.FPS).max()))
    ht = np.array([cover_times(W[W.ep == e].s_shoulder_pan.values, int(E.onset[e]), int(E.grasp[e]), float(T.pan_expected[e])) for e in range(256)])
    Hs.update(pan_t50_med=float(np.nanmedian(ht[:, 0])), pan_t50_p95=float(np.nanpercentile(ht[:, 0], 95)), pan_t90_med=float(np.nanmedian(ht[:, 1])),
              pan_t90_p95=float(np.nanpercentile(ht[:, 1], 95)), pan_t90_max=float(np.nanmax(ht[:, 1])), pan_t90_nan=int(np.isnan(ht[:, 1]).sum()))
    # 평가 wrist 라벨 프레임의 이웃 (기존 c5)
    NB = pd.read_csv(ac.D2 / "action_bottleneck/c5_eval_neighbors.csv")
    nb = dict(n=len(NB), frac_zero_tab_roll=float((NB.nb_eps_tab_roll == 0).mean()), frac_zero_tab_only=float((NB.nb_eps_tab_only == 0).mean()),
              tan_abs_p50=float(NB.tan_cm.abs().median()), tan_abs_p90=float(NB.tan_cm.abs().quantile(.9)),
              frac_tan_beyond_human_p99=float((NB.tan_cm.abs() > 1.46).mean()))
    out.update(thr99=thr99, thr95=thr95, human=Hs, c5_eval_neighbors=nb)
    json.dump(out, open(ac.TAB / "a07_policy_vs_demo.json", "w"), indent=1)
    t = ["## 측정 사실 (스크립트 생성: `scripts/a07_policy_vs_demo.py`)\n",
         f"d2 020000 실물 실행 기록: {len(RUNS)} 실행 · {len(R)} 판 (`eval/rollouts/`). 둘 다 RTC h20 · steps 5, 하나는 arm_filter. 성공/실패 판정은 기록되지 않았다 (평가_명령.md). "
         "그 밖의 d2 실물 평가 (eval_ui) 는 없다.\n",
         "### 7.1 판별 요약\n",
         "dist_K / dist_train = 큐브에서 가장 가까운 K 중심 / 학습 큐브까지 (cm). pan_needed = 기대 pan − onset pan. pan_sub1 = 첫 하위 움직임 pan 이동. pan_err = pan − 기대 pan (°). "
         "pan_t50/t90 = onset 뒤 pan 이 필요 회전의 50/90% 를 처음 넘긴 시간 (s). min_dist = 첫 닫힘 전 큐브-TCP 수평 거리 최소 (cm) 와 그 시각. first_close_hold = 첫 닫힘 뒤 그리퍼 state (≥ 5 면 무언가 쥠, 사람 최소 11.3). exit_* = 사람 상태 분포 이탈 첫 시각과 그때 특징.\n",
         "(a) 위치 · 결과\n",
         ac.md_table(R[["run", "ep", "cube", "dist_K", "dist_train", "n_closes", "first_close_hold", "any_hold", "pan_err_at_close", "e_t_close", "e_r_close", "roll_close", "z_close"]],
                     {"ep": "{:.0f}", "n_closes": "{:.0f}"}), "\n",
         "(b) 접근 시간 · pan\n",
         ac.md_table(R[["run", "ep", "onset_s", "approach_s", "pan_needed", "pan_t50_s", "pan_t90_s", "pan_sub1", "pan_sub1_end_s", "pan_err_at_sub1", "min_dist_cm", "min_dist_at_s"]],
                     {"ep": "{:.0f}"}), "\n",
         "(c) 사람 분포 이탈\n",
         ac.md_table(R[["run", "ep", "exit_s_after_onset", "exit_t_to_close", "exit_pan_err", "exit_e_r", "exit_z", "exit_prog", "frac_frames_outside"]],
                     {"ep": "{:.0f}", "frac_frames_outside": "{:.0%}"}), "\n",
         "사람 256편 같은 지표: " + ", ".join(f"{k} {v:.2f}" for k, v in Hs.items()) + "\n",
         f"- 이탈 기준: 과제 상대 특징 (pan 오차/2.15°, e_r/0.8 cm, z/1 cm, 진행률/0.25) 의 사람 최근접 거리, 사람 판-빼기 99% = {thr99:.2f} (95% {thr95:.2f}).",
         "- 판별 이탈 밖 프레임 비율: " + ", ".join(f"{r.run} ep{r.ep} {r.frac_frames_outside:.0%}" for r in R.itertuples()) + "\n",
         "### 7.2 평가 wrist 라벨 프레임 (기존 action_bottleneck c5, 닫힘 3 s 안 QC 통과)\n",
         f"- {nb['n']} 프레임. 라벨 |tan| 중앙값 {nb['tan_abs_p50']:.2f} cm, 90% {nb['tan_abs_p90']:.2f} cm; 사람 학습 범위 (|tan| 1.46 cm) 밖 {nb['frac_tan_beyond_human_p99']:.0%}.",
         f"- 사람 학습 판 중 (roll ±10°, tan ±0.5, rad ±0.5 cm) 이웃 0 인 프레임 {nb['frac_zero_tab_roll']:.0%}; roll 조건 없이 (tan, rad) 만 맞춰도 이웃 0 {nb['frac_zero_tab_only']:.0%}.\n"]
    ac.write_facts("07.md", "\n".join(t))
    print("\n".join(t))


if __name__ == "__main__":
    main()
