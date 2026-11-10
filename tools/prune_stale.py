#!/usr/bin/env python3
"""Remove repository copies under experiments/*/sources/ (and docs/appendix_survey_notes,
docs/so101_runs_original, configs/robot) that are no longer listed in SOURCES_MANIFEST.csv or
DERIVED_MANIFEST.csv. Only touches files inside this repository; never the original folders.
Usage: python3 tools/prune_stale.py [--dry-run]"""
import csv, glob, os, sys
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
keep = set()
for m in ("SOURCES_MANIFEST.csv", "DERIVED_MANIFEST.csv"):
    for r in csv.DictReader(open(os.path.join(REPO, m), encoding="utf-8")):
        keep.add(os.path.normpath(r["repo_path"]))
roots = glob.glob(f"{REPO}/experiments/*/sources") + [f"{REPO}/docs/appendix_survey_notes",
        f"{REPO}/docs/so101_runs_original", f"{REPO}/configs/robot"]
removed = 0
for root in roots:
    for d, _, files in os.walk(root):
        for f in files:
            p = os.path.join(d, f)
            rel = os.path.relpath(p, REPO)
            if rel in keep or f == "EXTRACTION.md":
                continue
            removed += 1
            if "--dry-run" in sys.argv:
                print("would remove", rel)
            else:
                os.remove(p)
for root in roots:
    for d, dirs, files in sorted(os.walk(root), key=lambda x: -len(x[0])):
        if not os.listdir(d):
            os.rmdir(d)
print("removed", removed)
