#!/home/user/so101-env/bin/python
"""Preview 전체 흐름 시험 (로봇 없음): 실제 r12_collect.py preview 를 pty 에서 실행하고 키를 보낸 뒤 기록 파일을 확인한다.

  ~/so101-env/bin/python tests/test_preview_flow.py [--viewer] [--root DIR]
확인: 쉬는 자세에서도 → 로 시작 (11-02, 경고만) · 영상 창 키 → 녹화 · 준비 단계 뒤 녹화 · 결과 입력(1/2/m) · ← 버리기 → 같은 번호 다시 · 저장 · 마지막 판 결과 질문 ·
     r12_attempts.jsonl / r12_episodes.csv 내용 · ~/so101_runs 를 건드리지 않음 · lerobot 을 부르지 않음.
"""

import csv
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pty_driver import ESC, LEFT, RIGHT, Driver  # noqa: E402

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools")
VENV = os.path.expanduser("~/so101-env/bin/python")


def main():
    viewer = "--viewer" in sys.argv
    root = sys.argv[sys.argv.index("--root") + 1] if "--root" in sys.argv else \
        f"/tmp/r12_preview_test_{datetime.datetime.now():%Y%m%d_%H%M%S}"
    runs_before = os.path.getmtime(os.path.expanduser("~/so101_runs/main_k8"))
    cmd = [VENV, os.path.join(TOOLS, "r12_collect.py"), "preview", "--type", "R2", "--episodes", "3", "--root", root]
    if not viewer:
        cmd.append("--no-viewer")
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    d = Driver(cmd, env)
    results = []

    def viewer_key(keysym, char=""):
        """영상 창에서 키를 누른 것처럼: r12_viewer.Viewer.on_key 를 그대로 불러 live/keys.in 에 쓴다."""
        import glob
        import types

        sys.path.insert(0, TOOLS)
        import r12_viewer

        live = max(glob.glob("/dev/shm/r12_live_*_preview"), key=os.path.getmtime)
        r12_viewer.Viewer.on_key(types.SimpleNamespace(live=live, KEYMAP=r12_viewer.Viewer.KEYMAP), types.SimpleNamespace(keysym=keysym, char=char))

    def go(ep, from_viewer=False):
        """사람처럼: 검사 통과를 보고 → — 그 사이 영상이 움직여 막히면 다시."""
        for _ in range(6):
            d.wait_safe(60)
            viewer_key("Right") if from_viewer else d.key(RIGHT)
            m = d.wait(rf"안전 조건 통과 — episode {ep}|를 막았어요|녹화를 시작하지 않았어요", 10)
            if "통과" in m.group(0):
                return
        raise TimeoutError("검사 통과 후 → 가 계속 막힘")

    def ok(name):
        results.append(name)
        print(f"  ✓ {name}", flush=True)

    d.wait(r"준비 — 녹화 안 함 · episode 0", 60)
    ok("첫 판 앞 준비 단계 (녹화 안 함)")
    d.sleep(1.0)
    d.key(RIGHT)  # 영상 처음 = 쉬는 자세 (lift 한계 근처 · 그리퍼 닫힘) → 11-02 부터 WARN 만, 막지 않음
    d.wait(r"안전 조건 통과 — episode 0", 10)
    d.wait(r"녹화 중 — episode 0", 10)
    ok("쉬는 자세에서도 → 로 녹화 시작 ep0 (경고만)")
    d.sleep(3.0)
    d.key(RIGHT)
    d.wait(r"episode 0: 기록 \d+ 프레임", 10)
    d.wait(r"결과 입력 — 녹화 안 함", 10)
    ok("ep0 녹화 끝 → 결과 입력 단계")
    d.key(b"2")
    d.wait(r"episode 0 결과: 첫 파지 ✗ · 최종 ✓ · 재시도 1", 5)
    d.key(b"2")
    d.wait(r"재시도 2", 5)
    d.key(b"m")
    d.key("빈 파지 1번 q n r".encode())  # q n r 이 lerobot 으로 새면 종료/다음/다시가 됨 → 새지 않아야 함
    d.key(b"\r")
    d.wait(r"메모 저장: 빈 파지 1번 q n r", 5)
    ok("결과 2·2·메모 입력 (q/n/r 이 lerobot 으로 새지 않음)")
    d.key(RIGHT)  # 4차: 결과 단계 → = 저장 → 준비 단계 (바로 녹화 안 함)
    d.wait(r"저장 완료", 15)
    d.wait(r"준비 — 녹화 안 함 · episode 1", 15)
    d.sleep(0.8)
    assert "녹화 중 — episode 1" not in d.plain[d.mark:]
    go(1)
    d.wait(r"녹화 중 — episode 1", 15)
    ok("결과 단계 → = ep0 저장 → 준비 단계 → → = ep1 녹화")
    d.sleep(2.0)
    d.key(LEFT)
    d.wait(r"이번 판은 버려요", 5)
    d.wait(r"결과 입력 — 녹화 안 함", 10)
    d.key(b"1")
    d.wait(r"결과를 넣을 판이 없어요", 5)
    ok("REC 중 ← → 버리기 예약, 결과 입력 막힘")
    d.key(RIGHT)
    d.wait(r"방금 판을 버렸어요", 10)
    d.wait(r"준비 — 녹화 안 함 · episode 1", 15)
    go(1)
    d.wait(r"녹화 중 — episode 1", 10)
    ok("버린 뒤 같은 번호 ep1 다시 준비 → 녹화")
    d.sleep(2.5)
    d.key(RIGHT)
    d.wait(r"결과 입력 — 녹화 안 함", 10)
    d.key(b"1")
    d.wait(r"episode 1 결과: 첫 파지 ✓ · 최종 ✓ · 재시도 0", 5)
    viewer_key("Right")  # 영상 창의 → 도 결과 단계에서 저장 → 준비
    d.wait(r"준비 — 녹화 안 함 · episode 2", 20)
    go(2, from_viewer=True)
    ok("영상 창에서 누른 → 로 저장·녹화 시작 (keys.in → pty)")
    d.wait(r"녹화 중 — episode 2", 20)
    ok("ep1 결과 1 → 저장 → ep2 (마지막 판)")
    d.sleep(2.5)
    d.key(RIGHT)
    d.wait(r"녹화 종료", 20)
    d.wait(r"episode 2 결과 \[1", 10)
    d.key(b"3\r")
    d.wait(r"메모", 5)
    d.key(b"\r")
    rc_ = d.finish(60)
    ok(f"마지막 판 결과 질문 → 종료 코드 {rc_}")

    sess = os.path.join(root, "runs", "main_k8", "r2_pregrasp_pilot")
    evs = [json.loads(x) for x in open(os.path.join(sess, "r12_attempts.jsonl"))]
    kinds = [e["ev"] for e in evs]
    assert kinds.count("saved") == 3, kinds
    assert kinds.count("discarded") == 1, kinds
    assert kinds.count("blocked") >= 0
    rows = list(csv.DictReader(open(os.path.join(sess, "r12_episodes.csv"))))
    assert [int(r["episode_index"]) for r in rows] == [0, 1, 2], rows
    assert rows[0]["first_grasp_success"] == "False" and rows[0]["final_success"] == "True" and rows[0]["retry_count"] == "2", rows[0]
    assert rows[0]["operator_notes"] == "빈 파지 1번 q n r", rows[0]
    assert rows[1]["first_grasp_success"] == "True" and rows[2]["final_success"] == "False", rows
    for r in rows:
        assert r["start_joint_state"] and r["start_gripper_state"], r  # 그리퍼 닫힘은 11-02 부터 WARN (막지 않음)
        assert int(r["frames"]) > 30, r
    plan = list(csv.DictReader(open(os.path.join(sess, "r12_plan.csv"))))
    assert [p["status"] for p in plan[:4]] == ["recorded", "recorded", "recorded", "planned"], [p["status"] for p in plan[:4]]
    ok("기록 파일: 저장 3 · 버림 1 · r12_episodes.csv 3줄 (결과·메모·시작 관절값·프레임 수) · 계획 상태")
    assert not os.path.exists(os.path.join(sess, "dataset")), "preview 가 dataset 을 만듦"
    log = open(sorted(__import__("glob").glob(os.path.join(root, "logs", "record_*.log")))[-1], errors="replace").read()
    assert "PREVIEW 모드" in log and "Traceback" not in log
    ok("dataset 없음 · 로그에 PREVIEW 모드 · Traceback 없음")
    assert os.path.getmtime(os.path.expanduser("~/so101_runs/main_k8")) == runs_before
    ok("~/so101_runs/main_k8 변화 없음")
    with open(os.path.join(root, "test_preview_flow.txt"), "w") as f:
        f.write(d.plain)
    print(f"PASS {len(results)} 항목 · 기록 {root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
