"""p14b 파일럿 판의 닫힘 시작 (on) 관절 · TCP 를 '큐브가 가장 가까운 사람 시연 10 편' 의 같은 시점 값과 비교 + 모든 닫힘 이벤트 표 (읽기만, CPU).
입력: pilot/p14_grasp_pilot.csv, p14_grasp_human.csv, 실행 filter_log
출력: pilot/p14b_knn_joint_diff.csv (판별 관절 · TCP: 정책 − 이웃 사람 중앙, 이웃 사람 p10–p90 폭), pilot/p14b_close_events.csv (판별 모든 닫힘: 바닥 · 들어 올림)
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python p14b_grasp_vs_human_knn.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import cube_coords as CC  # noqa: E402

ac, C = CC.ac, CC.C
OUT = Path(__import__("os").environ.get("PILOT_DIR", CC.D2 / "pan_inference_diagnostic/pilot"))  # 다른 묶음은 PILOT_DIR 로
J = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
COLS = {"pan_on": "shoulder_pan", "lift_on": "shoulder_lift", "elbow_on": "elbow_flex", "wflex_on": "wrist_flex", "roll_on": "wrist_roll",
        "z_c": "TCP z (cm)", "e_r": "TCP 반지름 (cm)", "e_t": "TCP 접선 (cm)", "w_v": "손목 화면 세로", "w_u": "손목 화면 가로"}
P = pd.read_csv(OUT / "p14_grasp_pilot.csv")
H = pd.read_csv(OUT / "p14_grasp_human.csv").dropna(subset=["on"])
rows = []
for _, r in P.iterrows():
    d = np.hypot(H.cube_x - r.cube_x, H.cube_y - r.cube_y)
    nn = H.iloc[np.argsort(d.values)[:10]]
    row = dict(label=r.label, verdict=r.verdict, nn_dist_max_cm=float(np.sort(d.values)[9]))
    for c, nm in COLS.items():
        if c in r and not pd.isna(r[c]):
            row[f"{c}_diff"] = float(r[c] - nn[c].median())
            row[f"{c}_nn_p10_p90"] = float(nn[c].quantile(.9) - nn[c].quantile(.1))
            row[f"{c}_out"] = bool(r[c] < nn[c].quantile(.1) or r[c] > nn[c].quantile(.9))
    rows.append(row)
K = pd.DataFrame(rows)
K.to_csv(OUT / "p14b_knn_joint_diff.csv", index=False)
ev = []
R = CC.D2 / "eval/rollouts"
for _, r in P.iterrows():
    FL = pd.read_csv(R / r.run / "filter_log.csv", dtype={"vclip_mask": str, "ema_reset_mask": str})
    f = FL[(FL.event == "cmd") & (FL.episode == r.episode)].sort_values("tick")
    s = f[[f"state_{j}" for j in J]].values.astype(float)
    g = s[:, 5]
    Pz = ac.tcp(s[:, :5])[:, 2]
    for k, c in enumerate(C.close_events(g)):
        w = slice(c, min(c + 30, len(g)))
        lw = slice(c, min(c + 61, len(g)))
        ev.append(dict(label=r.label, verdict=r.verdict, event=k, t_s=c / 30, bottom=float(g[w].min()), z_up=float(Pz[lw].max() - Pz[c]),
                       held=bool(g[lw].min() >= 9)))
E = pd.DataFrame(ev)
E.to_csv(OUT / "p14b_close_events.csv", index=False)
pd.set_option("display.width", 250, "display.max_columns", 40)
print(K[["label", "verdict", "nn_dist_max_cm"] + [f"{c}_diff" for c in COLS] ].round(2).to_string(index=False))
print(K[["label"] + [f"{c}_out" for c in COLS]].to_string(index=False))
print("이웃 사람 p10–p90 폭 중앙:", {c: round(float(K[f"{c}_nn_p10_p90"].median()), 2) for c in COLS})
print(E.round(2).to_string(index=False))
