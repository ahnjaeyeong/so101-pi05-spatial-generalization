# R1/R2 추가 시연 — 인계 (2026-10-30)

## 1. 상태

- 설계·구현·로봇 없는 검증 완료. **실물 로봇 연결·녹화는 하지 않았다** (사용자가 `record` 를 직접 실행).
- 계획 생성됨: `main_k8/r1_realign_pilot` 16편, `main_k8/r2_pregrasp_pilot` 32편 (dataset 없음).
- d2 dataset·체크포인트·d2 구성 세션·`~/so101_boxpick/scripts`·`config` 는 수정하지 않았다 (이 작업 중 수정 시각 확인).

## 2. 파일

| 경로 | 내용 |
|---|---|
| `01_existing_collection_pipeline.md` | 기존 d2 수집 경로·action 의미·단위·파일 위치 |
| `02_r1_r2_dataset_plan.md` | 시나리오·수량·메타데이터 |
| `03_collection_ui_design.md` | 구조·단계·안전 검사·키·화면 |
| `04_collection_ui_usage.md` | 명령 |
| `05_preview_test_results.md` | 검증 결과·스크린샷 |
| `06_dataset_qa_plan.md` | 품질 검사·현황 관리 |
| `config/r12_scenarios.yaml` | 시나리오·수량·안전 범위 |
| `tools/` | r12_collect.py (CLI·터미널 UI), r12_record_entry.py, r12_viewer.py, r12_common.py, r12_qa.py, r12_fake_record.py |
| `tests/` | test_units · test_errors · test_preview_flow · test_entry_stub · shot_session · pty_driver, `results/` |
| `screenshots/` | 바탕화면 스크린샷 사본 4장 |
| `~/Desktop/SO101_R1_R2_Collection_UI{,_R1,_R2,_Recording}.png` | 실제 실행 화면 |

## 3. 학습 데이터 섞을 때 지켜야 할 호환 조건

| 조건 | 값 (d2) | R1/R2 에서 보장하는 방법 |
|---|---|---|
| 형식 | LeRobot v3.0, fps 30, robot_type so_follower | 같은 lerobot 0.6.2 `record()`; QA 가 비교 |
| features | action·observation.state 6개 float32 (같은 이름·순서), images.front/wrist 480×640×3 video av1 yuv420p g2 crf30 | 같은 코드·같은 카메라 설정; 가짜 로봇 시험에서 같음 확인 |
| 단위 | 관절 5개 ° (use_degrees, 캘리브레이션 mid 기준), 그리퍼 0–100 | 같은 캘리브레이션 파일 `my_arm.json`·`my_leader.json`. **캘리브레이션을 다시 하면 d2 와 단위 기준이 달라진다** |
| action 의미 | 리더 위치 그대로 (필터·클리핑 없음, max_relative_target=None) | 진입점이 처리기·send 를 바꾸지 않음; lerobot 옵션을 도구가 고정 |
| 카메라 | /dev/cam_front·/dev/cam_wrist 640×480@30 MJPG, warmup 4 s, 자동 노출·화이트밸런스 (record_ui precheck) | 같은 옵션·같은 점검. front 카메라 위치는 main_k8 (2026-10-22) 그대로여야 함 |
| 과제 문장 | `pick up the red cube and put it in the brown box` (task_index 0 하나) | 설정에서 고정 |
| 판 끝 | 쉬는 자세 (lift ≈ −103, elbow ≈ 96, 그리퍼 닫힘) | 시연 안내 + QA 끝 자세 검사 |
| 판 시작 | d2: 쉬는 자세 / **R1/R2: 중간 자세** | 다름 — R1/R2 만으로 학습하지 않고 d2 와 섞는 실험 전제 |
| 제외 판 | d2 는 release 복사본에서 삭제 | R1/R2 는 `r12_plan.csv` excluded 목록 → 같은 release 방식 (`lerobot-edit-dataset delete_episodes --new_root`) |

병합할 때 d2 의 episode 순서 뒤에 붙이면 R1/R2 판의 `episode_index` 가 바뀐다 → `r12_episodes.csv` 는 원래 세션의 번호 기준이므로 병합 표(원래 세션·번호 → 새 번호)를 따로 남겨야 한다. 섞는 비율·학습 단계 수는 정하지 않았다.

## 4. 실제 수집 전에 사용자가 확인할 것

1. **Preview 를 직접 한 번**: `~/so101-env/bin/python ~/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py preview --type R2` — 키 흐름(→ ← 1 2 3 m Esc)과 창 배치.
2. **시나리오 수량·문구** (`r12_sheet.md`, `config/r12_scenarios.yaml`): 고치면 `plan --group … --force` (녹화 전만).
3. **안전 범위** (`safety`): |pan| ≤ 95°, 모두 WARN (11-02 완화: → 를 막는 것은 관절값 없음/NaN 뿐, 실제 시작 자세는 r12_episodes.csv 에 기록). 탁자·상자 충돌은 관절값으로 판정하지 않으므로 시작 자세를 눈으로 확인.
4. **Pan 목표**: 판마다 계획에 정해짐 (K 기준 = d2 에서 큐브를 쥔 순간 pan 중앙값 + 처음 어긋남). 가장 큰 목표 R1 ep12 K7 −90.7° (캘리브레이션 한계까지 19.5°, WARN 표시). 목표와 다르게 시작해도 녹화는 되고 실제 값이 기록된다.
5. **저장 중 리더 고정**: → 뒤 파란 배너 동안 리더를 움직이지 않는다 (그 자세에서 녹화 시작).
6. 손목 영상의 좌/우가 로봇 좌/우와 어떻게 대응하는지 첫 몇 판에서 확인 (QA 손목 dx 표).
7. 첫 실행은 `--num 4` 정도로 짧게 → `qa` 로 실물 Hz·늦은 틱·첫 화면 검출 확인.
8. ROS(twin_ws) 를 썼으면 팔로워 전원 재투입 (precheck 가 컨테이너를 경고).

## 5. 열린 항목

- R1C (빈 파지 뒤 재접근): 시작 그리퍼가 닫혀 있어 지금 안전 검사(그리퍼 열림)와 맞지 않음 — 시나리오별 그리퍼 조건 필요.
- 실물에서 탭(프레임 복사·상태 쓰기)이 30 Hz 루프에 주는 영향은 미측정 (Preview 는 30.0–30.03 Hz, 늦은 틱 0).
- 큐브 '물리적 접근 깊이' 는 측정하지 않음 (`unknown`). 손목 영상 큐브 넓이(px)는 기록되지만 거리로 보정되지 않았다.
- 메모리 규칙: Preview·시험은 모두 임시 폴더 (`/tmp/r12_preview_*`, 세션 스크래치). 실제 세션에 시험 기록 없음.

## 2026-11-02 정의 수정

- R1 = Pan 방향 재정렬 16 (R1-PAN-L 4 · R1-PAN-R 4 · R1-OVER 4 · R1-DRIFT 4), R2 = 국소 정렬·깊이·닫힘 32 (R2-DEPTH 8 · R2-AHEAD 8 · R2-LEFT 4 · R2-RIGHT 4 · R2-READY 8). 정의·저장 구조: 02 §12.
- 판별 메타데이터: `r12_episodes.csv` 의 recovery_type · scenario_id · error_kind · r1_pan_error_dir/deg · r2_local_error_dir/cm · r2_wrist_start_in_region · realign_mark_frames/pan.
- R1 은 쉬는 자세에서 시작해 녹화 안에 오차 구간이 있다. Space 프레임 (`realign_mark_frames`) 앞 구간을 학습에 쓸지는 정하지 않았다.

## 2026-11-02 작업 지시서 (3차) — R1 재정의

- R1 16 = 시작 자세 (home_near / mid_approach) × 손목 가시성 목표 (visible_or_edge / absent) 각 4, 셀 안 좌우 2/2: R1-HOME-VIS (±15·20°) · R1-HOME-OUT (±25·30°) · R1-MID-VIS (±15°) · R1-MID-OUT (±20·25°). 잘못된 시작 자세는 준비 단계(녹화 안 함), 녹화는 고쳐 돌아오는 동작만. 02 §13.
- 11-02 오후 R1 (녹화 중 오차 + Space) 은 수량 0. 그 정의로 사용자가 13:20 에 `practice/r1_try` 4편을 녹화함 (Space 0, 결과 미입력, review_videos·qa 없음 — 그대로 둠).
- R2 32 는 그대로 (값 이름만 지시서 §5 에 맞춤: local_alignment_type, approach_depth_category, first_close_result, cube_relative_position_in_wrist).
- 판 메타데이터 열 이름: 02 §13 표. 측정 Pan 오차는 K 기준 pan (d2 중앙값, 판마다 ±9°) 대비라 신뢰도 low/medium 으로만 적음. FK 위치는 쓰지 않음.
- 안전: Pan |pan| > 95° · 한계 10° 안 = BLOCK. R1 은 시도마다 사람의 시작 자세 확인 (→ 두 번) 을 기록.

## 2026-11-02 작업 지시서 (4차) — R1 A/B

- R1 16 = R1-A 초기 방향 4 · R1-B1 접근 중 반전 4 · R1-B2 지나침 4 · R1-B3 손목 놓침 4 (02 §14). 3차 HOME/MID 셀은 수량 0.
- 큐브 자리: K 8 + 자유 점 F1–F4 8 (+ 준비 단계 x = front 검출 자리). Pan 기준·자리 출처·신뢰도를 판마다 기록.
- 복구 측정 열 (02 §14 표). 녹화 프로세스 pan 열·축소 손목 영상으로 대략, QA 가 dataset 으로 다시 잼.
- 흐름 변경: 결과 단계 → = 저장 뒤 준비 단계 (녹화는 준비 단계 → 바로 뒤). r1_try2 ep1 (저장 중 리더 34° 이동 → 첫 프레임 팔로워 28° 튐) 이 근거.
- 안전 조건 (BLOCK): 관절값 없음·NaN · |pan| > 95° · Pan 한계 10° 안 · 리더−팔로워 > 25°. 시나리오 조건은 막지 않음.
- 사용자 기록 r1_try2 (13:52, 2편) 는 3차 정의로 남겨 둠. 14:08 에 그 세션의 후처리·QA 가 실행됐다 (review_videos, qa/).
