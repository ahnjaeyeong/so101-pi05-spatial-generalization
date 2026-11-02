"""카메라 해상도·조명 품질 측정 (CPU 만, 읽기 전용). π0.5 입력 전처리를 CPU 에서 그대로 재현해 잰다.

전처리 재현: lerobot.policies.common.vla_utils.resize_with_pad_torch (bilinear, antialias 없음, 640×480 → 224×168 + 위아래 28행 검은 패딩),
            modeling_pi05._preprocess_images 와 같이 float [0,1] 로 넣는다.
주의: 여기서 '검출'은 우리 라벨용 빨강 HSV 마스크다. π0.5 내부 인식 성능이 아니다.

프레임 (판마다, d2 학습 256편 + 평가 롤아웃 5판):
  start = 움직이기 시작 m, mid = m 과 c−90 의 가운데, pre3/pre2/pre1 = 첫 닫힘 c 의 90/60/30 프레임 전
  (평가 판의 c = 첫 닫힘 이벤트, grasp_eval.csv event 0)
  평가 판은 추가로 0/15/30/60/90 프레임 (카메라 warmup 영향 확인)
카메라마다 (front, wrist):
  640 원본: 빨강 덩어리 bbox w·h, 넓이, 중심
  224 입력: 같은 마스크로 bbox w·h, 넓이, 중심(224 → 640 좌표로 환산), 패치(14 px) 수
  밝기: 큐브 V 평균, 주변 고리(바깥 5–15 px) V 평균, 전체 V 평균·1/99 백분위·포화(>250) 비율
  대비: Lab L 차(큐브 − 고리), ΔE(Lab) 큐브 대 고리
  흐림: 큐브 둘레 bbox+10 px 잘라 Laplacian 분산 (640, 224 각각), 경계 기울기 / L 차 (대비로 나눈 선명도)
  색: 밝고 채도 낮은 픽셀(탁자·벽)의 R/G, B/G 중앙값
  움직임: 팔 5관절 속도 노름 (°/s, state)
출력: iq_frames.csv, iq_examples_224.jpg
사용: nice -n 19 env PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python image_quality.py
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import torch

sys.path.insert(0, str(Path.home() / "so101_runs/main_k8/d2/diag_grasp_bias"))
import common as C  # noqa: E402
from policy_probe import move_start  # noqa: E402
from lerobot.policies.common.vla_utils import resize_with_pad_torch  # noqa: E402

OUT = Path(__file__).resolve().parent
torch.set_num_threads(2)


def to224(img):
    t = torch.from_numpy(img).float().div(255)[None]          # [1,H,W,C] channels-last, float [0,1]
    r = resize_with_pad_torch(t, 224, 224)[0].numpy()
    return (r * 255).round().clip(0, 255).astype(np.uint8)


def blob(img, near=None, min_area=4):
    b = C.blobs(C.red_mask(img), min_area)
    if near is not None:
        b = [t for t in b if np.hypot(t[1][0] - near[0], t[1][1] - near[1]) < max(img.shape) * 0.12]
    if not b:
        return None
    a, (u, v), li, lab = max(b, key=lambda t: t[0])
    m = (lab == li).astype(np.uint8)
    ys, xs = np.nonzero(m)
    return dict(area=a, u=u, v=v, w=int(xs.max() - xs.min() + 1), h=int(ys.max() - ys.min() + 1), mask=m,
                x0=int(xs.min()), x1=int(xs.max()), y0=int(ys.min()), y1=int(ys.max()))


def quality(img, b, pre=""):
    r = {}
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB).astype(float)
    V = hsv[..., 2].astype(float)
    r[pre + "img_V_mean"] = V.mean()
    r[pre + "img_V_p01"], r[pre + "img_V_p99"] = np.percentile(V, [1, 99])
    r[pre + "img_sat_frac"] = float((img.max(-1) > 250).mean())
    bg = (hsv[..., 1] < 40) & (V > 120)
    if bg.sum() > 100:
        px = img[bg].astype(float)
        r[pre + "bg_RG"] = float(np.median(px[:, 0] / np.maximum(px[:, 1], 1)))
        r[pre + "bg_BG"] = float(np.median(px[:, 2] / np.maximum(px[:, 1], 1)))
        r[pre + "bg_V"] = float(np.median(V[bg]))
    if b is None:
        return r
    m = b["mask"].astype(bool)
    k = max(3, int(round(min(img.shape[:2]) / 96)))
    ring = cv2.dilate(b["mask"], np.ones((3 * k, 3 * k), np.uint8)).astype(bool) & ~cv2.dilate(b["mask"], np.ones((k, k), np.uint8)).astype(bool)
    r[pre + "cube_V"] = V[m].mean()
    r[pre + "cube_S"] = hsv[..., 1][m].mean()
    if ring.sum() > 5:
        r[pre + "ring_V"] = V[ring].mean()
        dL = lab[..., 0][m].mean() - lab[..., 0][ring].mean()
        r[pre + "dL"] = dL
        r[pre + "dE"] = float(np.linalg.norm(lab[m].mean(0) - lab[ring].mean(0)))
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY).astype(float)
        gx, gy = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3), cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        edge = cv2.dilate(b["mask"], np.ones((3, 3), np.uint8)).astype(bool) & ~cv2.erode(b["mask"], np.ones((3, 3), np.uint8)).astype(bool)
        gm = np.hypot(gx, gy)[edge].mean() if edge.any() else np.nan
        r[pre + "edge_grad"] = gm
        r[pre + "edge_grad_per_dE"] = gm / max(1.0, r[pre + "dE"])
        pad = max(4, k * 3)
        y0, y1 = max(0, b["y0"] - pad), min(img.shape[0], b["y1"] + pad + 1)
        x0, x1 = max(0, b["x0"] - pad), min(img.shape[1], b["x1"] + pad + 1)
        r[pre + "lapvar"] = float(cv2.Laplacian(gray[y0:y1, x0:x1], cv2.CV_64F).var())
    return r


def measure(ds, ep, s, frames_by_phase, cache, src, extra=None, ex=None):
    rows = []
    for ph, f in frames_by_phase.items():
        if f < 0 or f >= len(s):
            continue
        sp = float(np.linalg.norm(s[min(f + 1, len(s) - 1), :5] - s[max(f - 1, 0), :5]) * 15)  # °/s
        for cam in ("front", "wrist"):
            img = C.frames(ds, ep, cam, f, f, cache)[0]
            r = dict(src=src, ep=ep, phase=ph, frame=f, cam=cam, arm_speed=sp, **(extra or {}))
            near = None
            if cam == "front" and extra and "cube_x" in extra and not np.isnan(extra["cube_x"]):
                near = C.cm_to_px(extra["cube_x"], extra["cube_y"])
            b = blob(img, near, 30)
            r.update(quality(img, b, "o_"))
            if b:
                r.update(o_area=b["area"], o_w=b["w"], o_h=b["h"], o_u=b["u"], o_v=b["v"], o_border=bool(b["x0"] <= 1 or b["y0"] <= 1 or b["x1"] >= 638 or b["y1"] >= 478))
            i2 = to224(img)
            n2 = None if near is None else (near[0] * 0.35, near[1] * 0.35 + 28)
            b2 = blob(i2, n2 if b is None else (b["u"] * 0.35, b["v"] * 0.35 + 28), 2)
            r.update(quality(i2, b2, "m_"))
            if b2:
                r.update(m_area=b2["area"], m_w=b2["w"], m_h=b2["h"], m_patch_w=b2["w"] / 14, m_patch_h=b2["h"] / 14,
                         m_u640=b2["u"] / 0.35, m_v640=(b2["v"] - 28) / 0.35)
                if b:
                    r["centroid_shift_px640"] = float(np.hypot(r["m_u640"] - b["u"], r["m_v640"] - b["v"]))
            rows.append(r)
            if ex is not None and b2 is not None and len(ex) < 24 and ph in ("start", "pre1") and ep % 37 == 0:
                cy, cx = int(b2["v"]), int(b2["u"])
                crop = np.zeros((48, 48, 3), np.uint8)
                y0, x0 = max(0, cy - 24), max(0, cx - 24)
                c = i2[y0:y0 + 48, x0:x0 + 48]
                crop[: c.shape[0], : c.shape[1]] = c
                big = cv2.resize(crop, (192, 192), interpolation=cv2.INTER_NEAREST)
                cv2.putText(big, f"{src[:3]} e{ep} {ph} {cam}", (2, 12), 0, 0.4, (255, 255, 0), 1)
                cv2.putText(big, f"{b2['w']}x{b2['h']}px", (2, 186), 0, 0.45, (255, 255, 0), 1)
                ex.append(big)
    return rows


def main():
    T = pd.read_csv(C.OUT / "grasp_train.csv")
    data = C.load_parquet(C.D2 / "dataset")
    cache, rows, ex = {}, [], []
    for e in range(256):
        s, a = data[e]
        c, m = int(T.loc[e, "grasp_f"]), move_start(a)
        ph = {"start": m, "mid": (m + max(m, c - 90)) // 2, "pre3": c - 90, "pre2": c - 60, "pre1": c - 30}
        rows += measure(C.D2 / "dataset", e, s, ph, cache, "train",
                        dict(group=T.loc[e, "group"], cube_x=T.loc[e, "cube_x"], cube_y=T.loc[e, "cube_y"]), ex)
        if e % 32 == 31:
            print(f"train {e + 1}/256", flush=True)
    E = pd.read_csv(C.OUT / "grasp_eval.csv")
    for run in sorted(E.run.unique()):
        ds = C.D2 / "eval/rollouts" / run / "dataset"
        ed = C.load_parquet(ds)
        for e, (s, a) in ed.items():
            ev = E[(E.run == run) & (E.ep == e) & (E.event == 0)].iloc[0]
            c, m = int(ev.frame), move_start(a)
            ph = {"start": m, "mid": (m + max(m, c - 90)) // 2, "pre3": c - 90, "pre2": c - 60, "pre1": c - 30,
                  "f000": 0, "f015": 15, "f030": 30, "f060": 60, "f090": 90}
            rows += measure(ds, e, s, ph, cache, "eval", dict(run=run, cube_x=ev.start_x, cube_y=ev.start_y), ex)
    D = pd.DataFrame(rows)
    D.to_csv(OUT / "iq_frames.csv", index=False)
    if ex:
        while len(ex) % 6:
            ex.append(np.zeros_like(ex[0]))
        im = np.vstack([np.hstack(ex[i:i + 6]) for i in range(0, len(ex), 6)])
        cv2.imwrite(str(OUT / "iq_examples_224.jpg"), cv2.cvtColor(im, cv2.COLOR_RGB2BGR))
    print("rows", len(D))


if __name__ == "__main__":
    main()
