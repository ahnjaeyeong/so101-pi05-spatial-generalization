# LeRobot 학습 I/O 기록 — SUMMARY

- 자동 생성: 2026-11-07 20:12:21 (io_watch.sh → finalize.py), 폴더 `/home/user/io-capture/20261106-1607`
- 기록 간격 10 s. 모든 값은 읽기 전용 명령으로 얻었다. 표에 없는 값은 추정하지 않았다.

## 환경

| 항목 | 값 | 근거 파일 |
|---|---|---|
| 호스트명 | localhost.localdomain | env/system.txt |
| 장비 종류 | NVIDIA Jetson AGX Thor Developer Kit (Thor) | env/system.txt |
| OS | Ubuntu 24.04.4 LTS, kernel 6.8.12-1021-tegra | env/system.txt |
| CPU 코어 수 | 14 | env/system.txt |
| RAM | 128,828,564 kB (≈122.9 GiB) | env/system.txt |
| GPU | NVIDIA Thor, 595.78 | env/system.txt |
| 데이터셋 폴더 FS·장치 | ext4, /dev/nvme0n1p1 (936G) WD PC SN5000S SDEPNSJ-1T00 nvme | env/storage.txt |
| 학습 출력 폴더 FS·장치 | ext4, /dev/nvme0n1p1 (936G) WD PC SN5000S SDEPNSJ-1T00 nvme | env/storage.txt |
| lerobot 버전 | 0.6.2 | env/versions.txt |
| torch / torchcodec / av | 2.11.0 / 0.11.1 / 15.1.0 | env/versions.txt |
| 학습 시 영상 디코딩 백엔드 | torchcodec | train/train_config.json |

## 학습 설정

| 항목 | 값 | 근거 파일 |
|---|---|---|
| 실행 명령 | `/home/user/so101-env/bin/python /home/user/so101-env/bin/lerobot-train --dataset.repo_id=oxr/so101_sg50_pilot3 --dataset.root=/home/user/so101_runs/practice/sg50_pilot3/train/sgft01_p3_10k_s2001/dataset --dataset.episodes=[3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42] --policy.path=/home/user/so101_runs/main_k8/d2/train/32_20000/pi05_expert_bs32_20k/checkpoints/020000/pretrained_model --policy.push_to_hub=false --policy.dtype=bfloat16 --policy.train_expert_only=true --policy.freeze_vision_encoder=true --policy.gradient_checkpointing=true --policy.optimizer_lr=1e-5 --policy.scheduler_warmup_steps=50 --policy.scheduler_decay_steps=10000 --policy.scheduler_decay_lr=2.5e-6 --output_dir=/home/user/so101_runs/practice/sg50_pilot3/train/sgft01_p3_10k_s2001/run --job_name=sgft01_p3_10k_s2001 --batch_size=32 --steps=10000 --log_freq=50 --save_freq=2500 --num_workers=4 --seed=2001 --wandb.enable=false` | train/cmdline.txt |
| 학습 로그 | /home/user/so101_runs/practice/sg50_pilot3/train/sgft01_p3_10k_s2001/train.log | train/cmdline.txt |
| train_config.json | /home/user/so101_runs/practice/sg50_pilot3/train/sgft01_p3_10k_s2001/run/checkpoints/last/pretrained_model/train_config.json | train/train_config.json |
| 정책 종류 | pi05 (pretrained /home/user/so101_runs/main_k8/d2/train/32_20000/pi05_expert_bs32_20k/checkpoints/020000/pretrained_model, dtype bfloat16) | train/train_config.json |
| 학습 범위 | train_expert_only=True, freeze_vision_encoder=True | train/train_config.json |
| 배치 크기 / num_workers | 32 / 4 (persistent_workers=True, prefetch_factor=4) | train/train_config.json |
| 총 스텝 / save_freq / log_freq | 10000 / 2500 / 50 | train/train_config.json |
| resume | False | train/train_config.json |
| 학습 파라미터 수 | 693,422,112 | steps/events.txt |
| 사용 카메라 / 정책 입력 해상도 | observation.images.front, observation.images.wrist / [224, 224], n_obs_steps=1 | train/train_config.json |
| 학습 프로세스 시작 / 기록 시작 | 2026-11-06 16:07:45 / 2026-11-06 16:07:51 | live/target.txt |
| 첫 학습 스텝 시작 (Start offline training) | 2026-11-06 16:10:38 | steps/events.txt |
| 학습 프로세스 종료 | 2026-11-07 20:11:28 (전체 28 h 03 m 43 s) | live/target.txt |
| 정상 종료 (End of training) | 예 | steps/events.txt |

## 데이터셋

| 항목 | 값 | 근거 파일 |
|---|---|---|
| 위치 | /home/user/so101_runs/practice/sg50_pilot3/train/sgft01_p3_10k_s2001/dataset | train/train_config.json |
| 포맷 | LeRobot codebase v3.0 | dataset/info.json |
| 에피소드 수 / 총 프레임 / fps | 43 / 35,998 / 30 (≈0 h 20 m 00 s 분량) | dataset/info.json |
| 카메라 수·해상도·코덱 | 2대: front 640×480 av1 g=2; wrist 640×480 av1 g=2 | dataset/info.json |
| 전체 용량 / 파일 수 | 254,305,444 B (254.3 MB) / 27 | dataset/du.txt |
| mp4 | 12개, 최소 5.508 / 중앙 13.334 / 최대 37.833 / 합계 252.4 MB | dataset/file_list.tsv |
| parquet | 13개, 최소 0.002 / 중앙 0.064 / 최대 0.291 / 합계 1.9 MB | dataset/file_list.tsv |
| mp4 front | 6개, 183.5 MB | dataset/file_list.tsv |
| mp4 wrist | 6개, 69.0 MB | dataset/file_list.tsv |
| 태스크별 에피소드 (프레임) | "pick up the red cube and put it in the brown box" 43 (35,998) | dataset/episodes_breakdown.txt |
| 에피소드 길이 | 최소 548 / 중앙 819 / 최대 1257 프레임 | dataset/episodes_breakdown.txt |

## 스텝 시간

| 항목 | 값 | 근거 파일 |
|---|---|---|
| 추출한 로그 줄 | 200줄 (log_freq 구간 평균값) | steps/steplines.txt |
| 워밍업 제외 | 처음 2줄 제외 | steps/steplines.txt |
| 평균 data_s | 0.0024 s (중앙 0.0020, p95 0.0040, 최대 0.0120) | steps/steplines.txt |
| 평균 prep_s | 0.0163 s (중앙 0.0160, p95 0.0170, 최대 0.0180) | steps/steplines.txt |
| 평균 updt_s | 10.0525 s (중앙 10.0210, p95 10.0480, 최대 11.8750) | steps/steplines.txt |
| 평균 step_s | 10.0738 s (중앙 10.0420, p95 10.0690, 최대 11.8980) | steps/steplines.txt |
| smp/s (로그 표시값 평균) | 3.00 | steps/steplines.txt |
| 데이터 로딩 비율 data_s / step_s | 0.024 % ((data_s+prep_s)/step_s = 0.19 %) | steps/steplines.txt |
| 워밍업 줄 data_s | 0.379, 0.002 | steps/steplines.txt |

## 학습 중 I/O

| 항목 | 값 | 근거 파일 |
|---|---|---|
| 시작 구간 (프로세스 시작~첫 스텝, 데이터셋·모델 로딩) 읽기·쓰기 | 읽기 0.01 MB/s, 쓰기 1.66 MB/s (합계 읽기 0.8 MB, 쓰기 267.1 MB, 0 h 02 m 41 s) | live/diskstats.log (nvme0n1p1) |
| 평상시 구간 (체크포인트 저장 제외) 읽기·쓰기 | 읽기 0.02 MB/s, 쓰기 0.05 MB/s (합계 읽기 1981.2 MB, 쓰기 5361.5 MB, 27 h 57 m 33 s) | live/diskstats.log (nvme0n1p1) |
| 체크포인트 저장 구간 (저장 시작-1 s ~ dirty 페이지가 64 MB 아래로 내려간 시점, 최소 끝+30 s) 읽기·쓰기 | 읽기 0.27 MB/s, 쓰기 201.87 MB/s (합계 읽기 61.6 MB, 쓰기 46422.3 MB, 0 h 03 m 50 s) | live/diskstats.log (nvme0n1p1) |
| 종료 후 구간 (프로세스 종료~꼬리 기록 끝, 체크포인트 구간 제외) 읽기·쓰기 | 읽기 0.00 MB/s, 쓰기 0.01 MB/s (합계 읽기 0.0 MB, 쓰기 0.2 MB, 0 h 00 m 14 s) | live/diskstats.log (nvme0n1p1) |
| 평상시 구간 간격별 분포 | 읽기 p95 0.00 / 최대 42.67 MB/s, 쓰기 p95 0.16 / 최대 28.75 MB/s | live/diskstats.log (nvme0n1p1) |
| 체크포인트 2500 저장 구간 | 쓰기 11587 MB (간격 최대 678 MB/s), 읽기 3 MB; dirty 최대 2362 MB → 38 s 뒤 64 MB 아래 | live/diskstats.log (nvme0n1p1), live/dirty.log |
| 체크포인트 5000 저장 구간 | 쓰기 11620 MB (간격 최대 921 MB/s), 읽기 0 MB; dirty 최대 2127 MB → 32 s 뒤 64 MB 아래 | live/diskstats.log (nvme0n1p1), live/dirty.log |
| 체크포인트 7500 저장 구간 | 쓰기 11605 MB (간격 최대 760 MB/s), 읽기 0 MB; dirty 최대 6346 MB → 38 s 뒤 64 MB 아래 | live/diskstats.log (nvme0n1p1), live/dirty.log |
| 체크포인트 10000 저장 구간 | 쓰기 11610 MB (간격 최대 2117 MB/s), 읽기 59 MB; dirty 최대 6360 MB → 8 s 뒤 64 MB 아래 | live/diskstats.log (nvme0n1p1), live/dirty.log |
| 종료 후 꼬리 기록 | 2026-11-07 20:11:28 ~ 2026-11-07 20:12:08 (40 s), 끝날 때 Dirty+Writeback 0 MB | live/target.txt |
| 에폭별 디스크 읽기량 (장치 전체) | epoch 0.x: 1676 MB / 3 h 01 m 54 s; epoch 1.x: 22 MB / 2 h 55 m 24 s; epoch 2.x: 22 MB / 2 h 56 m 14 s; epoch 3.x: 10 MB / 2 h 55 m 24 s; epoch 4.x: 175 MB / 2 h 47 m 25 s; epoch 5.x: 35 MB / 2 h 55 m 34 s; epoch 6.x: 23 MB / 2 h 55 m 35 s; epoch 7.x: 14 MB / 2 h 55 m 44 s; epoch 8.x: 5 MB / 2 h 55 m 24 s; epoch 9.x: 59 MB / 1 h 41 m 17 s | live/diskstats.log (nvme0n1p1) |
| 주의 | diskstats 는 장치(nvme0n1p1) 전체 값이다. 같은 시간에 돈 다른 프로세스의 I/O 도 포함한다 | live/diskstats.log |
| 메인 프로세스 read_bytes / write_bytes | 52.4 MB / 36551.5 MB (rchar 257.2 MB) | live/proc_io_summary.tsv |
| 자식 프로세스(워커 등) 5개 합계 read_bytes / write_bytes | 4.3 MB / 0.0 MB (rchar 42421.7 MB) | live/proc_io_summary.tsv |
| 기록 범위 | 프로세스 시작~마지막 기록(최대 기록 간격만큼 종료 직전 누락). /proc/<pid>/io 는 프로세스 시작부터의 누적값 | live/proc_io.log |
| GPU 사용률 (평상시 구간) | 평균 97.3 %, 중앙 98 % (n=10067) | live/gpu_util.csv |
| iostat | 미수집 (설치 안 됨) | live/iostat.log |

## 체크포인트

| 항목 | 값 | 근거 파일 |
|---|---|---|
| 이번 실행에서 저장한 개수 | 4 | ckpt/checkpoints.txt |
| 1회 크기 | 11,583,636,028 B (11.58 GB) / 11,583,636,029 B (11.58 GB) / 11,583,636,054 B (11.58 GB) / 11,583,636,056 B (11.58 GB) | ckpt/checkpoints.txt |
| 큰 파일 | pretrained_model/model.safetensors 9.35 GB, training_state/optimizer_state.safetensors 2.20 GB, pretrained_model/tokenizer/tokenizer.json 0.03 GB | ckpt/checkpoints.txt |
| 저장 간격 | 2500 스텝, 벽시계 7 h 04 m 39 s, 6 h 58 m 57 s, 6 h 58 m 32 s, 6 h 58 m 30 s | steps/events.txt |
| 저장 1회 소요 시간 | 2500: 34.2 s, 5000: 8.7 s, 7500: 7.5 s, 10000: 7.3 s (로그 'Checkpoint policy' 시각 → 마지막 파일 mtime, 페이지 캐시 기준) | ckpt/checkpoints.txt |

## 메모리와 데이터셋 크기 비교

| 항목 | 값 | 근거 파일 |
|---|---|---|
| 데이터셋 크기 / RAM | 254 MB / 131,920 MB → RAM의 0.19 % | dataset/du.txt, env/system.txt |
| 두 번째 에폭부터 캐시 읽기 가능성 | 있음 (데이터셋 < RAM, 9.62 epoch 학습) | dataset/du.txt |
| 학습 프로세스 트리 rchar / read_bytes | 42679 MB / 57 MB → 비율 751.9 배 | live/proc_io_summary.tsv |
| 학습 중 free / cache 최소 | free 최소 666 MiB, cache 최소 45,226 MiB | live/vmstat.log |
| 학습 종료 직후 데이터셋 페이지 캐시 상주 | dataset/pagecache_at_end.txt 참고 (fincore) | dataset/pagecache_at_end.txt |

## 미수집·미확인 항목

| 항목 | 값 | 근거 파일 |
|---|---|---|
| 학습 중 I/O / iostat | 미수집 (설치 안 됨) | live/iostat.log |
