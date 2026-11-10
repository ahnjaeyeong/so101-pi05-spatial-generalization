#!/home/user/so101-env/bin/python
"""b10 결과 요약 (CPU) → 화면 · ../data/height_summary.json. 값 = 바깥 · 높이 cm (적용 구간 끝 / 49), 평균 [판 단위 bootstrap 95 %] · 중앙.
T1 실물: O · Cc · Zc, 차 Cc − O (큐브만 중심으로), Zc − Cc (큐브만 크기 1 로) — 전체 / edge 아님 / edge 아님 · size < 0.9.
T2 사람: 닫기 전 프레임 (10 · 30 · 60 · 90) 별 size · O · Cc · Zc, 차 Zc − Cc; size 구간별 (≥0.95, 0.8–0.95, <0.8) Cc."""
import json
import os

import numpy as np

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")


def cb(v, g, seed=0, n=2000):
    v, g = np.asarray(v, float), np.asarray(g)
    if len(v) == 0:
        return None
    G = sorted(set(g))
    r = np.random.default_rng(seed)
    bs = [np.mean(np.concatenate([v[g == x] for x in r.choice(G, len(G))])) for _ in range(n)]
    return [float(v.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5)), float(np.median(v)), int(len(v))]


def main():
    J = json.load(open(os.path.join(D, "height.json")))
    M, R = J["scenes"], J["res"]
    out = {}
    fmt = lambda t: "—" if t is None else f"{t[0]:+.2f} [{t[1]:+.2f}, {t[2]:+.2f}] 중앙 {t[3]:+.2f} (n {t[4]})"
    for si, sn in ((0, "h"), (1, "49")):
        o = {}
        for comp, cn in ((0, "out"), (2, "up")):
            val = lambda i, k: R[i][k][si][comp]
            rob = [i for i, m in enumerate(M) if m["kind"] == "robot"]
            for subn, sub in (("all", rob), ("noedge", [i for i in rob if not M[i]["edge"]]),
                              ("noedge_small", [i for i in rob if not M[i]["edge"] and M[i]["size"] < 0.9])):
                g = [M[i]["ep"] for i in sub]
                for k in ("O", "Cc", "Zc"):
                    o[f"robot_{subn}_{k}_{cn}"] = cb([val(i, k) for i in sub], g)
                o[f"robot_{subn}_Cc-O_{cn}"] = cb([val(i, "Cc") - val(i, "O") for i in sub], g)
                o[f"robot_{subn}_Zc-Cc_{cn}"] = cb([val(i, "Zc") - val(i, "Cc") for i in sub], g)
            hum = [i for i, m in enumerate(M) if m["kind"] == "human"]
            for b in J["back"]:
                sub = [i for i in hum if M[i]["back"] == b]
                g = [M[i]["ep"] for i in sub]
                o[f"human_b{b}_size_med"] = float(np.median([M[i]["size"] for i in sub])) if sub else None
                for k in ("O", "Cc", "Zc"):
                    o[f"human_b{b}_{k}_{cn}"] = cb([val(i, k) for i in sub], g)
                o[f"human_b{b}_Zc-Cc_{cn}"] = cb([val(i, "Zc") - val(i, "Cc") for i in sub], g)
            for lo, hi, nm in ((0.95, 9, "ge095"), (0.8, 0.95, "080_095"), (0, 0.8, "lt080")):
                for kind in ("human", "robot"):
                    sub = [i for i, m in enumerate(M) if m["kind"] == kind and lo <= m["size"] < hi and not m["edge"]]
                    o[f"{kind}_size{nm}_Cc_{cn}"] = cb([val(i, "Cc") for i in sub], [M[i]["ep"] for i in sub])
                    o[f"{kind}_size{nm}_Zc-Cc_{cn}"] = cb([val(i, "Zc") - val(i, "Cc") for i in sub], [M[i]["ep"] for i in sub])
        out[sn] = o
    json.dump(out, open(os.path.join(D, "height_summary.json"), "w"), ensure_ascii=False, indent=1)
    for sn in ("h", "49"):
        o = out[sn]
        print(f"\n===== 시점 {sn}")
        for cn in ("out", "up"):
            print(f"--- {'바깥' if cn == 'out' else '높이'}")
            for subn in ("all", "noedge", "noedge_small"):
                print(f"  실물 {subn:12s} O {fmt(o[f'robot_{subn}_O_{cn}'])} | Cc {fmt(o[f'robot_{subn}_Cc_{cn}'])} | Zc−Cc {fmt(o[f'robot_{subn}_Zc-Cc_{cn}'])}")
            for b in (10, 30, 60, 90):
                if o.get(f"human_b{b}_O_{cn}"):
                    print(f"  사람 {b:2d}프레임 전 size {o[f'human_b{b}_size_med']:.2f} O {fmt(o[f'human_b{b}_O_{cn}'])} | Cc {fmt(o[f'human_b{b}_Cc_{cn}'])} | Zc−Cc {fmt(o[f'human_b{b}_Zc-Cc_{cn}'])}")
            for nm in ("ge095", "080_095", "lt080"):
                print(f"  size {nm:8s} 사람 Cc {fmt(o[f'human_size{nm}_Cc_{cn}'])} · Zc−Cc {fmt(o[f'human_size{nm}_Zc-Cc_{cn}'])}")
                print(f"  size {nm:8s} 실물 Cc {fmt(o[f'robot_size{nm}_Cc_{cn}'])} · Zc−Cc {fmt(o[f'robot_size{nm}_Zc-Cc_{cn}'])}")


if __name__ == "__main__":
    main()
