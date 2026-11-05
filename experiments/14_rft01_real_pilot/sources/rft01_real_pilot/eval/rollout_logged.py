"""rft01 실물 파일럿 세션 (main_k8/rft01_real_pilot) 용 rollout_logged shim (2026-11-05).

eval_ui.py 는 필터 · 감시 옵션이 있으면 '<세션>/eval/rollout_logged.py' 를 불러 쓴다 (EVAL_UI_FILTER_DIR).
이 파일은 R2 진단 세션 shim (~/so101_runs/main_k8/r2_grasp_diagnostic/eval/rollout_logged.py) 을 **수정 없이 그대로** 불러온다.
  → 그 안에서 d2 원본 rollout_logged (필터 · 감시 · ROLLOUT_DIAG 기록) + r2_safety (명령 차단형 안전 정지 · 배치 안내 · 배치 창)
그 위에 이 폴더의 fault_latch (추론 오류 래치) 와 end_hold (자동 원위치 복귀 차단 · 종료 시 제자리 유지 · 토크 유지, 11-05 v2) 를 건다.

순서: (1) --fault_latch* 를 sys.argv 에서 뺀다 → (2) R2 shim import (--r2_safety* → --arm_filter* · --rollout_guard* 를 뺀다)
      → (3) install(opts) = R2 shim install (d2 install + r2_safety.install) + fault_latch.install
eval_ui 가 쓰는 이름 (_ARGV, _OPTS, install) 은 d2 원본과 같다.
"""

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
R2_EVAL = Path.home() / "so101_runs/main_k8/r2_grasp_diagnostic/eval"
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import end_hold  # noqa: E402
import fault_latch  # noqa: E402

FL_OPTS, sys.argv = fault_latch.pop_options(sys.argv)

_spec = importlib.util.spec_from_file_location("rollout_logged_r2", R2_EVAL / "rollout_logged.py")
_r2 = importlib.util.module_from_spec(_spec)
sys.modules["rollout_logged_r2"] = _r2
_spec.loader.exec_module(_r2)

_OPTS, _ARGV = _r2._OPTS, _r2._ARGV
_OPTS["fault_latch"] = FL_OPTS["mode"]
if FL_OPTS["mode"] != "off":
    _OPTS["active"] = True


def install(opts):
    st = _r2.install(opts)
    st["fault_latch"] = fault_latch.install(FL_OPTS, st["r2"])
    st["end_hold"] = end_hold.install(st["r2"], st["fault_latch"])  # 항상 켬 (끄는 옵션 없음)
    return st
