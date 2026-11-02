"""p06d p03c 반사실 결과 요약 (CPU). **재구성 · 반사실 값** 과 기록값 (실측) 을 나란히 둔다.

입력: tables/p03c_counterfactual.npz, p03c_cases.csv, p01_ticks.parquet, p02_policy_episodes.csv
출력:
  tables/p06d_chunk0_u256.csv   판별 chunk 0 (prefix 없음) noise 256 개: (U[idx] − s0)/resid 분포 (idx 29 · 49), 기록 실행 끝 (idx 29) 의 백분위
  tables/p06d_seams.csv         사례 · 조건별 need 부호 seam (양수 = 목표 쪽) p10/50/90, 실행 구간 (i0…i1) 안 '앞 chunk 끝보다 목표 반대쪽으로 간 최대량' p10/50/90,
                                기록값 (같은 정의)
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python p06d_counterfactual_summary.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

TAB = Path.home() / "so101_runs/main_k8/d2/pan_inference_diagnostic/tables"
RUNS = {"try3": "20261026_135128_20k_t1_try3", "filt": "20261026_140246_20k_t1_try3_filt"}


def rank(x, s):
    return float((s < x).mean() + 0.5 * (s == x).mean())


def main():
    Z = np.load(TAB / "p03c_counterfactual.npz")
    C = pd.read_csv(TAB / "p03c_cases.csv")
    T = pd.read_parquet(TAB / "p01_ticks.parquet")
    PE = pd.read_csv(TAB / "p02_policy_episodes.csv")
    rows = []
    for case in C[C.cond == "U256"].case:
        key, ep, _ = case.split("/")
        e = int(ep[2:])
        run = RUNS[key]
        g = T[(T.run == run) & (T.ep == e)]
        pr = PE[PE.ep == f"{run[16:]}/ep{e}"].iloc[0]
        s0 = g.state_shoulder_pan.values[0]
        res = float(pr.pe) - s0
        A = Z[f"{key}_{ep}_c0__U256"][:, :, 0]
        sel = g[g.chunk_id == 0]
        Le = sel.raw_shoulder_pan.values[sel.chunk_idx.values.astype(int) == 29]
        r = dict(ep=f"{key}/{ep}", resid=res, n=len(A), logged_idx29=float(Le[0]) if len(Le) else np.nan)
        for idx in (29, 49):
            f = (A[:, idx] - s0) / res
            r.update({f"f{idx}_p10": np.percentile(f, 10), f"f{idx}_p50": np.median(f), f"f{idx}_p90": np.percentile(f, 90), f"f{idx}_mean": f.mean(),
                      f"f{idx}_lt10": (f < 0.1).mean(), f"f{idx}_10_50": ((f >= 0.1) & (f < 0.5)).mean(), f"f{idx}_ge50": (f >= 0.5).mean(),
                      f"f{idx}_ge75": (f >= 0.75).mean()})
        if len(Le):
            r["logged_f29"] = (Le[0] - s0) / res
            r["logged_rank_in_u256"] = rank(Le[0], A[:, 29])
        rows.append(r)
    U = pd.DataFrame(rows)
    U.to_csv(TAB / "p06d_chunk0_u256.csv", index=False)

    srows = []
    for case in C[C.cond != "U256"].case.unique():
        key, ep, ck = case.split("/")
        e, k = int(ep[2:]), int(ck[1:])
        run = RUNS[key]
        pr = PE[PE.ep == f"{run[16:]}/ep{e}"].iloc[0]
        sg = np.sign(pr.need)
        cur = Z[f"{key}_{ep}_{ck}__logged_cur"]
        prev = Z[f"{key}_{ep}_{ck}__logged_prev"]
        ref = prev[-1, 1]
        i0, i1 = int(cur[0, 0]), int(cur[-1, 0])
        # 기록값
        Lseg = cur[:, 1]
        srows.append(dict(case=case, cond="logged", n=1, i0=i0, i1=i1, ref=ref, seam_p50=sg * (Lseg[0] - ref),
                          back_p50=max(0.0, -sg * (Lseg - ref).min() if sg > 0 else sg * (Lseg - ref).max() * -1)))
        for cond in C[(C.case == case)].cond:
            A = Z[f"{key}_{ep}_{ck}__{cond}"][:, :, 0]
            seam = sg * (A[:, i0] - ref)
            back = np.maximum(0.0, -(sg * (A[:, i0:i1 + 1] - ref)).min(1))
            srows.append(dict(case=case, cond=cond, n=len(A), i0=i0, i1=i1, ref=ref,
                              seam_p10=np.percentile(seam, 10), seam_p50=np.median(seam), seam_p90=np.percentile(seam, 90),
                              back_p10=np.percentile(back, 10), back_p50=np.median(back), back_p90=np.percentile(back, 90),
                              back_ge10=(back >= 10).mean()))
    S = pd.DataFrame(srows)
    # 기록값 back 재계산 (부호 처리 명확히)
    for i, r in S[S.cond == "logged"].iterrows():
        key, ep, ck = r.case.split("/")
        cur = Z[f"{key}_{ep}_{ck}__logged_cur"]
        run = RUNS[key]
        sg = np.sign(PE[PE.ep == f"{run[16:]}/ep{int(ep[2:])}"].iloc[0].need)
        S.loc[i, "back_p50"] = max(0.0, -(sg * (cur[:, 1] - r.ref)).min())
    S.to_csv(TAB / "p06d_seams.csv", index=False)
    pd.set_option("display.width", 250, "display.max_columns", 30)
    print(U.round(3).to_string(index=False))
    print(S.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
