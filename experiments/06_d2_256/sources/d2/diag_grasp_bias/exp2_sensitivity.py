"""실험 2: 접근 단계별 · 카메라별 큐브 위치 민감도 (d2 20k, 학습 T1 128편, 고정 noise 4개 — 조건끼리 같은 noise).

단계: start = 움직이기 시작한 프레임 m · mid = m 과 pre 의 가운데 · pre = 첫 파지 30 프레임(1 s) 전.
조건 (같은 관측에서 영상만 편집, state 그대로):
  base                  원본
  f0                    front: 큐브 지우고(inpaint) 같은 자리에 다시 붙임 — 편집 자체의 영향 대조
  f+ / f-               front: 큐브를 접선 방향(로봇 왼쪽 +) 으로 ±2 cm 옮김 (H 로 px 계산, 크기 변화는 무시)
  w0                    wrist: 같은 자리 다시 붙임 (대조)
  wu+/wu- , wv+/wv-     wrist: 큐브를 영상 가로(u)/세로(v) 로 ±1 cm 상당 옮김 (1 cm = √넓이 / 2.5 px)
front 큐브는 계획 위치 40 px 안 빨강 덩어리, 넓이가 시작 넓이 0.5 배 이상일 때만 (팔에 가리면 건너뜀). wrist 는 가장 큰 빨강 덩어리.
출력: exp2/sens.npz (chunks: noise × N × 50 × 6), exp2/rows.csv (관측·조건 목록)
사용: nice -n 19 env PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python exp2_sensitivity.py
"""
import time

import cv2
import numpy as np
import pandas as pd

import common as C
import probe_core as PC
from policy_probe import load_obs, move_start

OUT = C.OUT / "exp2"
D_FRONT_CM = 2.0
D_WRIST_CM = 1.0


def find_blob(img, near=None, max_d=40, min_area=60):
    b = C.blobs(C.red_mask(img), min_area)
    if near is not None:
        b = [t for t in b if np.hypot(t[1][0] - near[0], t[1][1] - near[1]) <= max_d]
    if not b:
        return None
    a, (u, v), li, lab = max(b, key=lambda t: t[0])
    return a, (u, v), (lab == li).astype(np.uint8)


def move_blob(img, mask, du, dv):
    """mask 영역을 지우고(inpaint) (du, dv) px 옮겨 붙인다. du=dv=0 이면 같은 자리 다시 붙이기."""
    big = cv2.dilate(mask, np.ones((7, 7), np.uint8))
    ys, xs = np.nonzero(big)
    pix = img[ys, xs].copy()
    bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    out = cv2.cvtColor(cv2.inpaint(bgr, big * 255, 5, cv2.INPAINT_TELEA), cv2.COLOR_BGR2RGB)
    yy, xx = ys + int(round(dv)), xs + int(round(du))
    ok = (yy >= 0) & (yy < img.shape[0]) & (xx >= 0) & (xx < img.shape[1])
    out[yy[ok], xx[ok]] = pix[ok]
    return out


def main():
    OUT.mkdir(exist_ok=True)
    T = pd.read_csv(C.OUT / "grasp_train.csv")
    data = C.load_parquet(C.D2 / "dataset")
    cache = {}
    eps = [e for e in range(256) if T.loc[e, "task"] == "T1"]
    E = PC.Engine("020000", n_noise=4)
    t0 = time.time()
    rows, chunks = [], []
    for i0 in range(0, len(eps), 8):
        Fb, Wb, Sb = [], [], []
        for e in eps[i0:i0 + 8]:
            s, a = data[e]
            m = move_start(a)
            pre = max(0, int(T.loc[e, "grasp_f"]) - 30)
            phases = {"start": m, "mid": (m + pre) // 2, "pre": pre}
            x, y = T.loc[e, "cube_x"], T.loc[e, "cube_y"]
            u0, v0 = C.cm_to_px(x, y)
            ur = np.array([x, y]) - C.BASE
            ur /= np.linalg.norm(ur)
            ut = np.array([-ur[1], ur[0]])
            F0, _ = load_obs(C.D2 / "dataset", [(e, m)], cache)
            b0 = find_blob(F0[0], (u0, v0))
            area0 = b0[0] if b0 else None
            for ph, f in phases.items():
                F, W = load_obs(C.D2 / "dataset", [(e, f)], cache)
                F, W, st = F[0], W[0], s[f]
                base = dict(ep=e, group=T.loc[e, "group"], phase=ph, frame=f, cube_x=x, cube_y=y, range_cm=T.loc[e, "range_cm"],
                            pan_exp=T.loc[e, "pan_exp"], human_pan=T.loc[e, "s_shoulder_pan"], grasp_f=int(T.loc[e, "grasp_f"]))

                def add(cond, fi, wi, **kw):
                    rows.append(dict(base, cond=cond, **kw))
                    Fb.append(fi)
                    Wb.append(wi)
                    Sb.append(st)

                add("base", F, W)
                bf = find_blob(F, (u0, v0))
                if bf and area0 and bf[0] >= 0.5 * area0:
                    add("f0", move_blob(F, bf[2], 0, 0), W)
                    for sg in (1, -1):
                        nx, ny = np.array([x, y]) + sg * D_FRONT_CM * ut
                        u1, v1 = C.cm_to_px(nx, ny)
                        add("f+" if sg > 0 else "f-", move_blob(F, bf[2], u1 - u0, v1 - v0), W,
                            d_pan_geom=C.pan_expected(nx, ny) - C.pan_expected(x, y))
                bw = find_blob(W, None)
                if bw:
                    pxcm = np.sqrt(bw[0]) / 2.5
                    add("w0", F, move_blob(W, bw[2], 0, 0), w_px_per_cm=pxcm, w_area=bw[0])
                    for name, du, dv in (("wu+", 1, 0), ("wu-", -1, 0), ("wv+", 0, 1), ("wv-", 0, -1)):
                        add(name, F, move_blob(W, bw[2], du * D_WRIST_CM * pxcm, dv * D_WRIST_CM * pxcm),
                            w_px_per_cm=pxcm, w_area=bw[0], w_u=bw[1][0] / W.shape[1], w_v=bw[1][1] / W.shape[0])
        ch = E.chunks(np.stack(Fb), np.stack(Wb), np.stack(Sb))[5]
        chunks.append(ch.astype(np.float32))
        print(f"{i0 + 8}/{len(eps)} eps · obs {sum(c.shape[1] for c in chunks)} · {time.time() - t0:.0f}s · gpu {E.gpu_busy_s:.0f}s", flush=True)
    np.savez_compressed(OUT / "sens.npz", chunks=np.concatenate(chunks, axis=1))
    pd.DataFrame(rows).to_csv(OUT / "rows.csv", index=False)
    print(f"done gpu_busy_s {E.gpu_busy_s:.0f}", flush=True)


if __name__ == "__main__":
    main()
