"""p04b harness 결과 모음 (CPU, 읽기만). harness/<run>/harness_<diag>.json + diag/summary.json + diag/replay/replay.csv + 디스크 사용량.
출력 tables/p04_harness_summary.csv, p04_harness_summary.json
사용: PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python p04b_harness_summary.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path.home() / "so101_runs/main_k8/d2/pan_inference_diagnostic"
rows = []
for f in sorted((OUT / "harness").glob("*/harness_*.json")):
    d = json.loads(f.read_text())
    lat = np.array(d["rtc_latency_s"]["all"])
    r = dict(run=f.parent.name, diag=d["diag"], ticks=d["ticks"], sent=d["sent"], starved=d["starved"], bus_writes=d["bus_writes"],
             n_infer=len(lat), lat_first_s=lat[0], lat_rest_p50_s=np.median(lat[1:]), lat_rest_max_s=lat[1:].max(),
             body_p50_ms=d["loop_body_ms"]["p50"], body_p99_ms=d["loop_body_ms"]["p99"], body_max_ms=d["loop_body_ms"]["max"])
    dg = f.parent / "diag"
    if (dg / "summary.json").exists():
        s = json.loads((dg / "summary.json").read_text())
        r.update(written_chunk=s["written"]["chunk"], written_tick=s["written"]["tick"], dropped_chunk=s["dropped"]["chunk"],
                 dropped_tick=s["dropped"]["tick"], ctl_wrapper_us_p50=s["ctl_wrapper_us"]["p50"], ctl_wrapper_us_p99=s["ctl_wrapper_us"]["p99"],
                 rtc_wrapper_us_p50=s["rtc_wrapper_us"]["p50"], writer_chunk_ms_p50=s["writer_chunk_ms"]["p50"],
                 wrapper_errors=len(s["wrapper_errors"]),
                 disk_bytes=sum(p.stat().st_size for p in dg.rglob("*") if p.is_file() and "replay" not in p.parts))
        r["disk_bytes_per_chunk"] = r["disk_bytes"] / max(r["written_chunk"], 1)
        rp = dg / "replay" / "replay.csv"
        if rp.exists():
            R = pd.read_csv(rp)
            r.update(replay_n=len(R), replay_max_abs_deg=R.replay_max_abs_deg.max(), replay_max_abs_norm=R.replay_max_abs_norm.max())
    rows.append(r)
D = pd.DataFrame(rows)
D.to_csv(OUT / "tables/p04_harness_summary.csv", index=False)
S = {k: {"lat_rest_p50_s": [float(x) for x in g.lat_rest_p50_s], "body_p50_ms": [float(x) for x in g.body_p50_ms],
         "body_p99_ms": [float(x) for x in g.body_p99_ms], "starved": [int(x) for x in g.starved]} for k, g in D.groupby("diag")}
json.dump(S, open(OUT / "tables/p04_harness_summary.json", "w"), indent=1)
pd.set_option("display.width", 250, "display.max_columns", 40)
print(D.round(3).T.to_string())
