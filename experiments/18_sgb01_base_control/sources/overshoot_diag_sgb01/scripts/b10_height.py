#!/home/user/so101-env/bin/python
"""P8 높이 · 보는 각도 (T1 · T2) (GPU 재추론, 로봇 · 카메라 연결 없음). 모두 prefix 없음, noise 8 평균.
손목 영상 조건 (집게 · 배경 그대로, 큐브만 바꿈): O = 원래, Cc = 큐브만 닫기 프레임 중심으로 옮김, Zc = 옮기고 큐브만 1/size 배 확대 (size ≥ 0.97 이면 확대 안 함).
T1 실물 (b2 장면 127). 큐브가 영상 끝에 걸린 장면 (edge) 기록.
T2 사람 (예비3 ep3–42, 닫기 10 · 30 · 60 · 90 프레임 전). front · 관절값은 그 프레임 것.
측정: 예측 끝 이동 (FK, 넣은 관절값 기준) 바깥 · 옆 · 높이 cm, 시점 = 적용 구간 끝 (실물 applied_delay+20, 사람 20) · 49.
  PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 nice -n 10 ~/so101-env/bin/python b10_height.py → ../data/height.json
"""
import json
import os
import pathlib
import sys
import time

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(HERE, "..", "..", "scripts"))  # sgb01 복사본: b1 · b2 · o1 은 원본 (수정 없음), o2_reinfer 만 복사본
import o2_reinfer as R2  # noqa: E402  (복사본을 먼저 불러 b2 도 같은 모듈을 쓰게 함)
assert os.path.dirname(os.path.abspath(R2.__file__)) == HERE, R2.__file__
import b1_bias as BB  # noqa: E402
import b2_equilibrium as B2  # noqa: E402
import o1_real_chain as O  # noqa: E402
assert B2.R2 is R2
OUTF = os.path.join(HERE, "..", "data", f"height_{os.environ['OD_TAG']}.json")  # sgb01 복사본: 출력 경로

BACK = [10, 30, 60, 90]


def disp(A, q, hs):
    p0 = BB.tip(np.asarray(q, float))[0]
    return np.array([BB.decomp(p0, BB.tip(A[:, h, :5]).mean(0) - p0) for h in hs])


def variants(w, VE):
    """→ dict(O, Cc, Zc) 영상 · 검출 정보 (검출 실패면 None). 집게 · 배경은 그대로, 큐브만 옮김 / 옮기고 크기 1 로 확대.
    큐브 원래 자리 = 볼록 껍질 1.25 배 영역을 inpaint (TELEA), 옮긴 큐브 = 같은 영역을 affine 으로 옮겨 경계 흐림 섞기."""
    det = O.ss.detect(w, O.PRM)
    c = O.ss.target_compare(det, O.ref)
    if c is None:
        return None, None
    cx, cy = det["cube"]["u"] * w.shape[1], det["cube"]["v"] * w.shape[0]
    dx, dy = -c["du"] * 640.0, -c["dv"] * 480.0
    hull = np.array(det["cube"]["hull"], float).reshape(-1, 2)
    m0 = np.zeros(w.shape[:2], np.uint8)
    cv2.fillConvexPoly(m0, ((hull - [cx, cy]) * 1.25 + [cx, cy]).astype(np.int32), 255)
    bg = cv2.inpaint(w, cv2.dilate(m0, np.ones((5, 5), np.uint8)), 7, cv2.INPAINT_TELEA)
    mf = cv2.GaussianBlur(m0.astype(np.float32) / 255.0, (0, 0), 2)
    out = {"O": w}
    s = 1.0 / c["size"] if c["size"] < 0.97 else 1.0
    for k, sc in (("Cc", 1.0), ("Zc", s)):
        M = cv2.getRotationMatrix2D((float(cx), float(cy)), 0.0, float(sc))
        M[0, 2] += dx
        M[1, 2] += dy
        P = cv2.warpAffine(w, M, (w.shape[1], w.shape[0]), borderMode=cv2.BORDER_REPLICATE)
        mk = cv2.warpAffine(mf, M, (w.shape[1], w.shape[0]))[..., None]
        out[k] = (bg * (1 - mk) + P * mk).astype(np.uint8)
    return out, dict(du=c["du"], dv=c["dv"], size=c["size"], edge=bool(c["edge"]), scale=s)


def main():
    sys.path.insert(0, R2.VD)
    import sg_vis_eval as VE
    import v_common as V
    import v02_engine as E

    V.CKPT = pathlib.Path(R2.CK)
    print("CKPT", V.CKPT, "→", OUTF, flush=True)
    t0 = time.time()
    SR, C = B2.scenes_real()
    info, em, d3 = O.load_ds(f"{O.P3}/dataset")
    SH = []
    for ep in range(3, 43):
        e = d3[d3.episode_index == ep].sort_values("frame_index")
        st = np.stack(e["observation.state"].values).astype(float)
        ac = np.stack(e["action"].values).astype(float)
        ci = O.sg_phase.analyze(st, ac, 30)["_idx"]["close"]
        want = [ci - b for b in BACK if ci - b >= 0]
        fw = O.frames(f"{O.P3}/dataset", info, em, ep, want)
        ff = O.frames(f"{O.P3}/dataset", info, em, ep, want, cam="front")
        for k in want:
            SH.append(dict(kind="human", ep=ep, lab="H", frame=k, back=ci - k, state=st[k], front=ff[k], wrist=fw[k]))
    print(f"장면 실물 {len(SR)} · 사람 {len(SH)} · {time.time() - t0:.0f}s", flush=True)
    eng = E.Engine(n_noise=8)
    RES, META = [], []
    for n, s in enumerate(SR + SH):
        if s["kind"] == "robot":
            m = C[s["chunk"]]
            f = R2.rgb(f"{O.R}/diag/obs/c{s['chunk']:05d}_front.png")
            w = R2.rgb(f"{O.R}/diag/obs/c{s['chunk']:05d}_wrist.png")
            q = np.array(m["obs_state"], float)
            h = min(49, int(m.get("applied_delay") or 0) + 20)
            keys = ["O", "Cc", "Zc"]
        else:
            f, w, q, h = s["front"], s["wrist"], s["state"], 20
            keys = ["O", "Cc", "Zc"]
        imgs, info_ = variants(w, VE)
        if imgs is None:
            continue
        A = eng.run(q, [(f, imgs[k]) for k in keys])
        RES.append({k: disp(A[i], q, (h, 49)).tolist() for i, k in enumerate(keys)})
        META.append(dict(kind=s["kind"], ep=s["ep"], lab=s["lab"], chunk=s.get("chunk"), frame=s["frame"], back=s.get("back"), h=h,
                         grip=float(q[5]), z=float(BB.tip(q)[0][2]), **info_))
        if n % 25 == 0:
            print(f"  {n}/{len(SR) + len(SH)} · {time.time() - t0:.0f}s", flush=True)
    json.dump(dict(ckpt=R2.CK, back=BACK, scenes=META, res=RES, sec=round(time.time() - t0, 1)),
              open(OUTF, "x"), ensure_ascii=False, default=float)
    print("B10_DONE", f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
