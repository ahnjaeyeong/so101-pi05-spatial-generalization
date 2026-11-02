"""pi05_2k guided-RTC 추론 시간 (오프라인, 팔 연결 없음). lerobot-rollout --inference.type=rtc 의 호출 형태를 흉내낸다."""
import json, math, time
from pathlib import Path
import numpy as np, torch
from lerobot.configs import PreTrainedConfig
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.policies import get_policy_class, make_pre_post_processors
from lerobot.policies.rtc.configuration_rtc import RTCConfig
from lerobot.policies.utils import prepare_observation_for_inference
from lerobot.rollout.inference.rtc import _normalize_prev_actions_length

S = Path.home() / "so101_runs/practice/practice_10"
CKPT = S / "train/pi05_2k/checkpoints/002000/pretrained_model"
dev = torch.device("cuda"); torch.manual_seed(0)
cfg = PreTrainedConfig.from_pretrained(CKPT); cfg.pretrained_path = CKPT; cfg.device = "cuda"
policy = get_policy_class(cfg.type).from_pretrained(CKPT, config=cfg).to(dev).eval()
rtc = RTCConfig()  # 기본값: guided, execution_horizon 10, max_guidance_weight 10
policy.config.rtc_config = rtc; policy.init_rtc_processor()
pre, post = make_pre_post_processors(policy_cfg=cfg, pretrained_path=CKPT, preprocessor_overrides={"device_processor": {"device": "cuda"}})
ds = LeRobotDataset("oxr/so101_cubebox_practice10", root=S / "dataset", return_uint8=True)
cams = [k for k in ds.meta.features if k.startswith("observation.images.")]
QUEUE_THRESHOLD, dt = 30, 1 / 30
start = int(ds.meta.episodes[1]["dataset_from_index"])
prev_raw, lat_max, rows = None, 0.0, []
for i in range(25):
    item = ds[start + 20 * i]
    obs = {"observation.state": item["observation.state"].numpy().astype(np.float32)}
    for c in cams:
        obs[c] = np.ascontiguousarray(item[c].permute(1, 2, 0).numpy())
    delay = math.ceil(lat_max / dt) if lat_max else 0
    prev = None
    if prev_raw is not None:
        prev = _normalize_prev_actions_length(prev_raw[0, -QUEUE_THRESHOLD:], target_steps=rtc.execution_horizon)
    torch.cuda.synchronize(); t0 = time.perf_counter()
    with torch.inference_mode():
        o = pre(prepare_observation_for_inference(dict(obs), dev, item["task"], "so101_follower"))
    a = policy.predict_action_chunk(o, inference_delay=delay, prev_chunk_left_over=prev)
    with torch.inference_mode():
        post(a)
    torch.cuda.synchronize(); lat = time.perf_counter() - t0
    prev_raw = a.detach()
    if i >= 2: lat_max = max(lat_max, lat)
    rows.append({"call": i, "with_prefix": prev is not None, "delay_ticks": delay, "ms": round(lat * 1e3, 1)})
    print(rows[-1], flush=True)
w = np.array([r["ms"] for r in rows[2:] if r["with_prefix"]])
summ = {"guided_rtc_ms": {"mean": round(float(w.mean()), 1), "max": round(float(w.max()), 1), "n": int(len(w))},
        "first_calls_ms": [r["ms"] for r in rows[:2]], "delay_ticks_used_max": max(r["delay_ticks"] for r in rows),
        "execution_horizon": rtc.execution_horizon, "queue_threshold": QUEUE_THRESHOLD,
        "gpu_max_allocated_gb": round(torch.cuda.max_memory_allocated() / 1e9, 2)}
(S / "eval/pi05_2k_rtc_timing.json").write_text(json.dumps({"summary": summ, "calls": rows}, indent=1))
print(summ)
