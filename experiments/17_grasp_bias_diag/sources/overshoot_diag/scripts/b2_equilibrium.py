#!/home/user/so101-env/bin/python
"""P4 평형점 (GPU 재추론, 로봇 · 카메라 연결 없음). 설계: ../10_bias_design.md §P4
손목 영상의 큐브를 좌우 (u) · 앞뒤 (v) 로 옮겨 가며 (큐브 중심 기준 2D 이동) 예측 chunk 의 그리퍼 끝 이동 (FK, 적용 구간 끝 − 지금) 을 잰다.
'정책이 더 움직이지 않는 손목 오차' (평형점) = 이동이 0 이 되는 오차. 편향이 없으면 평형점 ≈ 0 (주황 프레임 중심).
  실물: 각 닫기 시도 직전 1 s 안에 관측한 chunk (저장 prefix · delay, noise = bank 8)
  사람: 예비3 ep3–42 닫기 10 · 20 프레임 전 (prefix 없음, noise = bank 8) — 기준
  PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 nice -n 10 ~/so101-env/bin/python b2_equilibrium.py [--limit K]
→ ../data/equilibrium.npz · equilibrium.json
"""
import argparse
import json
import os
import pathlib
import sys
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import o1_real_chain as O  # noqa: E402
import o2_reinfer as R2  # noqa: E402
import b1_bias as BB  # noqa: E402

U_PX = [-48, -32, -16, 0, 16, 32, 48]   # du −0.075 … +0.075
V_PX = [-36, -24, -12, 0, 12, 24, 36]   # dv −0.075 … +0.075


def scenes_real():
    C = {json.loads(x)["chunk_id"]: json.loads(x) for x in open(f"{O.R}/diag/chunks.jsonl") if x.strip()}
    B = json.load(open(os.path.join(O.OUT, "bias.json")))
    T = pd.read_csv(f"{O.R}/diag/ticks.csv")
    out = []
    for de, ep in O.DIAG2DS.items():
        tick0 = int(T[T.episode == de].tick.iloc[0])
        r = B["robot"][ep]
        frames = [a["frame"] for a in r["attempts"]]
        seen = set()
        for c in C.values():
            if c["episode"] != de:
                continue
            fi = int(c["obs_tick"]) - tick0
            if any(0 <= k - fi <= 30 for k in frames) and c["chunk_id"] not in seen:
                seen.add(c["chunk_id"])
                out.append(dict(kind="robot", ep=ep, lab=O.LAB[ep], chunk=c["chunk_id"], frame=fi))
    return out, C


def scenes_human():
    info, em, d3 = O.load_ds(f"{O.P3}/dataset")
    out = []
    for ep in range(3, 43):
        e = d3[d3.episode_index == ep].sort_values("frame_index")
        st = np.stack(e["observation.state"].values).astype(float)
        ac = np.stack(e["action"].values).astype(float)
        ci = O.sg_phase.analyze(st, ac, 30)["_idx"]["close"]
        want = [ci - 10, ci - 20]
        fw = O.frames(f"{O.P3}/dataset", info, em, ep, want)
        ff = O.frames(f"{O.P3}/dataset", info, em, ep, want, cam="front")
        for k in want:
            out.append(dict(kind="human", ep=ep, lab="H", frame=k, state=st[k].tolist(), front=ff[k], wrist=fw[k]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    ap.add_argument("--noprefix", action="store_true", help="실물 장면도 prefix 없이 (사람 장면과 같은 조건)")
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    sys.path.insert(0, R2.VD)
    import sg_vis_eval as VE
    import v_common as V
    import v02_engine as E

    V.CKPT = pathlib.Path(R2.CK)
    t0 = time.time()
    SR, C = scenes_real()
    SH = scenes_human()
    S = SR + SH
    if a.limit:
        S = SR[: a.limit] + SH[: a.limit]
    print(f"장면 실물 {len(SR)} · 사람 {len(SH)} · {time.time() - t0:.0f}s", flush=True)
    eng = E.Engine(n_noise=8)
    TIPU, TIPV, META = [], [], []
    for n, s in enumerate(S):
        if s["kind"] == "robot":
            m = C[s["chunk"]]
            z = np.load(f"{O.R}/diag/chunks/c{s['chunk']:05d}.npz")
            f = R2.rgb(f"{O.R}/diag/obs/c{s['chunk']:05d}_front.png")
            w = R2.rgb(f"{O.R}/diag/obs/c{s['chunk']:05d}_wrist.png")
            st = m["obs_state"]
            kw = {} if a.noprefix else dict(prefix=z["prefix"], delay=m.get("inference_delay"))
            h = min(49, int(m.get("applied_delay") or 0) + 20)
        else:
            f, w, st, kw, h = s["front"], s["wrist"], s["state"], {}, 20
        det = O.ss.detect(w, O.PRM)
        cmp_ = O.ss.target_compare(det, O.ref)
        if cmp_ is None:
            continue
        cx, cy = det["cube"]["u"] * w.shape[1], det["cube"]["v"] * w.shape[0]
        p0 = BB.tip(st)[0]
        res = []
        for axis, PX in (("u", U_PX), ("v", V_PX)):
            imgs = [(f, VE.warp(w, cx, cy, (d if axis == "u" else 0), (d if axis == "v" else 0), 0, 1.0)) for d in PX]
            A = eng.run(st, imgs, **kw)                          # (K, 8, 50, 6)
            per = []
            for hh in (h, 49):
                tips = BB.tip(A[:, :, hh, :5].reshape(-1, 5)).reshape(len(PX), -1, 3).mean(1)    # (K, 3) 노이즈 평균 끝 위치
                per.append(np.array([BB.decomp(p0, t - p0) for t in tips]))                     # (K, 3) 바깥 · 옆 · 높이 cm
            res.append(per[0] if not a.tag else np.stack(per))
        TIPU.append(res[0])
        TIPV.append(res[1])
        META.append(dict(kind=s["kind"], ep=s["ep"], lab=s["lab"], chunk=s.get("chunk"), frame=s["frame"], du=cmp_["du"], dv=cmp_["dv"], size=cmp_["size"],
                         edge=cmp_["edge"], h=h))
        if n % 25 == 0:
            print(f"  {n}/{len(S)} · {time.time() - t0:.0f}s", flush=True)
    np.savez_compressed(os.path.join(O.OUT, f"equilibrium{a.tag}.npz"), U=np.array(TIPU), V=np.array(TIPV), u_px=np.array(U_PX), v_px=np.array(V_PX))
    json.dump(dict(ckpt=R2.CK, scenes=META, sec=round(time.time() - t0, 1)), open(os.path.join(O.OUT, f"equilibrium{a.tag}.json"), "w"), ensure_ascii=False, indent=1, default=float)
    print("B2_DONE", f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
