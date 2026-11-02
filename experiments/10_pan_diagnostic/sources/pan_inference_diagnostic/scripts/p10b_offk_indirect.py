"""p10b off-K 좌표의 간접 점검 (읽기만, CPU). **검증이 아니다** — off-K 자리에는 좌표 정답이 없다.

학습 R 판 (임의 배치, 계획 좌표 없음) 에서 사람 첫 파지 pan − pe(사진 좌표) 의 산포를 '가장 가까운 K 까지 거리' 구간별로 본다.
off-K 에서 좌표 역산이 크게 틀리면 이 잔차가 거리와 함께 커질 것이다. 같은 크기면 '큰 오차의 흔적이 없다' 까지만 말할 수 있다.
  - 사람 파지 pan 자체의 산포 (≈ 2°) 가 섞여 있어 1 cm 이하 좌표 오차 (≈ 2–4°/cm × …) 는 이 방법으로 가려내기 어렵다.
  - pe 의 베이스 · 오프셋은 이 256 편 (R 포함) 으로 맞춘 값이다 (in-sample).
입력 tables/p10_frames.csv (p10_coord_validation.py)
출력 tables/p10b_offk_indirect.csv, p10b_offk_indirect.json
사용: PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python p10b_offk_indirect.py
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import cube_coords as CC  # noqa: E402

TAB = CC.D2 / "pan_inference_diagnostic/tables"
F = pd.read_csv(TAB / "p10_frames.csv")
F = F[(F.det_n_blobs > 0) & F.pan_close.notna()].copy()
F["pe"] = [CC.pe(x, y) for x, y in zip(F.det_x, F.det_y)]
F["resid"] = F.pan_close - F.pe
F["dist_K"] = [min(math.hypot(x - kx, y - ky) for kx, ky in CC.ac.KNOWN.values()) for x, y in zip(F.det_x, F.det_y)]
F["bin"] = pd.cut(F.dist_K, [0, 1.5, 3, 6, 100], right=False, labels=["0-1.5", "1.5-3", "3-6", ">=6"])
G = F.groupby(["mode", "bin"], observed=True).resid.agg(n="size", mean="mean", sd="std", abs_p90=lambda v: v.abs().quantile(.9)).reset_index()
G.to_csv(TAB / "p10b_offk_indirect.csv", index=False)
R = F[F["mode"] == "R"]
S = {"note": "간접 점검, 검증 아님 (off-K 좌표 정답 없음). 잔차 = 사람 첫 파지 pan − pe(사진 좌표)",
     "R_corr_absresid_distK": float(np.corrcoef(R.resid.abs(), R.dist_K)[0, 1]),
     "R_dist_K_range": [float(R.dist_K.min()), float(R.dist_K.max())],
     "table": G.round(3).to_dict("records")}
json.dump(S, open(TAB / "p10b_offk_indirect.json", "w"), indent=1, ensure_ascii=False)
print(G.round(2).to_string(index=False))
print(json.dumps({k: v for k, v in S.items() if k != "table"}, indent=1, ensure_ascii=False))
