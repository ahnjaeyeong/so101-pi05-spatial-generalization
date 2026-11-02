"""p05 diag 기록 chunk 재현 · RTC 반사실 (GPU, 로봇 연결 없음, 체크포인트 읽기만).

diag/ 의 chunk 마다 기록된 입력 (추론 관측 PNG, 관측 state, noise, prefix = prev_chunk_left_over, inference_delay) 으로
  (a) 같은 조건 다시 계산 → 기록된 original 과의 차 (재현성 검사)
  (b) 같은 관측·같은 noise, prefix 없음 (RTC 안내 없음) → RTC 안내가 바꾼 몫 (반사실)
을 계산한다. 실물 설정과 같게: d2 020000, num_inference_steps 5, RTC guided EXP h20 max_guidance_weight 10.
출력: <diag>/replay/replay.csv (chunk 별 요약), replay.npz (키 rtc_off_c##### · replay_c#####: processed (50,6) °)
값의 종류: logged = 실물 기록 (RTC 안내 뒤 Action Expert 출력), replay = 기록 입력으로 다시 계산, rtc_off = 같은 관측·noise 로 안내 없이 계산 (오프라인 반사실, 실물 미적용).
판 첫 chunk (prefix 없음) 는 logged 자체가 RTC 안내 없는 출력이다.
사용: nice -n 19 env PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python p05_replay_check.py <diag 폴더> [--max N]
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

D2 = Path.home() / "so101_runs/main_k8/d2"
J = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
CKPT = D2 / "train/32_20000/pi05_expert_bs32_20k/checkpoints/020000/pretrained_model"
TASK = "pick up the red cube and put it in the brown box"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("diag")
    ap.add_argument("--max", type=int, default=0)
    args = ap.parse_args()
    root = Path(args.diag)
    import cv2
    import torch
    from lerobot.configs import RTCAttentionSchedule
    from lerobot.policies.factory import make_pre_post_processors
    from lerobot.policies.pi05.modeling_pi05 import PI05Policy
    from lerobot.policies.rtc.configuration_rtc import RTCConfig
    from lerobot.policies.utils import prepare_observation_for_inference
    from lerobot.utils.feature_utils import build_dataset_frame

    metas = [json.loads(x) for x in (root / "chunks.jsonl").read_text().splitlines()]
    if args.max:
        metas = metas[: args.max]
    policy = PI05Policy.from_pretrained(str(CKPT)).to("cuda").eval()
    policy.config.num_inference_steps = 5
    policy.config.rtc_config = RTCConfig(enabled=True, mode="guided", prefix_attention_schedule=RTCAttentionSchedule.EXP,
                                         max_guidance_weight=10.0, execution_horizon=20)
    policy.init_rtc_processor()
    pre, post = make_pre_post_processors(policy.config, pretrained_path=str(CKPT),
                                         preprocessor_overrides={"device_processor": {"device": "cuda"}})
    feats = {"observation.state": {"dtype": "float32", "shape": (6,), "names": [f"{j}.pos" for j in J]},
             "observation.images.front": {"dtype": "video", "shape": (480, 640, 3), "names": None},
             "observation.images.wrist": {"dtype": "video", "shape": (480, 640, 3), "names": None}}
    rows, rep, off = [], {}, {}
    for m in metas:
        cid = m["chunk_id"]
        z = np.load(root / "chunks" / f"c{cid:05d}.npz")
        if "noise" not in z or m.get("obs_state") is None:
            rows.append(dict(chunk_id=cid, skipped="no noise/state"))
            continue
        obs = {f"{j}.pos": float(v) for j, v in zip(J, m["obs_state"])}
        for cam in ("front", "wrist"):
            obs[cam] = cv2.cvtColor(cv2.imread(str(root / "obs" / f"c{cid:05d}_{cam}.png")), cv2.COLOR_BGR2RGB)
        fr = build_dataset_frame(feats, obs, prefix="observation")
        b = prepare_observation_for_inference(fr, torch.device("cuda"), TASK, "so_follower")
        b["task"] = [TASK]
        b = pre(b)
        noise = torch.from_numpy(z["noise"]).cuda()[None].to(torch.float32)
        prefix = torch.from_numpy(z["prefix"]).cuda() if "prefix" in z else None
        d = m.get("inference_delay")
        a_rep = policy.predict_action_chunk(b, noise=noise, inference_delay=d, prev_chunk_left_over=prefix)
        a_off = policy.predict_action_chunk(b, noise=noise, inference_delay=None, prev_chunk_left_over=None)
        p_rep = post(a_rep).squeeze(0).float().cpu().numpy()
        p_off = post(a_off).squeeze(0).float().cpu().numpy()
        o_log, p_log = z["original"], z["processed"]
        k0 = int(m["applied_delay"])
        win = slice(k0, min(k0 + 20, 50))
        rows.append(dict(chunk_id=cid, episode=m["episode"], applied_delay=k0, inference_delay=d, has_prefix=prefix is not None,
                         replay_max_abs_norm=float(np.abs(a_rep.squeeze(0).float().cpu().numpy() - o_log).max()),
                         replay_max_abs_deg=float(np.abs(p_rep - p_log).max()),
                         rtc_effect_pan_exec_mean=float((p_log[win, 0] - p_off[win, 0]).mean()),
                         rtc_effect_pan_exec_absmax=float(np.abs(p_log[win, 0] - p_off[win, 0]).max()),
                         rtc_effect_pan_idx49=float(p_log[49, 0] - p_off[49, 0]),
                         logged_pan_exec_end=float(p_log[min(k0 + 19, 49), 0]), off_pan_exec_end=float(p_off[min(k0 + 19, 49), 0]),
                         logged_pan_49=float(p_log[49, 0]), off_pan_49=float(p_off[49, 0]),
                         logged_pan_29=float(p_log[29, 0]), off_pan_29=float(p_off[29, 0]),
                         logged_pan_first_exec=float(p_log[k0, 0]), off_pan_first_exec=float(p_off[k0, 0])))
        rep[f"c{cid:05d}"] = p_rep
        off[f"c{cid:05d}"] = p_off
    out = root / "replay"
    out.mkdir(exist_ok=True)
    R = pd.DataFrame(rows)
    R.to_csv(out / "replay.csv", index=False)
    np.savez_compressed(out / "replay.npz", **{f"replay_{k}": v for k, v in rep.items()}, **{f"rtc_off_{k}": v for k, v in off.items()})
    print(R.describe().T.to_string())


if __name__ == "__main__":
    main()
