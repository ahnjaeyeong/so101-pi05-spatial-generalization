# 학습 설정 — pi05_15k

`train_summary.py` 가 `checkpoints/015000/` 의 설정과 학습 로그를 읽어 만든 파일 (같은 내용: training_params.csv).

| 구분 | 항목 | 값 | 설명 |
|---|---|---|---|
| 실행 | 학습 이름 | pi05_15k |  |
| 실행 | 학습 폴더 | $HOME/so101_runs/main/cubemark_v1/train/4_15000/pi05_15k |  |
| 실행 | 시간 | 2026-10-12 18:05:05 → 2026-10-13 03:59:11 (9시간 54분, 종료 코드 0) | launch 스크립트의 .time 파일 |
| 실행 | 속도 | 2.36 s/step | 마지막 진행 표시 기준 |
| 데이터 | dataset repo_id | oxr/so101_cubemark_v1 |  |
| 데이터 | dataset 위치 | $HOME/so101_runs/main/cubemark_v1/dataset |  |
| 데이터 | 과제 문장 | Pick up the red cube and place it on the X mark. | rollout 때 이 문장을 그대로 써야 한다 |
| 데이터 | 사용 에피소드 | 50 / 50 (전체) |  |
| 데이터 | 전체 프레임 (=샘플) | 38816 | 30 fps 기준 프레임 하나가 학습 샘플 하나 |
| 데이터 | fps | 30 |  |
| 데이터 | 이미지 증강 | 끔 | dataset.image_transforms.enable |
| 학습량 | steps | 15000 | 최적화 횟수 |
| 학습량 | batch size | 4 | GPU 한 번에 넣는 샘플 수 |
| 학습량 | gradient accumulation | 1 |  |
| 학습량 | GPU 수 (data parallel) | 1 |  |
| 학습량 | 실효 batch | 4 | batch × accumulation × GPU |
| 학습량 | 본 샘플 수 | 60,000 | steps × 실효 batch |
| 학습량 | epoch | 1.55 | 본 샘플 수 ÷ 전체 프레임 — 데이터를 몇 바퀴 봤는지 |
| 학습량 | 체크포인트 | 005000, 010000, 015000 | save_freq=5000 |
| 모델 | policy | pi05 |  |
| 모델 | 시작 가중치 | lerobot/pi05_base |  |
| 모델 | dtype | bfloat16 |  |
| 모델 | 학습 파라미터 | 4,143,404,816 | 전체 4,143,404,816 |
| 모델 | train_expert_only | False | true 면 action expert 만 학습 |
| 모델 | freeze_vision_encoder | False |  |
| 모델 | use_peft (LoRA 등) | False |  |
| 모델 | gradient_checkpointing | True | 메모리 절약 |
| 모델 | chunk_size / n_action_steps | 50 / 50 | 한 번 추론에 나오는 동작 수 / 그중 실행하는 수 |
| 모델 | num_inference_steps (학습 설정값) | 10 | flow 단계 — rollout 때 따로 바꿀 수 있다 |
| 모델 | image_resolution | [224, 224] |  |
| 최적화 | optimizer | adamw |  |
| 최적화 | learning rate (최고) | 2.5e-05 |  |
| 최적화 | learning rate (마지막) | 2.5e-06 |  |
| 최적화 | scheduler | cosine_decay_with_warmup |  |
| 최적화 | warmup steps | 500 | 설정값 1000 → steps 에 맞춰 자동 축소 |
| 최적화 | decay steps | 15000 | 설정값 30000 |
| 최적화 | betas | [0.9, 0.95] |  |
| 최적화 | eps | 1e-08 |  |
| 최적화 | weight decay | 0.01 |  |
| 최적화 | grad clip norm | 1.0 |  |
| 기타 | seed | 1000 |  |
| 기타 | num_workers | 4 | 데이터 로더 |
| 기타 | log_freq | 50 |  |
| 결과 | loss | 처음 0.095 (step 50) → 마지막 0.011 (step 15000), 최저 0.008 (step 12300) | 50 스텝마다 기록 300개 |
| 결과 | GPU 메모리 (최대) | 38.4 GB | nvidia-smi 프로세스 |
| 결과 | 시스템 메모리 (최대) | 66.7 GB | 통합 메모리 전체 사용량 |
