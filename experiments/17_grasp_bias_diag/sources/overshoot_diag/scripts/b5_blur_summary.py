#!/home/user/so101-env/bin/python
"""b4 모션 블러 결과 요약 (CPU) → 화면 · ../data/blur_summary.json. 블러 − 원래: 끝 이동 (바깥 · 옆 · 높이 cm) · 닫기 비율 변화, 판 단위 bootstrap 95 %."""
import json
import os

import numpy as np

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")


def ci(x, seed=0):
    x = np.asarray(x, float)
    r = np.random.default_rng(seed)
    b = [np.mean(r.choice(x, len(x))) for _ in range(2000)]
    return [float(np.mean(x)), float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))]


def main():
    z = np.load(os.path.join(D, "blur.npz"))
    M = json.load(open(os.path.join(D, "blur.json")))["scenes"]
    P, G, conds = z["P"], z["G"], list(z["conds"])
    kinds = np.array([m["kind"] for m in M])
    out = {}
    for kind in ("human", "robot"):
        m = kinds == kind
        o = {"n": int(m.sum()), "close_orig": float(G[m, 0].mean())}
        for k, c in enumerate(conds[1:], 1):
            d = P[m, k] - P[m, 0]
            o[c] = {"d_out": ci(d[:, 0]), "d_side": ci(d[:, 1]), "d_up": ci(d[:, 2]), "abs_move_med": float(np.median(np.linalg.norm(d, axis=1))),
                    "close": float(G[m, k].mean())}
        out[kind] = o
        print(f"\n{kind} n{o['n']} 닫기 비율 원래 {o['close_orig']:.2f}")
        for c in conds[1:]:
            v = o[c]
            f = lambda t: f"{t[0]:+.3f} [{t[1]:+.3f}, {t[2]:+.3f}]"
            print(f"  {c}: 바깥 {f(v['d_out'])} · 옆 {f(v['d_side'])} · 높이 {f(v['d_up'])} cm · |이동 차| 중앙 {v['abs_move_med']:.3f} · 닫기 {v['close']:.2f}")
    json.dump(out, open(os.path.join(D, "blur_summary.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
