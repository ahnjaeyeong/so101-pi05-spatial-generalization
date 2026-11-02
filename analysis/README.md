# analysis

| 경로 | 내용 |
|---|---|
| `loss/<run_id>_loss.csv` | 학습 로그에서 추출한 step·시각·epoch·loss·grad_norm·lr (log_freq 50 마다). **학습 loss 만 있고 검증 loss 는 없다** |
| `figures/loss_curves.png` | 위 표의 loss 곡선 (로그 축) |
| `scripts/` | 이 저장소에서 새로 만드는 분석 스크립트 자리. 기존 분석 스크립트 사본은 각 `experiments/*/sources/` 에 원래 폴더 구조대로 있다 |

loss 가 낮아진 것과 실물 성공률은 별개다 (예: redbox 20k→30k loss 동일·첫 파지 하락; A0/A1/A2 loss 모두 0.019).
