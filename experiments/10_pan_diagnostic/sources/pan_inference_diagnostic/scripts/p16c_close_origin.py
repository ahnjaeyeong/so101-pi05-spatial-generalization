"""p16c 닫힘 결정이 어느 chunk 에서 처음 계획됐는지 (읽기만, CPU).
닫힘 이벤트마다 그 앞 chunk 들 (최대 5 개) 의 계획 그리퍼 닫힘 시작을 '절대 틱' 으로 바꿔 나열한다:
  G = 기록된 chunk (RTC 안내 뒤, 실측) · U = 같은 관측 · 같은 noise 의 RTC 안내 없는 반사실 (p05)
  절대 시각 = merge 틱 + (index − 적용 delay) − 첫 정책 틱  (p16 의 tc 와 같은 '정책 틱 행 번호' 단위)
  닫힘 시작 = gripper < 앞선 최대 − 3 인 첫 index (없으면 '없음')
출력: filter_ab/p16c_close_origin.csv
사용: PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python p16c_close_origin.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

D2 = Path.home() / "so101_runs/main_k8/d2"
AB = D2 / "pan_inference_diagnostic/filter_ab"
ROLL = D2 / "eval/rollouts"
RUNS = {"A": "20261029_170219_32_20000_20k_filt_on", "B": "20261029_170818_32_20000_20k_filt_off"}


def cidx(gp):
    k = np.where(gp < np.maximum.accumulate(gp) - 3)[0]
    return int(k[0]) if len(k) else None


E = pd.read_csv(AB / "p16_events.csv")
E = E[E.event.astype(str) != "lost"]
rows = []
for _, e in E.iterrows():
    dg = ROLL / RUNS[e.tag[0]] / "diag"
    metas = {m["chunk_id"]: m for m in (json.loads(x) for x in (dg / "chunks.jsonl").read_text().splitlines())}
    RZ = np.load(dg / "replay/replay.npz")
    k0 = int(e.plan_chunk)
    ep = metas[k0]["episode"]
    TK = pd.read_csv(dg / "ticks.csv")
    off0 = int(TK[(TK.episode == ep) & (TK.pop_chunk >= 0)].tick.min())  # tc · on 은 정책 틱 행 번호 (첫 정책 틱 = 0) → 틱 번호 = 행 + off0
    for k in range(k0 - 5, k0 + 1):
        m = metas.get(k)
        if m is None or m["episode"] != ep:
            continue
        P = np.load(dg / "chunks" / f"c{k:05d}.npz")["processed"]
        O = RZ[f"rtc_off_c{k:05d}"] if f"rtc_off_c{k:05d}" in RZ else None
        base = m["tick_at_merge"] - m["applied_delay"] - off0  # 행 번호 기준
        g, u = cidx(P[:, 5]), (cidx(O[:, 5]) if O is not None else None)
        rows.append(dict(tag=e.tag, event=e.event, cond=e.cond, tc=int(e.tc), chunk=k, merge_tick=m["tick_at_merge"], inference_delay=m.get("inference_delay"),
                         G_close_tick=None if g is None else base + g, U_close_tick=None if u is None else base + u,
                         G_close_idx=g, U_close_idx=u))
D = pd.DataFrame(rows)
D.to_csv(AB / "p16c_close_origin.csv", index=False)
pd.set_option("display.width", 200)
print(D.to_string(index=False))
