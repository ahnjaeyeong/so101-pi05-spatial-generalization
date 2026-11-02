"""q05 민감도: 영상은 그대로 두고 state 의 pan 만 바꿔 넣은 RTC 없는 추론 (GPU, 오프라인). 로봇 연결 없음.

**물리적으로 일관된 반사실 관측이 아니다** (영상 속 팔은 기록 당시 자세). 결과는 '모델 출력이 state pan 입력에 얼마나 반응하는가' 의 민감도로만 쓴다.
상태: 아래 STATES (판 · chunk). 바꾸는 양 Δ ∈ {−30, −20, −10, 0, +10, +20, +30}° (pan state 에 더함, 다른 관절 그대로).
noise: torch.randn((32, 50, 32), seed 2026) 의 앞 32 개 = q02 bank 의 앞 32 개와 같음.
지표: 바꾼 state pan 기준 cum30 = a29 − (s0 + Δ), exec = a29 − a9 (U 만, prefix 없음).
출력: tables/q05_sensitivity.csv
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python q05_state_pan_sensitivity.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

D2 = Path.home() / "so101_runs/main_k8/d2"
OUT = D2 / "pan_inference_diagnostic/offline_pan_reversal_filter_off"
ROLL = D2 / "eval/rollouts"
CKPT = D2 / "train/32_20000/pi05_expert_bs32_20k/checkpoints/020000/pretrained_model"
TASK = "pick up the red cube and put it in the brown box"
J = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
DELTAS = (-30, -20, -10, 0, 10, 20, 30)


def states():
    Ch = pd.read_csv(OUT / "tables/q01b_chunks.csv")
    E = pd.read_csv(OUT / "tables/q01b_episodes.csv").set_index("tag")
    sel = []
    # A0 · B1: 지나침 (손목 보임 · 테두리 · 놓침) 각 시기 + 정상 접근 대조 (B0 · B2 · B3 under 손목 보임, aligned)
    for tag, wanted in (("A0", ["wrist_edge", "wrist_lost_after_seen"]), ("B1", ["wrist_lost_after_seen"])):
        g = Ch[(Ch.tag == tag) & (Ch.zone == "over") & Ch.wstate.isin(wanted)].sort_values("chunk_id")
        idx = np.linspace(0, len(g) - 1, min(4, len(g))).round().astype(int)
        sel.append(g.iloc[idx])
    for tag in ("B0", "B2", "B3"):
        g = Ch[(Ch.tag == tag) & Ch.before_first_close & (Ch.zone == "under") & (Ch.wstate == "wrist_in_view")].sort_values("chunk_id")
        if len(g):
            sel.append(g.iloc[[len(g) // 2]])
        g = Ch[(Ch.tag == tag) & Ch.before_first_close & (Ch.zone == "aligned")].sort_values("chunk_id")
        if len(g):
            sel.append(g.iloc[[0]])
    S = pd.concat(sel).reset_index(drop=True)
    S["run"] = [E.loc[t].run for t in S.tag]
    return S


def main():
    import cv2
    import torch
    from lerobot.policies.factory import make_pre_post_processors
    from lerobot.policies.pi05.modeling_pi05 import PI05Policy
    from lerobot.policies.utils import prepare_observation_for_inference
    from lerobot.utils.feature_utils import build_dataset_frame

    S = states()
    print(S[["tag", "chunk_id", "t_s", "zone", "wstate", "s0"]].to_string(), flush=True)
    policy = PI05Policy.from_pretrained(str(CKPT)).to("cuda").eval()
    policy.config.num_inference_steps = 5
    pre, post = make_pre_post_processors(policy.config, pretrained_path=str(CKPT), preprocessor_overrides={"device_processor": {"device": "cuda"}})
    feats = {"observation.state": {"dtype": "float32", "shape": (6,), "names": [f"{j}.pos" for j in J]},
             "observation.images.front": {"dtype": "video", "shape": (480, 640, 3), "names": None},
             "observation.images.wrist": {"dtype": "video", "shape": (480, 640, 3), "names": None}}
    N = 32
    bank = torch.randn((64, 50, 32), generator=torch.Generator(device="cpu").manual_seed(2026))[:N].cuda()
    rows = []
    for _, r in S.iterrows():
        run = ROLL / r.run
        m = next(json.loads(x) for x in (run / "diag/chunks.jsonl").read_text().splitlines() if json.loads(x)["chunk_id"] == int(r.chunk_id))
        imgs = {cam: cv2.cvtColor(cv2.imread(str(run / "diag/obs" / f"c{int(r.chunk_id):05d}_{cam}.png")), cv2.COLOR_BGR2RGB) for cam in ("front", "wrist")}
        for dlt in DELTAS:
            st = list(m["obs_state"])
            st[0] = st[0] + dlt
            obs = {f"{j}.pos": float(v) for j, v in zip(J, st)}
            obs.update(imgs)
            b = pre(dict(prepare_observation_for_inference(build_dataset_frame(feats, obs, prefix="observation"), torch.device("cuda"), TASK, "so_follower"), task=[TASK]))
            bb = {kk: (v.repeat(N, *([1] * (v.dim() - 1))) if torch.is_tensor(v) else ([TASK] * N if kk == "task" else v)) for kk, v in b.items()}
            with torch.no_grad():
                A = post(policy.predict_action_chunk(bb, noise=bank)).float().cpu().numpy()[:, :, 0]
            s_in = st[0]
            c30 = A[:, 29] - s_in
            ex = A[:, 29] - A[:, 9]
            mid = r.band_mid
            tdir_in = np.sign(mid - s_in)
            rows.append(dict(tag=r.tag, chunk_id=int(r.chunk_id), t_s=r.t_s, zone_real=r.zone, wstate=r.wstate, s0_real=r.s0, delta=dlt, s_in=s_in,
                             band_mid=mid, tdir_in=tdir_in, cum30_med=float(np.median(c30)), cum30_p10=float(np.percentile(c30, 10)), cum30_p90=float(np.percentile(c30, 90)),
                             exec_med=float(np.median(ex)), a29_med=float(np.median(A[:, 29])), a49_med=float(np.median(A[:, 49])),
                             frac_cum30_pos=float((c30 >= 2).mean()), frac_cum30_neg=float((c30 <= -2).mean()),
                             frac_toward_in=float((np.sign(c30) == tdir_in)[np.abs(c30) >= 2].sum() / N)))
            print(r.tag, int(r.chunk_id), dlt, round(rows[-1]["cum30_med"], 1), round(rows[-1]["a29_med"], 1), flush=True)
    pd.DataFrame(rows).to_csv(OUT / "tables/q05_sensitivity.csv", index=False)


if __name__ == "__main__":
    main()
