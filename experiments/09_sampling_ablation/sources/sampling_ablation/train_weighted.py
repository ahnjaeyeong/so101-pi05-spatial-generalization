#!/usr/bin/env python
"""가중 표집 lerobot-train launcher (d2 sampling ablation, 2026-10-27).

LeRobot 설치 파일 · d2 데이터셋 · d2 체크포인트는 수정하지 않는다. 이 파일은
`lerobot.scripts.lerobot_train.EpisodeAwareSampler` 를 이 프로세스 안에서만 WeightedEpisodeAwareSampler 로 바꿔 끼우고
`lerobot_train.main()` 을 그대로 실행한다 (CLI 인자는 lerobot-train 과 같음).

가중 sampler: 프레임 (전역 index) 을 정수 가중만큼 반복한 목록을 만들고, 원래 sampler 와 똑같이
epoch 마다 (seed, epoch) 로 torch.randperm 한다. 가중이 모두 1 이면 원래 sampler 와 순서가 같다.

환경 변수
  SA_WEIGHTS   가중 파일 (.npy, d2 전역 index 순서, int ≥ 1) — 필수
  SA_RUN_NAME  실험 이름 (manifest 이름) — 필수
시작 전에 막는 조건 (하나라도 걸리면 종료 코드 3):
  - 다른 lerobot-train 프로세스가 있음 (d4 등)
  - --dataset.root 가 d2 데이터셋이 아님, 또는 인자에 'heldout' 이 있음 (H 는 학습 금지)
  - --policy.path 가 d2 020000/pretrained_model 이 아님, --resume 사용
  - --output_dir 이 runs/ 밖이거나 이미 있음, 또는 보호 폴더 (d2/train, d4) 안
  - d2 020000 · d2 데이터셋 sha256 이 기록 (ops/d2_sha256.json) 과 다름
  - 가중 길이 ≠ 데이터셋 프레임 수, 또는 가중 < 1
"""
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

HOME = Path.home()
SA = HOME / "so101_runs/main_k8/d2/sampling_ablation"
RUNS = SA / "runs"
D2_DS = (HOME / "so101_runs/main_k8/d2/dataset").resolve()
D2_CK = (HOME / "so101_runs/main_k8/d2/train/32_20000/pi05_expert_bs32_20k/checkpoints/020000").resolve()
PROTECTED = [(HOME / "so101_runs/main_k8/d2/train").resolve(), (HOME / "so101_runs/main_k8/d4").resolve(),
             (HOME / "so101_runs/main_k8/d2/dataset").resolve()]
HASHES = SA / "ops/d2_sha256.json"


def sha256(p, bs=1 << 24):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while b := f.read(bs):
            h.update(b)
    return h.hexdigest()


def hash_targets():
    """보호 대상 파일 목록 (d2 020000 전체 + d2 데이터셋 meta · parquet · 동영상)."""
    files = sorted(p for p in D2_CK.rglob("*") if p.is_file())
    files += sorted(p for p in D2_DS.rglob("*") if p.is_file())
    return files


def record_hashes():
    out = {str(p): dict(size=p.stat().st_size, sha256=sha256(p)) for p in hash_targets()}
    HASHES.parent.mkdir(exist_ok=True)
    json.dump(dict(time=time.strftime("%F %T"), files=out), open(HASHES, "w"), indent=1)
    return out


def verify_hashes(full=True):
    rec = json.load(open(HASHES))["files"]
    cur = {str(p) for p in hash_targets()}
    bad = sorted(set(rec) ^ cur)
    for f, v in rec.items():
        p = Path(f)
        if not p.exists() or p.stat().st_size != v["size"] or (full and sha256(p) != v["sha256"]):
            bad.append(f)
    return bad


def argval(name, argv):
    for a in argv:
        if a.startswith(f"--{name}="):
            return a.split("=", 1)[1]
    return None


def under(p, root):
    try:
        Path(p).resolve().relative_to(root)
        return True
    except ValueError:
        return False


def training_processes():
    """다른 학습 프로세스 pid (인자 하나가 lerobot-train 또는 train_weighted.py 로 끝나는 프로세스; 셸 명령 문자열은 제외)."""
    me = {os.getpid(), os.getppid()}
    out = []
    for d in Path("/proc").iterdir():
        if not d.name.isdigit() or int(d.name) in me:
            continue
        try:
            args = (d / "cmdline").read_bytes().split(b"\0")
        except OSError:
            continue
        if any(a.endswith((b"lerobot-train", b"train_weighted.py")) for a in args[:3]):
            out.append(int(d.name))
    return sorted(out)


def guard(argv, weights_path, check_procs=True, full_hash=True):
    errs = []
    if check_procs:
        others = training_processes()
        if others:
            errs.append(f"다른 학습 프로세스 실행 중: {others}")
    if any("heldout" in a.lower() for a in argv) or "heldout" in str(weights_path).lower():
        errs.append("H (heldout) 경로가 인자에 있음 — 학습 금지")
    root = argval("dataset.root", argv)
    if root is None or Path(root).resolve() != D2_DS:
        errs.append(f"dataset.root 가 d2 가 아님: {root}")
    if argval("dataset.repo_id", argv) != "oxr/so101_k8_d2":
        errs.append("dataset.repo_id 가 oxr/so101_k8_d2 가 아님")
    pp = argval("policy.path", argv)
    if pp is None or Path(pp).resolve() != D2_CK / "pretrained_model":
        errs.append(f"policy.path 가 d2 020000 이 아님: {pp}")
    if any(a.startswith("--resume") and not a.endswith("false") for a in argv):
        errs.append("--resume 금지 (새 fine-tune 만)")
    od = argval("output_dir", argv)
    if od is None or not under(od, RUNS.resolve()) or Path(od).exists() or any(under(od, p) for p in PROTECTED):
        errs.append(f"output_dir 문제 (runs/ 밖 · 이미 있음 · 보호 폴더): {od}")
    w = np.load(weights_path)
    info = json.load(open(D2_DS / "meta/info.json"))
    if len(w) != info["total_frames"] or w.min() < 1 or w.dtype.kind not in "iu":
        errs.append(f"가중 파일 이상: len {len(w)} vs {info['total_frames']}, min {w.min()}, dtype {w.dtype}")
    if not HASHES.exists():
        errs.append("d2 sha256 기록 없음 (ops/d2_sha256.json)")
    else:
        bad = verify_hashes(full=full_hash)
        if bad:
            errs.append(f"d2 파일이 기록과 다름: {bad[:5]}")
    return errs, w


def make_weighted_sampler_class(base_cls, weights):
    W = np.asarray(weights, dtype=np.int64)

    class WeightedEpisodeAwareSampler(base_cls):
        """EpisodeAwareSampler 와 같은 (seed, epoch) randperm. 위치 → 전역 index 만 가중 반복 목록에서 찾는다."""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            lengths = np.diff(np.r_[0, self._cum_lengths])
            base = np.concatenate([np.arange(s, s + n, dtype=np.int64) for s, n in zip(self._starts, lengths)])
            self._expanded = np.repeat(base, W[base])
            self._num_frames = int(len(self._expanded))
            print(f"[train_weighted] frames {len(base)} → weighted list {self._num_frames} "
                  f"(sum w {int(W[base].sum())}, max {int(W[base].max())})", flush=True)

        def _frame_index(self, position):
            a = int(self._expanded[position])
            return self._absolute_to_relative[a] if self._absolute_to_relative is not None else a

    return WeightedEpisodeAwareSampler


def main():
    argv = sys.argv[1:]
    if argv and argv[0] == "--record_hashes":
        out = record_hashes()
        print(f"recorded {len(out)} files → {HASHES}")
        return
    wp, name = os.environ.get("SA_WEIGHTS"), os.environ.get("SA_RUN_NAME")
    if not wp or not name:
        sys.exit("SA_WEIGHTS · SA_RUN_NAME 필요")
    errs, w = guard(argv, wp)
    if errs:
        print("[train_weighted] 시작 거부:\n  " + "\n  ".join(errs), flush=True)
        sys.exit(3)
    man = dict(name=name, start=time.strftime("%F %T"), argv=argv, weights=str(Path(wp).resolve()), weights_sha256=sha256(wp),
               weights_sum=int(w.sum()), weights_max=int(w.max()), d2_hash_record=str(HASHES), pid=os.getpid())
    RUNS.mkdir(exist_ok=True)
    json.dump(man, open(RUNS / f"{name}.manifest.json", "w"), indent=1)
    import lerobot.scripts.lerobot_train as LT
    LT.EpisodeAwareSampler = make_weighted_sampler_class(LT.EpisodeAwareSampler, w)
    sys.argv = ["lerobot-train"] + argv
    LT.main()


if __name__ == "__main__":
    main()
