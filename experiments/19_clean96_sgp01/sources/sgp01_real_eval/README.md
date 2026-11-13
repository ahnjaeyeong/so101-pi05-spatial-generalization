# sgp01 실물 평가 (2026-11-13 준비)

- 사용자 순서: `RUN_REAL_EVAL.md`.
- 출처: `main_k8/sgb01_real_eval` (11-12) 의 config · eval/*.py · scripts · tests 를 복사하고 경로 `sgb01_real_eval` → `sgp01_real_eval` 로 바꿈 (rollouts · results · logs · stuck_probe 는 복사 안 함). 바꾼 것:
  - `config/models.env`: FT = main_k8/sg_pin/train/sgp01_pin96_20k_s2001 checkpoint 020000 (SHA-256 3548d66d…fcb2b2492).
  - `config/pilot_plan.csv`: 16 판 = 1–8 sgb01 과 같음 (0°) + 9–16 같은 자리에 각도 45 · L30 · R30 · L30 · R30 · 45 · L30 · R30.
  - `scripts/run_series.sh`: 안내 글 모델 이름, `MAXT=n` (시행 n 까지만).
  - `scripts/c01_verify_models.py`: 체크포인트 경로. M2 = 한강 기록 SHA (checkpoints_sha256.txt) 와 내려받은 파일 일치 + DONE. M3 학습 키에 gradient_checkpointing 추가. M5 = normalizer / unnormalizer 의 action · state q01 · q99 가 sg_pin/dataset/meta/stats.json 과 같음 (sgp01 은 자체 통계로 학습). M7 기록 없음. 결과 M1–M6 PASS.
  - `tests/test_series_sgb01.sh` → `tests/test_series_sgp01.sh` (가짜 run_trial · safe_home, 로봇 없음): `MAXT=8` 로 G1–G4 ALL_PASS.
- 체크포인트 `tokenizer/` 폴더: 브라우저로 내려받을 때 빠져 있어서 sgb01h 010000 의 것을 복사 (tokenizer.json · tokenizer_config.json 은 d2 · sgb01 · sgb01h 가 byte 동일, SHA 7336bb4c… · 247bcda9…).
- 확인: `CHECK=1 scripts/run_trial.sh 1` → CHECK_OK (RTC EXP h20 · queue 30 · arm_filter False · guard warn), 팔 · 카메라 연결 없음.
- `--r2_safety.over_target_deg=0` 유지 (sgb01 때 사용자 요청). 숄더팬 |cmd| 104 · |present| 100 · 관절 멈춤 · fault_latch 는 그대로.
