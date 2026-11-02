"""q04b d2 사람 256 편 접근 구간의 손목 큐브 가시성 (읽기만, CPU). dataset 영상 3 프레임마다, 판 시작 … close_start.

측정: p14 wrist_measure (빨강 덩어리 ≥ 300 px). 'lost_after_seen' = 그 판에서 손목에 큐브를 본 뒤, 연속 ≥ 1 s (3 프레임 간격 10 칸) 안 보임.
각 lost 구간: 시작 · 끝 프레임, 그 동안 pan 이 목표 (pan_c) 를 지나친 정도 s·(pan − pan_c) 최대, pan 이동 방향 (목표 쪽 / 반대 / 정지), 구간 뒤 다시 보임 여부.
출력: tables/q04b_wrist_vis.csv.gz (판 · 프레임 · 보임 · u · v), q04b_lost_segments.csv, q04b_summary.json
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python q04b_human_wrist_lost.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

D2 = Path.home() / "so101_runs/main_k8/d2"
PD = D2 / "pan_inference_diagnostic"
OUT = PD / "offline_pan_reversal_filter_off"
sys.path.insert(0, str(PD / "scripts"))
sys.path.insert(0, str(D2 / "diag_grasp_bias"))
import p14_grasp_analysis as P14  # noqa: E402
import common as Cm  # noqa: E402

STEP = 3


def main():
    EP = pd.read_csv(OUT / "tables/q04_human_episodes.csv")
    L = pd.read_parquet(D2 / "data_coverage_audit/02_servo_timeline.parquet", columns=["episode_id", "frame_index", "servo_name", "measured_position"])
    pan = L[L.servo_name == "shoulder_pan"].sort_values(["episode_id", "frame_index"])
    cache, rows, segs = {}, [], []
    for _, e in EP.iterrows():
        cs = int(e.close_start)
        fr = Cm.frames(D2 / "dataset", int(e.ep), "wrist", 0, cs, cache)
        x = pan[pan.episode_id == e.ep].measured_position.values[:cs + 1]
        vis = []
        for i in range(0, min(len(fr), cs + 1), STEP):
            w = P14.wrist_measure(fr[i])
            vis.append(bool(w.get("w_vis", False)))
            rows.append(dict(ep=int(e.ep), frame=i, w_vis=vis[-1], w_u=w.get("w_u", np.nan), w_v=w.get("w_v", np.nan)))
        vis = np.array(vis)
        seen = np.cumsum(vis) > 0
        k = 0
        while k < len(vis):
            if not vis[k] and seen[k]:
                j = k
                while j < len(vis) and not vis[j]:
                    j += 1
                if j - k >= 10:
                    f0, f1 = k * STEP, min(cs, (j - 1) * STEP)
                    seg = x[f0:f1 + 1]
                    past = e.s * (seg - e.pan_c) if e.s else np.full(len(seg), np.nan)
                    d = seg[-1] - seg[0]
                    segs.append(dict(ep=int(e.ep), f0=f0, f1=f1, dur_s=(f1 - f0) / 30, reacquired=bool(j < len(vis)), pan_start=float(seg[0]), pan_end=float(seg[-1]),
                                     past_target_max=float(np.nanmax(past)) if len(seg) else np.nan, move=float(d),
                                     move_dir=("hold" if abs(d) < 2 else ("toward" if e.s and np.sign(d) == np.sign(e.pan_c - seg[0]) else "away"))))
                k = j
            else:
                k += 1
    V = pd.DataFrame(rows)
    S = pd.DataFrame(segs)
    V.to_csv(OUT / "tables/q04b_wrist_vis.csv.gz", index=False)
    S.to_csv(OUT / "tables/q04b_lost_segments.csv", index=False)
    first_seen = V[V.w_vis].groupby("ep").frame.min()
    summ = {"n_eps": int(EP.shape[0]), "eps_seen_before_close": int(first_seen.shape[0]),
            "first_seen_s_quantiles": {q: float(first_seen.quantile(q / 100) / 30) for q in (10, 50, 90)},
            "eps_with_lost_after_seen_ge1s": int(S.ep.nunique()) if len(S) else 0, "n_segments": int(len(S)),
            "segments_past_target_gt5": int((S.past_target_max > 5).sum()) if len(S) else 0,
            "segments_move_dir": S.move_dir.value_counts().to_dict() if len(S) else {},
            "segments_dur_s_quantiles": {q: float(S.dur_s.quantile(q / 100)) for q in (50, 90, 100)} if len(S) else {}}
    (OUT / "tables/q04b_summary.json").write_text(json.dumps(summ, indent=1, ensure_ascii=False))
    print(json.dumps(summ, indent=1, ensure_ascii=False))
    if len(S):
        print(S.round(1).to_string())


if __name__ == "__main__":
    main()
