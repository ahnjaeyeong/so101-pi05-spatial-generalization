#!/home/user/so101-env/bin/python
"""SG50 시각 의존 오프라인 시험 (GPU, 로봇 · 카메라 연결 없음) — 같은 관절값에서 카메라 영상만 바꿔 넣고 예측 action 이 그에 맞게
바뀌는지 본다 (vd_20261103 과 같은 생각). 엔진 = vd v02_engine.Engine (수정 없음, prefix 없음, noise = seed 2026 bank 앞 N 개).
사용자 (2026-11-06) 중점: ① 처음 숄더팬을 front 를 보고 돌리는지, ② 그 뒤 다시 맞출 때 손목을 보고 하는지, ③ 손목의 주황 닫기 프레임에 맞으면 잡는지.

V1 front→pan (A 의 start 장면 40): 판 i 의 관절값 · 손목 영상 + 판 j 의 시작 front (큐브가 다른 자리, 같은 S0) 로 바꿔 넣음 (j = 큐브 방향이
    가장 다른 3 판). 지표: 예측 pan 변화 (chunk 끝 − 지금) 와 사람 pan 변화 (같은 50 프레임) — front 주인 판 j 와의 상관 · 기울기,
    관절값 · 손목 주인 판 i 와의 상관. front 를 따르면 j 쪽 상관이 높음.
V2 wrist→다시 맞추기 (A · B 의 descent · pre_close 장면): 손목 영상을 큐브 중심 기준으로 옮김 (좌우 ±40 px · 앞뒤 ±30 px) · 돌림 (±8°) ·
    키움/줄임 (×1.12 / ×0.89). 지표: 바꾼 영상 − 원래 영상의 예측 action 차 (chunk 끝, 관절별) 를 영상 변화량으로 나눈 '시각 이득'.
    사람 이득 = 같은 장면들에서 '손목 큐브가 주황 프레임에서 벗어난 양' ↔ '사람이 그 뒤 50 프레임 동안 고친 양' 회귀 기울기.
    + front 만 다른 판 front 로 바꿨을 때 예측 변화 (작을수록 손목에 기댐).
V3 프레임 맞으면 닫기 (A 의 pre_close 40): 원래 영상 vs 손목 큐브를 프레임 밖으로 (좌우 60 px · 앞뒤 45 px) 옮긴 영상 — chunk 안 닫기
    (그리퍼 시작 − 8 아래) 비율.
  PYTHONDONTWRITEBYTECODE=1 nice -n 10 ~/so101-env/bin/python sg_vis_eval.py --out DIR --ckpt TAG=PATH [...] [--n 4] [--limit K] [--dry]
  → DIR/vis_raw/<tag>.npz · DIR/vis_results.md · vis_results.json
"""
import argparse
import json
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sg_offline_eval as OE  # noqa: E402

SHIFTS = [("dx+40", 40, 0, 0, 1.0), ("dx-40", -40, 0, 0, 1.0), ("dy+30", 0, 30, 0, 1.0), ("dy-30", 0, -30, 0, 1.0),
          ("rot+8", 0, 0, 8, 1.0), ("rot-8", 0, 0, -8, 1.0), ("zoom1.12", 0, 0, 0, 1.12), ("zoom0.89", 0, 0, 0, 0.89)]
OFF = [("off_dx60", 60, 0, 0, 1.0), ("off_dy45", 0, 45, 0, 1.0)]


def warp(img, cx, cy, dx, dy, rot, scale):
    """큐브 중심 (cx, cy) 기준 돌림 · 크기 + 옮김. 빈 곳은 가장자리 색. rot + = 화면 시계 방향."""
    import cv2

    M = cv2.getRotationMatrix2D((float(cx), float(cy)), -float(rot), float(scale))
    M[0, 2] += dx
    M[1, 2] += dy
    return cv2.warpAffine(img, M, (img.shape[1], img.shape[0]), borderMode=cv2.BORDER_REPLICATE)


def cube_info(img, P, ref):
    import sg_sticker as ss

    d = ss.detect(img, P)
    c = d.get("cube")
    if not c:
        return None
    t = ss.target_compare(d, ref) if ref else None
    return {"cx": c["px"][0], "cy": c["px"][1], "u": c["u"], "v": c["v"], "size": math.sqrt(c["area_px"]), "angle": ss.cube_angle(c["hull"]),
            "tgt": t}


def build(limit=None):
    import sg_sticker as ss

    rows = OE.build_states(["A", "B"], limit)
    P = ss.load_params()
    ref = next((r for r in ss.read_refs()["refs"].values() if r.get("name") == "닫기자리"), None)  # ref-v5 (수직 닫기 자리, 예비2 ep0 · 3)
    for r in rows:
        r["cube"] = cube_info(r["wrist"], P, ref) if r["phase"] in ("descent", "pre_close") else None
    starts = [r for r in rows if r["set"] == "A" and r["phase"] == "start"]
    return rows, starts, ref


def run(out, ckpts, n, limit=None, dry=False):
    rows, starts, ref = build(limit)
    # V1: 판마다 사람 pan 변화 (시작 50 프레임) — front 주인 기준
    hp = {r["ep"]: float(r["human"][-1, 0] - r["state"][0]) for r in starts}
    order = sorted(starts, key=lambda r: hp[r["ep"]])
    v1 = []
    for r in starts:  # 사람 pan 변화가 가장 다른 3 판의 front
        others = sorted([o for o in starts if o["ep"] != r["ep"]], key=lambda o: -abs(hp[o["ep"]] - hp[r["ep"]]))[:3]
        v1.append((r, [r] + others))
    v2 = [r for r in rows if r["phase"] in ("descent", "pre_close") and r["cube"]]
    fronts = {r["ep"]: r["front"] for r in starts}
    print(f"V1 {len(v1)} 장면 × 4 · V2 {len(v2)} 장면 × {1 + len(SHIFTS) + 1} · V3 (V2 의 A pre_close) × {len(OFF)}", flush=True)
    if dry:
        return 0
    sys.path.insert(0, OE.VD)
    import torch
    import v02_engine as E
    import v_common as V

    for tag, path in ckpts:
        t1 = time.time()
        V.CKPT = __import__("pathlib").Path(path)
        eng = E.Engine(n_noise=n)
        # V1
        P1 = []
        for r, fs in v1:
            A = eng.run(r["state"], [(f["front"], r["wrist"]) for f in fs])  # (4, n, 50, 6)
            P1.append(A[:, :, -1, 0].mean(1) - r["state"][0])
        P1 = np.array(P1)  # (S, 4) 예측 pan 변화
        own = np.array([hp[r["ep"]] for r, _ in v1])
        src = np.array([[hp[f["ep"]] for f in fs] for _, fs in v1])
        # V2 · V3
        P2, P3, FR = [], [], []
        for r in v2:
            c = r["cube"]
            ims = [(r["front"], r["wrist"])] + [(r["front"], warp(r["wrist"], c["cx"], c["cy"], dx, dy, ro, sc)) for _, dx, dy, ro, sc in SHIFTS]
            fo = fronts.get(sorted(fronts, key=lambda e: abs(e - r["ep"]))[-1]) if fronts else r["front"]  # 큐브 자리가 다른 판의 시작 front
            ims.append((fo, r["wrist"]))
            if r["set"] == "A" and r["phase"] == "pre_close":
                ims += [(r["front"], warp(r["wrist"], c["cx"], c["cy"], dx, dy, ro, sc)) for _, dx, dy, ro, sc in OFF]
            A = eng.run(r["state"], ims)  # (K, n, 50, 6)
            end = A[:, :, -1, :].mean(1)  # (K, 6)
            P2.append(end[:1 + len(SHIFTS)])
            FR.append(end[1 + len(SHIFTS)])
            g0 = r["state"][5]
            closes = (A[:, :, :, 5].min(-1) < g0 - 8).mean(1)  # (K,)
            P3.append(np.r_[closes[0], closes[2 + len(SHIFTS):]] if len(closes) > 2 + len(SHIFTS) else np.r_[closes[0], [np.nan] * len(OFF)])
        d = os.path.join(out, "vis_raw")
        os.makedirs(d, exist_ok=True)
        np.savez_compressed(os.path.join(d, f"{tag}.npz"), v1_pred=P1, v1_own=own, v1_src=src, v2_end=np.array(P2), v2_front=np.array(FR),
                            v3_close=np.array(P3), v2_state=np.stack([r["state"] for r in v2]), v2_human_end=np.stack([r["human"][-1] for r in v2]),
                            v2_phase=np.array([r["phase"] for r in v2]), v2_set=np.array([r["set"] for r in v2]),
                            v2_tgt=np.array([[r["cube"]["tgt"]["du"], r["cube"]["tgt"]["dv"], r["cube"]["tgt"]["size"], r["cube"]["tgt"]["dangle"]]
                                             if r["cube"]["tgt"] else [np.nan] * 4 for r in v2]))
        print(f"  {tag}: {time.time() - t1:.0f} s", flush=True)
        del eng
        torch.cuda.empty_cache()
    summarize(out, [t for t, _ in ckpts])
    return 0


def _slope(x, y):
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 3 or np.std(x[m]) == 0:
        return float("nan"), float("nan")
    b = np.polyfit(x[m], y[m], 1)[0]
    return float(b), float(np.corrcoef(x[m], y[m])[0, 1])


def summarize(out, tags):
    J6 = ["pan", "lift", "elbow", "wflex", "wroll", "grip"]
    L = ["# SG50 시각 의존 오프라인 시험", "", f"- 만든 시각 {time.strftime('%Y-%m-%d %H:%M')} · `tools/sg_vis_eval.py` (설명은 파일 맨 위). 판정 아님 — 체크포인트 비교용 수치.", ""]
    res = {}
    # 사람 이득 (V2 장면, A+B): 손목 큐브의 주황 프레임 차이 ↔ 사람이 50 프레임 동안 고친 양
    z0 = np.load(os.path.join(out, "vis_raw", f"{tags[0]}.npz"), allow_pickle=True)
    dh = z0["v2_human_end"] - z0["v2_state"]
    tg = z0["v2_tgt"]
    hum = {"pan~du": _slope(tg[:, 0], dh[:, 0]), "wroll~dangle": _slope(tg[:, 3], dh[:, 4]), "lift~size": _slope(tg[:, 2], dh[:, 1]),
           "wflex~dv": _slope(tg[:, 1], dh[:, 3])}
    L += ["## 사람 기준 (V2 장면, 손목 큐브 ↔ 주황 프레임 차이와 사람이 그 뒤 50 프레임 동안 고친 양)", "",
          "| 관계 | 기울기 | 상관 |", "|---|---:|---:|"] + [f"| {k} | {v[0]:+.2f} | {v[1]:+.2f} |" for k, v in hum.items()] + [""]
    L += ["## V1 front → 숄더팬 (시작 장면, front 만 다른 판 것으로)", "",
          "| 체크포인트 | 예측 ↔ front 주인 판 사람 pan 변화 (기울기 · 상관) | 예측 ↔ 관절값 · 손목 주인 판 (기울기 · 상관) | 원래 front 예측 ↔ 사람 (상관) |",
          "|---|---|---|---|"]
    for t in tags:
        z = np.load(os.path.join(out, "vis_raw", f"{t}.npz"), allow_pickle=True)
        P1, own, src = z["v1_pred"], z["v1_own"], z["v1_src"]
        sw = _slope(src[:, 1:].ravel(), P1[:, 1:].ravel())
        ow = _slope(np.repeat(own, P1.shape[1] - 1), P1[:, 1:].ravel())
        orig = _slope(own, P1[:, 0])
        res.setdefault(t, {})["v1"] = {"front_src": sw, "own": ow, "orig": orig}
        L.append(f"| {t} | {sw[0]:+.2f} · {sw[1]:+.2f} | {ow[0]:+.2f} · {ow[1]:+.2f} | {orig[1]:+.2f} |")
    L += ["", "## V2 손목 → 다시 맞추기 (손목 영상만 바꿈, 예측 chunk 끝 action 차)", "",
          "- 이득 = (바꾼 영상 예측 − 원래 영상 예측) / 영상 변화. 좌우 du = dx/640, 앞뒤 dv = dy/480, 회전 °, 크기 비. 사람 기준 기울기와 같은 방향 · 비슷한 크기면 손목을 보고 고침.", "",
          "| 체크포인트 | pan / du (좌우 ±40 px) | wflex / dv (앞뒤 ±30 px) | lift / dv | wroll / 회전 (±8°) | lift / 크기 (×1.12 · ×0.89) | front 만 바꿈: 관절 변화 평균 ° | 손목 바꿈: 관절 변화 평균 ° |",
          "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for t in tags:
        z = np.load(os.path.join(out, "vis_raw", f"{t}.npz"), allow_pickle=True)
        E2 = z["v2_end"]  # (S, 9, 6): 0 = 원래, 1.. = SHIFTS
        D = E2[:, 1:] - E2[:, :1]
        g = {"pan/du": float(np.mean((D[:, 0, 0] - D[:, 1, 0]) / (80 / 640))), "wflex/dv": float(np.mean((D[:, 2, 3] - D[:, 3, 3]) / (60 / 480))),
             "lift/dv": float(np.mean((D[:, 2, 1] - D[:, 3, 1]) / (60 / 480))), "wroll/rot": float(np.mean((D[:, 4, 4] - D[:, 5, 4]) / 16.0)),
             "lift/size": float(np.mean((D[:, 6, 1] - D[:, 7, 1]) / (1.12 - 0.89)))}
        fchg = float(np.abs(z["v2_front"] - E2[:, 0])[:, :5].mean())
        wchg = float(np.abs(D[:, :, :5]).mean())
        res[t]["v2"] = {**g, "front_change": fchg, "wrist_change": wchg}
        L.append(f"| {t} | {g['pan/du']:+.1f} | {g['wflex/dv']:+.1f} | {g['lift/dv']:+.1f} | {g['wroll/rot']:+.2f} | {g['lift/size']:+.1f} | {fchg:.2f} | {wchg:.2f} |")
    L += ["", "## V3 주황 프레임에 맞으면 닫기 (A 의 닫기 직전 장면)", "",
          "| 체크포인트 | 원래 영상 (프레임 맞음) 닫기 비율 | 큐브를 좌우 60 px 밖으로 | 앞뒤 45 px 밖으로 |", "|---|---:|---:|---:|"]
    for t in tags:
        z = np.load(os.path.join(out, "vis_raw", f"{t}.npz"), allow_pickle=True)
        P3 = z["v3_close"]
        sel = ~np.isnan(P3[:, 1])
        m = P3[sel].mean(0) if sel.any() else [np.nan] * 3
        res[t]["v3"] = [float(x) for x in m]
        L.append(f"| {t} | {m[0]:.0%} | {m[1]:.0%} | {m[2]:.0%} |")
    with open(os.path.join(out, "vis_results.md"), "w") as f:
        f.write("\n".join(L) + "\n")
    json.dump({"human": hum, "ckpt": res}, open(os.path.join(out, "vis_results.json"), "w"), ensure_ascii=False, indent=1, default=float)
    print(f"→ {os.path.join(out, 'vis_results.md')}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--ckpt", action="append", default=[])
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--summarize", action="store_true")
    a = ap.parse_args()
    ck = [tuple(c.split("=", 1)) for c in a.ckpt]
    os.makedirs(a.out, exist_ok=True)
    if a.summarize:
        summarize(a.out, [t for t, _ in ck])
        return 0
    return run(a.out, ck, a.n, a.limit, a.dry)


if __name__ == "__main__":
    sys.exit(main())
