"""p02 기존 로그만으로 계산할 수 있는 pan 지표 (읽기만 함, CPU). 정책 5판 vs 사람 256편.

입력: tables/p01_ticks.parquet, p01_merges.csv (p01_timeline.py), data_coverage_audit/tables (a02_frames, a02_events, a04_eval_positions, a07_policy_episodes)
출력: tables/p02_*.csv, tables/p02_summary.json

기준 pan (pe) = 큐브 위치 추정 (front 시작 화면) → pan 축 방위 (ac.bearing, PAN_SIGN, PAN_OFF). 사람도 같은 식 (a02_events.pan_exp).
  사람 첫 파지 순간 pan − pe: SD 2.31°, |·| 95% 4.80° (data_coverage_audit 07) — 기준값 자체의 오차 범위로 쓴다.
시간 0 = onset (명령 팔 5관절이 첫 값에서 2° 넘게 벗어난 첫 프레임, a07 과 같은 규칙). 정책 명령 = raw (queue 출력), 사람 명령 = 리더 action.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HOME = Path.home()
sys.path.insert(0, str(HOME / "so101_runs/main_k8/d2/data_coverage_audit/scripts"))
import ac  # noqa: E402

OUT = ac.D2 / "pan_inference_diagnostic"
TAB = OUT / "tables"
FPS = 30
TS = (0.5, 1.0, 2.0, 3.0)


def frac_at(x, x0, need, on, ts):
    return [float((x[min(on + int(round(t * FPS)), len(x) - 1)] - x0) / need) for t in ts]


def cover(x, x0, need, on, end, k):
    f = (x[on:end + 1] - x0) / need
    i = np.where(f >= k)[0]
    return i[0] / FPS if len(i) else np.nan


def human():
    W = pd.read_parquet(ac.TAB / "a02_frames.parquet")
    E = pd.read_csv(ac.TAB / "a02_events.csv")
    rows, gain = [], []
    for e in range(256):
        g = W[W.ep == e]
        s, a = g.s_shoulder_pan.values, g.a_shoulder_pan.values
        on, c, pe = int(E.onset[e]), int(E.grasp[e]), float(E.pan_exp[e])
        need = pe - s[on]
        r = dict(ep=e, group=E.group[e], pe=pe, s0=s[on], need=need)
        if abs(need) >= 5:
            for nm, x in (("cmd", a), ("state", s)):
                for t, v in zip(TS, frac_at(x, s[on], need, on, TS)):
                    r[f"{nm}_frac_{t}"] = v
                r[f"{nm}_t50"], r[f"{nm}_t90"] = cover(x, s[on], need, on, c, .5), cover(x, s[on], need, on, c, .9)
        rows.append(r)
        # 닫힌 고리 이득: 시각 t 의 남은 오차 r_t = pe − s[t] 중 명령이 Δ 프레임 뒤까지 덮는 비율
        for t in range(on, c - 30, 10):
            res = pe - s[t]
            if abs(res) >= 3:
                gain.append(dict(who="human", ep=e, t_from_onset=(t - on) / FPS, t_to_close=(c - t) / FPS, resid=res,
                                 g20=(a[t + 20] - s[t]) / res, g30=(a[t + 30] - s[t]) / res))
    return pd.DataFrame(rows), pd.DataFrame(gain)


def nearest_humans(cx, cy, k=10):
    T = pd.read_csv(ac.TAB / "a01_cube_table.csv")
    d = np.hypot(T.cube_x - cx, T.cube_y - cy)
    idx = np.argsort(d.values)[:k]
    return idx, d.values[idx]


def main():
    T = pd.read_parquet(TAB / "p01_ticks.parquet")
    M = pd.read_csv(TAB / "p01_merges.csv")
    EV = pd.read_csv(ac.TAB / "a04_eval_positions.csv")
    PE = pd.read_csv(ac.TAB / "a07_policy_episodes.csv")
    H, HG = human()
    H.to_csv(TAB / "p02_human_episodes.csv", index=False)
    rows, chunks, gains, track = [], [], [], []
    for (run, e), g in T.groupby(["run", "ep"]):
        ev = EV[(EV.run == run) & (EV.ep == e)].iloc[0]
        cx, cy = float(ev.start_x), float(ev.start_y)
        pe = ac.PAN_SIGN * float(ac.bearing(cx, cy)) + ac.PAN_OFF
        raw, out, sent, st = (g[f"{p}_shoulder_pan"].values for p in ("raw", "out", "sent", "state"))
        arm_raw = g[[f"raw_{j}" for j in ac.JOINTS[:5]]].values
        on = ac.onset(arm_raw, 2.0) or 0
        c = ac.C.close_events(g.state_gripper.values)
        c = c[0] if c else len(g) - 1
        need = pe - st[on]
        tag = f"{run[16:]}/ep{e}"
        r = dict(ep=tag, cube=f"({cx:.1f}, {cy:.1f})", dist_K=float(ev.dist_K), nearest_K=ev.nearest_K, dist_train=float(ev.nearest_train_cm),
                 pe=pe, s0=st[0], s_on=st[on], need=need, onset_s=on / FPS, first_close_s=c / FPS)
        # 첫 chunk (chunk_id 0) 의 실행 구간
        g0 = g[g.chunk_id == 0]
        n0 = len(g0)
        r["chunk0_exec_idx"] = f"{int(g0.chunk_idx.min())}–{int(g0.chunk_idx.max())}"
        for idx in (0, 15, n0 - 1):
            r[f"chunk0_raw_idx{idx if idx != n0 - 1 else 'last'}_minus_s0"] = float(raw[idx] - st[0])
        r["chunk0_last_frac_need"] = float((raw[n0 - 1] - st[0]) / (pe - st[0]))
        mv = np.where(np.abs(raw - st[0]) > 3.0)[0]   # 3° 넘게 움직인 첫 명령의 방향
        r["first_dir_ok"] = bool(np.sign(raw[mv[0]] - st[0]) == np.sign(pe - st[0])) if len(mv) else None
        for nm, x in (("cmd", raw), ("state", st)):
            for t, v in zip(TS, frac_at(x, st[on], need, on, TS)):
                r[f"{nm}_frac_{t}"] = v
            r[f"{nm}_t50"], r[f"{nm}_t90"] = cover(x, st[on], need, on, c, .5), cover(x, st[on], need, on, c, .9)
        pr = PE[(PE.run == run[16:]) & (PE.ep == e)]
        r["pan_err_at_close"] = float(pr.pan_err_at_close.iloc[0]) if len(pr) else np.nan
        # 가까운 사람 10편 (큐브 위치)
        idx, dd = nearest_humans(cx, cy)
        hh = H.iloc[idx]
        r["nn10_dist_cm_max"] = float(dd.max())
        for t in TS:
            r[f"nn10_cmd_frac_{t}_med"] = float(np.nanmedian(hh[f"cmd_frac_{t}"]))
        r["nn10_cmd_t90_med"] = float(np.nanmedian(hh.cmd_t90))
        rows.append(r)
        # chunk 별 (재계획)
        mm = M[(M.run == run) & (M.ep == e)].sort_values("chunk_id").reset_index(drop=True)
        for k in range(len(mm)):
            mf = int(mm.merge_frame[k])
            nf = min(int(mm.merge_frame[k + 1]) if k + 1 < len(mm) else len(g), len(g))
            if nf <= mf or mf >= len(g):
                continue
            d = int(mm.applied_delay[k]) if not np.isnan(mm.applied_delay[k]) else 0
            fo = max(mf - d, 0) if k > 0 else 0   # 관측 프레임 근사 (merge − 적용 delay). chunk 0 은 frame 0 이전(정지 상태)
            res = pe - st[fo]
            seg_end = nf - 1
            cr = dict(ep=tag, chunk_id=k, merge_frame=mf, obs_frame=fo, t_obs=fo / FPS, delay=d, latency_s=mm.latency_s[k],
                      resid_obs=res, state_obs=st[fo], raw_first=raw[mf], raw_last=raw[seg_end],
                      seam_jump=(raw[mf] - raw[mf - 1]) if mf > 0 else np.nan,
                      seg_slope_deg_s=(raw[seg_end] - raw[mf]) / max(seg_end - mf, 1) * FPS,
                      obs_to_seg_end_s=(seg_end - fo) / FPS, before_close=mf < c)
            cr["gain_seg_end"] = (raw[seg_end] - st[fo]) / res if abs(res) >= 3 else np.nan
            chunks.append(cr)
        # 사람과 같은 정의의 닫힌 고리 이득 (10 프레임 간격, onset~첫 닫힘 30 프레임 전)
        for t in range(on, c - 30, 10):
            res = pe - st[t]
            if abs(res) >= 3:
                gains.append(dict(who="policy", ep=tag, t_from_onset=(t - on) / FPS, t_to_close=(c - t) / FPS, resid=res,
                                  g20=(raw[t + 20] - st[t]) / res, g30=(raw[t + 30] - st[t]) / res))
        # 서보 추종 (onset ~ 첫 닫힘)
        seg = slice(on, c + 1)
        v = np.abs(np.gradient(sent[seg]))
        lags = {}
        for L in range(0, 11):
            a_, b_ = sent[seg][: len(v) - L], st[seg][L:]
            mvm = v[: len(v) - L] > 0.2
            lags[L] = float(np.mean(np.abs(b_[mvm] - a_[mvm]))) if mvm.sum() > 10 else np.nan
        best = min(lags, key=lambda L: lags[L] if not np.isnan(lags[L]) else 1e9)
        moving = v > 0.2
        te = (sent - st)[seg]
        track.append(dict(ep=tag, frames=int(c + 1 - on), moving_frames=int(moving.sum()), lag_best_ticks=best, mae_at_best=lags[best], mae_lag0=lags[0],
                          te_abs_p50_moving=float(np.median(np.abs(te[moving]))) if moving.any() else np.nan,
                          te_abs_p95_moving=float(np.percentile(np.abs(te[moving]), 95)) if moving.any() else np.nan,
                          te_abs_p50_still=float(np.median(np.abs(te[~moving]))) if (~moving).any() else np.nan,
                          pan_clamp_ticks=int(g.clamp_shoulder_pan.sum()), any_clamp_ticks=int(g.filter(like="clamp_").any(axis=1).sum()),
                          filter_out_minus_raw_abs_p50=float(np.median(np.abs(out - raw)[seg])), filter_out_minus_raw_abs_p95=float(np.percentile(np.abs(out - raw)[seg], 95)),
                          sent_minus_out_abs_max=float(np.abs(sent - out)[seg].max())))
    R, CH, G, TR = pd.DataFrame(rows), pd.DataFrame(chunks), pd.concat([HG, pd.DataFrame(gains)], ignore_index=True), pd.DataFrame(track)
    R.to_csv(TAB / "p02_policy_episodes.csv", index=False)
    CH.to_csv(TAB / "p02_chunks.csv", index=False)
    G.to_csv(TAB / "p02_closed_loop_gain.csv", index=False)
    TR.to_csv(TAB / "p02_tracking.csv", index=False)
    # 사람 요약
    Hm = H[np.abs(H.need) >= 5]
    S = dict(n_human_need5=int(len(Hm)))
    for c_ in [f"{p}_frac_{t}" for p in ("cmd", "state") for t in TS] + ["cmd_t50", "cmd_t90", "state_t50", "state_t90"]:
        x = Hm[c_].values
        S[f"human_{c_}"] = dict(p5=float(np.nanpercentile(x, 5)), p25=float(np.nanpercentile(x, 25)), p50=float(np.nanmedian(x)),
                                p75=float(np.nanpercentile(x, 75)), p95=float(np.nanpercentile(x, 95)), n_nan=int(np.isnan(x).sum()))
    bins = [3, 6, 12, 25, 200]
    G["rbin"] = pd.cut(G.resid.abs(), bins, right=False).astype(str)
    S["gain_by_resid"] = G.groupby(["who", "rbin"]).agg(n=("g30", "size"), g20_med=("g20", "median"), g30_med=("g30", "median"),
                                                        g30_p25=("g30", lambda s: s.quantile(.25)), g30_p75=("g30", lambda s: s.quantile(.75))).reset_index().to_dict("records")
    json.dump(S, open(TAB / "p02_summary.json", "w"), indent=1, default=float)
    pd.set_option("display.width", 250, "display.max_columns", 60)
    print(R.T)
    print(TR.T)
    print(pd.DataFrame(S["gain_by_resid"]))
    print(CH.groupby("ep").agg(n=("chunk_id", "size"), seam_abs_med=("seam_jump", lambda s: s.abs().median()), lat=("latency_s", "median")))


if __name__ == "__main__":
    main()
