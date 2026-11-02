"""num_inference_steps 별 추론 시간(sync·guided RTC)과 정확도 (오프라인, 팔 연결 없음). 결과: steps_timing.json"""
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
dev = torch.device("cuda")
ds = LeRobotDataset("oxr/so101_cubebox_practice10", root=S / "dataset", return_uint8=True)
cams = [k for k in ds.meta.features if k.startswith("observation.images.")]
out = {}
for steps in (10, 5):
    cfg = PreTrainedConfig.from_pretrained(CKPT); cfg.pretrained_path = CKPT; cfg.device = "cuda"; cfg.num_inference_steps = steps
    policy = get_policy_class(cfg.type).from_pretrained(CKPT, config=cfg).to(dev).eval()
    pre, post = make_pre_post_processors(policy_cfg=cfg, pretrained_path=CKPT, preprocessor_overrides={"device_processor": {"device": "cuda"}})
    def obs(i):
        it = ds[i]; o = {"observation.state": it["observation.state"].numpy().astype(np.float32)}
        for c in cams: o[c] = np.ascontiguousarray(it[c].permute(1, 2, 0).numpy())
        return o, it["task"]
    def run(i, rtc=False, prev=None, delay=0):
        o, task = obs(i); torch.manual_seed(0); torch.cuda.synchronize(); t0 = time.perf_counter()
        with torch.inference_mode():
            x = pre(prepare_observation_for_inference(o, dev, task, "so101_follower"))
        if rtc:
            a = policy.predict_action_chunk(x, inference_delay=delay, prev_chunk_left_over=prev)
        else:
            with torch.inference_mode(): a = policy.predict_action_chunk(x)
        with torch.inference_mode(): p = post(a[:, :50]).squeeze(0).float().cpu().numpy()
        torch.cuda.synchronize(); return a.detach(), p, (time.perf_counter() - t0) * 1e3
    # 정확도: ep1·ep4, 50프레임 간격 open-loop (offline_eval 과 같은 방식)
    errs = []
    sync_ms = []
    for ep in (1, 4):
        a0, a1 = int(ds.meta.episodes[ep]["dataset_from_index"]), int(ds.meta.episodes[ep]["dataset_to_index"])
        rec = np.stack([np.asarray(ds.hf_dataset[i]["action"], dtype=np.float32) for i in range(a0, a1)])
        for t in range(0, a1 - a0, 50):
            _, p, ms = run(a0 + t); sync_ms.append(ms)
            m = min(50, a1 - a0 - t); errs.append(np.abs(p[:m] - rec[t:t + m]))
    err = np.concatenate(errs)
    # guided RTC 시간
    policy.config.rtc_config = RTCConfig(execution_horizon=20); policy.init_rtc_processor()
    a0 = int(ds.meta.episodes[1]["dataset_from_index"]); prev = None; rtc_ms = []
    for k in range(16):
        prev_in = None if prev is None else _normalize_prev_actions_length(prev[0, -30:], target_steps=20)
        prev, _, ms = run(a0 + 20 * k, rtc=True, prev=prev_in, delay=0 if prev is None else 10); rtc_ms.append(ms)
    s = np.array(sync_ms[2:]); r = np.array(rtc_ms[2:])
    out[steps] = {"sync_ms_mean": round(float(s.mean()), 1), "sync_ms_max": round(float(s.max()), 1),
                  "rtc_ms_mean": round(float(r.mean()), 1), "rtc_ms_max": round(float(r.max()), 1),
                  "mae_per_joint": np.round(err.mean(0), 2).tolist(), "mae_arm5": round(float(err[:, :5].mean()), 2)}
    print(steps, out[steps], flush=True)
    del policy; torch.cuda.empty_cache()
(S / "eval/steps_timing.json").write_text(json.dumps(out, indent=1))
