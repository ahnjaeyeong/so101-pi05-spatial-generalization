"""e00 기준선 (d2 020000) 재추론 배열을 기존 결과에서 옮겨 e01 형식으로 만든다 (CPU, 원본 읽기만).

근거: e02 지표 코드가 기존 q02c 표 (T1 · T3 · T4) 를 정확히 재현함을 확인 (2026-11-04), 그리고 e01 을 d2 020000 으로 짧게 돌려
      (--limit) 기존 배열과 차 0 인지 확인한다 (eval/raw/d2_020000_repro/meta.json repro). 같은 엔진 · 같은 noise bank 이므로
      기준선은 다시 계산하지 않고 기존 값을 쓴다.
  q02  : offline_pan_reversal_filter_off/tables/q02_seed_pan.npz — pan 은 float32 (U_/G_), 나머지 관절은 float16 (Ufull/Gfull).
         앞 N seed 만 (새 체크포인트와 같은 noise 와 짝). R1 지표는 pan 만 쓴다.
  vd_b : vd_20261103_01/tables/b_raw/<key>.npz G_A_base · U_A_base (16 seed, float32), obs_state
  vd_h : vd_20261103_01/tables/h_raw/<key>.npz G_A_base (16 seed)
  demo : 기존 결과 없음 → e01 --sets demo 로 GPU 계산 (eval/raw/d2_020000_demo) 후 이 폴더로 복사
사용: PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python scripts/e00_base_from_existing.py --n 32
"""
import argparse
import json
import shutil
import time
from pathlib import Path

import numpy as np
import pandas as pd

HOME = Path.home()
D2 = HOME / "so101_runs/main_k8/d2"
RF = D2 / "recovery_ft"
OPR = D2 / "pan_inference_diagnostic/offline_pan_reversal_filter_off"
VD = D2 / "visual_dependency/vd_20261103_01"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=32)
    a = ap.parse_args()
    out = RF / "eval/raw/d2_020000"
    if out.exists():
        raise SystemExit(f"{out} 이미 있음")
    out.mkdir(parents=True)
    Z = np.load(OPR / "tables/q02_seed_pan.npz")
    st = {}
    for k in Z.files:
        for src in ("U", "G"):
            if k.startswith(f"{src}full_"):
                key = k[len(src) + 5:]
                A = Z[k][:a.n].astype(np.float32)
                A[:, :, 0] = Z[f"{src}_{key}"][:a.n].astype(np.float32)
                st[f"{src}_{key}"] = A
    np.savez_compressed(out / "q02.npz", **st)
    shutil.copyfile(OPR / "tables/q02_states.csv", out / "q02_states.csv")
    for kind, nm in (("b", "vd_b"), ("h", "vd_h")):
        T = pd.read_csv(VD / f"tables/{kind}_states.csv")
        st = {}
        for r in T.itertuples():
            z = np.load(VD / f"tables/{kind}_raw/{r.key}.npz")
            st[f"G_{r.key}"] = z["G_A_base"].astype(np.float32)
            st[f"S_{r.key}"] = z["obs_state"].astype(np.float32)
            if kind == "b":
                st[f"U_{r.key}"] = z["U_A_base"].astype(np.float32)
        np.savez_compressed(out / f"{nm}.npz", **st)
    dm = RF / "eval/raw/d2_020000_demo"
    for f in ("demo.npz", "demo_states.csv"):
        shutil.copyfile(dm / f, out / f)
    meta = dict(tag="d2_020000", source="기존 재추론 결과 (q02 · vd_20261103_01) + e01 demo", n_noise_q02=a.n, n_noise_vd=16,
                created=time.strftime("%F %T"), demo_from=str(dm), repro_check=str(RF / "eval/raw/d2_020000_repro/meta.json"))
    (out / "meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    print("BASE_OK", out)


if __name__ == "__main__":
    main()
