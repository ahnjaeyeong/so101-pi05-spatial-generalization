"""정식 run 인자 파일 · 실행 스크립트 만들기 (CPU). 이미 있으면 덮어쓰지 않는다.

설정 근거 (EXP-09 sampling ablation A0 과 같은 값, 다른 것만 표시):
  시작 d2 020000 pretrained_model (신규 fine-tune, resume 아님) · Expert-only · vision freeze · bf16 · gradient checkpointing
  batch 32 · peak LR 1e-5 · decay LR 2.5e-6 · seed 2001 · num_workers 4 · log_freq 50 · image_transforms 꺼짐 (d2 와 같음)
  다른 점: steps 4000 → 1000, warmup 200 → 50, decay_steps 4000 → 1000 (EXP-09 곡선을 1/4 로 줄인 모양,
           lerobot CosineDecayWithWarmup: steps ≥ decay_steps 라 자동 축소 없음), save_freq 2000 → 250 (lerobot 기본 기능),
           dataset = 병합 사본 + --dataset.episodes (manifest 272 편), 가중 W=5 (교정 ≈ 20 %).
"""
import json
import os
import stat
import sys
from pathlib import Path

HOME = Path.home()
RF = HOME / "so101_runs/main_k8/d2/recovery_ft"
RUN_ID = "rft01_d2rc16_W5_1k_s2001"
CK = HOME / "so101_runs/main_k8/d2/train/32_20000/pi05_expert_bs32_20k/checkpoints/020000/pretrained_model"


def main():
    man = json.loads((RF / "manifest/training_manifest.json").read_text())
    eps = "[" + ",".join(str(e) for e in man["train_episodes_merged"]) + "]"
    args = [
        "--dataset.repo_id=oxr/so101_k8_d2_rc16",
        f"--dataset.root={RF / 'dataset'}",
        f"--dataset.episodes={eps}",
        f"--policy.path={CK}",
        "--policy.push_to_hub=false",
        "--policy.dtype=bfloat16",
        "--policy.train_expert_only=true",
        "--policy.freeze_vision_encoder=true",
        "--policy.gradient_checkpointing=true",
        "--policy.optimizer_lr=1e-5",
        "--policy.scheduler_warmup_steps=50",
        "--policy.scheduler_decay_steps=1000",
        "--policy.scheduler_decay_lr=2.5e-6",
        f"--output_dir={RF / 'runs' / RUN_ID}",
        f"--job_name={RUN_ID}",
        "--batch_size=32",
        "--steps=1000",
        "--log_freq=50",
        "--save_freq=250",
        "--num_workers=4",
        "--seed=2001",
        "--wandb.enable=false",
    ]
    af = RF / f"runs/{RUN_ID}.args"
    sh = RF / f"runs/run_{RUN_ID}.sh"
    if af.exists() or sh.exists():
        sys.exit("이미 있음 — 덮어쓰지 않음")
    af.write_text("\n".join(args) + "\n")
    sh.write_text(f"""#!/usr/bin/env bash
# {RUN_ID}: d2 020000 → d2 256 + R1 4 + R2(RC) 12 신규 fine-tune (make_run.py 가 만듦 — 직접 고치지 말 것)
export PYTHONDONTWRITEBYTECODE=1
export HF_HUB_OFFLINE=1
export RF_WEIGHTS={RF}/weights/weights_rc16_W5.npy
export RF_RUN_NAME={RUN_ID}
mapfile -t ARGS < {af}
exec $HOME/so101-env/bin/python {RF}/scripts/train_recovery.py "${{ARGS[@]}}"
""")
    sh.chmod(sh.stat().st_mode | stat.S_IXUSR)
    print(af, sh)


if __name__ == "__main__":
    main()
