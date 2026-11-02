#!/home/user/so101-env/bin/python
"""오류 처리 시험 (로봇 안 씀): 보호 세션 거부 · 모르는 세션 · 모르는 옵션 · 연결 실패 흉내(preview) 뒤 UI 정상 종료."""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pty_driver import Driver  # noqa: E402

T = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools", "r12_collect.py")
PY = os.path.expanduser("~/so101-env/bin/python")
ROOT = sys.argv[1]
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", RECORD_UI_RUNS=os.path.join(ROOT, "runs"), RECORD_UI_LOG_DIR=os.path.join(ROOT, "logs"))
ok = []


def check(name, cond, detail=""):
    print(f"  {'✓' if cond else '✗'} {name} {detail}")
    ok.append(bool(cond))


def run(args):
    d = Driver([PY, T] + args, env)
    code = d.finish(60)
    return code, d.plain


c, out = run(["record", "--session", "main_k8/redbox_t1_known"])
check("d2 세션 거부", c != 0 and "기존 d2 세션" in out)
c, out = run(["record", "--session", "main_k8/d2"])
check("d2 폴더 거부", c != 0 and "기존 d2 세션" in out)
c, out = run(["record", "--session", "main_k8/nope_session"])
check("설정에 없는 세션 거부", c != 0 and "groups 에 없어요" in out)
c, out = run(["record", "--session", "main_k8/r2_pregrasp_pilot"])
check("계획 없으면 거부 (lerobot 안 띄움)", c != 0 and "계획이 없어요" in out and "lerobot-record 종료" not in out)
subprocess.run([PY, T, "plan", "--group", "r2_pilot"], env=env, capture_output=True)
c, out = run(["record", "--session", "main_k8/r2_pregrasp_pilot", "--robot.port=/dev/ttyACM9"])
check("lerobot 옵션 직접 넣기 거부", c != 0 and "모르는 옵션" in out)
c, out = run(["preview", "--type", "R2", "--no-viewer", "--simulate-connect-error", "--root", os.path.join(ROOT, "pv_err")])
check("연결 실패 → 종료 코드 1, 저장 0, 파이썬 오류 없음", "종료 코드 1" in out and "저장 0개" in out and "r12_collect.py\", line" not in out)
print(("PASS" if all(ok) else "FAIL") + f" {sum(ok)}/{len(ok)}")
sys.exit(0 if all(ok) else 1)
