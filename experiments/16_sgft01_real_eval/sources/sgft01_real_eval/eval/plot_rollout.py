"""analyze_rollout.py 결과 그래프 (시스템 python3).
PYTHONDONTWRITEBYTECODE=1 python3 plot_rollout.py <run_dir> [...]   ("reference" = eval/reference_teleop)
"""

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

EVAL = Path(__file__).resolve().parent
for arg in sys.argv[1:]:
    d = EVAL / "reference_teleop" if arg == "reference" else Path(arg).resolve()
    z = np.load(d / "analysis.npz")
    res = json.loads((d / "analysis.json").read_text())
    names = res["joints"]
    for key in sorted({k.split("_")[0] for k in z.files}):
        a, s = z[f"{key}_action"], z[f"{key}_state"]
        m = res["episodes"][key[2:]]
        t = np.arange(len(a)) / 30
        fig, axes = plt.subplots(3, 2, figsize=(14, 10), sharex=True)
        for j, ax in enumerate(axes.T.flat):
            ax.plot(t, a[:, j], color="#d9480f", lw=1.0, label="action (command)")
            ax.plot(t, s[:, j], color="#222", lw=1.2, label="state (follower)")
            ax.set_title(f"{names[j]}  hf_rms a/s {m['action_hf_rms'][j]}/{m['state_hf_rms'][j]}  "
                         f"rev/s {m['action_reversals_per_s'][j]}  >8° {m['track_over8_pct'][j]}%", fontsize=9)
            ax.grid(alpha=0.3)
        for ax in axes[-1]:
            ax.set_xlabel("time (s)")
        axes[0, 0].legend(fontsize=8)
        fig.suptitle(f"{d.name} — episode {key[2:]}  (period {m['period']})")
        fig.tight_layout()
        fig.savefig(d / f"{key}_action_state.png", dpi=100)
        plt.close(fig)
    print("saved", d)
