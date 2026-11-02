"""2차 실험 그림 (시스템 python3). 입력: exp_summary.json, exp3/merge_compare.csv, exp3/ticks.csv, exp2/wrist_gain_rollmodel.csv
출력: fig7_ckpt.png, fig8_phase_camera.png, fig9_ep1_drift.png
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

H = Path(__file__).resolve().parent


def main():
    S = json.load(open(H / "exp_summary.json"))
    e1 = S["exp1"]
    steps = sorted(e1)
    x = [int(s) // 1000 for s in steps]
    fig, axs = plt.subplots(1, 3, figsize=(16, 4.5))
    for key, lab in (("grid_raw_aK", "grid K pull (raw)"), ("grid_cal_aK", "grid K pull (calibrated)"),
                     ("trainR_cal_aK", "train Random K pull (calibrated)"), ("grid_raw_cC", "grid centre pull (raw)"),
                     ("grid_cal_cC", "grid centre pull (calibrated)")):
        est = [e1[s][key]["est"] for s in steps]
        lo = [e1[s][key]["lo"] for s in steps]
        hi = [e1[s][key]["hi"] for s in steps]
        axs[0].errorbar(x, est, yerr=[np.subtract(est, lo), np.subtract(hi, est)], marker="o", capsize=3, label=lab)
    axs[0].axhline(0, c="k", lw=0.6)
    axs[0].set_xlabel("checkpoint (k steps)")
    axs[0].set_ylabel("pull coefficient (95% CI)")
    axs[0].legend(fontsize=7)
    axs[0].set_title("pull toward nearest K / centre")
    for key, lab in (("start_abs_err_med_R", "start |err| R (raw)"), ("start_abs_err_med_K", "start |err| K (raw)"),
                     ("grid_abs_err_cal_med", "grid |err| ≤3 cm (calibrated)"), ("pre_pan_abs_err_med_R", "pregrasp |err| R"),
                     ("pre_pan_abs_err_med_K", "pregrasp |err| K")):
        axs[1].plot(x, [e1[s][key] for s in steps], marker="o", label=lab)
    axs[1].set_xlabel("checkpoint (k steps)")
    axs[1].set_ylabel("median |pan error| (°)")
    axs[1].legend(fontsize=7)
    for b in ("0_2", "2_4", "4_6"):
        axs[2].plot(x, [e1[s][f"grid_abs_err_cal_med_{b}cm"][0] for s in steps], marker="o", label=f"{b.replace('_', '–')} cm from train cube")
    axs[2].set_xlabel("checkpoint (k steps)")
    axs[2].set_ylabel("grid median |pan error| calibrated (°)")
    axs[2].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(H / "fig7_ckpt.png", dpi=110)

    e2 = S["exp2"]
    G = pd.read_csv(H / "exp2/wrist_gain_rollmodel.csv")
    fig, ax = plt.subplots(figsize=(9, 4.5))
    labels = ["start\nfront", "mid\nfront", "pre\nfront", "start\nwrist*", "mid\nwrist*", "pre\nwrist*", "pre wrist\nlateral G_tt", "pre wrist\nradial G_rr"]
    vals = [e2["start"]["front_pan_gain_med"], e2["mid"]["front_pan_gain_med"], e2["pre"]["front_pan_gain_med"],
            e2["start"]["wrist_pan_grad_norm_over_ideal_med"], e2["mid"]["wrist_pan_grad_norm_over_ideal_med"],
            e2["pre"]["wrist_pan_grad_norm_over_ideal_med"], G.G_tt.median(), G.G_rr.median()]
    ax.bar(range(len(vals)), vals, color=["C0"] * 3 + ["C1"] * 3 + ["C3"] * 2)
    ax.axhline(1, c="k", ls="--", lw=0.8)
    ax.set_xticks(range(len(vals)))
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("response / ideal (median)")
    ax.set_title("cube-position sensitivity by phase × camera (d2 20k, T1 128 eps)\n*wrist pan: |∇pan| over ideal, direction-agnostic")
    fig.tight_layout()
    fig.savefig(H / "fig8_phase_camera.png", dpi=110)

    M = pd.read_csv(H / "exp3/merge_compare.csv")
    Tk = pd.read_csv(H / "exp3/ticks.csv")
    m5 = M[M.steps == 5]
    fig, axs = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
    ax = axs[0]
    ax.plot(Tk.t, Tk.raw_shoulder_pan, lw=0.8, label="raw (queue)")
    ax.plot(Tk.t, Tk.out_shoulder_pan, lw=0.8, label="out (arm_filter)")
    ax.plot(Tk.t, Tk.state_shoulder_pan, lw=0.8, label="state")
    ax.plot(m5.t, m5.model_exec_mean, "k.", ms=5, label="offline replan, executed part")
    ax.plot(m5.t, m5.model_end, "r^", ms=4, label="offline replan, chunk end (idx 49)")
    ax.axhline(17.1, c="gold", lw=2, label="cube expected pan")
    ax.axhline(31.4, c="gray", ls=":", label="K3 pan")
    ax.set_ylabel("pan °")
    ax.legend(fontsize=7, ncol=2)
    ax.set_title("try3_filt ep1: pan drift decomposition")
    ax = axs[1]
    ax.plot(m5.t, m5.raw_exec_mean - m5.model_exec_mean, "k.-", lw=0.6, label="raw − offline model (RTC/queue)")
    ax.plot(m5.t, m5.out_exec_mean - m5.raw_exec_mean, "b.-", lw=0.6, label="out − raw (arm_filter)")
    ax.plot(m5.t, m5.sent_exec_mean - m5.out_exec_mean, "g.-", lw=0.6, label="sent − out (clamp)")
    ax.plot(m5.t, m5.model_end - m5.state_pan_obs, "r.-", lw=0.6, label="model chunk end − state at obs")
    ax.axhline(0, c="k", lw=0.5)
    ax.set_xlabel("s")
    ax.set_ylabel("°")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(H / "fig9_ep1_drift.png", dpi=110)
    print("figures written")


if __name__ == "__main__":
    main()
