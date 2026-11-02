"""s1_frames.parquet (설계 가중) → weights/weights_<실험>.npy (d2 데이터셋 전역 index 순서, int32) + weights/manifest.json.

d2 데이터셋은 읽기만 한다. H (heldout) 데이터는 읽지 않는다 — 가중은 d2 256 판의 사람 라벨 밀도에서만 나온다.
사용: PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python make_weights.py
"""
import glob
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

D = Path(__file__).parent
DS = Path.home() / "so101_runs/main_k8/d2/dataset"
ARMS = ("A0", "A1", "A2", "A2r")          # 이번 실행 대상 (A3 · A3c12 는 보류)


def main():
    F = pd.read_parquet(D / "s1_frames.parquet")
    idx = pd.concat([pd.read_parquet(f, columns=["index", "episode_index", "frame_index"])
                     for f in sorted(glob.glob(str(DS / "data/*/*.parquet")))])
    m = F.merge(idx, left_on=["ep", "frame"], right_on=["episode_index", "frame_index"], how="left", validate="1:1")
    assert m["index"].notna().all() and len(m) == len(idx) == idx["index"].nunique()
    n = int(idx["index"].max()) + 1
    out = D / "weights"
    out.mkdir(exist_ok=True)
    man = dict(dataset=str(DS), n_frames=n, source="s1_frames.parquet", arms={})
    for a in ARMS:
        w = np.zeros(n, np.int32)
        w[m["index"].astype(int).values] = m[f"w_{a}"].astype(int).values
        assert (w >= 1).all()
        p = out / f"weights_{a}.npy"
        np.save(p, w)
        man["arms"][a] = dict(file=p.name, sha256=hashlib.sha256(p.read_bytes()).hexdigest(), sum=int(w.sum()),
                              max=int(w.max()), hist={int(k): int(v) for k, v in zip(*np.unique(w, return_counts=True))})
    json.dump(man, open(out / "manifest.json", "w"), indent=1)
    print(json.dumps(man, indent=1))


if __name__ == "__main__":
    main()
