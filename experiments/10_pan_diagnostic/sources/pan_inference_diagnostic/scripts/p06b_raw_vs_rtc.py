"""p06b 기록된 실행 명령 (실측) vs 재구성 raw chunk U (RTC 안내 없음) vs 재구성 RTC chunk G (같은 noise) — pan. CPU.

입력: tables/p01_ticks.parquet, p02_policy_episodes.csv, p03b_*.npz
출력: tables/p06b_chunks.csv, p06b_summary.json
chunk k 의 실행 구간 = 기록상 그 chunk 에서 꺼낸 index (chunk 0: 0–29, 이후 ≈ 10–29). e = 실행 구간 마지막 index.
열 (pan, °):
  L_first / L_end           기록된 raw (queue 출력) — 실측
  U_med_end, U_p10/p90_end  재구성 U 의 index e (noise N 개)
  G_med_end, G_p10/p90_end  재구성 G 의 index e (같은 noise)
  rtc_eff_end_med           median_n (G_n − U_n) at e   — 같은 noise 에서 RTC 안내가 바꾼 양 (재구성)
  L_rank_U / L_rank_G       L_end 가 U / G 분포에서 차지하는 백분위 (0–1)
  seam_L / seam_U / seam_G  chunk 경계 끊김: (그 chunk 첫 실행 index 값) − (앞 chunk 마지막 실행 기록값)
  seg_L / seg_U / seg_G     실행 구간 안 변화 (끝 − 처음), need 방향 부호로 (양수 = 목표 쪽)
  U_med_49, U_frac49        U index 49 (chunk 끝, 관측 뒤 1.67 s) 와 (U49 − state_obs) / resid
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python p06b_raw_vs_rtc.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

TAB = Path.home() / "so101_runs/main_k8/d2/pan_inference_diagnostic/tables"


def rank(x, s):
    return float((s < x).mean() + 0.5 * (s == x).mean())


def main():
    T = pd.read_parquet(TAB / "p01_ticks.parquet")
    PE = pd.read_csv(TAB / "p02_policy_episodes.csv")
    rows = []
    for (run, e), g in T.groupby(["run", "ep"]):
        f = TAB / f"p03b_{run}_ep{e}.npz"
        if not f.exists():
            continue
        z = np.load(f)
        ne = int(z["n_early"])
        U8, G8 = z["U"][..., 0], z["G"][..., 0]
        UE = z["U_early"][..., 0] if ne else None
        GE = z["G_early"][..., 0] if ne else None
        tag = f"{run[16:]}/ep{e}"
        pr = PE[PE.ep == tag].iloc[0]
        pe, on = float(pr.pe), int(round(pr.onset_s * 30))
        sgn = np.sign(pr.need)
        raw, st = g.raw_shoulder_pan.values, g.state_shoulder_pan.values
        cid_t, cidx_t = g.chunk_id.values, g.chunk_idx.values
        prev_last = None
        for i, k in enumerate(z["chunk_id"]):
            U = UE[:, i] if (ne and i < ne) else U8[:, i]
            G = GE[:, i] if (ne and i < ne) else G8[:, i]
            sel = np.where(cid_t == k)[0]
            if not len(sel):
                continue
            i0, i1 = int(cidx_t[sel[0]]), int(cidx_t[sel[-1]])
            fo = int(z["obs_frame"][i])
            res = pe - st[fo]
            Lf, Le = raw[sel[0]], raw[sel[-1]]
            r = dict(ep=tag, chunk_id=int(k), n_noise=len(U), t_obs=(fo - on) / 30, obs_frame=fo, state_obs=st[fo], resid=res,
                     delay=int(z["delay"][i]), inference_delay=int(z["inference_delay"][i]), prefix_known=int(z["prefix_known"][i].sum()),
                     idx_first=i0, idx_end=i1, L_first=Lf, L_end=Le,
                     U_med_first=np.median(U[:, i0]), G_med_first=np.median(G[:, i0]),
                     U_med_end=np.median(U[:, i1]), U_p10_end=np.percentile(U[:, i1], 10), U_p90_end=np.percentile(U[:, i1], 90),
                     G_med_end=np.median(G[:, i1]), G_p10_end=np.percentile(G[:, i1], 10), G_p90_end=np.percentile(G[:, i1], 90),
                     rtc_eff_first_med=np.median(G[:, i0] - U[:, i0]), rtc_eff_end_med=np.median(G[:, i1] - U[:, i1]),
                     rtc_eff_end_absmax=np.abs(G[:, i1] - U[:, i1]).max(),
                     L_rank_U=rank(Le, U[:, i1]), L_rank_G=rank(Le, G[:, i1]),
                     seg_L=sgn * (Le - Lf), seg_U=sgn * np.median(U[:, i1] - U[:, i0]), seg_G=sgn * np.median(G[:, i1] - G[:, i0]),
                     U_med_29=np.median(U[:, 29]), U_med_49=np.median(U[:, 49]), U_p10_49=np.percentile(U[:, 49], 10), U_p90_49=np.percentile(U[:, 49], 90),
                     G_med_49=np.median(G[:, 49]))
            if prev_last is not None:
                r.update(seam_L=sgn * (Lf - prev_last), seam_U=sgn * np.median(U[:, i0] - prev_last), seam_G=sgn * np.median(G[:, i0] - prev_last))
            if abs(res) >= 3:
                r.update(U_frac49=(np.median(U[:, 49]) - st[fo]) / res, U_frac_end=(np.median(U[:, i1]) - st[fo]) / res,
                         G_frac_end=(np.median(G[:, i1]) - st[fo]) / res, L_frac_end=(Le - st[fo]) / res,
                         U_dir49_ok_frac=float((np.sign(U[:, 49] - st[fo]) == np.sign(res)).mean()))
            rows.append(r)
            prev_last = raw[sel[-1]]
    R = pd.DataFrame(rows)
    R.to_csv(TAB / "p06b_chunks.csv", index=False)
    S = {}
    for nm, sub in (("first4s", R[(R.t_obs < 4)]), ("after4s", R[R.t_obs >= 4]), ("all", R)):
        k1 = sub[sub.chunk_id > 0]
        S[nm] = dict(n=int(len(sub)), n_k1=int(len(k1)),
                     L_rank_U_med=float(k1.L_rank_U.median()), L_rank_G_med=float(k1.L_rank_G.median()),
                     L_in_U_p10_p90=float(((k1.L_end >= k1.U_p10_end) & (k1.L_end <= k1.U_p90_end)).mean()),
                     L_in_G_p10_p90=float(((k1.L_end >= k1.G_p10_end) & (k1.L_end <= k1.G_p90_end)).mean()),
                     rtc_eff_end_abs_med=float(k1.rtc_eff_end_med.abs().median()), rtc_eff_first_abs_med=float(k1.rtc_eff_first_med.abs().median()),
                     L_minus_G_end_abs_med=float((k1.L_end - k1.G_med_end).abs().median()), L_minus_U_end_abs_med=float((k1.L_end - k1.U_med_end).abs().median()),
                     seam_L_med=float(k1.seam_L.median()), seam_U_med=float(k1.seam_U.median()), seam_G_med=float(k1.seam_G.median()))
    json.dump(S, open(TAB / "p06b_summary.json", "w"), indent=1, default=float)
    pd.set_option("display.width", 260, "display.max_columns", 40)
    print(json.dumps(S, indent=1, default=float))
    cols = ["ep", "chunk_id", "n_noise", "t_obs", "state_obs", "resid", "inference_delay", "idx_first", "idx_end", "L_first", "L_end",
            "U_med_first", "G_med_first", "U_med_end", "G_med_end", "U_p10_end", "U_p90_end", "rtc_eff_end_med", "L_rank_U", "L_rank_G",
            "seam_L", "seam_U", "seam_G", "U_med_49", "U_frac49", "U_dir49_ok_frac"]
    print(R[R.t_obs < 4][cols].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
