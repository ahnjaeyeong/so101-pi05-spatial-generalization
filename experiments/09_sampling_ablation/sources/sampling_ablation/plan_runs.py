"""실행 계획 (사용자 10-27 확정): A0 → A1 → A2 → A2r → A0′, 모두 d2 020000 에서 새 fine-tune.

공통: expert-only, vision 동결, peak LR 1e-5, warmup 200, cosine → 2.5e-6 / 4000 step, batch 32, 저장 2000 · 4000.
A3 · A3c12 는 실행하지 않는다 (개별 효과를 본 뒤 결정).
`python3 plan_runs.py` → runs/run_<이름>.sh 를 쓴다 (실행은 run_queue.sh).
"""
from pathlib import Path

HOME = Path.home()
SA = HOME / "so101_runs/main_k8/d2/sampling_ablation"
D2_DS = HOME / "so101_runs/main_k8/d2/dataset"
D2_CK = HOME / "so101_runs/main_k8/d2/train/32_20000/pi05_expert_bs32_20k/checkpoints/020000"

RUNS = [  # (이름, 가중, seed) — 이 순서대로
    ("A0_s2001", "A0", 2001),
    ("A1_s2001", "A1", 2001),
    ("A2_s2001", "A2", 2001),
    ("A2r_s2001", "A2r", 2001),
    ("A0_s2002", "A0", 2002),
]


def train_args(name, seed, output_root=SA / "runs"):
    return [
        "--dataset.repo_id=oxr/so101_k8_d2",
        f"--dataset.root={D2_DS}",
        f"--policy.path={D2_CK}/pretrained_model",
        "--policy.push_to_hub=false",
        "--policy.dtype=bfloat16",
        "--policy.train_expert_only=true",
        "--policy.freeze_vision_encoder=true",
        "--policy.gradient_checkpointing=true",
        "--policy.optimizer_lr=1e-5",
        "--policy.scheduler_warmup_steps=200",
        "--policy.scheduler_decay_steps=4000",
        "--policy.scheduler_decay_lr=2.5e-6",
        f"--output_dir={output_root}/{name}",
        f"--job_name={name}",
        "--batch_size=32",
        "--steps=4000",
        "--log_freq=50",
        "--save_freq=2000",
        "--num_workers=4",
        f"--seed={seed}",
        "--wandb.enable=false",
    ]


def write_scripts():
    out = SA / "runs"
    out.mkdir(exist_ok=True)
    for name, arm, seed in RUNS:
        args = " \\\n  ".join(train_args(name, seed))
        (out / f"run_{name}.sh").write_text(f"""#!/usr/bin/env bash
# {name}: 가중 {arm}, seed {seed}. d2 020000 에서 새 fine-tune (plan_runs.py 가 만듦 — 직접 고치지 말 것).
export PYTHONDONTWRITEBYTECODE=1
export SA_WEIGHTS={SA}/weights/weights_{arm}.npy
export SA_RUN_NAME={name}
exec $HOME/so101-env/bin/python {SA}/train_weighted.py \\
  {args}
""")
        (out / f"run_{name}.sh").chmod(0o755)
    print("\n".join(f"runs/run_{n}.sh" for n, _, _ in RUNS))


if __name__ == "__main__":
    write_scripts()
