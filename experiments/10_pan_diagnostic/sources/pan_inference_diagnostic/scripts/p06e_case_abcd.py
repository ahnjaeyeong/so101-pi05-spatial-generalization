"""p06e 작업 지시 6 절 A/B/C/D 분류 (CPU, 읽기만). chunk 단위, 첫 닫힘 전, 관측 때 |남은 오차| ≥ 6°.

입력 tables/p06b_chunks.csv (기록 L · 재구성 U/G 중앙), p01_ticks.parquet (state)
기준 (임의 문턱, 바꾸면 결과 달라짐):
  fU = (U 중앙[e] − s_obs)/resid   재구성: 새 관측에서 RTC 없이 모델이 낸 1 s 계획 (e = 그 chunk 마지막 실행 index ≈ 29)
  fG = (G 중앙[e] − s_obs)/resid   재구성: 같은 noise 로 RTC 안내 넣은 것
  fL = (L[e] − s_obs)/resid        실측: 실제 실행된 명령
  fS = (state[e 틱 + 4] − s_obs)/resid  실측: 4 틱 (측정된 서보 지연) 뒤 실제 위치
  D  : fU ≤ −0.1 (모델 계획 중앙이 반대 방향)
  A  : −0.1 < fU < 0.25 (모델 계획 중앙이 1 s 에 need 의 25 % 미만)
  B  : fU ≥ 0.25 이고 fG < fU − 0.15 (RTC 안내가 계획을 0.15 넘게 줄임)
  B' : fU ≥ 0.25, B 아님, fL < 0.5·fU (실행된 명령이 재구성 중앙의 절반 미만 — noise 차이 또는 재구성 오차와 구분 불가)
  C  : fU ≥ 0.25, B · B' 아님, fS < 0.5·fL (명령은 갔는데 실제 위치가 절반도 못 감)
  ok : 나머지
출력 tables/p06e_abcd.csv, p06e_abcd_summary.json
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python p06e_case_abcd.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

TAB = Path.home() / "so101_runs/main_k8/d2/pan_inference_diagnostic/tables"
R = pd.read_csv(TAB / "p06b_chunks.csv")
T = pd.read_parquet(TAB / "p01_ticks.parquet")
rows = []
for _, r in R[R.resid.abs() >= 6].iterrows():
    run = "20261026_" + ("135128_" if r.ep.startswith("20k_t1_try3/") else "140246_") + r.ep.split("/")[0]
    g = T[(T.run == run) & (T.ep == int(r.ep.split("ep")[-1]))]
    sel = np.where((g.chunk_id.values == r.chunk_id) & (g.chunk_idx.values == r.idx_end))[0]
    if not len(sel):
        continue
    t = min(int(sel[0]) + 4, len(g) - 1)
    so = r.state_obs
    fU = (r.U_med_end - so) / r.resid
    fG = (r.G_med_end - so) / r.resid
    fL = (r.L_end - so) / r.resid
    fS = (g.state_shoulder_pan.values[t] - so) / r.resid
    if fU <= -0.1:
        c = "D"
    elif fU < 0.25:
        c = "A"
    elif fG < fU - 0.15:
        c = "B"
    elif fL < 0.5 * fU:
        c = "B'"
    elif fS < 0.5 * fL:
        c = "C"
    else:
        c = "ok"
    rows.append(dict(ep=r.ep, chunk_id=int(r.chunk_id), t_obs=r.t_obs, resid=r.resid, fU=fU, fG=fG, fL=fL, fS=fS, cls=c))
D = pd.DataFrame(rows)
D.to_csv(TAB / "p06e_abcd.csv", index=False)
S = {"all": D.cls.value_counts().to_dict(), "first4s": D[D.t_obs < 4].cls.value_counts().to_dict(),
     "by_ep": {e: g.cls.value_counts().to_dict() for e, g in D.groupby("ep")},
     "median_fU_fG_fL_fS": {k: float(D[k].median()) for k in ("fU", "fG", "fL", "fS")}}
json.dump(S, open(TAB / "p06e_abcd_summary.json", "w"), indent=1)
print(json.dumps(S, indent=1))
print(D[D.t_obs < 4].round(2).to_string(index=False))
