# sgb01 실물 평가 (2026-11-12 준비)

- 사용자 순서: `RUN_REAL_EVAL.md`.
- 출처: `main_k8/sgft01_real_eval` (11-09) 의 config · eval/*.py · scripts · tests 를 복사하고 경로 `sgft01_real_eval` → `sgb01_real_eval` 만 바꿈. 바꾼 것:
  - `config/models.env`: FT = practice/sg50_pilot3/train/sgb01_p3_10k_s2001 checkpoint 010000 (SHA-256 01b22017…3d62eed4).
  - `config/pilot_plan.csv`: sgft01 과 같음 (8 판, 각도 0, K5 · U7 · K2 · HU3 · K8 · HU7 · K4 · U1).
  - `scripts/run_series.sh`: 안내 글 모델 이름.
  - `scripts/c01_verify_models.py`: 체크포인트 · 오프라인 raw 경로 sgb01, M7 = sgft_010000 · sgb_010000 배열 (기록만). 결과 `logs/c01_verify_models.json` M1–M6 PASS.
  - `tests/test_series_sgft01.sh` → `tests/test_series_sgb01.sh` (가짜 run_trial · safe_home, 로봇 없음): G1–G4 ALL_PASS.
- 확인: `CHECK=1 scripts/run_trial.sh 1` → CHECK_OK (RTC EXP h20 · max_relative_target 8.0 · arm_filter False · guard warn), 팔 · 카메라 연결 없음.
- 수정하지 않은 공용 코드: ~/so101_boxpick/scripts/eval_ui.py, main_k8/r2_grasp_diagnostic/eval (rollout_logged · r2_safety).
- 2026-11-12 09:35 (사용자 요청): `scripts/run_trial.sh` 에 `--r2_safety.over_target_deg=0` 추가 (큐브 방향 30° 지나침 정지 끔; 숄더팬 |cmd| 104 · |present| 100 · 관절 멈춤 · fault_latch 는 그대로). 백업 `scripts/run_trial.sh.bak_20261112_0935`.
  - 첫 세션 run `20261112_092137_…_ft_series` (over_target 정지 4 회, 9.9 s 판 1 개 판정 없이 저장) 은 `results/run_ledger_excluded.csv` 로 옮김 (원본 `results/run_ledger.csv.bak_20261112_0935`), run 폴더는 그대로 → 다음 run_series 는 1 번부터.
