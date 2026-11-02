"""p16b 닫힘 명령을 낸 chunk 를 같은 관측 · 같은 prefix 로 noise 32 개 다시 뽑기: RTC 안내 있음 (G) vs 없음 (U) (GPU, 오프라인, 로봇 연결 없음).

입력: filter_ab/p16_events.csv (판 · 이벤트 · plan_chunk · plan_idx_at_tc), 각 실행 diag/ (obs PNG · obs_state · prefix · inference_delay · noise)
재현 확인: 기록 noise 로 G 를 다시 계산하면 기록 chunk 와 같아야 함 (차 출력).
판별 · 이벤트마다 noise 32 개 (seed 777):
  close_idx  = 계획 그리퍼 닫힘 시작 index (gripper < 앞선 최대 − 3 인 첫 index, 없으면 50)
  early      = close_idx ≤ (실제 닫힘 명령이 나온 index i_c) + 2 인 비율
  z_left     = 닫힘 index 에서 계획 FK z − 그 뒤 계획 최저 z (cm, 상대값. 닫힐 때 계획상 남은 하강)
출력: filter_ab/p16b_close_resample.csv
사용: nice -n 19 env PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python p16b_close_chunk_resample.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import cube_coords as CC  # noqa: E402

ac = CC.ac
D2 = CC.D2
AB = D2 / "pan_inference_diagnostic/filter_ab"
ROLL = D2 / "eval/rollouts"
RUNS = {"A": "20261029_170219_32_20000_20k_filt_on", "B": "20261029_170818_32_20000_20k_filt_off"}
J = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
CKPT = D2 / "train/32_20000/pi05_expert_bs32_20k/checkpoints/020000/pretrained_model"
TASK = "pick up the red cube and put it in the brown box"


def close_idx(gp):
    k = np.where(gp < np.maximum.accumulate(gp) - 3)[0]
    return int(k[0]) if len(k) else 50


def main():
    import cv2
    import torch
    from lerobot.configs import RTCAttentionSchedule
    from lerobot.policies.factory import make_pre_post_processors
    from lerobot.policies.pi05.modeling_pi05 import PI05Policy
    from lerobot.policies.rtc.configuration_rtc import RTCConfig
    from lerobot.policies.utils import prepare_observation_for_inference
    from lerobot.utils.feature_utils import build_dataset_frame

    policy = PI05Policy.from_pretrained(str(CKPT)).to("cuda").eval()
    policy.config.num_inference_steps = 5
    policy.config.rtc_config = RTCConfig(enabled=True, mode="guided", prefix_attention_schedule=RTCAttentionSchedule.EXP,
                                         max_guidance_weight=10.0, execution_horizon=20)
    policy.init_rtc_processor()
    pre, post = make_pre_post_processors(policy.config, pretrained_path=str(CKPT), preprocessor_overrides={"device_processor": {"device": "cuda"}})
    feats = {"observation.state": {"dtype": "float32", "shape": (6,), "names": [f"{j}.pos" for j in J]},
             "observation.images.front": {"dtype": "video", "shape": (480, 640, 3), "names": None},
             "observation.images.wrist": {"dtype": "video", "shape": (480, 640, 3), "names": None}}
    N = 32
    bank = torch.randn((N, 50, 32), generator=torch.Generator(device="cpu").manual_seed(777))
    E = pd.read_csv(AB / "p16_events.csv")
    E = E[E.event.astype(str) != "lost"]
    rows = []
    for _, e in E.iterrows():
        dg = ROLL / RUNS[e.tag[0]] / "diag"
        cid, ic = int(e.plan_chunk), int(e.plan_idx_at_tc)
        m = next(json.loads(x) for x in (dg / "chunks.jsonl").read_text().splitlines() if json.loads(x)["chunk_id"] == cid)
        z = np.load(dg / "chunks" / f"c{cid:05d}.npz")
        obs = {f"{j}.pos": float(v) for j, v in zip(J, m["obs_state"])}
        for cam in ("front", "wrist"):
            obs[cam] = cv2.cvtColor(cv2.imread(str(dg / "obs" / f"c{cid:05d}_{cam}.png")), cv2.COLOR_BGR2RGB)
        b = pre(dict(prepare_observation_for_inference(build_dataset_frame(feats, obs, prefix="observation"), torch.device("cuda"), TASK, "so_follower"),
                     task=[TASK]))
        bb = {k: (v.repeat(N, *([1] * (v.dim() - 1))) if torch.is_tensor(v) else ([TASK] * N if k == "task" else v)) for k, v in b.items()}
        has_p = "prefix" in z
        with torch.no_grad():
            kw = dict(inference_delay=m.get("inference_delay"), prev_chunk_left_over=torch.from_numpy(z["prefix"]).cuda()) if has_p else {}
            rep = post(policy.predict_action_chunk(b, noise=torch.from_numpy(z["noise"]).cuda()[None].float(), **kw)).squeeze(0).float().cpu().numpy()
            pk = dict(inference_delay=m.get("inference_delay"), prev_chunk_left_over=torch.from_numpy(z["prefix"]).cuda()[None].repeat(N, 1, 1)) if has_p else {}
            if has_p and z["prefix"].ndim == 3:
                pk["prev_chunk_left_over"] = torch.from_numpy(z["prefix"]).cuda().repeat(N, 1, 1)
            G = post(policy.predict_action_chunk(bb, noise=bank.cuda(), **pk)).float().cpu().numpy()
            U = post(policy.predict_action_chunk(bb, noise=bank.cuda())).float().cpu().numpy()
        r = dict(tag=e.tag, event=e.event, cond=e.cond, chunk=cid, i_c=ic, has_prefix=has_p, inference_delay=m.get("inference_delay"),
                 replay_max_abs_deg=float(np.abs(rep - z["processed"]).max()), logged_close_idx=close_idx(z["processed"][:, 5]))
        for nm, A in (("G", G), ("U", U)):
            ci = np.array([close_idx(a[:, 5]) for a in A])
            zl = []
            for a, c in zip(A, ci):
                if c >= 50:
                    zl.append(np.nan)
                    continue
                zz = ac.tcp(a[:, :5])[:, 2]
                zl.append(float(zz[c] - zz[c:].min()))
            r.update({f"{nm}_close_idx_p10": float(np.percentile(ci, 10)), f"{nm}_close_idx_med": float(np.median(ci)),
                      f"{nm}_close_idx_p90": float(np.percentile(ci, 90)), f"{nm}_no_close_frac": float((ci >= 50).mean()),
                      f"{nm}_early_frac": float((ci <= ic + 2).mean()), f"{nm}_z_left_med": float(np.nanmedian(zl)) if np.isfinite(zl).any() else None})
        rows.append(r)
        print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()}, flush=True)
    pd.DataFrame(rows).to_csv(AB / "p16b_close_resample.csv", index=False)


if __name__ == "__main__":
    main()
