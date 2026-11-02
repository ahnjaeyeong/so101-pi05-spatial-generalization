# configs

| 경로 | 내용 |
|---|---|
| `training/<run_id>/` | 마지막 체크포인트의 `train_config.json`, `policy_config.json` (= pretrained_model/config.json), 실행 스크립트 `run_script.sh`, 시작·종료 시각 `time.txt`, `training_params.md` (있을 때) |
| `training/RUNS.csv` | 실행별 데이터·시작 가중치·freeze·batch·steps·LR·loss·시각·train_config SHA-256 |
| `checkpoints/CHECKPOINTS.csv` | 체크포인트 28개: 경로, `model.safetensors` 크기와 SHA-256 (가중치는 Git 에 없음, 원본 위치에 보관) |
| `checkpoints/model_sha256.txt` | `sha256sum` 원 출력 (2026-11-02 계산) |
| `datasets/DATASETS.csv`, `*_info.json` | LeRobot 데이터셋 23개 `meta/info.json` 사본과 편·프레임·카메라·SHA-256 |
| `layouts/` | 배치 설정: `redbox_layouts.yaml` (K1–K4, 옛 카메라), `redbox8_layouts.yaml` (K1–K8, 새 카메라 H 행렬·각도 규칙), `redbox8_heldout_h.yaml` (H 세트, 미확정) |
| `camera/camera_settings.md` | 카메라 노출·WB 결정 기록 |

주의: `train_config.json` 의 scheduler `num_warmup_steps`/`num_decay_steps` 는 설정값이다. LeRobot 은 실행 시 steps 에 맞춰 자동 축소한다 (실효값은 `training_params.md` 와 docs/02 3절).
재생성: `python3 tools/collect_run_metadata.py` (원본 읽기 전용).
