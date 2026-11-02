"""오프라인 진단: 로봇 없이 학습 데이터 관측으로 pi05 chunk 를 뽑아 chunk 안의 흔들림을 잰다.
사용: python offline_chunk_jitter.py <ckpt_dir> <dtype bfloat16|float32> <steps,steps,...> <out.json>
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

ckpt, dtype, steps_list, out = sys.argv[1], sys.argv[2], [int(s) for s in sys.argv[3].split(",")], sys.argv[4]
REPO = sys.argv[5] if len(sys.argv) > 5 else "oxr/so101_redbox_all"
ROOT = sys.argv[6] if len(sys.argv) > 6 else "/home/user/so101_runs/main/redbox_all/dataset"
H = 50
SEEDS = [0, 1, 2]
K = np.ones(9) / 9

ds = LeRobotDataset(REPO, root=ROOT)
ep = ds.meta.episodes
# 12 개 시점: 과제·그룹이 섞이도록 에피소드 6개 × (시작 직후, 중간)
picks = []
n_ep = ds.meta.total_episodes
for e in [int(n_ep * f) for f in (0.013, 0.18, 0.36, 0.52, 0.70, 0.91)]:
    s, t = ep[e]["dataset_from_index"], ep[e]["dataset_to_index"]
    picks += [s + 10, s + (t - s) // 2]

cfg = PreTrainedConfig.from_pretrained(ckpt)
cfg.dtype = dtype
t0 = time.time()
policy = PI05Policy.from_pretrained(ckpt, config=cfg).to("cuda").eval()
pre, post = make_pre_post_processors(cfg, pretrained_path=ckpt)
print(f"loaded {ckpt} dtype={dtype} in {time.time() - t0:.0f}s", flush=True)

A_all = np.stack(ds.hf_dataset.select_columns("action")[:]["action"])


def jitter(chunk):
    """chunk (H,6) → 9프레임 이동평균 잔차 std, 1차 차분 부호 바뀜 비율, 2차 차분 RMS."""
    sm = np.stack([np.convolve(np.pad(chunk[:, j], 4, mode="edge"), K, "valid") for j in range(6)], 1)
    res = (chunk - sm)[4:-4]
    d1 = np.diff(chunk, axis=0)
    flips = (np.sign(d1[1:]) * np.sign(d1[:-1]) < 0).mean(0)
    d2 = np.sqrt((np.diff(chunk, 2, axis=0) ** 2).mean(0))
    return res.std(0), flips, d2


results = {"ckpt": ckpt, "dtype": dtype, "runs": {}}
gt = [jitter(A_all[i : i + H]) for i in picks]
results["gt"] = {n: np.mean([g[k] for g in gt], 0).round(3).tolist() for k, n in enumerate(["res_std", "flip", "d2_rms"])}
for steps in steps_list:
    stats, maes, firsts, lat = [], [], [], []
    for i in picks:
        item = ds[i]
        batch = pre({k: v for k, v in item.items() if k.startswith("observation") or k == "task"})
        for seed in SEEDS:
            g = torch.Generator(device="cuda").manual_seed(seed)
            noise = torch.randn((1, cfg.chunk_size, cfg.max_action_dim), generator=g, device="cuda", dtype=torch.float32)
            torch.cuda.synchronize(); t1 = time.time()
            with torch.no_grad():
                images, img_masks = policy._preprocess_images(batch)
                states, state_masks = policy._prepare_memory_states(batch)
                act = policy.model.sample_actions(images, img_masks, batch["observation.language.tokens"],
                                                  batch["observation.language.attention_mask"], states=states,
                                                  state_masks=state_masks, noise=noise, num_steps=steps)
            torch.cuda.synchronize(); lat.append(time.time() - t1)
            act = post(act[:, :, :6].float()).cpu().numpy()[0]
            stats.append(jitter(act))
            maes.append(np.abs(act - A_all[i : i + H]).mean(0))
            firsts.append(np.abs(act[0] - np.asarray(item["observation.state"])).tolist())
    results["runs"][str(steps)] = {
        "res_std": np.mean([s[0] for s in stats], 0).round(3).tolist(),
        "flip": np.mean([s[1] for s in stats], 0).round(3).tolist(),
        "d2_rms": np.mean([s[2] for s in stats], 0).round(3).tolist(),
        "mae_vs_gt": np.mean(maes, 0).round(2).tolist(),
        "first_action_minus_state": np.mean(firsts, 0).round(2).tolist(),
        "latency_s": round(float(np.median(lat)), 3),
    }
    print(steps, json.dumps(results["runs"][str(steps)]), flush=True)
print("gt", json.dumps(results["gt"]), flush=True)
json.dump(results, open(out, "w"), indent=1)
