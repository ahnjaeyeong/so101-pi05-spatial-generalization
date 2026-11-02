"""G2 (분석 4 · 3b, GPU): F1 과 같은 프레임 (학습 probe 7,810 · 평가 롤아웃 558) 에서 정책 행동 chunk 와 Expert 내부를 기록.
d2 020000, 고정 noise 2개, denoise 5 step. 편집 없음. 로봇·카메라 연결 없음, 읽기만.

쓰임
  - 사람 이후 이동 (c5 M5) 과 같은 프레임 · 같은 라벨 · 같은 시간 범위로 정책 이후 이동 기울기 → 같은 조건의 사람 대비 행동 이득
  - SigLIP/Gemma probe 예측 (F1 특징) ~ 정책 pan · 집게 끝 (분석 4)
  - Expert 층별 hidden (첫 denoise step, 행동 토큰 평균) 에서 큐브 상대 위치 · roll 을 읽을 수 있는지 (F1 fold 그대로)
  - Expert 주의 질량 (front · wrist · 문장 · state · roll)
출력: g2/chunks.npy (noise × N × 50 × 6 f16), g2/expert_hidden.npy (N × 18 × 1024 f16), g2/attn_mass.npy, g2/rows.csv, g2/run.json
사용: nice -n 19 env PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python g2_policy_frames.py [--device cpu --limit 2 --n_noise 1]
"""
import argparse
import json
import time

import numpy as np
import pandas as pd

import ab_core as A
from ab_core import C

OUT = A.AB / "g2"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--limit", type=int, default=None, help="판 수 제한 (시험)")
    ap.add_argument("--n_noise", type=int, default=2)
    ap.add_argument("--bs", type=int, default=8)
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--d4_ratio", type=float, default=2.0, help="d4 가 기준의 이 배수보다 느리면 대기. d4 를 일시정지했으면 inf (메모리 하한만)")
    args = ap.parse_args()
    out = A.Path(args.out)
    out.mkdir(exist_ok=True)
    M = pd.read_csv(A.D2 / "vision_probe/f1_features/meta.csv")
    M = M[(M.src.isin(["train", "eval"])) & M.valid].reset_index(drop=True)
    groups = list(M.groupby(["ds", "ep"], sort=False))
    if args.limit:
        groups = groups[:args.limit] + [g for g in groups if g[1].src.iloc[0] == "eval"][:1]
    t0 = time.time()
    wd = A.Watchdog(ratio=args.d4_ratio) if args.device == "cuda" else None
    E = A.Engine("020000", device=args.device, n_noise=args.n_noise)
    t1 = time.time()
    data = {}
    cache, rows, ch, hid, att = {}, [], [], [], []
    for n, ((ds, ep), g) in enumerate(groups):
        if ds not in data:
            data[ds] = C.load_parquet(ds)
        s, _ = data[ds][int(ep)]
        f0, f1 = int(g.frame.min()), int(g.frame.max())
        Fr = C.frames(ds, int(ep), "front", f0, f1, cache)
        Wr = C.frames(ds, int(ep), "wrist", f0, f1, cache)
        idx = (g.frame.values - f0).astype(int)
        ok = idx < min(len(Fr), len(Wr))
        g = g[ok]
        idx = idx[ok]
        F = np.stack([Fr[i] for i in idx])
        W = np.stack([Wr[i] for i in idx])
        S = s[g.frame.values.astype(int)].astype(np.float32)
        c, h, am, gr = E.chunks(F, W, S, bs=args.bs, watchdog=wd, capture=True)
        ch.append(c.astype(np.float16))
        hid.append(h.astype(np.float16))
        att.append(am.astype(np.float32))
        r = g[["row", "src", "ep", "frame", "t_to_close", "roll", "rel_u_cm", "rel_v_cm", "tan_cm", "rad_cm", "cube_x", "cube_y", "group",
               "run", "event"]].copy()
        r["ds"] = ds
        r["n_numbers"] = [x["n_numbers"] for x in gr]
        r["roll_tokens"] = [" ".join(x["roll_tokens"]) for x in gr]
        rows.append(r)
        if n % 10 == 0 or n + 1 == len(groups):
            print(f"{n + 1}/{len(groups)} eps · obs {sum(len(x) for x in rows)} · {time.time() - t1:.0f}s · gpu {E.gpu_busy_s:.0f}s"
                  + (f" · d4 {A.d4_step_time()}" if wd else ""), flush=True)
        if (n + 1) % 32 == 0 or n + 1 == len(groups):
            np.save(out / "chunks.npy", np.concatenate(ch, axis=1))
            np.save(out / "expert_hidden.npy", np.concatenate(hid))
            np.save(out / "attn_mass.npy", np.concatenate(att))
            pd.concat(rows).to_csv(out / "rows.csv", index=False)
    json.dump(dict(n_obs=int(sum(len(x) for x in rows)), gpu_busy_s=E.gpu_busy_s, wall_s=time.time() - t0, load_s=t1 - t0,
                   watchdog_wait_s=wd.wait_s if wd else 0, d4_log=wd.log if wd else [], device=args.device, n_noise=args.n_noise),
              open(out / "run.json", "w"), indent=1, default=str)
    print(f"done gpu_busy_s {E.gpu_busy_s:.0f}", flush=True)


if __name__ == "__main__":
    main()
