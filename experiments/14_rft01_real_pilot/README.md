# EXP-14 · rft01 vs d2 020000 실물 파일럿 (Trial 1–16)

| 항목 | 내용 |
|---|---|
| 실험 ID | **EXP-14** (EXP-13 rft01 의 첫 실물 평가) |
| 날짜 | 2026-11-05 (준비 09:00 전후, 시행 11:14 – 14:5x) |
| 상태 | `COMPLETED` (계획 16 시행 모두 실행) · 모델 간 결론 **미결정** (Unknown 구간 교란, 아래 §교란) |
| 표기 | [사실] 파일 측정값 · [기록] 실행 기록 그대로 · [자동 후보] 규칙 계산 (사용자 판정 아님) · [가짜 장치] FakeBus · FakeCam 시험 · [가설] · [계획] |

원본 요약: [`sources/rft01_real_pilot/reports/pilot_summary_t01_t07.md`](sources/rft01_real_pilot/reports/pilot_summary_t01_t07.md), [`pilot_summary_t08_t16.md`](sources/rft01_real_pilot/reports/pilot_summary_t08_t16.md). 준비 보고서: [`sources/rft01_real_pilot/README.md`](sources/rft01_real_pilot/README.md). 이 문서는 요약.

## 목적
EXP-13 의 rft01 001000 (FT) 과 기준 d2 020000 (BL) 을 같은 자리·각도·추론 설정에서 실물로 번갈아 돌려, 오프라인에서 본 R1 복구 신호·R2 닫힘 변화가 실물 첫 파지·최종 성공에 나타나는지 확인하는 **파일럿**.

## 검증 가설
- [가설] FT 는 BL 보다 Known K 에서 빈 닫힘이 적고, Pan 지나침 뒤 복구가 낫다 (EXP-13 오프라인 근거).
- [가설] FT 는 정상 접근·파지를 잃지 않는다.
- 사전 판정 기준: 없음 (파일럿 — 시행 수가 판정에 부족하다는 점을 계획 단계에서 명시). 판정 = eval_ui 의 사용자 P/F.

## 데이터셋
학습 데이터 없음 (평가). 평가 기록 dataset (rollout, 영상 포함) 은 Git 제외 — 경로·해시는 [ARCHIVE](#원본-자료).

## 모델·학습
| | BL | FT |
|---|---|---|
| 체크포인트 | d2 020000 `…/main_k8/d2/train/32_20000/pi05_expert_bs32_20k/checkpoints/020000/pretrained_model` | rft01 001000 `…/main_k8/d2/recovery_ft/runs/rft01_d2rc16_W5_1k_s2001/checkpoints/001000/pretrained_model` |
| `model.safetensors` SHA-256 | `6c46dee79b167c48ad24b6af739157dc22636505c4c838815a4bf3656a364886` | `620c45988a35b77e76b5c0869c560697d9d095143aceee33b98946a7db712af9` |
| 학습 | [EXP-06](../06_d2_256/README.md) | [EXP-13](../13_recovery_ft/README.md) |

- [사실] c01 검증 (`sources/rft01_real_pilot/logs/c01_verify_models.json`): SHA · config · normalizer · tokenizer 동일 항목 PASS. M7 action 범위 규칙 FAIL 1 건 — FT 의 wrist_flex 최소 30.0 vs BL 38.2, U8/K7 재추론 상태에서만 (파일럿 자리 아님).
- [사실] 시행 후 p00b 점검: BL run VERIFY_OK. FT run 은 F4 `checkpoint 020000` 1 항목만 FAIL — d2 점검 스크립트가 경로를 020000 으로 고정한 항목이며, FT 체크포인트는 manifest SHA-256 으로 확인.

## 추론 설정
두 모델 같음 [사실, `command.txt` · CHECK_OK 출력]: `lerobot-rollout` episodic, RTC guided, prefix schedule EXP, max_guidance_weight 10, execution_horizon 20, queue_threshold 30, num_inference_steps 5, chunk 50, `max_relative_target=8` (8°/tick clamp), fps 30, **Arm Filter OFF** (`--rollout_guard=warn` 은 기록만), `--r2_safety=stop`, `--fault_latch=stop`, 자동 복귀 끔 (`--return_to_initial_position=false`, `--strategy.reset_to_initial_position=false`, `eval/end_hold.py`), 판 최대 60 s, 과제 문장 `pick up the red cube and put it in the brown box`.

## 평가 방법
- 실물, 판정 = eval_ui 사용자 P/F (사람). 자동 지표 (첫 닫힘, 빈 닫힘, Pan 지나침, Wrist 놓침) 는 `scripts/trial_auto.py` 의 [자동 후보].
- 시행표 [`config/pilot_plan.csv`](sources/rft01_real_pilot/config/pilot_plan.csv): 8 쌍 (P1–P8), 쌍마다 같은 자리·각도에서 FT·BL 각 1 회.
  - Known (1–8): K3 0° · K1 0° · K3 R30 · K1 L30.
  - Unknown (9–16): U2 L30 (K3 에서 3.5 cm) · U7 45° (K6 에서 5.7 cm) · U8 0° (K4 에서 3.5 cm) · U1 R30 (K2 에서 4.47 cm). 이 U 는 파일럿 계획 자리이며 Held-out H 의 U1–U8 (지정 좌표, `configs/layouts/redbox8_heldout_h.yaml`) 과 **다르다**.
- 실행 방식: 1–5 는 시행당 1 프로세스 (`run_trial.sh`), 6–7 · 8–12 · 13–16 은 모델 1 회 로딩 세션 (`run_series.sh`, 판 사이 E5 복귀). 복귀는 사용자 실행 `safe_home.py --auto`.

## 평가 결과
| # | 쌍 | 모델 | 조건 | 놓인 곳 [기록, 시작 사진] | 시작 그리퍼 | 판정 | 길이 s | 닫힘 [자동 후보] | Pan 지나침 최대 ° |
|---:|---|---|---|---|---:|---|---:|---|---:|
| 1 | P1 | FT | K3 0° | K3 0.6 cm · +7° | 0.0 | **P** | 18.0 | 첫 닫힘 9.9 s 파지, 닫힘 2 | 15.1 |
| 2 | P1 | BL | K3 0° | K3 0.5 cm · −1° | 0.55 | **F** | 58.8 | 9.4 s 빈 닫힘, 빈 닫힘 4, 파지 없음 | 8.1 |
| 3 | P2 | BL | K1 0° | K1 0.2 cm · −0° | 0.0–2.6 | **P** | 26.5 | 16.5 s 파지, 닫힘 2 | 3.5 |
| 4 | P2 | FT | K1 0° | K1 0.3 cm · +3° | 0.0–2.6 | **P** | 26.7 | 13.4 s 파지, 닫힘 2 | 6.9 |
| 5 | P3 | FT | K3 R30 | K3 0.6 cm · −27° | 0.0–2.6 | **P** | 21.4 | 11.5 s 파지, 닫힘 2 | 8.4 |
| 6 | P3 | BL | K3 R30 | K3 0.4 cm · −34° | 0.0–2.6 | **F** | 58.9 | 14.2 s 빈 닫힘, 빈 닫힘 8 (+판정불가 3), 파지 없음 | 3.6 |
| 7 | P4 | BL | K1 L30 | K1 0.9 cm · **각도 못 잼** | **30.6** | **P** | 30.5 | 0.5 s 닫힘 ※, 닫힘 4 | 2.0 |
| 8 | P4 | FT | K1 L30 | K1 0.4 cm · +36° | 0.6 | **F** | 58.8 | 9.2 s 빈 닫힘, 이후 닫힘 없음 | 6.7 |
| 9 | P5 | FT | U2 L30 | 계획과 1.0 cm · 사진 판정 Known (K3 3.0 cm) ⚠ · +24° | 1.1 | **F** | 59.3 | 18.7 s u · 21.6 s 파지 · 이후 5 회 | 11.9 |
| 10 | P6 | FT | U7 45° | 계획과 0.4 cm · Unknown · −39° | 2.3 | **P** | 17.1 | 9.1 s 파지 | −2.0 |
| 11 | P7 | FT | U8 0° | 계획과 0.4 cm · Unknown · +0° | 0.5 | **F** | 59.3 | 9 회, 파지 없음 (empty 3 · u 6) | 8.7 |
| 12 | P8 | FT | U1 R30 | 계획과 0.5 cm · Unknown · −29° | 1.1 | **F** | 59.3 | 7 회, 파지 없음 (u 5 · empty 2) | 2.9 |
| 13 | P5 | BL | U2 L30 | 계획과 0.9 cm · Unknown (K3 3.5 cm) · +21° | **24.8** | **F** | 58.8 | 0.1 s ※ · 27.0 s 빈 닫힘 · 50.1 s 파지 · 이후 2 회 | 9.4 |
| 14 | P6 | BL | U7 45° | 계획과 0.6 cm · Unknown · −44° | **24.5** | **P** | 15.2 | 0.1 s ※ · 파지 | −5.2 |
| 15 | P7 | BL | U8 0° | 계획과 0.9 cm · 사진 판정 Known (K4 2.6 cm) ⚠ · +1° | **24.5** | **P** | 22.5 | 0.6 s ※ · 11.7 s 파지 | 14.6 |
| 16 | P8 | BL | U1 R30 | 계획과 0.2 cm · Unknown · −37° | **24.5** | **P** | 28.6 | u 3 회 (1.6 s ※ 포함) · 파지 | 3.8 |

- 시작 그리퍼: 1–2 는 `results/trials.csv`, 8–16 은 `pilot_summary_t08_t16.md`. 3–6 은 개별 값 대신 요약의 범위 (0.0–2.6) 만 있다.
- ※ 시작 그리퍼가 열린 판 (7, 13–16) 의 첫 0.1–1.6 s 닫힘은 열린 그리퍼가 닫히는 것 (파지 시도 아님). 이 판들의 자동 '첫 닫힘' 값은 쓰지 않는다.
- Pan 지나침 = 시작 사진의 자리에서 계산한 목표 pan (pe) 을 넘어간 최대 각도 [자동 후보]. 음수 = 넘지 않음.

| 구간 [사람 P/F] | FT | BL |
|---|---:|---:|
| Known, 1–8 | **3/4** (1 · 4 · 5) | **2/4** (3 · 7) |
| Unknown, 9–16 | **1/4** (10) | **3/4** (14 · 15 · 16) |
| 전체 1–16 | **4/8** | **5/8** |
| 첫 닫힘 = 파지, 1–7 [자동 후보] | 3/3 | 1/4 |
| K3 (0° · R30) | 2/2 P | 0/2 P (빈 닫힘 4 · 8) |

## 교란 (통제되지 않은 차이)
1. [사실] **Unknown 구간 그리퍼 시작 상태가 모델과 완전히 겹친다**: FT 8–12 는 닫힘 (0.5–2.3), BL 13–16 은 열림 (24.5–24.8). 원인 — 판 사이 E5 복귀가 그리퍼를 '세션 시작 값' 으로 돌리고, 세션 끝 (teardown) 복귀는 팔만 옮김. FT 세션 마지막 판 (12) 이 열린 채 끝나 그 값이 BL 세션 시작 값이 됨 (실행 도구 설계 결함 — Claude).
2. [사실] **모델 순서가 교대되지 않음**: 6–7 BL 연속, 8–12 FT 연속, 13–16 BL 연속. 시간·잔여 상태 영향 통제 없음.
3. [사실] **K1 L30 쌍 (7/8)** 도 시작 그리퍼가 다름 (BL 30.6 열림, FT 0.6 닫힘). 시행 7 은 큐브 각도 측정 실패.
4. [사실] 시행 9 (U2) 와 15 (U8) 는 시작 사진 판정이 Known (K3 3.0 cm, K4 2.6 cm). 시행표 분류 (Unknown) 를 사후에 바꾸지 않았다.
5. [사실] 시행 5 실행 중 13:27–13:29 에 가짜 장치 시험 (GPU) 이 같이 돌았다 (inference_delay p50 13 vs 시행 3·4 12). 시행 5 의 `run_trial.sh` 는 실행 중 스크립트 수정 (Claude) 으로 eval_ui 종료 직후 중단, 판은 정상 저장, run_ledger 한 줄 수동 복구.
6. [사실] 조건당 1 회. K3 의 FT 2/2 vs BL 0/2 도 쌍 2 개.

→ **Unknown 결과를 FT 일반화 악화로, K3 결과를 FT 개선으로 확정할 수 없다.** 전체 모델 우열은 미결정.

## 실패 사례
- [자동 후보] BL K3 (2, 6): 첫 파지 전 빈 닫힘 반복 (4, 8+3), 끝내 파지 없음.
- [자동 후보] FT 8: 9.2 s 빈 닫힘 1 회 뒤 60 s 까지 추가 닫힘 없음.
- [자동 후보] FT 11 · 12: 닫힘 9 · 7 회, 파지 없음.
- [자동 후보] FT 9 · BL 13: 파지는 됐으나 (21.6 s · 50.1 s) 최종 F. 상자에 못 넣은 이유는 기록되지 않음.
- [기록] 시행 2 는 팔을 뻗은 채 끝남 (시작 자세와 최대 167°) → `safe_home.py --auto` 로 복귀, 이에 맞춰 H7 한계 140 → 210.

## 분석 결과
- [사실] 판 시작 1.5 s (팔 접힘, lift −92…−103) 의 pan: FT 시행 1 은 −7.6 → 47.3° (pe 32.1° 보다 +15.1° 지나침), BL 시행 2 는 +8.1° 지나침. 나머지 1–7 판은 pe 까지 26–36° 덜 감.
- [사실] Wrist 시야: 16 판 모두 놓친 구간 0 → 손목 시야 이탈 뒤 재획득 (R1 복구) 상황이 실물에서 생기지 않았다. **실물 R1 복구 능력은 이번에 검증되지 않았다.**
- [사실] r2_safety STOP 0 · FAULT 0 · 경고 0, fault_latch 발동 0, 손 개입 · 판 중 Ctrl+C 기록 없음 (16 판). |pan| 최대 47.3°, −109° 형 폭주 없음. 판 사이 복귀 8 회 · 세션 끝 복귀 2 회 모두 도착 (추종 오차 최대 5.8°).
- [사실] 시행 8 첫 시도 세션 (`20261105_134711_1k_t08_ft_series`) 은 모델 로딩 중 Ctrl+C 로 중단, 저장 판 없음 (`results/rest_…txt` 로 게이트 해제). 이후 시행 8 은 FT 세션 첫 판으로 실행.
- [가설] K3 에서 BL 의 빈 닫힘 반복 vs FT 의 첫 닫힘 파지는 EXP-13 의 R2 in-sample 조기 닫힘 감소와 같은 방향이지만, 오프라인 AHEAD 실물 상태에서는 변화가 없었으므로 연결은 미확인.

## 한계 및 미확인
- 조건당 1 회, 모델 순서 미교대, Unknown 구간 그리퍼 시작 교란 → 통계 비교 불가.
- fault_latch · r2_safety 의 실물 발동 동작은 이번에 한 번도 일어나지 않아 **실물 미검증** (가짜 장치 시험만: 오류 뒤 정책 명령 0, queue 30 → 0, 처리 약 0.03 s; unit 25/25 → v2 31/31).
- 시행 3–6 의 개별 시작 그리퍼 값은 요약에 범위로만 기록 (`reports/<run>/` 원본 표에서 다시 확인 가능).
- 실패 판의 원인 라벨 (사람) 없음. 사용자 상세 판정은 시행 1 만 `results/trials.csv` 에 있다.

## 다음 실험으로 이어진 이유
- [계획] 판 사이 · 세션 끝 복귀에서 그리퍼를 절대 목표 (닫힘) 로 맞추도록 실행 도구 수정 (값 확정 전 실물 정상 초기 조건 확인 필요). 원본 시행 기록은 고치지 않는다.
- [계획] FT/BL 을 판마다 번갈아, 같은 자리·각도·시작 관절·그리퍼에서 반복 → K3 차이 재현 여부와 Unknown 효과를 분리.
- [계획] 손목 시야 이탈이 실제로 생기는 조건 (R1 대상) 의 실물 평가는 별도 설계.
- 모두 사용자 승인 뒤 (실물 추가 평가 · HIL 수집 · GPU 학습 미실행).

## 원본 자료
- 복사본: [`sources/rft01_real_pilot/`](sources/rft01_real_pilot/) — scripts, config (pilot_plan · series), results (`trials.csv`, `run_ledger.csv`, manifests, home_logs), reports (pilot_summary 2 개 + run 별 `report.md` · `trial_auto.*` · `events.csv` · `joints_window.csv` · `ticks_ep1.csv` 해제본), eval 코드 (`rollout_logged.py`, `fault_latch.py`, `end_hold.py`), run 별 작은 로그 (`command.txt`, `console.log`, `debug.log`, `results.*`, `end_state.json`, `r2_safety.csv`, `fault_latch.csv`, `filter_log.csv`, `start_images/`), 시험 코드·로그 (`tests/`, `logs/tests/`). `tools/sync_sources.py` MAPPINGS.
- 축약·변환 ([DERIVED_MANIFEST.csv](../../DERIVED_MANIFEST.csv)): FT 세션 `debug.log` (3.2 MB) → `debug.log.condensed.log`, `ticks_ep1.csv.gz` → `.csv`, run 별 `dataset_state_action.csv` (parquet → csv).
- Git 제외 (원본에만): rollout `dataset/` (parquet · AV1 영상), `diag/` (chunks · obs · replay · ticks.csv), report `frames/` · `obs/` · `viewer/`, `analysis.npz`, 가짜 장치 출력 `tests/_out/`, `backup/`, `config/models.env` (경로·SHA 만 있음 — 같은 값이 `logs/c01_verify_models.json`). 경로·크기·SHA-256 은 [`sources/ARCHIVE_EXCLUDED.csv`](sources/ARCHIVE_EXCLUDED.csv).
- 원본 경로: `/home/user/so101_runs/main_k8/rft01_real_pilot` (911 MB).
