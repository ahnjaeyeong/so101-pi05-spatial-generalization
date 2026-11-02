"""F1 g_rep · 평가 MAE 의 픽셀 기준선 (CPU). f1_sensitivity.analyze 와 같은 계산을 wrist 픽셀 특징으로.

목적: g_rep < 1 이 특징 탓인지, ridge 축소·편집(move_blob) 방식 탓인지 가르는 기준값.
특징: wrist RGB 32×24, wrist 빨강 마스크 64×48 (f1_probe 기준선과 같은 정의).
  train = f1_baselines/<kind>.npy (labels_v2 probe_ok 순서 = f1_features meta train 순서)
  edit  = f1_extract.make_images 로 같은 편집 영상을 다시 만들어 계산
  eval  = 평가 롤아웃 wrist 프레임
출력: f1_results/sensitivity_baselines.json
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f1_extract as FE  # noqa: E402
import f1_sensitivity as S  # noqa: E402

C = FE.C
OUT = FE.OUT


def feat(img, kind):
    if kind == "wrist_rgb":
        return cv2.resize(img, (32, 24), interpolation=cv2.INTER_AREA).astype(np.float32).ravel() / 255
    return cv2.resize(C.red_mask(img).astype(np.float32), (64, 48), interpolation=cv2.INTER_AREA).ravel() / 255


def main():
    T, Ed, Ev, folds, ev_ok, ev_in = S.load_sets()
    fit = json.load(open(OUT / "folds.json"))
    cache, dcache = {}, {}
    wr_ed = []
    for _, r in Ed.iterrows():
        res = FE.make_images(r.to_dict(), cache, fit, dcache)
        assert res is not None
        wr_ed.append(res[1])
    wr_ev = [C.frames(r.ds, int(r.ep), "wrist", int(r.frame), int(r.frame), cache)[0] for _, r in Ev.iterrows()]
    out = {}
    for kind in ("wrist_mask", "wrist_rgb"):
        Xtr = np.load(OUT / "f1_baselines" / f"{kind}.npy")
        assert len(Xtr) == len(T)
        Xed = np.stack([feat(w, kind) for w in wr_ed])
        Xev = np.stack([feat(w, kind) for w in wr_ev])
        out[kind] = S.analyze(Xtr, Xed, Xev, T, Ed, Ev, folds, ev_ok, ev_in)
        print(kind, json.dumps(out[kind]), flush=True)
    json.dump(out, open(OUT / "f1_results/sensitivity_baselines.json", "w"), indent=1)


if __name__ == "__main__":
    main()
