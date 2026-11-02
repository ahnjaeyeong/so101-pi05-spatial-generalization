"""q00 환경 · 설정 · 필터 끔 확인 사실 (읽기만, CPU). 로봇 연결 없음.
출력: tables/q00_env_facts.json
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python q00_env_facts.py
"""
import hashlib
import json
import platform
from importlib import metadata
from pathlib import Path

import numpy as np
import pandas as pd

D2 = Path.home() / "so101_runs/main_k8/d2"
OUT = D2 / "pan_inference_diagnostic/offline_pan_reversal_filter_off"
ROLL = D2 / "eval/rollouts"
CKPT = D2 / "train/32_20000/pi05_expert_bs32_20k/checkpoints/020000/pretrained_model"
RUNS = ["20261029_155513_32_20000_20k_pan_diag", "20261029_160831_32_20000_20k_pan_diag",
        "20261029_170219_32_20000_20k_filt_on", "20261029_170818_32_20000_20k_filt_off"]


def sha(p, n=1 << 24):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        h.update(f.read(n))
    return h.hexdigest()[:16]


def main():
    F = {"python": platform.python_version(), "machine": platform.machine(), "node": platform.node()}
    for pkg in ("lerobot", "torch", "numpy", "pandas", "opencv-python", "opencv-python-headless"):
        try:
            F[pkg] = metadata.version(pkg)
        except Exception:
            pass
    cfg = json.loads((CKPT / "config.json").read_text())
    F["ckpt"] = str(CKPT)
    F["ckpt_model_sha256_first16MB"] = sha(CKPT / "model.safetensors")
    F["ckpt_config"] = {k: cfg.get(k) for k in ("type", "n_obs_steps", "chunk_size", "n_action_steps", "num_inference_steps", "train_expert_only")}
    E = pd.read_csv(OUT / "tables/q01b_episodes.csv")
    runs = {}
    for r in RUNS:
        m = json.loads((ROLL / r / "diag/manifest.json").read_text())
        argv = m["argv"]
        opt = {a.split("=", 1)[0].lstrip("-"): a.split("=", 1)[1] for a in argv if a.startswith("--") and "=" in a and "cameras" not in a}
        ch = [json.loads(x) for x in (ROLL / r / "diag/chunks.jsonl").read_text().splitlines()]
        tags = E[E.run == r].diag_ep.tolist()
        ch = [c for c in ch if c["episode"] in tags]
        ad = pd.Series([c.get("applied_delay") for c in ch if c["qsize_before"] > 0]).value_counts().to_dict()
        idl = pd.Series([c.get("inference_delay") for c in ch]).value_counts().to_dict()
        FL = pd.read_csv(ROLL / r / "filter_log.csv", dtype={"vclip_mask": str, "ema_reset_mask": str})
        f = FL[(FL.event == "cmd") & FL.episode.isin(tags)]
        TK = pd.read_csv(ROLL / r / "diag/ticks.csv")
        t = TK[TK.episode.isin(tags) & (TK.pop_chunk >= 0)]
        runs[r] = {"opts": {k: opt.get(k) for k in ("policy.num_inference_steps", "inference.type", "inference.rtc.execution_horizon", "inference.rtc.prefix_attention_schedule",
                                                    "inference.queue_threshold", "robot.max_relative_target", "arm_filter", "rollout_guard", "fps")},
                   "rollout_logged_opts": m.get("rollout_logged_opts", {}),
                   "n_saved_eps": len(tags), "n_chunks": len(ch), "applied_delay_counts": {str(k): int(v) for k, v in ad.items()},
                   "inference_delay_counts": {str(k): int(v) for k, v in idl.items()},
                   "pan_out_minus_rtc_absmax": float((f.out_shoulder_pan - f.raw_shoulder_pan).abs().max()),
                   "pan_sent_ne_goal_in_ticks": int((t.sent_shoulder_pan - t.goal_in_shoulder_pan).abs().gt(1e-3).sum()), "n_ticks": int(len(t))}
    F["runs"] = runs
    F["rtc_guidance_note"] = "max_guidance_weight: lerobot RTCConfig 기본 (q02 는 10.0 명시, 기존 p16b 와 같음)"
    (OUT / "tables/q00_env_facts.json").write_text(json.dumps(F, indent=1, ensure_ascii=False))
    print(json.dumps(F, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
