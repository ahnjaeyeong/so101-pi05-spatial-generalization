#!/usr/bin/env python3
"""File-level comparison: local research folders vs. this repository.

READ-ONLY on the source side. Walks every file under
  /home/user/so101_runs, /home/user/so101_boxpick/config, the 10-22 K8 calibration scratch
  folder, and research images on ~/Desktop,
classifies each file into a topic category and a status, and writes
  inventory/INVENTORY.csv       one row per local file
  ARCHIVE_MANIFEST.csv          files kept out of Git: path, bytes, SHA-256 (huge trees: size only),
                                reason, and the derivative in the repo that covers it (if any)
  inventory/SUMMARY.md          counts per category and status

Status:
  in_repo      copied verbatim (SOURCES_MANIFEST.csv)
  derived      not copied, but a condensed/converted/extracted derivative is in the repo (DERIVED_MANIFEST.csv)
  archived     kept out of Git on purpose (size/binary/raw data); path + hash recorded here
  unmapped     not covered by any mapping (listed so it can be reviewed)
Usage: python3 tools/compare_sources.py   (run after sync_sources.py and derive_condensed.py)
"""
import csv
import hashlib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sync_sources as S  # noqa: E402

REPO = S.REPO
NO_HASH_DIRS = ("/videos/", "/checkpoints/", "/f1_features/", "/f1_quality_features/",
                "/reference/aswinkumar99_so101_pick_place/", "/review_videos/", "/.cache/")
SPECIAL = (("/so101_runs/_deleted/", "deleted_session"),
           ("/reference/aswinkumar99_so101_pick_place/", "external_public_dataset"),
           ("/reference/aswin_task2_compare/github/", "external_public_repo_clone"),
           ("/reference/aswin_task2_compare/meta_dl/", "external_public_dataset_meta"))
DESKTOP_RE = re.compile(r"^(redbox|SO101|cam_)")
IN_PROGRESS = ("/main_k8/r2_grasp_diagnostic/",)

CATS = [
    ("camera_photo", r"(/setup_photos/|/main_k8/setting/.*\.(png|pdf)$|/camera_settings/|start_(front|wrist)\.png$|/start_images/|/diag/obs/|/Desktop/(cam_|redbox_K_위치_(녹화화면|카메라)|redbox_카메라)|front_(640|1280)\.png$|recheck_|front원본)"),
    ("camera_calibration", r"(layouts.*\.yaml$|heldout_h\.yaml$|/range_check/|/calibration_backup|k8_result|cam_model|cam_fit|/fit\d?\.|fit\d\.json|make_k8|plan_homography|camera_check|/ang/|/angle/|위치_평면도|cube_angle|feature_mapping)"),
    ("heatmap_spatial", r"(heatmap|히트맵|space_map|분포|positions\.csv$|position_map|/hard/|zones_guide)"),
    ("servo_pan_roll_timeseries", r"(servo|_action_state\.png$|pan_timeline|roll_alignment|/roll/|ticks\.csv(\.gz)?$|p08_human_pan|human_pan|a02_frames|02_servo_timeline|fig1_pan|fig6_pilot|wrist_rel|roll_)"),
    ("command_vs_actual", r"(filter_log\.csv$|ticks_chain|analysis\.(json|npz)$|real_command_compare|/dataset/data/.*\.parquet$|p18_|descent)"),
    ("rtc_action_log", r"(debug\.log$|console\.log$|viewer\.log$|inferences\.csv$|chunks\.(npz|jsonl)$|/diag/chunks/|/diag/(manifest|summary|verify)\.json$|/replay/|rtc)"),
    ("action_expert_analysis", r"(/action_bottleneck/|/sampling_ablation/eval/|/vision_probe/)"),
    ("dataset_or_checkpoint", r"(/dataset/|/checkpoints/|/release/|/review_videos/|\.safetensors$|\.mp4$)"),
    ("training_log_config", r"(/train/|/sampling_ablation/runs/)"),
]


def category(path):
    for name, pat in CATS:
        if re.search(pat, path):
            return name
    return "other"


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def load_col(fname, col):
    p = os.path.join(REPO, fname)
    out = {}
    if os.path.exists(p):
        for r in csv.DictReader(open(p, encoding="utf-8")):
            out.setdefault(r[col], []).append(r["repo_path"])
    return out


def local_files():
    roots = [S.RUNS, f"{S.BOXPICK}/config", S.K8_SCRATCH]
    for r in roots:
        for root, dirs, files in os.walk(r):
            dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(root, d))]
            for f in files:
                p = os.path.join(root, f)
                if not os.path.islink(p):
                    yield p
    for f in sorted(os.listdir(S.DESKTOP)):
        if DESKTOP_RE.match(f) and os.path.isfile(os.path.join(S.DESKTOP, f)):
            yield os.path.join(S.DESKTOP, f)


def main():
    copied = load_col("SOURCES_MANIFEST.csv", "source_path")
    derived = load_col("DERIVED_MANIFEST.csv", "source_path")
    mapped_roots = [m[0] for m in S.MAPPINGS]
    # map each source file -> exclusion reason via the same walker the sync uses
    reason = {}
    for src, _dst in S.iter_pairs():
        if src != "DIR":
            reason[src] = S.excluded(src)
    rows, arch = [], []
    inprog = [0, 0]
    for p in local_files():
        size = os.path.getsize(p)
        cat = category(p)
        repo = ";".join(copied.get(p, []))
        der = ";".join(derived.get(p, []))
        if repo:
            st, why = "in_repo", ""
        elif der:
            st, why = "derived", reason.get(p) or "derived"
        elif any(x in p for x in IN_PROGRESS):
            inprog[0] += 1
            inprog[1] += size
            continue
        elif any(x in p for x, _ in SPECIAL):
            st, why = "archived", next(w for x, w in SPECIAL if x in p)
        elif re.search(r"/(dataset|release|checkpoints|training_state|videos)/", p):
            st, why = "archived", "raw_dataset_or_checkpoint"
        elif any(p == r or p.startswith(r + os.sep) for r in mapped_roots):
            st = "archived"
            why = reason.get(p)
            if why is None:  # inside a pruned directory
                root = max((r for r in mapped_roots if p.startswith(r + os.sep)), key=len)
                extra = next((set(m[2]) for m in S.MAPPINGS if m[0] == root and len(m) > 2), set())
                rel_parts = os.path.relpath(p, root).split(os.sep)[:-1]
                d = next((x for x in rel_parts if x in S.EXCLUDE_DIRS or x in extra
                          or x.startswith(S.EXCLUDE_PREFIX)), "pruned")
                why = f"dir:{re.sub(r'_[0-9]{8}_[0-9]{6}$', '_*', re.sub(r'^tmp.+', 'tmp*', d))}"
        else:
            st, why = "unmapped", "no_mapping"
        rows.append({"source_path": p, "bytes": size, "category": cat, "status": st, "reason": why,
                     "repo_path": repo, "derived_repo_path": der})
        if st in ("archived", "derived") or (st == "unmapped" and why == "no_mapping"):
            h = "" if any(x in p for x in NO_HASH_DIRS) else sha(p)
            arch.append({"source_path": p, "bytes": size, "sha256": h or "NOT_HASHED_LARGE_TREE",
                         "category": cat, "status": st, "reason": why, "derived_repo_path": der})
    os.makedirs(f"{REPO}/inventory", exist_ok=True)
    with open(f"{REPO}/inventory/INVENTORY.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    with open(f"{REPO}/ARCHIVE_MANIFEST.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(arch[0].keys()))
        w.writeheader()
        w.writerows(arch)
    # summary
    stats = {}
    for r in rows:
        k = (r["category"], r["status"])
        n, b = stats.get(k, (0, 0))
        stats[k] = (n + 1, b + int(r["bytes"]))
    cats = [c for c, _ in CATS] + ["other"]
    sts = ["in_repo", "derived", "archived", "unmapped"]
    lines = ["| 범주 | 로컬 원본 | GitHub 직접 등록 | 축약·변환으로 반영 | 해시만 기록 (Git 제외) | 매핑 없음 |", "|---|---|---|---|---|---|"]
    tot = [0] * 5
    for c in cats:
        cnt = [stats.get((c, s), (0, 0))[0] for s in sts]
        if not sum(cnt):
            continue
        local = sum(cnt)
        tot = [a + b for a, b in zip(tot, [local] + cnt)]
        lines.append(f"| {c} | {local} | {cnt[0]} | {cnt[1]} | {cnt[2]} | {cnt[3]} |")
    lines.append(f"| **합계** | **{tot[0]}** | **{tot[1]}** | **{tot[2]}** | **{tot[3]}** | **{tot[4]}** |")
    reasons = {}
    for r in rows:
        if r["status"] in ("archived", "unmapped"):
            k = r["status"] + " · " + (r["reason"].split(":")[0] + ":" + r["reason"].split(":")[1] if r["reason"].startswith("dir:") else r["reason"])
            n, b = reasons.get(k, (0, 0))
            reasons[k] = (n + 1, b + int(r["bytes"]))
    lines += ["", "| 제외 사유 | 파일 수 | 용량 (MB) |", "|---|---|---|"]
    for k, (n, b) in sorted(reasons.items(), key=lambda x: -x[1][1]):
        lines.append(f"| {k} | {n} | {b/1e6:,.1f} |")
    lines += ["", f"| 제외: 다른 세션이 작업 중인 폴더 `main_k8/r2_grasp_diagnostic` | {inprog[0]} | {inprog[1]/1e6:,.1f} |"]
    with open(f"{REPO}/inventory/SUMMARY_TABLES.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
