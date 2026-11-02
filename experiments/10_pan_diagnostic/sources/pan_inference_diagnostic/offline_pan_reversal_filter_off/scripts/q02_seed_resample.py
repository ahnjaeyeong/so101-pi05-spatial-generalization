"""q02 저장 관측 상태별 noise seed 반복 추론: U (RTC prefix 없음) vs G (기록 prefix · inference_delay, guided EXP) (GPU, 오프라인). 로봇 연결 없음.

상태 = 기록된 chunk 의 추론 입력 (diag/obs PNG front · wrist + obs_state). 정책 d2 020000, num_inference_steps 5,
RTC guided EXP, max_guidance_weight 10, execution_horizon 20 (실물 manifest 와 같음).
noise bank: torch.randn((N, 50, 32), seed 2026) — 모든 상태 · U/G 에 같은 bank (짝지은 비교).
  U = predict_action_chunk(noise) — prefix 없음. 실물에서 판 첫 chunk 와 같은 조건, 이후 chunk 에는 실물에 없던 조건 [재구성 · 반사실].
  G = predict_action_chunk(noise, inference_delay = 기록값, prev_chunk_left_over = 기록 prefix) [재구성].
  첫 chunk (prefix 없음) 는 G = U 이므로 U 만 계산.
재현 확인: 기록 noise 로 G 를 다시 계산하면 기록 chunk (processed) 와 같아야 한다 (replay_g_maxabs),
           기록 noise 로 U = diag/replay rtc_off (replay_u_maxabs).
상태 선택 (q01b_chunks.csv, chunk 관측 시각의 zone · 손목 상태):
  A0 · B1: 판 전체 chunk 모두 (dense)
  나머지 18 판: 범주마다 판당 최대 3 개 (시간 고르게):
    S1 approach_moving  : zone under, 첫 닫힘 전, 직전 0.5 s 목표 쪽 이동 ≥ 2°
    S2 approach_static  : zone under, 첫 닫힘 전, 직전 0.5 s |이동| < 2°
    S3 near_aligned     : zone aligned, 첫 닫힘 전
    S6 moving_away      : zone under/over, 직전 0.5 s 목표 반대쪽 이동 ≥ 2°
    S7 post_close_over  : 첫 닫힘 뒤 zone over
출력: tables/q02_states.csv (상태 정보 + 재현 차), tables/q02_seed_pan.npz (상태별 U/G pan (N, 50)), logs/q02.log
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python q02_seed_resample.py [--n 64] [--limit K]
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

D2 = Path.home() / "so101_runs/main_k8/d2"
OUT = D2 / "pan_inference_diagnostic/offline_pan_reversal_filter_off"
ROLL = D2 / "eval/rollouts"
CKPT = D2 / "train/32_20000/pi05_expert_bs32_20k/checkpoints/020000/pretrained_model"
TASK = "pick up the red cube and put it in the brown box"
J = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]


def pick(g, k=3):
    if len(g) <= k:
        return g
    idx = np.linspace(0, len(g) - 1, k).round().astype(int)
    return g.iloc[idx]


def select():
    Ch = pd.read_csv(OUT / "tables/q01b_chunks.csv")
    E = pd.read_csv(OUT / "tables/q01b_episodes.csv").set_index("tag")
    Ch["run"] = [E.loc[t].run for t in Ch.tag]
    sel = []
    dense = Ch[Ch.tag.isin(["A0", "B1"])].copy()
    dense["category"] = "dense_A0B1"
    sel.append(dense)
    rest = Ch[~Ch.tag.isin(["A0", "B1"])]
    pm = rest.prior_move_0p5s * rest.tdir
    cats = {"S1_approach_moving": (rest.zone == "under") & rest.before_first_close & (pm >= 2),
            "S2_approach_static": (rest.zone == "under") & rest.before_first_close & (rest.prior_move_0p5s.abs() < 2),
            "S3_near_aligned": (rest.zone == "aligned") & rest.before_first_close,
            "S6_moving_away": rest.zone.isin(["under", "over"]) & (pm <= -2),
            "S7_post_close_over": (rest.zone == "over") & ~rest.before_first_close}
    for c, m in cats.items():
        g = rest[m]
        for tag, gg in g.groupby("tag"):
            x = pick(gg.sort_values("chunk_id")).copy()
            x["category"] = c
            sel.append(x)
    S = pd.concat(sel).drop_duplicates(subset=["tag", "chunk_id"]).reset_index(drop=True)
    return S


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=64)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    import cv2
    import torch
    from lerobot.configs import RTCAttentionSchedule
    from lerobot.policies.factory import make_pre_post_processors
    from lerobot.policies.pi05.modeling_pi05 import PI05Policy
    from lerobot.policies.rtc.configuration_rtc import RTCConfig
    from lerobot.policies.utils import prepare_observation_for_inference
    from lerobot.utils.feature_utils import build_dataset_frame

    S = select()
    if a.limit:
        S = S.head(a.limit)
    print("states", len(S), S.category.value_counts().to_dict(), flush=True)
    policy = PI05Policy.from_pretrained(str(CKPT)).to("cuda").eval()
    policy.config.num_inference_steps = 5
    policy.config.rtc_config = RTCConfig(enabled=True, mode="guided", prefix_attention_schedule=RTCAttentionSchedule.EXP,
                                         max_guidance_weight=10.0, execution_horizon=20)
    policy.init_rtc_processor()
    pre, post = make_pre_post_processors(policy.config, pretrained_path=str(CKPT), preprocessor_overrides={"device_processor": {"device": "cuda"}})
    feats = {"observation.state": {"dtype": "float32", "shape": (6,), "names": [f"{j}.pos" for j in J]},
             "observation.images.front": {"dtype": "video", "shape": (480, 640, 3), "names": None},
             "observation.images.wrist": {"dtype": "video", "shape": (480, 640, 3), "names": None}}
    N = a.n
    bank = torch.randn((N, 50, 32), generator=torch.Generator(device="cpu").manual_seed(2026)).cuda()
    store, rows = {}, []
    metas = {}
    t0 = time.time()
    for k, r in S.iterrows():
        run = ROLL / r.run
        if r.run not in metas:
            metas[r.run] = {json.loads(x)["chunk_id"]: json.loads(x) for x in (run / "diag/chunks.jsonl").read_text().splitlines()}
        m = metas[r.run][int(r.chunk_id)]
        cid = int(r.chunk_id)
        z = np.load(run / "diag/chunks" / f"c{cid:05d}.npz")
        RZ = np.load(run / "diag/replay/replay.npz")
        obs = {f"{j}.pos": float(v) for j, v in zip(J, m["obs_state"])}
        for cam in ("front", "wrist"):
            obs[cam] = cv2.cvtColor(cv2.imread(str(run / "diag/obs" / f"c{cid:05d}_{cam}.png")), cv2.COLOR_BGR2RGB)
        b = pre(dict(prepare_observation_for_inference(build_dataset_frame(feats, obs, prefix="observation"), torch.device("cuda"), TASK, "so_follower"),
                     task=[TASK]))
        bb = {kk: (v.repeat(N, *([1] * (v.dim() - 1))) if torch.is_tensor(v) else ([TASK] * N if kk == "task" else v)) for kk, v in b.items()}
        has_p = "prefix" in z.files
        ln = torch.from_numpy(z["noise"]).cuda()[None].float()
        with torch.no_grad():
            U1 = post(policy.predict_action_chunk(b, noise=ln)).squeeze(0).float().cpu().numpy()
            U = post(policy.predict_action_chunk(bb, noise=bank)).float().cpu().numpy()
            if has_p:
                pf = torch.from_numpy(z["prefix"]).cuda()
                G1 = post(policy.predict_action_chunk(b, noise=ln, inference_delay=m.get("inference_delay"), prev_chunk_left_over=pf)).squeeze(0).float().cpu().numpy()
                pfN = pf[None].repeat(N, 1, 1) if pf.dim() == 2 else pf.repeat(N, 1, 1)
                G = post(policy.predict_action_chunk(bb, noise=bank, inference_delay=m.get("inference_delay"), prev_chunk_left_over=pfN)).float().cpu().numpy()
            else:
                G1, G = U1, U
        key = f"{r.tag}_c{cid:05d}"
        store[f"U_{key}"] = U[:, :, 0].astype(np.float32)
        store[f"G_{key}"] = G[:, :, 0].astype(np.float32)
        store[f"Ufull_{key}"] = U.astype(np.float16)
        store[f"Gfull_{key}"] = G.astype(np.float16)
        off = RZ[f"rtc_off_c{cid:05d}"] if f"rtc_off_c{cid:05d}" in RZ.files else None
        row = r.to_dict()
        row.update(key=key, replay_g_maxabs=float(np.abs(G1 - z["processed"]).max()),
                   replay_u_maxabs=float(np.abs(U1 - off).max()) if off is not None else np.nan, prefix_shape=str(z["prefix"].shape) if has_p else "")
        rows.append(row)
        if k % 10 == 0:
            print(k, key, r.category, r.zone, "repG", round(row["replay_g_maxabs"], 4), "repU", round(row["replay_u_maxabs"], 4),
                  f"{time.time() - t0:.0f}s", flush=True)
    pd.DataFrame(rows).to_csv(OUT / "tables/q02_states.csv", index=False)
    np.savez_compressed(OUT / "tables/q02_seed_pan.npz", **store)
    print("done", len(rows), f"{time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
