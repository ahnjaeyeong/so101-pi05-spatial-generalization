#!/home/user/so101-env/bin/python
"""b6 결과 요약 (CPU) → 화면 · ../data/state_probe_summary.json.
k = (예측 끝 반지름 (+1 cm 상태) − (−1 cm 상태)) / (실제 바꾼 반지름 차). k≈0 절대 자리, k≈1 상대 이동.
닫기 비율: 상태 −1 · 0 · +1 cm 에서 chunk 안 닫기 비율."""
import json
import os

import numpy as np

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")


def ci(x, seed=0):
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    if not len(x):
        return [None, None, None]
    r = np.random.default_rng(seed)
    b = [np.mean(r.choice(x, len(x))) for _ in range(2000)]
    return [float(np.mean(x)), float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))]


def main():
    z = np.load(os.path.join(D, "state_probe.npz"))
    M = json.load(open(os.path.join(D, "state_probe.json")))["scenes"]
    ach = np.array([[a[0] for a in m["achieved"]] for m in M])        # (n, 3) 바꾼 반지름
    den = ach[:, 2] - ach[:, 0]
    kinds = np.array([m["kind"] for m in M])
    labs = np.array([m["lab"] for m in M])
    out = {}
    groups = [("human", kinds == "human"), ("robot", kinds == "robot")] + [(f"robot:{l}", labs == l) for l in sorted(set(labs[kinds == "robot"]))]
    for name, m in groups:
        o = {"n": int(m.sum())}
        for v in ("np_", "pf"):
            X = z[v][m]
            if np.all(np.isnan(X)):
                continue
            for si, sn in ((0, "h"), (1, "49")):
                k = (X[:, 2, si, 0] - X[:, 0, si, 0]) / den[m]
                kz = (X[:, 2, si, 1] - X[:, 0, si, 1]) / den[m]   # 높이 끝 변화 / 반지름 변화
                o[f"{v}{sn}"] = {"k_radial": ci(k), "k_height_per_cm": ci(kz)}
            g = z["g_np" if v == "np_" else "g_pf"][m]
            o[f"{v}close"] = [float(np.nanmean(g[:, j])) for j in range(3)]
        out[name] = o
    json.dump(out, open(os.path.join(D, "state_probe_summary.json"), "w"), ensure_ascii=False, indent=1)
    f = lambda t: "None" if t[0] is None else f"{t[0]:+.2f} [{t[1]:+.2f}, {t[2]:+.2f}]"
    for name, o in out.items():
        line = f"{name} n{o['n']}: "
        for v in ("np_", "pf"):
            if f"{v}h" in o:
                line += f"| {v} k(적용끝) {f(o[f'{v}h']['k_radial'])} k(49) {f(o[f'{v}49']['k_radial'])} 닫기 −1/0/+1 cm " + "/".join(f"{x:.2f}" for x in o[f"{v}close"]) + " "
        print(line)


if __name__ == "__main__":
    main()
