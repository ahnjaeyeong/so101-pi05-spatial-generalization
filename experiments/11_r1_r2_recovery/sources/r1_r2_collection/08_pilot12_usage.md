# 08 · 파일럿 12편 실행 명령 (사용자가 직접)

모든 명령에 `--config ~/so101_runs/main_k8/r1_r2_collection/config/r12_pilot12.yaml` 를 붙인다.
- 빠뜨리면 기존 R1/R2 설정이 쓰인다. 그 경우 이 파일럿 세션은 '설정 groups 에 없음' 으로 거부된다.
- 녹화 (`record`) 는 실물 팔 토크를 켠다. 사용자가 터미널에서 직접 실행한다.

```bash
C=~/so101_runs/main_k8/r1_r2_collection
P="--config $C/config/r12_pilot12.yaml"
PY=~/so101-env/bin/python
```

## 1. 확인 (로봇 안 움직임)

```bash
$PY $C/tools/r12_collect.py menu $P                      # 12편 메뉴 · 시나리오별 시작 조건 · 목표 동작 · 명령
$PY $C/tools/r12_collect.py check $P                     # 환경 확인 (장치를 열지 않음)
$PY $C/tools/r12_collect.py status --session main_k8/r12_pilot12_r1 $P
cat ~/so101_runs/main_k8/r12_pilot12_r1/r12_sheet.md      # 판별 큐브 자리 · 각도 · 지나침 방향
```

계획은 이미 만들어 두었다:
- `~/so101_runs/main_k8/r12_pilot12_{r1,r2p,r2o}/r12_plan.csv`
- `r12_sheet.md`

## 2. 미리보기 (로봇 · 카메라 없음, 임시 폴더)

```bash
$PY $C/tools/r12_collect.py preview --group pilot12_r1  $P --episodes 2
$PY $C/tools/r12_collect.py preview --group pilot12_r2p $P --episodes 2
$PY $C/tools/r12_collect.py preview --group pilot12_r2o $P --episodes 2
```

## 3. 녹화 (실물 — 사용자만)

시작 전:
- 다른 로봇 프로그램 (eval_ui · lerobot-record · teleoperate 등) 을 끈다. 켜져 있으면 녹화가 시작되지 않는다.
- 첫 실행은 `--num 2` 로 짧게 한다.

```bash
$PY $C/tools/r12_collect.py record --session main_k8/r12_pilot12_r1  $P --num 2
$PY $C/tools/r12_collect.py record --session main_k8/r12_pilot12_r2p $P --num 2
$PY $C/tools/r12_collect.py record --session main_k8/r12_pilot12_r2o $P --num 2
```

다시 실행하면 이어 찍는다. 남은 편수는 `--num` 없이 실행하면 된다.

### 키 (기존과 같음)

| 키 | 동작 |
|---|---|
| → | 녹화 시작. R1 은 두 번 (첫 → = 안전 확인) |
| ← | 버리기 |
| 1 · 2 · 3 | 결과 입력 |
| m | 메모 |
| p | 이전 판 다시 보기 |
| Esc | 종료 |

### 화면

- 맨 위: 시나리오 이름 (R1 · R2-P · R2-O)
- 왼쪽 아래 '시작 조건': Pan · Lift · 그리퍼 열림/닫힘 · 손목 큐브 u/v · front 가시성 · R1 복구 방향 · 실패 상태와 비슷함
  - 달라도 녹화된다. 막는 것은 안전 조건뿐이다.
- 가운데: 녹화 상태 (준비 중 · 녹화 중 · 저장 완료 · 무효 시연) · 명령 보호 상태

### 명령 보호 (이 설정에서만 켬)

- 리더 Pan 이 ±95° 를 넘으면 팔로워는 95° 에서 멈춘다.
- 리더−팔로워 차이가 25° 를 넘으면 팔로워가 그 자리에 고정된다.
  - 화면에 '팔로워 고정 중' 이 뜨면 리더를 팔로워 자세 쪽으로 천천히 맞춘다 (±10°). 그러면 풀린다.
- 녹화 중에 걸리면 그 판은 '무효 시연' 으로 저장되지 않는다. 결과 단계에서 → 를 누르면 같은 번호를 다시 준비한다.

### 끝낼 때

팔을 쉬는 자세에 둔 뒤 Esc. 종료하면 토크가 꺼진다.

### 시나리오별 준비 (녹화 안 함)

| 시나리오 | 준비 | 녹화 |
|---|---|---|
| R1 | 그리퍼 닫힌 채 팔을 접고, 쉬는 자세 pan 에서 큐브 쪽으로 돌려 큐브 방향을 지나친 곳 (주황 선 근처, 대략) 에서 멈춤 · Pan 한계 근처 금지 | Pan 을 되돌려 재정렬 → 접근 · 파지 → 상자 → 쉬는 자세 |
| R2-P | 그리퍼 연 채 큐브 앞 파지 높이 근처에서 정지 (손목 화면 주황 영역, 대략) · 큐브에 닿지 않게 | 연 채 보정 → 한 번 닫기 → 상자 → 쉬는 자세 |
| R2-O | 그리퍼 닫힌 채 (쉬는 자세 그대로) 큐브 앞 파지 높이 근처로 → 정지 · 큐브에 닿지 않게 · 빈 파지 동작 하지 않음 | 먼저 충분히 열기 (약 30) → 연 채 접근 · 정렬 → 한 번 닫기 → 상자 → 쉬는 자세 |

## 4. 녹화 뒤 (읽기만)

```bash
$PY $C/tools/r12_collect.py qa     --session main_k8/r12_pilot12_r2o $P   # qa/r12_qa_report.md §5 · qa/r12_pilot_qa.csv
$PY $C/tools/r12_collect.py sync   --session main_k8/r12_pilot12_r2o $P   # r12_episodes.csv · r12_pilot_episodes.csv 다시 만듦
$PY $C/tools/r12_collect.py label  --session main_k8/r12_pilot12_r2o --episode 0 --result 1 $P
$PY $C/tools/r12_collect.py exclude --session main_k8/r12_pilot12_r2o --episodes 2 --reason "큐브를 밀었음" $P
```

## 5. 시험 다시 돌리기 (로봇 없음)

```bash
cd $C && PYTHONDONTWRITEBYTECODE=1 $PY tests/test_pilot12.py --root /tmp/r12_p12
cd $C && PYTHONDONTWRITEBYTECODE=1 $PY tests/test_preview_pilot12.py --root /tmp/r12_pp12 --stub-ds /tmp/r12_p12/ds_guard
```

## 수집자 모드 (2026-11-03 추가, `10_collector_mode.md`)

- R2-P 판은 영상 창이 네모 그림 가이드 (수집자 모드) 로 뜬다. F4 = 이전 화면 (디버그).
- 창 키: F5/F6 단계 · F7 자동 · F9 관찰 그림 · F10 '정렬 확인함' (사람 표시, 자동 판정 아님).
- 결과 단계: 1/2/3 결과 (선택). 학습 판정 (g/e/v) 은 11-04 삭제.
