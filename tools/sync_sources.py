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
import re
import csv
import hashlib
import os
import shutil
import sys

HOME = "/home/user"
RUNS = f"{HOME}/so101_runs"
BOXPICK = f"{HOME}/so101_boxpick"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEXT_EXT = {".md", ".json", ".csv", ".yaml", ".yml", ".txt", ".py", ".sh", ".log", ".jsonl", ".time", ".in", ".lock"}
IMG_EXT = {".png", ".svg", ".jpg", ".jpeg", ".pdf"}
MAX_TEXT = 6_500_000          # bytes (2026-11-02: raised from 3 MB to keep probe/G1 row tables)
MAX_LOG = 2_000_000           # .log / .jsonl files (bigger logs -> tools/derive_condensed.py)
MAX_IMG = 1_500_000

# Directories never walked. Their contents are summarised (count/bytes) in ARCHIVE_MANIFEST.csv.
EXCLUDE_DIRS = {
    "dataset", "checkpoints", "review_videos", "frames", "frames_train",
    "obs", "chunks", "__pycache__", "release", "f1_features", "f1_quality_features",
    "harness", "runs_lat1.0", "runs_lat1.55", "runs_spike", ".cache", "_deleted",
    "replay", "preview", "ctrl", "backup",
    "dataset_empty_20261015_1449", "dataset_empty_20261023_1333", "plan_preview", "live",
    "weights", "f1_results_raw", ".git",
}
EXCLUDE_PREFIX = ("tmp", "runs_wide", "dataset_empty")
EXCLUDE_NAMES = set()
EXCLUDE_EXT = {".npz", ".npy", ".parquet", ".mp4", ".safetensors", ".pt", ".bin", ".gz", ".zip", ".pyc", ".bak"}
# raw training logs (tqdm progress bars, memory logs): loss is extracted to analysis/loss/ instead
TRAIN_LOG_MARKERS = ("/train/", "/sampling_ablation/runs/")
# per-episode QA sheets (773 files, ~70 MB): summarised in ARCHIVE_MANIFEST.csv
QA_EPISODE_RE = r"/qa/ep_\d+\.jpg$"

DESKTOP = f"{HOME}/Desktop"
K8_SCRATCH = "/tmp/claude-2001/-home-user/401de9d0-444f-477e-991b-156d7183fd3b/scratchpad/k8"  # 10-22 calibration work files

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
    # ---- added 2026-11-02 (source completeness audit) ----
    # camera / setup photos (camera-view captures; no external photo of the camera mount exists)
    *[(f"{RUNS}/{s}/setup_photos", f"experiments/{e}/sources/{dst}/setup_photos")
      for s, e, dst in (
          ("practice/practice_10", "01_paper_cube", "practice_10"),
          ("practice/practice_50", "01_paper_cube", "practice_50"),
          ("main/cubemark_v1", "02_cubemark_expert_only", "cubemark_v1"),
          *[(f"main/redbox_{t}_{k}", "03_redbox_384_20k", f"sessions/redbox_{t}_{k}")
            for t in ("t1", "t2", "t3") for k in ("known", "random")],
          *[(f"practice/{p}", "03_redbox_384_20k", f"pilots/{p}")
            for p in ("redbox_t1k_pilot", "redbox_t2k_pilot", "redbox_t3r_pilot")],
          *[(f"main_k8/redbox_{t}_{k}", "06_d2_256", f"sessions/redbox_{t}_{k}")
            for t in ("t1", "t3") for k in ("known", "random")],
          ("practice/redbox_k8_t3k_pilot", "06_d2_256", "pilots/redbox_k8_t3k_pilot"),
          *[(f"practice/{p}", "11_r1_r2_recovery", f"sessions/{p}")
            for p in ("r1_trial", "r1_trial_old_20261102", "r1_try2")],
      )],
    (f"{RUNS}/main_k8/setting", "experiments/06_d2_256/sources/main_k8_setting"),
    (f"{RUNS}/range_check", "configs/robot/range_check"),
    (f"{RUNS}/calibration_backup_20261002", "configs/robot/calibration_backup_20261002"),
    # QA folders (heatmaps, servo time series, overview/layout sheets; per-episode ep_N.jpg excluded)
    *[(f"{RUNS}/main/redbox_{t}_{k}/qa", f"experiments/03_redbox_384_20k/sources/sessions/redbox_{t}_{k}/qa")
      for t in ("t1", "t2", "t3") for k in ("known", "random")],
    *[(f"{RUNS}/main_k8/redbox_{t}_{k}/qa", f"experiments/06_d2_256/sources/sessions/redbox_{t}_{k}/qa")
      for t in ("t1", "t3") for k in ("known", "random")],
    *[(f"{RUNS}/practice/{p}/{f}", f"experiments/03_redbox_384_20k/sources/pilots/{p}/{f}")
      for p in ("redbox_t1k_pilot", "redbox_t2k_pilot", "redbox_t3r_pilot")
      for f in ("notes.md", "qa_report.md", "layout.csv", "layout_meta.json", "qa")],
    *[(f"{RUNS}/practice/redbox_k8_t3k_pilot/{f}", f"experiments/06_d2_256/sources/pilots/redbox_k8_t3k_pilot/{f}")
      for f in ("notes.md", "qa_report.md", "layout.csv", "layout_meta.json", "파일럿_명령.md", "qa")],
    (f"{RUNS}/practice/practice_10/qa", "experiments/01_paper_cube/sources/practice_10/qa"),
    (f"{RUNS}/practice/practice_50/qa", "experiments/01_paper_cube/sources/practice_50/qa"),
    (f"{RUNS}/main/cubemark_v1/qa", "experiments/02_cubemark_expert_only/sources/cubemark_v1/qa"),
    # 10-22 K1–K8 camera calibration work files (session scratchpad; reg/ and servo/ are bulk intermediates)
    (K8_SCRATCH, "experiments/06_d2_256/sources/k8_relayout_scratch_20261022", ("reg", "servo")),
    # Desktop snapshots made during the experiments
    *[(f"{DESKTOP}/{n}", f"experiments/{e}/sources/desktop_snapshots/{n}") for n, e in (
        ("cam_front_20261012_145019.png", "02_cubemark_expert_only"),
        ("redbox_K_위치_녹화화면640.png", "03_redbox_384_20k"),
        ("redbox_K_위치_카메라확인.png", "03_redbox_384_20k"),
        ("redbox_K_위치_평면도.png", "03_redbox_384_20k"),
        ("redbox_카메라_녹화영역비교.png", "03_redbox_384_20k"),
        ("redbox_T1R_히트맵.png", "03_redbox_384_20k"),
        ("redbox_T1R_분포_평면도.png", "03_redbox_384_20k"),
        ("redbox_T1R_분포_카메라.png", "03_redbox_384_20k"),
        ("redbox_T2R_히트맵.png", "03_redbox_384_20k"),
        ("redbox_T3R_히트맵.png", "03_redbox_384_20k"),
        ("SO101_R1_R2_Collection_UI.png", "11_r1_r2_recovery"),
        ("SO101_R1_R2_Collection_UI_R1A.png", "11_r1_r2_recovery"),
        ("SO101_R1_R2_Collection_UI_R1B.png", "11_r1_r2_recovery"),
        ("SO101_R1_R2_Collection_UI_R1.png", "11_r1_r2_recovery"),
        ("SO101_R1_R2_Collection_UI_R2.png", "11_r1_r2_recovery"),
        ("SO101_R1_R2_Collection_UI_Recording.png", "11_r1_r2_recovery"),
    )],
    # whole session folders (so every remaining file is either copied or listed with its hash)
    *[(f"{RUNS}/main/redbox_{t}_{k}", f"experiments/03_redbox_384_20k/sources/sessions/redbox_{t}_{k}")
      for t in ("t1", "t2", "t3") for k in ("known", "random")],
    *[(f"{RUNS}/main_k8/redbox_{t}_{k}", f"experiments/06_d2_256/sources/sessions/redbox_{t}_{k}")
      for t in ("t1", "t2", "t3") for k in ("known", "random")],
    *[(f"{RUNS}/practice/{p}", f"experiments/03_redbox_384_20k/sources/pilots/{p}")
      for p in ("redbox_t1k_pilot", "redbox_t2k_pilot", "redbox_t3r_pilot")],
    (f"{RUNS}/practice/redbox_k8_t3k_pilot", "experiments/06_d2_256/sources/pilots/redbox_k8_t3k_pilot"),
    (f"{RUNS}/practice/practice_10", "experiments/01_paper_cube/sources/practice_10"),
    (f"{RUNS}/practice/practice_50", "experiments/01_paper_cube/sources/practice_50"),
    (f"{RUNS}/main/cubemark_v1", "experiments/02_cubemark_expert_only/sources/cubemark_v1"),
    (f"{RUNS}/main/redbox_all/eval", "experiments/04_rtc_filter_space_eval/sources/main_redbox_all_eval"),
    (f"{RUNS}/reference/aswin_task2_compare", "experiments/06_d2_256/sources/reference_aswin_task2_compare",
     ("github", "meta_dl")),
    # remaining small originals (E0_J_0 checklists/run logs, top-level so101_runs notes, survey docs 01–10)
    (f"{RUNS}/e0_j0", "experiments/01_paper_cube/sources/e0_j0"),
    *[(f"{RUNS}/{n}", f"docs/so101_runs_original/{n}") for n in (
        "README.md", "description.md", "reorg_plan.md", "ros2_guide.md", "rollout")],
    *[(p, f"docs/{os.path.basename(p)}") for p in sorted(
        __import__("glob").glob(f"{RUNS}/research_survey_20261102/[01]*.md"))],
    (f"{BOXPICK}/config/feature_mapping.yaml", "configs/layouts/feature_mapping.yaml"),
    (f"{RUNS}/practice/README.md", "docs/so101_runs_original/practice_README.md"),
    (f"{RUNS}/research_survey_20261102/README.md", "docs/so101_runs_original/research_survey_20261102_README.md"),
    (f"{BOXPICK}/config/env", "configs/env"),
    (f"{DESKTOP}/redbox_K_템플릿_A3.svg", "experiments/03_redbox_384_20k/sources/desktop_snapshots/redbox_K_템플릿_A3.svg"),
    # ---- 13 recovery FT (11-04): scripts, manifest, tables, eval tables, small logs; dataset/checkpoints/raw excluded ----
    (f"{RUNS}/main_k8/d2/recovery_ft", "experiments/13_recovery_ft/sources/recovery_ft",
     ("dataset", "raw", "weights", "checkpoints", "training_state")),
    # ---- survey docs (11-02) ----
    (f"{RUNS}/research_survey_20261102/부록_조사노트", "docs/appendix_survey_notes"),
    # ---- added 2026-11-05 (handoff records) ----
    # 11 R1/R2: pilot12 sessions actually recorded 11-03 ~ 11-04 (dataset/review videos excluded; meta info.json kept)
    *[(f"{RUNS}/main_k8/{s}", f"experiments/11_r1_r2_recovery/sources/sessions/{s}")
      for s in ("r12_pilot12_r1", "r12_pilot12_rc", "r12_pilot12_r2p", "r12_pilot12_r2o")],
    *[(f"{RUNS}/main_k8/{s}/dataset/meta/info.json", f"experiments/11_r1_r2_recovery/sources/sessions/{s}/dataset_meta/info.json")
      for s in ("r12_pilot12_r1", "r12_pilot12_rc", "r12_pilot12_r2p")],
    # 12 HIL prep (11-04): adapter, tools, tests, reports; fake-device outputs (tests/_out*) and the
    # upstream LeRobot source copies (docs/upstream_main_ba83e4cf) excluded; tests/_out top-level summaries kept
    (f"{RUNS}/main_k8/hil_dagger", "experiments/12_hil/sources/hil_dagger",
     ("_out", "_out_perf", "_out_rep", "_out_v1", "upstream_main_ba83e4cf")),
    *[(p, f"experiments/12_hil/sources/hil_dagger/tests/_out/{os.path.basename(p)}") for p in sorted(
        __import__("glob").glob(f"{RUNS}/main_k8/hil_dagger/tests/_out/*")) if os.path.isfile(p)],
    # 14 rft01 real pilot (11-05): scripts, config, results, per-trial reports and small rollout logs;
    # rollout dataset/videos, diag chunks/obs/replay, report frames/obs, fake-device outputs excluded
    (f"{RUNS}/main_k8/rft01_real_pilot", "experiments/14_rft01_real_pilot/sources/rft01_real_pilot",
     ("_out", "diag", "viewer")),
    # ---- added 2026-11-09 ----
    # 15 SG50 collection (11-05 ~ 11-06) + sgft01 fine-tune / offline tests (11-06 ~ 11-07): pilot sessions (plans, QA, sticker
    # references, check reports), training run records (args, wrapper, logs summary, eval results); datasets, checkpoints,
    # offline-eval npz, per-frame sticker CSVs excluded (tools and the 13_sg50_sticker.md log live under EXP-11 r1_r2_collection)
    *[(f"{RUNS}/practice/{s}", f"experiments/15_sg50_sgft01/sources/{s}", ("sg_sticker", "raw", "vis_raw", "r12_start_frames"))
      for s in ("sg50_pilot", "sg50_pilot2", "sg50_pilot3")],
    (f"{HOME}/io-capture/20261106-1607/SUMMARY.md", "experiments/15_sg50_sgft01/sources/io_capture_20261106-1607/SUMMARY.md"),
    # 16 sgft01 real eval (11-09): copied rft01 pilot tooling with sgft01 plan, run logs/results, analysis report and extracted frames;
    # rollout dataset/videos, diag chunks, fake-device outputs excluded
    (f"{RUNS}/main_k8/sgft01_real_eval", "experiments/16_sgft01_real_eval/sources/sgft01_real_eval",
     ("_out", "diag", "viewer")),
]


def excluded(path):
    """Return None if the file is copied, else a short reason code."""
    rel = path
    for root in sorted((K8_SCRATCH, RUNS, BOXPICK, DESKTOP), key=len, reverse=True):
        if path.startswith(root + os.sep):
            rel = path[len(root) + 1:]
            break
    parts = rel.split(os.sep)
    for p in parts[:-1]:
        if p in EXCLUDE_DIRS or p.startswith(EXCLUDE_PREFIX):
            return "dir"
    name = parts[-1]
    ext = os.path.splitext(name)[1].lower()
    if name in EXCLUDE_NAMES or ext in EXCLUDE_EXT or name.startswith("."):
        return "binary_ext"
    if ext not in TEXT_EXT | IMG_EXT and name not in ("Makefile",):
        return "other_ext"
    if ext == ".log" and (name.endswith(".mem.log") or (any(m in path for m in TRAIN_LOG_MARKERS)
                                                         and re.match(r"^(pi05_.*|A\d\w*_s\d+)\.log$", name))):
        return "train_log"
    if re.search(QA_EPISODE_RE, path):
        return "qa_episode_sheet"
    size = os.path.getsize(path)
    if ext in IMG_EXT and size > MAX_IMG:
        return "size"
    if ext in (".log", ".jsonl") and size > MAX_LOG:
        return "size_log"
    if ext in TEXT_EXT and size > MAX_TEXT:
        return "size"
    return None


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def iter_pairs(with_skipped_dirs=False):
    """Yield (src, dst). MAPPINGS entries are (src, dst) or (src, dst, extra_excluded_dir_names).
    With with_skipped_dirs=True also yields ("DIR", pruned_dir_path) for pruned directories."""
    yielded = set()  # a source file is copied only once (first matching mapping wins)
    for m in MAPPINGS:
        src, dst = m[0], m[1]
        extra = set(m[2]) if len(m) > 2 else set()
        if os.path.isfile(src):
            if src not in yielded:
                yielded.add(src)
                yield src, dst
        elif os.path.isdir(src):
            for root, dirs, files in os.walk(src):
                rel_root = os.path.relpath(root, src)
                keep = []
                for d in sorted(dirs):
                    full = os.path.join(root, d)
                    if os.path.islink(full):
                        continue
                    if d in EXCLUDE_DIRS or d in extra or d.startswith(EXCLUDE_PREFIX):
                        if with_skipped_dirs:
                            yield "DIR", full
                        continue
                    keep.append(d)
                dirs[:] = keep
                for f in sorted(files):
                    s = os.path.join(root, f)
                    if os.path.islink(s) or s in yielded:
                        continue
                    yielded.add(s)
                    yield s, os.path.normpath(os.path.join(dst, rel_root, f))
        # missing sources are silently skipped (recorded below)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", action="append", default=[], metavar="DST_PREFIX",
                    help="copy only files whose repo path starts with this prefix (repeatable); "
                         "other SOURCES_MANIFEST.csv rows are kept unchanged")
    a = ap.parse_args()
    rows, skipped, total = [], {}, 0
    missing = [m[0] for m in MAPPINGS if not os.path.exists(m[0])]
    seen = set()
    for src, dst in iter_pairs():
        if dst in seen:
            continue
        seen.add(dst)
        if a.only and not dst.startswith(tuple(a.only)):
            continue
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
    n_new = len(rows)
    for src, dst, size in rows:
        d = os.path.join(REPO, dst)
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copy2(src, d)
        out.append({"repo_path": dst, "source_path": src, "bytes": size, "sha256": sha256(src),
                    "source_mtime": int(os.path.getmtime(src))})
    man = os.path.join(REPO, "SOURCES_MANIFEST.csv")
    if a.only and os.path.exists(man):
        # keep rows outside the selected prefixes; replace rows inside them
        with open(man, newline="", encoding="utf-8") as f:
            kept = [r for r in csv.DictReader(f) if not r["repo_path"].startswith(tuple(a.only))]
        out = kept + out
    with open(man, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    print(f"copied {n_new} files, {total/1e6:.1f} MB (manifest rows {len(out)}); skipped {skipped}; missing sources {len(missing)}")
    for m in missing:
        print("MISSING", m)


if __name__ == "__main__":
    sys.exit(main())
