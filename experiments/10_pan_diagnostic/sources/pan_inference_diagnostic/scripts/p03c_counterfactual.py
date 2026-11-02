"""p03c 집중 사례 오프라인 반사실 (GPU). **모두 재구성 · 반사실 값이다 — 실물 기록이 아니고, 실물에 적용하지 않는다.**

p03b 와 같은 정책 · RTC 설정 · noise 은행 (seed 1234) · 관측 (AV1 디코드 dataset 프레임, obs_frame) · prefix 를 쓴다.
A. inference_delay 반사실: 세션 두 번째 추론 (코드 규칙상 inference_delay 0) 인 filt/ep0 chunk 1, try3/ep0 chunk 1 을
   inference_delay 0 (기록 당시 규칙) 과 11 · 12 (이후 chunk 와 같은 값) 로 각각 G 계산 (같은 noise 32 · 같은 prefix).
B. prefix 미기록 부분 가정: prefix index 10…19 (앞 chunk index 30…39, 실행 안 됨 · 기록 없음) 를
   (est) p03b 추정값 / (hold) 앞 chunk 마지막 실행 기록값 고정 / (lin) 앞 chunk 실행 index 25…29 기울기로 연장 — 세 가정으로 G 계산.
   대상: filt/ep0 chunk 1 (delay 0 · 11), filt/ep2 chunk 1, try3/ep0 chunk 4 (기록된 inference_delay).
C. chunk 0 (prefix 없음) noise 256 개: 다섯 판 각각, 은행 seed 1234 (p03b 와 같은 첫 32 개) + seed 1235…1241.
출력: tables/p03c_counterfactual.npz, tables/p03c_cases.csv (사례 · 조건별 pan index 0…49 의 p10/p50/p90, seam 등)
사용: nice -n 19 env PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python p03c_counterfactual.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from p03b_guided_recon import D2, TAB, Pol, load_obs  # noqa: E402

RUNS = {"try3": "20261026_135128_20k_t1_try3", "filt": "20261026_140246_20k_t1_try3_filt"}


def main():
    T = pd.read_parquet(TAB / "p01_ticks.parquet")
    P = Pol(n_bank=32)
    torch = P.torch
    rows, saved = [], {}
    cache = {}

    def load(run, e):
        z = np.load(TAB / f"p03b_{run}_ep{e}.npz")
        g = T[(T.run == run) & (T.ep == e)]
        return z, g

    def obs(run, e, fo):
        F, W = load_obs(D2 / "eval/rollouts" / run / "dataset", [(int(e), int(fo))], cache)
        return F[0], W[0]

    def record(case, cond, A, seam_ref=None, i0=None, i1=None):
        pan = A[:, :, 0]
        saved[f"{case}|{cond}"] = A.astype(np.float32)
        r = dict(case=case, cond=cond, n=len(A))
        for j in range(50):
            r[f"p10_{j}"], r[f"p50_{j}"], r[f"p90_{j}"] = np.percentile(pan[:, j], 10), np.median(pan[:, j]), np.percentile(pan[:, j], 90)
        if seam_ref is not None:
            r.update(seam_ref=seam_ref, i0=i0, i1=i1, seam_med=float(np.median(pan[:, i0] - seam_ref)),
                     seam_p10=float(np.percentile(pan[:, i0] - seam_ref, 10)), seam_p90=float(np.percentile(pan[:, i0] - seam_ref, 90)),
                     min_i0_i1_minus_ref_med=float(np.median(pan[:, i0:i1 + 1].min(1) - seam_ref)),
                     max_i0_i1_minus_ref_med=float(np.median(pan[:, i0:i1 + 1].max(1) - seam_ref)))
        rows.append(r)
        print(case, cond, {k: round(v, 2) for k, v in r.items() if k.startswith("seam") or k.endswith("_med")}, flush=True)

    # A · B
    for key, e, k, delays in (("filt", 0, 1, (0, 11)), ("try3", 0, 1, (0, 12)), ("filt", 2, 1, (12,)), ("try3", 0, 4, (12,))):
        run = RUNS[key]
        z, g = load(run, e)
        i = int(np.where(z["chunk_id"] == k)[0][0])
        fo = int(z["obs_frame"][i])
        F, W = obs(run, e, fo)
        S = g[[c for c in g.columns if c.startswith("state_")]].values.astype(np.float32)
        raw = g[[c for c in g.columns if c.startswith("raw_")]].values
        cid, cidx = g.chunk_id.values, g.chunk_idx.values
        prev = np.where(cid == k - 1)[0]
        pidx = cidx[prev].astype(int)
        last = raw[prev[-1]]
        cur = np.where(cid == k)[0]
        i0, i1 = int(cidx[cur[0]]), int(cidx[cur[-1]])
        pfx_est = z["prefix_deg"][i].copy()
        known = z["prefix_known"][i]
        pfx_hold = pfx_est.copy()
        pfx_lin = pfx_est.copy()
        sl = (raw[prev[-1]] - raw[prev[-5]]) / max(pidx[-1] - pidx[-5], 1)
        for j in range(20):
            if not known[j]:
                pfx_hold[j] = last
                pfx_lin[j] = last + sl * (20 + j - pidx[-1])
        case = f"{key}/ep{e}/c{k}"
        U = P.chunks(F, W, S[fo], 32)
        record(case, "U", U, last[0], i0, i1)
        for d in delays:
            for nm, pf in (("est", pfx_est), ("hold", pfx_hold), ("lin", pfx_lin)):
                G = P.chunks(F, W, S[fo], 32, prefix_deg=pf, delay=d)
                record(case, f"G_d{d}_{nm}", G, last[0], i0, i1)
        saved[f"{case}|prefix_est"], saved[f"{case}|prefix_hold"], saved[f"{case}|prefix_lin"] = pfx_est, pfx_hold, pfx_lin
        saved[f"{case}|logged_cur"] = np.stack([cidx[cur], raw[cur, 0]], 1)
        saved[f"{case}|logged_prev"] = np.stack([pidx, raw[prev, 0]], 1)

    # C
    base = P.bank.clone()
    for key, run in RUNS.items():
        for e in sorted(T[T.run == run].ep.unique()):
            z, g = load(run, e)
            F, W = obs(run, e, 0)
            s0 = g[[c for c in g.columns if c.startswith("state_")]].values.astype(np.float32)[0]
            outs = []
            for b in range(8):
                gen = torch.Generator(device="cpu").manual_seed(1234 + b)
                P.bank = torch.randn(base.shape, generator=gen)
                outs.append(P.chunks(F, W, s0, 32))
            P.bank = base
            A = np.concatenate(outs)
            record(f"{key}/ep{e}/c0", "U256", A)
    np.savez_compressed(TAB / "p03c_counterfactual.npz", **{k.replace("/", "_").replace("|", "__"): v for k, v in saved.items()})
    pd.DataFrame(rows).to_csv(TAB / "p03c_cases.csv", index=False)
    print("gpu_s", round(P.gpu_s))


if __name__ == "__main__":
    main()
