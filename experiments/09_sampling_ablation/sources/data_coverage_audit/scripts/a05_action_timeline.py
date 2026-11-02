"""05 시간별 접근 행동 (읽기만 함). 입력 tables/a02_frames.parquet, a02_events.csv, a01_cube_table.csv, vision_probe/labels_v2.csv
출력 tables/a05_*.csv/json, _facts/05.md

핵심 양 (사람 시연, 팔로워 측정값):
  r_t(t), r_r(t) = (TCP(t) − TCP(c)) 를 큐브 접선/반지름 축에 투영 [cm] — '최종 파지 위치까지 남은 접선/반지름 거리'.
    TCP(c) 기준이라 판마다 고정된 모델 편향 (a00: 파지 순간 접선 SD 0.59 cm) 이 빠진다. 큐브 중심 기준 e_t 는 a02 열에 따로 있다.
  관절별 접선 기여 = Σ_frames J_tan,j(q) · Δq_j  (J = ac.tcp 수치 미분, 큐브 접선 축).
구간 정의는 a02 (idle · approach · fine_align · closing · lift · transport · retreat).
Q2 궤적 유사도: onset 뒤 고정 시간 / 진행률에서 관절값을 목표 (pan(c), range) 로 회귀한 R², Known 판의 K 별 분산 비율.
wrist 영상 라벨 (vision_probe/labels_v2.csv, 닫힘 3 s 전 ~ 닫힘, probe_ok) 의 tan_cm 과 r_t 비교 (독립 측정 검증).
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python a05_action_timeline.py
"""
import json

import numpy as np
import pandas as pd

import ac

PH = ["idle", "approach", "fine_align", "closing", "lift", "transport", "retreat"]


def tcp_jac(q, ut, ur, h=0.5):
    q = np.asarray(q, float)
    p0 = ac.tcp(q)
    J = np.zeros((len(q), 5, 3))
    for j in range(5):
        qq = q.copy()
        qq[:, j] += h
        d = (ac.tcp(qq) - p0) / h
        J[:, j, 0] = d[:, :2] @ ut
        J[:, j, 1] = d[:, :2] @ ur
        J[:, j, 2] = d[:, 2]
    return J


def main():
    W = pd.read_parquet(ac.TAB / "a02_frames.parquet")
    E = pd.read_csv(ac.TAB / "a02_events.csv")
    T = pd.read_csv(ac.TAB / "a01_cube_table.csv")
    out = {}
    SJ = [f"s_{j}" for j in ac.JOINTS]
    # ---- 프레임별 r_t, r_r, 관절 기여 ----
    parts = []
    for e, g in W.groupby("ep"):
        g = g.sort_values("frame").copy()
        c = int(E.grasp[e])
        ut, ur = ac.axes(T.cube_x[e], T.cube_y[e])
        P = g[["tip_x", "tip_y", "tip_z"]].values
        d = P[:, :2] - P[c, :2]
        g["r_t"], g["r_r"], g["r_z"] = d @ ut, d @ ur, P[:, 2] - P[c, 2]
        q = g[SJ].values
        J = tcp_jac(q, ut, ur)
        dq = np.vstack([np.zeros((1, 5)), np.diff(q[:, :5], axis=0)])
        contrib = J * dq[:, :, None]           # (n,5,3)
        for j, nm in enumerate(ac.J5):
            g[f"ct_{nm}"] = contrib[:, j, 0]
            g[f"cr_{nm}"] = contrib[:, j, 1]
            g[f"cz_{nm}"] = contrib[:, j, 2]
        g["dtan"] = np.r_[0, np.diff(d @ ut)]
        parts.append(g)
    W = pd.concat(parts, ignore_index=True)
    W.to_parquet(ac.TAB / "a05_frames_rel.parquet", index=False)

    # ---- 1. 이벤트 시각 ----
    ev = pd.DataFrame({"ep": E.ep, "group": E.group})
    for k in ("onset", "pan_reach2", "pan_settle2", "reach2", "close_start", "grasp", "lift", "release"):
        ev[k] = E[k] / ac.FPS
    ev["end"] = E.n / ac.FPS
    evs = []
    for k in ("onset", "pan_reach2", "pan_settle2", "reach2", "close_start", "grasp", "lift", "release", "end"):
        x = ev[k]
        evs.append(dict(event=k, med=x.median(), p25=ac.q(x, 25), p75=ac.q(x, 75), before_grasp_med=(ev.grasp - x).median()))
    EVS = pd.DataFrame(evs)
    # ---- 2. 구간별 관절 변화 ----
    rows = []
    for ph in PH[1:6]:
        sub = W[W.phase == ph]
        per = sub.groupby("ep")
        dur = per.size() / ac.FPS
        r = dict(phase=ph, n_eps=int(per.ngroups), dur_med=dur.median())
        for j in ac.J5:
            net = per[f"s_{j}"].agg(lambda s: s.iloc[-1] - s.iloc[0]).abs()
            path = per[f"s_{j}"].agg(lambda s: np.abs(np.diff(s.values)).sum())
            r[f"{j}_net"] = net.median()
            r[f"{j}_path"] = path.median()
        tnet = per.apply(lambda d: np.hypot(d.tip_x.iloc[-1] - d.tip_x.iloc[0], d.tip_y.iloc[-1] - d.tip_y.iloc[0]))
        r["tcp_xy_net_cm"] = tnet.median()
        r["tcp_z_net_cm"] = per.tip_z.agg(lambda s: s.iloc[-1] - s.iloc[0]).median()
        rows.append(r)
    PJ = pd.DataFrame(rows)
    # 구간별 접선/반지름/z 기여 비율 (관절)
    rows = []
    for ph in ("approach", "fine_align", "closing"):
        sub = W[W.phase == ph]
        for comp, pre in (("접선", "ct_"), ("반지름", "cr_"), ("z", "cz_")):
            a = np.array([sub[f"{pre}{j}"].abs().sum() for j in ac.J5])
            rows.append(dict(phase=ph, comp=comp, **{j: a[i] / a.sum() for i, j in enumerate(ac.J5)}))
    CJ = pd.DataFrame(rows)
    # ---- 3. 파지 전 시점 상태 ----
    snaps = []
    for sec in (5, 3, 2, 1, 0.5, 0):
        f = (E.grasp - int(sec * ac.FPS)).values
        sel = []
        for e, ff in zip(E.ep, f):
            if ff >= 0:
                sel.append((e, ff))
        S = W.set_index(["ep", "frame"]).loc[sel]
        snaps.append(dict(t=f"−{sec} s", n=len(S), rt_abs_med=S.r_t.abs().median(), rt_abs_p90=S.r_t.abs().quantile(.9),
                          rt_ge05=int((S.r_t.abs() >= 0.5).sum()), rt_ge1=int((S.r_t.abs() >= 1).sum()), rt_ge2=int((S.r_t.abs() >= 2).sum()),
                          rr_abs_med=S.r_r.abs().median(), rz_med=S.r_z.median(), dist_med=np.hypot(S.r_t, S.r_r).median(),
                          et_abs_med=S.e_t.abs().median(), dpan_abs_med=(S.s_shoulder_pan.values - E.pan_c.values[[e for e, _ in sel]]).__abs__().mean(),
                          droll_abs_med=np.median(np.abs(S.s_wrist_roll.values - E.roll_c.values[[e for e, _ in sel]]))))
    SN = pd.DataFrame(snaps)
    # 그룹별 −2 s
    f2 = E.grasp - 60
    S2 = W.set_index(["ep", "frame"]).loc[list(zip(E.ep, f2))].reset_index()
    S2["group"] = E.group.values
    g2 = S2.groupby("group").agg(n=("ep", "size"), rt_abs_med=("r_t", lambda s: s.abs().median()), rt_ge1=("r_t", lambda s: int((s.abs() >= 1).sum())),
                                 rr_abs_med=("r_r", lambda s: s.abs().median()), rz_med=("r_z", "median")).reset_index()
    # ---- Q1: 마지막 3 s pan 움직임 ----
    q1 = []
    for e in range(256):
        c = int(E.grasp[e])
        p = W[W.ep == e].s_shoulder_pan.values
        a = max(0, c - 90)
        q1.append(dict(ep=e, net3=abs(p[c] - p[a]), path3=np.abs(np.diff(p[a:c + 1])).sum(), net1=abs(p[c] - p[max(0, c - 30)]),
                       path1=np.abs(np.diff(p[max(0, c - 30):c + 1])).sum()))
    Q1 = pd.DataFrame(q1)
    Q1s = dict(net3_med=Q1.net3.median(), net3_ge3=int((Q1.net3 >= 3).sum()), path3_med=Q1.path3.median(), net1_med=Q1.net1.median(),
               path1_med=Q1.path1.median(), settle2_before_grasp_med=float(((E.grasp - E.pan_settle2) / ac.FPS).median()),
               reach2_frac_med=float(((E.pan_reach2 - E.onset) / (E.grasp - E.onset)).median()))
    # ---- Q2: 궤적 유사도 ----
    rows = []
    rng_c = T.range_cm.values
    for kind, pts in (("onset 뒤 s", (0.33, 0.67, 1.0, 1.5, 2.0, 3.0)), ("진행률", (0.1, 0.25, 0.5, 0.75, 0.9))):
        for v in pts:
            if kind == "onset 뒤 s":
                f = np.minimum(E.onset + int(round(v * ac.FPS)), E.grasp).values
            else:
                f = (E.onset + v * (E.grasp - E.onset)).round().astype(int).values
            Q = np.array([W[(W.ep == e)].iloc[ff][SJ].values for e, ff in zip(E.ep, f)], float)
            r = dict(kind=kind, at=v)
            # pan ~ pan(c)
            A = np.column_stack([E.pan_c, np.ones(256)])
            w = np.linalg.lstsq(A, Q[:, 0], rcond=None)[0]
            res = Q[:, 0] - A @ w
            r["pan_slope_on_target"] = w[0]
            r["pan_R2"] = 1 - res.var() / Q[:, 0].var()
            for j, nm in ((1, "lift"), (2, "elbow"), (3, "wflex")):
                A2 = np.column_stack([rng_c, np.ones(256)])
                w2 = np.linalg.lstsq(A2, Q[:, j], rcond=None)[0]
                res2 = Q[:, j] - A2 @ w2
                r[f"{nm}_R2_range"] = 1 - res2.var() / Q[:, j].var() if Q[:, j].var() > 0 else np.nan
            # Known: K 가 설명하는 분산 비율 (pan, lift)
            kk = (E["mode"] == "K").values
            Kl = T.plan_K.values[kk]
            for j, nm in ((0, "pan"), (1, "lift")):
                x = Q[kk, j]
                within = sum(((x[Kl == k] - x[Kl == k].mean()) ** 2).sum() for k in np.unique(Kl))
                r[f"{nm}_K_var_frac"] = 1 - within / ((x - x.mean()) ** 2).sum()
            rows.append(r)
    Q2 = pd.DataFrame(rows)
    # ---- Q3: 접선 보정 관절 ----
    late = W[(W.t_to_grasp > 0) & (W.t_to_grasp <= 3)]
    tot = np.array([late[f"ct_{j}"].abs().sum() for j in ac.J5])
    q3_share_late = {j: float(tot[i] / tot.sum()) for i, j in enumerate(ac.J5)}
    # 1 s 창에서 r_t 가 0.3 cm 넘게 줄어든 '보정' 창: 창 안 관절별 접선 기여 (부호 = 줄이는 쪽 +)
    corr_rows = []
    for e, g in late.groupby("ep"):
        g = g.sort_values("frame")
        rt = g.r_t.values
        for i in range(0, len(g) - 30, 15):
            dr = abs(rt[i + 30]) - abs(rt[i])
            if dr <= -0.3:
                sgn = -np.sign(rt[i])
                cc = {j: float(sgn * g[f"ct_{j}"].values[i + 1:i + 31].sum()) for j in ac.J5}
                corr_rows.append(dict(ep=e, t_to_grasp=g.t_to_grasp.values[i], rt0=rt[i], d_abs_rt=dr, roll=g.s_wrist_roll.values[i], **cc))
    CR = pd.DataFrame(corr_rows)
    CR.to_csv(ac.TAB / "a05_correction_windows.csv", index=False)
    q3 = dict(n_windows=len(CR), n_eps=int(CR.ep.nunique()) if len(CR) else 0)
    if len(CR):
        s = CR[list(ac.J5)].sum()
        q3["share_of_reduction"] = (s / CR.d_abs_rt.abs().sum()).to_dict()
        q3["main_joint_counts"] = CR[list(ac.J5)].idxmax(axis=1).value_counts().to_dict()
    # ---- Q4: 큰 접선 오차를 보정한 사례 ----
    q4 = []
    for sec in (3, 2, 1.5, 1):
        f = (E.grasp - int(sec * ac.FPS)).values
        rt = np.array([W[(W.ep == e)].iloc[ff].r_t for e, ff in zip(E.ep, f)])
        for thr in (0.5, 1.0, 1.5, 2.0):
            m = np.abs(rt) >= thr
            q4.append(dict(t=f"−{sec} s", thr_cm=thr, n_eps=int(m.sum()), T1K=int((m & (E.group == "T1K")).sum()), T1R=int((m & (E.group == "T1R")).sum()),
                           T3K=int((m & (E.group == "T3K")).sum()), T3R=int((m & (E.group == "T3R")).sum())))
    Q4 = pd.DataFrame(q4)
    # 같은 사례를 큐브 중심 기준 e_t 로
    q4b = []
    for sec in (3, 2, 1):
        f = (E.grasp - int(sec * ac.FPS)).values
        et = np.array([W[(W.ep == e)].iloc[ff].e_t for e, ff in zip(E.ep, f)])
        for thr in (1.0, 1.5, 2.0):
            q4b.append(dict(t=f"−{sec} s", thr_cm=thr, n_eps=int((np.abs(et) >= thr).sum())))
    Q4b = pd.DataFrame(q4b)
    # 접근 끝 (reach2) 시점 r_t
    rt_reach = np.array([W[(W.ep == e)].iloc[int(E.reach2[e])].r_t for e in range(256)])
    # ---- Q5: 같은 접선 오차 · 다른 roll ----
    lt = W[(W.t_to_grasp > 0) & (W.t_to_grasp <= 3) & (W.r_t.abs() >= 0.5)].copy()
    lt["roll_bin"] = pd.cut(lt.s_wrist_roll, np.arange(-60, 61, 15))
    lt["side"] = np.where(lt.r_t > 0, "r_t ≥ +0.5", "r_t ≤ −0.5")
    Q5 = lt.groupby(["roll_bin", "side"], observed=False).ep.nunique().unstack(fill_value=0)
    Q5f = lt.groupby(["roll_bin", "side"], observed=False).size().unstack(fill_value=0)
    # ---- roll ↔ pan 관계 ----
    rp = []
    for e in range(256):
        g = W[W.ep == e]
        c, on = int(E.grasp[e]), int(E.onset[e])
        p, r = g.s_shoulder_pan.values, g.s_wrist_roll.values
        rs = ac.settle_index(r, c, 2.0, on)
        tot_r = abs(r[c] - r[on])
        after = abs(r[c] - r[int(E.pan_settle2[e])]) if E.pan_settle2[e] <= c else np.nan
        vp, vr = np.gradient(ac.smooth(p[on:c + 1])), np.gradient(ac.smooth(r[on:c + 1]))
        cc = np.corrcoef(np.abs(vp), np.abs(vr))[0, 1] if len(vp) > 5 else np.nan
        a = max(on, c - 90)
        rp.append(dict(ep=e, roll_total=r[c] - r[on], roll_settle2_before_grasp=(c - rs) / ac.FPS, pan_settle2_before_grasp=(c - E.pan_settle2[e]) / ac.FPS,
                       roll_after_pan_settle_abs=after, roll_after_frac=after / tot_r if tot_r > 1 else np.nan, speed_corr=cc,
                       droll_last3=r[c] - r[a], dpan_last3=p[c] - p[a]))
    RP = pd.DataFrame(rp)
    RP.to_csv(ac.TAB / "a05_roll_pan.csv", index=False)
    rps = dict(roll_settle_before_grasp_med=RP.roll_settle2_before_grasp.median(), pan_settle_before_grasp_med=RP.pan_settle2_before_grasp.median(),
               roll_settles_after_pan=int((RP.roll_settle2_before_grasp < RP.pan_settle2_before_grasp).sum()),
               roll_after_frac_med=RP.roll_after_frac.median(), speed_corr_med=RP.speed_corr.median(),
               corr_droll_dpan_last3=float(np.corrcoef(RP.droll_last3, RP.dpan_last3)[0, 1]),
               abs_droll_last3_med=float(RP.droll_last3.abs().median()), roll_total_abs_med=float(RP.roll_total.abs().median()))
    # ---- wrist 라벨과 비교 ----
    Lb = pd.read_csv(ac.D2 / "vision_probe/labels_v2.csv")
    Lb = Lb[Lb.probe_ok].merge(W[["ep", "frame", "r_t", "r_r", "e_t", "e_r"]], on=["ep", "frame"], how="left")
    val = dict(n=len(Lb), corr_rt_tanlabel=float(np.corrcoef(Lb.r_t, Lb.tan_cm)[0, 1]), corr_rr_radlabel=float(np.corrcoef(Lb.r_r, Lb.rad_cm)[0, 1]),
               corr_et_tanlabel=float(np.corrcoef(Lb.e_t, Lb.tan_cm)[0, 1]), corr_rt_rel_u=float(np.corrcoef(Lb.r_t, Lb.rel_u_cm)[0, 1]),
               corr_rt_rel_v=float(np.corrcoef(Lb.r_t, Lb.rel_v_cm)[0, 1]))
    for lo, hi in ((0, 1), (1, 2), (2, 3)):
        d = Lb[(Lb.t_to_close > lo) & (Lb.t_to_close <= hi)]
        val[f"corr_rt_tan_{lo}-{hi}s"] = float(np.corrcoef(d.r_t, d.tan_cm)[0, 1])
        val[f"slope_tan_on_rt_{lo}-{hi}s"] = float(np.polyfit(d.r_t, d.tan_cm, 1)[0])
    # 대표 사례: −2 s |r_t| 최대 · 중앙 · roll 큰 판 · K/R 각 하나
    f2v = np.array([W[(W.ep == e)].iloc[int(E.grasp[e]) - 60].r_t for e in range(256)])
    reps = {"−2 s r_t 절댓값 최대": int(np.argmax(np.abs(f2v))), "−2 s r_t 절댓값 중앙": int(np.argsort(np.abs(f2v))[128]),
            "roll(c) 절댓값 최대": int(np.argmax(np.abs(E.roll_c))), "approach 가장 긺": int(np.argmax(E.grasp - E.onset))}
    rep_rows = []
    for lab, e in reps.items():
        rep_rows.append(dict(case=lab, ep=e, group=E.group[e], approach_s=(E.grasp[e] - E.onset[e]) / ac.FPS, pan_total=E.pan_total[e],
                             rt_m2=f2v[e], roll_c=E.roll_c[e], pan_settle2_before=(E.grasp[e] - E.pan_settle2[e]) / ac.FPS,
                             cube=f"({T.cube_x[e]:.1f}, {T.cube_y[e]:.1f})", zone_K=T.plan_K[e] or "R"))
        W[W.ep == e][["ep", "frame", "t_to_grasp", "phase"] + SJ + ["tip_x", "tip_y", "tip_z", "r_t", "r_r", "e_t", "e_r"]].to_csv(
            ac.TAB / f"a05_case_ep{e:03d}.csv", index=False)
    REP = pd.DataFrame(rep_rows)
    out.update(q1=Q1s, q3=q3, q3_share_late=q3_share_late, rt_at_reach2=dict(abs_med=float(np.median(np.abs(rt_reach))), ge1=int((np.abs(rt_reach) >= 1).sum())),
               roll_pan=rps, label_validation=val)
    json.dump(out, open(ac.TAB / "a05_action_timeline.json", "w"), indent=1, default=float)
    for nm, df in (("events", EVS), ("phase_joints", PJ), ("phase_contrib", CJ), ("snapshots", SN), ("q2", Q2), ("q4", Q4), ("q4_et", Q4b), ("q5_eps", Q5), ("q5_frames", Q5f)):
        df.to_csv(ac.TAB / f"a05_{nm}.csv")

    t = ["## 측정 사실 (스크립트 생성: `scripts/a05_action_timeline.py`)\n",
         "r_t / r_r = 최종 파지 TCP 위치까지 남은 접선 / 반지름 거리 (cm, + = 로봇 왼쪽으로 도는 쪽 / 바깥쪽), r_z = 높이 차 (cm). "
         "TCP 모델 편향이 판마다 고정이라 TCP(c) 기준으로 빼서 쓴다 (a00).\n",
         "### 5.1 이벤트 시각 (판 시작 기준 s, 중앙값 [25–75%])\n",
         ac.md_table(EVS.assign(med=EVS.apply(lambda r: f"{r.med:.2f} [{r.p25:.2f}–{r.p75:.2f}]", axis=1)).drop(columns=["p25", "p75"]), {"before_grasp_med": "{:.2f}"}), "\n",
         "### 5.2 구간별 관절 변화 (판별 |순변화| 와 경로 길이의 중앙값, °; TCP cm)\n",
         ac.md_table(PJ, {"n_eps": "{:.0f}"}), "\n",
         "### 5.3 구간별 TCP 이동에 대한 관절 기여 비율 (Σ|J·Δq|, 프레임 합)\n", ac.md_table(CJ, "{:.1%}"), "\n",
         "### 5.4 파지 전 시점별 상태 (256편)\n",
         "rt_ge* = |r_t| 가 그 값 이상인 판 수. et_abs_med = 큐브 중심 기준 |접선 오차| (모델 바닥 SD 0.59 cm 포함). dpan/droll = 파지 순간 대비 (°).\n",
         ac.md_table(SN, {"n": "{:.0f}", "rt_ge05": "{:.0f}", "rt_ge1": "{:.0f}", "rt_ge2": "{:.0f}"}), "\n",
         "그룹별 −2 s:\n", ac.md_table(g2, {"n": "{:.0f}", "rt_ge1": "{:.0f}"}), "\n",
         "### 5.5 Q1 pan 정렬 시점\n",
         f"- pan 이 최종 ±2° 에 처음 들어온 시점: 접근 시간 (onset→c) 의 {Q1s['reach2_frac_med']:.0%} (중앙값). ±2° 안에 계속 머물기 시작: 파지 {Q1s['settle2_before_grasp_med']:.2f} s 전 (중앙값).",
         f"- 마지막 3 s pan |순변화| 중앙값 {Q1s['net3_med']:.2f}°, 경로 {Q1s['path3_med']:.2f}°, ≥ 3° 인 판 {Q1s['net3_ge3']}/256. 마지막 1 s |순변화| {Q1s['net1_med']:.2f}°, 경로 {Q1s['path1_med']:.2f}°.\n",
         "### 5.6 Q2 궤적이 큐브 위치에 따라 얼마나 갈리는가\n",
         "pan_R2 = 그 시점 pan 을 최종 pan(c) 로 회귀한 R² (기울기 = pan_slope). *_R2_range = 관절값을 큐브 range 로 회귀한 R². *_K_var_frac = Known 128편에서 K 가 설명하는 분산 비율.\n",
         ac.md_table(Q2), "\n",
         "### 5.7 Q3 접선 방향 이동을 만든 관절\n",
         "파지 전 3 s 프레임 전체의 접선 이동 |기여| 비율: " + ", ".join(f"{k} {v:.1%}" for k, v in q3_share_late.items()) + ".\n",
         f"1 s 창 (0.5 s 간격) 에서 |r_t| 가 0.3 cm 넘게 줄어든 '보정 창': {q3['n_windows']}개 / {q3['n_eps']}편. "
         + ("창별 감소에 대한 관절 기여 합 비율: " + ", ".join(f"{k} {v:.1%}" for k, v in q3.get('share_of_reduction', {}).items())
            + "; 가장 크게 기여한 관절 (창 수): " + ", ".join(f"{k} {v}" for k, v in q3.get('main_joint_counts', {}).items()) if q3['n_windows'] else "") + "\n",
         "### 5.8 Q4 큰 접선 거리가 남은 상태에서 보정한 사례 (사람 첫 파지는 256/256 성공 — a02 n_close_before_lift = 1)\n",
         "|r_t| (최종 파지 위치까지 남은 접선 거리) 가 기준 이상인 판 수:\n", ac.md_table(Q4, {c: "{:.0f}" for c in ("n_eps", "T1K", "T1R", "T3K", "T3R")}), "\n",
         "같은 시점 큐브 중심 기준 |e_t| (모델 바닥 포함) ≥ 기준인 판 수:\n", ac.md_table(Q4b, {"n_eps": "{:.0f}"}), "\n",
         f"- 접근 끝 (reach2: TCP 가 최종 위치 2 cm 안에 머물기 시작) 시점 |r_t| 중앙값 {np.median(np.abs(rt_reach)):.2f} cm, ≥ 1 cm {int((np.abs(rt_reach) >= 1).sum())}편.\n",
         "### 5.9 Q5 같은 접선 거리 (|r_t| ≥ 0.5 cm, 파지 전 3 s) 를 roll 이 다른 상태에서 보정한 사례\n",
         "판 수 (프레임 수는 괄호):\n",
         ac.md_table(pd.DataFrame({c: [f"{Q5.loc[i, c]} ({Q5f.loc[i, c]})" for i in Q5.index] for c in Q5.columns}, index=[str(i) for i in Q5.index]), index=True), "\n",
         "### 5.10 wrist roll ↔ pan\n",
         f"- 판별 roll 총변화 |중앙값| {rps['roll_total_abs_med']:.1f}°. roll 이 최종 ±2° 에 머물기 시작: 파지 {rps['roll_settle_before_grasp_med']:.2f} s 전, pan {rps['pan_settle_before_grasp_med']:.2f} s 전 (중앙값). "
         f"roll 이 pan 보다 늦게 자리잡은 판 {rps['roll_settles_after_pan']}/256.",
         f"- pan 이 자리잡은 뒤 남은 roll 변화 / 총 roll 변화 중앙값 {rps['roll_after_frac_med']:.0%}. onset→c 동안 |pan 속도| 와 |roll 속도| 상관 중앙값 {rps['speed_corr_med']:.2f}.",
         f"- 마지막 3 s Δroll 과 Δpan 의 판 간 상관 {rps['corr_droll_dpan_last3']:.2f}; |Δroll| 중앙값 {rps['abs_droll_last3_med']:.1f}°.\n",
         "### 5.11 r_t 와 wrist 영상 라벨 비교 (vision_probe labels_v2, probe_ok)\n",
         "- " + ", ".join(f"{k} {v:.2f}" if isinstance(v, float) else f"{k} {v}" for k, v in val.items()) + "\n",
         "### 5.12 대표 사례 (프레임별 값: `tables/a05_case_ep###.csv`)\n", ac.md_table(REP), "\n"]
    ac.write_facts("05.md", "\n".join(t))
    print("\n".join(t))


if __name__ == "__main__":
    main()
