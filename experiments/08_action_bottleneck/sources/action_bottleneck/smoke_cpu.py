"""CPU 시험 (GPU 실행 전): ab_core.Engine 이 policy.predict_action_chunk 와 같은 값을 내는지, 가리기·기록이 동작하는지,
G1 편집 영상이 의도대로인지. 로봇·카메라 연결 없음. 출력: smoke/ (새 폴더).
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python smoke_cpu.py
"""
import json
import time

import numpy as np
import pandas as pd

import ab_core as A
import g1_roll_factorial as G1
from ab_core import C

OUT = A.AB / "smoke"


def main():
    OUT.mkdir(exist_ok=True)
    t0 = time.time()
    T = pd.read_csv(C.OUT / "grasp_train.csv")
    data = C.load_parquet(C.D2 / "dataset")
    bu, bv = A.ref_point_fit()
    skipped = []
    F, W, S, K, r = G1.build_ep(0, T, data, bu, bv, {}, skipped)
    R = pd.DataFrame(r)
    print("ep0 obs", len(R), "skipped", skipped, "conds", R.cond.nunique(), flush=True)
    want = ["F:base", "F:wu+", "W0", "KR:base", "KS:base", "RC:+15", "RI:+15"]
    sel = [int(R[(R.cond == c) & (R.phase == "t1.0") & (R.droll.isin([0.0, 15.0]) if c.startswith("F") else True)].index[0]) for c in want]
    sel.insert(1, int(R[(R.cond == "F:base") & (R.phase == "t1.0") & (R.droll == 15.0)].index[0]))
    import cv2
    tile = np.concatenate([np.concatenate([W[i] for i in sel[:4]], 1), np.concatenate([W[i] for i in sel[4:8]], 1)], 0)[::2, ::2]
    cv2.imwrite(str(OUT / "g1_edits_t1.0.jpg"), cv2.cvtColor(tile, cv2.COLOR_RGB2BGR))
    E = A.Engine("020000", device="cpu", n_noise=1)
    print(f"model loaded {time.time() - t0:.0f}s", flush=True)
    Fs, Ws, Ss, Ks = F[sel], W[sel], S[sel], [K[i] for i in sel]
    ch, hid, am, gr = E.chunks(Fs, Ws, Ss, knock=Ks, bs=4, capture=True)
    res = {"conds": [R.loc[i, "cond"] + f" d{R.loc[i, 'droll']:+.0f}" for i in sel]}
    # 같은 계산인지: knock 없는 첫 2 개를 predict_action_chunk 와 비교
    torch = E.torch
    E.policy.config.num_inference_steps = 5
    with torch.inference_mode():
        b = E.pre(E._batch(Fs[:2], Ws[:2], Ss[:2]))  # noqa: SLF001
        ref = E.post(E.policy.predict_action_chunk(b, noise=E.noise_bank[0][None].repeat(2, 1, 1))).float().numpy()
    res["max_abs_diff_vs_predict_action_chunk_deg"] = float(np.abs(ch[0, :2] - ref).max())
    base = ch[0, 0]
    tip = A.tip_fn()
    for k, i in enumerate(sel):
        d = ch[0, k] - base
        res[res["conds"][k]] = dict(max_abs_d_deg=float(np.abs(d).max()), d_pan_30=float(d[30, 0]), d_roll_30=float(d[30, 4]),
                                    tip30=tip(ch[0, k, 30, :5])[0].round(3).tolist())
    res["hidden_shape"] = list(hid.shape)
    res["hidden_finite"] = bool(np.isfinite(hid).all())
    res["attn_mass_layer0_first"] = am[0, 0].round(4).tolist()
    res["attn_mass_sum_check"] = am[:, :, :6].sum(-1).round(3).tolist()[0][:3]
    res["roll_tokens"] = [g["roll_tokens"] for g in gr]
    res["n_numbers"] = [g["n_numbers"] for g in gr]
    res["state_rolls"] = Ss[:, 4].round(2).tolist()
    res["wall_s"] = time.time() - t0
    json.dump(res, open(OUT / "smoke.json", "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
