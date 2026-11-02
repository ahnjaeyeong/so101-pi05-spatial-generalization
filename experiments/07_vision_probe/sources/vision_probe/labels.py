"""Vision/VLM linear probe 용 라벨 추출 (CPU 만, 읽기 전용). d2 학습 256편 wrist 영상.

프레임 표본: 판마다 움직이기 시작(m) ~ 첫 파지(c) 구간. c−90 … c 는 3 프레임 간격, 그 앞은 10 프레임 간격.
프레임마다:
  큐브   : 가장 큰 빨강 덩어리 (pregrasp_angles.red_mask_rgb). 중심 (cu, cv), 넓이, bbox, 테두리 닿음 여부
  손가락 : 아래쪽 절반에서 영상 아래 테두리에 닿는 어두운 덩어리(V < 70, 넓이 > 1500) 중 왼쪽·오른쪽 가장 큰 것,
           각 덩어리의 가장 위 점 = 손가락 끝 (lu, lv), (ru, rv). 둘 다 있을 때 집게 중심 = 두 끝의 가운데
  상대   : du, dv = 큐브 중심 − 집게 중심 (px, 640×480 기준). cm 근사 = px / (√넓이 / 2.5)
  roll 보정: u 축 각도 θ = 0.91·wrist_roll − 5.5° (exp2b 사람 시연 맞춤, u ≈ 반지름 · v ≈ 접선 방향)
            → (tan, rad) = 회전(du, dv; θ) / (px/cm). 부호 규약은 exp2b roll_model 과 같다 (v 축 접선 −).
  상태   : 관절 6개 (state), 그리퍼, 닫힘까지 남은 시간
출력: labels.csv, label_check.json, label_examples.jpg
사용: PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python labels.py
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path.home() / "so101_runs/main_k8/d2/diag_grasp_bias"))
import common as C  # noqa: E402
from policy_probe import move_start  # noqa: E402

OUT = Path(__file__).resolve().parent
ROLL_B1, ROLL_B0 = 0.91, -5.5


def fingers(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    dark = (hsv[..., 2] < 70).astype(np.uint8)
    h, w = dark.shape
    dark[: h // 2] = 0
    n, lab, st, _ = cv2.connectedComponentsWithStats(dark)
    cand = [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] > 1500 and st[i, cv2.CC_STAT_TOP] + st[i, cv2.CC_STAT_HEIGHT] >= h - 2]
    tips = []
    for i in cand:
        ys, xs = np.nonzero(lab == i)
        k = int(np.argmin(ys))
        tips.append((float(xs[k]), float(ys[k]), int(st[i, cv2.CC_STAT_AREA])))
    left = [t for t in tips if t[0] < w / 2]
    right = [t for t in tips if t[0] >= w / 2]
    L = max(left, key=lambda t: t[2]) if left else None
    R = max(right, key=lambda t: t[2]) if right else None
    return L, R


def cube(img):
    b = C.blobs(C.red_mask(img), 60)
    if not b:
        return None
    a, (u, v), li, lab = max(b, key=lambda t: t[0])
    ys, xs = np.nonzero(lab == li)
    h, w = img.shape[:2]
    return dict(cu=u, cv=v, carea=a, cx0=int(xs.min()), cx1=int(xs.max()), cy0=int(ys.min()), cy1=int(ys.max()),
                border=bool(xs.min() <= 1 or ys.min() <= 1 or xs.max() >= w - 2 or ys.max() >= h - 2))


def main():
    T = pd.read_csv(C.OUT / "grasp_train.csv")
    data = C.load_parquet(C.D2 / "dataset")
    cache = {}
    rows, examples = [], []
    for e in range(256):
        s, a = data[e]
        c = int(T.loc[e, "grasp_f"])
        m = move_start(a)
        idx = sorted(set(list(range(m, max(m, c - 90), 10)) + list(range(max(m, c - 90), c + 1, 3))))
        fr = C.frames(C.D2 / "dataset", e, "wrist", idx[0], idx[-1], cache)
        for f in idx:
            img = fr[f - idx[0]]
            r = dict(ep=e, group=T.loc[e, "group"], K=T.loc[e, "K"] if isinstance(T.loc[e, "K"], str) else "", frame=f, t_to_close=(c - f) / 30,
                     cube_x=T.loc[e, "cube_x"], cube_y=T.loc[e, "cube_y"], grip=s[f, 5], roll=s[f, 4])
            for i, j in enumerate(C.JOINTS):
                r[f"s_{j}"] = s[f, i]
            cb = cube(img)
            L, R = fingers(img)
            if cb:
                r.update(cb)
            if L:
                r["lu"], r["lv"] = L[0], L[1]
            if R:
                r["ru"], r["rv"] = R[0], R[1]
            if cb and L and R:
                mu, mv = (L[0] + R[0]) / 2, (L[1] + R[1]) / 2
                pxcm = math.sqrt(cb["carea"]) / 2.5
                du, dv = cb["cu"] - mu, cb["cv"] - mv
                th = math.radians(ROLL_B0 + ROLL_B1 * s[f, 4])
                au = np.array([math.sin(th), math.cos(th)])          # u 축 → (tan, rad)
                av = -np.array([math.cos(th), -math.sin(th)])        # v 축 → (tan, rad)
                tr = (du * au + dv * av) / pxcm
                r.update(mu=mu, mv=mv, du=du, dv=dv, px_per_cm=pxcm, du_cm=du / pxcm, dv_cm=dv / pxcm, tan_cm=tr[0], rad_cm=tr[1])
            rows.append(r)
            if e in (5, 70, 150, 220) and f in (idx[0], c - 60, c - 30, c - 9, c):
                ex = img.copy()
                if cb:
                    cv2.drawMarker(ex, (int(cb["cu"]), int(cb["cv"])), (0, 255, 255), cv2.MARKER_CROSS, 25, 2)
                for t in (L, R):
                    if t:
                        cv2.circle(ex, (int(t[0]), int(t[1])), 9, (0, 255, 0), 2)
                if cb and L and R:
                    cv2.drawMarker(ex, (int(mu), int(mv)), (255, 0, 255), cv2.MARKER_TILTED_CROSS, 25, 2)
                cv2.putText(ex, f"e{e} t-{(c - f) / 30:.1f}s roll{s[f, 4]:.0f}", (5, 25), 0, 0.8, (255, 255, 0), 2)
                examples.append(cv2.resize(ex, (320, 240)))
    D = pd.DataFrame(rows)
    D.to_csv(OUT / "labels.csv", index=False)
    if examples:
        while len(examples) % 5:
            examples.append(np.zeros_like(examples[0]))
        im = np.vstack([np.hstack(examples[i:i + 5]) for i in range(0, len(examples), 5)])
        cv2.imwrite(str(OUT / "label_examples.jpg"), cv2.cvtColor(im, cv2.COLOR_RGB2BGR))
    # 점검 요약
    bins = [(-0.01, 0.34), (0.34, 1.0), (1.0, 2.0), (2.0, 3.0), (3.0, 99)]
    chk = {"n_frames": len(D), "n_eps": int(D.ep.nunique())}
    for lo, hi in bins:
        d = D[(D.t_to_close > lo) & (D.t_to_close <= hi)]
        chk[f"t_to_close_{lo:.2f}_{hi:.0f}s"] = dict(
            n=len(d), cube=float(d.cu.notna().mean()), cube_no_border=float((d.cu.notna() & ~d.border.fillna(True).astype(bool)).mean()),
            both_fingers=float((d.lu.notna() & d.ru.notna()).mean()), label=float(d.du.notna().mean()))
    # 집게 중심 안정성: 그리퍼 열림 구간별 중심 위치 SD (px)
    ok = D[D.mu.notna()]
    gb = pd.cut(ok.grip, [0, 5, 10, 15, 20, 25, 30, 40, 60])
    chk["grip_center_by_opening"] = {str(k): dict(n=int(len(g)), mu_med=float(g.mu.median()), mu_sd=float(g.mu.std()), mv_med=float(g.mv.median()),
                                                  mv_sd=float(g.mv.std())) for k, g in ok.groupby(gb, observed=True)}
    lab = D[D.du.notna() & (D.t_to_close <= 1.0)]
    chk["last1s_label_stats"] = dict(n=len(lab), du_cm_sd=float(lab.du_cm.std()), dv_cm_sd=float(lab.dv_cm.std()),
                                     tan_sd=float(lab.tan_cm.std()), rad_sd=float(lab.rad_cm.std()),
                                     du_cm_med=float(lab.du_cm.median()), dv_cm_med=float(lab.dv_cm.median()),
                                     roll_sd=float(lab.roll.std()), px_per_cm_med=float(lab.px_per_cm.median()))
    json.dump(chk, open(OUT / "label_check.json", "w"), indent=1)
    print(json.dumps(chk, indent=1))


if __name__ == "__main__":
    main()
