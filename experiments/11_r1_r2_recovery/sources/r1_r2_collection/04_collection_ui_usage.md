# 04. 수집 UI 사용법

모든 명령은 `~/so101-env/bin/python` 으로. 아래 `T=~/so101_runs/main_k8/r1_r2_collection/tools`.

```bash
T=~/so101_runs/main_k8/r1_r2_collection/tools
```

## 0. 로봇 없이 먼저 보기 (Preview)

```bash
~/so101-env/bin/python $T/r12_collect.py preview --type R2            # R1 은 --type R1
~/so101-env/bin/python $T/r12_collect.py preview --type R1 --source dummy   # 만든 그림 + 고정 관절값
```
- 로봇·리더·카메라·lerobot 을 불러오지 않고 dataset 도 쓰지 않는다. 기록은 `/tmp/r12_preview_<시각>/` 에만.
- 영상·관절값 = 기존 녹화 `main_k8/redbox_t1_known` episode 5 의 review 영상과 state/action 재생 (읽기만). 큐브 위치는 계획과 무관. 창 위에 PREVIEW 표시.
- 키는 실제와 같다. 영상이 쉬는 자세일 때 → 를 누르면 시작 자세 검사로 막히고, 팔이 그리퍼를 연 채 내려간 구간에서 → 가 통과한다.
- 옵션: `--episodes N` (기본 3), `--no-viewer`, `--scale 0.85`, `--viewer-geometry +20+60`.

## 1. 준비 (한 번)

```bash
~/so101-env/bin/python $T/r12_collect.py check        # 파일·장치 경로·캘리브레이션 한계·lerobot 함수 모양 확인 (장치 안 엶)
cat ~/so101_runs/main_k8/r1_realign_pilot/r12_sheet.md # R1 계획표 (16편)
cat ~/so101_runs/main_k8/r2_pregrasp_pilot/r12_sheet.md # R2 계획표 (32편)
```
수량·문구를 바꿨으면 녹화 전에: `~/so101-env/bin/python $T/r12_collect.py plan --group r2_pilot --force`

## 2. 녹화 (사용자가 직접 — 토크가 켜지고 팔이 움직임)

```bash
~/so101-env/bin/python $T/r12_collect.py record --session main_k8/r2_pregrasp_pilot --num 8
~/so101-env/bin/python $T/r12_collect.py record --session main_k8/r1_realign_pilot  --num 8
```
- `--num` 을 빼면 계획의 남은 판을 모두. 이어 찍기는 같은 명령 (dataset 이 있으면 자동으로 `--resume=true`).
- lerobot 옵션(포트·id·카메라·과제 문장·`episode_time_s 45`)은 도구가 d2 와 같게 넣는다. 실제 명령은 실행마다 세션 `notes.md` 에 적힌다.
- 실행하면: 녹화 전 점검(twin_ws 컨테이너, 카메라 v4l2 값 — 읽기만) → 체크리스트 Enter → 영상 창이 뜨고 터미널에서 lerobot 이 리더·팔로워·카메라를 연결.
- 다른 옵션: `--camera-mode manual`, `--no-viewer`, `--scale 0.85`, `--viewer-geometry +20+60`.

### 한 판 순서

1. 영상 창 맨 위 큰 글씨로 이번 판 시나리오 확인 (예: R2 · PAN 정렬 불량 (왼쪽)). 왼쪽 아래 지도·front 영상에서 **초록 ■ = 큐브 놓을 곳, 주황 ✕ = 그리퍼 시작 위치(오답), 파랑 ○ = 경유(정렬) 지점, 하늘색 화살표 = 지금 Pan**.
1-1. **노란 배너 (준비, 녹화 안 함)**: 배너·창의 시나리오대로 큐브를 K 자리·각도에 놓고, 리더로 **먼저 Pan 을 배너의 'Pan 목표' 로** 옮긴 뒤 (창의 'Pan 지금 → 목표' 가 초록 ✓) 나머지 시작 자세(그리퍼 열림, 높이·손목)를 만든다. 창 왼쪽 아래 '시작 자세 검사' 가 ✓ 인지 본다.
2. 리더를 멈춘 채 **→**. ✗ 가 있으면 막히고 이유가 빨간 글씨로 나온다 → 고쳐서 다시 →.
3. **흰 배너 (녹화 중)**: 시연 (재정렬/접근 → 파지 → 상자 → 쉬는 자세). 고칠 때는 1–2초에 걸쳐 손목 화면을 보며 (크게 → 작게), **손목 영상의 점선 '닫기 영역'에 큐브가 들어와 '✓ 닫기 OK' 가 뜨면 닫기**. 끝나면 **→**. 잘못했으면 **←**.
4. **회색 배너 (결과 + 다음 준비, 녹화 안 함)**: 방금 판 결과 **1** 첫 파지 성공 / **2** 재시도 후 성공(누를 때마다 +1) / **3** 실패, 필요하면 **m** 메모 → Enter. 실패·잘못 찍은 판은 **←** (버리기 예약).
5. 다음 판 시나리오대로 큐브·시작 자세를 만들고 **→** → 파란 배너 '저장 중' 동안 **리더 팔을 움직이지 않는다** (저장이 끝나면 그 자세에서 바로 녹화 시작).
6. 마지막 판 뒤 / Esc 로 끝낸 뒤 결과를 안 넣은 판은 터미널이 묻는다 (Enter = 나중에).

종료: 준비 단계 Esc = 녹화 없이 끝, 녹화·결과 단계 Esc = 방금 판 저장 후 끝. 비상 정지 Ctrl+C.

## 3. 실행 뒤

```bash
~/so101-env/bin/python $T/r12_collect.py status --session main_k8/r2_pregrasp_pilot   # 시나리오별 저장/목표, 다음 판, 결과 입력 수
~/so101-env/bin/python $T/r12_collect.py qa     --session main_k8/r2_pregrasp_pilot   # → <세션>/qa/r12_qa_report.md (dataset 읽기만)
~/so101-env/bin/python $T/r12_collect.py label  --session main_k8/r2_pregrasp_pilot --episode 7 --result 2 --retry 1 --notes "..."
~/so101-env/bin/python $T/r12_collect.py exclude --session main_k8/r2_pregrasp_pilot --episodes 7 --reason "큐브 밀림"
```
- 자동 후처리 (record_ui 와 같음): `review_videos/episode_NNN.mp4`, `setup_photos/`, `notes.md` 결과 표, `main_k8/README.md` 세션 줄. 그리고 `r12_episodes.csv`, `r12_plan.csv` 상태 갱신.
- `exclude` 는 dataset 을 바꾸지 않는다. 계획에 같은 시나리오 재촬영 줄이 붙고, 학습 때 제외 목록으로 뺀다 (d2 의 release 복사본 방식).

## 4. 문제가 생기면

| 증상 | 할 일 |
|---|---|
| `장치가 없어요` | USB·전원, `ls -l /dev/so101_* /dev/cam_*` |
| 첫 판 저장 전에 멈춰 빈 dataset | 안내된 `mv ... _empty_<시각>` 뒤 다시 |
| 비정상 종료 | 화면에 나온 1)–3) (dataset 확인 → `record_ui.py --postprocess <세션>` → 같은 명령으로 이어 찍기) |
| 키가 안 먹음 | 터미널 창이나 영상 창을 클릭해 선택 (11-02 부터 영상 창 키도 같은 검사를 거쳐 넘어감) |
| 영상 창이 없음 | `DISPLAY` 없이 실행됨 → 터미널 배너만으로도 녹화 가능. 창 로그 `/dev/shm/r12_live_<run_id>/viewer.log` |
| 원본 로그 | `~/.local/state/record_ui/record_<run_id>.log` ([r12] 사건 줄 포함) |

## 5. 2026-11-02 (3차 지시서) R1 수집 방법

```bash
T=~/so101_runs/main_k8/r1_r2_collection/tools
~/so101-env/bin/python $T/r12_collect.py menu                                           # R1/R2 시나리오·진행률
~/so101-env/bin/python $T/r12_collect.py preview --type R1                               # 로봇 없이 같은 화면
bash ~/so101_runs/main_k8/r1_r2_collection/trial_practice.sh r1                          # 시험 4편 (practice/r1_try2)
~/so101-env/bin/python $T/r12_collect.py record --session main_k8/r1_realign_pilot      # 본 파일럿 16편
```

판마다:
1. (선택, 첫 판) 그리퍼를 큐브 바로 위에 두고 `c` = 로봇 선 보정.
2. 준비 (녹화 안 함): 큐브를 K·각도대로 놓기 → 그리퍼 열기 → 팔을 접은 채 Pan 을 주황 선으로 → 접근 중간 판만 팔을 일부 펴기 (그리퍼 탁자 위 8 cm 이상).
3. 영상 창 왼쪽 패널: 시작 자세·손목 큐브(보임/안 보임)·front 큐브가 ✓ 인지 봄 (⚠ 여도 녹화는 됨, 기록됨).
4. → 한 번 = 안전 확인 문구 → 맞으면 10 초 안에 → 한 번 더 = 녹화 시작. (아니면 자세를 고치거나 오차를 줄임)
5. 녹화: Pan 을 초록 선(큐브)으로 되돌려 큐브를 찾고 → 접근·파지 → 상자 → 쉬는 자세 → →.
6. 결과: 1 · 2 · 3 (재정렬 못 함) · 4 (재정렬 O·파지 실패) · m 메모 · p 방금 판 다시 보기 · ← 버리기.

R2 는 §2 그대로 (준비 단계에서 손목 화면 주황 시작 영역).

## 6. 2026-11-02 (4차) R1-A/B 수집

```bash
bash ~/so101_runs/main_k8/r1_r2_collection/trial_practice.sh r1                          # 시험 4편 (practice/r1_try3: A·B1·B2·B3)
~/so101-env/bin/python ~/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session main_k8/r1_realign_pilot
```
1. 준비 (녹화 안 함): 큐브를 놓는다 (F 자리는 표시가 없으니 지도·front 화면 점을 보고 대략). 그리퍼를 연다.
2. 시나리오의 오차 상태를 만든다 — A: 팔 거의 접은 채 Pan 을 주황 쪽 · B1: 팔을 펴며 주황 쪽(멀어짐)으로 움직여 멈춤 · B2: 반대쪽에서 와서 초록 선을 지나 멈춤 · B3: 편 팔로 주황 쪽, 손목 화면에 큐브 없게 (front 는 보임). 편 팔에서는 그리퍼를 탁자에서 띄우고 상자·탁자에 닿지 않게.
3. 영상 창 왼쪽: ✗ 안전 조건이 있으면 → 가 막힘 (이유가 적힘). ◇ 시나리오 조건은 달라도 녹화됨 — 원하면 s/d/k/x 로 바꿔 기록.
4. → 한 번 = 안전 확인 문구 → 10 초 안에 → = 녹화.
5. 녹화: 되돌리는 동작부터 → 접근·파지 → 상자 → 쉬는 자세 → →.
6. 결과 1/2/3/4 · m 메모 · p 다시 보기 → → = 저장 → 준비 단계 (저장 중에는 리더 그대로).
