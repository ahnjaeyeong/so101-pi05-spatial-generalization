#!/home/user/so101-env/bin/python
"""파일럿 12편 Preview 시험 (로봇 없음): 실제 r12_collect.py preview --config config/r12_pilot12.yaml 를 pty 에서 R1 · R2-P · R2-O 그룹마다 실행.
확인: 파일럿 체크리스트 · 시나리오 이름 · 준비 → 녹화 → 결과 → 저장 흐름 (R1 은 → 두 번) · armed 에 code_version · pilot_start 사건 (시작 조건 값 ·
     실패 상태 비슷함) · r12_pilot_episodes.csv (§8 열) · R2-O 의 '그리퍼 닫힘' 이 경고로 뜨지 않음 · dataset 안 만듦 · ~/so101_runs 변화 없음.
그 다음 파일럿 QA: 가짜 장치 dataset (test_pilot12 B 가 만든 것) 을 임시 세션에 놓고 `r12_collect.py qa --config ...` → 보고서 §5 · r12_pilot_qa.csv.

  PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python tests/test_preview_pilot12.py [--root DIR] [--stub-ds DIR]
"""

import csv
import datetime
import glob
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pty_driver import RIGHT, Driver  # noqa: E402

COLL = os.path.dirname(HERE)
TOOLS = os.path.join(COLL, "tools")
CFG = os.path.join(COLL, "config", "r12_pilot12.yaml")
VENV = os.path.expanduser("~/so101-env/bin/python")
RESULTS = []


def ok(name):
    RESULTS.append(name)
    print(f"  ✓ {name}", flush=True)


def run_group(root, group, r1):
    cmd = [VENV, os.path.join(TOOLS, "r12_collect.py"), "preview", "--group", group, "--config", CFG, "--episodes", "2", "--root", root, "--no-viewer"]
    d = Driver(cmd, dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))

    def go(ep):
        for _ in range(8):
            d.wait_safe(60)
            d.key(RIGHT)
            if r1:
                d.wait(r"안전 확인: 탁자", 5)
                d.sleep(0.8)
                d.key(RIGHT)
            m = d.wait(rf"안전 조건 통과 — episode {ep}|를 막았어요|녹화를 시작하지 않았어요", 10)
            if "통과" in m.group(0):
                d.wait(rf"녹화 중 — episode {ep}", 10)
                return
        raise TimeoutError("→ 가 계속 막힘")

    d.wait(r"준비 — 녹화 안 함 · episode 0", 60)
    head = d.plain
    go(0)
    d.sleep(2.0)
    d.key(RIGHT)
    d.wait(r"결과 입력 — 녹화 안 함", 15)
    d.key(b"1")
    d.wait(r"episode 0 결과: 첫 파지 ✓", 5)
    d.key(RIGHT)
    d.wait(r"준비 — 녹화 안 함 · episode 1", 20)
    go(1)
    d.sleep(2.0)
    d.key(RIGHT)
    d.wait(r"녹화 종료", 20)
    d.wait(r"episode 1 결과 \[1", 10)
    d.key(b"2\r")
    d.wait(r"메모", 5)
    d.key(b"\r")
    code = d.finish(60)
    return d.plain, head, code


def main():
    root = sys.argv[sys.argv.index("--root") + 1] if "--root" in sys.argv else f"/tmp/r12_preview_pilot12_{datetime.datetime.now():%Y%m%d_%H%M%S}"
    stub_ds = sys.argv[sys.argv.index("--stub-ds") + 1] if "--stub-ds" in sys.argv else None
    runs_before = os.path.getmtime(os.path.expanduser("~/so101_runs/main_k8"))
    expect = {"pilot12_r1": ("main_k8/r12_pilot12_r1", "R1", "파일럿 R1 = 팔 접힘 지나침", "R1-FOLD-OVER"),
              "pilot12_r2p": ("main_k8/r12_pilot12_r2p", "R2-P", "파일럿 R2-P = 열린 그리퍼", "R2-P-"),
              "pilot12_r2o": ("main_k8/r12_pilot12_r2o", "R2-O", "파일럿 R2-O = 닫힌 그리퍼", "R2-O-REOPEN")}
    for group, (session, var, chk, sid) in expect.items():
        print(f"[{group}]")
        groot = os.path.join(root, group)
        plain, head, code = run_group(groot, group, var == "R1")
        with open(os.path.join(root, f"{group}.txt"), "w") as f:
            f.write(plain)
        assert code == 0, code
        assert chk in plain, f"체크리스트 없음: {chk}"
        ok(f"{var}: 파일럿 체크리스트 · 준비 → 녹화 → 결과 → 저장 2판 · 종료 코드 0")
        sess = os.path.join(groot, "runs", *session.split("/"))
        evs = [json.loads(x) for x in open(os.path.join(sess, "r12_attempts.jsonl"))]
        armed = [e for e in evs if e["ev"] == "armed"]
        ps = [e for e in evs if e["ev"] == "pilot_start"]
        assert len([e for e in evs if e["ev"] == "saved"]) == 2
        assert armed and all(e.get("code_version") for e in armed), armed[:1]
        assert len(ps) >= 2 and all(p["pilot"]["values"].get("pilot_variant") == var for p in ps), ps[:1]
        assert all(p["pilot"]["similarity"]["total"] >= 1 for p in ps)
        ok(f"{var}: armed code_version · pilot_start (시작 조건 값 · 실패 상태 비슷함 {ps[0]['pilot']['similarity']['matched']}/{ps[0]['pilot']['similarity']['total']})")
        rows = list(csv.DictReader(open(os.path.join(sess, "r12_pilot_episodes.csv"))))
        assert len(rows) == 2 and all(r["pilot_variant"] == var and r["scenario_id"].startswith(sid) for r in rows), rows
        need = ["run_id", "start_joint_state", "start_gripper_value", "start_gripper_state", "cube_position", "cube_rotation", "failure_type",
                "correction_action", "first_grasp_success", "valid", "code_version", "config_sha256", "dataset_root"]
        assert all(r[k] != "" for r in rows for k in need), {k: rows[0][k] for k in need}
        assert rows[0]["first_grasp_success"] == "True" and rows[1]["final_success"] == "True" and rows[1]["first_grasp_success"] == "False"
        ok(f"{var}: r12_pilot_episodes.csv 2줄 · §8 열 채워짐 (run_id · 시작 관절 · 그리퍼 · 큐브 · 실패 유형 · 교정 · 결과 · code · config)")
        if var == "R2-O":
            warn_lines = [ln for ln in plain.splitlines() if "그리퍼" in ln and "녹화 시작 뒤 열어도 됨" in ln and "참고" in ln]
            assert not warn_lines, warn_lines[:2]
            assert all(r["gripper_start_expected"] == "closed" for r in rows)
            ok("R2-O: 시작 조건 '그리퍼 닫힘' — 경고(⚠ 참고)로 뜨지 않음")
        if var == "R2-P":
            assert all(r["gripper_start_expected"] == "open" for r in rows)
        assert not os.path.exists(os.path.join(sess, "dataset")), "preview 가 dataset 을 만듦"
        log = open(sorted(glob.glob(os.path.join(groot, "logs", "record_*.log")))[-1], errors="replace").read()
        assert "Traceback" not in log and "Traceback" not in plain
        side = json.load(open(sorted(glob.glob(os.path.join(groot, "logs", "record_*.json")))[-1]))
        assert side.get("teleop_guard") is True and side.get("config_extends_sha256") and side.get("code_version"), side
        ok(f"{var}: dataset 없음 · Traceback 없음 · 실행 기록에 명령 보호 켬 · 설정 sha · 코드 버전")

    # ---- 파일럿 QA (가짜 장치 dataset 을 임시 세션에)
    if stub_ds and os.path.isdir(stub_ds):
        print("[qa]")
        qroot = os.path.join(root, "qa_runs")
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", RECORD_UI_RUNS=qroot, RECORD_UI_LOG_DIR=os.path.join(root, "qa_logs"))
        subprocess.run([VENV, os.path.join(TOOLS, "r12_collect.py"), "plan", "--group", "pilot12_r2o", "--config", CFG], env=env, check=True,
                       capture_output=True)
        sess = os.path.join(qroot, "main_k8", "r12_pilot12_r2o")
        shutil.copytree(stub_ds, os.path.join(sess, "dataset"))
        with open(os.path.join(sess, "r12_attempts.jsonl"), "a") as f:
            for e in ({"ev": "armed", "attempt_id": "qa0", "ep": 0, "run_id": "qa", "state": {}, "code_version": "test"},
                      {"ev": "label", "attempt_id": "qa0", "first_grasp_success": True, "final_success": True, "retry_count": 0},
                      {"ev": "saved", "attempt_id": "qa0", "ep": 0}):
                f.write(json.dumps(e) + "\n")
        r = subprocess.run([VENV, os.path.join(TOOLS, "r12_collect.py"), "qa", "--session", "main_k8/r12_pilot12_r2o", "--config", CFG],
                           env=env, capture_output=True, text=True)
        assert r.returncode == 0, r.stdout[-800:] + r.stderr[-1500:]
        rep = open(os.path.join(sess, "qa", "r12_qa_report.md")).read()
        assert "## 5. 파일럿 12편 QA" in rep, rep[-500:]
        q = list(csv.DictReader(open(os.path.join(sess, "qa", "r12_pilot_qa.csv"))))
        assert len(q) == 1 and q[0]["q8"] == "ok" and q[0]["q7"] in ("ok", "check") and q[0]["q4"] in ("ok", "check"), q
        # 가짜 장치 판은 그리퍼를 연 적이 없어 (시작 28 열림 · 닫힘 없음) R2-O 조건과 다름 → check 여야 함 (성공해도 바로 적합 아님)
        assert q[0]["q1"] == "check" and q[0]["suitability"] != "candidate_needs_review", q[0]
        sync = subprocess.run([VENV, os.path.join(TOOLS, "r12_collect.py"), "sync", "--session", "main_k8/r12_pilot12_r2o", "--config", CFG],
                              env=env, capture_output=True, text=True)
        rows = list(csv.DictReader(open(os.path.join(sess, "r12_pilot_episodes.csv"))))
        assert sync.returncode == 0 and len(rows) == 1 and rows[0]["video_front"].startswith("videos/observation.images.front/"), rows
        ok(f"파일럿 QA: 보고서 §5 · r12_pilot_qa.csv (Q1 {q[0]['q1']} · Q4 {q[0]['q4']} · Q5 {q[0]['q5']} · Q7 {q[0]['q7']} · Q8 {q[0]['q8']} · 분류 {q[0]['suitability']})"
           f" · sync 뒤 영상 위치 열 ({rows[0]['video_front']})")
    else:
        print("  · --stub-ds 없음 — 파일럿 QA 시험 건너뜀")
    assert os.path.getmtime(os.path.expanduser("~/so101_runs/main_k8")) == runs_before
    ok("~/so101_runs/main_k8 변화 없음")
    print(f"PASS {len(RESULTS)} 항목 · 기록 {root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
