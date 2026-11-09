#!/home/user/so101-env/bin/python
"""SG50 preview 흐름 시험 (로봇 · 카메라 · lerobot 없음): r12_collect.py preview --config config/sg50.yaml --group sg50_pilot 을
pty 에서 실행하고 키를 보낸 뒤, 화면 (sg_viewer.Screen, 창 없이) · 기록 파일 (r12_episodes.csv · sg_episodes.csv · sg_plan.csv) 을 확인한다.

  PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python tests/test_sg_preview.py [--root DIR]
"""

import csv
import datetime
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pty_driver import RIGHT, Driver  # noqa: E402

ROOTDIR = os.path.dirname(HERE)
TOOLS = os.path.join(ROOTDIR, "tools")
VENV = os.path.expanduser("~/so101-env/bin/python")
CFG = os.path.join(ROOTDIR, "config", "sg50.yaml")


def main():
    root = sys.argv[sys.argv.index("--root") + 1] if "--root" in sys.argv else f"/tmp/sg_preview_test_{datetime.datetime.now():%Y%m%d_%H%M%S}"
    runs_before = os.path.getmtime(os.path.expanduser("~/so101_runs/main_k8"))
    cmd = [VENV, os.path.join(TOOLS, "r12_collect.py"), "preview", "--config", CFG, "--group", "sg50_pilot", "--episodes", "2",
           "--root", root, "--no-viewer"]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    d = Driver(cmd, env)
    results = []

    def ok(name):
        results.append(name)
        print(f"  ✓ {name}", flush=True)

    d.wait(r"준비 — 녹화 안 함 · episode 0", 90)
    ok("첫 판 앞 준비 단계 (녹화 안 함)")
    live = max(glob.glob("/dev/shm/r12_live_*_preview"), key=os.path.getmtime)
    sys.path.insert(0, TOOLS)
    os.environ["R12_CONFIG"] = CFG
    os.environ["RECORD_UI_RUNS"] = os.path.join(root, "runs")
    import sg_viewer

    scr = sg_viewer.Screen(live)
    d.sleep(2.0)
    scr.poll()
    ui = scr.ui
    assert ui.get("state") == "SETUP" and (ui.get("row") or {}).get("scenario_id") in ("SG-P0", "SG-FREE", "SG-S0"), ui.get("row")
    im = scr.render(1400, 860)
    im.save(os.path.join(root, "screen_setup_1400.png"))
    ok(f"준비 단계 화면: 상태 SETUP · 시나리오 SG-P0 · 큐브 {(ui.get('row') or {}).get('position')} · 그림 {im.size}")
    d.key(RIGHT)
    d.wait(r"녹화 중 — episode 0", 15)
    d.sleep(2.0)
    for _ in range(10):
        scr.poll()
        d.sleep(0.1)
    assert scr.st.get("phase") == "rec", scr.st.get("phase")
    assert scr.health.seq_t is not None and not scr.health.stale(__import__("time").time()), "녹화 중 영상이 오래됨"
    im = scr.render(1000, 620)
    im.save(os.path.join(root, "screen_rec_1000.png"))
    ok(f"녹화 중 화면 (실제 공유 메모리 프레임, 1000×620): 검출 상태 {scr.det['status'] if scr.det else None}")
    d.sleep(1.5)
    d.key(RIGHT)
    d.wait(r"판 끝 — 녹화 안 함", 15)  # result_entry: false (2026-11-06) — 1·2·3 결과 입력 없음
    d.key(b"2")
    d.wait(r"결과 입력을 쓰지 않아요", 5)
    d.key(b"m")
    d.key("재정렬 1번".encode())
    d.key(b"\r")
    d.wait(r"메모 저장: 재정렬 1번", 5)
    ok("ep0 판 끝: 결과 키 2 → '결과 입력 안 씀' 안내만 · 메모 m 은 됨")
    d.key(RIGHT)
    d.wait(r"준비 — 녹화 안 함 · episode 1", 20)
    d.sleep(1.0)
    for _ in range(6):
        d.wait_safe(60)
        d.key(RIGHT)
        m = d.wait(r"안전 조건 통과 — episode 1|를 막았어요|녹화를 시작하지 않았어요", 10)
        if "통과" in m.group(0):
            break
    d.wait(r"녹화 중 — episode 1", 20)
    d.sleep(2.5)
    d.key(RIGHT)
    d.wait(r"녹화 종료", 20)
    code = d.finish(90)
    assert "결과 [1" not in d.plain, "마지막 판 결과를 물음"
    ok(f"ep1 → 끝 (마지막 판 결과 묻지 않음) · 종료 코드 {code}")

    sess = os.path.join(root, "runs", "practice", "sg50_pilot")
    eps = list(csv.DictReader(open(os.path.join(sess, "r12_episodes.csv"))))
    assert len(eps) == 2, eps
    sge = list(csv.DictReader(open(os.path.join(sess, "sg_episodes.csv"))))
    assert len(sge) == 2, sge
    a, b = sge
    assert (a["start_pose_id"], b["start_pose_id"]) in (("P0", "P1"), ("FREE", "FREE"), ("S0", "S0")), (a["start_pose_id"], b["start_pose_id"])
    assert a["grasp_outcome"] == "" and a["regrasp_or_realign"] == "" and a["operator_notes"] == "재정렬 1번", a
    assert b["grasp_outcome"] == "" and b["regrasp_or_realign"] == "", b
    assert a["start_joint_state"].startswith("pan=") and (a["start_pose_id"] == "FREE" or a["start_pose_max_abs_dev_deg"] != ""), a
    assert a["cube_rotation_planned"] == "0" and a["cube_position"] == "K2" and b["cube_position"] == "K7", (a, b)
    assert a["follower_calib_sha"] and a["front_H_sha"] and a["calib_source"] == "녹화 시작 때 기록", a
    assert a["split"] == "train_candidate" and a["episode_id"], a
    ok(f"sg_episodes.csv 2줄: 자세 P0/P1 · 결과 칸 비움 (입력 안 씀) · 메모 · 시작 관절 · 보정 해시 · split (P0 최대 차이 {a['start_pose_max_abs_dev_deg']}°)")
    plan = list(csv.DictReader(open(os.path.join(sess, "sg_plan.csv"))))
    assert [p["start_pose_id"] for p in plan] in (["P0", "P1", "P2", "P3"], ["FREE"] * 4, ["S0"] * 4), plan
    assert os.path.exists(os.path.join(sess, "sg_plan.md"))
    ok("sg_plan.csv · sg_plan.md (예비 4편 = 자세 4 가지)")
    side = json.load(open(sorted(glob.glob(os.path.join(root, "logs", "record_*.json")))[-1]))
    assert side.get("sg50_calib", {}).get("front_H_sha"), side.keys()
    ok("실행 sidecar 에 보정 해시 (sg50_calib)")
    assert not os.path.exists(os.path.join(sess, "dataset")), "preview 가 dataset 을 만듦"
    log = open(sorted(glob.glob(os.path.join(root, "logs", "record_*.log")))[-1], errors="replace").read()
    assert "Traceback" not in log
    assert os.path.getmtime(os.path.expanduser("~/so101_runs/main_k8")) == runs_before
    ok("dataset 없음 · Traceback 없음 · ~/so101_runs/main_k8 변화 없음")
    leftover = [w for w in ("R2 준비", "닫기 영역", "R1 =", "R2 =", "주황 ✕", "Pan 목표") if w in d.plain]
    assert not leftover, leftover
    ok("터미널 배너에 R1/R2 안내 문구 없음 (R2 준비 · 닫기 영역 · Pan 목표 …)")
    with open(os.path.join(root, "test_sg_preview.txt"), "w") as f:
        f.write(d.plain)
    print(f"PASS {len(results)} 항목 · 기록 {root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
