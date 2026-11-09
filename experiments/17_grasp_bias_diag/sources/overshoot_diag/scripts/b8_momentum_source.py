#!/home/user/so101-env/bin/python
"""P7 기세 (A) · 출처 (B) (GPU 재추론, 로봇 · 카메라 연결 없음).
장면: 실물 각 닫기 시도 직전 1 s 안 chunk (b2 와 같음) · 사람 예비3 닫기 10 · 20 프레임 전 (b2 와 같음).
모든 실물 조건에서 손목 영상은 큐브를 주황 닫기 프레임 중심 (du = dv = 0) 으로 옮긴 것 (검출 실패 장면은 원래 영상, 기록).
측정: 예측 끝 위치 (노이즈 8 평균, FK) − 넣은 관절값의 끝 위치, 바깥 · 옆 · 높이 cm. 시점 = 적용 구간 끝 (실물 applied_delay+20, 사람 20) · 49.
A 기세 (실물):  np = prefix 없음 · pf = 저장 prefix · still = 팔 관절 prefix 를 지금 관절값 (정규화) 으로 고정 (그리퍼 열은 저장 prefix), delay 같음.
  사람 대조: np · pfh = 사람 실제 행동 action[k : k+20] 을 정규화한 prefix (delay 10).
B 출처 (실물, prefix 없음): front · wrist · state 각각 실물 (R) / 큐브 자리가 가장 가까운 사람 판 닫기 10 프레임 전 (H), 2×2×2.
  PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 nice -n 10 ~/so101-env/bin/python b8_momentum_source.py → ../data/momentum_source.npz · .json
"""
import json
import os
import pathlib
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import b1_bias as BB  # noqa: E402
import b2_equilibrium as B2  # noqa: E402
import o1_real_chain as O  # noqa: E402
import o2_reinfer as R2  # noqa: E402

def norm_map(C):
    """저장 chunk 의 processed (°) → original (정규화, prefix 와 같은 공간) 관절별 1 차식 맞춤: 정규화 = a·° + b."""
    X, Y = [], []
    for cid in list(C)[::7]:
        z = np.load(f"{O.R}/diag/chunks/c{cid:05d}.npz")
        X.append(z["processed"]), Y.append(z["original"])
    X, Y = np.concatenate(X), np.concatenate(Y)
    ab = [np.polyfit(X[:, j], Y[:, j], 1) for j in range(6)]
    res = [float(np.abs(np.polyval(ab[j], X[:, j]) - Y[:, j]).max()) for j in range(6)]
    return np.array(ab), res


def disp(A, q, hs):
    """A (N, 50, 6) → [(바깥, 옆, 높이) for h in hs], q 의 끝 기준."""
    p0 = BB.tip(np.asarray(q, float))[0]
    out = []
    for h in hs:
        t = BB.tip(A[:, h, :5]).mean(0)
        out.append(BB.decomp(p0, t - p0))
    return np.array(out)


def center(w, VE):
    det = O.ss.detect(w, O.PRM)
    c = O.ss.target_compare(det, O.ref)
    if c is None:
        return w, None
    cx, cy = det["cube"]["u"] * w.shape[1], det["cube"]["v"] * w.shape[0]
    return VE.warp(w, cx, cy, -c["du"] * 640.0, -c["dv"] * 480.0, 0, 1.0), c


def main():
    sys.path.insert(0, R2.VD)
    import sg_vis_eval as VE
    import v_common as V
    import v02_engine as E

    V.CKPT = pathlib.Path(R2.CK)
    t0 = time.time()
    SR, C = B2.scenes_real()
    SH = B2.scenes_human()
    ab, nres = norm_map(C)
    print(f"장면 실물 {len(SR)} · 사람 {len(SH)} · 정규화 맞춤 최대 잔차 {max(nres):.2e} · {time.time() - t0:.0f}s", flush=True)
    B = json.load(open(os.path.join(O.OUT, "bias.json")))
    hxy = {r["ep"]: np.array(r["xy"]) for r in B["human"]["rows"]}
    # 사람 판 행동 (prefix 대조용)
    info, em, d3 = O.load_ds(f"{O.P3}/dataset")
    acts = {ep: np.stack(d3[d3.episode_index == ep].sort_values("frame_index")["action"].values).astype(float) for ep in range(3, 43)}
    H10 = {s["ep"]: s for s in SH if s["frame"] == max(x["frame"] for x in SH if x["ep"] == s["ep"])}   # 닫기 10 프레임 전
    eng = E.Engine(n_noise=8)
    RES, META = [], []
    for n, s in enumerate(SR + SH):
        r = {}
        if s["kind"] == "robot":
            m = C[s["chunk"]]
            z = np.load(f"{O.R}/diag/chunks/c{s['chunk']:05d}.npz")
            fR = R2.rgb(f"{O.R}/diag/obs/c{s['chunk']:05d}_front.png")
            wR, cmp_ = center(R2.rgb(f"{O.R}/diag/obs/c{s['chunk']:05d}_wrist.png"), VE)
            qR = np.array(m["obs_state"], float)
            h = min(49, int(m.get("applied_delay") or 0) + 20)
            dl = m.get("inference_delay")
            cxy = np.array(B["robot"][s["ep"]]["cube_xy"])
            hep = min(hxy, key=lambda e: np.linalg.norm(hxy[e] - cxy))
            hs_ = H10[hep]
            fH, wH, qH = hs_["front"], hs_["wrist"], np.array(hs_["state"], float)
            # A
            A = eng.run(qR, [(fR, wR)], prefix=z["prefix"], delay=dl)[0]
            r["pf"] = disp(A, qR, (h, 49))
            still = z["prefix"].copy()
            still[:, :5] = (ab[:5, 0] * qR[:5] + ab[:5, 1])[None]
            A = eng.run(qR, [(fR, wR)], prefix=still, delay=dl)[0]
            r["still"] = disp(A, qR, (h, 49))
            # B (np), np 기준 = RRR
            for st_lab, q in (("R", qR), ("H", qH)):
                imgs = [(fR if f == "R" else fH, wR if w == "R" else wH) for f in "RH" for w in "RH"]
                A = eng.run(q, imgs)                                  # (4, N, 50, 6)
                for k, (f, w) in enumerate([(f, w) for f in "RH" for w in "RH"]):
                    r[f"B_{f}{w}{st_lab}"] = disp(A[k], q, (h, 49))
            r["np"] = r["B_RRR"]
            # 저장 prefix 의 팔 움직임 (정규화 역변환, 첫 → 끝 끝 위치 이동)
            pfdeg = (z["prefix"][:, :5] - ab[:5, 1]) / ab[:5, 0]
            r["prefix_move"] = BB.decomp(BB.tip(qR)[0], BB.tip(pfdeg[-1])[0] - BB.tip(pfdeg[0])[0])
            META.append(dict(kind="robot", ep=s["ep"], lab=s["lab"], chunk=s["chunk"], frame=s["frame"], h=h, centered=cmp_ is not None,
                             du=None if cmp_ is None else cmp_["du"], dv=None if cmp_ is None else cmp_["dv"], human_ep=int(hep),
                             human_dist_cm=float(np.linalg.norm(hxy[hep] - cxy))))
        else:
            q = np.array(s["state"], float)
            A = eng.run(q, [(s["front"], s["wrist"])])[0]
            r["np"] = disp(A, q, (20, 49))
            a = acts[s["ep"]][s["frame"]: s["frame"] + 20]
            pf = np.zeros((20, 6))
            pf[: len(a)] = ab[:, 0] * a + ab[:, 1]
            pf[len(a):] = pf[len(a) - 1]
            A = eng.run(q, [(s["front"], s["wrist"])], prefix=pf.astype(np.float32), delay=10)[0]
            r["pfh"] = disp(A, q, (20, 49))
            META.append(dict(kind="human", ep=s["ep"], lab="H", frame=s["frame"], h=20))
        RES.append({k: np.asarray(v, float).tolist() for k, v in r.items()})
        if n % 25 == 0:
            print(f"  {n}/{len(SR) + len(SH)} · {time.time() - t0:.0f}s", flush=True)
    json.dump(dict(ckpt=R2.CK, norm_ab=ab.tolist(), norm_res=nres, scenes=META, res=RES, sec=round(time.time() - t0, 1)),
              open(os.path.join(O.OUT, "momentum_source.json"), "w"), ensure_ascii=False, default=float)
    print("B8_DONE", f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
