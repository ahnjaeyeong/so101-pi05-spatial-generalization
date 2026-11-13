# sgp01 실물 평가 — 사용자 실행 순서

작성 2026-11-13. 도구는 sgb01 실물 평가 (11-12, `main_k8/sgb01_real_eval`) 를 복사해 모델 · 시행표만 바꿨다.
- **3 단계 명령은 팔에 토크를 걸고 정책이 팔을 움직인다. 사용자가 직접 터미널에서 실행한다.** Claude 는 로봇 · 카메라에 연결하지 않았다.
- 모델: **sgp01 020000** = pi05_base → main_k8/sg_pin 유효 96판 (스티커 없는 큐브, 각도 0 / L30 / R30 / 45, 자리 72 곳) 20000 스텝, 한강 H200. SHA-256 3548d66d…fcb2b2492 (`config/models.env`, 검증 `logs/c01_verify_models.json` M1–M6 PASS).
- 큐브: **흰 스티커 없는** 빨간 큐브 (학습 데이터와 같음).

## 0. 시행표 (`config/pilot_plan.csv`, 16 판)

| 판 | 자리 | 각도 | 구분 | 비교 |
|---|---|---|---|---|
| 1–8 | K5 · U7 · K2 · HU3 · K8 · HU7 · K4 · U1 | 0° | K = 학습 자리, U = 학습에 없는 자리 | sgft01 (11-09) · sgb01 (11-12) 와 같은 자리 · 같은 순서 |
| 9–16 | 같은 8 자리 | 45 · L30 · R30 · L30 · R30 · 45 · L30 · R30 | 〃 | 돌린 큐브 (이전 모델은 0° 만 학습) |

## 1. 실행 전 점검

1. 다른 프로세스가 팔 · 카메라 · GPU 를 쓰지 않는지 (출력이 없어야 함):
   ```bash
   pgrep -af "lerobot|r12_collect|record_ui|eval_ui|teleop|sg_cam_preview" ; nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader ; fuser -v /dev/so101_follower /dev/cam_front /dev/cam_wrist
   ```
2. follower 12 V 전원 스위치에 손이 닿는 자리에 선다 (비상시 전원 차단 = 최종 정지). 팔을 뻗은 자세에서 전원을 끊으면 팔이 내려오니 받칠 준비.
3. 작업공간: 스티커 없는 큐브 1 개와 상자만 (방해물 없음). 카메라 · 상자 위치는 수집 때 그대로.
4. **시작 자세 = S0** (쉬는 자세처럼 팔을 접고 손목만 약 90° 돌린 자세, 그리퍼 닫힘). eval_ui 는 연결 순간 자세를 '처음 자세' 로 잡고 판 사이에 그 자세로 돌아간다.

## 2. 옵션 확인 (팔 · 카메라 연결 없음)

```bash
CHECK=1 ~/so101_runs/main_k8/sgp01_real_eval/scripts/run_trial.sh 1
```

## 3. 실행

```bash
MAXT=8 ~/so101_runs/main_k8/sgp01_real_eval/scripts/run_series.sh     # 1–8 판 (0°), 모델 1 회 로딩
~/so101_runs/main_k8/sgp01_real_eval/scripts/run_series.sh            # 그 뒤 9–16 판 (돌린 큐브)
```

- Enter → 모델 로딩 2–3 분 → '큐브 배치' 창의 윤곽 (자리 · 각도) 에 큐브를 놓고 → → 판 최대 60 s → P / F 입력 → 팔이 S0 로 돌아감 → 다음 판.
- 멈추거나 끝난 뒤 같은 명령을 다시 실행하면 남은 판부터 이어진다.

## 4. 자동 정지 규칙 (켜져 있는 것 전부)

| 규칙 | 조건 | 동작 |
|---|---|---|
| 숄더팬 명령 한계 (r2_safety) | 보내려는 숄더팬 명령 \|°\| > 104 | 그 판 정지 |
| 숄더팬 현재 한계 (r2_safety) | 현재 숄더팬 \|°\| > 100 | 그 판 정지 |
| 관절 멈춤 (r2_safety) | 팔 관절 \|명령 − 현재\| > 8° 이면서 틱당 움직임 < 0.3° 가 20 틱 연속 | 그 판 정지 |
| 추론 오류 (fault_latch) | 추론 스레드 예외 등 | 그 판 정지, 기록 |
| 판 시간 | 60 s | 자동 종료 |
| 한 틱 이동 제한 | 관절당 8° (max_relative_target) | 명령을 잘라 보냄 (정지 아님) |

- **꺼 둔 것**: 큐브 방향 지나침 정지 (over_target) = 0 (2026-11-12 사용자 요청).
- 판 사이 · 끝: 점검 뒤 15°/s 로 시작 자세 복귀. Ctrl+C = 그 자리 정지 (토크 유지), 전원 차단 = 최종 정지.

## 5. 끝난 뒤

Claude 에게 알리면 run 폴더 (`eval/rollouts/<시각>_…`) 를 읽고 분석한다.
