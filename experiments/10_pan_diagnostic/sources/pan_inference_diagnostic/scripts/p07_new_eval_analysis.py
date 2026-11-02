"""p07 계측 켠 실물 평가 (ROLLOUT_DIAG=1) 실행 1 개 분석 (읽기만, CPU). 로봇 연결 없음.

입력 <RUN> = eval/rollouts/<시각>_..._pan_diag
  필수: diag/chunks.jsonl, diag/chunks/*.npz, diag/ticks.csv, filter_log.csv
  있으면: start_images/, results.csv, console.log ([eval_ui] START/SAVED/DISCARD 순서), diag/replay/ (p05 결과 → RTC 끔 반사실)
출력 <RUN>/analysis_pan/: chunks.csv, ticks_chain.csv, episodes.csv, summary.json
값의 종류 (열 이름 접두):
  logged (접두 없음) = 실물 기록. chunk 값 = RTC 안내 뒤 Action Expert 출력 (unnormalize 뒤, 필터 전). 판 첫 chunk 는 prefix 가 없어 안내 없는 출력과 같다.
  off_ = p05 오프라인 반사실 (같은 관측 PNG · state · noise, RTC 안내 없음). 실물에 적용한 적 없음.
  est  = 좌표 · pe: 판 시작 front 사진 (팔 움직이기 전) → cube_coords.estimate (기존 H · 검출 · ac 베이스 재사용).
         정책 행동 · 파지 위치는 정답에 쓰지 않는다. coord_status:
           valid_near_K (K 에서 3 cm 이내, 좌표 정확도 검증 범위) · valid_off_K (pe 저장, 좌표 정확도 미검증)
           invalid_detection · invalid_calibration → pe=None: pe 가 필요한 지표 (need · gain · 방향 맞음 · 목표 오차) 만 비고,
           raw chunk · RTC · 서보 지표는 그대로 낸다.
         Pan 오차의 두 불확실성을 따로 낸다: pe_sigma_coord_deg (좌표 추정 — K 검증값, off-K 는 참고치) ·
         pe_sigma_grasp_deg (사람 첫 파지 pan 의 pe 둘레 산포, CV SD).
부호: 'sg' 열이 붙은 양은 need 방향 (pe − 판 시작 pan) 부호를 곱한 값 (양수 = 목표 쪽).
판 대응: diag 의 episode 번호 (rollout_logged 판 계수기, 판 시작마다 +1) 를 console.log 의 START 순서에 맞추고,
  DISCARD 된 시도는 discarded=True 로 표시한다 (start_images · dataset 판 번호 = START 의 번호).
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python p07_new_eval_analysis.py <RUN>
"""
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

D2 = Path.home() / "so101_runs/main_k8/d2"
sys.path.insert(0, str(D2 / "data_coverage_audit/scripts"))
J = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
FPS = 30


def start_coords(p, train_xy):
    """start_images/ep###_front.png (판 시작 순간, 팔 움직이기 전) → cube_coords.estimate (좌표 · pe · 불확실성 · 상태)."""
    import cv2
    import cube_coords as CC
    img = cv2.cvtColor(cv2.imread(str(p)), cv2.COLOR_BGR2RGB)
    return CC.estimate(img, train_xy=train_xy, known=CC.ac.KNOWN)


def box_shift(p):
    """상자 사각형 (check_dataset.find_box) 의 학습 중앙값 대비 이동 (px) — 카메라가 움직였는지."""
    import cv2
    sys.path.insert(0, str(Path.home() / "so101_boxpick/scripts"))
    import check_dataset as cd
    import cube_coords as CC
    V = CC.validation()
    b = cd.find_box(cv2.imread(str(p)))
    if b is None or not V:
        return None
    m = V["box_rect_px"]["train_median"]
    return float(max(abs(b[0] - m["box_x0"]), abs(b[2] - m["box_x1"])))  # 좌우 변만 (위 변 y0 는 학습에서도 SD 3.6 px, 10-26 한 판 11 px 로 흔들림)


def attempts(run):
    """console.log 의 [eval_ui] START n / SAVED n / DISCARD n 순서 → 시도 목록 [(ds_ep, 'saved'|'discarded'|'?')]."""
    p = run / "console.log"
    if not p.exists():
        return []
    txt = re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", p.read_text(errors="replace"))
    out = []
    for m in re.finditer(r"\[eval_ui\] (START|SAVED|DISCARD) (\d+)", txt):
        kind, n = m.group(1), int(m.group(2))
        if kind == "START":
            out.append([n, "?"])
        elif out and out[-1][0] == n and out[-1][1] == "?":
            out[-1][1] = "saved" if kind == "SAVED" else "discarded"
    return [tuple(x) for x in out]


def best_lag(sent, pres):
    v = np.abs(np.gradient(sent))
    best, bv = 0, 1e9
    for L in range(0, 11):
        m = v[: len(sent) - L] > 0.2
        if m.sum() > 10:
            e = np.mean(np.abs(pres[L:] - sent[: len(sent) - L])[m])
            if e < bv:
                best, bv = L, e
    return best, bv


def main():
    import ac
    run = Path(sys.argv[1]).expanduser().resolve()
    dg = run / "diag"
    out = run / "analysis_pan"
    out.mkdir(exist_ok=True)
    metas = [json.loads(x) for x in (dg / "chunks.jsonl").read_text().splitlines()]
    TK = pd.read_csv(dg / "ticks.csv")
    FL = pd.read_csv(run / "filter_log.csv", dtype={"vclip_mask": str, "ema_reset_mask": str})
    FL = FL[FL.event == "cmd"]
    RP = pd.read_csv(dg / "replay/replay.csv") if (dg / "replay/replay.csv").exists() else None
    RZ = np.load(dg / "replay/replay.npz") if (dg / "replay/replay.npz").exists() else None
    res = pd.read_csv(run / "results.csv", encoding="utf-8-sig") if (run / "results.csv").exists() else None
    proc = {m["chunk_id"]: np.load(dg / "chunks" / f"c{m['chunk_id']:05d}.npz")["processed"] for m in metas}

    # ---- 판 대응
    eps = sorted({m["episode"] for m in metas})
    att = attempts(run)
    warn = []
    if len(att) == len(eps):
        amap = {e: a for e, a in zip(eps, att)}
    else:
        warn.append(f"START {len(att)} 개 vs diag 판 {len(eps)} 개 — 순서대로 0,1,2… 로 가정")
        amap = {e: (k, "?") for k, e in enumerate(eps)}
    train_xy = pd.read_csv(D2 / "data_coverage_audit/tables/a01_cube_table.csv")[["cube_x", "cube_y"]].values
    sys.path.insert(0, str(Path(__file__).parent))
    epinfo = {}
    for e in eps:
        ds_ep, status = amap[e]
        info = {"episode": e, "ds_ep": ds_ep, "attempt": status}
        p = run / "start_images" / f"ep{ds_ep:03d}_front.png"
        if p.exists() and status != "discarded":
            c = start_coords(p, train_xy)
            info.update({k: v for k, v in c.items() if v is not None or k == "pe"})
            info["box_shift_px"] = box_shift(p)
            if info["box_shift_px"] is not None and info["box_shift_px"] > 6:  # 학습 SD x0 1.3 · x1 0.3 px, 10-26 평가 ≤ 3 px
                info.update(pe=None, coord_status="invalid_calibration", coord_accuracy_validated=False,
                            coord_status_reason=(info.get("coord_status_reason") or "") + f"; 상자 사각형이 학습 때보다 {info['box_shift_px']:.0f} px 이동 (카메라 이동 의심)")
        else:
            info.update(pe=None, coord_status="invalid_detection", coord_accuracy_validated=False, coord_status_reason="시작 사진 없음 또는 버린 시도")
        if res is not None and status != "discarded":
            r = res[res.ep == ds_ep]
            if len(r):
                info.update(verdict=r.iloc[0].get("verdict"), memo=r.iloc[0].get("memo"))
        f = FL[FL.episode == e].sort_values("tick")
        if len(f):
            s0 = float(f.state_shoulder_pan.iloc[0])
            info["s0"] = s0
            arm_raw = f[[f"raw_{j}" for j in J[:5]]].values
            on = ac.onset(arm_raw, 2.0)
            cl = ac.C.close_events(f.state_gripper.values)
            info.update(onset_tick=on, first_close_tick=cl[0] if cl else None, n_close=len(cl), n_ticks=len(f))
            if info.get("pe") is not None:
                info["need"] = info["pe"] - s0
        epinfo[e] = info

    # ---- chunk 표
    TKc = TK[TK.pop_chunk >= 0]
    exec_ix = {c: g.sort_values("tick") for c, g in TKc.groupby("pop_chunk")}
    rows, prev_last = [], {}
    for m in metas:
        cid, e = m["chunk_id"], m["episode"]
        P = proc[cid]
        info = epinfo.get(e, {})
        pe, need = info.get("pe"), info.get("need")
        sg = float(np.sign(need)) if need else np.nan
        s_obs = m["obs_state"][0] if m.get("obs_state") else np.nan
        k0 = int(m["applied_delay"])
        resid = (pe - s_obs) if pe is not None else np.nan
        r = dict(chunk_id=cid, episode=e, ds_ep=info.get("ds_ep"), attempt=info.get("attempt"), first_in_ep=m["qsize_before"] == 0,
                 tick_merge=m["tick_at_merge"], obs_tick=m["obs_tick"],
                 obs_age_at_infer_ms=(m["t_build"] - m["obs_perf"]) * 1e3 if m.get("obs_perf") and m.get("t_build") else np.nan,
                 front_age_ms=(m["obs_perf"] - m["cam_ts"]["front"]) * 1e3 if m.get("cam_ts") and m["cam_ts"].get("front") else np.nan,
                 wrist_age_ms=(m["obs_perf"] - m["cam_ts"]["wrist"]) * 1e3 if m.get("cam_ts") and m["cam_ts"].get("wrist") else np.nan,
                 infer_ms=(m["t_pred1"] - m["t_pred0"]) * 1e3 if m.get("t_pred1") else np.nan,
                 inference_delay=m.get("inference_delay"), real_delay=m["real_delay"], applied_delay=k0, qsize_before=m["qsize_before"],
                 has_prefix=m["has_prefix"], state_pan_obs=s_obs, pe=pe, resid=resid,
                 pan_idx0=P[0, 0], pan_idx29=P[29, 0], pan_idx49=P[49, 0])
        g = exec_ix.get(cid)
        if g is not None and len(g):
            ix = g.pop_idx.values.astype(int)
            vals = P[ix, 0]
            r.update(exec_n=len(ix), exec_idx_first=int(ix[0]), exec_idx_last=int(ix[-1]), exec_first=vals[0], exec_last=vals[-1],
                     exec_tick_first=int(g.tick.iloc[0]), exec_tick_last=int(g.tick.iloc[-1]))
            if not np.isnan(sg):
                r["exec_move_sg"] = sg * (vals[-1] - vals[0])
                pl = prev_last.get(e)
                if pl is not None and not r["first_in_ep"]:
                    r["seam_sg"] = sg * (vals[0] - pl)
                    r["back_sg"] = max(0.0, -float((sg * (vals - pl)).min()))
            prev_last[e] = vals[-1]
            if RZ is not None and f"rtc_off_c{cid:05d}" in RZ:
                O = RZ[f"rtc_off_c{cid:05d}"][:, 0]
                r.update(off_exec_first=O[ix[0]], off_exec_last=O[ix[-1]], off_idx29=O[29], off_idx49=O[49],
                         rtc_minus_off_exec_first=vals[0] - O[ix[0]], rtc_minus_off_exec_last=vals[-1] - O[ix[-1]],
                         rtc_minus_off_exec_absmax=float(np.abs(vals - O[ix]).max()))
                if not np.isnan(sg) and "seam_sg" in r:
                    pl = vals[0] - r["seam_sg"] * sg
                    r["off_seam_sg"] = sg * (O[ix[0]] - pl)
                    r["off_back_sg"] = max(0.0, -float((sg * (O[ix] - pl)).min()))
        if not np.isnan(sg):
            r["plan_30_49_sg"] = sg * (P[49, 0] - P[29, 0])
        if pe is not None and abs(resid) >= 3:
            for nm, v in (("gain_idx29", P[29, 0]), ("gain_idx49", P[49, 0]), ("gain_exec_last", r.get("exec_last", np.nan))):
                r[nm] = (v - s_obs) / resid
            r["plan_30_49_frac"] = (P[49, 0] - P[29, 0]) / resid
            if "exec_last" in r:
                r["exec_move_frac"] = (r["exec_last"] - r["exec_first"]) / resid
            if "off_idx49" in r:
                r["off_gain_idx29"] = (r["off_idx29"] - s_obs) / resid
                r["off_gain_idx49"] = (r["off_idx49"] - s_obs) / resid
        if RP is not None:
            q = RP[RP.chunk_id == cid]
            if len(q) and "replay_max_abs_deg" in q:
                r["replay_max_abs_deg"] = float(q.iloc[0].replay_max_abs_deg)
        rows.append(r)
    CH = pd.DataFrame(rows)
    CH.to_csv(out / "chunks.csv", index=False)

    # ---- 틱 사슬: chunk 값 → queue 출력 raw (filter_log) → 필터 out → clamp 전 goal_in → sent → present
    T = TKc.copy()
    T["chunk_val_pan"] = [proc[c][i, 0] if c in proc and 0 <= i < 50 else np.nan for c, i in zip(T.pop_chunk, T.pop_idx)]
    T = T.merge(FL[["episode", "tick", "raw_shoulder_pan", "out_shoulder_pan", "state_shoulder_pan", "vclip_mask"]], on=["episode", "tick"], how="left")
    T["raw_minus_chunk"] = T.raw_shoulder_pan - T.chunk_val_pan
    T["out_minus_raw"] = T.out_shoulder_pan - T.raw_shoulder_pan
    T["sent_minus_goal_in"] = T.sent_shoulder_pan - T.goal_in_shoulder_pan
    T["sent_minus_present"] = T.sent_shoulder_pan - T.present_shoulder_pan
    T.to_csv(out / "ticks_chain.csv", index=False)

    # ---- 판 요약
    E = []
    for e in eps:
        info = epinfo[e]
        g = CH[CH.episode == e].sort_values("chunk_id")
        t = T[T.episode == e].sort_values("tick")
        r = dict(info)
        c0 = g[g.first_in_ep]
        if len(c0):
            c0 = c0.iloc[0]
            r.update(first_chunk_move29=c0.pan_idx29 - c0.state_pan_obs, first_chunk_move49=c0.pan_idx49 - c0.state_pan_obs,
                     first_chunk_dir29=float(np.sign(c0.pan_idx29 - c0.state_pan_obs)) if abs(c0.pan_idx29 - c0.state_pan_obs) >= 1 else 0.0)
            if info.get("need") is not None:
                r["first_chunk_dir29_ok"] = bool(r["first_chunk_dir29"] == np.sign(info["need"])) if r["first_chunk_dir29"] else None
            r.update(first_chunk_id=int(c0.chunk_id), first_chunk_idx29=c0.pan_idx29, first_chunk_idx49=c0.pan_idx49,
                     first_chunk_gain29=c0.get("gain_idx29", np.nan), first_chunk_gain49=c0.get("gain_idx49", np.nan),
                     first_chunk_idx49_minus_pe=(c0.pan_idx49 - info["pe"]) if info.get("pe") is not None else np.nan,
                     first_chunk_plan_30_49_frac=c0.get("plan_30_49_frac", np.nan), first_chunk_exec_last=c0.get("exec_last", np.nan))
        cl = info.get("first_close_tick")
        pre = g[g.exec_tick_first <= cl] if cl is not None and "exec_tick_first" in g else g
        if info.get("need") is not None and len(t):
            sg = np.sign(info["need"])
            pan_cmd = t.raw_shoulder_pan.values
            mv = np.where(np.abs(pan_cmd - info["s0"]) >= 3)[0]
            r["first_dir_ok"] = bool(np.sign(pan_cmd[mv[0]] - info["s0"]) == sg) if len(mv) else None
            if cl is not None:
                st = FL[FL.episode == e].sort_values("tick").state_shoulder_pan.values
                r.update(pan_at_close=st[cl], pan_err_at_close_sg=sg * (info["pe"] - st[cl]), pan_abs_err_at_close=abs(info["pe"] - st[cl]),
                         first_close_s=cl / FPS, onset_s=(info["onset_tick"] or 0) / FPS)
                # 두 불확실성을 섞지 않고 따로 비교
                if info.get("pe_sigma_coord_deg"):
                    r["pan_err_at_close_over_sigma_coord"] = (info["pe"] - st[cl]) / info["pe_sigma_coord_deg"]
                if info.get("pe_sigma_grasp_deg"):
                    r["pan_err_at_close_over_sigma_grasp"] = (info["pe"] - st[cl]) / info["pe_sigma_grasp_deg"]
                frac = sg * (st[: cl + 1] - info["s0"]) / abs(info["need"]) if abs(info["need"]) >= 3 else None
                if frac is not None:
                    k = np.where(frac >= 0.9)[0]
                    r["state_t90_s"] = (k[0] - (info["onset_tick"] or 0)) / FPS if len(k) else np.nan
        for col, nm in (("seam_sg", "seam"), ("back_sg", "back"), ("off_seam_sg", "off_seam"), ("off_back_sg", "off_back")):
            if col in pre and pre[col].notna().any():
                v = pre[col].dropna()
                r[f"{nm}_min" if "seam" in nm else f"{nm}_max"] = float(v.min() if "seam" in nm else v.max())
                r[f"n_{nm}_ge5" if "back" in nm else f"n_{nm}_le_m5"] = int((v >= 5).sum() if "back" in nm else (v <= -5).sum())
        if "rtc_minus_off_exec_last" in pre:
            r["rtc_minus_off_exec_last_abs_med"] = float(pre.rtc_minus_off_exec_last.abs().median())
        for c in ("exec_move_frac", "plan_30_49_frac", "gain_idx29", "gain_exec_last", "off_gain_idx29"):
            if c in pre:
                r[f"pre_close_{c}_med"] = float(pre[c].median())
        if len(t) > 20:
            L, err = best_lag(t.sent_shoulder_pan.values, t.present_shoulder_pan.values)
            mvg = np.abs(np.gradient(t.sent_shoulder_pan.values)) > 1.0
            d = np.abs(t.sent_minus_present.values)
            r.update(servo_lag_ticks=L, servo_lag_err=err, sent_minus_present_moving_p50=float(np.median(d[mvg])) if mvg.any() else np.nan,
                     sent_minus_present_moving_p95=float(np.percentile(d[mvg], 95)) if mvg.any() else np.nan,
                     pan_clamp_ticks=int((t.sent_minus_goal_in.abs() > 1e-4).sum()), filter_change_pan_p95=float(t.out_minus_raw.abs().quantile(.95)))
        r.update(n_chunks=len(g), infer_ms_p50=g.infer_ms.median(), front_age_ms_p50=g.front_age_ms.median())
        E.append(r)
    EP = pd.DataFrame(E)
    EP.to_csv(out / "episodes.csv", index=False)
    S = {"run": str(run), "warnings": warn, "attempts": att, "n_chunks": len(CH), "n_episodes_diag": len(eps),
         "infer_ms": CH.infer_ms.describe().to_dict(), "front_age_ms": CH.front_age_ms.describe().to_dict(),
         "applied_delay": CH.applied_delay.value_counts().to_dict(), "inference_delay": CH.inference_delay.value_counts(dropna=False).to_dict(),
         "raw_minus_chunk_absmax": float(T.raw_minus_chunk.abs().max()) if len(T) else None,
         "replay_max_abs_deg": float(CH.replay_max_abs_deg.max()) if "replay_max_abs_deg" in CH else None}
    json.dump(S, open(out / "summary.json", "w"), indent=1, default=float)
    print(json.dumps(S, indent=1, default=float))
    pd.set_option("display.width", 250)
    print(EP.T.to_string())


if __name__ == "__main__":
    main()
