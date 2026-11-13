#!/home/user/so101-env/bin/python
"""L3 (GPU 재추론, 로봇 · 카메라 연결 없음). 설계: ../00_design.md
실물 파지 직전 chunk (o1 의 chunks_err.csv) 마다, 실물 입력 그대로 (관절값 · front · wrist · 저장 noise · prefix · delay) 다시 추론해 재현을 확인하고,
  A: 손목 영상만 바꿈 — 직전 chunk 의 손목 · 큐브 중심 기준 ±u · ±v 옮김 · ×1.04 / ×0.96 (흔들림 크기, o1 고역 sd 의 약 2 배)
  B: 관절값만 직전 chunk 의 것
  C: 입력 그대로 noise 만 바꿈 (seed 2026 bank 8)
엔진 = vd_20261103_01/scripts/v02_engine.Engine (수정 없음), 체크포인트만 sgft01 010000 으로 (이 프로세스 안에서만).
  PYTHONDONTWRITEBYTECODE=1 nice -n 10 ~/so101-env/bin/python o2_reinfer.py [--limit K]
→ ../data/reinfer.npz · ../data/reinfer_meta.json
"""
import argparse
import json
import os
import pathlib
import sys
import time

import cv2
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data")
R = os.path.expanduser("~/so101_runs/main_k8/sgft01_real_eval/eval/rollouts/20261109_100345_10k_t01_02_03_04_05_06_07_08_ft_series")
VD = os.path.expanduser("~/so101_runs/main_k8/d2/visual_dependency/vd_20261103_01/scripts")
TOOLS = os.path.expanduser("~/so101_runs/main_k8/r1_r2_collection/tools")
CK = os.environ["OD_CK"]  # sgb01 복사본: 체크포인트는 환경변수 OD_CK 로 (필수). 원본은 sgft01 010000 고정
SHIFT_PX = {"u+": (12, 0, 0, 1.0), "u-": (-12, 0, 0, 1.0), "v+": (0, 8, 0, 1.0), "v-": (0, -8, 0, 1.0), "z+": (0, 0, 0, 1.04), "z-": (0, 0, 0, 0.96)}


def rgb(p):
    return cv2.cvtColor(cv2.imread(p), cv2.COLOR_BGR2RGB)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    a = ap.parse_args()
    sys.path.insert(0, VD)
    sys.path.insert(0, TOOLS)
    os.environ["R12_CONFIG"] = os.path.expanduser("~/so101_runs/main_k8/r1_r2_collection/config/sg50.yaml")
    import sg_sticker as ss
    import sg_vis_eval as VE
    import v_common as V
    import v02_engine as E

    V.CKPT = pathlib.Path(CK)
    C = {json.loads(x)["chunk_id"]: json.loads(x) for x in open(f"{R}/diag/chunks.jsonl") if x.strip()}
    rows = pd.read_csv(os.path.join(OUT, "chunks_err.csv"))
    rows = rows[~rows["du"].isna()]
    rows = rows[[(c - 1) in C and C[c - 1]["episode"] == C[c]["episode"] for c in rows.chunk]]
    if a.limit:
        rows = rows.iloc[: a.limit]
    P = ss.load_params()
    t0 = time.time()
    eng = E.Engine(n_noise=8)
    print(f"엔진 {time.time() - t0:.0f}s · chunk {len(rows)}", flush=True)

    def load(cid):
        z = np.load(f"{R}/diag/chunks/c{cid:05d}.npz")
        return C[cid], z, rgb(f"{R}/diag/obs/c{cid:05d}_front.png"), rgb(f"{R}/diag/obs/c{cid:05d}_wrist.png")

    # 재현 확인: delay 후보 (inference_delay / applied_delay / real_delay) 중 저장 chunk 와 맞는 것
    pick, rep = None, {}
    for key in ("applied_delay", "inference_delay", "real_delay"):
        d = []
        for cid in rows.chunk.iloc[:4]:
            m, z, f, w = load(int(cid))
            A = eng.run(m["obs_state"], [(f, w)], prefix=z["prefix"], delay=m.get(key), noise=z["noise"])[0, 0]
            d.append(float(np.abs(A - z["processed"]).max()))
        rep[key] = d
        print("재현", key, [round(x, 3) for x in d], flush=True)
        if pick is None or max(d) < max(rep[pick]):
            pick = key
    conds = ["orig", "wrist_prev"] + list(SHIFT_PX)
    OUTA, OUTB, OUTC, REPL, META = [], [], [], [], []
    for n, r in enumerate(rows.itertuples()):
        cid = int(r.chunk)
        m, z, f, w = load(cid)
        mp, zp, fp, wp = load(cid - 1)
        det = ss.detect(w, P)
        cu = det["cube"]
        cx, cy = cu["u"] * w.shape[1], cu["v"] * w.shape[0]
        imgs = [(f, w), (f, wp)] + [(f, VE.warp(w, cx, cy, *SHIFT_PX[k])) for k in SHIFT_PX]
        kw = dict(prefix=z["prefix"], delay=m.get(pick))
        A = eng.run(m["obs_state"], imgs, noise=z["noise"], **kw)[:, 0]                      # (K, 50, 6)
        B = eng.run(mp["obs_state"], [(f, w)], noise=z["noise"], **kw)[0, 0]                  # (50, 6)
        Cn = eng.run(m["obs_state"], [(f, w)], **kw)[0]                                       # (8, 50, 6)
        OUTA.append(A)
        OUTB.append(B)
        OUTC.append(Cn)
        REPL.append(float(np.abs(A[0] - z["processed"]).max()))
        META.append(dict(chunk=cid, prev=cid - 1, ep=int(r.ep), lab=r.lab, applied_delay=m.get("applied_delay"), delay_used=m.get(pick),
                         obs_state=m["obs_state"], prev_state=mp["obs_state"], cube_px=[cx, cy]))
        if n % 20 == 0:
            print(f"  {n}/{len(rows)} · {time.time() - t0:.0f}s · 재현 {REPL[-1]:.3f}", flush=True)
    np.savez_compressed(os.path.join(OUT, "reinfer.npz"), A=np.array(OUTA, np.float32), B=np.array(OUTB, np.float32), C=np.array(OUTC, np.float32),
                        replay=np.array(REPL), conds=np.array(conds))
    json.dump(dict(ckpt=CK, delay_key=pick, replay_check=rep, shift_px=SHIFT_PX, conds=conds, chunks=META, sec=round(time.time() - t0, 1)),
              open(os.path.join(OUT, "reinfer_meta.json"), "w"), indent=1, default=float)
    print("O2_DONE", f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
