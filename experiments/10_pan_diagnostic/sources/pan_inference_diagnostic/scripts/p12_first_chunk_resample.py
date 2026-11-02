"""p12 파일럿 판 첫 chunk 를 '실제로 받은 관측' 그대로 두고 noise 만 바꿔 다시 뽑기 (GPU, 오프라인 재추론, 로봇 연결 없음).

판 첫 chunk 는 prefix 가 없어 RTC 안내가 없다 → 같은 관측 (diag/obs PNG · obs_state) 에 noise N 개를 넣은 출력 분포가
'그 자리 · 그 관측에서 모델 raw 출력이 낼 수 있는 범위' 다. 기록된 첫 chunk (실측, 실제 noise) 가 그 분포 어디에 있는지 본다.
p05 와 같은 입력 경로 (build_dataset_frame → prepare_observation_for_inference → preprocessor) · 같은 정책 설정.
noise: 기록된 noise 1 개 (재현 확인) + seed 4321 의 N 개.
입력: pilot/pilot_episodes.csv (판 · 첫 chunk id · pe · s0), 각 실행 diag/
출력: pilot/p12_first_chunk_resample.csv (판별), pilot/p12_first_chunk_resample.npz (판별 pan (N, 50))
반사실 --state_pan V: state 입력의 pan 만 V 로 (학습 시작 평균 −4.3°). 영상 속 팔은 실제 위치 그대로라 입력끼리 어긋난다 — 민감도 확인용.
사용: nice -n 19 env PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python p12_first_chunk_resample.py [--n 64] [--state_pan -4.3]
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

D2 = Path.home() / "so101_runs/main_k8/d2"
OUT = D2 / "pan_inference_diagnostic/pilot"
J = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
CKPT = D2 / "train/32_20000/pi05_expert_bs32_20k/checkpoints/020000/pretrained_model"
TASK = "pick up the red cube and put it in the brown box"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=64)
    ap.add_argument("--state_pan", type=float, default=None,
                    help="반사실: 관측 state 의 shoulder_pan 만 이 값으로 바꿈 (영상은 그대로 — 영상 속 팔 위치와 어긋남). 출력 파일 이름에 _statepan<값>")
    a = ap.parse_args()
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
    g = torch.Generator(device="cpu").manual_seed(4321)
    bank = torch.randn((a.n, 50, 32), generator=g)
    P = pd.read_csv(OUT / "pilot_episodes.csv")
    rows, arrs = [], {}
    for _, r in P.iterrows():
        dg = D2 / "eval/rollouts" / r.run / "diag"
        cid = int(r.first_chunk_id)
        m = next(json.loads(x) for x in (dg / "chunks.jsonl").read_text().splitlines() if json.loads(x)["chunk_id"] == cid)
        z = np.load(dg / "chunks" / f"c{cid:05d}.npz")
        st_in = list(m["obs_state"])
        if a.state_pan is not None:
            st_in[0] = a.state_pan
        obs = {f"{j}.pos": float(v) for j, v in zip(J, st_in)}
        for cam in ("front", "wrist"):
            obs[cam] = cv2.cvtColor(cv2.imread(str(dg / "obs" / f"c{cid:05d}_{cam}.png")), cv2.COLOR_BGR2RGB)
        fr = build_dataset_frame(feats, obs, prefix="observation")
        b = prepare_observation_for_inference(fr, torch.device("cuda"), TASK, "so_follower")
        b["task"] = [TASK]
        b = pre(b)
        with torch.no_grad():
            # 기록 noise 로 재현 확인
            rep = post(policy.predict_action_chunk(b, noise=torch.from_numpy(z["noise"]).cuda()[None].float())).squeeze(0).float().cpu().numpy()
            bb = {k: (v.repeat(a.n, *([1] * (v.dim() - 1))) if torch.is_tensor(v) else (v * a.n if isinstance(v, list) else v)) for k, v in b.items()}
            out = post(policy.predict_action_chunk(bb, noise=bank.cuda())).float().cpu().numpy()
        pan = out[:, :, 0]
        s0 = m["obs_state"][0]  # 이동 · 비율은 실제 시작 pan 기준 (반사실에서도 같음)
        logged = z["processed"][:, 0]
        r2 = dict(label=r.label, run=r.run, episode=int(r.episode), chunk_id=cid, s0=s0, pe=r.pe, coord_status=r.coord_status,
                  replay_max_abs_deg=float(np.abs(rep - z["processed"]).max()),
                  logged_idx29=logged[29], logged_idx49=logged[49])
        for idx in (29, 49):
            r2[f"move{idx}_p10"], r2[f"move{idx}_p50"], r2[f"move{idx}_p90"] = np.percentile(pan[:, idx] - s0, [10, 50, 90])
            r2[f"logged_move{idx}_rank"] = float((pan[:, idx] < logged[idx]).mean() + 0.5 * (pan[:, idx] == logged[idx]).mean())
            if not pd.isna(r.pe) and abs(r.pe - s0) >= 3:
                fr_ = (pan[:, idx] - s0) / (r.pe - s0)
                r2[f"gain{idx}_p10"], r2[f"gain{idx}_p50"], r2[f"gain{idx}_p90"] = np.percentile(fr_, [10, 50, 90])
                r2[f"gain{idx}_lt10"] = float((fr_ < 0.1).mean())
                r2[f"gain{idx}_ge50"] = float((fr_ >= 0.5).mean())
                r2[f"logged_gain{idx}"] = (logged[idx] - s0) / (r.pe - s0)
                r2[f"dir{idx}_ok_frac"] = float((np.sign(pan[:, idx] - s0) == np.sign(r.pe - s0)).mean())
        rows.append(r2)
        arrs[r.label] = pan.astype(np.float32)
        print(r.label, {k: round(v, 2) for k, v in r2.items() if isinstance(v, float) and ("gain29" in k or "replay" in k)}, flush=True)
    D = pd.DataFrame(rows)
    tag = "" if a.state_pan is None else f"_statepan{a.state_pan:g}"
    D.to_csv(OUT / f"p12_first_chunk_resample{tag}.csv", index=False)
    np.savez_compressed(OUT / f"p12_first_chunk_resample{tag}.npz", **arrs)


if __name__ == "__main__":
    main()
