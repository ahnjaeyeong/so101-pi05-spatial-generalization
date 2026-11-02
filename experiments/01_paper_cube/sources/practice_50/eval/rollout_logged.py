"""lerobot-rollout 을 그대로 실행하면서 DEBUG 로그 파일을 하나 더 남긴다 (venv 는 건드리지 않음).

- RTC 추론마다의 지연·큐 길이 ("RTC inference latency=…", DEBUG)
- max_relative_target 제한 경고 ("Relative goal position magnitude had to be clamped", WARNING)
를 ms 단위 시각과 함께 ROLLOUT_DEBUG_LOG 경로에 기록한다. 인자는 lerobot-rollout 과 같다.

주의: --interactive=true 는 실행 중 WARNING 이하를 전부 끄므로 이 파일에도 안 남는다.
"""

import logging
import os
import sys

import lerobot.scripts.lerobot_rollout as lr

_orig_init_logging = lr.init_logging


def _init_logging(*args, **kwargs):
    _orig_init_logging(*args, **kwargs)
    path = os.environ.get("ROLLOUT_DEBUG_LOG")
    if not path:
        return
    h = logging.FileHandler(path)
    h.setLevel(logging.DEBUG)
    h.setFormatter(logging.Formatter("%(asctime)s.%(msecs)03d %(levelname)s %(name)s: %(message)s", "%H:%M:%S"))
    h.addFilter(lambda r: r.name.startswith("lerobot") or r.levelno >= logging.WARNING)
    logging.getLogger().addHandler(h)
    logging.getLogger("lerobot.rollout_logged").info("debug log: %s · argv: %s", path, " ".join(sys.argv[1:]))


lr.init_logging = _init_logging

if __name__ == "__main__":
    lr.main()
