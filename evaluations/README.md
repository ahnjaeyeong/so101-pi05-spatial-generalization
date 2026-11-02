# 평가 결과 관리

| 폴더 | 내용 |
|---|---|
| [`real_robot/`](real_robot/README.md) | 실물 로봇 평가 전체 표 (판정 방식·조건 포함) |
| [`offline/`](offline/README.md) | 오프라인 평가 (probe, 반사실, 재표집, 재생) — **실물 성공률이 아님** |
| [`comparisons/`](comparisons/README.md) | 모델·조건 간 비교와 그 비교에서 통제되지 않은 차이 |

## 규칙
1. 실물 결과와 오프라인 결과를 같은 표에 섞지 않는다.
2. 성공률 옆에 항상 **판정 방식** (사람 UI / 자동 분류 / 분석자 판정) 과 **n** 을 적는다.
3. 서로 다른 조건의 성공률을 비교할 때는 데이터셋, 카메라, 시작 자세, 필터, RTC·추론 설정, 평가 위치, 큐브 각도, 날짜 차이를 같이 적고, 그 비교만으로 "개선" 이라고 쓰지 않는다.
4. 오프라인 지표는 데이터 종류를 표기한다: [in-sample] · [held-out fold] · [합성] · [반사실] · [재구성 (실물 관측 재추론)].
5. 진짜 held-out 사람 시연 세트 (H) 는 아직 없다.

## 지표 정의

### 실물
| 지표 | 정의 | 출처 |
|---|---|---|
| 최종 성공 | eval UI 에서 판 끝에 사람이 P/F (상자에 넣었나) | eval_ui |
| 첫 파지 성공 (사람) | eval_ab_ui 판정 칸 (redbox A/B·공간). 정의 문서 없음, 판정–메모 불일치 5판 | eval_ab |
| 첫 파지 (자동) | 첫 닫힘 c 뒤 1 s 그리퍼 최소 (사람 쥠 11.5–13.6 / 빈 닫힘 1–4), 2 s 안 TCP z ≥4 cm & 그리퍼 ≥9 = 들어 올림 | pan_inference_diagnostic/11 |
| 고정 / 미학습 위치 | K 3 cm 안 = near_K (좌표 검증됨), 밖 = off_K (미검증) | pan_inference_diagnostic/09 |
| 큐브 시작 각도 | 시작 front 화면 윤곽 → homography → minAreaRect | eval_space, cube_angle |
| Wrist Roll | 시작 → 첫 닫힘 \|Δroll\|, 방향 | eval_space |
| 초기 Pan 오차 / 첫 접근 | need = pe − 시작 pan (pe = front 사진 좌표 → bearing), 첫 1 s 이동 비율 = (chunk[29] − 시작) / need | pan_inference_diagnostic/09·10 |
| 첫 닫힘 Pan 오차 | (pe − pan) × need 부호 | pan_inference_diagnostic/10 |
| 파지 직전 정렬 | 손목 화면 큐브 u/v (사람 v 0.64–0.76), 닫기 영역 u 0.255–0.432·v 0.633–0.78; TCP 상대 높이 (kNN 사람 10편 대비) | pan_inference_diagnostic/11·13 |
| 실패 유형 | 큐브 밀림, 얕은 파지, 미끄러짐, 그리퍼 개방 부족, 팔 도착 전 닫힘, 손목 정렬 실패, 빈 닫힘 (앞쪽/아래쪽/가려짐), 지나침 (zone over) | eval_ab, pan_inference_diagnostic |

### 오프라인
| 지표 | 정의 |
|---|---|
| Vision Probe MAE / R² | 특징 → 손목 화면 큐브 상대 좌우 (cm), 판·위치 hold-out 5-fold |
| g_rep | 영상 편집 (큐브 이동) 에 대한 특징 예측 이동 비율 |
| G_tt / G_rr | 손목 영상 편집에 대한 정책 집게 끝 이동 (접선 / 반지름) 이득 |
| w_rot | roll state 변경에 따라 영상→탁자 매핑이 회전하는 정도 (1 = 완전 반영) |
| K 끌림 aK | 새 위치 pan 오차를 가까운 K 쪽으로 회귀한 계수 (합성 격자) |
| 첫 chunk 이득 k± | 첫 chunk 끝 pan 변화 / 사람 최종 pan 변화 |
| T4 목표 쪽 비율 | '손목 놓침·front 보임' 상태에서 실행 구간 (idx 10–29) 이 목표 쪽으로 ≥2° 가는 noise seed 비율 (U = RTC 없음, G = RTC) |
| 상태 커버리지 | roll × 접선 오차 칸별 판 수, 실물 프레임의 학습 이웃 수 |
