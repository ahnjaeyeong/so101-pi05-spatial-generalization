# sgft01 실물 평가 — 사용자 실행 순서

작성 2026-11-09.
- **3 단계 명령은 팔에 토크를 걸고 정책이 팔을 움직인다. 사용자가 직접 터미널에서 실행한다.** Claude 는 로봇 · 카메라에 연결하지 않았다.
- 도구는 rft01 실물 파일럿 (`main_k8/rft01_real_pilot`, 11-05) 을 그대로 복사해 경로 · 모델 · 시행표만 바꿨다 (eval_ui · R2 안전 정지 r2_safety · fault_latch · end_hold · safe_home · run_series v3.1).
- 모델: **sgft01 010000** = d2 020000 → 예비3 (practice/sg50_pilot3 ep3–42) 10000 스텝. SHA-256 7da73701…78797327 (`config/models.env`, 검증 `logs/c01_verify_models.json` M1–M6 PASS).

## 0. 시행표 (`config/pilot_plan.csv`, 8 판, 모두 각도 0°)

학습에 쓴 K 자리와 학습에 없는 평가 전용 자리 (U) 를 번갈아. K1 · H_U5 · H_U8 은 수직 최대거리 밖, K7 은 수집 때 기울기가 늘 튀어서 뺐다.

| 판 | 자리 | 좌표 cm | 구분 |
|---|---|---|---|
| 1 | K5 | (−17.0, 11.5) | 학습 자리 (첫 안전 확인 — 가깝고 정면) |
| 2 | U7 | (−15.5, 2.0) | 학습에 없는 자리 (pilot U7) |
| 3 | K2 | (−8.5, 11.5) | 학습 자리 |
| 4 | HU3 | (−10.6, 9.5) | 학습에 없는 자리 (H U3) |
| 5 | K8 | (−25.5, −3.5) | 학습 자리 |
| 6 | HU7 | (−14.6, 20.0) | 학습에 없는 자리 (H U7) |
| 7 | K4 | (−17.0, 26.5) | 학습 자리 |
| 8 | U1 | (−6.5, 15.5) | 학습에 없는 자리 (pilot U1) |

## 1. 실행 전 점검

1. 다른 프로세스가 팔 · 카메라 · GPU 를 쓰지 않는지 (출력이 없어야 함):
   ```bash
   pgrep -af "lerobot|r12_collect|record_ui|eval_ui|teleop|sg_cam_preview" ; nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader ; fuser -v /dev/so101_follower /dev/cam_front /dev/cam_wrist
   ```
2. follower 12 V 전원 스위치에 손이 닿는 자리에 선다 (비상시 전원 차단 = 최종 정지). 팔을 뻗은 자세에서 전원을 끊으면 팔이 내려오니 받칠 준비.
3. 작업공간: 큐브 1 개와 상자만. 카메라 · 상자 위치는 수집 때 그대로.
4. **시작 자세 = S0** (수집과 같음): 쉬는 자세처럼 팔을 접고 손목만 사진처럼 약 90° 돌린 자세, 그리퍼 닫힘. eval_ui 는 연결 순간 자세를 '처음 자세' 로 잡고, 판 사이에 그 자세로 천천히 돌아간다 (그리퍼도 그 값으로). → **연결 전에 팔을 S0 에 두고 시작**.
5. 정책은 수집처럼 숄더팬 → 그리퍼 열기 → 찾기 → 이동 → 닫기 → 상자 → S0 로 움직이도록 학습됐다.

## 2. 옵션 확인 (팔 · 카메라 연결 없음)

```bash
CHECK=1 ~/so101_runs/main_k8/sgft01_real_eval/scripts/run_trial.sh 1
```
`CHECK_OK ... RTCConfig(... EXP ... execution_horizon=20) ... max_relative_target=8.0 ... arm_filter=False ... guard=warn` 가 나오면 된다.

## 3. 실행 (8 판 연속, 모델 1 회 로딩)

```bash
~/so101_runs/main_k8/sgft01_real_eval/scripts/run_series.sh
```

- eval_ui 가 `Enter = 시작` 을 물으면 Enter → 모델 로딩 2–3 분 (그 동안 '큐브 배치' 창이 뜨고 이번 판 자리 윤곽이 보임).
- **⏸ 준비**: 큐브를 창 윤곽 자리에 0° 로 놓고 '맞음' 이 뜨면 → (또는 Enter).
- **▶ 실행**: 판 최대 60 s.
- 판이 끝나면 P (성공) / F (실패) 와 메모를 묻는다 → 입력하면 팔이 처음 자세 (S0) 로 돌아가고 다음 판 '준비'.
- 다 끝나거나 멈추면, 같은 명령을 다시 실행하면 남은 판부터 이어진다.

### 판 끝 기준

| 상황 | 하는 일 |
|---|---|
| 큐브를 상자에 넣고 팔이 물러남 | → (판 끝) — 성공 P |
| 60 s 경과 | 자동 종료 — 그때까지 상자에 없으면 F |
| 안전 정지 (r2_safety: 숄더팬 한계 · 큐브 방향 크게 지나침 · 관절 멈춤) · 추론 오류 (fault_latch) | 자동 종료 (콘솔 `R2_SAFETY STOP` / `FAULT_LATCH`) → F, 메모에 적기 |
| 위험해 보임 | Ctrl+C (그 자리 정지, 토크 유지) 또는 전원 차단 |

- 판정 기준 메모 권장: 첫 시도에 잡았는지 · 다시 맞추기 횟수 · 그리퍼를 숄더팬 뒤 바로 열었는지 · 닫을 때 손목 주황 프레임과 맞았는지 (분석은 끝난 뒤 Claude 가 영상 · 기록으로).
