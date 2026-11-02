"""rollout 녹화 영상 확인 (읽기만): 정책이 실제로 본 화면이 학습 때와 같은지, 프레임이 멈추지 않았는지.

실행: PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python camera_check.py <run_dir> [...]   ("reference" = 학습 데이터)
결과: <run_dir>/camera_check.json, cam_ep<N>_sheet.jpg (0.5초 간격 front·wrist 화면 + 관절 값)

- 색·밝기: 화면 전체 평균 R·G·B (학습 데이터와 비교)
- 같은 프레임: 바로 앞 프레임과 거의 같은 화면(160x120 회색, 평균 차이 < 0.5)인데 팔은 1°/프레임 넘게 움직이는 중
  → wrist 카메라는 팔과 같이 움직이므로 이 경우 카메라 프레임이 늦게 오거나 반복된 것
"""

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from lerobot.datasets.lerobot_dataset import LeRobotDataset

EVAL = Path(__file__).resolve().parent
SESSION = EVAL.parent
CAMS = ["observation.images.front", "observation.images.wrist"]
STEP = 15  # 0.5초


def to_hwc(t):
    a = t.numpy()
    return np.ascontiguousarray(a.transpose(1, 2, 0) if a.shape[0] == 3 else a)


def gray_small(img):
    return np.asarray(Image.fromarray(img).convert("L").resize((160, 120)), dtype=np.float32)


def check(arg):
    if arg == "reference":
        root, out, repo = SESSION / "dataset", EVAL / "reference_teleop", "oxr/so101_cubebox_practice10"
        episodes = [1, 4]
    else:
        out = Path(arg).resolve()
        root = out / "dataset"
        repo = json.loads((root / "meta/info.json").read_text()).get("repo_id", "oxr/rollout_x")
        episodes = None
    ds = LeRobotDataset(repo, root=root, return_uint8=True)
    eps = episodes if episodes is not None else list(range(ds.meta.total_episodes))
    res = {}
    for ep in eps:
        a0, a1 = int(ds.meta.episodes[ep]["dataset_from_index"]), int(ds.meta.episodes[ep]["dataset_to_index"])
        prev = {c: None for c in CAMS}
        means = {c: [] for c in CAMS}
        stale = {c: 0 for c in CAMS}
        moving = 0
        prev_state = None
        tiles = []
        for i in range(a0, a1):
            it = ds[i]
            state = it["observation.state"].numpy()
            mv = prev_state is not None and np.abs(state[:5] - prev_state[:5]).max() > 1.0
            moving += int(mv)
            imgs = {c: to_hwc(it[c]) for c in CAMS}
            for c in CAMS:
                g = gray_small(imgs[c])
                if mv and prev[c] is not None and np.abs(g - prev[c]).mean() < 0.5:
                    stale[c] += 1
                prev[c] = g
                if (i - a0) % 5 == 0:
                    means[c].append(imgs[c].reshape(-1, 3).mean(0))
            prev_state = state
            if (i - a0) % STEP == 0:
                row = Image.new("RGB", (320 * 2, 240 + 16), "white")
                for k, c in enumerate(CAMS):
                    row.paste(Image.fromarray(imgs[c]).resize((320, 240)), (320 * k, 16))
                d = ImageDraw.Draw(row)
                d.text((4, 2), f"t={(i - a0) / 30:5.1f}s  pan {state[0]:.0f} lift {state[1]:.0f} elbow {state[2]:.0f} "
                                f"wflex {state[3]:.0f} roll {state[4]:.0f} grip {state[5]:.0f}", fill="black")
                tiles.append(row)
        cols = 4
        rows = (len(tiles) + cols - 1) // cols
        sheet = Image.new("RGB", (640 * cols, 256 * rows), "white")
        for k, t in enumerate(tiles):
            sheet.paste(t, (640 * (k % cols), 256 * (k // cols)))
        sheet.save(out / f"cam_ep{ep}_sheet.jpg", quality=80)
        res[ep] = {
            "frames": a1 - a0,
            "moving_frames": moving,
            "stale_while_moving": stale,
            "mean_rgb": {c.split(".")[-1]: np.round(np.mean(means[c], 0), 1).tolist() for c in CAMS},
        }
        print(out.name, ep, res[ep])
    (out / "camera_check.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))


for a in sys.argv[1:]:
    check(a)
