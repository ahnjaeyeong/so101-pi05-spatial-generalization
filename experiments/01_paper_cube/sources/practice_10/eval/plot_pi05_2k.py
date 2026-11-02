"""offline_eval_pi05_2k.py 결과 그래프. 시스템 python3 (matplotlib) 으로 실행:
PYTHONDONTWRITEBYTECODE=1 python3 plot_pi05_2k.py
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = Path(__file__).resolve().parent
d = np.load(OUT / "pi05_2k_offline.npz")
s = json.loads((OUT / "pi05_2k_offline.json").read_text())
names = [n.replace(".pos", "") for n in d["joint_names"]]
chunk, fps = int(d["chunk"]), float(d["fps"])
eps = [int(e) for e in s["episodes"]]

for ep in eps:
    rec, pred, state = d[f"ep{ep}_rec"], d[f"ep{ep}_pred"], d[f"ep{ep}_state"]
    t = np.arange(len(rec)) / fps
    fig, axes = plt.subplots(3, 2, figsize=(14, 10), sharex=True)
    for j, ax in enumerate(axes.T.flat):
        ax.plot(t, rec[:, j], color="#222", lw=1.6, label="recorded action (leader)")
        ax.plot(t, pred[:, j], color="#d9480f", lw=1.2, label="policy action (open-loop chunks)")
        ax.plot(t, state[:, j], color="#868e96", lw=0.8, ls=":", label="recorded state (follower)")
        for c in range(0, len(rec), chunk):
            ax.axvline(c / fps, color="#4dabf7", lw=0.6, alpha=0.5)
        mae = s["episodes"][str(ep)]["mae_per_joint"][d["joint_names"][j]]
        ax.set_title(f"{names[j]}  MAE {mae:.2f}" + (" (0-100)" if names[j] == "gripper" else " deg"))
        ax.grid(alpha=0.3)
    for ax in axes[-1]:
        ax.set_xlabel("time (s)")
    axes[0, 0].legend(loc="best", fontsize=8)
    fig.suptitle(f"practice_10 pi05_2k — episode {ep}: policy vs recorded action "
                 f"(chunk {chunk} steps, blue lines = new chunk)")
    fig.tight_layout()
    fig.savefig(OUT / f"pi05_2k_ep{ep:03d}_actions.png", dpi=110)
    plt.close(fig)

fig, ax = plt.subplots(1, 2, figsize=(13, 4.5))
for ep in eps:
    h = d[f"ep{ep}_horizon_err"]
    ax[0].plot(np.nanmean(h[:, :, :5], axis=(0, 2)), label=f"ep {ep}")
    ax[1].plot(np.nanmean(h[:, :, 5], axis=0), label=f"ep {ep}")
ax[0].set_title("arm 5 joints: mean |pred - recorded| vs step in chunk (deg)")
ax[1].set_title("gripper: mean |pred - recorded| vs step in chunk (0-100)")
for a in ax:
    a.set_xlabel(f"step within chunk (1/{fps:.0f} s)")
    a.grid(alpha=0.3)
    a.legend()
fig.tight_layout()
fig.savefig(OUT / "pi05_2k_error_vs_horizon.png", dpi=110)
print("saved", sorted(p.name for p in OUT.glob("pi05_2k_*.png")))
