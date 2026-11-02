"""p03b 기존 5 판: Action Expert raw chunk (RTC 안내 없음) 과 RTC 안내 chunk 를 **같은 noise 로 짝지어** 오프라인 재구성 (GPU).

**모두 재구성 값이다 — 실물에서 기록된 chunk 가 아니다.** 실물 기록 (raw 실행 구간) 과 비교만 한다.
- 정책: d2 020000, num_inference_steps 5, RTC guided EXP h20 max_guidance_weight 10 (실물과 같음), policy.predict_action_chunk 그대로.
- 관측: dataset AV1 디코드 영상 + observation.state. chunk 0 은 frame 0 (실제 관측은 그 직전 정지 상태), chunk k≥1 은 merge 프레임 − 적용 delay (±1 틱).
- noise: 고정 은행 (seed 1234) 의 N 개. 같은 noise 로 '안내 없음 (U)' 과 '안내 있음 (G)' 을 둘 다 계산 → 같은 noise 에서 RTC 안내가 바꾼 양.
- G 의 prefix (prev_chunk_left_over): 실물 코드와 같이 '앞 chunk 의 index 20…39' (추론 시작 때 남은 30 개 중 앞 20 개).
    그중 추론 동안 실제로 나간 index 20…(20+d−1) 은 **기록된 raw** 값, 나머지는 앞 chunk 재구성 (기록된 실행 구간과 가장 잘 맞는 noise 8 개의 G 평균, chunk 0 은 U) 으로 채움.
- inference_delay: 코드 규칙 (rtc.py _estimate_rtc_delay) 을 기록된 지연 순서에 적용 — 실행 (세션) 의 두 번째 추론 0, 이후 ceil(그때까지 최대 지연 × 30). 기록된 지연은 0.01 s 반올림 값.
출력: tables/p03b_<run>_ep<e>.npz (U, G: (N, n_chunk, 50, 6) °, obs_frame, merge_frame, delay, inference_delay, prefix_deg (n_chunk, 20, 6), prefix_known (n_chunk, 20))
사용: nice -n 19 env PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python p03b_guided_recon.py [--n 32] [--t_max 4.0]
  --t_max: onset 뒤 이 시간 (s) 까지의 chunk 는 noise N 개, 그 뒤 첫 닫힘까지는 noise 8 개.
"""
import argparse
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

D2 = Path.home() / "so101_runs/main_k8/d2"
sys.path.insert(0, str(D2 / "diag_grasp_bias"))
import common as C  # noqa: E402
from policy_probe import load_obs  # noqa: E402

TAB = D2 / "pan_inference_diagnostic/tables"
CKPT = D2 / "train/32_20000/pi05_expert_bs32_20k/checkpoints/020000/pretrained_model"
TASK = "pick up the red cube and put it in the brown box"
J = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]


class Pol:
    def __init__(self, n_bank=32, seed=1234):
        import torch
        from lerobot.configs import RTCAttentionSchedule
        from lerobot.policies.factory import make_pre_post_processors
        from lerobot.policies.pi05.modeling_pi05 import PI05Policy
        from lerobot.policies.rtc.configuration_rtc import RTCConfig
        from safetensors.torch import load_file
        self.torch = torch
        self.p = PI05Policy.from_pretrained(str(CKPT)).to("cuda").eval()
        self.p.config.num_inference_steps = 5
        self.p.config.rtc_config = RTCConfig(enabled=True, mode="guided", prefix_attention_schedule=RTCAttentionSchedule.EXP,
                                             max_guidance_weight=10.0, execution_horizon=20)
        self.p.init_rtc_processor()
        self.pre, self.post = make_pre_post_processors(self.p.config, pretrained_path=str(CKPT),
                                                       preprocessor_overrides={"device_processor": {"device": "cuda"}})
        st = load_file(str(CKPT / "policy_preprocessor_step_3_normalizer_processor.safetensors"))
        self.q01, self.q99 = st["action.q01"].numpy(), st["action.q99"].numpy()
        g = torch.Generator(device="cpu").manual_seed(seed)
        cfg = self.p.config
        self.bank = torch.randn((n_bank, cfg.chunk_size, cfg.max_action_dim), generator=g)
        self.gpu_s = 0.0

    def norm(self, deg):
        return 2.0 * (deg - self.q01) / (self.q99 - self.q01) - 1.0

    def chunks(self, front, wrist, state, n, prefix_deg=None, delay=None):
        """한 관측 → noise n 개 chunk (n, 50, 6) °. prefix_deg 가 있으면 RTC 안내."""
        torch = self.torch
        t0 = time.time()
        b = {"observation.images.front": torch.from_numpy(np.ascontiguousarray(front[None])).cuda().float().div(255).permute(0, 3, 1, 2).repeat(n, 1, 1, 1),
             "observation.images.wrist": torch.from_numpy(np.ascontiguousarray(wrist[None])).cuda().float().div(255).permute(0, 3, 1, 2).repeat(n, 1, 1, 1),
             "observation.state": torch.from_numpy(np.asarray(state, np.float32)[None]).cuda().repeat(n, 1),
             "task": [TASK] * n}
        b = self.pre(b)
        noise = self.bank[:n].cuda()
        kw = {}
        if prefix_deg is not None:
            kw = dict(prev_chunk_left_over=torch.from_numpy(self.norm(prefix_deg).astype(np.float32)).cuda(), inference_delay=int(delay))
        a = self.p.predict_action_chunk(b, noise=noise, **kw)
        out = self.post(a).float().cpu().numpy()
        torch.cuda.synchronize()
        self.gpu_s += time.time() - t0
        return out


def inference_delays(M):
    """실행 (run) 단위로 코드 규칙 재현: 세션 첫 추론 뒤 tracker reset → 두 번째 추론 0, 이후 ceil(최대 지연 × 30)."""
    out = {}
    for run, g in M.sort_values(["run", "ep", "chunk_id"]).groupby("run", sort=False):
        mx, k = 0.0, 0
        for _, r in g.iterrows():
            if r.chunk_id == 0:
                d = None  # 판 첫 chunk: prefix 없음
            else:
                d = math.ceil(mx * 30 - 1e-9) if mx > 0 else 0
            out[(run, int(r.ep), int(r.chunk_id))] = d
            if k >= 1 and not np.isnan(r.latency_s):  # 세션 첫 추론은 tracker 에 안 들어감
                mx = max(mx, float(r.latency_s))
            k += 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=32)
    ap.add_argument("--t_max", type=float, default=4.0)
    args = ap.parse_args()
    T = pd.read_parquet(TAB / "p01_ticks.parquet")
    M = pd.read_csv(TAB / "p01_merges.csv")
    PE = pd.read_csv(TAB / "p02_policy_episodes.csv")
    ID = inference_delays(M)
    P = Pol(n_bank=max(args.n, 8))
    # 정규화 왕복 검사
    x = np.array([[-30.0, -90, 80, 60, 5, 20]], np.float32)
    rt = P.post(P.torch.from_numpy(P.norm(x)).cuda()[None]).float().cpu().numpy()[0]
    print("norm round-trip max err", float(np.abs(rt - x).max()), flush=True)
    for (run, e), g in T.groupby(["run", "ep"]):
        out = TAB / f"p03b_{run}_ep{e}.npz"
        if out.exists():
            print("skip", out.name, flush=True)
            continue
        tag = f"{run[16:]}/ep{e}"
        pr = PE[PE.ep == tag].iloc[0]
        on, c = int(round(pr.onset_s * 30)), int(round(pr.first_close_s * 30))
        mm = M[(M.run == run) & (M.ep == e)].sort_values("chunk_id")
        mm = mm[mm.merge_frame < min(len(g), c + 1)]
        raw = g[[f"raw_{j}" for j in J]].values
        S = g[[f"state_{j}" for j in J]].values.astype(np.float32)
        cid_t, cidx_t = g.chunk_id.values, g.chunk_idx.values
        ds = D2 / "eval/rollouts" / run / "dataset"
        cache = {}
        Us, Gs, FO, MF, DL, IDL, PFX, PKN, NN = [], [], [], [], [], [], [], [], []
        prev_est = None  # 앞 chunk 재구성 추정 (50, 6)
        for _, r in mm.iterrows():
            k = int(r.chunk_id)
            mf, d = int(r.merge_frame), int(0 if np.isnan(r.applied_delay) else r.applied_delay)
            fo = 0 if k == 0 else max(mf - d, 0)
            n = args.n if (fo - on) / 30 <= args.t_max else 8
            F, W = load_obs(ds, [(int(e), fo)], cache)
            U = P.chunks(F[0], W[0], S[fo], n)
            idl = ID[(run, int(e), k)]
            Gc, pfx, pkn = U, np.full((20, 6), np.nan, np.float32), np.zeros(20, bool)
            if k > 0 and prev_est is not None:
                # 앞 chunk index 20…39. 기록된 실행 값이 있으면 그것 (앞 chunk 의 index 별 기록)
                pfx = prev_est[20:40].copy()
                sel = np.where(cid_t == k - 1)[0]
                for t in sel:
                    i = int(cidx_t[t])
                    if 20 <= i < 40:
                        pfx[i - 20] = raw[t]
                        pkn[i - 20] = True
                Gc = P.chunks(F[0], W[0], S[fo], n, prefix_deg=pfx, delay=idl)
            # 이 chunk 의 기록된 실행 구간과 가장 잘 맞는 noise 8 개 → 다음 chunk prefix 의 미기록 부분 추정
            sel = np.where(cid_t == k)[0]
            idx = cidx_t[sel].astype(int)
            ok = idx < 50
            err = np.sqrt(((Gc[:, idx[ok], :5] - raw[sel[ok], None, :5].transpose(1, 0, 2)) ** 2).mean((1, 2)))
            best = np.argsort(err)[:8]
            prev_est = Gc[best].mean(0)
            Us.append(U[:8] if n < args.n else U)
            Gs.append(Gc[:8] if n < args.n else Gc)
            FO.append(fo), MF.append(mf), DL.append(d), IDL.append(-1 if idl is None else idl), PFX.append(pfx), PKN.append(pkn), NN.append(n)
        nmin = min(NN)
        np.savez_compressed(out, U=np.stack([u[:nmin] for u in Us], 1), G=np.stack([x[:nmin] for x in Gs], 1),
                            U_early=np.stack([u for u, nn in zip(Us, NN) if nn == args.n], 1) if NN.count(args.n) else np.zeros(0),
                            G_early=np.stack([x for x, nn in zip(Gs, NN) if nn == args.n], 1) if NN.count(args.n) else np.zeros(0),
                            n_early=NN.count(args.n), obs_frame=np.array(FO), merge_frame=np.array(MF), delay=np.array(DL),
                            inference_delay=np.array(IDL), prefix_deg=np.array(PFX), prefix_known=np.array(PKN), chunk_id=mm.chunk_id.values)
        print(f"{tag}: {len(FO)} chunks ({NN.count(args.n)} with n={args.n}), gpu_s {P.gpu_s:.0f}", flush=True)


if __name__ == "__main__":
    main()
