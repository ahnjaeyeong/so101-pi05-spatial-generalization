"""p06c 집중 사례 표: 기록된 실행 pan (실측) 과 재구성 U / G (같은 noise 32 개) 의 index 별 비교. CPU.

입력: tables/p01_ticks.parquet, p02_policy_episodes.csv, p03b_*.npz (U_early, G_early)
출력:
  tables/p06c_traj.csv     판 · chunk · index 별: L (기록, 실행된 index 만), state (그 틱 Present), U/G p10 · 50 · 90, prefix (G 에 쓴 값), prefix_known
  tables/p06c_noise.csv    판 · chunk 별 noise 분포: index 29 / 49 에서 '움직임 비율' ((U − state_obs) / resid) 의 구간별 noise 개수,
                           L_first / L_end 의 U · G 백분위 (첫 실행 index, 마지막 실행 index)
  tables/p06c_summary.json chunk 0 (prefix 없음) 다섯 판의 기록 vs 재구성 요약
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python p06c_focus_cases.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

TAB = Path.home() / "so101_runs/main_k8/d2/pan_inference_diagnostic/tables"
BINS = [-np.inf, 0.0, 0.25, 0.5, 0.75, np.inf]
BIN_NAMES = ["lt0", "0_25", "25_50", "50_75", "ge75"]


def rank(x, s):
    return float((s < x).mean() + 0.5 * (s == x).mean())


def main():
    T = pd.read_parquet(TAB / "p01_ticks.parquet")
    PE = pd.read_csv(TAB / "p02_policy_episodes.csv")
    traj, nz = [], []
    for (run, e), g in T.groupby(["run", "ep"]):
        f = TAB / f"p03b_{run}_ep{e}.npz"
        if not f.exists():
            continue
        z = np.load(f)
        ne = int(z["n_early"])
        tag = f"{run[16:]}/ep{e}"
        pr = PE[PE.ep == tag].iloc[0]
        pe = float(pr.pe)
        raw, st = g.raw_shoulder_pan.values, g.state_shoulder_pan.values
        cid_t, cidx_t = g.chunk_id.values, g.chunk_idx.values
        for i in range(ne):
            k = int(z["chunk_id"][i])
            U, G = z["U_early"][:, i, :, 0], z["G_early"][:, i, :, 0]
            fo = int(z["obs_frame"][i])
            res = pe - st[fo]
            sel = np.where(cid_t == k)[0]
            Lmap = {int(cidx_t[t]): (raw[t], st[t], int(t)) for t in sel}
            for j in range(50):
                Lj = Lmap.get(j)
                traj.append(dict(ep=tag, chunk_id=k, idx=j, frame=Lj[2] if Lj else np.nan, L=Lj[0] if Lj else np.nan, state=Lj[1] if Lj else np.nan,
                                 U_p10=np.percentile(U[:, j], 10), U_p50=np.median(U[:, j]), U_p90=np.percentile(U[:, j], 90),
                                 G_p10=np.percentile(G[:, j], 10), G_p50=np.median(G[:, j]), G_p90=np.percentile(G[:, j], 90),
                                 prefix=z["prefix_deg"][i][j, 0] if j < 20 else np.nan,
                                 prefix_known=bool(z["prefix_known"][i][j]) if j < 20 else False))
            if not len(sel):
                continue
            i0, i1 = int(cidx_t[sel[0]]), int(cidx_t[sel[-1]])
            r = dict(ep=tag, chunk_id=k, n_noise=len(U), obs_frame=fo, state_obs=st[fo], pe=pe, resid=res,
                     inference_delay=int(z["inference_delay"][i]), idx_first=i0, idx_end=i1,
                     L_first=raw[sel[0]], L_end=raw[sel[-1]],
                     L_first_rank_U=rank(raw[sel[0]], U[:, i0]), L_first_rank_G=rank(raw[sel[0]], G[:, i0]),
                     L_end_rank_U=rank(raw[sel[-1]], U[:, i1]), L_end_rank_G=rank(raw[sel[-1]], G[:, i1]),
                     U_min_end=U[:, i1].min(), U_max_end=U[:, i1].max(),
                     L_frac_end=(raw[sel[-1]] - st[fo]) / res if abs(res) >= 3 else np.nan)
            if abs(res) >= 3:
                for idx in (29, 49):
                    fr = (U[:, idx] - st[fo]) / res
                    c = np.histogram(fr, BINS)[0]
                    r.update({f"U{idx}_frac_{b}": int(n) for b, n in zip(BIN_NAMES, c)})
                    r[f"U{idx}_frac_med"] = float(np.median(fr))
            nz.append(r)
    TR, NZ = pd.DataFrame(traj), pd.DataFrame(nz)
    TR.to_csv(TAB / "p06c_traj.csv", index=False)
    NZ.to_csv(TAB / "p06c_noise.csv", index=False)
    c0 = NZ[NZ.chunk_id == 0]
    S = {"chunk0": {r.ep: dict(resid=r.resid, L_end_idx29=r.L_end, L_frac_end=r.L_frac_end, U_min_29=r.U_min_end, U_max_29=r.U_max_end,
                               L_end_rank_U=r.L_end_rank_U, U29_frac_med=r.get("U29_frac_med"), U49_frac_med=r.get("U49_frac_med"),
                               U29_frac_bins={b: r.get(f"U29_frac_{b}") for b in BIN_NAMES},
                               U49_frac_bins={b: r.get(f"U49_frac_{b}") for b in BIN_NAMES}) for _, r in c0.iterrows()},
         "early_chunks_ge1": dict(n=int((NZ.chunk_id > 0).sum()),
                                  L_first_rank_G_med=float(NZ[NZ.chunk_id > 0].L_first_rank_G.median()),
                                  L_end_rank_G_med=float(NZ[NZ.chunk_id > 0].L_end_rank_G.median()),
                                  L_end_outside_U_minmax=int(((NZ.chunk_id > 0) & ((NZ.L_end < NZ.U_min_end) | (NZ.L_end > NZ.U_max_end))).sum()))}
    # 재구성 U (noise 8 개, 첫 닫힘 전 모든 chunk) 의 '1 s 계획 이득' (U[idx29] − state_obs) / resid 를 |resid| 구간별로 모음.
    # 같은 구간의 사람 시연 g30 (p02_closed_loop_gain.csv, 사람 리더 action t+30 기준) 과 나란히 둔다.
    pool = []
    for (run, e), g in T.groupby(["run", "ep"]):
        f = TAB / f"p03b_{run}_ep{e}.npz"
        if not f.exists():
            continue
        z = np.load(f)
        st = g.state_shoulder_pan.values
        pe = float(PE[PE.ep == f"{run[16:]}/ep{e}"].iloc[0].pe)
        for i in range(len(z["chunk_id"])):
            fo = int(z["obs_frame"][i])
            res = pe - st[fo]
            for n in range(z["U"].shape[0]):
                pool.append(dict(ep=f"{run[16:]}/ep{e}", chunk_id=int(z["chunk_id"][i]), resid=res, f29=(z["U"][n, i, 29, 0] - st[fo]) / res,
                                 f49=(z["U"][n, i, 49, 0] - st[fo]) / res))
    PO = pd.DataFrame(pool)
    HG = pd.read_csv(TAB / "p02_closed_loop_gain.csv")
    edges = [3, 6, 12, 25, np.inf]
    S["plan_gain_by_resid"] = {}
    for lo, hi in zip(edges[:-1], edges[1:]):
        p = PO[(PO.resid.abs() >= lo) & (PO.resid.abs() < hi)]
        h = HG[(HG.who == "human") & (HG.resid.abs() >= lo) & (HG.resid.abs() < hi)]
        pol = HG[(HG.who != "human") & (HG.resid.abs() >= lo) & (HG.resid.abs() < hi)]
        S["plan_gain_by_resid"][f"{lo}-{hi}"] = dict(
            n_chunks=int(p.groupby(["ep", "chunk_id"]).ngroups), n_samples=int(len(p)),
            U29_med=float(p.f29.median()) if len(p) else None, U29_mean=float(p.f29.mean()) if len(p) else None,
            U29_ge50_frac=float((p.f29 >= 0.5).mean()) if len(p) else None, U49_med=float(p.f49.median()) if len(p) else None,
            policy_logged_g30_med=float(pol.g30.median()) if len(pol) else None, human_g30_med=float(h.g30.median()) if len(h) else None,
            n_human=int(len(h)), n_policy_logged=int(len(pol)))
    json.dump(S, open(TAB / "p06c_summary.json", "w"), indent=1, default=float)
    pd.set_option("display.width", 250, "display.max_columns", 40)
    print(json.dumps(S, indent=1, default=float))
    print(NZ.drop(columns=[c for c in NZ.columns if c.startswith("U49_frac_") and c != "U49_frac_med"]).round(2).to_string(index=False))


if __name__ == "__main__":
    main()
