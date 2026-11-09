#!/home/user/so101-env/bin/python
"""P10 큐브 × 배경 교차 (GPU 재추론, 로봇 · 카메라 연결 없음). prefix 없음, noise 8 평균.
장면: b10 실물 장면 중 그리퍼 열림 (상태값 ≥ 35) — 짝 = 큐브 자리가 가장 가까운 사람 판 (b8 human_ep) 의 닫기 10 프레임 전.
손목 영상 4 종 (큐브는 모두 닫기 프레임 중심 · 크기 1 로 붙임; 원래 큐브 자리는 inpaint):
  bg R/H = 실물 / 사람 손목 영상의 배경 · 집게 · 조명,  cube R/H = 실물 / 사람 영상에서 오려 낸 큐브 (볼록 껍질 1.25 배, 경계 흐림).
맥락 2 종: ctx R = 실물 front · 관절값, ctx H = 사람 front · 관절값 (영상만 4 종으로 바꿈).
측정: 예측 끝 이동 (넣은 관절값 기준) 바깥 · 옆 · 높이 cm, 시점 = 적용 구간 끝 (ctx R: 실물 applied_delay+20, ctx H: 20) · 49.
  PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 nice -n 10 ~/so101-env/bin/python b12_cross.py → ../data/cross.json
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
import b1_bias as BB  # noqa: E402
import b2_equilibrium as B2  # noqa: E402
import o1_real_chain as O  # noqa: E402
import o2_reinfer as R2  # noqa: E402

COMBOS = [("R", "R"), ("R", "H"), ("H", "R"), ("H", "H")]   # (bg, cube)


def extract(w):
    det = O.ss.detect(w, O.PRM)
    c = O.ss.target_compare(det, O.ref)
    if c is None:
        return None
    cx, cy = det["cube"]["u"] * w.shape[1], det["cube"]["v"] * w.shape[0]
    hull = np.array(det["cube"]["hull"], float).reshape(-1, 2)
    m0 = np.zeros(w.shape[:2], np.uint8)
    cv2.fillConvexPoly(m0, ((hull - [cx, cy]) * 1.25 + [cx, cy]).astype(np.int32), 255)
    bg = cv2.inpaint(w, cv2.dilate(m0, np.ones((5, 5), np.uint8)), 7, cv2.INPAINT_TELEA)
    mf = cv2.GaussianBlur(m0.astype(np.float32) / 255.0, (0, 0), 2)
    return dict(img=w, bg=bg, mf=mf, cx=cx, cy=cy, tx=cx - c["du"] * 640.0, ty=cy - c["dv"] * 480.0, size=c["size"], edge=bool(c["edge"]),
                du=c["du"], dv=c["dv"])


def paste(dst, src):
    """dst 의 배경 (큐브 지운 것) 위에 src 큐브를 닫기 프레임 중심 · 크기 1 로."""
    M = cv2.getRotationMatrix2D((float(src["cx"]), float(src["cy"])), 0.0, float(1.0 / src["size"]))
    M[0, 2] += src["tx"] - src["cx"]
    M[1, 2] += src["ty"] - src["cy"]
    sh = dst["img"].shape
    P = cv2.warpAffine(src["img"], M, (sh[1], sh[0]), borderMode=cv2.BORDER_REPLICATE)
    mk = cv2.warpAffine(src["mf"], M, (sh[1], sh[0]))[..., None]
    return (dst["bg"] * (1 - mk) + P * mk).astype(np.uint8)


def disp(A, q, hs):
    p0 = BB.tip(np.asarray(q, float))[0]
    return np.array([BB.decomp(p0, BB.tip(A[:, h, :5]).mean(0) - p0) for h in hs])


def scenes():
    H = json.load(open(os.path.join(O.OUT, "height.json")))
    MS = json.load(open(os.path.join(O.OUT, "momentum_source.json")))
    hmap = {m["chunk"]: m["human_ep"] for m in MS["scenes"] if m["kind"] == "robot"}
    return [m for m in H["scenes"] if m["kind"] == "robot" and m["grip"] >= 35 and m["chunk"] in hmap], hmap


def main():
    sys.path.insert(0, R2.VD)
    import v_common as V
    import v02_engine as E

    V.CKPT = pathlib.Path(R2.CK)
    t0 = time.time()
    SR, hmap = scenes()
    C = {json.loads(x)["chunk_id"]: json.loads(x) for x in open(f"{O.R}/diag/chunks.jsonl") if x.strip()}
    hs_all = B2.scenes_human()
    SH = {}
    for s in hs_all:
        if s["ep"] not in SH or s["frame"] > SH[s["ep"]]["frame"]:
            SH[s["ep"]] = s
    print(f"장면 실물 {len(SR)} · {time.time() - t0:.0f}s", flush=True)
    eng = E.Engine(n_noise=8)
    RES, META = [], []
    for n, s in enumerate(SR):
        m = C[s["chunk"]]
        h = SH[hmap[s["chunk"]]]
        xr = extract(R2.rgb(f"{O.R}/diag/obs/c{s['chunk']:05d}_wrist.png"))
        xh = extract(h["wrist"])
        if xr is None or xh is None:
            continue
        src = {"R": xr, "H": xh}
        imgsW = [paste(src[b], src[c]) for b, c in COMBOS]
        ctx = {"R": (R2.rgb(f"{O.R}/diag/obs/c{s['chunk']:05d}_front.png"), np.array(m["obs_state"], float), min(49, int(m.get("applied_delay") or 0) + 20)),
               "H": (h["front"], np.array(h["state"], float), 20)}
        r = {}
        for cn, (f, q, hh) in ctx.items():
            A = eng.run(q, [(f, w) for w in imgsW])
            for k, (b, c) in enumerate(COMBOS):
                r[f"{cn}_bg{b}_cube{c}"] = disp(A[k], q, (hh, 49)).tolist()
        RES.append(r)
        META.append(dict(lab=s["lab"], ep=s["ep"], chunk=s["chunk"], human_ep=int(h["ep"]), grip=s["grip"], r_size=xr["size"], h_size=xh["size"],
                         r_edge=xr["edge"], h_edge=xh["edge"]))
        if n % 10 == 0:
            print(f"  {n}/{len(SR)} · {time.time() - t0:.0f}s", flush=True)
            if n == 0:
                cv2.imwrite(os.path.join(O.OUT, "cross_example.jpg"), np.hstack([cv2.resize(x, (320, 240)) for x in imgsW])[:, :, ::-1])
    json.dump(dict(ckpt=R2.CK, combos=COMBOS, scenes=META, res=RES, sec=round(time.time() - t0, 1)),
              open(os.path.join(O.OUT, "cross.json"), "w"), ensure_ascii=False, default=float)
    print("B12_DONE", f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
