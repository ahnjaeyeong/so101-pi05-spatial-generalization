"""G1 (분석 1 · 2 · 3b, GPU): wrist_roll state × wrist 영상 큐브 위치 요인 실험 + Expert 의 roll/state 토큰 가리기.
d2 020000, 학습 T1 128편 × 닫힘 2.5 · 1.5 · 1.0 s 전 프레임. 고정 noise 4개 (조건끼리 같은 noise), denoise 5 step.
로봇·카메라 연결 없음. 데이터셋·체크포인트 읽기만. 출력은 action_bottleneck/g1/ 아래 새 파일만.

조건 (프레임마다; roll+Δ 가 학습 q01..q99 밖이면 그 조건은 건너뛰고 기록)
  F  (분석 1)  roll Δ ∈ {−30, −15, 0, +15, +30}° × wrist 영상 {base, wu±, wv±} (큐브를 영상 u/v 로 ±1 cm 상당 이동, exp2 move_blob)
  RC (분석 2)  roll-일관 회전: 큐브를 기준점 둘레로 Q = M(θ+0.91Δ)⁻¹ M(θ) 만큼 돌려 옮기고(조각도 같이 회전) state roll += Δ
               → 라벨 규약상 탁자 위 큐브 상대 위치는 그대로 (기대 행동 변화 0). Δ ∈ {−30, −15, +15, +30}
  RI (분석 2)  같은 회전 영상, state 그대로 → 라벨 규약상 탁자 위치가 바뀐 것과 같다
  KR / KS (분석 3b) Expert 가 roll 숫자 토큰 / state 숫자 전체를 못 보게 (prefix_pad_mask) — base, wu±, wv± (KR), base (KS)
  W0 대조: 큐브를 같은 자리에 다시 붙임 (편집 흔적만)
출력: g1/chunks.npy (noise × N × 50 × 6, float16), g1/expert_hidden.npy (N × 18 × 1024, 첫 denoise step, 행동 토큰 평균),
      g1/attn_mass.npy (N × 18 × 7: front, wrist, task, state(roll 제외), roll, suffix, pad), g1/rows.csv, g1/run.json
사용: nice -n 19 env PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python g1_roll_factorial.py [--device cpu --limit 2 --n_noise 1]
"""
import argparse
import json
import time

import cv2
import numpy as np
import pandas as pd

import ab_core as A
from ab_core import C

OUT = A.AB / "g1"
D_CM = 1.0
DELTAS = (-30.0, -15.0, 15.0, 30.0)
PHASES = {"t2.5": 75, "t1.5": 45, "t1.0": 30}


def wrist_blob(img, min_area=200):
    b = C.blobs(C.red_mask(img), min_area)
    if not b:
        return None
    a, (u, v), li, lab = max(b, key=lambda t: t[0])
    m = (lab == li).astype(np.uint8)
    ys, xs = np.nonzero(m)
    border = xs.min() <= 1 or ys.min() <= 1 or xs.max() >= img.shape[1] - 2 or ys.max() >= img.shape[0] - 2
    return dict(area=a, u=u, v=v, mask=m, border=bool(border))


def _inpaint(img, mask):
    big = cv2.dilate(mask, np.ones((7, 7), np.uint8))
    bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    return cv2.cvtColor(cv2.inpaint(bgr, big * 255, 5, cv2.INPAINT_TELEA), cv2.COLOR_BGR2RGB), big


def move_blob(img, mask, du, dv):
    """exp2_sensitivity.move_blob 과 같은 편집 (지우고 (du, dv) px 옮겨 붙임)."""
    out, big = _inpaint(img, mask)
    ys, xs = np.nonzero(big)
    pix = img[ys, xs].copy()
    yy, xx = ys + int(round(dv)), xs + int(round(du))
    ok = (yy >= 0) & (yy < img.shape[0]) & (xx >= 0) & (xx < img.shape[1])
    out[yy[ok], xx[ok]] = pix[ok]
    return out


def rotate_blob(img, mask, c_old, c_new, Q):
    """큐브 조각을 c_old 중심으로 Q (영상 px 좌표 (u, v) 에 작용하는 2×2) 만큼 돌려 c_new 에 붙인다."""
    out, big = _inpaint(img, mask)
    Aff = np.zeros((2, 3))
    Aff[:, :2] = Q
    Aff[:, 2] = np.asarray(c_new) - Q @ np.asarray(c_old)
    h, w = img.shape[:2]
    wimg = cv2.warpAffine(img, Aff, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    wm = cv2.warpAffine(big.astype(np.float32), Aff, (w, h), flags=cv2.INTER_LINEAR) > 0.5
    out[wm] = wimg[wm]
    return out


def build_ep(e, T, data, bu, bv, cache, skipped):
    """판 하나의 관측 묶음 (메모리 때문에 판 단위로 만들고 바로 추론)."""
    from policy_probe import load_obs
    F_, W_, S_, K_, rows = [], [], [], [], []
    if True:
        s, _ = data[e]
        gf = int(T.loc[e, "grasp_f"])
        for ph, off in PHASES.items():
            f = gf - off
            if f < 0:
                skipped.append((e, ph, "f<0"))
                continue
            Fi, Wi = load_obs(C.D2 / "dataset", [(e, f)], cache)
            Fi, Wi = Fi[0], Wi[0]
            st = s[f].astype(np.float32)
            bl = wrist_blob(Wi)
            if bl is None or bl["border"]:
                skipped.append((e, ph, "no blob" if bl is None else "border"))
                continue
            pxcm = np.sqrt(bl["area"]) / 2.5
            us = np.polyval(bu, 1 / np.sqrt(bl["area"]))
            vs = np.polyval(bv, 1 / np.sqrt(bl["area"]))
            rel = np.array([(bl["u"] - us) / pxcm, (bl["v"] - vs) / pxcm])
            roll = float(st[4])
            base = dict(ep=e, group=T.loc[e, "group"], phase=ph, frame=f, grasp_f=gf, cube_x=T.loc[e, "cube_x"], cube_y=T.loc[e, "cube_y"],
                        roll=roll, rel_u=rel[0], rel_v=rel[1], pxcm=pxcm, area=bl["area"])

            def add(cond, img, droll=0.0, knock=None, d_img=(0.0, 0.0), rel_new=None):
                s2 = st.copy()
                s2[4] = roll + droll
                rn = rel if rel_new is None else rel_new
                # 라벨 규약 기대값: 영상 rel → 탁자 (tan, rad), state roll 로 회전
                tab_state = A.M_img2tab(roll + droll) @ rn
                rows.append(dict(base, cond=cond, droll=droll, knock=knock or "", d_img_u=d_img[0], d_img_v=d_img[1],
                                 rel_u_new=rn[0], rel_v_new=rn[1], tab_tan=tab_state[0], tab_rad=tab_state[1]))
                F_.append(Fi)
                W_.append(img)
                S_.append(s2)
                K_.append(knock)

            edits = {"base": (Wi, (0, 0))}
            for nm, du, dv in (("wu+", 1, 0), ("wu-", -1, 0), ("wv+", 0, 1), ("wv-", 0, -1)):
                edits[nm] = (move_blob(Wi, bl["mask"], du * D_CM * pxcm, dv * D_CM * pxcm), (du * D_CM, dv * D_CM))
            for d in (0.0,) + DELTAS:
                if not (A.Q01_ROLL <= roll + d <= A.Q99_ROLL):
                    skipped.append((e, ph, f"F droll {d}"))
                    continue
                for nm, (img, di) in edits.items():
                    add(f"F:{nm}", img, droll=d, d_img=di, rel_new=rel + np.array(di))
            add("W0", move_blob(Wi, bl["mask"], 0, 0))
            for nm, (img, di) in edits.items():
                add(f"KR:{nm}", img, knock="roll", d_img=di, rel_new=rel + np.array(di))
            add("KS:base", Wi, knock="state")
            for d in DELTAS:
                Q = np.linalg.solve(A.M_img2tab(roll + d), A.M_img2tab(roll))     # rel' = Q rel
                rel2 = Q @ rel
                c_old = np.array([bl["u"], bl["v"]])
                c_new = np.array([us, vs]) + rel2 * pxcm
                img = rotate_blob(Wi, bl["mask"], c_old, c_new, Q)
                if A.Q01_ROLL <= roll + d <= A.Q99_ROLL:
                    add(f"RC:{d:+.0f}", img, droll=d, rel_new=rel2)
                else:
                    skipped.append((e, ph, f"RC {d}"))
                add(f"RI:{d:+.0f}", img, droll=0.0, rel_new=rel2)
    if not rows:
        return None
    return np.stack(F_), np.stack(W_), np.stack(S_), K_, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--n_noise", type=int, default=4)
    ap.add_argument("--bs", type=int, default=8)
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--d4_ratio", type=float, default=2.0, help="d4 가 기준의 이 배수보다 느리면 대기. d4 를 일시정지했으면 inf (메모리 하한만)")
    ap.add_argument("--eps", default=None, help="판 범위 (예: 64-95). 없으면 T1 128편 전부")
    ap.add_argument("--smoke", action="store_true", help="CPU 시험: 첫 판 첫 단계에서 조건 종류마다 1개씩만")
    args = ap.parse_args()
    out = A.Path(args.out)
    out.mkdir(exist_ok=True)
    t0 = time.time()
    T = pd.read_csv(C.OUT / "grasp_train.csv")
    data = C.load_parquet(C.D2 / "dataset")
    bu, bv = A.ref_point_fit()
    eps = [e for e in range(256) if T.loc[e, "task"] == "T1"][:args.limit]
    if args.eps:
        lo, hi = map(int, args.eps.split("-"))
        eps = [e for e in eps if lo <= e <= hi]
    wd = A.Watchdog(ratio=args.d4_ratio) if args.device == "cuda" else None
    E = A.Engine("020000", device=args.device, n_noise=args.n_noise)
    t1 = time.time()
    cache, skipped, rows, ch, hid, att = {}, [], [], [], [], []
    for n, e in enumerate(eps):
        b = build_ep(e, T, data, bu, bv, cache, skipped)
        if b is None:
            continue
        F, W, S, K, r = b
        if args.smoke:
            want = ["F:base", "F:wu+", "W0", "KR:base", "KR:wu+", "KS:base", "RC:+15", "RI:+15"]
            sel = [next(i for i, x in enumerate(r) if x["cond"] == c and x["phase"] == r[0]["phase"]
                        and (x["droll"] in (0.0, 15.0) if c.startswith("F") else True)) for c in want]
            sel.insert(1, next(i for i, x in enumerate(r) if x["cond"] == "F:base" and x["droll"] == 15.0))
            F, W, S, K, r = F[sel], W[sel], S[sel], [K[i] for i in sel], [r[i] for i in sel]
        if args.limit and n == 0:
            cv2.imwrite(str(out / "smoke_edits.jpg"), cv2.cvtColor(np.concatenate(
                [np.concatenate(list(W[i:i + 6]), 1) for i in range(0, len(W) - 5, 6)][:7], 0)[::3, ::3], cv2.COLOR_RGB2BGR))
        c, h, am, _ = E.chunks(F, W, S, knock=K, bs=args.bs, watchdog=wd, capture=True)
        ch.append(c.astype(np.float16))
        hid.append(h.astype(np.float16))
        att.append(am.astype(np.float32))
        rows.extend(r)
        print(f"ep {e} ({n + 1}/{len(eps)}) obs {len(rows)} · {time.time() - t1:.0f}s · gpu {E.gpu_busy_s:.0f}s"
              + (f" · d4 {A.d4_step_time()}" if wd else ""), flush=True)
        if (n + 1) % 16 == 0 or n + 1 == len(eps):      # 중간 저장 (멈춰도 앞부분은 남게)
            np.save(out / "chunks.npy", np.concatenate(ch, axis=1))
            np.save(out / "expert_hidden.npy", np.concatenate(hid))
            np.save(out / "attn_mass.npy", np.concatenate(att))
            pd.DataFrame(rows).to_csv(out / "rows.csv", index=False)
    R = pd.DataFrame(rows)
    json.dump(dict(n_obs=len(R), skipped=skipped, gpu_busy_s=E.gpu_busy_s, wall_s=time.time() - t0, load_s=t1 - t0,
                   watchdog_wait_s=wd.wait_s if wd else 0, d4_log=wd.log if wd else [], device=args.device, n_noise=args.n_noise),
              open(out / "run.json", "w"), indent=1, default=str)
    print(f"done gpu_busy_s {E.gpu_busy_s:.0f}", flush=True)


if __name__ == "__main__":
    main()
