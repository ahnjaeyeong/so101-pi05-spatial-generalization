#!/home/user/so101-env/bin/python
"""P5 '정해진 자세로 가기' vs '지금 위치에서 더 가기' (GPU 재추론, 로봇 · 카메라 연결 없음).
영상 (front · wrist) 은 그대로, 관절값만 그리퍼 끝이 바깥 (반지름) 으로 ±1 cm 있는 것처럼 바꿈 — 높이 · 앞뒤 기울기 고정
(lift · elbow · wflex 3 관절, FK 수치 미분으로 선형 풀이 후 2 번 보정). 예측 끝 위치 (FK, 절대) 의 바깥 성분이 관절값 변화에 따라 움직이는 비율 k:
  k ≈ 0 → 지금 위치와 상관없이 정해진 자리로 감 (절대 목표 · 자세 기억),  k ≈ 1 → 지금 위치에서 일정량 더 감 (상대 이동).
장면: 실물 각 판 마지막 잡기 (잡힌 닫기 중 마지막 묶음, 없으면 마지막 닫기) 앞 3 s 의 chunk 관측 + 사람 예비3 닫기 10 · 20 프레임 전.
조건: prefix 없음 (사람과 같음) · 실물은 prefix 있음도 (저장 prefix · delay). 시점 = 적용 구간 끝 (실물 applied_delay+20, 사람 20) · chunk 끝 49.
  PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 nice -n 10 ~/so101-env/bin/python b6_state_probe.py → ../data/state_probe.npz · .json
"""
import json
import os
import pathlib
import sys
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import b1_bias as BB  # noqa: E402
import b2_equilibrium as B2  # noqa: E402
import o1_real_chain as O  # noqa: E402
import o2_reinfer as R2  # noqa: E402

DR = [-1.0, 0.0, 1.0]   # 바깥 cm


def feat(q):
    p, R = BB.sg_fk.fk(np.atleast_2d(q)[:, :5])
    r = np.hypot(p[0, 0], p[0, 1]) * 100
    return np.array([r, p[0, 2] * 100, BB.sg_fk.tool_tilt(q[:5])[0]])   # 반지름 cm · 높이 cm · 앞뒤 기울기 °


def shift_radial(q, dr):
    """q 의 lift(1) · elbow(2) · wflex(3) 만 바꿔 반지름 + dr cm, 높이 · 기울기 그대로."""
    q = np.array(q, float)
    f0 = feat(q)
    tgt = f0 + np.array([dr, 0, 0])
    x = q.copy()
    for _ in range(3):
        f = feat(x)
        Jm = np.zeros((3, 3))
        for c, j in enumerate((1, 2, 3)):
            xx = x.copy()
            xx[j] += 0.1
            Jm[:, c] = (feat(xx) - f) / 0.1
        x[[1, 2, 3]] += np.linalg.solve(Jm, tgt - f)
    return x, feat(x) - f0


def scenes():
    C = {json.loads(x)["chunk_id"]: json.loads(x) for x in open(f"{O.R}/diag/chunks.jsonl") if x.strip()}
    B = json.load(open(os.path.join(O.OUT, "bias.json")))
    T = pd.read_csv(f"{O.R}/diag/ticks.csv")
    out = []
    for de, ep in O.DIAG2DS.items():
        tick0 = int(T[T.episode == de].tick.iloc[0])
        att = B["robot"][ep]["attempts"]
        held = [a["frame"] for a in att if a["held"]]
        k = (held[-1] if held else (att[-1]["frame"] if att else None))
        # 잡힌 닫기 묶음의 첫 프레임 (0.5 s 안에 이어진 닫기는 한 묶음)
        if held:
            grp = [held[-1]]
            for f in reversed(held[:-1]):
                if grp[-1] - f <= 15:
                    grp.append(f)
                else:
                    break
            k = grp[-1]
        if k is None:
            continue
        for c in C.values():
            fi = int(c["obs_tick"]) - tick0
            if c["episode"] == de and 0 <= k - fi <= 90:
                out.append(dict(kind="robot", ep=ep, lab=O.LAB[ep], chunk=c["chunk_id"], frame=fi, close=k))
    return out, C


def main():
    sys.path.insert(0, R2.VD)
    import v_common as V
    import v02_engine as E

    V.CKPT = pathlib.Path(R2.CK)
    t0 = time.time()
    SR, C = scenes()
    SH = B2.scenes_human()
    print(f"장면 실물 {len(SR)} · 사람 {len(SH)} · {time.time() - t0:.0f}s", flush=True)
    eng = E.Engine(n_noise=8)
    RES, META = [], []
    for n, s in enumerate(SR + SH):
        if s["kind"] == "robot":
            m = C[s["chunk"]]
            z = np.load(f"{O.R}/diag/chunks/c{s['chunk']:05d}.npz")
            f = R2.rgb(f"{O.R}/diag/obs/c{s['chunk']:05d}_front.png")
            w = R2.rgb(f"{O.R}/diag/obs/c{s['chunk']:05d}_wrist.png")
            st0 = np.array(m["obs_state"], float)
            h = min(49, int(m.get("applied_delay") or 0) + 20)
            variants = [("np", {}), ("pf", dict(prefix=z["prefix"], delay=m.get("inference_delay")))]
        else:
            f, w, st0, h = s["front"], s["wrist"], np.array(s["state"], float), 20
            variants = [("np", {})]
        states, achieved = [], []
        for dr in DR:
            q, d = shift_radial(st0, dr) if dr else (st0.copy(), np.zeros(3))
            states.append(q)
            achieved.append(d)
        r = {}
        for vn, kw in variants:
            ends, gs = [], []
            for q in states:
                A = eng.run(q, [(f, w)], **kw)[0]                      # (8, 50, 6)
                ends.append([feat(A[:, hh, :5].mean(0)) for hh in (h, 49)])   # 노이즈 평균 관절 → (반지름, 높이, 기울기)
                gs.append(float((A[:, :, 5].min(1) < A[:, 0, 5] - 8).mean()))  # chunk 안 닫기 비율
            r[vn] = np.array(ends)                                       # (3 상태, 2 시점, 3)
            r[vn + "_g"] = np.array(gs)
        RES.append(r)
        META.append(dict(kind=s["kind"], ep=s["ep"], lab=s["lab"], chunk=s.get("chunk"), frame=s["frame"], close=s.get("close"), h=h,
                         achieved=[a.tolist() for a in achieved], state_feat=feat(st0).tolist()))
        if n % 25 == 0:
            print(f"  {n}/{len(SR) + len(SH)} · {time.time() - t0:.0f}s", flush=True)
    np.savez_compressed(os.path.join(O.OUT, "state_probe.npz"), np_=np.array([r["np"] for r in RES]),
                        pf=np.array([r.get("pf", np.full_like(r["np"], np.nan)) for r in RES]),
                        g_np=np.array([r["np_g"] for r in RES]), g_pf=np.array([r.get("pf_g", np.full(3, np.nan)) for r in RES]))
    json.dump(dict(ckpt=R2.CK, dr=DR, scenes=META, sec=round(time.time() - t0, 1)), open(os.path.join(O.OUT, "state_probe.json"), "w"), ensure_ascii=False, indent=1, default=float)
    print("B6_DONE", f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
