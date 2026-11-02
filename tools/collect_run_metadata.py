#!/usr/bin/env python3
"""Collect reproducibility metadata for every training run and dataset.

READ-ONLY on the source side. Writes into this repository:
  configs/training/<run_id>/{train_config.json, policy_config.json, run_script.sh, time.txt}
  configs/training/RUNS.csv                 one row per run
  configs/checkpoints/CHECKPOINTS.csv       one row per saved checkpoint (path, bytes, sha256)
  configs/datasets/DATASETS.csv + <name>_info.json
  analysis/loss/<run_id>_loss.csv           loss / grad-norm / lr every log_freq steps (from training log)
  analysis/figures/loss_curves.png          (needs matplotlib; system python3)

Checkpoint weight hashes are read from configs/checkpoints/model_sha256.txt
(produced once with: find … -name model.safetensors | xargs sha256sum). Weights are NOT copied.
"""
import csv
import hashlib
import json
import os
import re
import shutil

RUNS = "/home/user/so101_runs"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# run_id: (output_dir, last checkpoint step dir, log file, run script, time file, first logged step offset)
TRAIN_RUNS = {
    "practice_10_pi05_2k": ("practice/practice_10/train/pi05_2k", "002000", "practice/practice_10/train/pi05_2k.log",
                            "practice/practice_10/train/run_pi05_2k.sh", "practice/practice_10/train/pi05_2k.time", 0),
    "practice_50_pi05_15k": ("practice/practice_50/train/pi05_15k", "015000", "practice/practice_50/train/pi05_15k.log",
                             "practice/practice_50/train/run_pi05_15k.sh", "practice/practice_50/train/pi05_15k.time", 0),
    "cubemark_pi05_15k": ("main/cubemark_v1/train/4_15000/pi05_15k", "015000", "main/cubemark_v1/train/4_15000/pi05_15k.log",
                          "main/cubemark_v1/train/4_15000/run_pi05_15k.sh", "main/cubemark_v1/train/4_15000/pi05_15k.time", 0),
    "cubemark_expert_bs8_3k": ("main/cubemark_v1/train/8_3000/pi05_expert_bs8_3k", "003000",
                               "main/cubemark_v1/train/8_3000/pi05_expert_bs8_3k.log",
                               "main/cubemark_v1/train/8_3000/run_pi05_expert_bs8_3k.sh",
                               "main/cubemark_v1/train/8_3000/pi05_expert_bs8_3k.time", 0),
    "redbox_expert_bs32_20k": ("main/redbox_all/train/32_20000/pi05_expert_bs32_20k", "020000",
                               "main/redbox_all/train/32_20000/pi05_expert_bs32_20k.log",
                               "main/redbox_all/train/32_20000/run_pi05_expert_bs32_20k.sh",
                               "main/redbox_all/train/32_20000/pi05_expert_bs32_20k.time", 0),
    "redbox_expert_bs32_resume30k": ("main/redbox_all/train/32_20000/pi05_expert_bs32_20k", "030000",
                                     "main/redbox_all/train/32_20000/pi05_expert_bs32_resume30k.log",
                                     "main/redbox_all/train/32_20000/run_pi05_expert_bs32_resume30k.sh",
                                     "main/redbox_all/train/32_20000/pi05_expert_bs32_resume30k.time", 20000),
    "d2_expert_bs32_20k": ("main_k8/d2/train/32_20000/pi05_expert_bs32_20k", "020000",
                           "main_k8/d2/train/32_20000/pi05_expert_bs32_20k.log",
                           "main_k8/d2/train/32_20000/run_pi05_expert_bs32_20k.sh",
                           "main_k8/d2/train/32_20000/pi05_expert_bs32_20k.time", 0),
    "d4_expert_bs32_20k_stopped10k": ("main_k8/d4/train/32_20000/pi05_expert_bs32_20k", "010000",
                                      "main_k8/d4/train/32_20000/pi05_expert_bs32_20k.log",
                                      "main_k8/d4/train/32_20000/run_pi05_expert_bs32_20k.sh",
                                      "main_k8/d4/train/32_20000/pi05_expert_bs32_20k.time", 0),
    **{f"sampling_{r}": (f"main_k8/d2/sampling_ablation/runs/{r}", "004000", f"main_k8/d2/sampling_ablation/runs/{r}.log",
                         f"main_k8/d2/sampling_ablation/runs/run_{r}.sh", f"main_k8/d2/sampling_ablation/runs/{r}.time", 0)
       for r in ("A0_s2001", "A1_s2001", "A2_s2001")},
}

DATASETS = {
    "practice_10": "practice/practice_10/dataset", "practice_50": "practice/practice_50/dataset",
    "cubemark_v1": "main/cubemark_v1/dataset",
    **{f"redbox_{t}_{k}": f"main/redbox_{t}_{k}/dataset" for t in ("t1", "t2", "t3") for k in ("known", "random")},
    "redbox_all": "main/redbox_all/dataset",
    **{f"k8_redbox_{t}_{k}": f"main_k8/redbox_{t}_{k}/dataset" for t in ("t1", "t3") for k in ("known", "random")},
    **{f"k8_redbox_{t}_{k}_release": f"main_k8/redbox_{t}_{k}/release" for t, k in (("t1", "known"), ("t1", "random"), ("t3", "random"))},
    "k8_d2": "main_k8/d2/dataset", "k8_d4": "main_k8/d4/dataset",
    **{f"practice_{s}": f"practice/{s}/dataset" for s in ("r1_trial", "r1_trial_old_20261102", "r1_try", "r1_try2")},
}

LINE = re.compile(r"INFO (\S+ \S+) \S+ step:(\S+) smpl:\S+ ep:\S+ epch:(\S+) loss:(\S+) grdn:(\S+) lr:(\S+)")


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def parse_loss(log, log_freq, offset):
    rows = []
    with open(log, errors="replace") as f:
        txt = f.read()
    for i, m in enumerate(LINE.finditer(txt)):
        rows.append({"step": offset + (i + 1) * log_freq, "time": m.group(1), "epoch": m.group(3),
                     "loss": m.group(4), "grad_norm": m.group(5), "lr": m.group(6)})
    return rows


def main():
    os.makedirs(f"{REPO}/configs/training", exist_ok=True)
    os.makedirs(f"{REPO}/configs/checkpoints", exist_ok=True)
    os.makedirs(f"{REPO}/configs/datasets", exist_ok=True)
    os.makedirs(f"{REPO}/analysis/loss", exist_ok=True)
    os.makedirs(f"{REPO}/analysis/figures", exist_ok=True)

    hashes = {}
    hfile = f"{REPO}/configs/checkpoints/model_sha256.txt"
    if os.path.exists(hfile):
        for ln in open(hfile):
            h, p = ln.split(None, 1)
            hashes[p.strip()] = h

    run_rows, ck_rows, curves = [], [], {}
    for rid, (out, last, log, script, tfile, offset) in TRAIN_RUNS.items():
        d = f"{REPO}/configs/training/{rid}"
        os.makedirs(d, exist_ok=True)
        pm = f"{RUNS}/{out}/checkpoints/{last}/pretrained_model"
        tc = json.load(open(f"{pm}/train_config.json"))
        shutil.copy2(f"{pm}/train_config.json", f"{d}/train_config.json")
        shutil.copy2(f"{pm}/config.json", f"{d}/policy_config.json")
        for src, name in ((script, "run_script.sh"), (tfile, "time.txt")):
            if os.path.exists(f"{RUNS}/{src}"):
                shutil.copy2(f"{RUNS}/{src}", f"{d}/{name}")
        tp = f"{RUNS}/{out}/training_params.md"
        if os.path.exists(tp) and rid != "redbox_expert_bs32_resume30k":
            shutil.copy2(tp, f"{d}/training_params.md")
        p, o, s = tc.get("policy", {}), tc.get("optimizer") or {}, tc.get("scheduler") or {}
        loss = parse_loss(f"{RUNS}/{log}", tc.get("log_freq", 50), offset) if os.path.exists(f"{RUNS}/{log}") else []
        if loss:
            with open(f"{REPO}/analysis/loss/{rid}_loss.csv", "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(loss[0].keys()))
                w.writeheader()
                w.writerows(loss)
            curves[rid] = loss
        times = open(f"{RUNS}/{tfile}").read().split("\n") if os.path.exists(f"{RUNS}/{tfile}") else []
        run_rows.append({
            "run_id": rid, "output_dir": f"{RUNS}/{out}", "dataset_repo_id": tc["dataset"]["repo_id"],
            "dataset_root": tc["dataset"]["root"], "pretrained_path": p.get("pretrained_path"),
            "resume": tc.get("resume"), "freeze_vision_encoder": p.get("freeze_vision_encoder"),
            "train_expert_only": p.get("train_expert_only"), "batch_size": tc.get("batch_size"),
            "steps_config": tc.get("steps"), "lr_peak": s.get("peak_lr") or o.get("lr"), "lr_end": s.get("decay_lr"),
            "warmup_config": s.get("num_warmup_steps"), "decay_config": s.get("num_decay_steps"),
            "seed": tc.get("seed"), "dtype": p.get("dtype"), "chunk_size": p.get("chunk_size"),
            "num_inference_steps_cfg": p.get("num_inference_steps"),
            "loss_first": loss[0]["loss"] if loss else "", "loss_last": loss[-1]["loss"] if loss else "",
            "loss_min": min((float(r["loss"]) for r in loss), default=""),
            "last_logged_step": loss[-1]["step"] if loss else "",
            "time_start_end": " | ".join(t for t in times if t),
            "train_config_sha256": sha(f"{pm}/train_config.json"),
        })
        ck_dir = f"{RUNS}/{out}/checkpoints"
        for step in sorted(x for x in os.listdir(ck_dir) if x.isdigit()):
            if rid == "redbox_expert_bs32_resume30k" and int(step) <= 20000:
                continue
            if rid == "redbox_expert_bs32_20k" and int(step) > 20000:
                continue
            mp = f"{ck_dir}/{step}/pretrained_model/model.safetensors"
            ck_rows.append({"run_id": rid, "step": step, "model_path": mp,
                            "model_bytes": os.path.getsize(mp) if os.path.exists(mp) else "",
                            "model_sha256": hashes.get(mp, "NOT_HASHED"),
                            "train_config_sha256": sha(f"{ck_dir}/{step}/pretrained_model/train_config.json")})

    with open(f"{REPO}/configs/training/RUNS.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(run_rows[0].keys()))
        w.writeheader()
        w.writerows(run_rows)
    with open(f"{REPO}/configs/checkpoints/CHECKPOINTS.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(ck_rows[0].keys()))
        w.writeheader()
        w.writerows(ck_rows)

    ds_rows = []
    for name, rel in DATASETS.items():
        info = f"{RUNS}/{rel}/meta/info.json"
        if not os.path.exists(info):
            ds_rows.append({"dataset": name, "path": f"{RUNS}/{rel}", "status": "MISSING"})
            continue
        j = json.load(open(info))
        shutil.copy2(info, f"{REPO}/configs/datasets/{name}_info.json")
        tasks = ""
        ds_rows.append({"dataset": name, "path": f"{RUNS}/{rel}", "status": "OK",
                        "codebase_version": j.get("codebase_version"), "robot_type": j.get("robot_type"),
                        "total_episodes": j.get("total_episodes"), "total_frames": j.get("total_frames"),
                        "total_tasks": j.get("total_tasks"), "fps": j.get("fps"),
                        "cameras": ";".join(k for k in j.get("features", {}) if k.startswith("observation.images")),
                        "info_json_sha256": sha(info)})
    keys = sorted({k for r in ds_rows for k in r}, key=lambda k: list(ds_rows[0]).index(k) if k in ds_rows[0] else 99)
    with open(f"{REPO}/configs/datasets/DATASETS.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(ds_rows)

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(10, 5.5))
        for rid, rows in curves.items():
            ax.plot([r["step"] for r in rows], [float(r["loss"]) for r in rows], label=rid, lw=1)
        ax.set_yscale("log")
        ax.set_xlabel("step")
        ax.set_ylabel("train loss (log)")
        ax.set_title("Training loss per run (from training logs; train loss only, no validation)")
        ax.legend(fontsize=7, ncol=2)
        ax.grid(alpha=.3)
        fig.tight_layout()
        fig.savefig(f"{REPO}/analysis/figures/loss_curves.png", dpi=110)
    except ImportError:
        print("matplotlib not available: skipped figure")
    print(f"runs {len(run_rows)}, checkpoints {len(ck_rows)}, datasets {len(ds_rows)}")


if __name__ == "__main__":
    main()
