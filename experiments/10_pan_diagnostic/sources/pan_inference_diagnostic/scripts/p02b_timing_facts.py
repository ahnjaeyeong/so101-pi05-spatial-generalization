"""p02b 시간·필터 사실 (읽기만, CPU). 입력 p01_merges.csv, p01_ticks.parquet, filter_log.csv, 사람 a02_frames. 출력 tables/p02b_timing.json"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HOME = Path.home()
sys.path.insert(0, str(HOME / "so101_runs/main_k8/d2/data_coverage_audit/scripts"))
import ac  # noqa: E402

TAB = ac.D2 / "pan_inference_diagnostic/tables"
M = pd.read_csv(TAB / "p01_merges.csv")
T = pd.read_parquet(TAB / "p01_ticks.parquet")
o = {}
first = M[M.chunk_id == 0]
rest = M[M.chunk_id > 0]
q = lambda s: {"n": int(s.notna().sum()), "p5": float(s.quantile(.05)), "p50": float(s.median()), "p95": float(s.quantile(.95)), "max": float(s.max())}  # noqa: E731
o["latency_first_chunk_s"] = q(first.latency_s)
o["latency_later_s"] = q(rest.latency_s)
o["merge_interval_s"] = q(rest.merge_interval_s)
o["applied_delay_later"] = rest.applied_delay.value_counts().sort_index().to_dict()
o["real_delay_log_later"] = rest.real_delay_log.value_counts().sort_index().to_dict()
# 실행 구간 길이 (chunk 당 실행된 action 수)
seg = T.groupby(["run", "ep", "chunk_id"]).size()
o["exec_actions_per_chunk"] = {"chunk0": q(seg.xs(0, level="chunk_id").astype(float)), "later": q(seg[seg.index.get_level_values("chunk_id") > 0].astype(float))}
ci = T[T.chunk_id > 0].chunk_idx
o["exec_chunk_index_range_later"] = {"min": int(ci.min()), "p50_min_per_chunk": float(T[T.chunk_id > 0].groupby(["run", "ep", "chunk_id"]).chunk_idx.min().median()),
                                     "p50_max_per_chunk": float(T[T.chunk_id > 0].groupby(["run", "ep", "chunk_id"]).chunk_idx.max().median()), "max": int(ci.max())}
# arm_filter pan 속도 제한 (filt 실행)
L = pd.read_csv(ac.D2 / "eval/rollouts/20261026_140246_20k_t1_try3_filt/filter_log.csv", dtype={"vclip_mask": str, "ema_reset_mask": str})
C = L[L.event == "cmd"].copy()
C["vclip_pan"] = C.vclip_mask.fillna("").astype(str).str[0] == "1"
C["ema_reset_pan"] = C.ema_reset_mask.fillna("").astype(str).str[0] == "1"
C["k"] = C.groupby("episode").cumcount()
o["filt_pan_vclip_ticks"] = {int(e): int(g.vclip_pan.sum()) for e, g in C.groupby("episode")}
o["filt_pan_vclip_ticks_first3s"] = {int(e): int(g[g.k < 90].vclip_pan.sum()) for e, g in C.groupby("episode")}
o["filt_pan_ema_reset_ticks"] = {int(e): int(g.ema_reset_pan.sum()) for e, g in C.groupby("episode")}
o["vclip_mask_example"] = str(C.vclip_mask.dropna().iloc[0]) if C.vclip_mask.notna().any() else None
o["vmax_pan_deg_per_tick"] = 2.4615383
# 사람: 첫 pan 움직임 중 리더 pan 프레임 간 변화가 vmax 를 넘는 비율
W = pd.read_parquet(ac.TAB / "a02_frames.parquet")
E = pd.read_csv(ac.TAB / "a02_events.csv")
fr, eps = [], 0
pk = []
for e in range(256):
    g = W[W.ep == e]
    on = int(E.onset[e])
    a = g.a_shoulder_pan.values[on:on + 45]
    d = np.abs(np.diff(a))
    fr.append((d > 2.4615383).mean())
    eps += int((d > 2.4615383).any())
    pk.append(d.max() * 30)
o["human_first1p5s_frac_frames_over_vmax"] = {"p50": float(np.median(fr)), "mean": float(np.mean(fr))}
o["human_eps_with_any_over_vmax_first1p5s"] = eps
o["human_pan_peak_speed_deg_s_first1p5s"] = {"p50": float(np.median(pk)), "p95": float(np.percentile(pk, 95))}
# 정책 raw pan 속도 (처음 3 s)
pk2 = {}
for (r, e), g in T.groupby(["run", "ep"]):
    d = np.abs(np.diff(g.raw_shoulder_pan.values[:90]))
    pk2[f"{r[16:]}/ep{e}"] = {"peak_deg_s": float(d.max() * 30), "frac_over_vmax": float((d > 2.4615383).mean())}
o["policy_raw_pan_first3s"] = pk2
json.dump(o, open(TAB / "p02b_timing.json", "w"), indent=1, default=float)
print(json.dumps(o, indent=1, default=float))
