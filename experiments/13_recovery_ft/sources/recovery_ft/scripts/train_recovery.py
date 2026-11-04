#!/usr/bin/env python
"""d2 + R1/R2 교정 16 편 신규 fine-tune launcher (2026-11-04). LeRobot 설치 · 원본 dataset · d2 체크포인트는 수정하지 않는다.

sampling_ablation/train_weighted.py 를 **수정 없이 import** 해서 재사용한다:
  - make_weighted_sampler_class: EpisodeAwareSampler 와 같은 (seed, epoch) randperm, 위치 → 가중 반복 목록의 전역 index
  - sha256 / verify_hashes: d2 020000 체크포인트 + d2 dataset sha256 기록 (sampling_ablation/ops/d2_sha256.json) 대조
  - training_processes: 다른 학습 프로세스 검사
train_weighted 의 guard() 는 d2 dataset 경로에 묶여 있어 이 실험용 guard 를 따로 둔다 (아래).
추가: 학습이 실제로 꺼낸 표본 index 를 첫 steps × batch_size 개까지 기록 (runs/<name>.sampled_abs_idx.npy, 병합 전역 index).
      sampler 는 DataLoader 주 프로세스에서 차례로 돌므로 앞에서부터 steps × batch 개 = 학습에 들어간 표본 (prefetch 분은 뒤에 붙음).

환경 변수: RF_WEIGHTS (가중 .npy), RF_RUN_NAME (run ID)
시작 거부 (종료 코드 3):
  - 다른 학습 프로세스 · GPU compute 프로세스 있음
  - --dataset.root ≠ recovery_ft/dataset, repo_id ≠ oxr/so101_k8_d2_rc16, 인자에 'heldout'
  - --dataset.episodes ≠ manifest 학습 272 편 (순서 포함), manifest sha256 ≠ 기록
  - --policy.path ≠ d2 020000/pretrained_model, --resume 사용
  - --output_dir 이 recovery_ft/runs 밖 · 이미 있음 · 보호 폴더 안
  - d2 020000 · d2 dataset sha256 ≠ 기록, 병합 사본 sha256 ≠ 기록 (manifest/dataset_sha256.json), 사본 stats.json ≠ d2 stats.json
  - 가중 길이 ≠ 사본 프레임 수, 가중 < 1, 정수 아님
"""
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

HOME = Path.home()
SA = HOME / "so101_runs/main_k8/d2/sampling_ablation"
sys.path.insert(0, str(SA))
import train_weighted as TW  # noqa: E402  (수정 없이 재사용)

RF = HOME / "so101_runs/main_k8/d2/recovery_ft"
RUNS = RF / "runs"
DS = (RF / "dataset").resolve()
REPO = "oxr/so101_k8_d2_rc16"
DS_HASH = RF / "manifest/dataset_sha256.json"
MAN = RF / "manifest/training_manifest.json"
MAN_SHA = RF / "manifest/training_manifest.sha256"
PROTECTED = TW.PROTECTED + [(SA / "runs").resolve(), DS]


def dataset_files():
    return sorted(p for p in DS.rglob("*") if p.is_file())


def record_dataset_hashes():
    out = {str(p): dict(size=p.stat().st_size, sha256=TW.sha256(p)) for p in dataset_files()}
    json.dump(dict(time=time.strftime("%F %T"), files=out), open(DS_HASH, "w"), indent=1)
    return out


def verify_dataset_hashes():
    rec = json.load(open(DS_HASH))["files"]
    cur = {str(p) for p in dataset_files()}
    bad = sorted(set(rec) ^ cur)
    for f, v in rec.items():
        p = Path(f)
        if not p.exists() or p.stat().st_size != v["size"] or TW.sha256(p) != v["sha256"]:
            bad.append(f)
    return bad


def parse_list(s):
    return [int(x) for x in s.strip("[]").split(",") if x.strip()] if s else None


def gpu_compute_pids():
    try:
        out = subprocess.run(["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"], capture_output=True, text=True, timeout=30).stdout
    except Exception:
        return []
    return [int(x) for x in out.split() if x.strip().isdigit() and int(x) != os.getpid()]


def guard(argv, weights_path, check_procs=True, full_hash=True):
    errs = []
    if check_procs:
        if TW.training_processes():
            errs.append(f"다른 학습 프로세스 실행 중: {TW.training_processes()}")
        if gpu_compute_pids():
            errs.append(f"GPU compute 프로세스 있음: {gpu_compute_pids()}")
    if any("heldout" in a.lower() for a in argv):
        errs.append("heldout 경로가 인자에 있음")
    root = TW.argval("dataset.root", argv)
    if root is None or Path(root).resolve() != DS:
        errs.append(f"dataset.root 가 병합 사본이 아님: {root}")
    if TW.argval("dataset.repo_id", argv) != REPO:
        errs.append(f"dataset.repo_id 가 {REPO} 가 아님")
    man_txt = MAN.read_text()
    if hashlib.sha256(man_txt.encode()).hexdigest() != MAN_SHA.read_text().split()[0]:
        errs.append("manifest json sha256 이 기록과 다름")
    man = json.loads(man_txt)
    if parse_list(TW.argval("dataset.episodes", argv)) != man["train_episodes_merged"]:
        errs.append("--dataset.episodes 가 manifest 학습 목록 (272 편) 과 다름")
    if TW.argval("dataset.exclude_episodes", argv):
        errs.append("--dataset.exclude_episodes 사용 안 함 (manifest 목록만)")
    pp = TW.argval("policy.path", argv)
    if pp is None or Path(pp).resolve() != TW.D2_CK / "pretrained_model":
        errs.append(f"policy.path 가 d2 020000 이 아님: {pp}")
    if any(a.startswith("--resume") and not a.endswith("false") for a in argv):
        errs.append("--resume 금지 (신규 fine-tune)")
    od = TW.argval("output_dir", argv)
    if od is None or not TW.under(od, RUNS.resolve()) or Path(od).exists() or any(TW.under(od, p) for p in PROTECTED):
        errs.append(f"output_dir 문제 (runs/ 밖 · 이미 있음 · 보호 폴더): {od}")
    w = np.load(weights_path)
    info = json.load(open(DS / "meta/info.json"))
    if len(w) != info["total_frames"] or w.min() < 1 or w.dtype.kind not in "iu":
        errs.append(f"가중 파일 이상: len {len(w)} vs {info['total_frames']}, min {w.min()}, dtype {w.dtype}")
    if TW.sha256(DS / "meta/stats.json") != TW.sha256(TW.D2_DS / "meta/stats.json"):
        errs.append("사본 stats.json ≠ d2 stats.json (d2 020000 정규화와 다름)")
    bad = TW.verify_hashes(full=full_hash)
    if bad:
        errs.append(f"d2 020000/dataset 파일이 기록과 다름: {bad[:5]}")
    if not DS_HASH.exists():
        errs.append("병합 사본 sha256 기록 없음")
    else:
        bad = verify_dataset_hashes()
        if bad:
            errs.append(f"병합 사본 파일이 기록과 다름: {bad[:5]}")
    return errs, w


def make_logging_sampler_class(base_cls, weights, log_path, n_log):
    Weighted = TW.make_weighted_sampler_class(base_cls, weights)

    class LoggingWeightedSampler(Weighted):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self._log = []
            self._saved = False

        def _frame_index(self, position):
            if not self._saved:
                self._log.append(int(self._expanded[position]))
                if len(self._log) >= n_log:
                    np.save(log_path, np.asarray(self._log[:n_log], dtype=np.int64))
                    self._saved = True
                    print(f"[train_recovery] sampled index log saved ({n_log}) → {log_path}", flush=True)
            return super()._frame_index(position)

    return LoggingWeightedSampler


def main():
    argv = sys.argv[1:]
    if argv and argv[0] == "--record_dataset_hashes":
        out = record_dataset_hashes()
        print(f"recorded {len(out)} files → {DS_HASH}")
        return
    wp, name = os.environ.get("RF_WEIGHTS"), os.environ.get("RF_RUN_NAME")
    if not wp or not name:
        sys.exit("RF_WEIGHTS · RF_RUN_NAME 필요")
    check_procs = os.environ.get("RF_DRYRUN_NO_PROC_CHECK") != "1"
    errs, w = guard(argv, wp, check_procs=check_procs)
    if errs:
        print("[train_recovery] 시작 거부:\n  " + "\n  ".join(errs), flush=True)
        sys.exit(3)
    steps, bs = int(TW.argval("steps", argv)), int(TW.argval("batch_size", argv))
    RUNS.mkdir(exist_ok=True)
    log_path = RUNS / f"{name}.sampled_abs_idx.npy"
    man = dict(name=name, start=time.strftime("%F %T"), argv=argv, weights=str(Path(wp).resolve()), weights_sha256=TW.sha256(wp),
               weights_sum_used=None, weights_max=int(w.max()), manifest_sha256=MAN_SHA.read_text().split()[0], d2_hash_record=str(TW.HASHES),
               dataset_hash_record=str(DS_HASH), pid=os.getpid(), sampled_index_log=str(log_path))
    json.dump(man, open(RUNS / f"{name}.manifest.json", "w"), indent=1)
    print("[train_recovery] guard OK", flush=True)
    import lerobot.scripts.lerobot_train as LT
    LT.EpisodeAwareSampler = make_logging_sampler_class(LT.EpisodeAwareSampler, w, log_path, steps * bs)
    sys.argv = ["lerobot-train"] + argv
    LT.main()


if __name__ == "__main__":
    main()
