# practice/sg_pin_pilot2 — SG50 배치표 (3편)

- 만든 때 2026-11-12T13:03:38 · 설정 `$HOME/so101_runs/main_k8/r1_r2_collection/config/sg50.yaml` (sha256 1cba1fb24c73) · 계획 sha256 f1dfafa21569
- 큐브 회전각 **0°** = redbox8_layouts.yaml angles: 로봇에 가장 가까운 면의 모서리 ↔ 로봇 좌우축 예각 = 0 (위에서 볼 때). wrist_roll 아님
- 큐브 2.5 cm · 스티커 미정 (예비 시연 확인 전) · front H 7c6b080cf79eb457 · follower 보정 0e539000c753c8a0 · leader 보정 4f62ad9c95c966ed
- 손목 필요 회전 = 0° 큐브를 잡을 때 필요한 손목 회전 참고값 (wrap90(0 − 방향), + 반시계). wrist_roll 목표가 아님.
- N 위치 = 계산 좌표 (미확정). front 화면 흰 점선에 놓아 확인한 뒤 설정 confirmed: true.

| ep | 시작 자세 | 큐브 | 각도 | 좌표 cm | 확정 | d2 학습 위치 | 방향° | 손목 필요° | 평가 자리까지 cm | split | 접근 |
|---:|---|---|---|---|---|---|---:|---:|---:|---|---|
| 0 | S0 쉬는 자세 + 손목 돌림 | K3 | ↻30° | -8.5,-3.5 | ✓ | d2 Known (K 마다 32편 학습) | -33 | +3 | 3.5 | train_candidate |  |
| 1 | S0 쉬는 자세 + 손목 돌림 | K1p7 | ↺30° | -9.5,21.5 | ✓ | K1 영역 무작위 (탁자 표시 없음, front 빨간 원) | +26 | +4 | 3.9 | train_candidate |  |
| 2 | S0 쉬는 자세 + 손목 돌림 | K4p2 | 45° | -15.0,24.5 | ✓ | K4 영역 무작위 (탁자 표시 없음, front 빨간 원) | +40 | +5 | 4.5 | train_candidate |  |

## 분포

- 위치별: K1p7 1, K3 1, K4p2 1
- 시작 자세별: S0 3

## 시작 자세 후보

- **S0 쉬는 자세 + 손목 돌림** (user_fixed): pan -4.3±8, lift -102.9±5, elbow 95.3±8, wflex 77.8±12, wroll 92.9±10, grip 1.2±5 — 출처: 사용자 2026-11-06: '휴식자세랑 거의 비슷한데, 현재 자세처럼 손목의 형태가 돌아가 있어야 해'
- **P0 쉬는 자세** (confirmed_in_d2): pan -4.3±8, lift -102.9±5, elbow 95.3±8, wflex 65.5±12, wroll 2.5±10, grip 1.2±5 — 출처: d2 256편 첫 프레임 팔로워 평균 (d2/data_coverage_audit/03_initial_state_analysis.md 3.1)
- **P1 접은 채 Pan 로봇 왼쪽** (candidate_user_check): pan -55±10, lift -103±5, elbow 95±8, wflex 70±12, wroll 2±10, grip 1.2±5 — 출처: R1 파일럿 시작 (main_k8/r12_pilot12_r1 ep4 pan −65.5 · ep6 −53.5, 팔 접힘 lift −103) 사이 값
- **P2 접은 채 Pan 로봇 오른쪽** (candidate_user_check): pan 55±10, lift -103±5, elbow 96±8, wflex 64±12, wroll 1.2±10, grip 1.2±5 — 출처: R1 파일럿 시작 (ep5 pan +67.7 · ep7 +56.5, 팔 접힘) 사이 값
- **P3 상자 위** (candidate_user_check): pan -0.7±8, lift 34.1±10, elbow -40.1±12, wflex 70.3±12, wroll 6.7±12, grip 1.2±5 — 출처: d2 256편 '파지 뒤 처음 그리퍼 열기 (상자 위 놓기)' 순간 팔로워 중앙값 (pan −0.7 lift 34.1 elbow −40.1 wflex 70.3 wroll 6.7). 그리퍼는 그때 12.6 (큐브 쥠) → 시작은 닫힘 1.2 로 제안
