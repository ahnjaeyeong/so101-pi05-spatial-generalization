#!/home/user/so101-env/bin/python
"""R1 Preview 흐름 시험 (로봇 없음, 4차 지시서 R1-A/B1/B2/B3): 실제 r12_collect.py preview --type R1 을 pty 에서 실행하고 키를 보낸 뒤 기록을 확인한다.

  ~/so101-env/bin/python tests/test_preview_r1.py [--root DIR]
확인: 4 시나리오 (A·B1·B2·B3) 를 한 판씩 녹화 시작 → 저장 · 준비 단계 → 한 번은 녹화 안 함 (안전 확인), 두 번째 → 로 녹화 ·
     결과 단계 → = 저장 뒤 준비 단계 (바로 녹화하지 않음) · s/d/k/x 다음 판 바꾸기 (계획 반영·수량 그대로) · p 다시 보기 · 결과 4 ·
     판 끝 R1 복구 측정 사건 · r12_episodes.csv R1 메타데이터 · dataset 없음 · ~/so101_runs 변화 없음.
"""

import collections
import csv
import datetime
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pty_driver import RIGHT, Driver  # noqa: E402

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools")
VENV = os.path.expanduser("~/so101-env/bin/python")


def main():
    root = sys.argv[sys.argv.index("--root") + 1] if "--root" in sys.argv else \
        f"/tmp/r12_preview_r1_{datetime.datetime.now():%Y%m%d_%H%M%S}"
    runs_before = os.path.getmtime(os.path.expanduser("~/so101_runs/main_k8"))
    cmd = [VENV, os.path.join(TOOLS, "r12_collect.py"), "preview", "--type", "R1", "--episodes", "4", "--root", root, "--no-viewer"]
    d = Driver(cmd, dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    results = []
    sess = os.path.join(root, "runs", "main_k8", "r1_realign_pilot")

    def ok(name):
        results.append(name)
        print(f"  ✓ {name}", flush=True)

    def live():
        return max(glob.glob("/dev/shm/r12_live_*_preview"), key=os.path.getmtime)

    def plan():
        return list(csv.DictReader(open(os.path.join(sess, "r12_plan.csv"))))

    def go(ep):
        """준비 단계: → (안전 확인 문구, 녹화 안 함) → → (녹화). 재생 영상 때문에 안전 조건 BLOCK 이면 다시."""
        for _ in range(8):
            d.wait_safe(60)
            d.key(RIGHT)
            d.wait(r"안전 확인: 탁자", 5)
            d.sleep(0.8)
            assert f"녹화 중 — episode {ep}" not in d.plain[d.mark:], "→ 한 번에 녹화가 시작됨"
            d.key(RIGHT)
            m = d.wait(rf"안전 조건 통과 — episode {ep}|를 막았어요|녹화를 시작하지 않았어요", 10)
            if "통과" in m.group(0):
                d.wait(rf"녹화 중 — episode {ep}", 10)
                return
        raise TimeoutError("안전 조건 통과 후 → 가 계속 막힘")

    def finish_rec(ep, secs):
        d.sleep(secs)
        d.key(RIGHT)
        d.wait(r"R1 복구 \(대략\)", 10)  # rec_end 때 (결과 단계 배너보다 먼저)
        d.wait(r"결과 입력 — 녹화 안 함", 10)

    def next_setup(ep):
        """결과 단계 → = 저장 → 준비 단계 (녹화 안 함)."""
        d.key(RIGHT)
        d.wait(r"저장 완료", 20)
        d.wait(rf"준비 — 녹화 안 함 · episode {ep}", 20)
        d.sleep(0.8)
        assert f"녹화 중 — episode {ep}" not in d.plain[d.mark:], "결과 단계 → 뒤 바로 녹화가 시작됨"

    d.wait(r"준비 — 녹화 안 함 · episode 0", 60)
    d.wait(r"R1 = Pan 재탐색·재정렬", 5)
    ok("R1 준비 단계: 시나리오·큐브 자리·단계·Pan 오차(후보)·손목·바꾸기 키 안내")
    d.sleep(1.0)
    before = collections.Counter(r["scenario_id"] for r in plan())
    sid0 = plan()[0]["scenario_id"]
    for _ in range(4):  # 시나리오 4개를 한 바퀴 → 처음 시나리오로 돌아옴 (뒤쪽 줄과 맞바꿈, 수량 그대로)
        d.key(b"s")
        d.wait(r"계획 바꿈 — episode 0", 5)
    p = plan()
    assert collections.Counter(r["scenario_id"] for r in p) == before and p[0]["scenario_id"] == sid0, (before, [r["scenario_id"] for r in p[:4]])
    dir0 = p[0]["pan_error_direction"]
    d.key(b"d")
    d.wait(r"오차 방향 바꿈", 5)
    assert plan()[0]["pan_error_direction"] != dir0
    pos0 = plan()[0]["position"]
    d.key(b"k")
    d.wait(rf"큐브 자리 {pos0} →", 5)
    p0 = plan()[0]
    assert p0["position"] != pos0 and abs(float(p0["pan_target_deg"]) - float(p0["pan_offset_deg"]) - __import__("r12_common_shim").ref(p0["position"])) < 0.06
    ok("s ×4 (시나리오 한 바퀴, 시나리오별 수량 그대로) · d 방향 · k 자리 → 계획 파일 반영")
    go(0)
    ok("준비 → 한 번 = 안전 확인 (녹화 안 함) · 두 번째 → = 녹화 ep0")
    finish_rec(0, 3.0)
    ok("ep0 끝 → 결과 단계 + R1 복구 측정 (준비 때 움직임 · 첫 이동 · 반전 · 손목)")
    d.key(b"p")
    d.wait(r"이전 판 episode 0 \(저장 대기\)", 5)
    import numpy as np

    lj = json.load(open(os.path.join(live(), "last_episode.json")))
    arr = np.load(os.path.join(live(), "last_episode.npy"))
    assert lj["ep"] == 0 and arr.shape[1:] == (2, 120, 160, 3) and len(lj["pan"]) == lj["frames"], (lj["ep"], arr.shape)
    d.key(b"4")
    d.wait(r"episode 0 결과: 첫 파지 ✗ · 최종 ✗ · 재시도 0 · 재정렬 ✓", 5)
    ok("p 다시 보기 · 결과 4 (재정렬 O · 파지 실패)")
    next_setup(1)
    ok("결과 단계 → = 저장 뒤 준비 단계 (바로 녹화 안 함)")
    d.key(b"x")
    m = d.wait(r"front 검출 X\(|검출되지 않아", 5)
    ok("x = front 검출 자리 (" + ("검출됨" if "X(" in m.group(0) else "검출 없음 → 안내") + ")")
    go(1)
    finish_rec(1, 2.5)
    d.key(b"1")
    d.wait(r"episode 1 결과: 첫 파지 ✓", 5)
    next_setup(2)
    go(2)
    finish_rec(2, 2.5)
    d.key(b"3")
    d.wait(r"episode 2 결과: 첫 파지 ✗ · 최종 ✗ · 재시도 0 · 재정렬 ✗", 5)
    next_setup(3)
    go(3)
    d.sleep(2.5)
    d.key(RIGHT)
    d.wait(r"녹화 종료", 20)
    d.wait(r"episode 3 결과 \[1 .*4 재정렬 O", 10)
    d.key(b"2\r")
    d.wait(r"메모", 5)
    d.key(b"\r")
    rc_ = d.finish(60)
    assert rc_ == 0, rc_
    ok("4판 녹화·저장 → 종료 코드 0")

    evs = [json.loads(x) for x in open(os.path.join(sess, "r12_attempts.jsonl"))]
    kinds = collections.Counter(e["ev"] for e in evs)
    assert kinds["saved"] == 4 and kinds["safety_confirmed"] == 4 and kinds["recovery"] >= 4 and kinds["override"] >= 6, kinds  # s×4·d·k (x 는 front 검출이 될 때만)
    assert not any("error" in e for e in evs if e["ev"] == "recovery"), [e for e in evs if e["ev"] == "recovery" and "error" in e]
    rows = list(csv.DictReader(open(os.path.join(sess, "r12_episodes.csv"))))
    assert sorted(r["scenario_id"] for r in rows) == ["R1-A", "R1-B1", "R1-B2", "R1-B3"], [r["scenario_id"] for r in rows]
    ok("시나리오 4개 (A·B1·B2·B3) 각 1판 저장")
    for r in rows:
        for k in ("approach_stage_at_start", "start_pan_deg", "measured_start_pan_error_deg", "pan_reference_source", "cube_position_source",
                  "cube_xy_cm_used", "wrist_cube_visibility", "front_cube_visibility", "first_pan_move_dir", "pan_reversal",
                  "cube_reacquired_in_wrist" if r["wrist_cube_visibility"] == "absent" else "first_pan_move_deg", "start_safety_confirmed", "episode_id"):
            assert r[k] not in ("",), (k, r)
        assert r["dataset_group"] == "R1" and r["start_safety_confirmed"] == "yes" and r["recording_fps"] == "30", r
    assert rows[0]["scenario_override"] and rows[0]["recovery_completed"] == "yes" and rows[2]["recovery_completed"] == "no", \
        [(x["scenario_override"], x["recovery_completed"]) for x in rows]
    ok("r12_episodes.csv R1 메타데이터 (시작 Pan·단계·자리 출처·가시성·첫 이동·반전·재획득·재분류·안전 확인·재정렬)")
    assert not os.path.exists(os.path.join(sess, "dataset")), "preview 가 dataset 을 만듦"
    log = open(sorted(glob.glob(os.path.join(root, "logs", "record_*.log")))[-1], errors="replace").read()
    assert "PREVIEW 모드" in log and "Traceback" not in log
    assert os.path.getmtime(os.path.expanduser("~/so101_runs/main_k8")) == runs_before
    ok("dataset 없음 · Traceback 없음 · ~/so101_runs/main_k8 변화 없음")
    with open(os.path.join(root, "test_preview_r1.txt"), "w") as f:
        f.write(d.plain)
    print(f"PASS {len(results)} 항목 · 기록 {root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
