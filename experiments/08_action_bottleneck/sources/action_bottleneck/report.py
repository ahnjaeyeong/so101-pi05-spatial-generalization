"""분석결과.md 생성 — 숫자는 모두 json 에서 (손으로 옮기지 않음). 사실 · 측정값만.
사용: python3 report.py
"""
import json
from pathlib import Path

AB = Path(__file__).resolve().parent
J = lambda n: json.load(open(AB / n))  # noqa: E731
c3, c5, c2, c2b, c2c = J("c3_state_path.json"), J("c5_coverage.json"), J("c2_roll_rotation_check.json"), J("c2b_pivot_fit.json"), J("c2c_cube_angle.json")
a1, a2, sm = J("a1_g1.json"), J("a2_g2.json"), J("smoke/smoke.json")
g1r, g1cr, g2r = J("g1/run.json") if (AB / "g1/run.json").exists() else None, J("g1c/run.json"), J("g2/run.json")


def f(x, n=2):
    return "—" if x is None else (f"{x:.{n}f}" if isinstance(x, (int, float)) else str(x))


def ci(v, n=2):
    return f"[{f(v[0], n)}, {f(v[1], n)}]"


L = []
w = L.append
w("# Action Expert 병목 분석 — 결과 (2026-10-27)\n")
w("설계: `실험설계.md`. 로봇 연결 없음, 학습 코드 · 데이터셋 · 체크포인트 변경 없음 (읽기만). 모델: d2 `checkpoints/020000`. 이 문서는 `report.py` 가 json 에서 만든다.\n")

w("## 0. 실행 기록 · d4\n")
w("| 단계 | 시각 | d4 |")
w("|---|---|---|")
w("| G1 ep 0–31 (d4 와 동시, watchdog) | 13:22–14:03 | step 7,315 → 7,472, 동시 실행 중 16–21 s/step (단독 10.1). watchdog '2 배 초과' 대기 여러 번 |")
w("| 사용자 지시 '일단 멈추고 진행' → d4 SIGSTOP (pid 3000922 + 자식 5) | 14:04:22 | step 7,472 에서 정지 (`PAUSE_NOTE_F1.txt`) |")
w(f"| G1 ep 32–127 (`g1c/`) | 14:04–14:41 | 정지. GPU {f(g1cr['gpu_busy_s'], 0)} s |")
w(f"| G2 (`g2/`) | 14:41–15:04 | 정지. GPU {f(g2r['gpu_busy_s'], 0)} s |")
w("| d4 SIGCONT | 15:04:04 | 재개 확인 (프로세스 상태 S), 이후 10.9 s/step (CPU 분석 동시) |")
w("")
w("- G1 은 d4 정지 전(g1, 동시 실행)과 정지 뒤(g1c) 두 묶음이다. 같은 스크립트 · 같은 noise 은행 · 같은 체크포인트라 결과값은 실행 환경과 무관하다 (결정적 계산, smoke 에서 predict_action_chunk 와 차이 0.0).\n")

w("## 1. 사전 점검 (CPU)\n")
w("### 1.1 엔진 동일성 · 가리기 동작 (`smoke_cpu.py`, 판 0, 1 프레임)\n")
w(f"- ab_core.Engine vs `policy.predict_action_chunk` (같은 noise): 최대 차 {sm['max_abs_diff_vs_predict_action_chunk_deg']} °.")
w(f"- 큐브 같은 자리 다시 붙이기 (W0): 최대 변화 {sm['W0 d+0']['max_abs_d_deg']} °.")
w(f"- roll 숫자 토큰 예: roll {f(sm["state_rolls"][0], 1)}° → {sm['roll_tokens'][0]}, {f(sm["state_rolls"][1], 1)}° → {sm['roll_tokens'][1]}. state 숫자 6 개 모두 인식.\n")

w("### 1.2 wrist_roll state 입력 경로 (분석 3a, `c3_state_path.py`)\n")
tr = c3["train"]
w("| 항목 | 값 |")
w("|---|---|")
w(f"| 정규화 | QUANTILES, roll q01 {f(c3['q01'][4])} ° / q99 {f(c3['q99'][4])} °, 잘라내기 없음 |")
w(f"| 이산화 | 256 구간, roll 1 구간 {f(c3['bin_deg'][4], 3)} °. 범위 아래 → 토큰 '-1', 위 → '255' |")
w(f"| 토큰화 | 숫자를 한 자리씩 토큰으로: 예 `{' '.join(c3['token_examples'][3]['state_tokens'][:24])}` |")
w(f"| 숫자당 토큰 수 (구분 '▁' 포함, −1…255) | {c3['tokens_per_number_hist']} |")
w(f"| 학습 프레임 roll 자릿수 | {c3['train_roll_ndigits']} (1 자리 = roll ≤ {f(c5['M7_digit_boundary_deg'][0], 1)} °, 2 자리 ≤ {f(c5['M7_digit_boundary_deg'][1], 1)} °) |")
w(f"| roll 토큰 위치 | 앞 숫자 4 개 글자 수에 따라 변함: {c3['train_roll_pos_offset_digits']} |")
w(f"| 문장 토큰 수 | 43–45 (최대 200, 잘림 없음) |")
w(f"| 학습 데이터 범위 밖 | roll 아래 {tr['frac_below'][4]}, 위 {tr['frac_above'][4]} (q01 = 최솟값 envelope) |")
for k, v in c3["eval"].items():
    w(f"| 평가 `{k}` 범위 밖 (pan, lift, elbow, flex, roll, grip) | 아래 {v['frac_below']}, 위 {v['frac_above']}; '-1' 토큰 {v['tok_minus1']} 개 / {v['n']} 프레임 |")
w("| 주의 마스크 (장난감 prefix 3 + suffix 2) | " + str(c3["att2d_toy(prefix3_suffix2)"]) + " — prefix 끼리 양방향, suffix 는 prefix 전체 + suffix |")
w(f"| 학습 설정 | {c3['train_config_policy']} |")
w("| 코드 위치 | state → `processor_pi05.Pi05PrepareStateTokenizerProcessorStep` (np.digitize) → 프롬프트 `Task: …, State: …;\\nAction: `. Expert 입력 `embed_suffix` = noisy action + timestep(adaRMS), state 없음. `train_expert_only` → PaliGemma 고정 |")
w("")

w("### 1.3 영상 회전 규약 확인 (`c2*_*.py`, 사람 시연)\n")
w(f"- wrist 큐브 모서리 각도 (minAreaRect, 90° 주기) 변화 ~ Δroll, Δpan ({c2c['n_pairs']} 쌍, {c2c['n_eps']} 판): "
  f"roll 계수 {f(c2c['coef_roll'])} {ci(c2c['coef_roll_ci'])}, pan 계수 {f(c2c['coef_pan'])} {ci(c2c['coef_pan_ci'])}, 잔차 SD {f(c2c['resid_sd_deg'], 1)} °. "
  f"라벨 규약 θ = 0.91·roll − 5.5° 의 회전 방향과 같은 부호.")
w(f"- 집게 끝 정지 (≤ 0.4 cm) · |Δroll| ≥ 6° 쌍에서 큐브 중심 위치의 회전: 기준점 (u*, v*) 중심 기울기 {f(c2['ref']['slope_obs_on_exp'])} {ci(c2['ref']['ci'])}, "
  f"영상 중심 기준 {f(c2['center']['slope_obs_on_exp'])} {ci(c2['center']['ci'])}.")
w(f"- 회전 중심 맞춤 ({c2b['n_pairs']} 쌍): 회전 없음 모형 잔차 {f(c2b['rmse_no_rotation_px'], 1)} px 가 회전 모형 최소 ({f(c2b['rmse_px'], 1)} px, k 격자 하한 {c2b['k']}) 보다 작음. "
  f"기준점 고정 {f(c2b['rmse_pivot_ref_px'], 1)} px, 영상 중심 고정 {f(c2b['rmse_pivot_center_px'], 1)} px. → roll 축의 영상 투영점은 이 자료로 정해지지 않음.")
w("- 그래서 아래 B (회전, 영상 편집 차이) 는 회전 중심과 무관하고, C (state 만) · D (RC/RI) 의 기대값은 '기준점 = 회전 중심' 가정에 의존한다.\n")

w("## 2. 학습 데이터 roll × 큐브 위치 (분석 5, `c5_coverage.py`, d2 256 판, 닫힘 3 s 안 probe_ok 7,810 프레임)\n")
m1 = c5["M1_roll_pre_1s"]
w(f"- 닫힘 1 s 전 roll (판 단위): 중앙값 {f(m1['50%'], 1)}, 25–75 % {f(m1['25%'], 1)}…{f(m1['75%'], 1)}, 범위 {f(m1['min'], 1)}…{f(m1['max'], 1)} °. 그룹별 SD: "
  + ", ".join(f"{g} {f(v['std'], 1)}" for g, v in c5["M1_roll_pre_by_group"].items()) + ".")
w(f"- 닫힘 3 s 전 → 닫힘 roll 변화 |Δ| 중앙값 {f(c5['M1_roll_change_last3s_abs']['50%'])} °, 75 % {f(c5['M1_roll_change_last3s_abs']['75%'])} °.")
w(f"- roll ← 큐브 위치 (CV R²): 선형 {f(c5['M2_roll_from_pos']['lin'])}, kNN5 {f(c5['M2_roll_from_pos']['knn5'])}, 위치+그룹 {f(c5['M2_roll_from_pos']['lin_pos_group'])}; "
  f"← 계획 큐브 각도 ({c5['M2_roll_from_yaw']['yaw_values']}, 90° 주기) {f(c5['M2_roll_from_yaw']['lin_yaw90'])}.")
w(f"- roll 과 라벨 상관: " + ", ".join(f"{k} {f(v)}" for k, v in c5["M4_corr_roll_vs"].items()) + ".")
w(f"- 영상 축 상대 위치 크기 |rel|: 중앙값 {c5['M3_offset_mag_cm']['50%']}, 90 % {c5['M3_offset_mag_cm']['90%']}, 99 % {c5['M3_offset_mag_cm']['99%']} cm.")
for nm, lab in (("tan", "탁자 tan 0.5 cm 칸"), ("phi", "영상 각도 45° 칸")):
    m = c5[f"M3_cells_{nm}"]
    w(f"- roll 15° × {lab} (닫힘 1.5 s 안): {m['n_cells']} 칸 중 판 ≥ 5 인 칸 {m['cells_ge5eps']}, ≥ 1 인 칸 {m['cells_ge1ep']}. 표: `c5_cells_roll_x_{nm}_episodes.csv`.")
w("")
w("판 수 표 (roll × tan):\n")
m = c5["M3_cells_tan"]
w("| roll \\ tan | " + " | ".join(m["cols"]) + " |")
w("|---" * (len(m["cols"]) + 1) + "|")
for r, row in zip(m["rows"], m["table_eps"]):
    w(f"| {r} | " + " | ".join(str(x) for x in row) + " |")
w("")
m6 = c5["M6_eval_neighbors"]
w(f"- 평가 프레임 (조건 통과 {m6['n']}) 의 train 이웃 판 (|Δroll| ≤ 10°, |Δtan|, |Δrad| ≤ 0.5 cm): 0 개인 비율 {f(m6['frac_zero_tab_roll'])} "
  f"(roll 조건 없이 {f(m6['frac_zero_tab_only'])}), 중앙값 {m6['median_tab_roll']}. train 판 하나 빼기 기준: 0 개 비율 {f(c5['M6_train_loo_neighbors']['frac_zero'], 3)}, 중앙값 {c5['M6_train_loo_neighbors']['median']}.")
w(f"- 평가 roll: 중앙값 {m6['roll_eval']['50%']}, 범위 {m6['roll_eval']['min']}…{m6['roll_eval']['max']} °. roll 자릿수 경계 ±2° 안 비율: train {f(c5['M7_frac_within2deg']['train_probe'], 3)}, 평가 {f(c5['M7_frac_within2deg']['eval'], 3)}.")
w(f"- 학습 프레임 구성: 시작 ~ 닫힘 3 s 전 {c5['M8_frame_share']['before']}, 닫힘 3 s 전 ~ 닫힘 {c5['M8_frame_share']['pre3']}, 닫힘 뒤 {c5['M8_frame_share']['after']} (전체 {c5['M8_frame_share']['n_frames']} 프레임).\n")

w("## 3. 시각 위치 정확도 vs 행동 정확도 — 같은 프레임 · 같은 라벨 (분석 4, G2 + `a2_g2_analyze.py` S1, S5)\n")
w("이후 이동 = 닫힘까지 (최대 50 프레임) 집게 끝 이동 (사람: 행동 목표 관절, 정책: chunk). 회귀 fut ~ tan + rad, 기울기 = 라벨 1 cm 당 이동 cm. train probe 7,810 프레임 (in-sample).\n")
w("| 닫힘 전 | n | 사람 tan 기울기 (R²) | 정책 tan 기울기 (R²) | 차 (정책−사람) CI | 사람 rad | 정책 rad | 차 CI | 정책~사람 r (tan / rad) |")
w("|---|---|---|---|---|---|---|---|---|")
for k, v in a2["S1_future_slopes"].items():
    w(f"| {k} | {v['n']} | {f(v['hum_a_tan_slope'])} ({f(v['hum_a_tan_r2'])}) | {f(v['pol_tan_slope'])} ({f(v['pol_tan_r2'], 3)}) | {ci(v['diff_tan_ci'])} | "
      f"{f(v['hum_a_rad_slope'])} | {f(v['pol_rad_slope'])} | {ci(v['diff_rad_ci'])} | {f(v['pol_vs_hum_tan_r'])} / {f(v['pol_vs_hum_rad_r'])} |")
w("\n(state 기준 사람 tan 기울기: " + ", ".join(f"{k} {f(v['hum_s_tan_slope'])}" for k, v in a2["S1_future_slopes"].items()) + ")\n")
w("F1 특징 해독값 (img→rot tan, F1 fold 교차 예측) 에 대한 기울기. pan 이득 = Δpan 을 접선 cm 로 바꾼 값 (57.3/거리 °/cm):\n")
w("| 특징 | 닫힘 전 | 해독~라벨 r | 정책 tan | 사람 tan | 정책 pan 이득 | 사람 pan 이득 |")
w("|---|---|---|---|---|---|---|")
for lab, v in a2["S5_feature_to_action"].items():
    for k, x in v.items():
        w(f"| {lab} | {k} | {f(x['dec_vs_label_tan_r'])} | {f(x['pol_tan_on_dec_slope'])} | {f(x['hum_a_tan_on_dec_slope'])} | {f(x['pol_pan_on_dec_gain'])} | {f(x['hum_a_pan_on_dec_gain'])} |")
s6 = a2["S6_eval"]
w(f"\n평가 롤아웃 (조건 통과 {s6['n']}): train 범위 안 {s6['in_range']['n']} 프레임 정책 tan 기울기 {f(s6['in_range']['pol_tan_slope'])} (R² {f(s6['in_range']['r2'], 3)}), "
  f"범위 밖 {s6['out_range']['n']} 프레임 {f(s6['out_range']['pol_tan_slope'])} (R² {f(s6['out_range']['r2'])}; 라벨 |tan| 중앙값 {f(s6['out_range']['label_tan_absmed'])} cm, 정책 이동 |tan| {f(s6['out_range']['pol_tan_absmed'])} cm).\n")

w("## 4. roll 조건부 공간 매핑 — 요인 실험 (분석 1 · 2 · 3b, G1 + `a1_g1_analyze.py`)\n")
w(f"T1 128 판 × 3 단계 = {a1['n_frames']} 프레임, {a1['n_obs']} 관측, noise 4, step 5. 집게 끝은 roll 행동을 base 값으로 고정한 FK (tipf).\n")
w("| 단계 (chunk idx) | 프레임 | G_tt [CI] | G_rr [CI] | G_rt / G_tr | **w_rot** [CI] (1 = roll 반영, 0 = 무시) | ψ 정책 / 기대 (Δ −30, −15, +15, +30) |")
w("|---|---|---|---|---|---|---|")
for ph, idx in (("t2.5", 49), ("t1.5", 45), ("t1.0", 30)):
    r = a1[ph]
    ps = ", ".join(f"{f(v[0], 1)}/{f(v[1], 1)}" for v in r["B_psi_median"].values())
    w(f"| 닫힘 {ph[1:]} s 전 ({idx}) | {r['n_frames']} | {f(r['G_tt'])} {ci(r['G_tt_ci'])} | {f(r['G_rr'])} {ci(r['G_rr_ci'])} | {f(r['G_rt'])} / {f(r['G_tr'])} | {f(r['B_w_rot'])} {ci(r['B_w_rot_ci'])} | {ps} |")
w("\nroll Δ 별 영상 이득 G_tt / G_rr (G(Δ) = Rp(Δ) M(θ+0.91Δ)⁻¹):\n")
w("| 단계 | Δ −30 | Δ −15 | Δ 0 | Δ +15 | Δ +30 |")
w("|---|---|---|---|---|---|")
for ph in ("t2.5", "t1.5", "t1.0"):
    r = a1[ph]
    cells = [f"{f(r.get(f'G_tt_{d}'))} / {f(r.get(f'G_rr_{d}'))}" for d in ("-30", "-15")] + [f"{f(r['G_tt'])} / {f(r['G_rr'])}"] + \
            [f"{f(r.get(f'G_tt_{d}'))} / {f(r.get(f'G_rr_{d}'))}" for d in ("+15", "+30")]
    w(f"| {ph} | " + " | ".join(cells) + " |")
w("\nstate 만 바꿈 (C) · roll-일관 회전 (D) — 기대값은 기준점 = 회전 중심 가정:\n")
w("| 단계 | **w_state** [CI] | Δ±30 \\|Δtip_S\\| / 자기 이득 기대 / 큐브 함의 dC (cm) | Δpan (−30/+30) | roll 행동 복사 | **w_RC** [CI] | Δ±30 \\|RC\\| / \\|RI\\| (cm) | RI ~ 자기 이득 기대 |")
w("|---|---|---|---|---|---|---|---|")
for ph in ("t2.5", "t1.5", "t1.0"):
    r = a1[ph]
    cA, dA = r["C_abs"], r["D_abs"]
    w(f"| {ph} | {f(r['C_w_state'])} {ci(r['C_w_state_ci'])} | {f(cA['-30']['dS'])}/{f(cA['-30']['dSpred'])}/{f(cA['-30']['dC'])} · {f(cA['+30']['dS'])}/{f(cA['+30']['dSpred'])}/{f(cA['+30']['dC'])} | "
      f"{f(cA['-30']['dpan'])} / {f(cA['+30']['dpan'])} | {f(cA['+30']['droll_copy'])} | {f(r['D_w_RC'])} {ci(r['D_w_RC_ci'])} | "
      f"{f(dA['-30']['RC'])}/{f(dA['-30']['RI'])} · {f(dA['+30']['RC'])}/{f(dA['+30']['RI'])} | {f(r['D_RI_vs_ownpred'])} |")
w("\n가리기 (Expert 의 직접 읽기만 막음):\n")
w("| 단계 | KR: G_tt / G_rr | KR: base 집게 끝 변화 | KR: base pan \\|Δ\\| | KR: roll 행동 \\|Δ\\| | KS: pan \\|Δ\\| | KS: 집게 끝 변화 | KS: 관절 최대 \\|Δ\\| | W0 최대 |")
w("|---|---|---|---|---|---|---|---|---|")
for ph in ("t2.5", "t1.5", "t1.0"):
    r = a1[ph]
    w(f"| {ph} | {f(r['E_GK_tt'])} / {f(r['E_GK_rr'])} | {f(r['E_KR_base_tip_med'])} cm | {f(r['E_KR_base_pan_absmed'])} ° | {f(r['E_KR_base_droll_a_absmed'])} ° | "
      f"{f(r['E_KS_base_pan_absmed'], 1)} ° | {f(r['E_KS_base_tip_med'], 1)} cm | {f(r['E_KS_max_joint_med'], 1)} ° | {r['W0_tip_max']} |")
w("\nK / R 위치별 (중앙값 · 점추정):\n")
w("| 단계 | 위치 | n | G_tt | G_rr | w_rot | w_state | w_RC |")
w("|---|---|---|---|---|---|---|---|")
for ph in ("t2.5", "t1.5", "t1.0"):
    for md in ("K", "R"):
        r = a1.get(f"{ph}_{md}")
        if r:
            w(f"| {ph} | {md} | {r['n_frames']} | {f(r['G_tt'])} | {f(r['G_rr'])} | {f(r['B_w_rot'])} | {f(r['C_w_state'])} | {f(r['D_w_RC'])} |")
w("")

w("## 5. Expert 내부 (분석 3b · 4, G2 hidden probe + G1 hidden)\n")
w("첫 denoise step (고정 noise 입력) 의 행동 토큰 평균 hidden, 층별 ridge, F1 과 같은 5-fold. 비교: F1 Gemma KV probe img→rot tan MAE 0.076–0.120 cm, roll 없는 tab R² 0.59–0.87.\n")
w("| Expert 층 | img→rot tan MAE (R²) | tab tan MAE (R²) | roll MAE ° (R²) | G1: g_img (tab) | G1: g_state (tab) | G1: w_RC (tab) |")
w("|---|---|---|---|---|---|---|")
s2, s3 = a2["S2_expert_probe"], a2["S3_expert_hidden_edits"]
for i in range(18):
    a, b = s2[f"L{i}"], s3[f"L{i}"]
    w(f"| {i} | {f(a['img_rot_tan'], 3)} ({f(a['img_rot_tan_r2'])}) | {f(a['tab_tan'], 3)} ({f(a['tab_tan_r2'])}) | {f(a['roll_mae'], 1)} ({f(a['roll_r2'])}) | "
      f"{f(b['g_img_tab'])} | {f(b['g_state_tab'])} | {f(b['w_RC_tab'])} |")
w("\n- g_img: 영상 큐브 ±1 cm 편집 → 해독 tab 변화 / 기대 (M(θ)·e). g_state: state roll 만 바꿈 → 해독 tab 변화 / dC. w_RC: 1 − ⟨RC, RI⟩/|RI|² (해독 tab).")
w("- 같은 G1 관측의 최종 행동 값은 4 절 (w_rot, w_state, w_RC).\n")
w("주의 질량 (첫 denoise step, 행동 토큰 → prefix 묶음, head · 토큰 평균; train 프레임 평균):\n")
w("| 닫힘 전 | 층 | front | wrist | 과제 문장 | state (roll 제외) | roll 숫자 | suffix |")
w("|---|---|---|---|---|---|---|---|")
for ph in ("0-1s", "2-3s"):
    for li in (0, 4, 8, 12, 17):
        x = a2["S4_attention"][ph][f"L{li}"]
        w(f"| {ph} | {li} | {f(x['front'], 3)} | {f(x['wrist'], 3)} | {f(x['task'], 3)} | {f(x['state_other'], 3)} | {f(x['roll'], 3)} | {f(x['suffix'], 3)} |")
w(f"\n- roll 숫자 토큰 수 분포 (G2 프레임): {a2['S4_attention']['n_roll_tokens']}. prefix 712 토큰 중 roll 숫자 1–3 개 (균등 배분이면 0.0014–0.0042). 전체 층 표: `a2_g2.json`.\n")

w("## 6. 한계\n")
w("- C · D 기대값은 회전 중심 = 라벨 기준점 가정 (1.3 절에서 회전 중심을 정하지 못함). B (w_rot) 는 이 가정과 무관.")
w("- G1 편집은 큐브만 옮기거나 돌린다. 배경 (탁자 무늬 · 그림자 · 상자) 은 그대로라 state roll 과 영상 속 방향 단서가 서로 맞지 않는 관측이 된다. 정책이 state 대신 영상 속 방향 단서를 쓰는지는 이 편집으로 분리되지 않는다.")
w("- 편집 흔적 (inpaint) 은 ± 대칭 차이로 상쇄. W0 는 원본과 픽셀이 같아 대조 의미가 제한적이다 (exp2 와 같음).")
w("- S1 · S5 는 학습 프레임 (in-sample) 의 관측 회귀라 라벨 잡음만큼 기울기가 작아진다 (사람 · 정책 같은 조건). G1 의 G 는 반사실 편집 반응이다 — 두 값은 정의가 다르다.")
w("- Expert hidden 은 첫 denoise step 하나 · 행동 토큰 평균만 기록했다. 층 사이 비교는 같은 probe 방식 안에서만 의미가 있다.")
w("- d2 020000 하나만. d4 · 다른 step 은 측정하지 않았다.\n")

w("## 7. 파일\n")
w("`실험설계.md`, `ab_core.py`, `smoke_cpu.py` (smoke/), `c3_state_path.py`, `c5_coverage.py`, `c2_roll_rotation_check.py`, `c2b_pivot_fit.py`, `c2c_cube_angle.py`, "
  "`g1_roll_factorial.py` (g1/ ep 0–31, g1c/ ep 32–127), `g2_policy_frames.py` (g2/), `a1_g1_analyze.py`, `a2_g2_analyze.py` (S2·S3 는 첫 실행 로그 `a2.log` → `a2_s2s3_fromlog.json`, 나머지 `--skip_s2s3` 재실행 `a2b.log`), "
  "`run_gpu.sh`, `run_gpu_paused.sh`, 결과 json/csv, 이 문서 (`report.py`).")
(AB / "분석결과.md").write_text("\n".join(L) + "\n")
print("written", len(L), "lines")
