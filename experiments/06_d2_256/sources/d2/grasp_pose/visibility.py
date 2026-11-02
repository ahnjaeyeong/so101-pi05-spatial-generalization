"""우리 d2 영상에서 접근 중 큐브 가시성 · 그림자 · 가림을 재고 그리퍼 기울기(FK)와 맞춘다 (CPU, 읽기만).

프레임: 판마다 움직이기 시작 m ~ 첫 닫힘 c. c−90…c 는 6 프레임 간격, 그 앞은 15 프레임 간격.
front (큐브는 닫힐 때까지 움직이지 않는다고 본다):
  발자국 F = start 프레임 빨강 덩어리 (2 px 넓힘). 매 프레임 F 안 픽셀을 나눈다:
    red_vis   = 지금도 빨강인 비율
    occ_dark  = 어둡고 채도 낮음 (V<90, S<90) = 로봇 몸체(검정)로 가림
    occ_other = 그 밖에 시작 프레임과 RGB 차가 40 넘게 바뀜 (다른 색 부품·흐림 등)
  cube_shade  = 보이는 빨강 픽셀 V / 같은 픽셀의 시작 V          (큐브 위 그림자·조명 변화)
  ring_shade  = 고리(F 바깥 6–16 px) 중 가리지 않은 픽셀 V / 시작 V (큐브 옆 탁자에 드리운 그림자)
  ambient     = 상자 영역(로봇이 닫힘 전 들어가지 않는 곳, y 395–470, x 120–520) V 중앙값 / 시작 값 (실내 조명 변화)
  vis_px224   = 보이는 빨강 픽셀 수 × 0.35² (π0.5 224 입력 기준 근사)
wrist:
  cube_V, cube_area, cu, cv (가장 큰 빨강), sharp = 경계 기울기/ΔE (image_quality 와 같은 정의)
  shade_near  = 큐브 둘레 고리(바깥 10–30 px) 중 손가락 아닌 픽셀 V / 영상 위쪽 1/4 의 밝은 탁자(V>100, S<60) V 중앙값
  finger_cover = 큐브 bbox 안 어두운 픽셀(V<70) 비율
FK: grasp_tilt.frames, 규약 A·B 둘 다 (tilt, pitch_r). 위치 통제용 큐브 거리·방향(grasp_train.csv).
출력: visibility_frames.csv
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

HOME = Path.home()
sys.path.insert(0, str(HOME / "so101_runs/main_k8/d2/diag_grasp_bias"))
import common as C  # noqa: E402
from policy_probe import move_start  # noqa: E402
import grasp_tilt as GT  # noqa: E402

OUT = Path(__file__).resolve().parent
BOX = (slice(395, 470), slice(120, 520))


def hsv(img):
    return cv2.cvtColor(img, cv2.COLOR_RGB2HSV)


def main():
    T = pd.read_csv(C.OUT / "grasp_train.csv")
    data = C.load_parquet(C.D2 / "dataset")
    cache, rows = {}, []
    for e in range(256):
        s, a = data[e]
        c, m = int(T.loc[e, "grasp_f"]), move_start(a)
        idx = sorted(set(list(range(m, max(m, c - 90), 15)) + list(range(max(m, c - 90), c + 1, 6))))
        Fr = C.frames(C.D2 / "dataset", e, "front", 0, c, cache)
        Wr = C.frames(C.D2 / "dataset", e, "wrist", idx[0], c, cache)
        f0 = Fr[min(m, len(Fr) - 1)]
        u0, v0 = C.cm_to_px(T.loc[e, "cube_x"], T.loc[e, "cube_y"])
        b = [t for t in C.blobs(C.red_mask(f0), 80) if np.hypot(t[1][0] - u0, t[1][1] - v0) < 60]
        if not b:
            continue
        _, _, li, lab = max(b, key=lambda t: t[0])
        F = cv2.dilate((lab == li).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
        ring = cv2.dilate(F.astype(np.uint8), np.ones((33, 33), np.uint8)).astype(bool) & ~cv2.dilate(F.astype(np.uint8), np.ones((13, 13), np.uint8)).astype(bool)
        h0 = hsv(f0)
        V0 = h0[..., 2].astype(float)
        amb0 = np.median(V0[BOX])
        q = s[idx, :5]
        tilt = {}
        for conv in ("A", "B"):
            aa, tip, _ = GT.frames(q + (GT.SHIFT["ours_d2"] if conv == "B" else 0))
            t, pr, _ = GT.tilt_terms(aa, tip)
            tilt[conv] = (t, pr, tip)
        for k, f in enumerate(idx):
            img = Fr[f]
            h = hsv(img)
            V, S = h[..., 2].astype(float), h[..., 1]
            red = C.red_mask(img).astype(bool)
            dark = (V < 90) & (S < 90)
            changed = np.abs(img.astype(int) - f0.astype(int)).max(-1) > 40
            nF = F.sum()
            r = dict(ep=e, group=T.loc[e, "group"], frame=f, t_to_close=(c - f) / 30, range_cm=T.loc[e, "range_cm"], bearing=T.loc[e, "bearing"],
                     tilt_A=tilt["A"][0][k], pitch_A=tilt["A"][1][k], tilt_B=tilt["B"][0][k], pitch_B=tilt["B"][1][k],
                     tip_z_B=tilt["B"][2][k, 2] * 100, roll=s[f, 4],
                     red_vis=(F & red).sum() / nF, occ_dark=(F & dark & ~red).sum() / nF, occ_other=(F & changed & ~red & ~dark).sum() / nF,
                     vis_px224=(F & red).sum() * 0.35 ** 2, ambient=np.median(V[BOX]) / amb0)
            vis = F & red
            if vis.sum() > 10:
                r["cube_shade"] = V[vis].mean() / max(1.0, V0[vis].mean())
            rr = ring & ~dark & ~red
            if rr.sum() > 20:
                r["ring_shade"] = V[rr].mean() / max(1.0, V0[rr].mean())
            w = Wr[f - idx[0]]
            hw = hsv(w)
            Vw = hw[..., 2].astype(float)
            bw = C.blobs(C.red_mask(w), 200)
            top = Vw[: w.shape[0] // 4][(hw[: w.shape[0] // 4, :, 1] < 60) & (Vw[: w.shape[0] // 4] > 100)]
            if bw:
                ar, (cu, cv), li2, lab2 = max(bw, key=lambda t: t[0])
                mk = (lab2 == li2).astype(np.uint8)
                ys, xs = np.nonzero(mk)
                r.update(w_cube_V=Vw[mk.astype(bool)].mean(), w_area=ar, w_cu=cu, w_cv=cv,
                         w_border=bool(xs.min() <= 1 or ys.min() <= 1 or xs.max() >= w.shape[1] - 2 or ys.max() >= w.shape[0] - 2))
                bb = (slice(ys.min(), ys.max() + 1), slice(xs.min(), xs.max() + 1))
                r["w_finger_cover"] = float((Vw[bb] < 70).mean())
                rg = cv2.dilate(mk, np.ones((61, 61), np.uint8)).astype(bool) & ~cv2.dilate(mk, np.ones((21, 21), np.uint8)).astype(bool) & (Vw >= 70)
                if rg.sum() > 50 and len(top) > 100:
                    r["w_shade_near"] = Vw[rg].mean() / np.median(top)
                gray = cv2.cvtColor(w, cv2.COLOR_RGB2GRAY).astype(float)
                gm = np.hypot(cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3), cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3))
                edge = cv2.dilate(mk, np.ones((3, 3), np.uint8)).astype(bool) & ~cv2.erode(mk, np.ones((3, 3), np.uint8)).astype(bool)
                lab_w = cv2.cvtColor(w, cv2.COLOR_RGB2LAB).astype(float)
                ring_w = cv2.dilate(mk, np.ones((31, 31), np.uint8)).astype(bool) & ~cv2.dilate(mk, np.ones((11, 11), np.uint8)).astype(bool)
                if ring_w.any():
                    dE = np.linalg.norm(lab_w[mk.astype(bool)].mean(0) - lab_w[ring_w].mean(0))
                    r["w_sharp"] = gm[edge].mean() / max(1.0, dE)
            if len(top) > 100:
                r["w_top_V"] = float(np.median(top))
            rows.append(r)
        if e % 32 == 31:
            print(f"{e + 1}/256", flush=True)
    pd.DataFrame(rows).to_csv(OUT / "visibility_frames.csv", index=False)


if __name__ == "__main__":
    main()
