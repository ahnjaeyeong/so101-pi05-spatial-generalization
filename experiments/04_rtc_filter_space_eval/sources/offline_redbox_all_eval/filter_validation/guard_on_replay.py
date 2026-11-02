"""감시 규칙(horizon·stale·starve)을 재생 추론 로그에 적용 — 정상(현실 지연)과 스파이크 조건에서 몇 번 작동하나. CPU.
재생 json 의 delays = [(추정 delay, 실제 지연 틱)] (RTC 추론마다), hold_or_starved = 명령 없는 틱 수(시작 포함).
"""

import glob
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
H, STALE, HCOUNT = 20, 30, 10
rows = []
for d in ["runs_wide_lat1.55", "runs_wide_spike"]:
    for f in sorted(glob.glob(str(HERE / d / "run_rtc*.json"))):
        m = json.load(open(f))
        for sn, s in m["sources"].items():
            dl = s["delays"]
            run, htrips, maxrun = 0, 0, 0
            for est, real in dl:
                run = run + 1 if est >= H else 0
                maxrun = max(maxrun, run)
                if run == HCOUNT: htrips += 1
            rows.append(dict(cond=d.replace("runs_wide_", ""), src=sn, inferences=len(dl), est_ge_h=sum(e >= H for e, _ in dl),
                             max_consecutive_est_ge_h=maxrun, horizon_trips=htrips, stale_merges=sum(r >= STALE for _, r in dl),
                             real_delay_max=max(r for _, r in dl), no_cmd_ticks=s["hold_or_starved"]))
import pandas as pd  # noqa: E402
T = pd.DataFrame(rows)
T.to_csv(HERE / "guard_on_replay.csv", index=False)
print(T.groupby("cond")[["inferences", "est_ge_h", "horizon_trips", "stale_merges", "real_delay_max", "no_cmd_ticks"]].agg(["sum", "max"]).to_string())
