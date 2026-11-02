# d4 — T1 (K+R) + T3-R (main_k8)

작성 2026-10-26. 사용자 요청: "t1 128편이랑 t3 r 64편해서 총 192편 다시 파인튜닝".
d2 (T1 + T3 전체, 256편) 에서 **T3-K 64편을 뺀 것**. 나머지(학습 설정·문장·release 사본)는 d2 와 같다.

| 실험 | 학습 데이터 | 편수 | 상태 |
|---|---|---|---|
| d1 | T1 + T2 | (256) | T2 미녹화 |
| d2 | T1-K · T1-R · T3-K · T3-R | 256 | 학습 완료 10-26 00:50 |
| d3 | T1 + T2 + T3 | (384) | T2 미녹화 |
| **d4** | **T1-K · T1-R · T3-R** | **192** | **학습 시작 2026-10-26 14:20:39** |

과제 정의·수집 환경·release 사본 만드는 법과 확인 결과는 `../d2/description.md` (1–3절) 와 같다.

## 1. 데이터셋

- 경로: `~/so101_runs/main_k8/d4/dataset` · repo_id `oxr/so101_k8_d4` · 724 MB · task 1개 (`pick up the red cube and put it in the brown box`)
- 명령 (2026-10-26 14:20):

```bash
$HOME/so101-env/bin/lerobot-edit-dataset --new_repo_id oxr/so101_k8_d4 --new_root $HOME/so101_runs/main_k8/d4/dataset --operation.type merge \
  "--operation.repo_ids=[oxr/so101_k8_redbox_t1_known_release, oxr/so101_k8_redbox_t1_random_release, oxr/so101_k8_redbox_t3_random_release]" \
  "--operation.roots=[$HOME/so101_runs/main_k8/redbox_t1_known/release, $HOME/so101_runs/main_k8/redbox_t1_random/release, $HOME/so101_runs/main_k8/redbox_t3_random/release]"
```

| 합친 episode_index | 원본 | 제외한 원본 판 | 편수 | 프레임 | 판 길이 (s) 평균 / 중앙 / 최소–최대 |
|---|---|---|---|---|---|
| 0–63 | T1-K (`redbox_t1_known/release`) | 51, 64 | 64 | 33,974 | 17.7 / 17.5 / 11.9–23.8 |
| 64–127 | T1-R (`redbox_t1_random/release`) | 2, 36, 39, 41 | 64 | 32,758 | 17.1 / 16.8 / 13.0–25.9 |
| 128–191 | T3-R (`redbox_t3_random/release`) | 57 | 64 | 28,360 | 14.8 / 14.6 / 10.6–23.9 |
| 합 | | | 192 | 95,092 | |

- 과제별: T1 128편 · 66,732 프레임 (70%), T3 64편 · 28,360 프레임 (30%).
- T3-R: 위치 자유, 방해물 2~6개 (판 수 12 · 13 · 13 · 14 · 12), 빨강 각도 0 / L30 / R30 / 45 각 16판. 방해물 각도는 자유롭게 놓음.
- 빠진 것 (d2 대비): T3-K 64편 (빨강·방해물 모두 K1–K8 고정 위치, 방해물 1~3개).
- 확인 (2026-10-26): 판 길이 순서가 원본 3개를 이은 것과 일치. 각 원본의 첫·마지막 판 프레임(+5) action · state · front · wrist 6곳 모두 같음.

## 2. 학습

- 폴더 `~/so101_runs/main_k8/d4/train/32_20000/` — `run_pi05_expert_bs32_20k.sh`, `launch_pi05_expert_bs32_20k.sh` (d2 와 데이터셋·출력 경로만 다름).
- 설정: pi05 (`lerobot/pi05_base` 에서 시작), train_expert_only · freeze_vision_encoder, bf16, gradient checkpointing, AdamW lr 2.5e-5,
  cosine_decay_with_warmup (warmup 666 · decay 20000 → 2.5e-6), batch 32, 20,000 스텝, 5,000 스텝마다 저장, num_workers 4.
- 20,000 × 32 = 640,000 샘플 ≈ **6.7 epoch** (95,092 프레임). d2 는 5.2 epoch, redbox_all 은 3.4 epoch.
- 시작 2026-10-26 14:20:39 (pid 3000922). d2 실측 9.92 s/step 이면 약 55시간 → 끝 예상 2026-10-28 (수) 21시 무렵.
- I/O 기록: io-watch → `~/io-capture/20261026-1420/` (끝나면 SUMMARY.md · zip).

## 3. 정하지 않은 것

- 평가: d2 와 같은 방법(`../d2/eval/평가_명령.md`)으로 할지, 판 수·배치.

## 4. 폴더

```
main_k8/d4/
  description.md
  dataset/            합친 데이터셋 (oxr/so101_k8_d4)
  train/32_20000/     학습 스크립트·로그, 출력 pi05_expert_bs32_20k/
```
