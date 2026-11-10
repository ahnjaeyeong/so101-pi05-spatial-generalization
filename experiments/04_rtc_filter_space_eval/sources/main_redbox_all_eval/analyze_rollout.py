"""rollout 녹화(dataset) + DEBUG 로그로 흔들림을 숫자로 본다. 읽기만 함.

실행: PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python analyze_rollout.py <run_dir> [<run_dir> ...]
  run_dir = run_rollout.sh 가 만든 폴더 (dataset/, debug.log, console.log)
  특수값 "reference" = 학습 데이터(redbox_all/dataset, 사람 조작) — 비교 기준
결과: <run_dir>/analysis.json, analysis.npz (그래프는 plot_rollout.py)

지표 (관절별, °; 그리퍼 0–100)
- hf_rms   : 0.3초(9프레임) 이동평균을 뺀 고주파 성분의 RMS — "흔들흔들"의 크기
- reversals: 초당 속도 부호 바뀜 횟수 (|속도| > 0.3°/프레임 인 구간만) — 흔들림의 잦기
- d2_rms   : 프레임 간 가속(2차 차분) RMS
- track    : |action - state| 평균·p95, 8° 넘는 프레임 비율 (max_relative_target=8 이 걸렸을 가능성)
- period   : action 2차 차분 크기의 자기상관이 가장 큰 주기(프레임) — chunk 전환 주기와 겹치는지
"""

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SESSION = Path.home() / "so101_runs/main/redbox_all"
FPS = 30
WIN = 9
CLAMP = 8.0


def load(root: Path) -> pd.DataFrame:
    files = sorted((root / "data").rglob("*.parquet"))
    return pd.concat([pd.read_parquet(f, columns=["episode_index", "frame_index", "action", "observation.state"]) for f in files])


def hf(x):
    k = np.ones(WIN) / WIN
    pad = np.pad(x, ((WIN // 2, WIN // 2), (0, 0)), mode="edge")
    smooth = np.stack([np.convolve(pad[:, j], k, mode="valid") for j in range(x.shape[1])], 1)
    return x - smooth


def reversals_per_s(x):
    v = np.diff(x, axis=0)
    out = []
    for j in range(x.shape[1]):
        s = np.sign(v[:, j][np.abs(v[:, j]) > 0.3])
        out.append(float((np.diff(s) != 0).sum()) / (len(x) / FPS))
    return out


def period(x):
    a = np.abs(np.diff(x[:, :5], n=2, axis=0)).max(1)
    a = a - a.mean()
    if len(a) < 130 or not a.any():
        return None
    ac = np.correlate(a, a, mode="full")[len(a) - 1:] / (a.var() * len(a))
    lag = int(np.argmax(ac[5:61]) + 5)
    return {"lag_frames": lag, "autocorr": round(float(ac[lag]), 3)}


def metrics(a, s):
    r = lambda v: [round(float(t), 2) for t in v]
    track = np.abs(a - s)
    return {
        "frames": int(len(a)),
        "action_hf_rms": r(np.sqrt((hf(a) ** 2).mean(0))),
        "state_hf_rms": r(np.sqrt((hf(s) ** 2).mean(0))),
        "action_reversals_per_s": r(reversals_per_s(a)),
        "state_reversals_per_s": r(reversals_per_s(s)),
        "action_d2_rms": r(np.sqrt((np.diff(a, n=2, axis=0) ** 2).mean(0))),
        "track_mean": r(track.mean(0)),
        "track_p95": r(np.percentile(track, 95, axis=0)),
        "track_over8_pct": r((track > CLAMP).mean(0) * 100),
        "action_step_max": r(np.abs(np.diff(a, axis=0)).max(0)),
        "period": period(a),
    }


def parse_debug(log: Path):
    if not log.exists():
        return None
    lat, q, clamps, starved = [], [], 0, []
    for line in log.read_text(errors="replace").splitlines():
        m = re.search(r"RTC inference latency=([\d.]+)s, queue=(\d+)", line)
        if m:
            lat.append(float(m.group(1)))
            q.append(int(m.group(2)))
        if "had to be clamped" in line:
            clamps += 1
    for line in (log.parent / "console.log").read_text(errors="replace").splitlines() if (log.parent / "console.log").exists() else []:
        m = re.search(r"inference engine starved\): (\d+)", line)
        if m:
            starved.append(int(m.group(1)))
    out = {"clamp_warnings": clamps, "starved_ticks_per_run": starved}
    if lat:
        lat = np.array(lat[2:] if len(lat) > 4 else lat)  # 첫 2회(콜드 스타트) 제외
        out |= {"rtc_inferences": len(q), "latency_ms_mean": round(float(lat.mean() * 1e3), 1),
                "latency_ms_max": round(float(lat.max() * 1e3), 1),
                "delay_ticks_max": int(np.ceil(lat.max() * FPS)), "queue_after_merge_min": int(min(q))}
    return out


def main():
    for arg in sys.argv[1:]:
        if arg == "reference":
            root, out_dir, dbg = SESSION / "dataset", SESSION / "eval/reference_teleop", None
            out_dir.mkdir(exist_ok=True)
        else:
            out_dir = Path(arg).resolve()
            root, dbg = out_dir / "dataset", out_dir / "debug.log"
        df = load(root)
        res, arrays = {"source": str(root), "joints": ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"], "episodes": {}}, {}
        for ep, g in df.groupby("episode_index"):
            g = g.sort_values("frame_index")
            a, s = np.stack(g["action"].to_numpy()), np.stack(g["observation.state"].to_numpy())
            res["episodes"][int(ep)] = metrics(a, s)
            arrays[f"ep{int(ep)}_action"], arrays[f"ep{int(ep)}_state"] = a, s
        allm = [m for m in res["episodes"].values()]
        res["mean_over_episodes"] = {k: np.round(np.mean([m[k] for m in allm], 0), 2).tolist()
                                     for k in allm[0] if k not in ("frames", "period")}
        if dbg is not None:
            res["debug_log"] = parse_debug(dbg)
        (out_dir / "analysis.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
        np.savez(out_dir / "analysis.npz", **arrays)
        mm = res["mean_over_episodes"]
        print(f"== {out_dir.name}: {len(allm)} ep")
        for k in ("action_hf_rms", "state_hf_rms", "action_reversals_per_s", "track_over8_pct"):
            print(f"  {k:24s} {mm[k]}")
        print("  period", [m["period"] for m in allm][:4], "| debug", res.get("debug_log"))


if __name__ == "__main__":
    main()
