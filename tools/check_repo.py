#!/usr/bin/env python3
"""Repository checks before commit/push. Exit code 1 on any error.

1. experiments/*/README.md has required sections and a status code
2. relative Markdown links resolve (in hand-written docs; copied sources are only warned)
3. no file over the size limit, no forbidden binary extensions
4. no secret-looking strings (tokens, keys, private keys)

Usage: python3 tools/check_repo.py [--all-links]
Only checks files that git would track (uses `git ls-files -co --exclude-standard` when inside a repo).
"""
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_BYTES = 5_000_000
FORBIDDEN_EXT = {".safetensors", ".pt", ".pth", ".ckpt", ".bin", ".parquet", ".mp4", ".npz", ".npy", ".gz", ".zip"}
STATUS = ("PLANNED", "IN_PROGRESS", "COMPLETED", "NOT_EVALUATED", "PAUSED", "PARTIAL", "STOPPED")
REQUIRED = ["목적", "가설", "데이터", "모델", "평가", "한계", "원본 자료"]
SECRET_PATTERNS = [
    (r"\bhf_[A-Za-z0-9]{30,}\b", "HuggingFace token"),
    (r"\bgh[pousr]_[A-Za-z0-9]{30,}\b", "GitHub token"),
    (r"github_pat_[A-Za-z0-9_]{40,}", "GitHub PAT"),
    (r"\bsk-[A-Za-z0-9_-]{20,}\b", "API key (sk-)"),
    (r"\bAKIA[0-9A-Z]{16}\b", "AWS key"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "private key"),
    (r"(?i)(api[_-]?key|secret|password|passwd)\s*[:=]\s*['\"][^'\"\s]{8,}['\"]", "credential assignment"),
    (r"\bwandb_[A-Za-z0-9]{20,}\b", "wandb key"),
]
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


def tracked_files():
    try:
        out = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=REPO,
                             capture_output=True, text=True, check=True).stdout
        return [l for l in out.splitlines() if l]
    except Exception:
        res = []
        for root, dirs, files in os.walk(REPO):
            dirs[:] = [d for d in dirs if d != ".git"]
            res += [os.path.relpath(os.path.join(root, f), REPO) for f in files]
        return res


def main():
    all_links = "--all-links" in sys.argv
    errors, warns = [], []
    files = tracked_files()

    # 1. experiment READMEs
    exp_dir = os.path.join(REPO, "experiments")
    for d in sorted(os.listdir(exp_dir)):
        p = os.path.join(exp_dir, d, "README.md")
        if not os.path.isdir(os.path.join(exp_dir, d)):
            continue
        if not os.path.exists(p):
            errors.append(f"missing README: experiments/{d}")
            continue
        txt = open(p, encoding="utf-8").read()
        heads = " ".join(l for l in txt.splitlines() if l.startswith("#"))
        for key in REQUIRED:
            if key not in heads and key not in txt[:2000]:
                errors.append(f"experiments/{d}/README.md: section '{key}' missing")
        if not any(f"`{s}`" in txt for s in STATUS):
            errors.append(f"experiments/{d}/README.md: no status code")
        if not re.search(r"EXP-\d{2}", txt):
            errors.append(f"experiments/{d}/README.md: no EXP-NN id")

    # 2. links, 3. size/ext, 4. secrets
    for rel in files:
        full = os.path.join(REPO, rel)
        if not os.path.isfile(full):
            continue
        ext = os.path.splitext(rel)[1].lower()
        size = os.path.getsize(full)
        if ext in FORBIDDEN_EXT:
            errors.append(f"forbidden file type: {rel}")
        if size > MAX_BYTES:
            errors.append(f"file too large ({size/1e6:.1f} MB): {rel}")
        if ext in {".png", ".jpg", ".jpeg", ".pdf", ".svg"}:
            continue
        try:
            txt = open(full, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        for pat, name in SECRET_PATTERNS:
            for m in re.finditer(pat, txt):
                errors.append(f"possible secret ({name}) in {rel}: {m.group(0)[:12]}…")
        if ext == ".md":
            is_source = "/sources/" in rel or rel.startswith("docs/appendix")
            for target in LINK.findall(txt):
                if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                    continue
                t = target.split("#")[0]
                if not t:
                    continue
                dest = os.path.normpath(os.path.join(os.path.dirname(full), t))
                if not os.path.exists(dest):
                    msg = f"broken link in {rel}: {target}"
                    (warns if (is_source and not all_links) else errors).append(msg)

    for w in warns[:20]:
        print("WARN ", w)
    if len(warns) > 20:
        print(f"WARN  … {len(warns) - 20} more (links inside copied source docs)")
    for e in errors:
        print("ERROR", e)
    print(f"checked {len(files)} files: {len(errors)} errors, {len(warns)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
