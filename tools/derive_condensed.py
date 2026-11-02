#!/usr/bin/env python3
"""Make small, analysis-ready derivatives of large source files and record their provenance.

READ-ONLY on the source side (/home/user/so101_runs). Writes inside this repository only.
Run with the LeRobot venv (needs pandas, pyarrow, av):
    PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python tools/derive_condensed.py

Derivatives (each row recorded in DERIVED_MANIFEST.csv with source path + source SHA-256):
  a) *.condensed.log   rollout logs > MAX_LOG: per-tick servo DEBUG lines
                       ("lerobot.robots.so_follower.so_follower:") removed; RTC, action queue,
                       clamp warnings (robots.utils), cycle timer and all INFO/WARNING kept.
  b) *.csv             decompressed copies of analysis *.csv.gz tables (<= MAX_TEXT)
  c) 02_servo_timeline_10hz_wide.csv   human demo servo timeline (d2 256 eps), every 3rd frame,
                       measured / commanded / tracking error per joint
  d) dataset_state_action.csv          every real-robot rollout dataset: per frame action
                       (policy command sent to the queue) and observation.state (measured joints)
  e) start_frames_extracted/*.png      first video frame of each episode of the 10-26 d2 rollouts
                       (the only d2 evaluation without saved start images), decoded from the
                       original AV1 video at the episode's from_timestamp
  f) diag/obs_first/*.png              original (not re-encoded) observation PNGs of the first
                       policy chunk of every episode in the 10-29 diag runs (copied, not derived)
"""
import csv
import glob
import gzip
import hashlib
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sync_sources as S  # noqa: E402

REPO = S.REPO
RUNS = S.RUNS
ROWS = []


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def record(out, kind, src, method, note=""):
    ROWS.append({"repo_path": os.path.relpath(out, REPO), "kind": kind, "source_path": src,
                 "source_bytes": os.path.getsize(src), "source_sha256": sha(src),
                 "method": method, "note": note})


def mapped_dst(path):
    """Destination in the repo for a source path that lies under a mapped directory."""
    best = None
    for m in S.MAPPINGS:
        src, dst = m[0], m[1]
        if os.path.isdir(src) and path.startswith(src + os.sep):
            if best is None or len(src) > len(best[0]):
                best = (src, dst)
    if best is None:
        return None
    return os.path.join(REPO, best[1], os.path.relpath(path, best[0]))


def condense_logs():
    for src, dst in S.iter_pairs():
        if S.excluded(src) != "size_log" or not src.endswith(".log"):
            continue
        out = os.path.join(REPO, dst) + ".condensed.log"
        os.makedirs(os.path.dirname(out), exist_ok=True)
        kept = dropped = 0
        with open(src, errors="replace") as fi, open(out, "w") as fo:
            fo.write(f"# CONDENSED copy of {src}\n# sha256 {sha(src)}\n"
                     "# removed: lines containing 'lerobot.robots.so_follower.so_follower:' (per-tick servo DEBUG)\n")
            for ln in fi:
                if "lerobot.robots.so_follower.so_follower:" in ln:
                    dropped += 1
                    continue
                kept += 1
                fo.write(ln)
        record(out, "condensed_log", src, "drop per-tick so_follower DEBUG lines", f"kept {kept}, dropped {dropped}")


def gunzip_tables():
    for src, dst in S.iter_pairs():
        if not src.endswith(".csv.gz"):
            continue
        out = os.path.join(REPO, dst[:-3])
        with gzip.open(src, "rb") as f:
            data = f.read()
        if len(data) > S.MAX_TEXT:
            print("skip (too big after gunzip):", src, len(data))
            continue
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "wb") as f:
            f.write(data)
        record(out, "gunzip", src, "gzip -d")


def servo_timeline():
    import pandas as pd
    src = f"{RUNS}/main_k8/d2/data_coverage_audit/02_servo_timeline.parquet"
    if not os.path.exists(src):
        return
    d = pd.read_parquet(src)
    d = d[d["frame_index"] % 3 == 0]
    keep = ["measured_position", "commanded_position", "tracking_error_cmd_minus_meas"]
    w = d.pivot_table(index=["episode_id", "task_type", "frame_index", "timestamp"],
                      columns="servo_name", values=keep, aggfunc="first", observed=True)
    w.columns = [f"{j}__{ {'measured_position': 'meas', 'commanded_position': 'cmd', 'tracking_error_cmd_minus_meas': 'err'}[i]}"
                 for i, j in w.columns]
    w = w.reset_index().round(3)
    out = f"{REPO}/experiments/09_sampling_ablation/sources/data_coverage_audit/02_servo_timeline_10hz_wide.csv"
    w.to_csv(out, index=False)
    record(out, "servo_timeline_10hz", src, "frame_index % 3 == 0 (30 -> 10 Hz), long -> wide per servo",
           f"{len(w)} rows; columns <servo>__meas / __cmd / __err (cmd = leader action, meas = follower)")


def rollout_state_action():
    import pandas as pd
    roots = [m[0] for m in S.MAPPINGS if os.path.isdir(m[0])]
    seen = set()
    for r in roots:
        for info in glob.glob(f"{r}/**/dataset/meta/info.json", recursive=True):
            ds = os.path.dirname(os.path.dirname(info))
            if ds in seen or "/eval" not in ds:
                continue
            seen.add(ds)
            j = json.load(open(info))
            if not j.get("total_frames"):
                continue
            parts = sorted(glob.glob(f"{ds}/data/*/*.parquet"))
            df = pd.concat([pd.read_parquet(p) for p in parts], ignore_index=True)
            names = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
            a = pd.DataFrame(df["action"].tolist(), columns=[f"action__{n}" for n in names])
            s = pd.DataFrame(df["observation.state"].tolist(), columns=[f"state__{n}" for n in names])
            o = pd.concat([df[["episode_index", "frame_index", "timestamp"]], a, s], axis=1).round(3)
            dst = mapped_dst(ds)
            if dst is None:
                continue
            out = os.path.join(os.path.dirname(dst), "dataset_state_action.csv")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            o.to_csv(out, index=False)
            for p in parts:
                record(out, "rollout_state_action", p, "parquet -> csv (action, observation.state, 3 decimals)",
                       f"{j['total_episodes']} eps, {j['total_frames']} frames; action = policy command (before 8deg clamp), state = measured")


def extract_1026_frames():
    import av
    import pandas as pd
    for run in ("20261026_135128_20k_t1_try3", "20261026_140246_20k_t1_try3_filt"):
        ds = f"{RUNS}/main_k8/d2/eval/rollouts/{run}/dataset"
        ep = pd.read_parquet(sorted(glob.glob(f"{ds}/meta/episodes/*/*.parquet"))[0])
        outdir = f"{REPO}/experiments/06_d2_256/sources/d2/eval/rollouts/{run}/start_frames_extracted"
        os.makedirs(outdir, exist_ok=True)
        lines = [f"# {run} — first frame of each episode, extracted from the original AV1 videos (2026-11-02)", "",
                 "| file | video | episode | from_timestamp (s) | decoded frame pts (s) | video sha256 |", "|---|---|---|---|---|---|"]
        for cam in ("front", "wrist"):
            for _, row in ep.iterrows():
                ci = int(row[f"videos/observation.images.{cam}/chunk_index"])
                fi = int(row[f"videos/observation.images.{cam}/file_index"])
                t0 = float(row[f"videos/observation.images.{cam}/from_timestamp"])
                vid = f"{ds}/videos/observation.images.{cam}/chunk-{ci:03d}/file-{fi:03d}.mp4"
                with av.open(vid) as c:
                    st = c.streams.video[0]
                    c.seek(int(max(t0 - 1.0, 0) / st.time_base), stream=st, backward=True)
                    frame = None
                    for f in c.decode(st):
                        if f.time is not None and f.time >= t0 - 1e-3:
                            frame = f
                            break
                if frame is None:
                    continue
                name = f"ep{int(row['episode_index']):03d}_{cam}.png"
                out = os.path.join(outdir, name)
                frame.to_image().save(out)
                record(out, "video_frame", vid, "PyAV decode, first frame with pts >= episode from_timestamp",
                       f"episode {int(row['episode_index'])}, from_timestamp {t0:.4f}, frame pts {frame.time:.4f}")
                lines.append(f"| {name} | `{vid}` | {int(row['episode_index'])} | {t0:.4f} | {frame.time:.4f} | {sha(vid)[:16]}… |")
        with open(os.path.join(outdir, "EXTRACTION.md"), "w") as f:
            f.write("\n".join(lines) + "\n\nThese are decoded video frames (AV1 CRF 30), not separately saved photos.\n")


def diag_first_obs():
    for run in sorted(glob.glob(f"{RUNS}/main_k8/d2/eval/rollouts/20261029_*")):
        cj = f"{run}/diag/chunks.jsonl"
        if not os.path.exists(cj):
            continue
        first = {}
        for ln in open(cj):
            j = json.loads(ln)
            ep, cid = j.get("episode"), j.get("chunk_id")
            if ep is not None and (ep not in first or cid < first[ep]):
                first[ep] = cid
        dst = mapped_dst(f"{run}/diag")
        outdir = os.path.join(dst, "obs_first")
        os.makedirs(outdir, exist_ok=True)
        for ep, cid in sorted(first.items()):
            for cam in ("front", "wrist"):
                src = f"{run}/diag/obs/c{cid:05d}_{cam}.png"
                if os.path.exists(src):
                    out = os.path.join(outdir, f"ep{ep:03d}_c{cid:05d}_{cam}.png")
                    shutil.copy2(src, out)
                    record(out, "original_copy", src, "copy (first policy chunk observation of the episode)",
                           f"episode {ep}, chunk {cid}")


def main():
    condense_logs()
    gunzip_tables()
    servo_timeline()
    rollout_state_action()
    extract_1026_frames()
    diag_first_obs()
    with open(f"{REPO}/DERIVED_MANIFEST.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(ROWS[0].keys()))
        w.writeheader()
        w.writerows(ROWS)
    kinds = {}
    for r in ROWS:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    print("derived rows:", kinds)


if __name__ == "__main__":
    main()
