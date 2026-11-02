"""Extract observation.state / action per frame from reference and redbox datasets -> states.npz (run with so101-env)."""
import glob
from pathlib import Path
import numpy as np
import pandas as pd

REF = Path.home() / "so101_runs/reference/aswinkumar99_so101_pick_place"
OURS = Path.home() / "so101_runs/main"
SRC = {}
for t, tn in [(1, "task1-single-sponge-no-distractors"), (2, "task2-multiple-sponges-no-distractors"),
              (3, "task3-single-sponge-with-distractors")]:
    for k, kn in [("K", "fixed-locations"), ("R", "random-locations")]:
        SRC[f"ref_T{t}-{k}"] = REF / tn / kn
        SRC[f"our_T{t}-{k}"] = OURS / f"redbox_t{t}_{'known' if k == 'K' else 'random'}" / "dataset"

out = {}
for name, root in SRC.items():
    files = sorted(glob.glob(str(root / "data/*/*.parquet")))
    df = pd.concat(pd.read_parquet(f, columns=["episode_index", "frame_index", "observation.state", "action"]) for f in files)
    df = df.sort_values(["episode_index", "frame_index"])
    out[name + "/ep"] = df["episode_index"].to_numpy(np.int32)
    out[name + "/state"] = np.stack(df["observation.state"].to_numpy()).astype(np.float32)
    out[name + "/action"] = np.stack(df["action"].to_numpy()).astype(np.float32)
    print(name, len(df), df["episode_index"].nunique())
np.savez_compressed("states.npz", **out)
