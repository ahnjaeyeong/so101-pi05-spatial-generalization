"""G1 결과 분석 (CPU). 입력 g1/chunks.npy · rows.csv. 출력 a1_g1.json, a1_g1_frames.csv.

정의 (행동 = noise 4개 평균 chunk 의 index h: t1.0 → 30 (닫힘 시각), t1.5 → 45, t2.5 → 49 (chunk 끝, 닫힘 0.83 s 전))
  tip       : FK 집게 끝 (diag fk_fit) 을 판의 큐브 방향 축으로 — tan (접선, 로봇 왼쪽 +) · rad (반지름, 바깥 +), cm
  tip_fr    : 같은 계산이되 wrist_roll 행동을 그 프레임 base 조건 값으로 고정 (roll 행동 변화가 FK 로 끝점을 옮기는 몫 제외)
  M(θ)      : 영상 상대 위치 (rel_u, rel_v) cm → 탁자 (tan, rad), θ = 0.91·roll − 5.5° (vision_probe 라벨 규약)

  A  영상 이득 행렬: Rp(Δ) = [ (wu+ − wu−)/2 , (wv+ − wv−)/2 ]  (영상 1 cm 이동당 집게 끝 이동, roll state = roll+Δ)
     G(Δ) = Rp(Δ) · M(θ+0.91Δ)⁻¹   (탁자 큐브 이동당 집게 끝 이동; 이상값 단위행렬)
  B  roll 조건부 회전: Rp(Δ) ≈ Rp(0) · R(ψ) 의 ψ (오른쪽 Procrustes). roll 을 반영하면 ψ = ψ_ideal = ∠(M(θ)⁻¹ M(θ+0.91Δ)),
     roll 을 무시하면 ψ = 0. w_rot = Σψ·ψ_ideal / Σψ_ideal²  (판 bootstrap)
  C  state 만 바꿈 (영상 그대로): Δtip_S = tip(base, Δ) − tip(base, 0). 같은 영상이 뜻하는 큐브 탁자 위치 변화
     dC = (M(θ+0.91Δ) − M(θ)) rel. 정책 자신의 이득으로 기대값 G(0) dC → w_state = Σ<Δtip_S, G(0)dC> / Σ|G(0)dC|²
  D  roll-일관 회전 RC (영상 큐브 회전 + state roll+Δ, 탁자 위치 그대로 → 기대 0) vs 영상만 회전 RI (기대 G(0) M(θ)(rel'−rel))
     w_RC = 1 − Σ<RC, RI> / Σ|RI|²   (1 = roll 반영, 0 = 무시)
  E  가리기: KR (roll 숫자 토큰) 에서 Rp_KR 과 base 변화, KS (state 숫자 전체) 에서 base 변화
"""
import json

import numpy as np
import pandas as pd

import ab_core as A
from ab_core import C

G1 = A.AB / "g1"
HIDX = {"t1.0": 30, "t1.5": 45, "t2.5": 49}
RNG = np.random.default_rng(0)


def rot_angle(R):
    return float(np.degrees(np.arctan2(R[1, 0], R[0, 0])))


def right_procrustes(R0, R1):
    B = R0.T @ R1
    return float(np.degrees(np.arctan2(B[1, 0] - B[0, 1], B[0, 0] + B[1, 1])))


def boot(df, fn, n=2000):
    eps = df.ep.unique()
    g = {e: d for e, d in df.groupby("ep")}
    vals = []
    for _ in range(n):
        s = RNG.choice(eps, len(eps))
        vals.append(fn(pd.concat([g[e] for e in s])))
    v = np.array(vals, float)
    return [float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))]


def main():
    R, ch = A.load_g1()
    ch = ch.mean(0)                                                   # N × 50 × 6
    assert len(ch) == len(R), (len(ch), len(R))
    tip = A.tip_fn()
    h = R.phase.map(HIDX).values
    a = ch[np.arange(len(R)), h]                                       # N × 6
    R["pan"], R["roll_a"] = a[:, 0], a[:, 4]
    for j, nm in enumerate(C.JOINTS):
        R[f"a_{nm}"] = a[:, j]
    ur = np.stack([R.cube_x - C.BASE[0], R.cube_y - C.BASE[1]], 1)
    ur /= np.linalg.norm(ur, axis=1, keepdims=True)
    ut = np.stack([-ur[:, 1], ur[:, 0]], 1)
    cube = R[["cube_x", "cube_y"]].values
    tp = tip(a[:, :5]) - cube
    R["tip_tan"], R["tip_rad"] = (tp * ut).sum(1), (tp * ur).sum(1)
    # roll 행동을 base 값으로 고정한 끝점
    key = ["ep", "phase"]
    base_roll = R[(R.cond == "F:base") & (R.droll == 0)].set_index(key).roll_a
    a2 = a[:, :5].copy()
    a2[:, 4] = base_roll.reindex(pd.MultiIndex.from_frame(R[key])).values
    tp2 = tip(a2) - cube
    R["tipf_tan"], R["tipf_rad"] = (tp2 * ut).sum(1), (tp2 * ur).sum(1)
    R.to_csv(A.AB / "a1_g1_rows.csv", index=False)

    out = {"n_obs": len(R), "n_frames": int(R.groupby(key).ngroups)}
    frames = []
    for (e, ph), g in R.groupby(key):
        g = g.set_index(["cond", "droll"])
        if ("F:base", 0.0) not in g.index:
            continue
        b0 = g.loc[("F:base", 0.0)]
        roll = float(b0.roll)
        rel = np.array([b0.rel_u, b0.rel_v])

        def T(c, d=0.0, fr=True):
            r = g.loc[(c, d)]
            return np.array([r.tipf_tan, r.tipf_rad]) if fr else np.array([r.tip_tan, r.tip_rad])

        def Rp(prefix, d):
            try:
                return np.stack([(T(f"{prefix}wu+", d) - T(f"{prefix}wu-", d)) / 2, (T(f"{prefix}wv+", d) - T(f"{prefix}wv-", d)) / 2], 1)
            except KeyError:
                return None
        R0 = Rp("F:", 0.0)
        M0 = A.M_img2tab(roll)
        G0 = R0 @ np.linalg.inv(M0)
        fr = dict(ep=e, phase=ph, group=b0.group, roll=roll, rel_u=rel[0], rel_v=rel[1],
                  G_tt=G0[0, 0], G_tr=G0[0, 1], G_rt=G0[1, 0], G_rr=G0[1, 1], R0_norm=float(np.linalg.norm(R0)))
        for d in (-30.0, -15.0, 15.0, 30.0):
            Md = A.M_img2tab(roll + d)
            Rd = Rp("F:", d)
            if Rd is not None:
                Gd = Rd @ np.linalg.inv(Md)
                fr[f"G_tt_{d:+.0f}"], fr[f"G_rr_{d:+.0f}"] = Gd[0, 0], Gd[1, 1]
                fr[f"psi_{d:+.0f}"] = right_procrustes(R0, Rd)
                fr[f"psi_ideal_{d:+.0f}"] = rot_angle(np.linalg.inv(M0) @ Md)
                # C: state 만
                dS = T("F:base", d) - T("F:base", 0.0)
                dC = (Md - M0) @ rel
                pred = G0 @ dC
                fr[f"dS_tan_{d:+.0f}"], fr[f"dS_rad_{d:+.0f}"] = dS
                fr[f"dSpred_tan_{d:+.0f}"], fr[f"dSpred_rad_{d:+.0f}"] = pred
                fr[f"dC_tan_{d:+.0f}"], fr[f"dC_rad_{d:+.0f}"] = dC
                fr[f"dS_pan_{d:+.0f}"] = g.loc[("F:base", d)].pan - b0.pan
                fr[f"droll_a_{d:+.0f}"] = g.loc[("F:base", d)].roll_a - b0.roll_a
                fr[f"dS_full_tan_{d:+.0f}"] = (T("F:base", d, fr=False) - T("F:base", 0.0, fr=False))[0]
            # D: RC / RI
            if (f"RI:{d:+.0f}", 0.0) in g.index:
                ri = T(f"RI:{d:+.0f}", 0.0) - T("F:base", 0.0)
                r_new = np.array([g.loc[(f"RI:{d:+.0f}", 0.0)].rel_u_new, g.loc[(f"RI:{d:+.0f}", 0.0)].rel_v_new])
                fr[f"RI_tan_{d:+.0f}"], fr[f"RI_rad_{d:+.0f}"] = ri
                pri = G0 @ M0 @ (r_new - rel)
                fr[f"RIpred_tan_{d:+.0f}"], fr[f"RIpred_rad_{d:+.0f}"] = pri
                fr[f"RI_pan_{d:+.0f}"] = g.loc[(f"RI:{d:+.0f}", 0.0)].pan - b0.pan
            if (f"RC:{d:+.0f}", d) in g.index:
                rc = T(f"RC:{d:+.0f}", d) - T("F:base", 0.0)
                fr[f"RC_tan_{d:+.0f}"], fr[f"RC_rad_{d:+.0f}"] = rc
                fr[f"RC_pan_{d:+.0f}"] = g.loc[(f"RC:{d:+.0f}", d)].pan - b0.pan
                fr[f"RC_droll_a_{d:+.0f}"] = g.loc[(f"RC:{d:+.0f}", d)].roll_a - b0.roll_a
        # E: 가리기
        Rk = Rp("KR:", 0.0)
        if Rk is not None:
            Gk = Rk @ np.linalg.inv(M0)
            fr["GK_tt"], fr["GK_rr"] = Gk[0, 0], Gk[1, 1]
        kb = T("KR:base") - T("F:base")
        fr["KR_base_tan"], fr["KR_base_rad"] = kb
        fr["KR_base_pan"] = g.loc[("KR:base", 0.0)].pan - b0.pan
        fr["KR_base_droll_a"] = g.loc[("KR:base", 0.0)].roll_a - b0.roll_a
        ks = g.loc[("KS:base", 0.0)]
        fr["KS_base_pan"] = ks.pan - b0.pan
        fr["KS_base_tip"] = float(np.hypot(ks.tip_tan - b0.tip_tan, ks.tip_rad - b0.tip_rad))
        fr["KS_max_joint"] = float(np.max(np.abs(ks[[f"a_{j}" for j in C.JOINTS[:5]]].values.astype(float)
                                                 - b0[[f"a_{j}" for j in C.JOINTS[:5]]].values.astype(float))))
        w0 = g.loc[("W0", 0.0)]
        fr["W0_tip"] = float(np.hypot(w0.tipf_tan - b0.tipf_tan, w0.tipf_rad - b0.tipf_rad))
        frames.append(fr)
    Fm = pd.DataFrame(frames)
    Fm.to_csv(A.AB / "a1_g1_frames.csv", index=False)

    D = (-30.0, -15.0, 15.0, 30.0)

    def stats_phase(Fp):
        r = {"n_frames": len(Fp), "n_eps": int(Fp.ep.nunique())}
        for k in ("G_tt", "G_rr", "G_tr", "G_rt"):
            r[k] = float(Fp[k].median())
            r[k + "_ci"] = boot(Fp, lambda d, k=k: d[k].median(), 1000)
        for d in D:
            for k in ("G_tt", "G_rr"):
                c = f"{k}_{d:+.0f}"
                if c in Fp:
                    r[c] = float(Fp[c].median())
        # B 회전
        ok = Fp[Fp.R0_norm >= 0.1]

        def w_rot(dd):
            num = sum((dd[f"psi_{d:+.0f}"] * dd[f"psi_ideal_{d:+.0f}"]).sum() for d in D if f"psi_{d:+.0f}" in dd)
            den = sum((dd[f"psi_ideal_{d:+.0f}"] ** 2).where(dd[f"psi_{d:+.0f}"].notna()).sum() for d in D if f"psi_{d:+.0f}" in dd)
            return num / den if den else np.nan
        r["B_n"] = len(ok)
        r["B_w_rot"] = float(w_rot(ok))
        r["B_w_rot_ci"] = boot(ok, w_rot, 1000)
        r["B_psi_median"] = {f"{d:+.0f}": [float(ok[f"psi_{d:+.0f}"].median()), float(ok[f"psi_ideal_{d:+.0f}"].median())] for d in D}

        # C state 만
        def w_state(dd):
            num = den = 0.0
            for d in D:
                for ax in ("tan", "rad"):
                    x, y = dd[f"dSpred_{ax}_{d:+.0f}"], dd[f"dS_{ax}_{d:+.0f}"]
                    m = x.notna() & y.notna()
                    num += (x[m] * y[m]).sum()
                    den += (x[m] ** 2).sum()
            return num / den if den else np.nan
        r["C_w_state"] = float(w_state(Fp))
        r["C_w_state_ci"] = boot(Fp, w_state, 1000)
        r["C_abs"] = {f"{d:+.0f}": dict(dS=float(np.hypot(Fp[f"dS_tan_{d:+.0f}"], Fp[f"dS_rad_{d:+.0f}"]).median()),
                                        dSpred=float(np.hypot(Fp[f"dSpred_tan_{d:+.0f}"], Fp[f"dSpred_rad_{d:+.0f}"]).median()),
                                        dC=float(np.hypot(Fp[f"dC_tan_{d:+.0f}"], Fp[f"dC_rad_{d:+.0f}"]).median()),
                                        dpan=float(Fp[f"dS_pan_{d:+.0f}"].median()),
                                        droll_copy=float((Fp[f"droll_a_{d:+.0f}"] / d).median()))
                      for d in D if f"dS_tan_{d:+.0f}" in Fp}

        # D RC vs RI
        def w_rc(dd):
            num = den = 0.0
            for d in D:
                for ax in ("tan", "rad"):
                    if f"RC_{ax}_{d:+.0f}" not in dd:
                        continue
                    x, y = dd[f"RI_{ax}_{d:+.0f}"], dd[f"RC_{ax}_{d:+.0f}"]
                    m = x.notna() & y.notna()
                    num += (x[m] * y[m]).sum()
                    den += (x[m] ** 2).sum()
            return 1 - num / den if den else np.nan

        def w_ri(dd):           # RI 반응이 자기 이득 기대값을 따르는 정도 (영상 회전에 대한 이득)
            num = den = 0.0
            for d in D:
                for ax in ("tan", "rad"):
                    x, y = dd[f"RIpred_{ax}_{d:+.0f}"], dd[f"RI_{ax}_{d:+.0f}"]
                    m = x.notna() & y.notna()
                    num += (x[m] * y[m]).sum()
                    den += (x[m] ** 2).sum()
            return num / den if den else np.nan
        r["D_w_RC"] = float(w_rc(Fp))
        r["D_w_RC_ci"] = boot(Fp, w_rc, 1000)
        r["D_RI_vs_ownpred"] = float(w_ri(Fp))
        r["D_abs"] = {f"{d:+.0f}": dict(RC=float(np.hypot(Fp[f"RC_tan_{d:+.0f}"], Fp[f"RC_rad_{d:+.0f}"]).median()),
                                        RI=float(np.hypot(Fp[f"RI_tan_{d:+.0f}"], Fp[f"RI_rad_{d:+.0f}"]).median()),
                                        RC_pan=float(Fp[f"RC_pan_{d:+.0f}"].abs().median()),
                                        RI_pan=float(Fp[f"RI_pan_{d:+.0f}"].abs().median()),
                                        RC_roll_copy=float((Fp[f"RC_droll_a_{d:+.0f}"] / d).median()))
                      for d in D if f"RC_tan_{d:+.0f}" in Fp}
        # E
        r["E_GK_tt"], r["E_GK_rr"] = float(Fp.GK_tt.median()), float(Fp.GK_rr.median())
        r["E_KR_base_tip_med"] = float(np.hypot(Fp.KR_base_tan, Fp.KR_base_rad).median())
        r["E_KR_base_pan_absmed"] = float(Fp.KR_base_pan.abs().median())
        r["E_KR_base_droll_a_absmed"] = float(Fp.KR_base_droll_a.abs().median())
        r["E_KS_base_pan_absmed"] = float(Fp.KS_base_pan.abs().median())
        r["E_KS_base_tip_med"] = float(Fp.KS_base_tip.median())
        r["E_KS_max_joint_med"] = float(Fp.KS_max_joint.median())
        r["W0_tip_max"] = float(Fp.W0_tip.max())
        return r

    for ph in HIDX:
        Fp = Fm[Fm.phase == ph]
        if len(Fp):
            out[ph] = stats_phase(Fp)
            for md in ("K", "R"):
                if not (Fp.group.str[2] == md).any():
                    continue
                out[f"{ph}_{md}"] = {k: v for k, v in stats_phase(Fp[Fp.group.str[2] == md]).items()
                                     if k in ("n_frames", "G_tt", "G_rr", "B_w_rot", "C_w_state", "D_w_RC")}
    json.dump(out, open(A.AB / "a1_g1.json", "w"), indent=1)
    print(json.dumps(out, indent=1)[:6000])


if __name__ == "__main__":
    main()
