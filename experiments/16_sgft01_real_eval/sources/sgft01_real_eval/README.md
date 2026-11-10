# sgft01 실물 평가 (2026-11-09 준비)

- 사용자 순서: `RUN_REAL_EVAL.md`.
- 출처: `main_k8/rft01_real_pilot` (11-05) 의 scripts · eval/*.py · tests 를 복사하고 경로 `rft01_real_pilot` → `sgft01_real_eval` 만 바꿈. 바꾼 것:
  - `config/models.env`: FT = practice/sg50_pilot3/train/sgft01_p3_10k_s2001 checkpoint 010000 (SHA-256 7da73701…78797327), BL (d2 020000) 은 계획에 없음.
  - `config/pilot_plan.csv`: 8 판, 모두 ft · 각도 0, K5 · U7 · K2 · HU3 · K8 · HU7 · K4 · U1.
  - `scripts/run_series.sh`: 남은 시행을 1 번부터 (원래 2 번부터 — rft01 은 1 번을 run_trial 로 따로 함), 안내 글 모델 이름.
  - `scripts/c01_verify_models.py`: M1 = models.env SHA, M2 = 다른 저장 체크포인트 존재, M7 = sgft01 오프라인 테스트 배열 (기록만). 결과 `logs/c01_verify_models.json` M1–M6 PASS.
- 수정하지 않은 공용 코드: ~/so101_boxpick/scripts/eval_ui.py, main_k8/r2_grasp_diagnostic/eval (rollout_logged · r2_safety).
