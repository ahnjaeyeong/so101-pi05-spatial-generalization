"""q03b q03 짝 비교를 02 문서 상태 유형 (T1–T6) 으로 묶음 (CPU).
출력: tables/q03b_type_pairs.csv
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python q03b_type_pairs.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

TB = Path.home() / "so101_runs/main_k8/d2/pan_inference_diagnostic/offline_pan_reversal_filter_off/tables"
import sys
sys.path.insert(0, str(Path(__file__).parent))
from q02c_report_table import typ  # noqa: E402


def main():
    P = pd.read_csv(TB / "q03_pairs.csv")
    S = pd.read_csv(TB / "q02_states.csv").set_index("key")
    for c in ("before_first_close", "has_prefix", "front_vis"):
        P[c] = S.loc[P.key, c].values
    P["type"] = P.apply(typ, axis=1)
    rows = []
    for t, g in P.groupby("type"):
        n = g.n.sum()
        r = dict(type=t, n_eps=g.tag.nunique(), n_states=len(g), n_pairs=int(n))
        for k in ("both", "U_only", "G_only", "neither", "U_toward_by29", "G_toward_by29", "U_toward_by19", "G_toward_by19"):
            r[k] = int(g[k].sum()) if k in g and g[k].notna().any() else np.nan
        r["along_GminusU_med"] = float(g.along_GminusU_med.median())
        r["absdiff_a9_med"] = float(g.absdiff_a9_med.median())
        r["absdiff_a29_med"] = float(g.absdiff_a29_med.median())
        r["absdiff_a49_med"] = float(g.absdiff_a49_med.median())
        r["delay_G_minus_U_med"] = float(g.delay_G_minus_U_med.median()) if g.delay_G_minus_U_med.notna().any() else np.nan
        rows.append(r)
    D = pd.DataFrame(rows)
    D.to_csv(TB / "q03b_type_pairs.csv", index=False)
    pd.set_option("display.width", 250)
    print(D.round(2).to_string())


if __name__ == "__main__":
    main()
