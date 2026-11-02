"""03 초기 자세 분포 · 첫 pan 움직임 (읽기만 함). 입력 tables/a02_events.csv, a02_frames.parquet. 출력 tables/a03_*.csv/json, _facts/03.md

시작 상태 = 프레임 0 의 팔로워 state (측정값). 리더(action) 프레임 0 도 같이.
초기 TCP = ac.tcp (pan 축 극좌표 모델). 집게(=wrist 카메라가 붙은 몸체) 방향 = FK gripper_frame 회전의 z 축 (카메라 장착 오프셋은 모름).
첫 pan 움직임: onset 뒤 pan 이 1° 넘게 바뀐 첫 프레임의 방향, 첫 하위 움직임 끝까지 이동량 (a02 정의).
pan 정렬: pan(c) ±2° 에 처음 들어온 (reach2) / 머물기 시작한 (settle2) 프레임.
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python a03_initial_state.py
"""
import json

import numpy as np
import pandas as pd
from scipy import stats

import ac


def main():
    E = pd.read_csv(ac.TAB / "a02_events.csv")
    T = pd.read_csv(ac.TAB / "a01_cube_table.csv")
    Cd = pd.read_csv(ac.TAB / "a01_cadence_per_episode.csv")
    data = ac.load_d2()
    out = {}
    S0 = np.array([data[e][0][0] for e in range(256)])
    A0 = np.array([data[e][1][0] for e in range(256)])
    So = np.array([data[e][0][E.onset[e]] for e in range(256)])
    P0 = ac.tcp(S0)
    _, R0 = ac.tip(S0)
    zax = R0[:, :, 2]
    Sg = np.array([data[e][0][E.grasp[e]] for e in range(256)])
    D = pd.DataFrame({"ep": range(256), "group": E.group, "task": E.task, "mode": E["mode"]})
    for j, nm in enumerate(ac.JOINTS):
        D[f"s0_{nm}"] = S0[:, j]
        D[f"a0_{nm}"] = A0[:, j]
        D[f"sg_{nm}"] = Sg[:, j]
    D["tcp0_x"], D["tcp0_y"], D["tcp0_z"] = P0.T
    D["grip_axis_pitch_deg"] = np.degrees(np.arcsin(np.clip(-zax[:, 2], -1, 1)))
    D["grip_axis_yaw_deg"] = np.degrees(np.arctan2(zax[:, 1], zax[:, 0]))
    D["run"] = D.ep.map(Cd.set_index("ep").run)
    D.to_csv(ac.TAB / "a03_initial_states.csv", index=False)

    # 1. 관절별 시작값 요약
    rows = []
    for j, nm in enumerate(ac.JOINTS):
        for lab, sel in [("전체", D.index)] + [(g, D.index[D.group == g]) for g in ("T1K", "T1R", "T3K", "T3R")]:
            x = S0[sel, j]
            rows.append(dict(joint=nm, set=lab, n=len(x), mean=x.mean(), sd=x.std(ddof=1), min=x.min(), max=x.max(), p5=ac.q(x, 5), p95=ac.q(x, 95)))
    J = pd.DataFrame(rows)
    J.to_csv(ac.TAB / "a03_start_joint_summary.csv", index=False)
    # 시작 vs 파지 순간 SD (다양성 비교)
    sd_cmp = pd.DataFrame(dict(joint=ac.JOINTS, start_sd=S0.std(0, ddof=1), onset_sd=So.std(0, ddof=1), grasp_sd=Sg.std(0, ddof=1),
                               start_range=S0.max(0) - S0.min(0), grasp_range=Sg.max(0) - Sg.min(0)))
    # 2. K/R, T1/T3 차이 (Mann-Whitney)
    diff = []
    for j, nm in enumerate(ac.JOINTS):
        for lab, a, b in (("K vs R", D["mode"] == "K", D["mode"] == "R"), ("T1 vs T3", D.task == "T1", D.task == "T3")):
            x, y = S0[a.values, j], S0[b.values, j]
            u = stats.mannwhitneyu(x, y)
            diff.append(dict(joint=nm, compare=lab, median_a=np.median(x), median_b=np.median(y), diff=np.median(x) - np.median(y), p=u.pvalue))
    Df = pd.DataFrame(diff)
    # 3. 녹화 실행별 시작 pan (흐름)
    by_run = D.groupby("run").agg(n=("ep", "size"), group=("group", "first"), pan_mean=("s0_shoulder_pan", "mean"), pan_sd=("s0_shoulder_pan", "std"),
                                  roll_mean=("s0_wrist_roll", "mean"), wflex_mean=("s0_wrist_flex", "mean")).reset_index()
    # 4. 중복도: 판 쌍의 관절 최대 차 (팔 5관절)
    dmax = np.abs(S0[:, None, :5] - S0[None, :, :5]).max(2)
    iu = np.triu_indices(256, 1)
    pair = dmax[iu]
    dg = np.abs(Sg[:, None, :5] - Sg[None, :, :5]).max(2)[iu]
    dup = dict(pairs=len(pair), frac_le2=float((pair <= 2).mean()), frac_le3=float((pair <= 3).mean()), frac_le5=float((pair <= 5).mean()),
               frac_le10=float((pair <= 10).mean()), median=float(np.median(pair)), p95=float(np.percentile(pair, 95)), max=float(pair.max()),
               grasp_median=float(np.median(dg)), grasp_frac_le5=float((dg <= 5).mean()))
    # 같은 시작 상태 묶음 (모든 관절 2° 이내 연결) 개수
    adj = dmax <= 2
    seen, comps = np.zeros(256, bool), []
    for i in range(256):
        if seen[i]:
            continue
        st, comp = [i], []
        seen[i] = True
        while st:
            k = st.pop()
            comp.append(k)
            for m in np.where(adj[k] & ~seen)[0]:
                seen[m] = True
                st.append(m)
        comps.append(len(comp))
    dup["clusters_2deg"] = len(comps)
    dup["largest_cluster_2deg"] = int(max(comps))
    # 5. 초기 TCP · 집게 방향
    tcp0 = dict(x_mean=float(P0[:, 0].mean()), x_sd=float(P0[:, 0].std()), y_mean=float(P0[:, 1].mean()), y_sd=float(P0[:, 1].std()),
                z_mean=float(P0[:, 2].mean()), z_sd=float(P0[:, 2].std()), pitch_mean=float(D.grip_axis_pitch_deg.mean()), pitch_sd=float(D.grip_axis_pitch_deg.std()),
                yaw_mean=float(D.grip_axis_yaw_deg.mean()), yaw_sd=float(D.grip_axis_yaw_deg.std()),
                start_bearing=float(np.mean(ac.bearing(P0[:, 0], P0[:, 1]))), start_bearing_sd=float(np.std(ac.bearing(P0[:, 0], P0[:, 1]))))
    # 6. 첫 pan 움직임
    F = E.copy()
    F["onset_s"] = F.onset / ac.FPS
    F["first_dir_ok"] = F.pan_first_dir == F.pan_target_dir
    F["sub1_frac"] = F.pan_sub1_amount / F.pan_total.where(F.pan_total.abs() > 1e-6)
    F["pan_reach2_from_onset_s"] = (F.pan_reach2 - F.onset) / ac.FPS
    F["pan_settle2_from_onset_s"] = (F.pan_settle2 - F.onset) / ac.FPS
    F["pan_settle2_before_grasp_s"] = (F.grasp - F.pan_settle2) / ac.FPS
    F["pan_reach2_before_grasp_s"] = (F.grasp - F.pan_reach2) / ac.FPS
    F["approach_s"] = (F.grasp - F.onset) / ac.FPS
    F["pan_settle2_frac"] = (F.pan_settle2 - F.onset) / (F.grasp - F.onset)
    F["pan_reach2_frac"] = (F.pan_reach2 - F.onset) / (F.grasp - F.onset)
    F["abs_total"] = F.pan_total.abs()
    F["bearing"] = T.bearing
    F["range_cm"] = T.range_cm
    F[["ep", "group", "onset_s", "pan0", "pan_c", "pan_exp", "pan_total", "pan_first_dir", "pan_target_dir", "first_dir_ok", "pan_sub1_amount", "sub1_frac",
       "pan_reach2_from_onset_s", "pan_settle2_from_onset_s", "pan_reach2_before_grasp_s", "pan_settle2_before_grasp_s", "approach_s", "pan_reach2_frac",
       "pan_settle2_frac", "bearing", "range_cm"]].to_csv(ac.TAB / "a03_pan_first_move.csv", index=False)
    big = F.abs_total >= 10
    pm = []
    for lab, sel in [("전체", F.index), ("pan 총회전 ≥ 10° (절댓값)", F.index[big]), ("pan 총회전 < 10° (절댓값)", F.index[~big])] + [(g, F.index[F.group == g]) for g in ("T1K", "T1R", "T3K", "T3R")]:
        f = F.loc[sel]
        fb = f[f.abs_total >= 10]
        pm.append(dict(set=lab, n=len(f), first_dir_ok=f"{int(fb.first_dir_ok.sum())}/{len(fb)}" if len(fb) else "–",
                       sub1_frac_med=fb.sub1_frac.median() if len(fb) else np.nan,
                       reach2_from_onset_med=f.pan_reach2_from_onset_s.median(), settle2_from_onset_med=f.pan_settle2_from_onset_s.median(),
                       settle2_before_grasp_med=f.pan_settle2_before_grasp_s.median(), reach2_frac_med=f.pan_reach2_frac.median(),
                       settle2_frac_med=f.pan_settle2_frac.median(), settle_lt50pct=f"{int((f.pan_settle2_frac < 0.5).sum())}/{len(f)}",
                       approach_s_med=f.approach_s.median()))
    PM = pd.DataFrame(pm)
    # pan 첫 하위 움직임 크기 ~ 목표
    fb = F[big]
    sl = np.polyfit(fb.pan_total, fb.pan_sub1_amount, 1)
    r_sub = float(np.corrcoef(fb.pan_total, fb.pan_sub1_amount)[0, 1])
    out.update(dup=dup, tcp0=tcp0, sub1_slope=sl.tolist(), sub1_r=r_sub,
               start_pan_sd=float(S0[:, 0].std(ddof=1)), grasp_pan_sd=float(Sg[:, 0].std(ddof=1)))
    json.dump(out, open(ac.TAB / "a03_initial_state.json", "w"), indent=1)

    # 사실 문서
    t = ["## 측정 사실 (스크립트 생성: `scripts/a03_initial_state.py`)\n",
         "### 3.1 시작 프레임 (frame 0) 팔로워 관절값 [°, 그리퍼 0–100]\n",
         ac.md_table(J[J.set == "전체"].drop(columns="set"), {"n": "{:.0f}"}), "\n",
         "그룹별 (평균 ± SD, min–max):\n",
         ac.md_table(J[J.set != "전체"].assign(v=lambda d: d.apply(lambda r: f"{r['mean']:.1f} ± {r.sd:.1f} ({r['min']:.1f}–{r['max']:.1f})", axis=1))
                     .pivot(index="joint", columns="set", values="v").reindex(ac.JOINTS), index=True), "\n",
         "### 3.2 시작 · 움직임 시작(onset) · 첫 파지 순간의 관절 SD 비교 [°]\n",
         ac.md_table(sd_cmp), "\n",
         "### 3.3 K/R · T1/T3 시작값 차이 (중앙값, Mann–Whitney p)\n",
         ac.md_table(Df, {"p": "{:.3g}"}), "\n",
         "### 3.4 녹화 실행별 시작값 평균\n",
         ac.md_table(by_run, {"n": "{:.0f}"}), "\n",
         "### 3.5 시작 상태 중복도 (팔 5관절, 판 쌍의 관절별 차이 중 최대)\n",
         f"- 판 쌍 {dup['pairs']:,}개: 최대 관절 차 ≤ 2° {dup['frac_le2']:.1%} · ≤ 3° {dup['frac_le3']:.1%} · ≤ 5° {dup['frac_le5']:.1%} · ≤ 10° {dup['frac_le10']:.1%}; "
         f"중앙값 {dup['median']:.1f}°, 95% {dup['p95']:.1f}°, 최대 {dup['max']:.1f}°.",
         f"- 같은 판 쌍의 첫 파지 순간 최대 관절 차 중앙값 {dup['grasp_median']:.1f}° (≤ 5° 인 쌍 {dup['grasp_frac_le5']:.1%}).",
         f"- 모든 관절 2° 이내로 이어지는 묶음: {dup['clusters_2deg']}개, 가장 큰 묶음 {dup['largest_cluster_2deg']}편.\n",
         "### 3.6 초기 TCP · 집게 방향 (FK, ac.tcp)\n",
         f"- TCP x {tcp0['x_mean']:.1f} ± {tcp0['x_sd']:.2f} cm, y {tcp0['y_mean']:.1f} ± {tcp0['y_sd']:.2f} cm, z(FK) {tcp0['z_mean']:.1f} ± {tcp0['z_sd']:.2f} cm; "
         f"베이스에서 본 방향 {tcp0['start_bearing']:.1f} ± {tcp0['start_bearing_sd']:.2f}°.",
         f"- 집게 축 (FK gripper_frame z) 수평면 아래 각 {tcp0['pitch_mean']:.1f} ± {tcp0['pitch_sd']:.2f}°, 수평 방향 {tcp0['yaw_mean']:.1f} ± {tcp0['yaw_sd']:.2f}° (FK 프레임). "
         "wrist 카메라는 집게에 고정되어 있으나 장착 오프셋은 측정된 적 없음 → 카메라 광축 방향은 이 값 + 미지 상수.\n",
         "### 3.7 첫 pan 움직임 · pan 정렬 시점\n",
         "pan 총회전 = pan(첫 파지) − pan(onset). 방향 일치 = onset 뒤 처음 1° 넘게 움직인 방향이 총회전 방향과 같음 (|총회전| ≥ 10° 판만). "
         "첫 하위 움직임 비율 = 첫 속도 봉우리가 끝날 때까지 pan 변화 / 총회전. 정렬 = pan(c) ±2°.\n",
         ac.md_table(PM, {"n": "{:.0f}"}), "\n",
         f"- |총회전| ≥ 10° 판: 첫 하위 움직임 이동량 = {sl[0]:.2f} × 총회전 {sl[1]:+.1f}°, r = {r_sub:.2f}.",
         f"- 시작 pan SD {out['start_pan_sd']:.2f}° vs 첫 파지 pan SD {out['grasp_pan_sd']:.1f}°.\n"]
    ac.write_facts("03.md", "\n".join(t))
    print("\n".join(t))


if __name__ == "__main__":
    main()
