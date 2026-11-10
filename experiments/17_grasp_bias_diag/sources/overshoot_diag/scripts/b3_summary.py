#!/home/user/so101-env/bin/python
"""b2 평형점 결과 요약 (CPU) → ../data/equilibrium_summary.json, 화면.
장면마다: 손목 오차 e (= 지금 오차 + 옮긴 양) 에 대한 끝 이동 (u → 옆, v → 바깥) 직선 맞춤 → 기울기 (cm / 오차 단위), e = 0 (큐브가 프레임 중심) 에서의 이동 (cm),
평형점 e* = 이동 0 이 되는 e (기울기 부호가 '바로잡는 쪽' 이고 |기울기| ≥ 2 cm/단위 인 장면만)."""
import json
import os

import numpy as np

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")


def boot_med(x, n=2000, seed=0):
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    if len(x) < 3:
        return [float(np.median(x)) if len(x) else None, None, None]
    r = np.random.default_rng(seed)
    b = [np.median(r.choice(x, len(x))) for _ in range(n)]
    return [float(np.median(x)), float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))]


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="")
    ap.add_argument("--step", type=int, default=0, help="tag 결과: 0 = 적용 구간 끝 (실물 applied_delay+20, 사람 20), 1 = chunk 끝 (49)")
    a = ap.parse_args()
    z = np.load(os.path.join(D, f"equilibrium{a.tag}.npz"))
    M = json.load(open(os.path.join(D, f"equilibrium{a.tag}.json")))["scenes"]
    U, V = z["U"], z["V"]
    if U.ndim == 4:
        U, V = U[:, a.step], V[:, a.step]
    du_s, dv_s = z["u_px"] / 640.0, z["v_px"] / 480.0
    rows = []
    for i, m in enumerate(M):
        r = dict(m)
        for ax, Y, sh, obs, comp in (("u", U[i], du_s, m["du"], 1), ("v", V[i], dv_s, m["dv"], 0)):
            e = obs + sh
            y = Y[:, comp]
            g, c = np.polyfit(e, y, 1)
            r[f"{ax}_slope"] = float(g)
            r[f"{ax}_push0"] = float(c)          # e = 0 에서 이동 (cm)
            r[f"{ax}_push_obs"] = float(y[len(y) // 2])   # 안 옮긴 영상 (지금 오차) 에서 이동
            r[f"{ax}_eq"] = float(-c / g) if abs(g) >= 2 else np.nan
        rows.append(r)
    # 바로잡는 방향 부호: 사람 장면 기울기 중앙의 부호를 기준으로 (사람 시연에서 정책이 배운 방향)
    out = {}
    for ax in ("u", "v"):
        hs = np.median([r[f"{ax}_slope"] for r in rows if r["kind"] == "human"])
        sgn = np.sign(hs)
        out[ax] = {"corrective_sign_from_human": float(sgn)}
        for kind in ("human", "robot"):
            R = [r for r in rows if r["kind"] == kind]
            eq = [r[f"{ax}_eq"] for r in R if np.sign(r[f"{ax}_slope"]) == sgn]
            out[ax][kind] = dict(n=len(R), slope=boot_med([r[f"{ax}_slope"] for r in R]), push0=boot_med([r[f"{ax}_push0"] for r in R]),
                                 push_obs=boot_med([r[f"{ax}_push_obs"] for r in R]), obs_err=boot_med([r[f"d{ax}"] for r in R]),
                                 eq=boot_med(eq), n_eq=int(np.sum(~np.isnan(eq))), frac_corrective=float(np.mean([np.sign(r[f"{ax}_slope"]) == sgn for r in R])))
        # 판별 (실물)
        out[ax]["robot_by_lab"] = {}
        for lab in sorted({r["lab"] for r in rows if r["kind"] == "robot"}):
            R = [r for r in rows if r["lab"] == lab]
            out[ax]["robot_by_lab"][lab] = dict(n=len(R), obs_err=float(np.median([r[f"d{ax}"] for r in R])), push0=float(np.median([r[f"{ax}_push0"] for r in R])),
                                                slope=float(np.median([r[f"{ax}_slope"] for r in R])),
                                                eq=float(np.nanmedian([r[f"{ax}_eq"] for r in R if np.sign(r[f"{ax}_slope"]) == sgn])) if any(np.sign(r[f"{ax}_slope"]) == sgn and not np.isnan(r[f"{ax}_eq"]) for r in R) else None)
    json.dump(dict(summary=out, rows=rows), open(os.path.join(D, f"equilibrium{a.tag}_s{a.step}_summary.json"), "w"), ensure_ascii=False, indent=1, default=float)
    for ax in ("u", "v"):
        o = out[ax]
        print(f"\n[{ax}] 바로잡는 기울기 부호 (사람 기준) {o['corrective_sign_from_human']:+.0f} · 이동 성분 = {'옆 (pan +)' if ax == 'u' else '바깥'}")
        for kind in ("human", "robot"):
            k = o[kind]
            f = lambda v: "None" if v[0] is None else (f"{v[0]:+.3f}" + ("" if v[1] is None else f" [{v[1]:+.3f}, {v[2]:+.3f}]"))
            print(f"  {kind} n{k['n']}: 지금 오차 {f(k['obs_err'])} · 기울기 cm/단위 {f(k['slope'])} (바로잡는 쪽 {k['frac_corrective']:.2f}) · "
                  f"e=0 이동 cm {f(k['push0'])} · 지금 영상 이동 cm {f(k['push_obs'])} · 평형점 e* {f(k['eq'])} (n {k['n_eq']})")
        for lab, v in o["robot_by_lab"].items():
            print(f"    {lab}: n{v['n']} 지금 {v['obs_err']:+.3f} · 기울기 {v['slope']:+.1f} · e=0 이동 {v['push0']:+.2f} cm · e* {v['eq']}")


if __name__ == "__main__":
    main()
