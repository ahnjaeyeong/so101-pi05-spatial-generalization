#!/usr/bin/env python3
"""Per-experiment list of local files kept out of Git (path, bytes, SHA-256, reason).

Added 2026-11-05: a full `tools/compare_sources.py` run now produces ARCHIVE_MANIFEST.csv (12 MB) and
inventory/INVENTORY.csv (9.4 MB), both over the 7 MB file limit of tools/check_repo.py, mainly because
of ~40k report frame JPGs. Until that is solved, new experiments get their own exclusion list instead.

READ-ONLY on the source side. Usage:
    python3 tools/compare_sources.py                      # writes the full ARCHIVE_MANIFEST.csv
    cp ARCHIVE_MANIFEST.csv /some/scratch/full.csv && git checkout -- ARCHIVE_MANIFEST.csv inventory/
    python3 tools/archive_excluded.py /some/scratch/full.csv

Output rows:
  kind=file         one excluded file. Files that compare_sources.py leaves NOT_HASHED_LARGE_TREE
                    (videos) are hashed here.
  kind=dir_summary  a directory with > 50 excluded files: files, bytes, and sha256 over the sorted lines
                    "<file name>\\t<sha256>" of the files directly in it.
"""
import collections
import csv
import hashlib
import os
import sys

R = "/home/user/so101_runs/main_k8/"
TARGETS = {
    "experiments/11_r1_r2_recovery/sources/ARCHIVE_EXCLUDED.csv":
        [R + "r12_pilot12_r1/", R + "r12_pilot12_rc/", R + "r12_pilot12_r2p/", R + "r12_pilot12_r2o/",
         R + "r1_r2_collection/"],
    "experiments/12_hil/sources/ARCHIVE_EXCLUDED.csv": [R + "hil_dagger/"],
    "experiments/14_rft01_real_pilot/sources/ARCHIVE_EXCLUDED.csv": [R + "rft01_real_pilot/"],
    # added 2026-11-09
    "experiments/15_sg50_sgft01/sources/ARCHIVE_EXCLUDED.csv":
        ["/home/user/so101_runs/practice/sg50_pilot/", "/home/user/so101_runs/practice/sg50_pilot2/", "/home/user/so101_runs/practice/sg50_pilot3/"],
    "experiments/16_sgft01_real_eval/sources/ARCHIVE_EXCLUDED.csv": [R + "sgft01_real_eval/"],
}
DIR_SUMMARY_MIN = 50
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main(full):
    rows = list(csv.DictReader(open(full, encoding="utf-8")))
    for r in rows:
        if r["sha256"] == "NOT_HASHED_LARGE_TREE" and r["source_path"].startswith(
                tuple(p for v in TARGETS.values() for p in v)):
            r["sha256"] = sha256(r["source_path"])
    for out, roots in TARGETS.items():
        bydir = collections.defaultdict(list)
        for r in rows:
            if r["source_path"].startswith(tuple(roots)):
                bydir[os.path.dirname(r["source_path"])].append(r)
        res = []
        for d, rs in sorted(bydir.items()):
            if len(rs) > DIR_SUMMARY_MIN:
                lines = sorted(f"{os.path.basename(r['source_path'])}\t{r['sha256']}" for r in rs)
                res.append({"source_path": d + "/", "kind": "dir_summary", "files": len(rs),
                            "bytes": sum(int(r["bytes"]) for r in rs),
                            "sha256": hashlib.sha256("\n".join(lines).encode()).hexdigest(),
                            "reason": ";".join(sorted({r["reason"] for r in rs})), "derived_repo_path": ""})
            else:
                res += [{"source_path": r["source_path"], "kind": "file", "files": 1, "bytes": r["bytes"],
                         "sha256": r["sha256"], "reason": r["reason"],
                         "derived_repo_path": r["derived_repo_path"]} for r in rs]
        with open(os.path.join(REPO, out), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(res[0].keys()))
            w.writeheader()
            w.writerows(res)
        print(out, "rows", len(res), "files", sum(int(r["files"]) for r in res),
              "MB", round(sum(int(r["bytes"]) for r in res) / 1e6, 1))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
