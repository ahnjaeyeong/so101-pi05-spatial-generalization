#!/home/user/so101-env/bin/python
"""b12 결과 요약 (CPU) → 화면 · ../data/cross_summary.json. 값 = 바깥 · 높이 cm, 평균 [판 단위 bootstrap 95 %] · 중앙.
칸 = 맥락 (R/H) × 배경 (R/H) × 큐브 (R/H). 주효과: 큐브 (H − R, 배경 평균) · 배경 (H − R, 큐브 평균). 전체 / 실물 큐브가 영상 끝에 안 걸린 장면."""
import json
import os

import numpy as np

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")


def cb(v, g, seed=0, n=2000):
    v, g = np.asarray(v, float), np.asarray(g)
    if len(v) < 2:
        return None
    G = sorted(set(g))
    r = np.random.default_rng(seed)
    bs = [np.mean(np.concatenate([v[g == x] for x in r.choice(G, len(G))])) for _ in range(n)]
    return [float(v.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5)), float(np.median(v)), int(len(v)), int(len(G))]


def main():
    J = json.load(open(os.path.join(D, "cross.json")))
    M, R = J["scenes"], J["res"]
    out = {}
    f = lambda t: "—" if t is None else f"{t[0]:+.2f} [{t[1]:+.2f}, {t[2]:+.2f}] 중앙 {t[3]:+.2f} (n {t[4]} · 판 {t[5]})"
    for si, sn in ((0, "h"), (1, "49")):
        for subn, idx in (("all", list(range(len(M)))), ("r_noedge", [i for i, m in enumerate(M) if not m["r_edge"]])):
            g = [M[i]["ep"] for i in idx]
            for comp, cn in ((0, "out"), (2, "up")):
                o = {}
                for ctx in "RH":
                    V = lambda b, c: np.array([R[i][f"{ctx}_bg{b}_cube{c}"][si][comp] for i in idx])
                    for b in "RH":
                        for c in "RH":
                            o[f"{ctx}_bg{b}_cube{c}"] = cb(V(b, c), g)
                    o[f"{ctx}_cube_H-R"] = cb((V("R", "H") - V("R", "R") + V("H", "H") - V("H", "R")) / 2, g)
                    o[f"{ctx}_bg_H-R"] = cb((V("H", "R") - V("R", "R") + V("H", "H") - V("R", "H")) / 2, g)
                    o[f"{ctx}_interaction"] = cb((V("H", "H") - V("H", "R")) - (V("R", "H") - V("R", "R")), g)
                out[f"{sn}_{subn}_{cn}"] = o
    json.dump(out, open(os.path.join(D, "cross_summary.json"), "w"), ensure_ascii=False, indent=1)
    for key, o in out.items():
        print(f"\n== {key}")
        for ctx in "RH":
            print(f"  맥락 {ctx}: " + " | ".join(f"bg{b}·cube{c} {o[f'{ctx}_bg{b}_cube{c}'][0]:+.2f}" for b in "RH" for c in "RH" if o[f"{ctx}_bg{b}_cube{c}"]))
            print(f"     큐브 H−R {f(o[f'{ctx}_cube_H-R'])}")
            print(f"     배경 H−R {f(o[f'{ctx}_bg_H-R'])}")


if __name__ == "__main__":
    main()
