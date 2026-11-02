"""report.md from the CSV/JSON outputs (no hand-copied numbers)."""
import json
from pathlib import Path
import pandas as pd
from scipy.stats import mannwhitneyu

H = Path(__file__).parent
W = pd.read_csv(H / "joint_ranges_working.csv"); C = pd.read_csv(H / "calibration_compare.csv")
Sp = pd.read_csv(H / "grasp_spread.csv"); G = pd.read_csv(H / "first_close_points.csv")
S0 = pd.read_csv(H / "start_pose.csv"); ck = json.load(open(H / "checks.json"))
G["absroll"] = G.droll_from_start.abs()
f = lambda v, n=1: f"{v:.{n}f}"
L = ["# 팔로워 관절 범위 · 작업 영역 비교: 레퍼런스(aswinkumar99) vs 우리(redbox)", "",
     "작성 2026-10-21. 데이터: 레퍼런스 `aswinkumar99/LeRobot-SO101-Pick-Place` 6분할 384편(로컬 사본, 영상 없음), 우리 `redbox_t{1,2,3}_{known,random}` 384편. 값은 `observation.state` (follower).", "",
     "## 방법", "",
     "- 관절 각도: 데이터셋 값 그대로(lerobot 도). lerobot 0° = 각 팔 캘리브레이션 스윕 범위의 중앙. gripper는 0–100.",
     "- 작업 구간: 에피소드마다 그리퍼가 처음 시작값+8 넘게 열린 프레임부터 마지막으로 그 값을 넘은 프레임까지.",
     "- 첫 집기: 처음 열린 뒤 열린 최댓값에서 5 이상 내려가고 이후 15프레임 동안 프레임 간 변화 < 0.4 인 첫 프레임.",
     f"  - 우리 데이터에서 기존 census(`first_grasps.csv`) 닫힘 시각과 비교: {ck['detector_check']['matched']}편 중 {ck['detector_check']['within_0_5s']}편이 0.5 s 이내, 중앙 차 {f(ck['detector_check']['median_abs_dt_s'],2)} s.",
     "- 위치: `so101_new_calib.urdf` FK로 `gripper_frame_link` 원점(그리퍼 끝)을 base_link 좌표로 계산. URDF 0 rad = lerobot 0°로 둠(twin `servo_map` 규약과 같음). wrist_roll·gripper는 위치 계산에 쓰지 않거나 영향이 작음.",
     f"- FK 검증(우리): 첫 집기 FK 위치 ↔ 영상에서 잰 큐브 위치 {ck['fk_fit']['n']}편, 2D 강체 맞춤 잔차 중앙 {f(ck['fk_fit']['resid_cm_median'])} cm, 90% {f(ck['fk_fit']['resid_cm_p90'])} cm. 맞춤으로 얻은 base 위치(탁자 cm) {ck['fk_fit']['base_table_cm']} — space_geom의 별도 추정 (−33.5, 11.6)과 비교용.",
     "- K1–K4·상자는 위 맞춤으로 우리 탁자 좌표 → 우리 base 좌표로 옮겨 그림에 표시. 레퍼런스의 물체·상자 위치는 영상이 없어 표시하지 않음.", "",
     "## 캘리브레이션 비교", "",
     "| 관절 | 레퍼런스 범위(tick) | 폭(°) | 우리 범위(tick) | 폭(°) | 두 팔의 '범위중앙−homing' 차(°) |", "|---|---|---|---|---|---|"]
for _, r in C.iterrows():
    L.append(f"| {r.joint} | {r.ref_range_ticks} | {f(r.ref_span_deg)} | {r.our_range_ticks} | {f(r.our_span_deg)} | {f(r.convention_shift_deg)} |")
L += ["", "- 마지막 열: 기준을 '범위 중앙' 대신 'homing 자세(tick 2047)'로 바꾸면 두 팔 사이 각도가 이만큼 달라짐. 같은 물리 자세가 두 팔에서 같은 lerobot 각도라는 보장은 이 정도 불확실성 안에서만 성립.",
      f"- 이 대안 기준으로 FK를 다시 하면 첫 집기 거리 중앙값: 레퍼런스 {f(ck['convention_alt'][0]['r_median_mid'])} → {f(ck['convention_alt'][0]['r_median_home'])} cm, 우리 {f(ck['convention_alt'][1]['r_median_mid'])} → {f(ck['convention_alt'][1]['r_median_home'])} cm.",
      "- wrist_roll은 두 팔 모두 0–4095(한 바퀴)라 0° = homing 자세. 에피소드 시작 자세 중앙값: " + ", ".join(f"{r.joint} 레퍼런스 {f(r.ref)}° / 우리 {f(r.our)}°" for _, r in S0.iterrows() if r.joint == "wrist_roll") + ". 절대값 비교 대신 변화량(시작→집기)을 사용.", "",
      "## 작업 구간 관절 범위 (fig2_joint_ranges.png)", "",
      "| 관절 | 레퍼런스 5–95% | 폭 | 우리 5–95% | 폭 | 레퍼런스 1–99% 폭 | 우리 1–99% 폭 |", "|---|---|---|---|---|---|---|"]
for j in W.joint.unique():
    a, b = W[(W.src == "ref") & (W.joint == j)].iloc[0], W[(W.src == "our") & (W.joint == j)].iloc[0]
    L.append(f"| {j} | {f(a.p5)} ~ {f(a.p95)} | {f(a.span_p5_p95)} | {f(b.p5)} ~ {f(b.p95)} | {f(b.span_p5_p95)} | {f(a.span_p1_p99)} | {f(b.span_p1_p99)} |")
L += ["", f"프레임 수: 레퍼런스 {int(W[W.src=='ref'].frames.iloc[0])}, 우리 {int(W[W.src=='our'].frames.iloc[0])}. 작업 구간에는 상자로 옮기는 동작도 포함.", "",
      "## 첫 집기 지점 (fig1_top_view.png, fig3_at_grasp.png)", "",
      "| 데이터 | 그룹 | 편 | 볼록껍질 면적(cm²) | 거리 r 5/50/95% (cm) | 방향 5/50/95% (°, +오른쪽) | \\|roll 변화\\| 중앙(°) | roll 변화 5~95% (°) | wrist_flex 중앙(°) |", "|---|---|---|---|---|---|---|---|---|"]
for _, r in Sp.iterrows():
    L.append(f"| {'레퍼런스' if r.src=='ref' else '우리'} | {r.group} | {r.n} | {f(r.hull_area_cm2,0)} | {f(r.r_p5)} / {f(r.r_p50)} / {f(r.r_p95)} | {f(r.az_p5)} / {f(r.az_p50)} / {f(r.az_p95)} | {f(r.droll_abs_p50)} | {f(r.droll_p5)} ~ {f(r.droll_p95)} | {f(r.wflex_p50)} |")
ref, our = G[G.src == "ref"], G[G.src == "our"]
L += ["", "검정 (Mann–Whitney, 전체 첫 집기):",
      f"- 거리 r: p = {mannwhitneyu(ref.r_cm, our.r_cm).pvalue:.1e}",
      f"- \\|roll 변화\\|: p = {mannwhitneyu(ref.absroll, our.absroll).pvalue:.1e}; >30° 비율 레퍼런스 {ref.absroll.gt(30).mean():.1%} / 우리 {our.absroll.gt(30).mean():.1%}; >45° {ref.absroll.gt(45).mean():.1%} / {our.absroll.gt(45).mean():.1%}",
      f"- wrist_flex: p = {mannwhitneyu(ref.wrist_flex, our.wrist_flex).pvalue:.1e}", "",
      "## 한계", "",
      "- 두 팔의 base 좌표는 각자 기준. 탁자 높이·카메라·상자 위치·물체(스펀지 vs 2.5 cm 큐브)가 다름.",
      "- 레퍼런스 FK는 그 팔에서 검증하지 못함(영상·물체 위치 없음). 캘리브레이션 기준 불확실성은 위 표 참조.",
      f"- 첫 집기 검출 실패: 레퍼런스 {384 - len(ref)}편, 우리 {384 - len(our)}편 (표에서 제외).",
      "- 레퍼런스 물체(스펀지) 각도는 영상 없이 알 수 없음.", "",
      "## 파일", "", "`extract_states.py`(so101-env) → states.npz; `analyze.py`, `work_ranges.py`, `make_plots.py`, `write_report.py`(system python3); joint_ranges*.csv, calibration_compare.csv, first_close_points.csv, grasp_spread.csv, start_pose.csv, checks.json, fig1–3."]
(H / "report.md").write_text("\n".join(L) + "\n")
print("\n".join(L))
