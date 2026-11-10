#!/home/user/so101-env/bin/python
"""b8 결과 요약 (CPU) → 화면 · ../data/momentum_source_summary.json.
값 = 예측 끝 이동 (cm, 바깥 · 옆 · 높이), 장면 평균, 판 (실물 8 판 / 사람 40 판) 단위 bootstrap 95 %.
A: 실물 np · pf · still, 차 pf − np · still − np · pf − still; 사람 np · pfh.
B: 2×2×2 (front · wrist · state, R/H) 칸 평균과 주효과 (H − R, 다른 두 요인 평균)."""
import json
import os

import numpy as np

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")


def cboot(vals, groups, seed=0, n=2000):
    vals, groups = np.asarray(vals, float), np.asarray(groups)
    G = sorted(set(groups))
    r = np.random.default_rng(seed)
    bs = []
    for _ in range(n):
        pick = r.choice(G, len(G))
        bs.append(np.mean(np.concatenate([vals[groups == g] for g in pick]), 0))
    return [np.mean(vals, 0).tolist(), np.percentile(bs, 2.5, 0).tolist(), np.percentile(bs, 97.5, 0).tolist()]


def main():
    J = json.load(open(os.path.join(D, "momentum_source.json")))
    M, Rs = J["scenes"], J["res"]
    out = {}
    for si, sn in ((0, "h"), (1, "49")):
        o = {}
        rob = [i for i, m in enumerate(M) if m["kind"] == "robot"]
        hum = [i for i, m in enumerate(M) if m["kind"] == "human"]
        g_r = [M[i]["ep"] for i in rob]
        g_h = [M[i]["ep"] for i in hum]
        V = lambda key, idx: np.array([Rs[i][key][si] for i in idx])
        for k in ("np", "pf", "still"):
            o[f"robot_{k}"] = cboot(V(k, rob), g_r)
        o["robot_pf-np"] = cboot(V("pf", rob) - V("np", rob), g_r)
        o["robot_still-np"] = cboot(V("still", rob) - V("np", rob), g_r)
        o["robot_pf-still"] = cboot(V("pf", rob) - V("still", rob), g_r)
        o["human_np"] = cboot(V("np", hum), g_h)
        o["human_pfh"] = cboot(V("pfh", hum), g_h)
        o["human_pfh-np"] = cboot(V("pfh", hum) - V("np", hum), g_h)
        cells = {f"{f}{w}{s}": V(f"B_{f}{w}{s}", rob) for f in "RH" for w in "RH" for s in "RH"}
        o["B_cells"] = {c: cboot(v, g_r) for c, v in cells.items()}
        for name, pos in (("front", 0), ("wrist", 1), ("state", 2)):
            d = np.mean([cells[c] - cells[c[:pos] + "R" + c[pos + 1:]] for c in cells if c[pos] == "H"], 0)
            o[f"B_main_{name}"] = cboot(d, g_r)
        # 판별 (실물) np · pf · still 바깥
        o["by_lab"] = {}
        for lab in sorted({M[i]["lab"] for i in rob}):
            idx = [i for i in rob if M[i]["lab"] == lab]
            o["by_lab"][lab] = {k: float(V(k, idx)[:, 0].mean()) for k in ("np", "pf", "still")} | {"n": len(idx)}
        out[sn] = o
    rob = [i for i, m in enumerate(M) if m["kind"] == "robot"]
    pm = np.array([Rs[i]["prefix_move"] for i in rob])
    out["prefix_move_out_median"] = float(np.median(pm[:, 0]))
    out["human_dist_cm_median"] = float(np.median([M[i]["human_dist_cm"] for i in rob]))
    out["centered_frac"] = float(np.mean([M[i]["centered"] for i in rob]))
    out["n_robot"], out["n_human"] = len(rob), len(M) - len(rob)
    json.dump(out, open(os.path.join(D, "momentum_source_summary.json"), "w"), ensure_ascii=False, indent=1)
    f = lambda t: f"바깥 {t[0][0]:+.2f} [{t[1][0]:+.2f}, {t[2][0]:+.2f}] · 옆 {t[0][1]:+.2f} · 높이 {t[0][2]:+.2f} [{t[1][2]:+.2f}, {t[2][2]:+.2f}]"
    print(f"실물 {out['n_robot']} 장면 (손목 중심 맞춤 {out['centered_frac']:.2f}) · 사람 {out['n_human']} · 짝 사람 판 거리 중앙 {out['human_dist_cm_median']:.1f} cm · "
          f"저장 prefix 팔 이동 (바깥) 중앙 {out['prefix_move_out_median']:+.2f} cm")
    for sn in ("h", "49"):
        o = out[sn]
        print(f"\n[시점 {sn}]")
        for k in ("robot_np", "robot_pf", "robot_still", "robot_pf-np", "robot_still-np", "robot_pf-still", "human_np", "human_pfh", "human_pfh-np"):
            print(f"  {k:16s} {f(o[k])}")
        for k in ("front", "wrist", "state"):
            print(f"  B 주효과 {k:6s} (사람 것으로 바꿈 − 실물) {f(o['B_main_' + k])}")
        print("  B 칸 (front wrist state):", " ".join(f"{c} {v[0][0]:+.2f}" for c, v in o["B_cells"].items()))
        print("  판별 바깥 np/pf/still:", " ".join(f"{l} {v['np']:+.2f}/{v['pf']:+.2f}/{v['still']:+.2f}" for l, v in o["by_lab"].items()))


if __name__ == "__main__":
    main()
