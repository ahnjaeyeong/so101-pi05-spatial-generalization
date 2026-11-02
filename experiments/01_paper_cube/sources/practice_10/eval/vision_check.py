"""pi05_2k 가 화면을 보고 움직이는지 오프라인 확인 (팔 연결 없음, 데이터셋 읽기만).

각 학습 에피소드에서 팔이 움직이기 시작하는 프레임을 고른다. 이때 팔 자세(state)는 판마다 거의 같아서,
큐브가 어디 있는지는 화면으로만 알 수 있다. 같은 노이즈로 chunk 를 뽑아 비교:
  own     : 자기 state + 자기 화면
  swap    : 자기 state + 다른 판(같은 순간) 화면  → 예측이 화면 쪽 판을 따라가면 화면을 쓰는 것
  gray    : 자기 state + 회색 화면
지표: chunk 끝(50번째) 예측값이 각 판의 실제 50프레임 뒤 action 과 얼마나 맞는지 (shoulder_pan 등).

실행: PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python vision_check.py
결과: vision_check.json
"""

import json
from pathlib import Path

import numpy as np
import torch

from lerobot.configs import PreTrainedConfig
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.policies import get_policy_class, make_pre_post_processors
from lerobot.policies.utils import prepare_observation_for_inference

S = Path.home() / "so101_runs/practice/practice_10"
CKPT = S / "train/pi05_2k/checkpoints/002000/pretrained_model"
OUT = S / "eval"
J = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
H = 49  # chunk 마지막 스텝

dev = torch.device("cuda")
cfg = PreTrainedConfig.from_pretrained(CKPT)
cfg.pretrained_path = CKPT
cfg.device = "cuda"
policy = get_policy_class(cfg.type).from_pretrained(CKPT, config=cfg).to(dev).eval()
pre, post = make_pre_post_processors(policy_cfg=cfg, pretrained_path=CKPT,
                                     preprocessor_overrides={"device_processor": {"device": "cuda"}})
ds = LeRobotDataset("oxr/so101_cubebox_practice10", root=S / "dataset", return_uint8=True)
cams = [k for k in ds.meta.features if k.startswith("observation.images.")]
task = "pick up the red cube and put it in the brown box"


def hwc(t):
    a = t.numpy()
    return np.ascontiguousarray(a.transpose(1, 2, 0) if a.shape[0] == 3 else a)


def infer(state, imgs):
    torch.manual_seed(0)  # 같은 노이즈 → 차이는 입력에서만
    obs = {"observation.state": state.astype(np.float32), **{c: imgs[c] for c in cams}}
    with torch.inference_mode():
        o = pre(prepare_observation_for_inference(obs, dev, task, "so101_follower"))
        a = policy.predict_action_chunk(o)[:, :50]
        return post(a).squeeze(0).float().cpu().numpy()


# 판마다 움직임 시작 프레임 (리더 action 속도가 처음 2°/프레임 넘는 곳의 5프레임 전)
onset = {}
for ep in range(ds.meta.total_episodes):
    a0, a1 = int(ds.meta.episodes[ep]["dataset_from_index"]), int(ds.meta.episodes[ep]["dataset_to_index"])
    act = np.stack([np.asarray(ds.hf_dataset[i]["action"], dtype=np.float32) for i in range(a0, a1)])
    st = np.stack([np.asarray(ds.hf_dataset[i]["observation.state"], dtype=np.float32) for i in range(a0, a1)])
    k = int(np.argmax(np.abs(np.diff(act[:, :5], axis=0)).max(1) > 2.0))
    f = max(k - 5, 0)
    item = ds[a0 + f]
    onset[ep] = {"frame": f, "state": st[f], "future": act[min(f + H, len(act) - 1)],
                 "imgs": {c: hwc(item[c]) for c in cams}}

eps = sorted(onset)
gray = {c: np.full_like(onset[eps[0]]["imgs"][c], 128) for c in cams}
own, grayp, swap = {}, {}, {}
for ep in eps:
    own[ep] = infer(onset[ep]["state"], onset[ep]["imgs"])[H]
    grayp[ep] = infer(onset[ep]["state"], gray)[H]
    for other in eps:
        if other != ep:
            swap[(ep, other)] = infer(onset[ep]["state"], onset[other]["imgs"])[H]

fut = np.stack([onset[e]["future"] for e in eps])
st0 = np.stack([onset[e]["state"] for e in eps])
own_a = np.stack([own[e] for e in eps])
gray_a = np.stack([grayp[e] for e in eps])

# swap 예측이 화면 쪽 판(other)의 실제값에 더 가까운지, state 쪽 판(ep)의 실제값에 더 가까운지
closer_to_image = {j: 0 for j in range(6)}
pairs = 0
for (ep, other), p in swap.items():
    pairs += 1
    for j in range(6):
        if abs(p[j] - onset[other]["future"][j]) < abs(p[j] - onset[ep]["future"][j]):
            closer_to_image[j] += 1


def corr(x, y):
    return float(np.corrcoef(x, y)[0, 1]) if np.std(x) > 1e-6 and np.std(y) > 1e-6 else float("nan")


res = {
    "onset_frames": {int(e): onset[e]["frame"] for e in eps},
    "state_spread_at_onset_deg": dict(zip(J, np.round(st0.std(0), 2).tolist())),
    "actual_future_spread_deg": dict(zip(J, np.round(fut.std(0), 2).tolist())),
    "own_pred_vs_actual_mae": dict(zip(J, np.round(np.abs(own_a - fut).mean(0), 2).tolist())),
    "own_pred_vs_actual_corr": dict(zip(J, [round(corr(own_a[:, j], fut[:, j]), 2) for j in range(6)])),
    "gray_pred_vs_actual_mae": dict(zip(J, np.round(np.abs(gray_a - fut).mean(0), 2).tolist())),
    "gray_vs_own_mae": dict(zip(J, np.round(np.abs(gray_a - own_a).mean(0), 2).tolist())),
    "swap_vs_own_mae": dict(zip(J, np.round(np.mean([np.abs(p - own[ep]) for (ep, _), p in swap.items()], 0), 2).tolist())),
    "swap_closer_to_image_episode_pct": {J[j]: round(100 * closer_to_image[j] / pairs, 1) for j in range(6)},
    "pairs": pairs,
    "horizon_frames": H + 1,
}
(OUT / "vision_check.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
print(json.dumps(res, indent=1, ensure_ascii=False))
