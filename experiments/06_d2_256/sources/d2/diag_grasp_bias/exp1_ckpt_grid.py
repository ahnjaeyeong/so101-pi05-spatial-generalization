"""실험 1: d2 체크포인트 5k/10k/15k/20k 에서 같은 관측으로 start · pregrasp · grid 프로브 (고정 noise 4개, step 5).

출력: exp1/ckpt_<step>.npz — start_pan (noise,256,50), pregrasp (noise,256,50,6), grid_pan (noise,G,50), grid_info.csv, meta
분석은 exp_analyze.py.
사용: nice -n 19 env PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python exp1_ckpt_grid.py [--steps 005000,010000,015000,020000]
"""
import argparse
import gc
import json
import time

import numpy as np
import pandas as pd

import common as C
import probe_core as PC
from policy_probe import load_obs, move_start

OUT = C.OUT / "exp1"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", default="005000,010000,015000,020000")
    ap.add_argument("--n_noise", type=int, default=4)
    args = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    T = pd.read_csv(C.OUT / "grasp_train.csv")
    data = C.load_parquet(C.D2 / "dataset")
    cache = {}
    eps = list(range(256))
    m = [move_start(data[e][1]) for e in eps]
    pg = [max(0, int(T.loc[e, "grasp_f"]) - 30) for e in eps]
    t0 = time.time()
    Fs, Ws = load_obs(C.D2 / "dataset", list(zip(eps, m)), cache)
    Ss = np.stack([data[e][0][m[i]] for i, e in enumerate(eps)])
    Fp, Wp = load_obs(C.D2 / "dataset", list(zip(eps, pg)), cache)
    Sp = np.stack([data[e][0][pg[i]] for i, e in enumerate(eps)])
    t1 = [i for i in eps if T.loc[i, "task"] == "T1"]
    Fg, Wg, Sg, info = PC.build_grid(T.loc[t1].reset_index(drop=True), Fs[t1], Ws[t1], Ss[t1])
    pd.DataFrame(info).to_csv(OUT / "grid_info.csv", index=False)
    print(f"obs ready {time.time() - t0:.0f}s  grid {len(info)}", flush=True)
    for step in args.steps.split(","):
        ts = time.time()
        E = PC.Engine(step, n_noise=args.n_noise)
        load_s = time.time() - ts
        st = E.chunks(Fs, Ws, Ss)[5]
        pr = E.chunks(Fp, Wp, Sp)[5]
        gr = E.chunks(Fg, Wg, Sg)[5]
        np.savez_compressed(OUT / f"ckpt_{step}.npz", start_pan=st[..., 0], start_all=st[:, :, 49, :], pregrasp=pr,
                            grid_pan=gr[..., 0], m=np.array(m), pg=np.array(pg))
        meta = dict(step=step, load_s=load_s, gpu_busy_s=E.gpu_busy_s, wall_s=time.time() - ts, n_noise=args.n_noise)
        json.dump(meta, open(OUT / f"ckpt_{step}.json", "w"), indent=1)
        print(json.dumps(meta), flush=True)
        del E
        gc.collect()
        import torch
        torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
