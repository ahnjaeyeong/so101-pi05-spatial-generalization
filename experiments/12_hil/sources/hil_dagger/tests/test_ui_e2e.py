"""화면 e2e 시험 — 가짜 장치 실행 (run_all.sh) 의 tap 기록 (tap_log.jsonl) 을 가짜 장치의 실제 기록 (raw.json) 과 맞춰 본다.
사용: python test_ui_e2e.py [_out]  → _out/UI_E2E.md

E1 tap 기록 주기 (중앙값 ≤ 0.15 s) · SIMULATION 표시 (sim=True)
E2 화면 '사람 제어 준비 완료' 순간: 가짜 리더 토크 켜짐 · 그 전후 0.12 s 리더 이동 명령 없음 · 정지 시작 뒤 정책 명령 0
E3 화면 '사람 교정 중' 순간: 가짜 리더 토크 꺼짐 (사람이 움직이는 상태) · 정책 명령 0 (그 순간 앞뒤 0.1 s)
E4 전환 중 (in_transition) 샘플에서 '사람 제어 가능' 0
E5 오류 (S12): '오류로 잠김' 표시, 오류 뒤 '정책 실행 중' 0
E6 종료 메뉴: S16 (터미널) 에서 '종료 선택' 표시 · S14 (follower 오류) 종료 선택지에 home 없음
E7 결과 칸 = hil_qa 결과 (유형 · 복구 · 첫 파지 · 최종 · 제외 사유)
E8 화면 프로세스가 죽어도 (S17) 세션 정상 진행 · 검사 통과
E9 tap 오류 (S18): tap 만 멈추고 세션 정상 · 검사 통과
E10 화면 (headless) 프로세스 오류 없음 · 그리기 시간
"""

import csv
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H.parent / "tools"))
import hil_ui_state as U  # noqa: E402

root = Path(sys.argv[1] if len(sys.argv) > 1 else H / "_out")
lines = ["# 화면 e2e 시험 (test_ui_e2e.py 자동 생성)", ""]
ok_all = True


def chk(scen, name, cond, detail=""):
    global ok_all
    ok_all &= bool(cond)
    s = f"{'PASS' if cond else 'FAIL'} {scen} {name} {detail}"
    print(s)
    lines.append("- " + s)


def at(events, t, kind_on, kind_off):
    st = None
    for e in events:
        if e["t"] > t:
            break
        if e["kind"] == kind_on:
            st = True
        elif e["kind"] == kind_off:
            st = False
    return st


for sdir in sorted(p for p in root.iterdir() if (p / "tap_log.jsonl").exists()):
    scen = sdir.name
    raw = json.loads((sdir / "raw.json").read_text())
    t0 = raw["rec_t0"]
    taps = [json.loads(x) for x in (sdir / "tap_log.jsonl").read_text().splitlines() if x.strip()]
    for s in taps:
        s["ft"] = s["t"] - t0
        s["ui"] = U.derive(s, s["t"])
    W = [w for w in raw["follower_writes"] if w.get("kind") == "write"]
    pw = [w for w in W if w["origin"] == "policy"]
    L = raw["leader_events"]
    E = raw["engine_events"]
    dts = np.diff([s["t"] for s in taps]) if len(taps) > 1 else np.array([9.0])
    tap_off = scen.startswith("S18")  # S18 은 tap 을 일부러 멈춤 → E1 · E7 해당 없음 (E9 로 확인)
    if not tap_off:
        chk(scen, "E1_tap_rate_and_sim_label", len(taps) >= 20 and float(np.median(dts)) <= 0.15 and all(s.get("sim") for s in taps),
            f"samples {len(taps)} · median interval {np.median(dts):.3f} s · max {dts.max():.3f} s")
    bad_ready, bad_corr = [], []
    for s in taps:
        code, ft = s["ui"]["code"], s["ft"]
        if code == "HUMAN_READY":
            lt = at(L, ft, "torque_on", "torque_off")
            moving = [e for e in L if e["kind"] == "goal" and ft - 0.12 < e["t"] <= ft + 0.12]
            ps = [e["t"] for e in E if e["kind"] == "pause" and e["t"] <= ft]
            pol = [w for w in pw if ps and ps[-1] < w["t"] <= ft]
            if lt is not True or moving or pol:
                bad_ready.append((round(ft, 2), lt, len(moving), len(pol)))
        if code == "CORRECTING":
            lt = at(L, ft, "torque_on", "torque_off")
            pol = [w for w in pw if ft - 0.1 < w["t"] <= ft + 0.1]
            if lt is not False or pol:
                bad_corr.append((round(ft, 2), lt, len(pol)))
    n_ready = sum(1 for s in taps if s["ui"]["code"] == "HUMAN_READY")
    n_corr = sum(1 for s in taps if s["ui"]["code"] == "CORRECTING")
    chk(scen, "E2_human_ready_matches_device", not bad_ready, f"HUMAN_READY samples {n_ready} · mismatches {bad_ready[:3]}")
    chk(scen, "E3_correcting_matches_device", not bad_corr, f"CORRECTING samples {n_corr} · mismatches {bad_corr[:3]}")
    tr_bad = [s for s in taps if s.get("in_transition") and s["ui"]["human_control_ok"]]
    chk(scen, "E4_no_human_control_during_transition", not tr_bad,
        f"in_transition samples {sum(1 for s in taps if s.get('in_transition'))} · shown as human-control {len(tr_bad)}")
    codes = [s["ui"]["code"] for s in taps]
    seq = [c for i, c in enumerate(codes) if i == 0 or c != codes[i - 1]]
    lines.append(f"  - {scen} 화면 상태 순서: {' → '.join(seq)}")
    evs = [json.loads(x) for x in (sdir / "hil_events.jsonl").read_text().splitlines()]
    if scen.startswith("S12"):
        lat = [e["perf"] - t0 for e in evs if e["kind"] == "policy_fault"]
        after = [s for s in taps if lat and s["ft"] > lat[0] and s["ui"]["code"] == "POLICY_RUNNING"]
        chk(scen, "E5_fault_locked_shown_no_running_after", "FAULT_LOCKED" in codes and not after,
            f"FAULT_LOCKED samples {codes.count('FAULT_LOCKED')} · POLICY_RUNNING after fault {len(after)}")
    if scen.startswith("S16"):
        em = [s for s in taps if s["ui"]["code"] == "END_MENU"]
        chk(scen, "E6_end_menu_shown_terminal", em and em[0]["end_menu"]["options"] == ["home", "release", "hold"], f"END_MENU samples {len(em)}")
    if scen.startswith("S14"):
        ch = [e for e in evs if e["kind"] == "end_choice"]
        chk(scen, "E6b_follower_fault_menu_without_home", ch and "home" not in ch[-1]["options"] and ch[-1]["follower_ok"] is False, str(ch[-1]["options"] if ch else None))
    # E7 결과 칸 vs hil_qa
    if (sdir / "dataset").exists() and not tap_off:
        subprocess.run([sys.executable, str(H.parent / "tools/hil_qa.py"), str(sdir)], check=True, capture_output=True)
        qa = {int(r["episode"]): r for r in csv.DictReader(open(sdir / "qa/hil_qa.csv"))}
        ui_eps = {}
        for s in taps:
            ls = s.get("last_saved")
            if ls and ls.get("episode") is not None:
                ui_eps[int(ls["episode"])] = U.result_from_marks(ls["marks"], frames=ls.get("frames"), ended_during_correction=ls.get("ended_during_correction"))
        mism = []
        for ep, r in ui_eps.items():
            q = qa.get(ep)
            if q is None:
                mism.append((ep, "no QA row"))
                continue
            ui_t = (r["type"] or "미입력", "예" if r["recovery_done"] else "미입력", r["first_grasp"] or "미입력", r["final"] or "미입력",
                    " · ".join(r["exclusion"]))
            qa_t = (q["type"], q["recovery_done"], q["first_grasp"], q["final_task"], q["변환_제외_사유"])
            if ui_t != qa_t:
                mism.append((ep, ui_t, qa_t))
        chk(scen, "E7_result_panel_equals_qa", ui_eps and not mism, f"episodes {sorted(ui_eps)} · mismatches {mism[:2]}")
    res = json.loads((sdir / "result.json").read_text()) if (sdir / "result.json").exists() else None
    if scen.startswith("S17"):
        killed = [o for o in raw["ops"] if o["kind"] == "viewer_killed"]
        chk(scen, "E8_viewer_killed_session_ok", killed and raw["err"].get("main") is None and res and all(c["pass"] for c in res["checks"].values()),
            f"killed at phase {killed[0].get('phase') if killed else None} · checks {sum(c['pass'] for c in res['checks'].values()) if res else 0}/{len(res['checks']) if res else 0}")
    if scen.startswith("S18"):
        dis = [e for e in evs if e["kind"] == "tap_disabled"]
        chk(scen, "E9_tap_fault_isolated", dis and raw["err"].get("main") is None and res and all(c["pass"] for c in res["checks"].values()),
            f"tap_disabled after {dis[0]['iterations'] if dis else None} iterations · checks {sum(c['pass'] for c in res['checks'].values()) if res else 0}/{len(res['checks']) if res else 0}")
    st = [e for e in evs if e["kind"] == "tap_stats"]
    if st:
        lines.append(f"  - {scen} tap 스레드 1 회 시간: mean {st[-1]['mean_ms']} ms · p99 {st[-1]['p99_ms']} ms · max {st[-1]['max_ms']} ms (n {st[-1]['n']})")
    vs = sdir / "viewer/viewer_stats.json"
    if vs.exists():
        v = json.loads(vs.read_text())
        log = (sdir / "viewer.log").read_text() if (sdir / "viewer.log").exists() else ""
        chk(scen, "E10_viewer_headless_ok", "Traceback" not in log and v["frames"] > 10,
            f"frames {v['frames']} · render mean {v['render_mean_ms']} ms · p99 {v['render_p99_ms']} ms · codes {len(v['codes'])}")
lines.append("")
lines.append("UI_E2E_ALL_PASS" if ok_all else "UI_E2E_FAIL")
(root / "UI_E2E.md").write_text("\n".join(lines) + "\n")
print("UI_E2E_ALL_PASS" if ok_all else "UI_E2E_FAIL")
sys.exit(0 if ok_all else 1)
