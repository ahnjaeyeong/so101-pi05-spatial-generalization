# 카메라 기록 — 설치·설정·보정 (2026-10-02 ~ 11-02)

표기: [사실] 파일 기록 · [관찰] 연구자 발언·메모 · 원본 없음 = 로컬 어디에도 파일이 없음.
모든 사진은 **카메라 자신이 찍은 화면**(front / wrist 첫 프레임, 캡처)이다. **카메라 거치대·설치 모습을 바깥에서 찍은 사진은 로컬 어디에도 없다 (원본 없음).**

## 1. 장치와 설정
| 항목 | 값 | 근거 |
|---|---|---|
| 카메라 | Innomaker-U20CAM-720P × 2 (front, wrist), 640×480 MJPG 30 fps; front 는 1280×720 MJPG 지원 | [사실] [`camera_settings.md`](camera_settings.md) |
| 노출·WB 결정 (10-02) | 자동: `auto_exposure=3`, `white_balance_automatic=1`, `exposure_dynamic_framerate=0` (`exposure_time_absolute=156`, `white_balance_temperature=4600` 은 기본값) | [사실] [`camera_settings.md`](camera_settings.md), 비교 사진 [`camera_settings/cam_wb_compare.jpg`](camera_settings/cam_wb_compare.jpg) |
| 녹화마다 점검값 | 모든 세션 `notes.md` 의 "녹화 전 점검" 줄: 위 값과 같음 ("auto 기대값과 같음") — 카메라 이동 전·후 동일 | [사실] 예: [`experiments/06_d2_256/sources/sessions/redbox_t1_known/notes.md`](../../experiments/06_d2_256/sources/sessions/redbox_t1_known/notes.md), [`experiments/03_redbox_384_20k/sources/sessions/redbox_t1_known/notes.md`](../../experiments/03_redbox_384_20k/sources/sessions/redbox_t1_known/notes.md) |
| warmup (10-14~) | 녹화 명령에 `warmup_s: 4` (첫 판 노란 화면 해결) — 평가 명령은 기본 1 s | [사실] 녹화 명령 원문 (notes.md) |
| 640×480 과 1280×720 관계 | 640 = 1280 화면의 가로 160–1119 를 1/1.5 축소 | [사실] [`docs/02`](../../docs/02_데이터셋_및_파인튜닝_이력.md), K8 설정 주석 |
| 10-22 이동 | front 카메라를 상자 쪽 위로 이동 (로봇이 화면 위, 상자가 화면 아래), 높이 약 46 cm (±2 cm 어림), 카메라 바로 아래 탁자점 C 좌표 (9.0, 13.7) cm | [사실] [`configs/layouts/redbox8_layouts.yaml`](../layouts/redbox8_layouts.yaml) `camera:` 주석. 이동 이유: 원본 없음 |
| 10-22 노출 경고 | 녹화 사전 점검이 `exposure_dynamic_framerate=1` 을 경고 → v4l2-ctl 로 0 재설정 (재연결·재부팅 때 초기화) | [관찰·기록] Claude 세션 메모 (원 파일 기록은 notes.md 점검 줄) |

## 2. 카메라 이동 전 (옛 front, K1–K4) 화면
| 날짜 | 파일 | 내용 |
|---|---|---|
| 10-02 | [`experiments/01_paper_cube/sources/practice_10/setup_photos/`](../../experiments/01_paper_cube/sources/practice_10/setup_photos/) | practice_10 첫 판 front / wrist (수동 노출 시기) |
| 10-06 | [`experiments/01_paper_cube/sources/practice_50/setup_photos/`](../../experiments/01_paper_cube/sources/practice_50/setup_photos/) | practice_50 첫 판 |
| 10-12 14:50 | [`experiments/02_cubemark_expert_only/sources/desktop_snapshots/cam_front_20261012_145019.png`](../../experiments/02_cubemark_expert_only/sources/desktop_snapshots/cam_front_20261012_145019.png), [`…/cubemark_v1/setup_photos/`](../../experiments/02_cubemark_expert_only/sources/cubemark_v1/setup_photos/) | cubemark 장면 (작은 큐브 첫 등장) |
| 10-13 | [`experiments/03_redbox_384_20k/sources/desktop_snapshots/`](../../experiments/03_redbox_384_20k/sources/desktop_snapshots/) `redbox_K_위치_카메라확인.png`, `redbox_K_위치_녹화화면640.png`, `redbox_카메라_녹화영역비교.png`, `redbox_K_위치_평면도.png`, `redbox_K_템플릿_A3.svg` | K1–K4 표시와 homography 확인, 640/1280 녹화 영역 비교 |
| 10-13 ~ 10-15 | [`experiments/03_redbox_384_20k/sources/pilots/*/setup_photos/`](../../experiments/03_redbox_384_20k/sources/pilots/), [`…/sessions/redbox_*/setup_photos/`](../../experiments/03_redbox_384_20k/sources/sessions/) | redbox 파일럿 3개 + 본 수집 6세션 첫 판 (예: T1-K 10-14 11:05) |
| 10-19 ~ 10-22 | [`experiments/04_rtc_filter_space_eval/sources/eval_ab/20261019_A_vs_B/trials/*/start_front.png`](../../experiments/04_rtc_filter_space_eval/sources/eval_ab/20261019_A_vs_B/trials/), [`…/eval_space_20k/trials/`](../../experiments/04_rtc_filter_space_eval/sources/eval_space_20k/trials/), [`experiments/05_redbox_30k/sources/eval_space_30k/trials/`](../../experiments/05_redbox_30k/sources/eval_space_30k/trials/) | 실물 평가 122판의 시작 front / wrist 화면 (큐브 배치 증거) |

## 3. 카메라 이동 후 (새 front, K1–K8) 화면
| 날짜 | 파일 | 내용 |
|---|---|---|
| 10-22 13:20–13:35 | [`experiments/06_d2_256/sources/main_k8_setting/`](../../experiments/06_d2_256/sources/main_k8_setting/) `redbox_K8_front원본_1280.png`, `redbox_K8_번호_카메라.png`, `redbox_K8_위치_카메라확인.png`, `redbox_K8_위치_평면도.png` | 이동 직후 front 원본 1280 캡처, K1–K8 번호·좌표 확인 |
| 10-22 | [`experiments/06_d2_256/sources/k8_relayout_scratch_20261022/`](../../experiments/06_d2_256/sources/k8_relayout_scratch_20261022/) `front_1280.png`, `front_640.png`, `recheck_1280.png`, `recheck_640.png`, `cubes.png`, `box*.png`, `ruler.png`, `proposed_numbering.png`, `hard/hard_check.png`, `ang/*.png` | 보정 작업 캡처 (K7/K8 재확인, 상자·자, 어려운 구역, 큐브 각도 시험) |
| 10-22 ~ 10-23 | [`experiments/06_d2_256/sources/sessions/redbox_*/setup_photos/`](../../experiments/06_d2_256/sources/sessions/), [`…/pilots/redbox_k8_t3k_pilot/setup_photos/`](../../experiments/06_d2_256/sources/pilots/redbox_k8_t3k_pilot/) | main_k8 4세션 + K8 파일럿 첫 판 (예: T1-K 10-22 15:52) |
| 10-26 | [`experiments/06_d2_256/sources/d2/eval/rollouts/20261026_*/start_frames_extracted/`](../../experiments/06_d2_256/sources/d2/eval/rollouts/) | **영상에서 추출한 프레임** (원본 사진 없음 → AV1 영상의 에피소드 시작 시각 프레임; 영상 경로·시각은 각 폴더 `EXTRACTION.md`) |
| 10-29 | [`experiments/06_d2_256/sources/d2/eval/rollouts/20261029_*/diag/obs_first/`](../../experiments/06_d2_256/sources/d2/eval/rollouts/) | 계측 기록의 원본 관측 PNG (에피소드 첫 chunk, 20판 × front/wrist). 나머지 1,508장은 `ARCHIVE_MANIFEST.csv` 에 경로·해시 |
| 11-02 | [`experiments/11_r1_r2_recovery/sources/sessions/*/setup_photos/`](../../experiments/11_r1_r2_recovery/sources/sessions/) | R1 연습 녹화 첫 판 |

## 4. 보정·좌표계
| 항목 | 내용 | 파일 |
|---|---|---|
| 좌표계 | cm, 원점 C = 상자 앞 벽 바깥면 (로봇 쪽) 모서리; x = 상자 쪽 +, y = 로봇 왼쪽 + | 두 layout yaml 주석 |
| 옛 front H (K1–K4) | `camera.front_640x480.H_cm_to_px` = [[3.761925, −9.990971, 589.362678], [−7.790239, 0.019007, 176.820281], [0.006368, 0.001593, 1.0]]. 사용자 실측 거리 6개 + 1280×720 표시·상자 모서리로 맞춤, 잔차 <0.25 cm | [`../layouts/redbox_layouts.yaml`](../layouts/redbox_layouts.yaml). 계산 스크립트 (`solve_marks.py`, `draw_marks.py`, 10-13 세션 임시 폴더): **원본 없음 (삭제됨)** |
| 새 front H (K1–K8) | [[−3.13422, 12.106333, 175.13384], [9.506667, −0.268513, 383.244486], [−0.009781, −0.001094, 1.0]], K 큐브 8개 중심으로 맞춤 (재투영 약 2 px ≈ 0.2 cm), 상자 근처 (x > −5) 덜 정확 | [`../layouts/redbox8_layouts.yaml`](../layouts/redbox8_layouts.yaml), 계산 파일 [`k8_result.json`, `fit*.py`, `cam_fit.json`, `cam_model_C640.json`, `make_k8.py`](../../experiments/06_d2_256/sources/k8_relayout_scratch_20261022/) |
| 로봇 base 추정 | 옛 (−33.5, 11.6) [K1–K4 pan 피팅], 새 (−31.0, 11.0) → 재적합 (−30.55, 11.18), pan offset −0.75°; **자로 잰 값 없음** | redbox8 yaml `robot:`, `experiments/09_sampling_ablation/sources/data_coverage_audit/tables/a00_base_fit.json` |
| 좌표 역산 검증 | 학습 K 128편: 2D RMS 0.65 cm, p90 0.98 cm | `experiments/10_pan_diagnostic/sources/pan_inference_diagnostic/09_coordinate_inversion.md` |
| 팔 캘리브레이션 | 10-02 백업 (팔로워·리더 json) | [`../robot/calibration_backup_20261002/`](../robot/calibration_backup_20261002/) |
| 관절 범위 기록 | teleop_view 범위 6회 (10-13, 10-22) | [`../robot/range_check/`](../robot/range_check/) |
| Held-out H 좌표 | U1–U8 (confirmed: false) | [`../layouts/redbox8_heldout_h.yaml`](../layouts/redbox8_heldout_h.yaml) |

## 5. 원본 없음
- 카메라 거치대·설치 모습을 바깥에서 찍은 사진 (이동 전·후 모두).
- 10-22 카메라를 옮긴 이유, 카메라 자세 (높이·기울기) 실측값 — 높이는 카메라 모델 어림 46 ± 2 cm 뿐.
- 10-13 K1–K4 보정 계산 스크립트·중간 결과 (세션 임시 폴더가 지워짐; 결과 H 행렬만 yaml 에 남음).
- 로봇 base 의 실측 좌표.
