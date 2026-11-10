"""run_hil.sh 의 실제 인자 묶음이 lerobot 0.6.2 RolloutConfig 로 파싱되는지만 확인 (장치 · 모델 로드 · GPU 없음).
run_hil.sh 를 DRY=1 로 불러 명령을 얻고, adapter · rollout_logged 가 자기 옵션을 뺀 나머지를 parser.wrap 으로 파싱한다."""
import os
import shlex
import subprocess
import sys
from pathlib import Path

R = Path(__file__).resolve().parents[1]
cmd = shlex.split(subprocess.run(["bash", str(R / "tools/run_hil.sh"), "parsecheck"], env={**os.environ, "DRY": "1"},
                                 capture_output=True, text=True, check=True).stdout.splitlines()[0])
i = next(k for k, a in enumerate(cmd) if a.endswith("hil_dagger_entry.py"))
argv = ["lerobot-rollout"] + cmd[i + 1:]
sys.path.insert(0, str(R / "tools"))
sys.path.insert(0, str(Path.home() / "so101_runs/main_k8/d2/eval"))
import hil_dagger_entry as H  # noqa: E402

hil, rest = H._pop_hil(argv)
sys.argv = rest
import rollout_logged as rl  # noqa: E402

sys.argv = rl._ARGV
from lerobot.configs import parser  # noqa: E402
from lerobot.rollout.configs import RolloutConfig  # noqa: E402

got = {}


@parser.wrap()
def f(cfg: RolloutConfig):
    got["cfg"] = cfg


f()
c = got["cfg"]
print("hil opts", hil)
print("rollout_logged opts arm_filter", rl._OPTS["arm_filter"], "active", rl._OPTS["active"])
print("strategy", c.strategy.type, "record_autonomous", c.strategy.record_autonomous, "num_episodes", c.strategy.num_episodes,
      "smooth_handover", c.strategy.smooth_handover, "input", c.strategy.input_device)
print("inference", c.inference.type, "horizon", c.inference.rtc.execution_horizon, "schedule", c.inference.rtc.prefix_attention_schedule,
      "queue_threshold", c.inference.queue_threshold, "steps", c.policy.num_inference_steps, "policy", c.policy.type)
print("robot", c.robot.type, c.robot.port, "max_rel", c.robot.max_relative_target, "cams", {k: (v.width, v.height, v.fps, v.fourcc) for k, v in c.robot.cameras.items()})
print("teleop", c.teleop.type, c.teleop.port, c.teleop.id, "dataset", c.dataset.repo_id, c.dataset.single_task, "streaming", c.dataset.streaming_encoding,
      "return_to_initial", c.return_to_initial_position)
assert rl._OPTS["arm_filter"] is False and rl._OPTS["guard"] == "warn", rl._OPTS
assert c.return_to_initial_position is False and c.robot.max_relative_target == 8.0
assert hil["correction_max_relative_target"] == "keep" and hil["start_paused"] is True
assert hil["tap"].startswith("/dev/shm/hil_parsecheck_") and hil["tap_hz"] == 10.0, hil
print("rollout_logged guard", rl._OPTS["guard"], "· arm_filter", rl._OPTS["arm_filter"])
print("CLI_PARSE_OK")
