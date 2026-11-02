"""p18b 하강 구간 (p18 의 s0 … tc) 의 틱별 FK 상대 경로 (반지름 · 접선 · z, s0 기준 cm) 를 신호별로 저장 (읽기만, CPU). 그림 p18c 용.
FK 는 상대 이동만 (K1 에서 절대 위치 4–5 cm 불일치). 출력 filter_ab/p18_fk_ticks.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import p16_k1_pregrasp as P16  # noqa: E402
import p18_descent_path as P18  # noqa: E402

ac = P18.ac
P = pd.read_csv(P18.AB / "p18_paths.csv")[["tag", "event", "cond", "s0", "tc", "bottom"]].drop_duplicates()
keys = [f"{j}.pos" for j in P16.J]
rows = []
for _, e in P.iterrows():
    G, epi = e.tag[0], int(e.tag[1])
    run = P16.RUNS[G]
    ep = sorted(pd.read_csv(P18.ROLL / run / "filter_log.csv", usecols=["episode"]).episode.unique())[epi]
    f, t, RZ, proc = P16.load(run, ep)
    sig = {"rtc": f[[f"raw_{j}" for j in P16.J]].values.astype(float), "out": f[[f"out_{j}" for j in P16.J]].values.astype(float),
           "present": t[[f"present_{j}" for j in P16.J]].values.astype(float)}
    if G == "B":
        af = P18.ArmFilter(keys, enabled=True)
        sig["cf_out"] = np.array([af.step(sig["rtc"][i], sig["present"][i] if i == 0 else None)[0] for i in range(len(f))])
    s0, tc = int(e.s0), int(e.tc)
    for nm, Q in sig.items():
        Pp = ac.tcp(Q[s0:tc + 1, :5])
        ur = (Pp[0, :2] - ac.BASE) / np.linalg.norm(Pp[0, :2] - ac.BASE)
        ut = np.array([-ur[1], ur[0]])
        d = Pp - Pp[0]
        for i in range(len(Pp)):
            rows.append(dict(tag=e.tag, event=e.event, cond=e.cond, bottom=e.bottom, signal=nm, t_rel_s=(s0 + i - tc) / 30,
                             radial=float(d[i, :2] @ ur), tangential=float(d[i, :2] @ ut), dz=float(d[i, 2])))
pd.DataFrame(rows).to_csv(P18.AB / "p18_fk_ticks.csv", index=False)
print("ok", len(rows))
