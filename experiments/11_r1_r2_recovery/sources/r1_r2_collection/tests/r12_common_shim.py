"""시험용: r12_common 의 pan 기준값 (tools 경로·설정을 읽어 둠)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import r12_common as rc  # noqa: E402

_CFG = rc.load_config()


def ref(pos):
    return rc.pan_ref(_CFG, pos)
