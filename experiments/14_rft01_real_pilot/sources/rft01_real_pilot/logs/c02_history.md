# 파일럿 조건의 d2 020000 과거 실물 기록 [기록 · 자동 계산]

출처: /home/user/so101_runs/main_k8/r2_grasp_diagnostic/reports/summary_existing_20.csv · summary_r2_all_8.csv (시작 사진 판정 Known, 각도 = d2 규칙 분류), command.txt, dataset state. 생성 20261105_094920.

| run | ds_ep | K | 각도 | K 거리 cm | arm_filter | 첫 닫힘 T4 | 사용자 P/F | pan 최소 | pan 최대 |
|---|---|---|---|---|---|---|---|---|---|
| 20261029_170818 | 1 | K1 | 0 | 0.07 | false | no_close | F | -109.0 | 4.3 |
| 20261029_170818 | 2 | K1 | 0 | 0.08 | false | grasp | P | -33.2 | 4.3 |
| 20261029_170818 | 3 | K1 | 0 | 0.61 | false | grasp | P | -29.0 | 4.3 |
| 20261103_103428 | 0 | K1 | 0 | 0.33 | false | undetermined | F | -48.1 | 2.4 |
| 20261029_170818 | 0 | K1 | L30 | 0.05 | false | grasp | P | -26.7 | 4.8 |
| 20261029_160831 | 0 | K1 | L30 | 0.17 | true | empty | F | -43.0 | 5.6 |
| 20261029_170219 | 0 | K1 | L30 | 0.41 | true | no_close | F | -108.9 | 5.5 |
| 20261029_170219 | 1 | K1 | L30 | 0.4 | true | empty | F | -39.4 | 4.8 |
| 20261029_170219 | 2 | K1 | L30 | 0.15 | true | grasp | P | -26.2 | 5.1 |
| 20261029_160831 | 3 | K3 | 0 | 0.58 | true | empty | F | 4.3 | 37.9 |
| 20261103_103428 | 2 | K3 | R30 | 0.27 | false | empty | F | 1.6 | 37.8 |

## 조건 × arm_filter 집계

| K | 각도 | arm_filter | 판 | 첫 닫힘 grasp | empty | no_close · undetermined | 사용자 P | pan 최소 < −100 |
|---|---|---|---|---|---|---|---|---|
| K1 | 0 | false | 4 | 2 | 0 | 2 | 2 | 1 |
| K1 | 0 | true | 0 | 0 | 0 | 0 | 0 | 0 |
| K1 | L30 | false | 1 | 1 | 0 | 0 | 1 | 0 |
| K1 | L30 | true | 4 | 1 | 2 | 1 | 1 | 1 |
| K3 | 0 | false | 0 | 0 | 0 | 0 | 0 | 0 |
| K3 | 0 | true | 1 | 0 | 1 | 0 | 0 | 0 |
| K3 | R30 | false | 1 | 0 | 1 | 0 | 0 | 0 |
| K3 | R30 | true | 0 | 0 | 0 | 0 | 0 | 0 |
