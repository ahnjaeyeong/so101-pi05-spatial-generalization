#!/home/user/so101-env/bin/python
"""S2 카메라 떨림의 번짐 (모션 블러) → 추론 (GPU 재추론, 로봇 · 카메라 연결 없음).
손목 영상에 직선 모션 블러 (가로 · 세로, 길이 5 · 11 px) 를 넣고 예측 chunk 의 끝 이동 (FK, 적용 구간 끝 − 지금; 바깥 · 옆 · 높이 cm) 과
닫기 (chunk 안 그리퍼가 시작 − 8 아래) 비율이 원래 영상 대비 어떻게 바뀌는지. 장면 = b2 와 같은 실물 닫기 직전 chunk · 사람 닫기 10 프레임 전.
  PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 nice -n 10 ~/so101-env/bin/python b4_blur.py → ../data/blur.npz · blur.json
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

CONDS = [("orig", None, 0), ("h5", "h", 5), ("h11", "h", 11), ("v5", "v", 5), ("v11", "v", 11)]


def blur(img, d, L):
    k = np.zeros((L, L), np.float32)
    if d == "h":
        k[L // 2, :] = 1
    else:
        k[:, L // 2] = 1
    return cv2.filter2D(img, -1, k / k.sum(), borderType=cv2.BORDER_REPLICATE)


def main():
    sys.path.insert(0, R2.VD)
    import v_common as V
    import v02_engine as E

    V.CKPT = pathlib.Path(R2.CK)
    t0 = time.time()
    SR, C = B2.scenes_real()
    SH = [s for s in B2.scenes_human() if True]
    SH = SH[::2]  # 닫기 10 프레임 전만 (scenes_human 은 [ci−10, ci−20] 순서)
    eng = E.Engine(n_noise=8)
    P, G, META = [], [], []
    for n, s in enumerate(SR + SH):
        if s["kind"] == "robot":
            m = C[s["chunk"]]
            z = np.load(f"{O.R}/diag/chunks/c{s['chunk']:05d}.npz")
            f = R2.rgb(f"{O.R}/diag/obs/c{s['chunk']:05d}_front.png")
            w = R2.rgb(f"{O.R}/diag/obs/c{s['chunk']:05d}_wrist.png")
            st, kw, h = m["obs_state"], dict(prefix=z["prefix"], delay=m.get("inference_delay")), min(49, int(m.get("applied_delay") or 0) + 20)
        else:
            f, w, st, kw, h = s["front"], s["wrist"], s["state"], {}, 20
        imgs = [(f, w if d is None else blur(w, d, L)) for _, d, L in CONDS]
        A = eng.run(st, imgs, **kw)                                   # (K, 8, 50, 6)
        p0 = BB.tip(st)[0]
        tips = BB.tip(A[:, :, h, :5].reshape(-1, 5)).reshape(len(CONDS), -1, 3).mean(1)
        P.append(np.array([BB.decomp(p0, t - p0) for t in tips]))
        G.append((A[:, :, :, 5].min(2) < A[:, :, :1, 5].min(2) - 8).mean(1))   # (K,) 닫기 비율
        META.append(dict(kind=s["kind"], ep=s["ep"], lab=s["lab"], chunk=s.get("chunk"), frame=s["frame"]))
        if n % 25 == 0:
            print(f"  {n}/{len(SR) + len(SH)} · {time.time() - t0:.0f}s", flush=True)
    np.savez_compressed(os.path.join(O.OUT, "blur.npz"), P=np.array(P), G=np.array(G), conds=np.array([c[0] for c in CONDS]))
    json.dump(dict(ckpt=R2.CK, scenes=META, sec=round(time.time() - t0, 1)), open(os.path.join(O.OUT, "blur.json"), "w"), indent=1, default=float)
    print("B4_DONE", f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
