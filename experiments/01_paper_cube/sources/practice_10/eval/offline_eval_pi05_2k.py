"""practice_10 pi05_2k 오프라인 확인 (팔·카메라 연결 없음, 데이터셋 읽기만).

lerobot-rollout --inference.type=sync 과 같은 경로로 추론한다:
  prepare_observation_for_inference -> preprocessor -> predict_action_chunk -> postprocessor
에피소드마다 50프레임(= n_action_steps) 간격으로 그 시점의 녹화 관측을 넣어 chunk 를 받고,
chunk 를 이어 붙인 open-loop 궤적을 녹화 action 과 비교한다.

실행: PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python offline_eval_pi05_2k.py
결과: pi05_2k_offline.npz / pi05_2k_offline.json (그래프는 plot_pi05_2k.py)
"""

import json
import time
from pathlib import Path

import numpy as np
import torch

from lerobot.configs import PreTrainedConfig
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.policies import get_policy_class, make_pre_post_processors
from lerobot.policies.utils import prepare_observation_for_inference

HOME = Path.home()
SESSION = HOME / "so101_runs/practice/practice_10"
CKPT = SESSION / "train/pi05_2k/checkpoints/002000/pretrained_model"
OUT = SESSION / "eval"
EPISODES = [1, 4]  # 가장 긴 판(29.3 s)과 가장 짧은 판(17.4 s)
N_TIMING = 30  # 추론 시간 측정용 추가 호출 수
SEED = 0

device = torch.device("cuda")
torch.manual_seed(SEED)

cfg = PreTrainedConfig.from_pretrained(CKPT)
cfg.pretrained_path = CKPT
cfg.device = "cuda"
policy = get_policy_class(cfg.type).from_pretrained(CKPT, config=cfg)
policy.to(device).eval()
pre, post = make_pre_post_processors(
    policy_cfg=cfg,
    pretrained_path=CKPT,
    preprocessor_overrides={"device_processor": {"device": "cuda"}},
)
chunk = cfg.n_action_steps
print(f"chunk_size={cfg.chunk_size} n_action_steps={cfg.n_action_steps} "
      f"num_inference_steps={cfg.num_inference_steps} dtype={cfg.dtype}")

ds = LeRobotDataset("oxr/so101_cubebox_practice10", root=SESSION / "dataset", return_uint8=True)
names = ds.meta.features["action"]["names"]
cams = [k for k in ds.meta.features if k.startswith("observation.images.")]
fps = ds.meta.fps


def obs_from_item(item):
    """데이터셋 프레임 -> 로봇이 주는 형태(numpy, 이미지 HWC uint8)."""
    obs = {"observation.state": item["observation.state"].numpy().astype(np.float32)}
    for c in cams:
        img = item[c]
        if img.ndim == 3 and img.shape[0] == 3:
            img = img.permute(1, 2, 0)
        obs[c] = np.ascontiguousarray(img.numpy())
    return obs


def infer(obs, task):
    """sync 엔진과 같은 순서. (actions[chunk, 6], 단계별 시간 ms) 반환."""
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    with torch.inference_mode():
        o = prepare_observation_for_inference(dict(obs), device, task, "so101_follower")
        o = pre(o)
        torch.cuda.synchronize()
        t1 = time.perf_counter()
        a = policy.predict_action_chunk(o)[:, :chunk]
        torch.cuda.synchronize()
        t2 = time.perf_counter()
        a = post(a)
        a = a.squeeze(0).float().cpu().numpy()
    t3 = time.perf_counter()
    return a, {"pre": (t1 - t0) * 1e3, "model": (t2 - t1) * 1e3, "post": (t3 - t2) * 1e3, "total": (t3 - t0) * 1e3}


ep_meta = ds.meta.episodes
timings = []
first_call = None
results = {}
arrays = {}
for ep in EPISODES:
    start = int(ep_meta[ep]["dataset_from_index"])
    end = int(ep_meta[ep]["dataset_to_index"])
    n = end - start
    rec_action = np.stack([np.asarray(ds.hf_dataset[start + i]["action"], dtype=np.float32) for i in range(n)])
    rec_state = np.stack([np.asarray(ds.hf_dataset[start + i]["observation.state"], dtype=np.float32) for i in range(n)])
    pred = np.zeros_like(rec_action)
    hold = np.zeros_like(rec_action)  # 비교 기준: chunk 시작 때 자세를 그대로 유지
    horizon_err = []  # (k, 6) per chunk
    task = None
    for t in range(0, n, chunk):
        item = ds[start + t]
        task = item["task"]
        a, tm = infer(obs_from_item(item), task)
        if first_call is None:
            first_call = tm
        else:
            timings.append(tm)
        m = min(chunk, n - t)
        pred[t:t + m] = a[:m]
        hold[t:t + m] = rec_state[t]
        horizon_err.append(np.abs(a[:m] - rec_action[t:t + m]))
    err = np.abs(pred - rec_action)
    herr = np.full((len(horizon_err), chunk, len(names)), np.nan)
    for i, h in enumerate(horizon_err):
        herr[i, : len(h)] = h
    results[ep] = {
        "frames": n,
        "chunks": len(horizon_err),
        "mae_per_joint": dict(zip(names, err.mean(0).round(2).tolist())),
        "mae_arm5": round(float(err[:, :5].mean()), 2),
        "mae_hold_baseline_per_joint": dict(zip(names, np.abs(hold - rec_action).mean(0).round(2).tolist())),
        "mae_first10_per_joint": dict(zip(names, np.nanmean(herr[:, :10], axis=(0, 1)).round(2).tolist())),
        "max_err_per_joint": dict(zip(names, err.max(0).round(1).tolist())),
    }
    arrays[f"ep{ep}_pred"] = pred
    arrays[f"ep{ep}_rec"] = rec_action
    arrays[f"ep{ep}_state"] = rec_state
    arrays[f"ep{ep}_horizon_err"] = herr
    print(f"ep {ep}: {n} frames, {len(horizon_err)} chunks, arm5 MAE {results[ep]['mae_arm5']}")

# 추가 시간 측정: 여러 프레임에서 반복 호출
rng = np.random.default_rng(SEED)
for idx in rng.integers(0, len(ds), N_TIMING):
    item = ds[int(idx)]
    _, tm = infer(obs_from_item(item), item["task"])
    timings.append(tm)


def stat(key):
    v = np.array([t[key] for t in timings])
    return {"mean": round(float(v.mean()), 1), "p50": round(float(np.median(v)), 1),
            "p95": round(float(np.percentile(v, 95)), 1), "max": round(float(v.max()), 1)}


summary = {
    "checkpoint": str(CKPT),
    "episodes": results,
    "joint_names": names,
    "fps": fps,
    "chunk_size": cfg.chunk_size,
    "n_action_steps": cfg.n_action_steps,
    "num_inference_steps": cfg.num_inference_steps,
    "dtype": cfg.dtype,
    "timing_ms": {k: stat(k) for k in ["pre", "model", "post", "total"]},
    "timing_calls": len(timings),
    "first_call_ms": {k: round(v, 1) for k, v in first_call.items()},
    "gpu_max_allocated_gb": round(torch.cuda.max_memory_allocated() / 1e9, 2),
    "seed": SEED,
}
np.savez(OUT / "pi05_2k_offline.npz", **arrays, joint_names=np.array(names), chunk=chunk, fps=fps)
(OUT / "pi05_2k_offline.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
print(json.dumps(summary["timing_ms"], indent=1))
print("first call", summary["first_call_ms"], "gpu max GB", summary["gpu_max_allocated_gb"])
