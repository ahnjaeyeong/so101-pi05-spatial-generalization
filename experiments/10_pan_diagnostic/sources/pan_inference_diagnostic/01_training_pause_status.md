# 01 sampling_ablation 학습 일시정지 상태

작성 2026-10-29 11:50, 5 절은 14:00 에 채움 (A2 완료 · 큐 정지 확인 뒤).

## 1. 확인 시점 상태 (2026-10-29 11:24–11:26)

| 항목 | 값 | 근거 |
|---|---|---|
| 큐 | `run_queue.sh` pid 1407380 (setsid, 10-27 17:30 시작), 순서 A0_s2001 → A1_s2001 → A2_s2001 → A2r_s2001 → A0_s2002 | `ps`, `runs/queue.log` |
| 끝난 실험 | A0_s2001 (10-28 09:46 rc 0, 점검 통과, eval_hook OK), A1_s2001 (10-29 00:34 rc 0, 점검 통과, eval_hook OK) | queue.log |
| 실행 중 | **A2_s2001** pid 2790079 (10-29 02:28:37 시작), step ≈ 3,100 / 4,000, 10.9–11.2 s/step, loss 0.020, lr 3.4e-6 | `runs/A2_s2001.log` |
| 남은 실험 | A2r_s2001, A0_s2002 (시작 안 함, 폴더 없음) | `runs/` |
| 마지막 저장 체크포인트 (A2) | `runs/A2_s2001/checkpoints/002000` (08:08), `last → 002000`. 다음 저장 004000 (마지막 step) | ls |
| 002000 training_state | optimizer_state.safetensors 2,195,136,504 B · optimizer_param_groups.json · scheduler_state.json (last_epoch 2000, lr 6.25e-6) · rng_state.safetensors · training_step.json (step 2000) | ls, json |
| GPU | compute 프로세스 1 개 (A2, 21,047 MiB), 사용률 98 % | nvidia-smi |
| d4 · 기타 학습 | 없음 (d4 는 10-27 22:28 에 010000 에서 멈춘 상태 그대로) | ps |
| 다른 감시 프로세스 | `ops/wait_queue_event.sh 17` pid 2790277 — 다른 Claude 세션 (pid 3007964) 이 queue.log 17 번째 줄 다음 줄을 기다림. 건드리지 않음 | ps |

## 2. 재개 가능성 판단

- `train_weighted.py` 는 `--resume` 을 막는다 (`train_weighted.py:121-122`, 새 fine-tune 만 허용). 따라서 A2 를 004000 전에 멈추면 002000 체크포인트가 있어도 **같은 실행으로 이어서 학습할 수 없고** A2 를 처음부터 다시 해야 한다 (≈ 11 h).
- lerobot 에는 신호를 받으면 저장하는 기능이 없다 (10-27 d4 중단 때 확인: SIGINT 로 120 s 안에 끝나지 않아 SIGTERM, 15 step 잃음).
- A2 는 11:25 기준 약 900 step (≈ 2 h 45 m) 남았다. 004000 은 A2 의 마지막 저장점이다.

## 3. 한 조치 (2026-10-29 11:25:47)

**프로세스는 하나도 멈추거나 죽이지 않았다.** A2 를 004000 까지 정상으로 끝내고, 큐가 그다음에 스스로 멈추게 했다.

| 조치 | 효과 |
|---|---|
| `chmod -x runs/run_A2r_s2001.sh` | A2 점검이 끝난 뒤 큐의 다음 반복에서 `[ -x runs/run_A2r_s2001.sh ] \|\| stop "… 없음"` 에 걸려 `runs/QUEUE_STOPPED` 를 쓰고 exit 4 (큐 스크립트의 정상 정지 경로) |
| `chmod -x eval_hook.sh` | A2 뒤 eval_hook (A2 오프라인 평가, GPU ≈ 2 h) 를 건너뜀 → GPU 가 A2 직후 비게 함. A2 평가는 재개 때 따로 실행 |
| `runs/PAUSE_NOTE_pan_diag.txt` | 위 내용과 재개 방법 메모 |

- 큐 스크립트 (`run_queue.sh`) 내용은 고치지 않았다 (실행 중인 bash 스크립트).
- A2 의 004000 뒤 점검 (rc 0, 002000 · 004000 training_step, last → 004000, nan/OOM 없음, 가중 sampler 흔적, d2 sha256) 은 큐가 그대로 한다.
- 체크포인트 · 결과 파일은 덮어쓰거나 지우지 않았다.

## 4. 재개 절차 (자동으로 재개하지 않음)

```bash
cd ~/so101_runs/main_k8/d2/sampling_ablation
chmod +x runs/run_A2r_s2001.sh eval_hook.sh
./eval_hook.sh A2_s2001 >> runs/eval_hook_A2_s2001.log 2>&1      # A2 평가 (GPU ≈ 2 h)
# 남은 A2r_s2001 · A0_s2002: run_queue.sh 는 이미 있는 runs/A0_s2001 등에서 멈추므로 그대로 다시 돌릴 수 없다.
#   RUNS=(A2r_s2001 A0_s2002) 로 바꾼 사본 (예: ops/run_queue_resume.sh) 을 만들어 setsid nohup 으로 시작한다.
```

- 남은 두 실험은 모두 d2 020000 에서 시작하는 새 fine-tune 이고 seed 가 고정 (2001, 2002) 이라, 중단 때문에 잃는 상태가 없다 (sampler 순서는 (seed, epoch) 로 정해짐 — `train_weighted.py:8-9`).

## 5. A2 완료 · 큐 정지 결과

확인 2026-10-29 13:58:54 (대기 스크립트) · 13:59:12 (수동).

| 항목 | 값 | 근거 |
|---|---|---|
| A2_s2001 종료 | 13:58:31 rc 0 (02:28:37 시작, 11 h 30 m). 마지막 log: `Model weights successfully saved … /004000/pretrained_model` (13:58:16), `End of training` (13:58:18), 4000/4000 | `A2_s2001.time`, `A2_s2001.log` |
| 큐 점검 | `13:58:41 A2_s2001 checks OK (last loss:0.019, weighted list 203776)` | `queue.log` |
| 큐 정지 | `13:58:41 STOP: runs/run_A2r_s2001.sh 없음` → `runs/QUEUE_STOPPED` 생성, 큐 pid 1407380 없음 | `queue.log`, `QUEUE_STOPPED`, `ps` |
| A2 004000 | `pretrained_model/` (model.safetensors, config, pre/post processor, tokenizer, train_config) + `training_state/` (optimizer_state, optimizer_param_groups, scheduler_state last_epoch 4000 · lr 2.5e-6, rng_state, training_step step 4000). 11 GB. `last → 004000`. 002000 그대로 있음 | ls, json |
| A2 오프라인 평가 (eval_hook) | 실행 안 됨 (`eval_hook.sh` 실행권한 없음, `eval_hook_A2_s2001.log` 없음) — 재개 때 4 절 명령으로 실행 | ls |
| A2r_s2001 · A0_s2002 | 시작 안 됨 (폴더 없음). `run_A2r_s2001.sh` 는 `-rw-r--r--` 그대로 | ls |
| GPU | compute 프로세스 0 개, 사용률 1 % (13:59:12) | nvidia-smi |
| 다른 감시 프로세스 | `wait_queue_event.sh` pid 2790277 은 이미 끝나 있음 (queue.log 21 줄). 그 세션 (pid 3007964) 은 그대로 | ps |
| 지운 · 덮어쓴 파일 | 없음 | — |

이후 GPU 사용: 이 진단의 오프라인 재추론 (`scripts/p03b_guided_recon.py`, `p04_harness.py`, `p05_replay_check.py`) 만. 학습 · 파인튜닝 없음.
