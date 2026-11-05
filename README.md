# SO-101 π₀.₅ Spatial Generalization

SO-101 LeRobot π₀.₅ fine-tuning, spatial generalization experiments, offline diagnostics and real-world evaluation.

이 저장소는 연구 **기록** 저장소다. 학습·평가 코드는 원래 위치 (`~/so101_boxpick`, 각 실험 폴더의 스크립트) 에서 돌았고, 여기에는 문서·설정·작은 결과 파일·분석 스크립트 사본과 원본 경로·SHA-256 을 모았다. 체크포인트·데이터셋·영상은 넣지 않았다 ([제외 규칙](#git-에서-제외한-자료)).

## 1. 연구 목표

> **학습하지 않은 새로운 큐브 위치에서도 로봇이 첫 접근부터 정확한 위치로 이동하여 파지하도록 공간 일반화 능력을 개선한다.**

## 2. 구성
| 항목 | 내용 |
|---|---|
| 로봇 | SO-101 follower + leader (6관절: shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll, gripper), P16/I0/D32 |
| 카메라 | front (탁자 전체) + wrist (집게), 640×480 30 fps |
| 정책 | π₀.₅ (`lerobot/pi05_base`, PaliGemma = SigLIP + Gemma, action expert 693M / 전체 4.14B), LeRobot 0.6.2 |
| 계산 | NVIDIA Jetson Thor |
| 과제 | 빨간 2.5 cm 큐브를 갈색 상자에 넣기 (T1 1개 · T2 여러 개 · T3 방해 큐브) |
| 표준 추론 | RTC (horizon 20, EXP, guidance 10, queue 30), denoise 5, max_relative_target 8°, 팔 필터 선택 |

## 3. 연구 진행 과정
| 단계 | 기간 | 내용 | 실험 |
|---|---|---|---|
| 1 | 10-02 ~ 10-13 | 종이 큐브 10편·50편, full fine-tune; cubemark 과제와 첫 expert-only | [EXP-01](experiments/01_paper_cube/README.md), [EXP-02](experiments/02_cubemark_expert_only/README.md) |
| 2 | 10-13 ~ 10-20 | 2.5 cm 큐브, K1–K4, 384편 (Known 192 + Random 192), expert-only 20k; RTC·필터·공간 평가 | [EXP-03](experiments/03_redbox_384_20k/README.md), [EXP-04](experiments/04_rtc_filter_space_eval/README.md) |
| 3 | 10-20 ~ 10-22 | 같은 데이터로 20k → 30k 추가 학습 | [EXP-05](experiments/05_redbox_30k/README.md) |
| 4 | 10-22 ~ 10-27 | 카메라 이동·K1–K8, 256편 (T2 미녹화) d2 를 pi05_base 에서 새로 학습 | [EXP-06](experiments/06_d2_256/README.md) |
| 5 | 10-26 ~ 10-27 | Vision/VLM Feature Probe | [EXP-07](experiments/07_vision_probe/README.md) |
| 6 | 10-27 ~ 11-02 | Action Expert·Wrist Roll, 가중 재표집, Shoulder Pan 진단·실물 파일럿 | [EXP-08](experiments/08_action_bottleneck/README.md), [EXP-09](experiments/09_sampling_ablation/README.md), [EXP-10](experiments/10_pan_diagnostic/README.md) |
| 7 | 10-30 ~ | R1/R2 수동 복구 시연 수집 준비, HIL 검토 | [EXP-11](experiments/11_r1_r2_recovery/README.md), [EXP-12](experiments/12_hil/README.md) |
전체 타임라인: [docs/01](docs/01_연구_전체_타임라인.md) · 실험 목록: [EXPERIMENT_INDEX.md](EXPERIMENT_INDEX.md)

## 4. 데이터셋 및 학습 이력
| 데이터셋 | 편 | 학습 | 비고 |
|---|---|---|---|
| practice_10 / practice_50 | 10 / 50 | full FT bs4 2k / 15k | 종이 큐브 |
| cubemark_v1 | 50 | full FT 15k, expert-only bs8 3k | X 표시 과제 |
| redbox_all (옛 카메라, K1–K4) | 384 | expert-only bs32 20k → resume 30k | |
| d2 (새 카메라, K1–K8, T1+T3) | 256 | expert-only bs32 20k (pi05_base 에서) | redbox_all 과 **별개** |
| d4 (d2 − T3-K) | 192 | 10k 에서 정지 | 평가 없음 |
| d2 가중 재표집 A0/A1/A2 | 256 | d2 020000 에서 새 FT 4k | A2 미평가 |
상세: [docs/02](docs/02_데이터셋_및_파인튜닝_이력.md), [configs/training/RUNS.csv](configs/training/RUNS.csv), [configs/datasets/DATASETS.csv](configs/datasets/DATASETS.csv), loss 곡선 [analysis/figures/loss_curves.png](analysis/figures/loss_curves.png).

## 5. 주요 실험 결과 (요약 — 수치·조건은 실험 문서)
- 고정 위치 (K) 에서는 어느 정도 성공, K 에서 2 cm 만 벗어나도 최종 성공이 82% → 50% (redbox 20k). → [EXP-04](experiments/04_rtc_filter_space_eval/README.md)
- 팔 필터는 성공률을 바꾸지 않았다 (A/B 40판, p=1.0). 큰 진동은 RTC 없는 sync 모드에서 나왔다.
- 실패와 관련된 것은 시작 큐브 각도가 아니라 **정책이 손목을 돌린 크기**와 **손목 기준 큐브–집게 정렬**이었다.
- 20k → 30k 추가 학습: loss 변화 없음, 첫 파지 22/40 → 12/40 (시작 자세가 달라 통제되지 않은 비교). → [EXP-05](experiments/05_redbox_30k/README.md)
- d2 (새 카메라): 10-29 실물 20판 P 9. 실패는 대부분 파지 직전 '덜 다가감' 빈 닫힘. → [EXP-10](experiments/10_pan_diagnostic/README.md)
- d2 + 교정 시연 16편 FT (rft01) 실물 파일럿 16판: FT 4/8 · BL 5/8 (사람). Known K3 에서 FT 2/2 · BL 0/2 (조건당 1회), Unknown 은 시작 그리퍼 교란으로 비교 무효. → [EXP-14](experiments/14_rft01_real_pilot/README.md)
- 모든 실물 결과: [evaluations/real_robot/](evaluations/real_robot/README.md)

## 6. 현재 확인된 문제
1. 새 위치에서 첫 접근 pan 이 가까운 학습 위치 (K) 쪽으로 끌린다 (합성 격자 a≈0.3; 학습 Random 위치에서도 0.21).
2. 왼쪽 목표에서 첫 chunk 의 pan 이 거의 움직이지 않는다 (실물 첫 1 s 이동 need 의 0.035 vs 오른쪽 0.69).
3. 파지 직전 손목 영상의 좌우 정보를 행동에 거의 쓰지 않는다 (G_tt 0.10), roll 에 따라 좌표를 돌리지 않는다 (w_rot ≈ 0).
4. 손목 시야에서 큐브를 놓친 뒤에는 front 에 큐브가 보여도 같은 방향으로 계속 돈다 (−109° 이탈 2/20).
5. 이런 상태 (큰 지나침, 손목 놓침, 덜 다가감에서 고치기) 가 사람 시연에 없다.

## 7. Vision 과 Action Expert 분석
- Vision 인코더·Gemma 는 학습 중 고정 (d2 가중치가 pi05_base 와 bit 동일).
- 고정 특징의 wrist 토큰에서 큐브 상대 위치가 정확히 읽힌다 (SigLIP L26 MAE 0.079 cm, 학습 데이터 held-out fold). front 특징의 탁자 절대 위치는 약하다 (6–10 cm).
- 정책 행동은 그 정보를 거의 쓰지 않는다 → 사전 규칙상 병목은 Action Expert. **단 "Vision 에 문제가 없다" 고 단정하지 않는다** (실물 상태에서는 표현이 무너지고, VLM 학습 비교가 없음).
→ [EXP-07](experiments/07_vision_probe/README.md), [EXP-08](experiments/08_action_bottleneck/README.md), [docs/04](docs/04_실패원인_분석.md)

## 8. Shoulder Pan 및 공간 일반화 분석
- 출발 방향은 front 영상이 정한다; 같은 관측에서 noise 에 따라 '기다림 / 감' 두 갈래.
- 첫 chunk 정지·방향 지속은 모델 Raw Action (서보·필터 아님); RTC 는 경계 점프를 억제하지만 방향 지속의 주원인은 아님.
- 가중 재표집 (A1) 은 오프라인 지표에서 개선 없음.
→ [EXP-09](experiments/09_sampling_ablation/README.md), [EXP-10](experiments/10_pan_diagnostic/README.md)

## 9. 현재 상태 (2026-11-05 갱신; 이전 기준 11-02)
| 구분 | 항목 |
|---|---|
| ✅ 완료 | EXP-01 ~ EXP-08, EXP-10 (필터 A/B 는 일부만), A0/A1 학습·오프라인 평가, A2 학습 |
| ⏸ 일시정지 | Sampling ablation 큐 (A2 평가, A2r, A0′ 미실행; 재개는 사용자 지시) |
| ⏹ 정지 | d4 (10k) |
| ✅ 수집 (부분) | EXP-11 R1/R2 pilot12: 학습 유효 16편 (R1 4 · RC 12), QA 완료 (11-03 ~ 11-04). 원래 계획 R1 16 · R2 32 본 수집은 안 함 |
| ✅ 학습 · 오프라인 | EXP-13 (11-04): d2 + R1 4 · RC 12 FT 1k — 재추론에서 R1 복구 방향 신호만 개선, R2 실물 AHEAD 상태 변화 없음 |
| ✅ 실물 파일럿 | EXP-14 (11-05): FT 4/8 · BL 5/8 [사람]. Unknown 구간 시작 그리퍼 · 모델 순서 교란 → **모델 우열 미결정** |
| 🔄 진행 중 | EXP-12 HIL: 수집 도구 구현 · 가짜 장치 검증만 (179/179, UI 205/205). 실물 안전 검증 · 수집 0 |
| 📝 계획 | 그리퍼 시작 상태를 고정한 FT/BL 교대 반복 평가, d2 + R2 단독 FT 검토, Held-out H 32편, HIL 실물 사전 확인 (모두 사용자 승인 뒤) |
| 인계 | [HANDOFF.md](HANDOFF.md) — 11-05 기준 다음 세션 인계 문서 |

## 10. 향후 실험 계획
(11-05 갱신 — 1·2 는 EXP-11/13/14 에서 일부 실행됨)
1. ~~R1 을 실패 상태에 맞춰 수집, R2 수집~~ → pilot12 로 R1 4 · RC 12 수집 (EXP-11).
2. ~~d2 + R1/R2 재학습 → 오프라인 T4 지표 → 실물 평가~~ → EXP-13 · EXP-14. 다음: 실행 도구의 그리퍼 시작 상태 고정 후 FT/BL 교대 반복 평가, d2 + R2 단독 FT 검토.
3. Held-out H 녹화로 진짜 held-out 평가 마련.
4. HIL (정책 실행 중 교정): 전환 장치 구현 · 가짜 장치 검증 완료 (EXP-12, 11-04). 남은 것: 사용자 실물 사전 확인 (리더 토크 전환 · 정렬 · hold 뒤 재연결) 과 별도 승인.
→ [docs/06](docs/06_HIL_및_향후실험.md), [EXP-12](experiments/12_hil/README.md)

## 11. 문서 지도
| 위치 | 내용 |
|---|---|
| [docs/](docs/README.md) | 11-02 전수 조사 문서 01–10 (타임라인, 데이터·학습, 공간 평가, 원인, 오프라인, HIL, 비교표, 근거, ChatGPT 종합, 미확인) + 영역별 조사 노트 |
| [experiments/](EXPERIMENT_INDEX.md) | 실험별 README + `sources/` (원본 기록 사본) |
| [evaluations/](evaluations/README.md) | 실물 / 오프라인 / 비교 표와 지표 정의 |
| [configs/](configs/README.md) | 학습 설정, 체크포인트 해시, 데이터셋 메타, 배치 yaml, 카메라 설정 |
| [analysis/](analysis/README.md) | loss 표·그림 |
| [templates/](templates/) | 새 실험·평가 문서 템플릿 |
| [tools/](tools/) | 동기화·메타 수집·저장소 검사 스크립트 |
| [CLAUDE.md](CLAUDE.md) | 이 저장소를 갱신할 때의 규칙 |
| [HANDOFF.md](HANDOFF.md) | 11-05 연구 인계 (R1/R2 → rft01 → 실물 16판 → HIL 준비, 다음 단계) |
| [inventory/](inventory/README.md) | 로컬 원본 ↔ GitHub 파일 단위 비교 (10,873개 분류), 항목별 누락표, 원본 없는 항목 |
| [configs/camera/](configs/camera/README.md) | 카메라 설정·이동 전후 화면·보정 (H 행렬, 좌표계) 기록 |
| [ARCHIVE_MANIFEST.csv](ARCHIVE_MANIFEST.csv) | Git 에 넣지 않은 원본 (대용량 로그·관측 PNG·npz·데이터셋 등) 의 경로·크기·SHA-256 |
| [DERIVED_MANIFEST.csv](DERIVED_MANIFEST.csv) | 축약·변환·추출 파일 (로그 축약, 명령 vs 실제값 CSV, 서보 타임라인 10 Hz, 영상 프레임) 과 원본 해시 |
| [SOURCES_MANIFEST.csv](SOURCES_MANIFEST.csv) | 복사한 모든 파일의 원본 경로·크기·SHA-256 (해시는 **원본 파일** 기준; CSV 줄바꿈은 Git 에서 LF 로 정규화되어 사본 해시가 다를 수 있음) |

## 표기 규칙
[사실] 파일 측정값 · [관찰] 연구자 실물 관찰 · [가설] 분석 해석 · [계획] 설계만 (docs/ 에서는 A/B/C/D). 오프라인 probe 결과는 실물 성공률이 아니다. 진짜 held-out 사람 시연은 아직 없다.

## Git 에서 제외한 자료
전체 목록과 해시는 [ARCHIVE_MANIFEST.csv](ARCHIVE_MANIFEST.csv), 요약은 [inventory/README.md](inventory/README.md).
모델 체크포인트 (32개, 각 9.35 GB `model.safetensors` + optimizer — 경로·SHA-256 은 `configs/checkpoints/`), LeRobot 데이터셋 parquet·AV1 영상 (메타는 `configs/datasets/`), 실물 rollout dataset·영상·review 영상, diag 원 chunk (`.npz`) 와 관측 PNG (에피소드 첫 chunk 52장만 등록), 2 MB 넘는 rollout 로그 (축약본 `*.condensed.log` 등록), QA 판별 시트 `ep_N.jpg` 773장, F1 특징 (86 GB), 학습 로그 원본 (진행 막대; loss 는 `analysis/loss/` 로 추출), `.npz/.npy/.parquet/.gz/.mp4/.safetensors`, 가상환경·캐시.

## 새 실험 추가
[CLAUDE.md](CLAUDE.md) 의 "새 실험 기록 절차" 참고. 요약: 템플릿 복사 → ID 부여 → 목적·가설 → 설정 기록 (`tools/sync_sources.py`, `tools/collect_run_metadata.py` 매핑 추가) → 결과 연결 → `EXPERIMENT_INDEX.md`·`CHANGELOG.md` 갱신 → `python3 tools/check_repo.py` → commit → push.
