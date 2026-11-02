"""p02d 첫 닫힘 직전 3 s pan: 기록 명령 (raw · sent) 과 state 의 차, 목표 (pe, 영상 추정) 와의 차 (읽기만, CPU).
'명령은 목표에 갔는데 서보가 못 갔는가' 와 '명령 자체가 목표에 못 갔는가' 를 가르는 표.
출력 tables/p02d_late_cmd.csv
  raw/sent/state_med : 구간 중앙값 (°)
  sent_minus_state4_abs_p50 : |sent[t] − state[t+4]| 중앙값 (서보 지연 4 틱 반영)
  pe_minus_sent_med, pe_minus_state_med : 목표 − 명령, 목표 − state (need 부호 곱, 양수 = 목표에 못 미침)
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python p02d_late_cmd.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

TAB = Path.home() / "so101_runs/main_k8/d2/pan_inference_diagnostic/tables"
T = pd.read_parquet(TAB / "p01_ticks.parquet")
P = pd.read_csv(TAB / "p02_policy_episodes.csv")
rows = []
for (r, e), g in T.groupby(["run", "ep"]):
    tag = f"{r[16:]}/ep{e}"
    p = P[P.ep == tag].iloc[0]
    c = int(round(p.first_close_s * 30))
    a, b = max(c - 90, 0), c
    raw, sent, st = g.raw_shoulder_pan.values, g.sent_shoulder_pan.values, g.state_shoulder_pan.values
    sg = np.sign(p.need)
    w = slice(a, b)
    lagd = np.abs(sent[a:b - 4] - st[a + 4:b])
    rows.append(dict(ep=tag, frames=f"{a}-{b}", raw_med=np.median(raw[w]), sent_med=np.median(sent[w]), state_med=np.median(st[w]),
                     raw_range=np.ptp(raw[w]), sent_minus_state4_abs_p50=np.median(lagd), sent_minus_state4_abs_p95=np.percentile(lagd, 95),
                     pe=p.pe, pe_minus_sent_med=sg * (p.pe - np.median(sent[w])), pe_minus_state_med=sg * (p.pe - np.median(st[w]))))
R = pd.DataFrame(rows)
R.to_csv(TAB / "p02d_late_cmd.csv", index=False)
print(R.round(2).to_string(index=False))
