"""q04c 사람 256 편 pan state (판 시작 … close_start) 를 CSV 로 내보냄 (그림용, 시스템 python3 은 parquet 못 읽음). 읽기만.
출력: tables/q04c_human_pan_preclose.csv.gz (ep, frame, pan)
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python q04c_export_human_pan.py
"""
from pathlib import Path

import pandas as pd

D2 = Path.home() / "so101_runs/main_k8/d2"
OUT = D2 / "pan_inference_diagnostic/offline_pan_reversal_filter_off"
L = pd.read_parquet(D2 / "data_coverage_audit/02_servo_timeline.parquet", columns=["episode_id", "frame_index", "servo_name", "measured_position"])
L = L[L.servo_name == "shoulder_pan"]
cs = pd.read_csv(D2 / "data_coverage_audit/tables/a02_events.csv").set_index("ep").close_start
L = L[L.frame_index <= L.episode_id.map(cs)]
L.rename(columns={"episode_id": "ep", "frame_index": "frame", "measured_position": "pan"})[["ep", "frame", "pan"]].to_csv(OUT / "tables/q04c_human_pan_preclose.csv.gz", index=False)
print(len(L))
