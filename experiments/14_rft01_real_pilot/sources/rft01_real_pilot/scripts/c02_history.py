"""c02 — 파일럿 조건 (K1 · K3 × 0 · L30 · R30) 의 d2 020000 과거 실물 기록 (읽기만, CPU).

출처: r2_grasp_diagnostic/reports/summary_existing_20.csv (10-29 4 실행) · summary_r2_all_8.csv (11-03 2 실행) [기록 · 자동 계산],
      각 run 의 command.txt (arm_filter), dataset observation.state (pan 최소 · 최대).
출력: logs/c02_history.md · logs/c02_history.csv (있으면 _<시각>)
"""
import csv
import datetime
import glob
import re
from pathlib import Path

import numpy as np
import pandas as pd

S_DIR = Path(__file__).resolve().parents[1]
K8 = Path.home() / "so101_runs/main_k8"
REP = K8 / "r2_grasp_diagnostic/reports"
RUN_DIRS = [K8 / "d2/eval/rollouts", K8 / "r2_grasp_diagnostic/eval/rollouts"]
COND = {("K1", "0"), ("K1", "L30"), ("K3", "0"), ("K3", "R30")}


def run_dir(name):
    for d in RUN_DIRS:
        hits = [p for p in glob.glob(str(d / f"{name}*")) if Path(p).is_dir()]
        if hits:
            return Path(hits[0])
    return None


def main():
    rows = []
    for f in ("summary_existing_20.csv", "summary_r2_all_8.csv"):
        for r in csv.DictReader(open(REP / f, newline="")):
            rows.append(r)
    out = []
    cache = {}
    for r in rows:
        k, ang = r.get("nearest_K"), r.get("angle_class")
        pos = r.get("position", "")
        if (k, ang) not in COND or "Known" not in pos:
            continue
        rd = run_dir(r["run"])
        filt = None
        pan_min = pan_max = None
        if rd is not None:
            cmd = (rd / "command.txt").read_text() if (rd / "command.txt").exists() else ""
            m = re.search(r"--arm_filter=(\w+)", cmd)
            filt = m.group(1) if m else "미기록"
            if rd not in cache:
                pq = sorted(glob.glob(str(rd / "dataset/data/*/*.parquet")))
                cache[rd] = pd.concat([pd.read_parquet(p) for p in pq]) if pq else pd.DataFrame()
            df = cache[rd]
            d = df[df.episode_index == int(r["ds_ep"])]
            if len(d):
                pan = np.stack(d["observation.state"].values)[:, 0]
                pan_min, pan_max = round(float(pan.min()), 1), round(float(pan.max()), 1)
        out.append({"run": r["run"], "ds_ep": r["ds_ep"], "K": k, "angle": ang, "dist_K_cm": round(float(r["dist_K_cm"]), 2) if r.get("dist_K_cm") else "",
                    "cube_yaw": r.get("cube_yaw"), "arm_filter": filt, "first_close_T4": r.get("T4") or "no_close", "user_PF": r.get("user_PF"),
                    "pan_min": pan_min, "pan_max": pan_max, "run_dir": str(rd) if rd else ""})
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    cp, mp = S_DIR / "logs/c02_history.csv", S_DIR / "logs/c02_history.md"
    if cp.exists():
        cp, mp = S_DIR / f"logs/c02_history_{stamp}.csv", S_DIR / f"logs/c02_history_{stamp}.md"
    pd.DataFrame(out).to_csv(cp, index=False)
    lines = ["# 파일럿 조건의 d2 020000 과거 실물 기록 [기록 · 자동 계산]", "",
             f"출처: {REP}/summary_existing_20.csv · summary_r2_all_8.csv (시작 사진 판정 Known, 각도 = d2 규칙 분류), command.txt, dataset state. 생성 {stamp}.", "",
             "| run | ds_ep | K | 각도 | K 거리 cm | arm_filter | 첫 닫힘 T4 | 사용자 P/F | pan 최소 | pan 최대 |", "|---|---|---|---|---|---|---|---|---|---|"]
    for o in sorted(out, key=lambda x: (x["K"], x["angle"], x["arm_filter"] or "", x["run"], int(x["ds_ep"]))):
        lines.append(f"| {o['run'][:15]} | {o['ds_ep']} | {o['K']} | {o['angle']} | {o['dist_K_cm']} | {o['arm_filter']} | {o['first_close_T4']} | {o['user_PF']} | {o['pan_min']} | {o['pan_max']} |")
    lines += ["", "## 조건 × arm_filter 집계", "", "| K | 각도 | arm_filter | 판 | 첫 닫힘 grasp | empty | no_close · undetermined | 사용자 P | pan 최소 < −100 |", "|---|---|---|---|---|---|---|---|---|"]
    for (k, ang) in sorted(COND):
        for fl in ("false", "true"):
            g = [o for o in out if o["K"] == k and o["angle"] == ang and o["arm_filter"] == fl]
            lines.append(f"| {k} | {ang} | {fl} | {len(g)} | {sum(o['first_close_T4'] == 'grasp' for o in g)} | {sum(o['first_close_T4'] == 'empty' for o in g)} | "
                         f"{sum(o['first_close_T4'] in ('no_close', 'undetermined') for o in g)} | {sum(o['user_PF'] == 'P' for o in g)} | "
                         f"{sum(1 for o in g if o['pan_min'] is not None and o['pan_min'] < -100)} |")
    mp.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print("OUT", cp, mp)


if __name__ == "__main__":
    main()
