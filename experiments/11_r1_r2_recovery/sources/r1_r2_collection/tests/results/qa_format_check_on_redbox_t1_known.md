# R1/R2 품질 검사 — main_k8/r2_pregrasp_pilot

- 만든 시각: 2026-10-30 15:27 · dataset `~/so101_runs/main_k8/redbox_t1_known/dataset` (읽기만)
- 계획 `r12_plan.csv` 32줄 (유효 32) · 저장 66편 · 제외 표시 0편
- 문제 없음 0/66 (제외 판 빼고)

## 1. d2 와 형식 비교

| 항목 | 결과 |
|---|---|
| features.action | 같음 |
| features.observation.state | 같음 |
| features.observation.images.front | 같음 |
| features.observation.images.wrist | 같음 |
| features.timestamp | 같음 |
| features.frame_index | 같음 |
| features.episode_index | 같음 |
| features.index | 같음 |
| features.task_index | 같음 |
| features 이름 집합 | 같음 |
| fps | 30 (d2 30) 같음 |
| robot_type | so_follower (d2 so_follower) 같음 |
| codebase_version | v3.0 (d2 v3.0) 같음 |
| tasks | ['pick up the red cube and put it in the brown box'] = d2 |
