#!/usr/bin/env python3
"""Copy small research records (md/json/csv/yaml/py/png …) from the original
experiment folders into this repository, and write a provenance manifest.

READ-ONLY on the source side: it only reads files under SRC_ROOTS and writes
inside this repository. It never touches datasets, checkpoints, videos or
large binary files (see EXCLUDE_* and size limits below).

Usage:
    python3 tools/sync_sources.py --dry-run      # list what would be copied
    python3 tools/sync_sources.py                # copy + write SOURCES_MANIFEST.csv

Re-running is safe: files are overwritten with the current source content and
the manifest is regenerated. Add new mappings to MAPPINGS when a new
experiment folder appears.
"""
import argparse
import csv
import hashlib
import os
import shutil
import sys

HOME = "/home/user"
RUNS = f"{HOME}/so101_runs"
BOXPICK = f"{HOME}/so101_boxpick"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEXT_EXT = {".md", ".json", ".csv", ".yaml", ".yml", ".txt", ".py", ".sh", ".log", ".jsonl", ".time"}
IMG_EXT = {".png", ".svg", ".jpg", ".jpeg", ".pdf"}
MAX_TEXT = 3_000_000          # bytes
MAX_LOG = 300_000             # .log / .jsonl files
MAX_IMG = 1_500_000

EXCLUDE_DIRS = {
    "dataset", "checkpoints", "review_videos", "setup_photos", "frames", "frames_train",
    "diag", "obs", "chunks", "__pycache__", "release", "f1_features", "f1_quality_features",
    "harness", "trials", "runs_lat1.0", "runs_lat1.55", "runs_spike", ".cache", "_deleted",
    "start_images", "smoke", "g1", "g1c", "g2", "replay", "preview", "ctrl", "backup",
    "dataset_empty_20261015_1449", "dataset_empty_20261023_1333", "plan_preview", "live",
    "weights", "_smoke", "f1_results_raw",
}
EXCLUDE_PREFIX = ("tmp", "runs_wide", "dataset_empty")
EXCLUDE_NAMES = {"console.log", "debug.log", "viewer.log"}
EXCLUDE_EXT = {".npz", ".npy", ".parquet", ".mp4", ".safetensors", ".pt", ".bin", ".gz", ".zip", ".pyc", ".bak"}

# (source path, destination inside repo). Source may be a file or a directory.
MAPPINGS = [
    # ---- 01 paper cube (practice_10, practice_50, E0_J_0) ----
    (f"{RUNS}/docs/practice_10_pi05_2k.md", "experiments/01_paper_cube/sources/docs/practice_10_pi05_2k.md"),
    (f"{RUNS}/practice/practice_10/notes.md", "experiments/01_paper_cube/sources/practice_10/notes.md"),
    (f"{RUNS}/practice/practice_10/qa_report.md", "experiments/01_paper_cube/sources/practice_10/qa_report.md"),
    (f"{RUNS}/practice/practice_10/eval", "experiments/01_paper_cube/sources/practice_10/eval"),
    (f"{RUNS}/practice/practice_10/train", "experiments/01_paper_cube/sources/practice_10/train"),
    (f"{RUNS}/practice/practice_50/notes.md", "experiments/01_paper_cube/sources/practice_50/notes.md"),
    (f"{RUNS}/practice/practice_50/qa_report.md", "experiments/01_paper_cube/sources/practice_50/qa_report.md"),
    (f"{RUNS}/practice/practice_50/eval", "experiments/01_paper_cube/sources/practice_50/eval"),
    (f"{RUNS}/practice/practice_50/train", "experiments/01_paper_cube/sources/practice_50/train"),
    (f"{RUNS}/e0_j0/design.md", "experiments/01_paper_cube/sources/e0_j0/design.md"),
    (f"{RUNS}/e0_j0/experiment_log.md", "experiments/01_paper_cube/sources/e0_j0/experiment_log.md"),
    (f"{RUNS}/e0_j0/report_for_dr_lee.md", "experiments/01_paper_cube/sources/e0_j0/report_for_dr_lee.md"),
    (f"{RUNS}/e0_j0/runs/index.md", "experiments/01_paper_cube/sources/e0_j0/runs/index.md"),
    (f"{RUNS}/camera_settings.md", "configs/camera/camera_settings.md"),
    (f"{RUNS}/camera_settings/cam_wb_compare.jpg", "configs/camera/camera_settings/cam_wb_compare.jpg"),
    # ---- 02 cubemark / first expert-only ----
    (f"{RUNS}/main/cubemark_v1/notes.md", "experiments/02_cubemark_expert_only/sources/cubemark_v1/notes.md"),
    (f"{RUNS}/main/cubemark_v1/qa_report.md", "experiments/02_cubemark_expert_only/sources/cubemark_v1/qa_report.md"),
    (f"{RUNS}/main/cubemark_v1/eval", "experiments/02_cubemark_expert_only/sources/cubemark_v1/eval"),
    (f"{RUNS}/main/cubemark_v1/train", "experiments/02_cubemark_expert_only/sources/cubemark_v1/train"),
    # ---- 03 redbox 384 dataset + 20k training ----
    *[(f"{RUNS}/main/redbox_{t}_{k}/{f}", f"experiments/03_redbox_384_20k/sources/sessions/redbox_{t}_{k}/{f}")
      for t in ("t1", "t2", "t3") for k in ("known", "random")
      for f in ("notes.md", "qa_report.md", "layout.csv", "layout_meta.json", "layout_sheet.md",
                "positions_manual.csv", "qa/positions.csv", "qa/heatmap.png")],
    (f"{RUNS}/main/redbox_수집명령.md", "experiments/03_redbox_384_20k/sources/redbox_수집명령.md"),
    (f"{RUNS}/main/README.md", "experiments/03_redbox_384_20k/sources/main_README.md"),
    (f"{RUNS}/main/redbox_all/dataset/meta/info.json", "experiments/03_redbox_384_20k/sources/redbox_all_meta/info.json"),
    (f"{RUNS}/main/redbox_all/train", "experiments/03_redbox_384_20k/sources/train"),
    (f"{RUNS}/main/redbox_all/eval/train_roll_census", "experiments/03_redbox_384_20k/sources/train_roll_census"),
    (f"{RUNS}/reference/analysis_20261019", "experiments/03_redbox_384_20k/sources/reference_analysis_20261019"),
    (f"{RUNS}/reference/range_compare_20261021", "experiments/03_redbox_384_20k/sources/reference_range_compare_20261021"),
    # ---- 04 RTC / filter / spatial eval (20k) ----
    (f"{RUNS}/redbox_all/eval", "experiments/04_rtc_filter_space_eval/sources/offline_redbox_all_eval"),
    (f"{RUNS}/main/redbox_all/eval/rollouts", "experiments/04_rtc_filter_space_eval/sources/rollouts"),
    (f"{RUNS}/main/redbox_all/eval/eval_ab", "experiments/04_rtc_filter_space_eval/sources/eval_ab"),
    (f"{RUNS}/main/redbox_all/eval/eval_space/20261020_space", "experiments/04_rtc_filter_space_eval/sources/eval_space_20k"),
    (f"{RUNS}/main/redbox_all/eval/pregrasp_angles", "experiments/04_rtc_filter_space_eval/sources/pregrasp_angles"),
    (f"{RUNS}/main/redbox_all/eval/pregrasp_review", "experiments/04_rtc_filter_space_eval/sources/pregrasp_review"),
    (f"{RUNS}/main/redbox_all/eval/run_rollout.sh", "experiments/04_rtc_filter_space_eval/sources/eval_tools/run_rollout.sh"),
    (f"{RUNS}/main/redbox_all/eval/rollout_logged.py", "experiments/04_rtc_filter_space_eval/sources/eval_tools/rollout_logged.py"),
    (f"{RUNS}/main/redbox_all/eval/arm_filter.py", "experiments/04_rtc_filter_space_eval/sources/eval_tools/arm_filter.py"),
    # ---- 05 redbox 30k ----
    (f"{RUNS}/main/redbox_all/eval/eval_space/20261022_space_30k", "experiments/05_redbox_30k/sources/eval_space_30k"),
    # ---- 06 K8 relayout + d2 256 (+ d4) ----
    (f"{RUNS}/main_k8/README.md", "experiments/06_d2_256/sources/main_k8_README.md"),
    (f"{RUNS}/main_k8/redbox_수집명령.md", "experiments/06_d2_256/sources/redbox_수집명령.md"),
    *[(f"{RUNS}/main_k8/redbox_{t}_{k}/{f}", f"experiments/06_d2_256/sources/sessions/redbox_{t}_{k}/{f}")
      for t in ("t1", "t2", "t3") for k in ("known", "random")
      for f in ("notes.md", "qa_report.md", "layout.csv", "layout_meta.json", "layout_sheet.md",
                "qa/positions.csv", "qa/heatmap.png", "qa/roll_alignment.png")],
    *[(f"{RUNS}/main_k8/{d}/description.md", f"experiments/06_d2_256/sources/{d}/description.md")
      for d in ("d1", "d2", "d3", "d4")],
    (f"{RUNS}/main_k8/d2/dataset/meta/info.json", "experiments/06_d2_256/sources/d2/dataset_meta/info.json"),
    (f"{RUNS}/main_k8/d4/dataset/meta/info.json", "experiments/06_d2_256/sources/d4/dataset_meta/info.json"),
    (f"{RUNS}/main_k8/d2/train", "experiments/06_d2_256/sources/d2/train"),
    (f"{RUNS}/main_k8/d4/train", "experiments/06_d2_256/sources/d4/train"),
    (f"{RUNS}/main_k8/d2/eval", "experiments/06_d2_256/sources/d2/eval"),
    (f"{RUNS}/main_k8/d2/diag_grasp_bias", "experiments/06_d2_256/sources/d2/diag_grasp_bias"),
    (f"{RUNS}/main_k8/d2/grasp_pose", "experiments/06_d2_256/sources/d2/grasp_pose"),
    (f"{RUNS}/reference/aswin_task2_compare/비교_리포트.md", "experiments/06_d2_256/sources/reference_aswin_task2_compare/비교_리포트.md"),
    # ---- 07 vision probe ----
    (f"{RUNS}/main_k8/d2/vision_probe", "experiments/07_vision_probe/sources/vision_probe"),
    # ---- 08 action bottleneck ----
    (f"{RUNS}/main_k8/d2/action_bottleneck", "experiments/08_action_bottleneck/sources/action_bottleneck"),
    # ---- 09 sampling ablation + data coverage audit ----
    (f"{RUNS}/main_k8/d2/sampling_ablation", "experiments/09_sampling_ablation/sources/sampling_ablation"),
    (f"{RUNS}/main_k8/d2/data_coverage_audit", "experiments/09_sampling_ablation/sources/data_coverage_audit"),
    # ---- 10 pan diagnostic (incl. offline pan reversal) ----
    (f"{RUNS}/main_k8/d2/pan_inference_diagnostic", "experiments/10_pan_diagnostic/sources/pan_inference_diagnostic"),
    # ---- 11 R1/R2 recovery demos ----
    (f"{RUNS}/main_k8/r1_r2_collection", "experiments/11_r1_r2_recovery/sources/r1_r2_collection"),
    *[(f"{RUNS}/{s}", f"experiments/11_r1_r2_recovery/sources/sessions/{os.path.basename(s)}")
      for s in ("main_k8/r1_realign_pilot", "main_k8/r2_pregrasp_pilot", "practice/r1_trial",
                "practice/r1_trial_old_20261102", "practice/r1_try", "practice/r1_try2",
                "practice/r1_try3", "practice/r2_trial")],
    *[(f"{RUNS}/{s}/dataset/meta/info.json", f"experiments/11_r1_r2_recovery/sources/sessions/{os.path.basename(s)}/dataset_meta/info.json")
      for s in ("practice/r1_trial", "practice/r1_trial_old_20261102", "practice/r1_try", "practice/r1_try2")],
    # ---- configs (layouts, held-out) ----
    (f"{BOXPICK}/config/redbox_layouts.yaml", "configs/layouts/redbox_layouts.yaml"),
    (f"{BOXPICK}/config/redbox8_layouts.yaml", "configs/layouts/redbox8_layouts.yaml"),
    (f"{BOXPICK}/config/redbox8_heldout_h.yaml", "configs/layouts/redbox8_heldout_h.yaml"),
    # ---- survey docs (11-02) ----
    (f"{RUNS}/research_survey_20261102/부록_조사노트", "docs/appendix_survey_notes"),
]


def excluded(path):
    parts = path.split(os.sep)
    for p in parts[:-1]:
        if p in EXCLUDE_DIRS or p.startswith(EXCLUDE_PREFIX):
            return "dir"
    name = parts[-1]
    ext = os.path.splitext(name)[1].lower()
    if name in EXCLUDE_NAMES or ext in EXCLUDE_EXT or name.startswith("."):
        return "name"
    if ext not in TEXT_EXT | IMG_EXT and name not in ("Makefile",):
        return "ext"
    size = os.path.getsize(path)
    if ext in IMG_EXT and size > MAX_IMG:
        return "size"
    if ext in (".log", ".jsonl") and size > MAX_LOG:
        return "size"
    if ext in TEXT_EXT and size > MAX_TEXT:
        return "size"
    return None


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def iter_pairs():
    for src, dst in MAPPINGS:
        if os.path.isfile(src):
            yield src, dst
        elif os.path.isdir(src):
            for root, dirs, files in os.walk(src):
                rel_root = os.path.relpath(root, src)
                dirs[:] = sorted(d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(EXCLUDE_PREFIX)
                                 and not os.path.islink(os.path.join(root, d)))
                for f in sorted(files):
                    s = os.path.join(root, f)
                    if os.path.islink(s):
                        continue
                    yield s, os.path.normpath(os.path.join(dst, rel_root, f))
        # missing sources are silently skipped (recorded below)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    rows, skipped, total = [], {}, 0
    missing = [s for s, _ in MAPPINGS if not os.path.exists(s)]
    for src, dst in iter_pairs():
        why = excluded(src)
        if why:
            skipped[why] = skipped.get(why, 0) + 1
            continue
        size = os.path.getsize(src)
        total += size
        rows.append((src, dst, size))
    if a.dry_run:
        for s, d, z in rows:
            print(f"{z:>10} {d}")
        print(f"FILES {len(rows)} TOTAL_MB {total/1e6:.1f} SKIPPED {skipped} MISSING {len(missing)}")
        for m in missing:
            print("MISSING", m)
        return
    out = []
    for src, dst, size in rows:
        d = os.path.join(REPO, dst)
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copy2(src, d)
        out.append({"repo_path": dst, "source_path": src, "bytes": size, "sha256": sha256(src),
                    "source_mtime": int(os.path.getmtime(src))})
    with open(os.path.join(REPO, "SOURCES_MANIFEST.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    print(f"copied {len(out)} files, {total/1e6:.1f} MB; skipped {skipped}; missing sources {len(missing)}")
    for m in missing:
        print("MISSING", m)


if __name__ == "__main__":
    sys.exit(main())
