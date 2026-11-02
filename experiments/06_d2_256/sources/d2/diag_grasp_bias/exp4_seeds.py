"""실험 4: 같은 관측에서 action sampling noise 만 64개로 바꿔 분산을 본다 (d2 20k, step 5 와 10 둘 다, prefix 공유).

관측 묶음:
  eval_start  평가 5판의 움직이기 시작한 프레임 (probe_eval 과 같은 프레임)
  ep1_drift   try3_filt ep1 의 t = 5, 10, 14, 18, 22, 26, 28.5 s 프레임 (흐름 구간)
  grid_novel  합성 grid 중 학습 큐브에서 2–4 cm 떨어진 8곳 (exp1/grid_info + build_grid 와 같은 영상)
  train_start 학습 판 8편 (K 4 · R 4) 의 m 프레임
  train_pre   같은 8편의 첫 파지 30 프레임 전
출력: exp4/seeds.npz (s5, s10: noise × N × 50 × 6), exp4/rows.csv
사용: nice -n 19 env PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python exp4_seeds.py
"""
import math

import numpy as np
import pandas as pd

import common as C
import probe_core as PC
from policy_probe import load_obs, move_start

OUT = C.OUT / "exp4"
EVAL = C.D2 / "eval/rollouts"


def main():
    OUT.mkdir(exist_ok=True)
    T = pd.read_csv(C.OUT / "grasp_train.csv")
    data = C.load_parquet(C.D2 / "dataset")
    cache = {}
    rows, F, W, S = [], [], [], []

    def add(meta, f, w, s):
        rows.append(meta)
        F.append(f)
        W.append(w)
        S.append(s)

    E0 = pd.read_csv(C.OUT / "grasp_eval.csv")
    for run in sorted(p.parent.name for p in EVAL.glob("*/dataset")):
        ds = EVAL / run / "dataset"
        ed = C.load_parquet(ds)
        for e, (s, a) in ed.items():
            me = move_start(a)
            fr, wr = load_obs(ds, [(e, me)], cache)
            ev = E0[(E0.run == run) & (E0.ep == e)].iloc[0]
            add(dict(set="eval_start", run=run, ep=e, frame=me, pan_exp=C.pan_expected(ev.start_x, ev.start_y)), fr[0], wr[0], s[me])
            if run.endswith("try3_filt") and e == 1:
                for t in (5, 10, 14, 18, 22, 26, 28.5):
                    f = int(t * 30)
                    fr, wr = load_obs(ds, [(e, f)], cache)
                    add(dict(set="ep1_drift", run=run, ep=e, frame=f, t=t, pan_exp=C.pan_expected(ev.start_x, ev.start_y),
                             state_pan=s[f, 0]), fr[0], wr[0], s[f])
    t1 = [e for e in range(256) if T.loc[e, "task"] == "T1"]
    m = {e: move_start(data[e][1]) for e in t1}
    Fs, Ws = load_obs(C.D2 / "dataset", [(e, m[e]) for e in t1], cache)
    Ss = np.stack([data[e][0][m[e]] for e in t1])
    Fg, Wg, Sg, info = PC.build_grid(T.loc[t1].reset_index(drop=True), Fs, Ws, Ss)
    G = pd.DataFrame(info)
    G["nearest_train_cm"] = [float(np.min(np.hypot(T.cube_x - x, T.cube_y - y))) for x, y in zip(G.x, G.y)]
    K = C.load_known()
    cand = G[(G.nearest_train_cm >= 2) & (G.nearest_train_cm <= 4)]
    pick = cand.iloc[np.linspace(0, len(cand) - 1, 8).astype(int)]
    for i, r in pick.iterrows():
        nk = min(K, key=lambda k: math.hypot(r.x - K[k][0], r.y - K[k][1]))
        add(dict(set="grid_novel", x=r.x, y=r.y, pan_exp=C.pan_expected(r.x, r.y), nearest_train_cm=r.nearest_train_cm,
                 K_pan_exp=C.pan_expected(*K[nk]), nearest_K=nk), Fg[i], Wg[i], Sg[i])
    for e in (3, 20, 40, 60, 70, 85, 100, 120):
        s, a = data[e]
        for st, f in (("train_start", m[e]), ("train_pre", int(T.loc[e, "grasp_f"]) - 30)):
            fr, wr = load_obs(C.D2 / "dataset", [(e, f)], cache)
            add(dict(set=st, ep=e, group=T.loc[e, "group"], frame=f, pan_exp=T.loc[e, "pan_exp"], human_pan=T.loc[e, "s_shoulder_pan"]),
                fr[0], wr[0], s[f])
    E = PC.Engine("020000", n_noise=64)
    ch = E.chunks(np.stack(F), np.stack(W), np.stack(S), steps=(5, 10))
    np.savez_compressed(OUT / "seeds.npz", s5=ch[5].astype(np.float32), s10=ch[10].astype(np.float32))
    pd.DataFrame(rows).to_csv(OUT / "rows.csv", index=False)
    print(f"obs {len(rows)} gpu_busy_s {E.gpu_busy_s:.0f}", flush=True)


if __name__ == "__main__":
    main()
