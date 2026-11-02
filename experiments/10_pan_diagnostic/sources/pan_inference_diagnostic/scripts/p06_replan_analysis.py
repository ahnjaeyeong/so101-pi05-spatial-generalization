"""p06 기존 5판: 실행된 raw (실측) vs 같은 관측의 오프라인 재계획 (재구성, RTC 안내 없음, noise 8개) 비교. CPU.

입력: tables/p01_ticks.parquet, p02_chunks.csv, p03_replan_*.npz, p02_policy_episodes.csv (pe)
출력: tables/p06_chunks.csv (chunk 별), p06_summary.json
정의 (chunk k, 관측 프레임 fo, 적용 delay d, 실행 구간 = merge 프레임 mf … 다음 merge 전 = chunk index d … d+n−1):
  resid      = pe − state_pan[fo]                       (관측 시점 남은 pan, 기준 pe 는 큐브 위치 추정값)
  exec_end   = raw_pan[실행 구간 마지막]                  (실측: queue 출력, RTC 이어붙이기 뒤)
  model_m(i) = 오프라인 chunk pan index i 의 noise 8개 평균, model_lo/hi = 최소/최대
  exec_vs_model = exec_end − model_m(같은 index)         (RTC 안내 + noise 차이가 섞인 값; noise 범위 안인지 표시)
  gain_exec  = (exec_end − state[fo]) / resid,  gain_model29 / gain_model49 = (model_m(29|49) − state[fo]) / resid  (|resid| ≥ 3° 만)
  model_tail = |model_m(49) − model_m(40)|              (chunk 끝에서도 아직 움직이는 정도)
  seam       = raw[mf] − raw[mf−1] (실측), seam_model = model_m(d) − (앞 chunk 실행 마지막 raw)
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python p06_replan_analysis.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

TAB = Path.home() / "so101_runs/main_k8/d2/pan_inference_diagnostic/tables"
FPS = 30


def main():
    T = pd.read_parquet(TAB / "p01_ticks.parquet")
    PE = pd.read_csv(TAB / "p02_policy_episodes.csv")
    rows = []
    for (run, e), g in T.groupby(["run", "ep"]):
        z = np.load(TAB / f"p03_replan_{run}_ep{e}.npz")
        ch = z["chunks"][..., 0]  # (8, n_chunk, 50) pan
        tag = f"{run[16:]}/ep{e}"
        pr = PE[PE.ep == tag].iloc[0]
        pe, on = float(pr.pe), int(round(pr.onset_s * FPS))
        c = int(round(pr.first_close_s * FPS))
        raw, st = g.raw_shoulder_pan.values, g.state_shoulder_pan.values
        prev_last = None
        for i, (cid, fo, mf, d) in enumerate(zip(z["chunk_id"], z["obs_frame"], z["merge_frame"], z["delay"])):
            seg = np.where(g.chunk_id.values == cid)[0]
            if not len(seg):
                continue
            k_last = int(g.chunk_idx.values[seg[-1]])
            m = ch[:, i, :].mean(0)
            lo, hi = ch[:, i, :].min(0), ch[:, i, :].max(0)
            res = pe - st[fo]
            ee = raw[seg[-1]]
            r = dict(ep=tag, chunk_id=int(cid), obs_frame=int(fo), t_obs_from_onset=(fo - on) / FPS, before_close=bool(fo < c), delay=int(d),
                     n_exec=len(seg), k_last=k_last, state_obs=st[fo], resid=res, exec_end=ee,
                     model_at_exec_end=m[k_last], model_lo_at_exec_end=lo[k_last], model_hi_at_exec_end=hi[k_last],
                     model_sd_at_exec_end=ch[:, i, k_last].std(), exec_vs_model=ee - m[k_last],
                     exec_in_model_range=bool(lo[k_last] - 0.5 <= ee <= hi[k_last] + 0.5),
                     model29=m[29], model49=m[49], model49_sd=ch[:, i, 49].std(), model_tail=abs(m[49] - m[40]),
                     seam=(raw[seg[0]] - raw[seg[0] - 1]) if seg[0] > 0 else np.nan,
                     seam_model=(m[int(d)] - prev_last) if prev_last is not None else np.nan)
            if abs(res) >= 3:
                r.update(gain_exec=(ee - st[fo]) / res, gain_model29=(m[29] - st[fo]) / res, gain_model49=(m[49] - st[fo]) / res,
                         dir_model49_ok=bool(np.sign(m[49] - st[fo]) == np.sign(res)))
            rows.append(r)
            prev_last = raw[seg[-1]]
    R = pd.DataFrame(rows)
    R.to_csv(TAB / "p06_chunks.csv", index=False)
    S = {}
    A = R[R.before_close]
    for name, sub in (("all_before_close", A), ("first3s", A[A.t_obs_from_onset < 3]), ("after3s", A[A.t_obs_from_onset >= 3])):
        big = sub[sub.resid.abs() >= 3]
        S[name] = dict(n=int(len(sub)), n_resid3=int(len(big)),
                       exec_in_model_range_frac=float(sub.exec_in_model_range.mean()),
                       exec_vs_model_med=float(sub.exec_vs_model.median()), exec_vs_model_abs_med=float(sub.exec_vs_model.abs().median()),
                       model_sd_med=float(sub.model_sd_at_exec_end.median()),
                       gain_exec_med=float(big.gain_exec.median()) if len(big) else None,
                       gain_model29_med=float(big.gain_model29.median()) if len(big) else None,
                       gain_model49_med=float(big.gain_model49.median()) if len(big) else None,
                       dir_model49_ok_frac=float(big.dir_model49_ok.mean()) if len(big) else None,
                       model_tail_med=float(sub.model_tail.median()))
    S["per_episode"] = A.groupby("ep").apply(lambda s: pd.Series(dict(
        n=len(s), exec_vs_model_med=s.exec_vs_model.median(), in_range=s.exec_in_model_range.mean(),
        gain_exec_med=s.gain_exec.median(), gain_model29_med=s.gain_model29.median(), gain_model49_med=s.gain_model49.median(),
        dir_ok=s.dir_model49_ok.mean()))).reset_index().to_dict("records")
    json.dump(S, open(TAB / "p06_summary.json", "w"), indent=1, default=float)
    pd.set_option("display.width", 250, "display.max_columns", 40)
    print(json.dumps(S, indent=1, default=float))
    print(R[R.t_obs_from_onset < 4][["ep", "chunk_id", "t_obs_from_onset", "state_obs", "resid", "exec_end", "model_at_exec_end", "model_sd_at_exec_end",
                                     "model29", "model49", "model49_sd", "seam", "seam_model", "gain_exec", "gain_model49"]].round(2).to_string())


if __name__ == "__main__":
    main()
