"""p15 arm_filter 끔의 오프라인 명령 비교 (읽기만, CPU). **열린 고리 계산 — 필터를 끈 정책의 실제 폐루프 행동이 아니다.**

A. 파일럿 12 판 (필터 켬, 저장된 시도): 같은 틱의 queue 출력 raw (= 필터를 껐다면 보냈을 clamp 전 명령) vs 필터 out (실제 clamp 전 명령)
   관절별: |out − raw| 분포, 틱당 명령 변화 |Δ| (raw vs out), 속도 제한 · EMA 재설정 작동 틱,
           8° clamp: |raw − present| > 8 (필터 껐다면 clamp 가 걸렸을 틱, present 는 필터 켠 폐루프의 실제 값) vs 실제 |out − present| > 8,
           FK TCP (ac.tcp): tcp(raw) − tcp(out) 거리, 닫힘 시작 전 1 s 창 따로
   그리퍼는 필터가 건드리지 않는다 (확인).
B. 실물 기록 비교 (실측): 10-26 try3 (필터 끔, d2 020000, 2 판) vs try3_filt (필터 켬, 3 판) vs 10-29 파일럿 (필터 켬, 12 판)
   보낸 Goal 의 틱당 |Δ| p99 · 최대, |sent − state| p95, clamp 틱 비율 (관절별).
출력: pilot/p15_filter_offline_joint.csv, p15_filter_offline_episode.csv, p15_real_compare.csv, p15_summary.json
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python p15_filter_off_offline.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import cube_coords as CC  # noqa: E402

ac = CC.ac
D2 = CC.D2
OUT = Path(__import__("os").environ.get("PILOT_DIR", D2 / "pan_inference_diagnostic/pilot"))  # 다른 묶음 (예: filter_ab) 은 PILOT_DIR 로
TAB = D2 / "pan_inference_diagnostic/tables"
ROLL = D2 / "eval/rollouts"
J = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
CLAMP = 8.0


def main():
    P = pd.read_csv(OUT / "pilot_episodes.csv")
    G = pd.read_csv(OUT / "p14_grasp_pilot.csv").set_index("label")
    acc = {j: {k: [] for k in ("d_or", "step_raw", "step_out", "raw_pres", "out_pres")} for j in J}
    ep_rows, tcp_all, tcp_pre = [], [], []
    for _, p in P.iterrows():
        FL = pd.read_csv(ROLL / p.run / "filter_log.csv", dtype={"vclip_mask": str, "ema_reset_mask": str})
        f = FL[(FL.event == "cmd") & (FL.episode == p.episode)].sort_values("tick").reset_index(drop=True)
        TK = pd.read_csv(ROLL / p.run / "diag/ticks.csv")
        t = TK[(TK.episode == p.episode) & (TK.pop_chunk >= 0)].sort_values("tick").reset_index(drop=True)
        raw = f[[f"raw_{j}" for j in J]].values.astype(float)
        out = f[[f"out_{j}" for j in J]].values.astype(float)
        pres = t[[f"present_{j}" for j in J]].values.astype(float)
        r = dict(label=p.label, n_ticks=len(f), vclip_ticks=int((f.vclip_mask.fillna("").str.contains("1")).sum()),
                 ema_reset_ticks=int((f.ema_reset_mask.fillna("").str.contains("1")).sum()))
        for k, j in enumerate(J):
            d_or = np.abs(out[:, k] - raw[:, k])
            sr, so = np.abs(np.diff(raw[:, k])), np.abs(np.diff(out[:, k]))
            rp, op = np.abs(raw[:, k] - pres[:, k]), np.abs(out[:, k] - pres[:, k])
            for nm, v in (("d_or", d_or), ("step_raw", sr), ("step_out", so), ("raw_pres", rp), ("out_pres", op)):
                acc[j][nm].append(v)
            r[f"{j}_d_or_p95"] = float(np.percentile(d_or, 95))
            r[f"{j}_clamp_if_off"] = int((rp > CLAMP).sum())
            r[f"{j}_clamp_on"] = int((op > CLAMP).sum())
        tr, to = ac.tcp(raw[:, :5]), ac.tcp(out[:, :5])
        dd = np.linalg.norm(tr - to, axis=1)
        tcp_all.append(dd)
        r.update(tcp_diff_p50=float(np.median(dd)), tcp_diff_p95=float(np.percentile(dd, 95)), tcp_diff_max=float(dd.max()))
        if p.label in G.index and not pd.isna(G.loc[p.label, "on"]):
            on = int(G.loc[p.label, "on"])
            w = dd[max(0, on - 30):on]
            tcp_pre.append(w)
            r.update(tcp_diff_pre_close_p50=float(np.median(w)), tcp_diff_pre_close_max=float(w.max()))
        ep_rows.append(r)
    EP = pd.DataFrame(ep_rows)
    EP.to_csv(OUT / "p15_filter_offline_episode.csv", index=False)
    jr = []
    for j in J:
        c = {k: np.concatenate(v) for k, v in acc[j].items()}
        jr.append(dict(joint=j, d_or_p50=np.median(c["d_or"]), d_or_p95=np.percentile(c["d_or"], 95), d_or_max=c["d_or"].max(),
                       step_raw_p99=np.percentile(c["step_raw"], 99), step_raw_max=c["step_raw"].max(),
                       step_out_p99=np.percentile(c["step_out"], 99), step_out_max=c["step_out"].max(),
                       clamp_if_off_frac=float((c["raw_pres"] > CLAMP).mean()), clamp_on_frac=float((c["out_pres"] > CLAMP).mean()),
                       raw_pres_max=c["raw_pres"].max(), out_pres_max=c["out_pres"].max()))
    JR = pd.DataFrame(jr)
    JR.to_csv(OUT / "p15_filter_offline_joint.csv", index=False)
    # B 실물 기록 비교
    rows = []
    T1 = pd.read_parquet(TAB / "p01_ticks.parquet")
    for (run, e), g in T1.groupby(["run", "ep"]):
        rows.append(("try3 (필터 끔, 10-26)" if not run.endswith("filt") else "try3_filt (필터 켬, 10-26)", f"{run[16:]}/ep{e}",
                     g[[f"sent_{j}" for j in J]].values.astype(float), g[[f"state_{j}" for j in J]].values.astype(float),
                     g[[f"clamp_{j}" for j in J]].values.astype(bool) if f"clamp_{J[0]}" in g else None))
    for _, p in P.iterrows():
        TK = pd.read_csv(ROLL / p.run / "diag/ticks.csv")
        t = TK[(TK.episode == p.episode) & (TK.pop_chunk >= 0)].sort_values("tick")
        se = t[[f"sent_{j}" for j in J]].values.astype(float)
        gi = t[[f"goal_in_{j}" for j in J]].values.astype(float)
        rows.append(("pilot (필터 켬, 10-29)", p.label, se, t[[f"present_{j}" for j in J]].values.astype(float), np.abs(se - gi) > 1e-4))
    rc = []
    for grp in dict.fromkeys(r[0] for r in rows):
        sel = [r for r in rows if r[0] == grp]
        for k, j in enumerate(J):
            st = np.concatenate([np.abs(np.diff(r[2][:, k])) for r in sel])
            sp = np.concatenate([np.abs(r[2][:, k] - r[3][:, k]) for r in sel])
            cl = np.concatenate([r[4][:, k] for r in sel]) if all(r[4] is not None for r in sel) else None
            rc.append(dict(group=grp, n_eps=len(sel), joint=j, sent_step_p99=np.percentile(st, 99), sent_step_max=st.max(),
                           sent_minus_state_p95=np.percentile(sp, 95), clamp_frac=None if cl is None else float(cl.mean())))
    RC = pd.DataFrame(rc)
    RC.to_csv(OUT / "p15_real_compare.csv", index=False)
    ta, tp = np.concatenate(tcp_all), np.concatenate(tcp_pre)
    S = {"note": "열린 고리: 필터 켠 폐루프에서 기록된 raw 를 필터 없이 보냈다면의 명령. present 는 필터 켠 실제 값. 실물 정확도 · 성공률 향상을 뜻하지 않음.",
         "tcp_diff_cm_all": {"p50": float(np.median(ta)), "p95": float(np.percentile(ta, 95)), "max": float(ta.max())},
         "tcp_diff_cm_pre_close_1s": {"p50": float(np.median(tp)), "p95": float(np.percentile(tp, 95)), "max": float(tp.max())},
         "vclip_ticks_total": int(EP.vclip_ticks.sum()), "ema_reset_ticks_total": int(EP.ema_reset_ticks.sum()), "ticks_total": int(EP.n_ticks.sum())}
    json.dump(S, open(OUT / "p15_summary.json", "w"), indent=1, ensure_ascii=False)
    pd.set_option("display.width", 250, "display.max_columns", 40)
    print(json.dumps(S, indent=1, ensure_ascii=False))
    print(JR.round(3).to_string(index=False))
    print(EP[["label", "n_ticks", "vclip_ticks", "ema_reset_ticks", "tcp_diff_p50", "tcp_diff_p95", "tcp_diff_max", "tcp_diff_pre_close_p50",
              "tcp_diff_pre_close_max"] + [f"{j}_clamp_if_off" for j in J[:5]] + [f"{j}_clamp_on" for j in J[:5]]].round(2).to_string(index=False))
    print(RC.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
