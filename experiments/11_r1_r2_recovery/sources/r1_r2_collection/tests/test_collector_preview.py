#!/home/user/so101-env/bin/python
"""수집자 모드 Preview 시험 + 기록 주기 측정 (로봇 없음 · Fake Robot = r12_fake_record.py, 기존 녹화 재생).

실제 `r12_collect.py preview --group pilot12_r2p --config config/r12_pilot12.yaml --episodes 2` 를 pty 에서 세 번:
  none      = 영상 창 없음 (--no-viewer)
  collector = 영상 창 수집자 모드 (기본)
  debug     = 영상 창 디버그 모드 (viewer_cmd.json F4)
  결과 단계: 1 · 마지막 판 터미널 결과 1 (collector 는 2) / 메모 Enter. 학습 판정 (g/e/v) 은 11-04 삭제 — 묻지 않는지 확인.
판마다 녹화 REC_S 초. 확인: 녹화 · 결과 · 저장 흐름 (기존과 같음) · 판정 사건 · 판정 질문 없음 ·
  rec_end 기록 주기 (loop_hz_mean · late_ticks) 세 경우 비교 · 영상 창 한 번 그리기 시간 (viewer_perf.json) · 영상 창 오류 없음 · ~/so101_runs 안 바뀜.

  PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python tests/test_collector_preview.py [--root DIR] [--rec 12]
"""

import csv
import datetime
import glob
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pty_driver import RIGHT, Driver, latest_live  # noqa: E402

COLL = os.path.dirname(HERE)
TOOLS = os.path.join(COLL, "tools")
CFG = os.path.join(COLL, "config", "r12_pilot12.yaml")
VENV = os.path.expanduser("~/so101-env/bin/python")
OK = []


def check(name, cond, detail=""):
    print(f"  {'✓' if cond else '✗'} {name} {detail}", flush=True)
    OK.append(bool(cond))


GROUP = sys.argv[sys.argv.index("--group") + 1] if "--group" in sys.argv else "pilot12_r2p"
if "--config" in sys.argv:
    CFG = os.path.abspath(sys.argv[sys.argv.index("--config") + 1])
MODES = sys.argv[sys.argv.index("--modes") + 1].split(",") if "--modes" in sys.argv else ["none", "collector", "debug"]


def session_of(group):
    import yaml

    return yaml.safe_load(open(CFG))["groups"][group]["session"]


def run(root, mode, rec_s):
    cmd = [VENV, os.path.join(TOOLS, "r12_collect.py"), "preview", "--group", GROUP, "--config", CFG, "--episodes", "2", "--root", root,
           "--scale", "0.8"] + (["--no-viewer"] if mode == "none" else [])
    t_start = time.time()
    d = Driver(cmd, dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    d.wait(r"준비 — 녹화 안 함 · episode 0", 90)
    live = None
    if mode != "none":
        for _ in range(100):
            live = latest_live()
            if live and os.path.getmtime(live) >= t_start - 1 and os.path.exists(os.path.join(live, "viewer_ready.json")):
                break
            d.sleep(0.2)
        if mode == "debug":
            with open(os.path.join(live, "viewer_cmd.json"), "w") as f:
                json.dump({"keys": ["F4"]}, f)
        d.sleep(1.0)

    def go(ep):
        for _ in range(8):
            d.wait_safe(60)
            d.key(RIGHT)
            m = d.wait(rf"안전 조건 통과 — episode {ep}|를 막았어요|녹화를 시작하지 않았어요", 10)
            if "통과" in m.group(0):
                d.wait(rf"녹화 중 — episode {ep}", 10)
                return
        raise TimeoutError("→ 가 계속 막힘")

    go(0)
    d.sleep(rec_s)
    d.key(RIGHT)
    d.wait(r"결과 입력 — 녹화 안 함", 20)
    d.key(b"1")
    d.wait(r"episode 0 결과: 첫 파지 ✓", 5)
    d.sleep(1.5)  # 결과 단계 화면 (영상 창) 이 그려질 시간
    d.key(RIGHT)
    d.wait(r"준비 — 녹화 안 함 · episode 1", 30)
    go(1)
    d.sleep(rec_s)
    d.key(RIGHT)
    d.wait(r"녹화 종료", 30)
    d.wait(r"episode 1 결과 \[1", 15)
    d.key({"collector": b"2\r"}.get(mode, b"1\r"))
    d.wait(r"메모", 5)
    d.key(b"\r")
    perf = None
    if live:
        perf = json.load(open(os.path.join(live, "viewer_perf.json"))) if os.path.exists(os.path.join(live, "viewer_perf.json")) else None
        vlog = open(os.path.join(live, "viewer.log")).read() if os.path.exists(os.path.join(live, "viewer.log")) else ""
    else:
        vlog = ""
    code = d.finish(90)
    sess = os.path.join(root, "runs", *session_of(GROUP).split("/"))
    evs = [json.loads(x) for x in open(os.path.join(sess, "r12_attempts.jsonl"))]
    rows = list(csv.DictReader(open(os.path.join(sess, "r12_pilot_episodes.csv"))))
    return code, d.plain, evs, rows, perf, vlog


def main():
    root = sys.argv[sys.argv.index("--root") + 1] if "--root" in sys.argv else f"/tmp/r12_collector_preview_{datetime.datetime.now():%Y%m%d_%H%M%S}"
    rec_s = float(sys.argv[sys.argv.index("--rec") + 1]) if "--rec" in sys.argv else 12.0
    if not os.environ.get("DISPLAY"):
        print("DISPLAY 없음 — 영상 창 시험 불가")
        return 2
    runs_mt = os.path.getmtime(os.path.expanduser("~/so101_runs/main_k8"))
    r2p_mt = max(os.path.getmtime(p) for p in glob.glob(os.path.expanduser("~/so101_runs/main_k8/r12_pilot12_r2p/**"), recursive=True))
    rc_real = os.path.expanduser("~/so101_runs/" + session_of(GROUP))
    rc_existed = os.path.exists(rc_real)
    summ = {}
    for mode in MODES:
        print(f"[{mode}]")
        code, plain, evs, rows, perf, vlog = run(os.path.join(root, mode), mode, rec_s)
        with open(os.path.join(root, f"{mode}.txt"), "w") as f:
            f.write(plain)
        saved = [e for e in evs if e["ev"] == "saved"]
        re_ = [e for e in evs if e["ev"] == "rec_end"]
        ov = [e for e in evs if e["ev"] in ("operator_verdict", "auto_verdict")]
        check(f"{mode}: 준비 → 녹화 → 결과 → 저장 2판 · 종료 코드 0", code == 0 and len(saved) == 2, f"code {code}")
        check(f"{mode}: 학습 판정 없음 — 판정 사건 0 · 터미널이 판정을 묻지 않음 · CSV 판정 열 없음",
              not ov and "학습 판정" not in plain and "operator_verdict" not in (rows[0] if rows else {}), str(ov[:1]))
        check(f"{mode}: 결과 입력은 그대로 (r12_pilot_episodes first_grasp_success)", rows and rows[0]["first_grasp_success"] == "True", str([r["first_grasp_success"] for r in rows]))
        if mode != "none":
            check(f"{mode}: 영상 창 오류 없음 (viewer.log)", "Traceback" not in vlog and "Error" not in vlog, vlog[-200:])
            mm = "collector" if mode == "collector" else "debug"
            check(f"{mode}: 영상 창이 {mm} 모드로 그림 (viewer_perf.json)", bool(perf and perf.get(mm)), json.dumps(perf, ensure_ascii=False)[:200])
        summ[mode] = {"loop_hz_mean": [e.get("loop_hz_mean") for e in re_], "late_ticks": [e.get("late_ticks") for e in re_],
                      "frames": [e.get("frames") for e in re_], "stall_ticks": [e.get("stall_ticks") for e in re_], "viewer_perf": perf}
    print("\n기록 주기 (rec_end, Fake Robot · 목표 30 Hz):")
    for m, s in summ.items():
        print(f"  {m:10s} Hz {s['loop_hz_mean']} · 늦은 틱 {s['late_ticks']} · 프레임 {s['frames']} · 카메라 반복 {s['stall_ticks']}"
              + (f" · 영상 창 {json.dumps({k: v for k, v in (s['viewer_perf'] or {}).items() if k in ('collector', 'debug', 'scale', 'size')}, ensure_ascii=False)}"
                 if s["viewer_perf"] else ""))
    hz = {m: min(x for x in s["loop_hz_mean"] if x is not None) for m, s in summ.items()}
    check("기록 주기: 영상 창 (수집자 · 디버그) 이 있어도 30 Hz 의 95 % 이상" + (" · 창 없을 때와 차이 ≤ 0.5 Hz" if "none" in hz and "collector" in hz else ""),
          all(h >= 28.5 for h in hz.values()) and ("none" not in hz or "collector" not in hz or abs(hz["collector"] - hz["none"]) <= 0.5), str(hz))
    check(f"실제 세션 폴더 {session_of(GROUP)} 를 만들지 않음 (preview 는 --root 아래에만)", os.path.exists(rc_real) == rc_existed)
    check("~/so101_runs/main_k8 · 실물 R2-P 세션 안 바뀜 (preview 는 --root 아래에만)",
          os.path.getmtime(os.path.expanduser("~/so101_runs/main_k8")) == runs_mt and
          max(os.path.getmtime(p) for p in glob.glob(os.path.expanduser("~/so101_runs/main_k8/r12_pilot12_r2p/**"), recursive=True)) == r2p_mt)
    with open(os.path.join(root, "summary.json"), "w") as f:
        json.dump(summ, f, ensure_ascii=False, indent=1)
    print(("PASS" if all(OK) else "FAIL") + f" {sum(OK)}/{len(OK)} · {root}")
    return 0 if all(OK) else 1


if __name__ == "__main__":
    sys.exit(main())
