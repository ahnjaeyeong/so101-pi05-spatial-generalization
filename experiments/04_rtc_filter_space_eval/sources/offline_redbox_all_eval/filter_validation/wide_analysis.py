"""확대 검증: 새 ArmFilter(실제 코드) 를 T1/T2/T3 사람 시연 24편 + rollout 재생 명령에 걸어 비교. CPU, 읽기만.

⚠ 열린 루프 재생 — 상대 비교용. 추종·clamp 는 P0 서보 모델 v2 추정치.
필터: none | armf (arm_filter.ArmFilter, α 0.5, init=state: 각 소스 첫 틱의 녹화된 실제 상태 기준, 그리퍼 미적용)
빠른 동작: 필터 전 명령의 9프레임 이동평균 속도 > 2°/프레임(60°/s) 인 관절·프레임
사용: python wide_analysis.py
"""

import glob
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
P0 = Path.home() / "so101_runs/redbox_all/eval/p0_offline_replay"
sys.path.insert(0, str(Path.home() / "so101_runs/main/redbox_all/eval"))
from arm_filter import ArmFilter  # noqa: E402

spec = importlib.util.spec_from_file_location("p0a", P0 / "analyze_runs.py")
sys.argv = ["x", str(P0 / "runs_lat1.55")]  # analyze_runs 는 argv 경로의 상위 폴더에서 servo_model_v2.json 을 읽는다
p0a = importlib.util.module_from_spec(spec); spec.loader.exec_module(p0a)
KEYS = ["shoulder_pan.pos", "shoulder_lift.pos", "elbow_flex.pos", "wrist_flex.pos", "wrist_roll.pos", "gripper.pos"]
J = [k[:-4] for k in KEYS]
FAST = 2.0


def task_of(sn):
    if sn.startswith("rollout"): return "rollout(T1)"
    g = int(sn.split("_g")[1].split("_")[0]); return ["T1", "T1", "T2", "T2", "T3", "T3"][g]


def apply_armf(c, states_at_tick):
    f = ArmFilter(KEYS, init="state"); out = np.full_like(c, np.nan); vc = np.zeros((len(c), 5), bool)
    for t in range(len(c)):
        if np.isnan(c[t]).any(): continue
        out[t], info = f.step(c[t], states_at_tick[t]); vc[t] = info["vclip"]
    return out, vc


def fast_stats(raw, filt, vc):
    v = ~np.isnan(raw).any(1)
    r, fo = raw[v], filt[v]; vcv = vc[v]
    lr, lf = p0a.lowpass(r), p0a.lowpass(fo)
    sr = np.abs(np.diff(lr[:, :5], axis=0)); sf = np.abs(np.diff(lf[:, :5], axis=0))
    fast = sr > FAST
    dev = np.abs(fo[1:, :5] - r[1:, :5])
    return {"fast_frames": int(fast.sum()), "speed_ratio_fast": float(sf[fast].sum() / max(sr[fast].sum(), 1e-9)),
            "vclip_in_fast_pct": float(vcv[1:][fast].mean() * 100) if fast.any() else 0.0,
            "vclip_all_pct": float(vcv.mean() * 100), "dev_fast_p95": float(np.percentile(dev[fast], 95)) if fast.any() else 0.0,
            "dev_fast_max": float(dev[fast].max()) if fast.any() else 0.0}


rows, fastrows, keep = [], [], {}
for tag, d in [("lat1.55", HERE / "runs_wide_lat1.55"), ("spike", HERE / "runs_wide_spike")]:
    srcdata = {}
    for fs in glob.glob(str(d / "src_*.npz")):
        sn = Path(fs).stem[4:]; z = np.load(fs)
        srcdata[sn] = {"action": z["action"], "state": z["state"], "gt": sn.startswith("train")}
    for fz in sorted(glob.glob(str(d / "run_*.npz"))):
        name = Path(fz).stem[4:]
        meta = json.load(open(str(fz).replace(".npz", ".json")))
        run = p0a.load_run(fz)
        for sn, r in run.items():
            c0 = r["cmds"].astype(float); obs_t = r["obs_t"].astype(int); sw = list(r["switch"].astype(int))
            st = srcdata[sn]["state"][np.minimum(obs_t, len(srcdata[sn]["state"]) - 1)]
            c1, vc = apply_armf(c0, st)
            for filt, c in (("none", c0), ("armf", c1)):
                m, s = p0a.metrics(c, sw, obs_t, srcdata[sn], None if filt == "none" else c0)
                m.update(cfg=name, filter=filt, src=sn, task=task_of(sn), lat=tag, ticks=len(c), hold=meta["sources"][sn]["hold_or_starved"],
                         lat_ms=meta["sources"][sn]["lat_ms_median"])
                rows.append(m)
            fs_ = fast_stats(c0, c1, vc); fs_.update(cfg=name, src=sn, task=task_of(sn), lat=tag); fastrows.append(fs_)
            if sn.startswith("train_g2") or sn.startswith("rollout"):
                keep[f"{tag}|{name}|{sn}"] = (c0, c1, st)
        print("analyzed", tag, name, flush=True)
E = pd.DataFrame(rows); E.to_csv(HERE / "wide_metrics_by_source.csv", index=False)
F = pd.DataFrame(fastrows); F.to_csv(HERE / "wide_fast_motion.csv", index=False)
np.savez_compressed(HERE / "wide_keep.npz", **{f"{k}|{n}": v for k, (a, b, s) in keep.items() for n, v in (("raw", a), ("armf", b), ("state", s))})


def agg(g):
    w = g["ticks"].to_numpy()
    out = {"sources": len(g), "ticks": int(w.sum()), "boundary_max": g.boundary_max.max(), "boundary_gt8": int(g.boundary_gt8.sum()),
           "anyframe_gt8": int(g.anyframe_gt8.sum()), "hold_pct": 100 * g.hold.sum() / w.sum()}
    for k in ["noise_arm", "acc_rms_arm", "track_mean_arm", "clamp_pct", "lag_frames", "lat_ms"] + [f"vel_p99|{j}" for j in J]:
        if k in g and g[k].notna().any():
            out[k] = float(np.average(g[k].fillna(0), weights=w)) if k != "lag_frames" else float(g[k].median())
    out.update(grasp_err=np.nan, n_grasp=0, grip_abs_dt=np.nan, grip_miss=0)  # 모든 그룹이 같은 열을 갖게
    gt = g[g.n_grasp > 0] if "n_grasp" in g else g.iloc[0:0]
    if len(gt):
        out["grasp_err"] = float(np.average(gt.grasp_err, weights=gt.n_grasp)); out["n_grasp"] = int(gt.n_grasp.sum())
        out["grip_abs_dt"] = float(np.average(gt.grip_abs_dt.fillna(0), weights=gt.n_grasp)); out["grip_miss"] = int(gt.grip_miss.sum())
    return pd.Series(out)


T = pd.DataFrame([dict(lat=k[0], cfg=k[1], filter=k[2], task=k[3], **agg(g).to_dict()) for k, g in E.groupby(["lat", "cfg", "filter", "task"])])
T.to_csv(HERE / "wide_table.csv", index=False)
FT = F.groupby(["lat", "cfg", "task"]).agg(fast_frames=("fast_frames", "sum"), speed_ratio_fast=("speed_ratio_fast", "mean"),
                                           vclip_in_fast_pct=("vclip_in_fast_pct", "mean"), vclip_all_pct=("vclip_all_pct", "mean"),
                                           dev_fast_p95=("dev_fast_p95", "mean"), dev_fast_max=("dev_fast_max", "max")).reset_index()
FT.to_csv(HERE / "wide_fast_table.csv", index=False)

# 사람 조작 384편에 같은 필터 → 정상 사람 속도 동작이 얼마나 바뀌나
hum = []
for fp in sorted(glob.glob(str(Path.home() / "so101_runs/main/redbox_all/dataset/data/*/*.parquet"))):
    dd = pd.read_parquet(fp, columns=["episode_index", "frame_index", "action", "observation.state"]).sort_values(["episode_index", "frame_index"])
    for e, gg in dd.groupby("episode_index"):
        A = np.stack(gg["action"]).astype(float); S = np.stack(gg["observation.state"]).astype(float)
        out, vc = apply_armf(A, S)
        fs_ = fast_stats(A, out, vc); fs_.update(episode=int(e), task=["T1", "T1", "T2", "T2", "T3", "T3"][int(e) // 64])
        fs_["noise_raw"] = float((A - p0a.lowpass(A))[4:-4, :5].std(0).mean()); fs_["noise_filt"] = float((out - p0a.lowpass(out))[4:-4, :5].std(0).mean())
        hum.append(fs_)
H = pd.DataFrame(hum); H.to_csv(HERE / "human_filter_effect.csv", index=False)
HT = H.groupby("task").agg(episodes=("episode", "count"), fast_frames=("fast_frames", "sum"), speed_ratio_fast=("speed_ratio_fast", "mean"),
                           vclip_in_fast_pct=("vclip_in_fast_pct", "mean"), vclip_all_pct=("vclip_all_pct", "mean"),
                           dev_fast_p95=("dev_fast_p95", "mean"), dev_fast_max=("dev_fast_max", "max"), noise_raw=("noise_raw", "mean"),
                           noise_filt=("noise_filt", "mean")).reset_index()
HT.to_csv(HERE / "human_filter_table.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
print(T[T.lat == "lat1.55"][["cfg", "filter", "task", "sources", "boundary_max", "boundary_gt8", "anyframe_gt8", "noise_arm", "lag_frames", "grasp_err", "grip_abs_dt", "grip_miss", "track_mean_arm", "clamp_pct", "hold_pct"]].round(2).to_string(index=False))
print(FT.round(3).to_string(index=False)); print(HT.round(3).to_string(index=False))
