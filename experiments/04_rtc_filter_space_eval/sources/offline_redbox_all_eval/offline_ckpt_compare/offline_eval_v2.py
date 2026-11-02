"""체크포인트 오프라인 비교 v2 — 로봇 없이 학습 데이터 관측으로 chunk 를 뽑아 '작업 정확도'와 '잡음'을 따로 잰다.

사용: python -I offline_eval_v2.py <ckpt_dir> <repo_id> <dataset_root> <out.json> [num_steps=10]

샘플: 에피소드 16개(고르게) × 시점 3개 × 노이즈 seed 2개
  start  : 에피소드 10프레임째 (출발)
  pregrasp: 사람이 그리퍼를 닫기 시작한 순간(첫 close)보다 30프레임 앞 → chunk 안 30번째가 실제 파지 순간
  carry  : 첫 close + 30프레임 (운반)
지표 (팔 5관절, °):
  lp_mae      : 예측을 9프레임 이동평균한 '작업 성분'과 사람 action 의 평균 오차
  grasp_err   : pregrasp 에서 chunk 30번째(사람이 닫는 순간)의 작업 성분 오차 — 파지 자세 정확도
  grip_hit    : pregrasp 에서 예측 그리퍼가 chunk 20–45번째 사이에 10 아래로 닫히는지 (사람과 같은 타이밍에 쥐는가)
  res_std     : 예측 − 작업 성분 = 고주파 잡음 크기
  motion_ratio: 예측 작업 성분의 이동 거리 ÷ 사람 이동 거리 (1 보다 작으면 덜 움직임)
  seed_spread : 같은 관측에서 seed 0·1 예측 작업 성분 차이 (불확실성)
"""

import json
import sys
import time

import numpy as np
import torch

from lerobot.configs.policies import PreTrainedConfig
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.policies.factory import make_pre_post_processors
from lerobot.policies.pi05.modeling_pi05 import PI05Policy

ckpt, repo, root, out = sys.argv[1:5]
steps = int(sys.argv[5]) if len(sys.argv) > 5 else 10
H, K = 50, np.ones(9) / 9
ARM = slice(0, 5)

ds = LeRobotDataset(repo, root=root)
A_all = np.stack(ds.hf_dataset.select_columns("action")[:]["action"]).astype(np.float64)
ep = ds.meta.episodes
n_ep = ds.meta.total_episodes
samples = []
for e in np.linspace(0, n_ep - 1, 16).astype(int):
    s, t = int(ep[int(e)]["dataset_from_index"]), int(ep[int(e)]["dataset_to_index"])
    g = A_all[s:t, 5]
    opened = np.where(g > 15)[0]
    close = None
    if len(opened):
        after = np.where(g[opened[0]:] < 8)[0]
        if len(after):
            close = opened[0] + after[0]
    samples.append(("start", s + 10))
    if close is not None and close - 30 >= 0 and close + 30 + H <= t - s:
        samples.append(("pregrasp", s + close - 30))
        samples.append(("carry", s + close + 30))

cfg = PreTrainedConfig.from_pretrained(ckpt)
t0 = time.time()
policy = PI05Policy.from_pretrained(ckpt, config=cfg).to("cuda").eval()
pre, post = make_pre_post_processors(cfg, pretrained_path=ckpt)
print(f"loaded {ckpt} in {time.time() - t0:.0f}s, samples {len(samples)}", flush=True)


def lowpass(x):
    return np.stack([np.convolve(np.pad(x[:, j], 4, mode="edge"), K, "valid") for j in range(x.shape[1])], 1)


rec = []
for phase, i in samples:
    item = ds[i]
    batch = pre({k: v for k, v in item.items() if k.startswith("observation") or k == "task"})
    gt = A_all[i:i + H]
    preds = []
    for seed in (0, 1):
        g = torch.Generator(device="cuda").manual_seed(seed)
        noise = torch.randn((1, cfg.chunk_size, cfg.max_action_dim), generator=g, device="cuda", dtype=torch.float32)
        with torch.no_grad():
            images, img_masks = policy._preprocess_images(batch)
            states, state_masks = policy._prepare_memory_states(batch)
            act = policy.model.sample_actions(images, img_masks, batch["observation.language.tokens"],
                                              batch["observation.language.attention_mask"], states=states,
                                              state_masks=state_masks, noise=noise, num_steps=steps)
        preds.append(post(act[:, :, :6].float()).cpu().numpy()[0].astype(np.float64))
    lps = [lowpass(p) for p in preds]
    for p, lp in zip(preds, lps):
        r = {"phase": phase, "idx": int(i),
             "lp_mae": np.abs(lp[:, ARM] - gt[:, ARM]).mean(),
             "lp_mae_joint": np.abs(lp - gt).mean(0).tolist(),
             "res_std": (p - lp)[4:-4, ARM].std(0).mean(),
             "motion_ratio": np.abs(np.diff(lp[:, ARM], axis=0)).sum() / max(np.abs(np.diff(gt[:, ARM], axis=0)).sum(), 1e-6),
             "gt_motion": np.abs(np.diff(gt[:, ARM], axis=0)).sum(),
             "seed_spread": np.abs(lps[0][:, ARM] - lps[1][:, ARM]).mean()}
        if phase == "pregrasp":
            r["grasp_err"] = np.abs(lp[30, ARM] - gt[30, ARM]).mean()
            r["grasp_err_joint"] = np.abs(lp[30] - gt[30]).tolist()
            r["grip_hit"] = bool((p[20:46, 5] < 10).any())
        rec.append(r)


def summarize(rs):
    o = {k: float(np.mean([r[k] for r in rs])) for k in ("lp_mae", "res_std", "motion_ratio", "seed_spread", "gt_motion")}
    o["n"] = len(rs)
    g = [r for r in rs if r["phase"] == "pregrasp"]
    if g:
        o["grasp_err"] = float(np.mean([r["grasp_err"] for r in g]))
        o["grasp_err_joint"] = np.mean([r["grasp_err_joint"] for r in g], 0).round(2).tolist()
        o["grip_hit"] = float(np.mean([r["grip_hit"] for r in g]))
    o["lp_mae_joint"] = np.mean([r["lp_mae_joint"] for r in rs], 0).round(2).tolist()
    return o


res = {"ckpt": ckpt, "steps": steps, "all": summarize(rec)}
for ph in ("start", "pregrasp", "carry"):
    res[ph] = summarize([r for r in rec if r["phase"] == ph])
json.dump(res, open(out, "w"), indent=1)
print(json.dumps({k: (v if k in ("ckpt", "steps") else {kk: (round(vv, 3) if isinstance(vv, float) else vv) for kk, vv in v.items()}) for k, v in res.items()}), flush=True)
