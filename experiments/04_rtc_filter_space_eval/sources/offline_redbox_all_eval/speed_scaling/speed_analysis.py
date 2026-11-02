"""실행 속도 100/80/60% × 그리퍼 동기화(sync / arm-only / gate) 비교. CPU, 읽기만.

⚠ 열린 루프 '시간축 보정' 재생: 관측을 s 배속으로 진행시킨 근사. 실제 팔 상태는 P0 서보 모델 v2 로 시뮬레이션 (8° clamp 포함).
   필터 = 실제 arm_filter.ArmFilter (init=state). 그리퍼는 필터 없음.
그리퍼 방식
  sync     : 팔·그리퍼 같은 배율 (시뮬레이터 출력 그대로)
  armonly  : 팔만 배율, 그리퍼는 원래 시간 (g[k] = sync 그리퍼[round(k/s)])
  gate     : sync + 닫힘 대기 — 그리퍼 명령이 닫히는 쪽(직전 출력보다 작고 15 미만)인데 시뮬레이션 팔 오차
             max(|cmd−state|, lift·elbow·wrist_flex) > GATE_ERR 이면 그리퍼를 직전 값에 유지 (닫힘 이벤트마다 최대 GATE_MAX 틱)
지표
  arm_err_close   : 그리퍼가 닫히는 틱(출력 그리퍼 <8)의 시뮬레이션 팔 오차 (lift/elbow 평균) — 팔이 도착했나
  premature       : 닫힐 때 lift 또는 elbow 오차 > 8° 인 닫힘 비율
  pose_vs_human   : (사람 시연) 닫힐 때 시뮬레이션 팔 자세 vs 사람이 닫을 때의 실제 팔(follower) 자세, 팔 5관절 평균 차
  grip_dt_obs     : (사람 시연) 닫힘 시점 차이를 녹화 시간(프레임)으로 — 양수 = 사람보다 늦게 닫음
  time_to_close_s : 첫 닫힘까지 실제 시간(틱/30)
"""

import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
P0 = Path.home() / "so101_runs/redbox_all/eval/p0_offline_replay"
sys.path.insert(0, str(Path.home() / "so101_runs/main/redbox_all/eval"))
from arm_filter import ArmFilter  # noqa: E402

SERVO = json.load(open(P0 / "servo_model_v2.json"))
SV = [SERVO[k] for k in ["pan", "lift", "elbow", "wflex", "wroll", "grip"]]
KEYS = ["shoulder_pan.pos", "shoulder_lift.pos", "elbow_flex.pos", "wrist_flex.pos", "wrist_roll.pos", "gripper.pos"]
GATE_ERR, GATE_MAX, LIM = 4.0, 30, 8.0
K9 = np.ones(9) / 9


def servo_step(s_hist, c_tgt, t, j):
    m = SV[j]; td = max(t - m["d"], 0)
    tgt = c_tgt if not np.isnan(c_tgt) else s_hist[td, j]
    sent = s_hist[td, j] + np.clip(tgt - s_hist[td, j], -LIM, LIM)
    e = sent - s_hist[t, j]
    return s_hist[t, j] + np.clip((m["kp"] if e > 0 else m["kn"]) * e, -m["vmax"], m["vmax"])


def simulate(c, s0, gate=False):
    """명령 c 로 서보 시뮬레이션. gate=True 면 그리퍼 닫힘을 팔 오차로 지연. 반환 (보낸 명령, 상태, 대기 틱 수)."""
    n = len(c); s = np.zeros((n, 6)); s[0] = s0; out = c.copy(); held = 0; hold_run = 0
    for t in range(n):
        if gate and t > 0 and not np.isnan(c[t, 5]):
            err = np.nanmax(np.abs(out[t - 1, 1:4] - s[t, 1:4])) if not np.isnan(out[t - 1, 1:4]).any() else 0.0
            closing = c[t, 5] < out[t - 1, 5] - 1e-6 and c[t, 5] < 15
            if closing and err > GATE_ERR and hold_run < GATE_MAX:
                out[t, 5] = out[t - 1, 5]; held += 1; hold_run += 1
            elif not closing:
                hold_run = 0
        if t + 1 < n:
            for j in range(6):
                s[t + 1, j] = servo_step(s, out[t, j], t, j)
    return out, s, held


def closes(g):
    ev, st = [], 0
    for t in range(len(g)):
        if np.isnan(g[t]): continue
        if st == 0 and g[t] > 15: st = 1
        elif st == 1 and g[t] < 8: ev.append(t); st = 0
    return ev


def lowpass(x):
    return np.stack([np.convolve(np.pad(x[:, j], 4, mode="edge"), K9, "valid") for j in range(x.shape[1])], 1)


def load_run(fz):
    z = np.load(fz, allow_pickle=True)
    return {sn: {k.split("|")[1]: z[k] for k in z.files if k.startswith(sn + "|")} for sn in sorted({k.split("|")[0] for k in z.files})}


rows, keep = [], {}
src = {Path(f).stem[4:]: np.load(f) for f in glob.glob(str(HERE / "runs/src_*.npz"))}
for fz in sorted(glob.glob(str(HERE / "runs/run_*.npz"))):
    name = Path(fz).stem[4:]
    meta = json.load(open(fz.replace(".npz", ".json")))
    spd = meta["config"].get("speed", 1.0)
    for sn, r in load_run(fz).items():
        c_raw = r["cmds"].astype(float); obs_t = r["obs_t"].astype(int); S_rec = src[sn]["state"]; A_gt = src[sn]["action"]
        first = int(np.argmax(~np.isnan(c_raw).any(1)))
        st_at = S_rec[np.minimum(obs_t, len(S_rec) - 1)]
        f = ArmFilter(KEYS, init="state"); c = np.full_like(c_raw, np.nan)
        for t in range(len(c)):
            if not np.isnan(c_raw[t]).any(): c[t] = f.step(c_raw[t], st_at[t])[0]
        c[:first] = st_at[first]  # 첫 명령 전에는 제자리
        modes = {"sync": c}
        am = c.copy(); idx = np.minimum(np.round(np.arange(len(c)) / spd).astype(int), len(c) - 1); am[:, 5] = c[idx, 5]
        modes["armonly"] = am
        for mode, cm in list(modes.items()) + [("gate", c)]:
            out, s, held = simulate(cm, st_at[first], gate=(mode == "gate"))
            ev = closes(out[:, 5])
            m = dict(cfg=name, speed=spd, mode=mode, src=sn, task="rollout" if sn.startswith("rollout") else ["T1", "T1", "T2", "T2", "T3", "T3"][int(sn.split("_g")[1][0])],
                     ticks=len(out), n_close=len(ev), gate_hold_ticks=held)
            e_close = [np.abs(out[k, 1:3] - s[k, 1:3]).mean() for k in ev]
            m["arm_err_close"] = float(np.mean(e_close)) if ev else np.nan
            m["premature"] = float(np.mean([(np.abs(out[k, 1:3] - s[k, 1:3]) > 8).any() for k in ev])) if ev else np.nan
            m["arm_speed_close"] = float(np.mean([np.abs(s[k, 1:3] - s[k - 3, 1:3]).max() / 3 * 30 for k in ev if k >= 3])) if ev else np.nan
            m["time_to_close_s"] = ev[0] / 30 if ev else np.nan
            m["clamp_pct"] = float(((np.abs(out - s) > LIM).any(1))[first:].mean() * 100)
            m["track_lift_elbow"] = float(np.abs(out[first:, 1:3] - s[first:, 1:3]).mean())
            lp = lowpass(out[first:]); m["noise"] = float((out[first:] - lp)[4:-4, :5].std(0).mean())
            m["jump_gt8"] = int((np.abs(np.diff(out[first:, :5], axis=0)).max(1) > 8).sum())
            if not sn.startswith("rollout"):
                gt = closes(A_gt[:, 5]); pe, dt = [], []
                for tc in gt:
                    ks = np.where(obs_t >= tc)[0]
                    if len(ks) == 0: continue
                    k0 = int(ks[0])
                    near = [k for k in ev if abs(obs_t[k] - tc) <= 60]
                    if near:
                        kc = min(near, key=lambda k: abs(obs_t[k] - tc))
                        dt.append(obs_t[kc] - tc)
                        pe.append(np.abs(s[kc, :5] - S_rec[tc, :5]).mean())
                m["pose_vs_human"] = float(np.mean(pe)) if pe else np.nan
                m["grip_dt_obs"] = float(np.mean(dt)) if dt else np.nan
                m["grip_absdt_obs"] = float(np.mean(np.abs(dt))) if dt else np.nan
                m["matched"] = len(pe); m["gt_closes"] = len(gt)
            rows.append(m)
            if sn.startswith("rollout"):
                keep[f"{name}|{mode}"] = np.concatenate([out, s], 1)
    print("analyzed", name, flush=True)

D = pd.DataFrame(rows); D.to_csv(HERE / "speed_by_source.csv", index=False)
np.savez_compressed(HERE / "speed_keep.npz", **keep)


def agg(g):
    w = g.ticks.to_numpy()
    o = {"sources": len(g), "ticks": int(w.sum()), "closes": int(g.n_close.sum()), "gate_hold_ticks": int(g.gate_hold_ticks.sum())}
    for k in ["arm_err_close", "premature", "arm_speed_close", "time_to_close_s", "clamp_pct", "track_lift_elbow", "noise", "pose_vs_human", "grip_dt_obs", "grip_absdt_obs"]:
        if k in g and g[k].notna().any():
            v = g[k].dropna(); o[k] = float(np.average(v, weights=g.loc[v.index, "n_close"].clip(lower=1) if k in ("arm_err_close", "premature", "arm_speed_close", "pose_vs_human", "grip_dt_obs", "grip_absdt_obs") else g.loc[v.index, "ticks"]))
    o["jump_gt8"] = int(g.jump_gt8.sum())
    return o


T = pd.DataFrame([dict(cfg=k[0], speed=k[1], mode=k[2], part=k[3], **agg(g)) for k, g in D.assign(part=np.where(D.task == "rollout", "rollout", "human")).groupby(["cfg", "speed", "mode", "part"])])
T.to_csv(HERE / "speed_table.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(T.round(2).to_string(index=False))
