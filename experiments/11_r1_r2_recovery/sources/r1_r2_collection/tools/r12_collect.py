#!/home/user/so101-env/bin/python
"""R1/R2 추가 시연 수집 — 터미널 UI (record_ui.py 를 그대로 재사용) + Tk 영상 창.

  ~/so101-env/bin/python r12_collect.py menu                          # R1/R2 시나리오 메뉴 · 시작 조건·목표 동작 · 48편 진행률
  ~/so101-env/bin/python r12_collect.py check                         # 환경 확인 (장치 열지 않음)
  ~/so101-env/bin/python r12_collect.py plan   --group r1_pilot|r2_pilot
  ~/so101-env/bin/python r12_collect.py status --session main_k8/r2_pregrasp_pilot
  ~/so101-env/bin/python r12_collect.py preview [--type R1|R2] [--source d2|dummy] [--episodes 3] [--preview-session S --preview-episode N]   # 로봇 없이
  ~/so101-env/bin/python r12_collect.py record --session main_k8/r2_pregrasp_pilot [--num 8]         # 실제 녹화 (사용자가 직접)
  ~/so101-env/bin/python r12_collect.py label  --session S --episode N [--result 1|2|3|4] [--retry K] [--notes "..."]   # 4 = R1 재정렬 O·파지 실패
  ~/so101-env/bin/python r12_collect.py exclude --session S --episodes 3,7 --reason "..."
  ~/so101-env/bin/python r12_collect.py sync   --session S          # r12_episodes.csv · 계획 상태 다시 맞춤
  ~/so101-env/bin/python r12_collect.py qa     --session S          # 품질 검사 보고서 (dataset 읽기만)

record 는 d2 와 같은 lerobot-record 옵션(포트·id·카메라 640×480@30 MJPG warmup 4·과제 문장)을 스스로 만든다
(옵션을 손으로 넣지 않음 → d2 와 다른 설정으로 찍히는 일을 막음). lerobot-record 대신 r12_record_entry.py 가 실행된다.
키: → 다음/시작 (R1 은 두 번 = 시작 자세 안전 확인) · ← 버리기·다시 · Esc 종료 (n r q 도 같음, lerobot 과 같음)
    + 결과 입력 1 2 3 (4 = R1 재정렬 O·파지 실패) 0 m (reset 단계에서만) · p 이전 판 다시 보기 · c 로봇선 맞추기.
"""

import datetime
import json
import re
import os
import shlex
import shutil
import subprocess
import sys
import time
import types

HERE = os.path.dirname(os.path.abspath(__file__))
HOME = os.path.expanduser("~")
SCRIPTS = os.path.join(HOME, "so101_boxpick", "scripts")
VENV_PY = os.path.join(HOME, "so101-env", "bin", "python")
ENTRY = os.path.join(HERE, "r12_record_entry.py")
FAKE = os.path.join(HERE, "r12_fake_record.py")
VIEWER = os.path.join(HERE, "r12_viewer.py")
SG_VIEWER = os.path.join(HERE, "sg_viewer.py")  # 2026-11-05 설정 viewer: sg (config/sg50.yaml) 일 때만

# d2 와 같은 장치·카메라 설정 (main_k8/redbox_수집명령.md, d2 세션 notes.md 의 실제 lerobot 명령과 같음)
D2_ARGS = [
    "--robot.type=so101_follower", "--robot.port=/dev/so101_follower", "--robot.id=my_arm",
    '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, '
    'wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }',
    "--teleop.type=so101_leader", "--teleop.port=/dev/so101_leader", "--teleop.id=my_leader",
    "--dataset.no_stamp=true", "--dataset.push_to_hub=false",
]

rc = ru = None  # r12_common · record_ui (환경 변수를 정한 뒤 불러온다)
CTX = {}


def load_mods():
    global rc, ru
    sys.path.insert(0, HERE)
    sys.path.insert(0, SCRIPTS)
    import r12_common
    import record_ui

    rc, ru = r12_common, record_ui
    ru.COLORS.update({"SETUP": ("43", "30"), "BLOCK": ("41", "97"), "ARMED": ("42", "30"), "WAIT": ("100", "97")})


def say(s=""):
    print(s, flush=True)


def fail(lines):
    say("\x1b[31;1m✗ " + lines[0] + "\x1b[0m")
    for ln in lines[1:]:
        say("  " + ln)
    return 1


def opt(argv, name, default=None, flag=False):
    if flag:
        if name in argv:
            argv.remove(name)
            return True
        return False
    for i, a in enumerate(argv):
        if a == name and i + 1 < len(argv):
            v = argv[i + 1]
            del argv[i:i + 2]
            return v
        if a.startswith(name + "="):
            del argv[i]
            return a.split("=", 1)[1]
    return default


def hpath(p):
    return p.replace(HOME, "~")


# ================================================================ 터미널 화면 (record_ui.UI 확장)

def make_ui_class():
    base = ru.UI
    BLOCKED = ru.BLOCKED

    class R12UI(base):
        """record_ui 의 배너·저장 중 키 차단·창 제목을 그대로 쓰고, r12 진입점의 '[r12] {json}' 줄로 단계를 바꾼다."""

        def __init__(self, args, layout=None):
            super().__init__(args, layout)
            self.reset_time = float("inf")  # 준비·결과 단계는 시간 초과가 없다 (진입점이 → 로만 끝냄)
            c = CTX
            self.cfg, self.rows, self.sess_dir = c["cfg"], c["rows"], c["sess_dir"]
            self.live = c["live"]
            self.pending = None  # 방금 녹화한(아직 저장 전) 시도
            self.ep_attempt = {}
            self.attempt_ep = {}
            self.discard_pending = False
            self.setup_ep = None
            self.memo = None
            self.labels = {}
            self.results = []
            self.messages = []
            self.saved_eps = []
            self.blocked = []
            self.last_ui = 0.0
            self.save_note = ""
            self.key_off = 0
            self.rec_aid, self.marks = None, []
            self.invalid_aids = {}  # 파일럿: 명령 보호로 무효가 된 시도 {attempt_id: 사유}
            self.review = []  # 방금 판 자동 검토 표시 (보조): [(level, code, 글)]
            self.safety_ask = None  # R1 시작 자세 안전 확인 (3차 지시서): (ep, 시각) — 첫 → 에 확인 문구, 10 초 안 두 번째 → 로 시작
            self.safety_ok = {}     # ep → True (확인하고 시작)
            self.replay_until = 0.0  # p: 이전 판 다시 보기 (영상 창)
            # 로봇선 보정 (11-02): '그리퍼가 큐브 바로 위' 일 때 c → 지금 pan − K 기준 pan. 세션에 저장, 다음 실행에도 씀
            self.calib_path = os.path.join(self.sess_dir, "r12_pan_calib.json")
            self.pan_calib = float((rc.read_json(self.calib_path, {}) or {}).get("offset_deg", 0.0))
            try:
                os.remove(os.path.join(self.live, "keys.in"))
            except FileNotFoundError:
                pass
            self.write_ui(force=True)

        # ---- 기록
        def ev(self, d):
            rc.append_event(self.sess_dir, d)

        def note(self, msg, color="33"):
            self.messages.append(msg)
            self.out(f"\x1b[{color}m  {msg}\x1b[0m\r\n")
            self.write_ui(force=True)

        def row(self, ep):
            if ep is None or ep >= len(self.rows):
                return None
            return rc.describe_row(self.cfg, self.rows[ep])

        def row_lines(self, ep, head=""):
            r = self.row(ep)
            if r is None:
                return [f"{head}episode {ep} 는 계획에 없어요"]
            rt = f" (재촬영: ep {r['retake_of']})" if r["retake_of"] else ""
            if r.get("type") == "SG":  # 2026-11-05 SG50 일반 파지 (config/sg50.yaml) — 오차 상태 없음
                s50 = self.cfg.get("sg50") or {}
                q = self.cfg["scenarios"].get(r["scenario_id"], {}).get("pose", "")
                p = (s50.get("start_poses") or {}).get(q, {})
                conf = (s50.get("positions") or {}).get(r["position"], {}).get("confirmed", True)
                tgt = (" ".join(f"{rc.SHORT[j]} {v:+g}" for j, v in (p.get("joints") or {}).items()) or "자유 — 직접 정함 (실제 값 기록)") \
                    + (f" · {p['pending']}" if p.get("pending") else "")
                return [f"{head}【 {r['label']} 】 {r['scenario_id']}" + rt,
                        f"큐브 {r['position']} ({r['cube_xy_cm']} cm){'' if conf else ' — 좌표 미확정 (front 흰 점선에 놓고 확인)'} · 회전 0° (로봇 좌우축 기준, wrist_roll 아님)",
                        f"준비 (녹화 안 함): {r['start']}",
                        f"시작 자세 {q}: {tgt}" if q == "FREE" else f"시작 자세 {q} 목표 (참고, 막지 않음): {tgt}",
                        f"녹화 (목표 동작): {r['demo']}"] + (
                        ["결과: 1 첫 파지 성공 · 2 재파지 · 재정렬 뒤 성공 · 3 실패 · m 메모 (실패 판도 지우지 않고 기록)"] if self.cfg.get("result_entry", True) else [])
            if r.get("r1_setup"):  # R1 (3·4차): 오차 상태는 준비 단계(녹화 안 함)에서, 녹화는 되돌리는 동작부터
                pe = {"left": "왼쪽(−)", "right": "오른쪽(+)"}.get(r.get("pan_error_direction"), "")
                src = {"K_grid": "K 격자", "free_point": "자유 점 (대략 놓기, front 로 확인)", "front_detected": "front 검출 자리"}.get(r["cube_position_source"], "")
                if r.get("approach_stage_expected"):
                    stg = "/".join(rc.STAGE_KO.get(x, x) for x in r["approach_stage_expected"].split("|"))
                else:
                    stg = rc.POSE_KO.get(r.get("start_pose_type"), "")
                return [f"{head}【 {r['label']} 】 {r['scenario_id']} · R1 = Pan 재탐색·재정렬" + rt,
                        f"큐브 {r['position']} ({src}) · 각도 {r['angle']} · 접근 단계 {stg}",
                        f"Pan 오차 (후보·대략): {pe} {r.get('nominal_pan_error_deg', '')}° → 주황 선 · K 기준 pan 자체가 ±9° 흔들려 값은 참고",
                        f"손목 화면: {rc.VIS_KO.get(r.get('wrist_visibility_target'), '상관없음')} · front 에는 큐브가 보여야 함",
                        f"준비 (녹화 안 함): {r['start']}",
                        f"녹화 (목표 동작): {r['demo']}",
                        "조건이 달라도 녹화됨 (경고만) — 바꾸기: s 시나리오 · d 오차 방향 · k 큐브 자리 · x 검출 자리. 막는 것 = 안전 조건뿐",
                        "→ 두 번 (첫 → = 안전 확인: 탁자·상자 닿지 않음 · 케이블 · 관절 끝 밀지 않음 · 그리퍼 열림)"]
            if r.get("error_in_rec"):  # 11-02 오후 정의 (수량 0): 쉬는 자세에서 시작, 어긋남은 녹화 중에
                pe = {"left": "왼쪽(−)", "right": "오른쪽(+)"}.get(r.get("pan_error_direction"), "")
                return [f"{head}【 {r['label']} 】 {r['scenario_id']} · R1 = Pan 방향 재정렬" + rt,
                        f"시작 조건: {r['start']} 큐브 {r['position']} · 각도 {r['angle']} (영상 창 흰 점선)",
                        f"Pan 오차: {rc.KIND_KO.get(r.get('error_kind'), '')} · {pe} {r.get('nominal_pan_error_deg', '')}° (주황 선 = {r['x_label']})",
                        f"목표 동작: {r['demo']}",
                        "주황 선에 닿으면 Space = 재정렬 시작 표시 (대략이면 됨)"]
            if r.get("wrist_start_region"):  # 11-02: R2 = 국소 오차, 준비 단계에서 만듦, Pan 목표 없음
                cm = r.get("nominal_local_error_cm")
                return [f"{head}【 {r['label']} 】 {r['scenario_id']} · R2 = 파지 직전 국소 정렬·깊이·닫힘" + rt,
                        f"시작 조건: {r['start']}",
                        f"국소 오차: {rc.LOCAL_KO.get(r.get('local_alignment_type'), '')}" + (f" {cm} cm" if cm not in ("", "0") else "")
                        + f" — {r['offset_mag']} · Pan 목표 없음 (작은 Pan 수정은 허용)",
                        f"목표 동작: {r['demo']}",
                        self.cfg.get("setup_order_text", "")]
            out = [f"{head}【 {r['label']} 】 {r['scenario_id']}" + (f" (재촬영: ep {r['retake_of']})" if r["retake_of"] else ""),
                   f"영상 창 지도: 초록 ■ 계획 위치(큐브 {r['position']}) · 주황 ✕ 시작 위치(오답, 높이 {r['start_height']})"
                   + (f" · 파랑 ○ 경유 ({r['via']})" if r.get("via") else ""),
                   f"큐브 {r['position']} ({r['cube_xy_cm']} cm) · 각도 {r['angle']} · 어긋남 {r['offset_mag']}",
                   f"▶ {r['pan_text']} (대략 맞추고 →, 값은 참고)" if r.get("pan_text") else "",
                   self.cfg.get("setup_order_text", ""),
                   f"시작 자세: {r['start']}",
                   f"시연: {r['pace']}" if r.get("pace") else ""]
            return out

        def vision_now(self, ep):
            try:
                fr = rc.LiveFrames(self.live, create=False)
                seq, f, w = fr.get()
                if seq <= 0:
                    return None
                r = self.rows[ep] if ep is not None and ep < len(self.rows) else {}
                v = rc.vision(f, w, self.cfg, r.get("position"))
                v.update(t=time.time(), seq=seq, by="terminal")
                return v
            except Exception as e:  # 검출 실패는 기록만
                return {"error": repr(e)}

        # ---- 단계
        def on_line(self, line):
            s = line.strip()
            if s.startswith("[r12] "):
                try:
                    d = json.loads(s[6:])
                except ValueError:
                    return
                self.on_r12(d)
                return
            import re

            m = re.search(r"Recording episode (\d+)", line)
            if m:
                self.finish_save()
                self.episode = int(m.group(1))
                self.rerecord = False
                self.set_state("WAIT")
            elif "Reset the environment" in line:
                self.set_state(ru.RESET)
            elif "Re-record episode" in line:
                if self.pending:
                    self.ev({"ev": "discarded", "attempt_id": self.pending, "ep": self.attempt_ep.get(self.pending)})
                    self.banner("INFO", "⟲ 방금 판을 버렸어요 — 같은 번호·같은 시나리오로 다시 녹화", f"episode {self.attempt_ep.get(self.pending)}")
                self.pending = None
                self.discard_pending = False
            elif "Left arrow key pressed" in line:
                if self.state == ru.REC:
                    self.rerecord = True
                    self.note("← 이번 판은 버려요 (준비 단계에서 같은 시나리오를 다시 준비 → →)")
            elif "Right arrow key pressed" in line or "Escape key pressed" in line:
                esc = "Escape" in line
                if self.state == ru.REC and not self.rerecord and (esc or self.is_last()):
                    self.to_saving()
            elif re.match(r"\s*(Map(:|\s+\d)|Svt\[)", line):
                if line.lstrip().startswith("Map") and self.state not in BLOCKED:
                    self.to_saving()
                if self.state == ru.SAVING:
                    self.save_seen = True
            elif "Stop recording" in line:
                self.finish_save()
                self.set_state(ru.FINAL)
                self.banner(ru.FINAL, "💾 마무리 저장 중 — 키 누르지 마세요", "dataset finalize")
            elif re.search(r"\bExiting\b", line) and self.state == ru.FINAL:
                self.set_state(ru.DONE)
                self.banner(ru.DONE, f"✅ 녹화 종료 — 이번 실행 {self.saved}개 저장")
            self.write_ui(force=True)

        def on_r12(self, d):
            k = d.get("ev")
            ep = d.get("ep")
            if k == "setup_start":
                self.discard_pending = bool(d.get("discard_pending"))
                self.setup_ep = (ep - 1) if (self.discard_pending and ep is not None) else ep
                if d.get("after_episode"):
                    self.set_state(ru.RESET)
                    self.reset_banner()
                else:
                    self.set_state("SETUP")
                    self.banner("SETUP", f"🛠 준비 — 녹화 안 함 · episode {self.setup_ep}",
                                "리더로 시작 자세를 만들고 큐브를 놓은 뒤 → (시작 자세 검사 통과해야 녹화 시작) · 종료 Esc",
                                *self.row_lines(self.setup_ep))
            elif k == "reset_end":  # 결과 단계 → : 방금 판 저장(또는 버림) 뒤 준비 단계로 (바로 녹화하지 않음)
                if d.get("discard_previous"):
                    self.banner("INFO", "⟲ 방금 판을 버리고 같은 번호를 다시 준비해요", "준비 단계에서 오차 자세 → →")
                else:
                    self.to_saving()
                    self.save_note = "저장 중 — 리더를 그대로 두세요 (움직이면 저장 뒤 팔로워가 빠르게 따라감, 녹화는 안 됨)"
            elif k == "discard_pending":
                self.discard_pending = True
                self.setup_ep = ep - 1 if ep is not None else None
                self.banner("INFO", "⟲ 방금 판 버리기 예약 — 같은 시나리오를 다시 준비하고 →", "(되돌릴 수 없음)",
                            *self.row_lines(self.setup_ep))
            elif k == "blocked":
                self.blocked = d.get("checks", [])
                if self.state == ru.SAVING:
                    self.set_state(ru.RESET)
                self.banner("BLOCK", "✗ 안전 조건 — 녹화를 시작하지 않았어요 (준비 계속)", "아래 ✗ 를 고친 뒤 → (시나리오 조건은 막지 않음)",
                            *[("✗ 안전: " if c[0] == "BLOCK" else "⚠ 참고: ") + c[2] for c in self.blocked])
                self.ev({"ev": "blocked", "ep": ep, "checks": self.blocked, "state": d.get("state"), "run_id": CTX["run_id"]})
            elif k == "armed":
                aid = d["attempt_id"]
                self.ep_attempt[ep] = aid
                self.attempt_ep[aid] = ep
                r_pre = self.row(ep)
                closed_ok = bool(r_pre and r_pre.get("gripper_start") == "closed")  # R2-O: 닫힌 그리퍼가 시작 조건 (경고 아님)
                warn = [c[2] for c in d.get("checks", []) if c[0] == "WARN" and not (closed_ok and c[1] == "gripper_closed")]
                pan0 = (d.get("state") or {}).get("shoulder_pan.pos")
                pdiff, ptxt, pok = rc.pan_guide(self.cfg, self.rows[ep] if ep is not None and ep < len(self.rows) else None,
                                                None if pan0 is None else pan0 - self.pan_calib)
                r_ = self.row(ep)
                if ptxt and not pok and r_ and r_.get("pan_text") and not r_.get("r1_setup"):  # 10-30 옛 시나리오 (R1 3차는 아래)
                    warn.append("계획 pan 과 다름 — " + ptxt + " (그대로 녹화, 실제 값은 기록됨)")
                vis = rc.read_json(os.path.join(self.live, "vision.json"))
                if not vis or time.time() - vis.get("t", 0) > 2.0:
                    vis = self.vision_now(ep)  # 영상 창이 없을 때: 공유 프레임으로 직접
                scen = []
                if r_ and r_.get("r1_setup"):  # R1 시나리오 조건: 경고만 (녹화는 시작됨), 실제 값은 기록
                    scen = [t for ok_, _, t in rc.scenario_checks(self.cfg, r_, d.get("state"), vis, self.pan_calib) if ok_ is False]
                self.ev({"ev": "armed", "attempt_id": aid, "ep": ep, "run_id": CTX["run_id"], "state": d.get("state"),
                         "action": d.get("action"), "checks": d.get("checks", []), "row": self.rows[ep] if ep is not None and ep < len(self.rows) else None,
                         "preview": CTX["preview"], "pan_calib": self.pan_calib, "setup_pan": d.get("setup_pan"), "scenario_warn": scen,
                         "safety_confirmed": bool(self.safety_ok.pop(ep, False)) if r_ and r_.get("r1_setup") else None,
                         "code_version": CTX.get("code_version", "")})
                self.ev({"ev": "vision", "attempt_id": aid, "ep": ep, "vision": vis})
                if r_ and r_.get("pilot_variant"):  # 파일럿 12편: 시작 상태 값 · 실물 실패 상태와 비슷함 (근사, 막지 않음)
                    ps = rc.pilot_start_checks(self.cfg, r_, d.get("state"), vis, self.pan_calib)
                    self.ev({"ev": "pilot_start", "attempt_id": aid, "ep": ep, "pilot": ps})
                    sim = ps["similarity"]
                    scen = scen + [t for ok_, _, t in ps["items"] if ok_ is False] + \
                        ([f"실패 상태와 비슷함 {sim['matched']}/{sim['total']} (근사 · 참고)"] if sim["total"] else [])
                after_reset = self.state == ru.RESET
                self.banner("ARMED", f"✓ 안전 조건 통과 — episode {ep}",
                            ("방금 판 " + ("버리고" if d.get("discard_previous") else "저장한 뒤") + " 바로 녹화 시작 · 리더 팔을 그대로 두세요")
                            if after_reset else "녹화 시작", *(["⚠ 참고: " + w for w in warn] + ["◇ 시나리오 (녹화됨·기록): " + w for w in scen]))
                if after_reset and not d.get("discard_previous"):
                    self.to_saving()
                    self.save_note = "저장 중에는 리더 팔을 움직이지 마세요 (다음 판 시작 자세)"
                self.blocked = []
            elif k == "rec_start":
                aid = d.get("attempt_id")
                self.review = []
                self.rec_aid, self.marks = aid, []
                self.set_state(ru.REC)
                self.save_note = ""
                self.ev({"ev": "rec_start", "attempt_id": aid, "ep": ep, "state": d.get("state"),
                         "shift_from_armed_deg": d.get("shift_from_armed_deg")})
                r = self.row(ep)
                self.banner(ru.REC, f"▶ 녹화 중 — episode {ep} ({self.ordinal()}번째 / {self.num_episodes})",
                            f"{self.episode_time:.0f}초 · 끝나면 →  버리고 다시 ←  종료 Esc",
                            *(([f"【 {r['label']} 】 {r['position']} · {r['angle']}", f"시연: {r['demo']}", r.get("pace", "")]) if r else []))
                sh = d.get("shift_from_armed_deg")
                if sh is not None and sh > 5:
                    self.note(f"⚠ 준비 때 자세에서 {sh:.1f}° 움직인 채 녹화가 시작됐어요 (저장 중 리더가 움직임?) — 필요하면 ← 로 다시")
            elif k == "rec_end":
                aid = d.get("attempt_id")
                self.pending = aid
                self.ev({"ev": "rec_end", **{x: d.get(x) for x in ("attempt_id", "ep", "frames", "loop_hz_mean", "late_ticks",
                                                                    "stall_ticks", "stall_by_cam", "rerecord", "stop")}})
                self.measure_recovery(aid, ep)
                self.review_last(aid, ep)
                fps = int(self.cfg.get("fps", 30))
                msg = (f"episode {ep}: 기록 {d.get('frames')} 프레임 · 평균 {d.get('loop_hz_mean')} Hz · 늦은 틱 {d.get('late_ticks')} · "
                       f"카메라 반복 {d.get('stall_ticks')}")
                self.note(msg, "36" if (d.get("loop_hz_mean") or 0) >= fps * 0.95 and not d.get("late_ticks") else "33")
            elif k == "guard":  # 녹화 중 명령 보호 (파일럿 설정) — 녹화 중이면 무효 시연 · 자동 버림
                self.ev({"ev": "guard", **{x: d.get(x) for x in ("attempt_id", "ep", "phase", "reason", "invalid", "joint", "gap", "cmd", "sent")}})
                why = {"pan_cmd_limit": f"리더 Pan 명령 {d.get('cmd', 0):+.0f}° → 팔로워 ±{GUARD_PAN(self.cfg):g}° 까지만",
                       "leader_follower_gap": f"{d.get('joint', '')} 리더−팔로워 {d.get('gap', 0):.0f}° → 팔로워 고정 (리더를 팔로워 자세 쪽으로 맞추면 풀림)"
                       }.get(d.get("reason"), d.get("reason", ""))
                if d.get("invalid"):
                    self.invalid_aids[d.get("attempt_id")] = d.get("reason")
                    if self.state == ru.REC:
                        self.rerecord = True  # 진입점이 '다시 찍기' 경로로 이 판을 버림 (← 와 같음)
                    self.banner("BLOCK", f"⛔ 무효 시연 — episode {ep} 녹화를 멈추고 자동으로 버려요", why,
                                "결과 단계에서 → = 버리고 같은 번호를 다시 준비 (팔로워가 고정돼 있으면 리더를 맞춰 풀기)")
                else:
                    self.note(f"⚠ 명령 보호: {why}", "31")
            elif k in ("guard_warn", "guard_release", "guard_on"):
                if k == "guard_on":
                    self.note("명령 보호 켜짐: Pan 명령 ±95° · 리더−팔로워 25° 넘으면 팔로워 고정 · 녹화 중 걸리면 무효", "36")
                else:
                    self.note(("⚠ " + d.get("msg", "")) if k == "guard_warn" else f"팔로워 고정 풀림 (리더−고정 자세 {d.get('gap')}°)",
                              "33" if k == "guard_warn" else "36")
                self.ev({"ev": k, **{x: d.get(x) for x in ("ep", "phase", "joint", "gap", "msg")}})
            elif k == "start_frames":
                self.ev({"ev": "start_frames", "attempt_id": d.get("attempt_id"), "ep": ep, "files": d.get("files")})
            elif k in ("setup_note", "setup_timeout", "tap_error", "stop_before_rec", "setup_end"):
                if k == "setup_note":
                    self.note(d.get("msg", ""))
                elif k == "setup_timeout":
                    self.note("준비 단계가 오래 이어지고 있어요 (저절로 녹화를 시작하지 않음)")
                elif k == "tap_error":
                    self.note(f"화면 탭 오류 (녹화는 계속): {d.get('error')}", "31")
            self.write_ui(force=True)

        def review_last(self, aid, ep):
            """녹화 뒤 자동 검토 (보조): 그리퍼 명령 · 팔로워 그리퍼 열 + 축소 손목 영상 (live/last_episode.*) → 표시 · 기록. 판정이 아님."""
            try:
                import numpy as np
                import r12_guide as G

                lj = rc.read_json(os.path.join(self.live, "last_episode.json"), {}) or {}
                if lj.get("attempt_id") not in (None, aid) or not lj.get("grip_state"):
                    return
                thumbs = None
                try:
                    arr = np.load(os.path.join(self.live, "last_episode.npy"))
                    thumbs = [a[1] for a in arr]  # (n, 2, 120, 160, 3) → wrist
                except (OSError, ValueError):
                    pass
                self.review = G.review_episode(lj.get("grip_cmd") or [], lj["grip_state"], thumbs, self.cfg, every=int(lj.get("every_ticks", 10)))
                self.ev({"ev": "review_flags", "attempt_id": aid, "ep": ep, "flags": self.review})
                for lv, _, t in self.review:
                    if lv == "warn":
                        self.note(f"⚠ 검토 (자동 · 보조): {t} — 영상으로 확인, 의도와 다르면 ← 로 버리기", "31")
            except Exception as e:  # 검토 실패로 수집이 멈추면 안 됨
                self.note(f"검토 표시 실패 (수집은 계속): {e!r}")

        def reset_banner(self):  # noqa: C901
            p = self.pending
            nxt = self.setup_ep
            lines = []
            res = self.cfg.get("result_entry", True)
            if p and not self.discard_pending and not res:
                lines.append(f"방금 episode {self.attempt_ep.get(p)}: → 저장 · ← 버리기 (같은 시나리오 다시) · m 메모 · p 다시 보기")
            elif p and not self.discard_pending:
                r1 = (self.row(self.attempt_ep.get(p)) or {}).get("r1_setup")
                lines.append(f"방금 episode {self.attempt_ep.get(p)} 결과: 1 첫 파지 성공 · 2 재시도 후 성공(누를 때마다 재시도 +1) · 3 실패"
                             + (" (재정렬 못 함) · 4 재정렬은 했지만 파지 실패" if r1 else "") + " · 0 지우기 · m 메모")
                lines.append("잘못 찍었으면 ← (방금 판 버리고 같은 시나리오 다시)")
            lines += self.row_lines(nxt, f"다음 판 episode {nxt}: ")
            self.banner(ru.RESET, "↺ 결과 입력 — 녹화 안 함" if res else "↺ 판 끝 — 녹화 안 함",
                        ("결과를 넣고 " if res else "") + "→ = 방금 판 저장 → 준비 단계 (다음 판 자세는 저장 뒤에) · 종료 Esc (방금 판 저장 후 끝)", *lines)

        def finish_save(self):
            before = self.saved
            super().finish_save()
            if self.saved > before:
                aid = self.pending
                ep = self.attempt_ep.get(aid, self.episode)
                self.ev({"ev": "saved", "attempt_id": aid, "ep": ep, "run_id": CTX["run_id"]})
                self.saved_eps.append(ep)
                r = self.row(ep)
                self.results.append({"ep": ep, "scenario": r["scenario_id"] if r else "?",
                                     "label": self.label_text(aid) or ("결과 미입력" if self.cfg.get("result_entry", True) else "저장")})
                self.pending = None

        # ---- 결과 입력
        def label_text(self, aid):
            lab = self.labels.get(aid)
            if not lab:
                return ""
            yn = lambda v: "✓" if v else "✗"  # noqa: E731
            t = f"첫 파지 {yn(lab['first_grasp_success'])} · 최종 {yn(lab['final_success'])} · 재시도 {lab['retry_count']}"
            if lab.get("recovery_completed") is not None:
                t += f" · 재정렬 {yn(lab['recovery_completed'])}"
            return t + (f" · 메모 {lab['operator_notes']}" if lab.get("operator_notes") else "")

        def set_label(self, key):
            aid = self.pending
            prev = self.labels.get(aid) or {}
            notes = prev.get("operator_notes", "")
            if key == "1":
                lab = {"first_grasp_success": True, "final_success": True, "retry_count": 0}
            elif key == "2":
                r = prev.get("retry_count", 0) + 1 if (prev.get("final_success") and not prev.get("first_grasp_success")) else 1
                lab = {"first_grasp_success": False, "final_success": True, "retry_count": r}
            elif key == "3":
                lab = {"first_grasp_success": False, "final_success": False, "retry_count": prev.get("retry_count", 0)}
            elif key == "4":  # R1: Pan 재정렬은 끝냈지만 파지 실패
                lab = {"first_grasp_success": False, "final_success": False, "retry_count": prev.get("retry_count", 0),
                       "recovery_completed": True}
            else:
                self.labels.pop(aid, None)
                self.ev({"ev": "label", "attempt_id": aid, "first_grasp_success": None, "final_success": None,
                         "retry_count": None, "operator_notes": None})
                self.note(f"episode {self.attempt_ep.get(aid)} 결과를 지웠어요")
                return
            lab["operator_notes"] = notes
            if (self.row(self.attempt_ep.get(aid)) or {}).get("r1_setup"):  # R1 재정렬 완료: 1·2 = 예, 3 = 아니오, 4 = 예
                lab.setdefault("recovery_completed", key in ("1", "2"))
            self.labels[aid] = lab
            self.ev({"ev": "label", "attempt_id": aid, **lab})
            self.note(f"episode {self.attempt_ep.get(aid)} 결과: {self.label_text(aid)}"
                      + ("  — 실패한 시연은 보통 ← 로 버리고 다시 찍어요" if key == "3" else ""), "32")

        def memo_input(self, data):
            if data.startswith(b"\x1b"):
                self.memo = None
                self.note("메모 취소")
                return
            for ch in data.decode(errors="ignore"):
                if ch in "\r\n":
                    aid = self.pending
                    text = self.memo.decode(errors="ignore") if isinstance(self.memo, (bytes, bytearray)) else self.memo
                    self.memo = None
                    lab = self.labels.setdefault(aid, {"first_grasp_success": None, "final_success": None, "retry_count": None})
                    lab["operator_notes"] = text
                    self.ev({"ev": "label", "attempt_id": aid, **lab})
                    self.note(f"메모 저장: {text}", "32")
                    return
                if ch in "\x7f\x08":
                    self.memo = self.memo[:-1]
                elif ch.isprintable():
                    self.memo += ch
            self.out(f"\r\x1b[K  메모: {self.memo}")
            self.write_ui(force=True)

        def key_allowed(self, data):
            if b"\x03" in data:
                return super().key_allowed(data)
            if self.memo is not None:
                self.memo_input(data)
                return False
            if self.state in BLOCKED:
                return super().key_allowed(data)
            if self.state == ru.RESET and data in (b"1", b"2", b"3", b"4", b"0") and not self.cfg.get("result_entry", True):
                self.note("이 수집은 결과 입력을 쓰지 않아요 (config result_entry: false) — → 저장 · ← 버리기 · m 메모")
                return False
            if self.state == ru.RESET and data in (b"1", b"2", b"3", b"4", b"0", b"m", b"M"):
                if not self.pending or self.discard_pending:
                    self.note("결과를 넣을 판이 없어요 (버릴 판이거나 아직 녹화 전)")
                elif data == b"4" and not (self.row(self.attempt_ep.get(self.pending)) or {}).get("r1_setup"):
                    self.note("4 (재정렬은 했지만 파지 실패) 는 R1 판에만 써요")
                elif data in (b"m", b"M"):
                    self.memo = ""
                    self.out("\r\n  메모 (Enter 저장 · Esc 취소): ")
                    self.write_ui(force=True)
                else:
                    self.set_label(data.decode())
                return False
            if data in (b"c", b"C"):  # 로봇선 맞추기 (lerobot 은 c 를 쓰지 않음 — 넘기지 않음)
                row = self.row(self.setup_ep if self.state in ("SETUP", ru.RESET, "WAIT") else self.episode)
                st = rc.read_json(os.path.join(self.live, "status.json"), {}) or {}
                pan = (st.get("state") or {}).get("shoulder_pan.pos")
                if row is None or pan is None:
                    self.note("로봇선 맞추기: 계획 줄이나 관절값이 없어요")
                    return False
                off = round(pan - rc.pan_ref(self.cfg, row["position"]), 1)
                if abs(off) > 15:  # 큐브 위가 아닌데 잘못 누른 경우 (11-02 연습의 차이는 4–9°)
                    self.note(f"로봇선 맞추기 안 함: pan {pan:+.1f}° 가 {row['position']} 기준 {rc.pan_ref(self.cfg, row['position']):+.1f}° 와 "
                              f"{off:+.1f}° 차이 (15° 넘음) — 그리퍼를 큐브 바로 위에 두고 c")
                    return False
                self.pan_calib = off
                rc.write_json(self.calib_path, {"offset_deg": self.pan_calib, "position": row["position"], "pan": round(pan, 1),
                                                "pan_reference_deg": rc.pan_ref(self.cfg, row["position"]),
                                                "t": time.strftime("%Y-%m-%dT%H:%M:%S"), "run_id": CTX["run_id"]})
                self.ev({"ev": "pan_calib", "offset_deg": self.pan_calib, "position": row["position"], "pan": pan, "run_id": CTX["run_id"]})
                self.note(f"로봇선 맞춤 ✓ — {row['position']} 에서 pan {pan:+.1f}° = 큐브 바로 위 → 보정 {self.pan_calib:+.1f}°", "36")
                return False
            if data == b" ":  # 재정렬 시작 표시 (lerobot 은 Space 를 쓰지 않음 — 넘기지 않음)
                if self.state == ru.REC and self.rec_aid:
                    st = rc.read_json(os.path.join(self.live, "status.json"), {}) or {}
                    fr = st.get("rec_frames")
                    pan = (st.get("state") or {}).get("shoulder_pan.pos")
                    self.marks.append(fr)
                    self.ev({"ev": "mark", "attempt_id": self.rec_aid, "ep": self.episode, "frame": fr, "pan": pan})
                    self.note(f"재정렬 시작 표시 ✓ ({fr} 프레임" + (f" · pan {pan:+.1f}°" if pan is not None else "") + ")", "36")
                else:
                    self.note("Space(재정렬 표시)는 녹화 중에만 써요")
                return False
            if data in (b"s", b"d", b"k", b"x"):  # R1 다음 판 바꾸기 (lerobot 은 쓰지 않음 — 넘기지 않음)
                self.override(data.decode())
                return False
            if data in (b"p", b"P"):  # 이전 판 확인 (lerobot 은 p 를 쓰지 않음 — 넘기지 않음)
                self.review_previous()
                return False
            if data in (b"?",):
                self.note("키: → 시작/다음 (R1 은 두 번: 안전 확인) · ← 버리기·다시 · Esc 종료 · reset 단계 1/2/3(/4 R1)/0 결과 · m 메모 · p 이전 판")
                return False
            if self.state in ("SETUP", "WAIT") and data in (b"\x1b[C", b"\x1bOC", b"n", b"N"):  # 녹화 시작은 준비 단계에서만 (4차)
                st = rc.read_json(os.path.join(self.live, "status.json"), {}) or {}
                if time.time() - st.get("t", 0) < 1.5 and rc.blocking([tuple(c) for c in st.get("checks", [])]):
                    self.note("✗ 안전 조건이라 → 를 막았어요: " + " / ".join(c[2] for c in st["checks"] if c[0] == "BLOCK"), "31")
                    self.ev({"ev": "key_blocked", "ep": self.setup_ep, "checks": st.get("checks"), "state": st.get("state"), "run_id": CTX["run_id"]})
                    return False
                r_ = self.row(self.setup_ep)
                if r_ and r_.get("r1_setup") and not self.safety_ok.get(self.setup_ep):
                    # R1 (3차 지시서): 경고 기록만으로 안전을 대신하지 않음 — 사람이 시작 자세를 보고 확인한 뒤에만 녹화
                    if self.safety_ask and self.safety_ask[0] == self.setup_ep and time.time() - self.safety_ask[1] < 10:
                        self.safety_ok[self.setup_ep] = True
                        self.safety_ask = None
                        self.ev({"ev": "safety_confirmed", "ep": self.setup_ep, "state": st.get("state"), "run_id": CTX["run_id"]})
                    else:
                        self.safety_ask = (self.setup_ep, time.time())
                        self.note("안전 확인: 탁자·상자에 닿지 않음 · 케이블 당김 없음 · 관절이 끝을 밀지 않음 · 그리퍼 열림 "
                                  "→ 맞으면 10 초 안에 → 한 번 더 (아니면 자세를 고치거나 오차를 줄이기)", "33;1")
                        return False
            if data[:1].isdigit():
                return False  # 숫자는 lerobot 이 쓰지 않음 — 넘기지 않음
            return True

        def measure_recovery(self, aid, ep):
            """R1 복구 측정 (녹화 프로세스가 남긴 pan 열·축소 손목 영상) → 'recovery' 사건. 값은 대략 (QA 가 dataset 으로 다시 잼)."""
            r = self.row(ep)
            last = rc.read_json(os.path.join(self.live, "last_episode.json"))
            if not r or not r.get("r1_setup") or not last or last.get("attempt_id") != aid or not last.get("pan"):
                return
            try:
                arm = next((e for e in reversed(rc.read_events(self.sess_dir)) if e.get("ev") == "armed" and e.get("attempt_id") == aid), {})
                ref = rc.pan_ref(self.cfg, r["position"]) + float(arm.get("pan_calib") or 0)
                m = rc.pan_recovery(last["pan"], float(last.get("fps") or 30), ref, arm.get("setup_pan"), last.get("grip_cmd"))
                import numpy as np

                arr = np.load(os.path.join(self.live, "last_episode.npy"))
                seen = [bool(rc.find_red(t[1], self.cfg, min_area=10)) for t in arr]
                w0, reacq, tre = rc.wrist_reacquire(seen, 10 / float(last.get("fps") or 30))
                m.update(wrist_visible_at_start=w0, cube_reacquired_in_wrist=reacq, cube_reacquire_t_s=tre, pan_ref_used=round(ref, 1))
                self.ev({"ev": "recovery", "attempt_id": aid, "ep": ep, **m})
                rv = (f"반전 {m['pan_reversal_kind'] + ' @' + format(m['pan_reversal_t_s'], '+.1f') + 's' if m.get('pan_reversal') else '없음'}")
                self.note(f"R1 복구 (대략): 시작 Pan 오차 {m.get('start_error_deg', 0):+.0f}° · 준비 때 움직임 {m.get('setup_pan_motion')} · "
                          f"녹화 첫 이동 {'큐브 쪽' if m.get('first_pan_move_dir') == 'toward' else '멀어짐' if m.get('first_pan_move_dir') == 'away' else '없음'}"
                          f" {m.get('first_pan_move_deg', 0):+.0f}° · {rv} · 손목 " + ("처음부터 보임" if w0 else "다시 찾음 @" + str(tre) + "s" if reacq else "못 찾음"), "36")
            except Exception as e:  # 측정 실패는 녹화와 무관
                self.ev({"ev": "recovery", "attempt_id": aid, "ep": ep, "error": repr(e)})

        def override(self, key):
            """R1 준비·결과 단계에서 다음 판의 시나리오·오차 방향·큐브 자리를 사람이 바꿈 (s/d/k/x). 계획 파일에 반영 + 'override' 사건.
            s 는 뒤쪽의 같은 시나리오 줄과 시나리오 칸을 맞바꿔 시나리오별 수량을 그대로 둔다."""
            ep = self.setup_ep
            if self.state not in ("SETUP", ru.RESET, "WAIT") or ep is None or ep >= len(self.rows):
                self.note("s/d/k/x 는 준비·결과 단계에서 다음 판에만 써요")
                return
            row = self.rows[ep]
            if row["type"] != "R1" or not (row.get("approach_stage_expected") or row.get("start_pose_type")):
                self.note("s/d/k/x 는 R1 판에서만 써요")
                return
            before = {k: row.get(k, "") for k in rc.PLAN_FIELDS}
            msg = ""
            if key == "s":
                order = [sid for sid, _ in rc.scenarios_of(self.cfg, "R1")]
                order = [x for x in order if any(r_["scenario_id"] == x for r_ in self.rows)] or order
                nxt = order[(order.index(row["scenario_id"]) + 1) % len(order)] if row["scenario_id"] in order else order[0]
                j = next((i for i in range(ep + 1, len(self.rows)) if self.rows[i]["scenario_id"] == nxt and self.rows[i]["status"] == rc.PLANNED), None)
                if j is not None:
                    other = self.rows[j]
                    for k in rc.SCENARIO_FIELDS:
                        row[k], other[k] = other.get(k, ""), row.get(k, "")
                    rc.refresh_row(self.cfg, other)
                    msg = f"시나리오 {before['scenario_id']} → {nxt} (episode {j} 와 맞바꿈, 수량 그대로)"
                else:
                    rc.set_scenario(self.cfg, row, nxt)
                    msg = f"시나리오 {before['scenario_id']} → {nxt} (맞바꿀 뒤쪽 줄 없음 — 시나리오별 수량이 바뀜)"
            elif key == "d":
                row["pan_offset_deg"] = f"{-float(row['pan_offset_deg'] or 0):g}"
                msg = "오차 방향 바꿈"
            elif key == "k":
                cyc = list(self.cfg["positions"]) + list((self.cfg.get("free_points") or {}).keys())
                cur = row["position"]
                row["position"] = cyc[(cyc.index(cur) + 1) % len(cyc)] if cur in cyc else cyc[0]
                msg = f"큐브 자리 {cur} → {row['position']}"
            elif key == "x":
                vis = rc.read_json(os.path.join(self.live, "vision.json")) or self.vision_now(ep) or {}
                f = vis.get("front") or {}
                if not f.get("detected"):
                    self.note("front 에서 큐브가 검출되지 않아 검출 자리를 쓸 수 없어요")
                    return
                cur = row["position"]
                row["position"] = rc.detected_pos(f["xy_cm"])
                msg = f"큐브 자리 {cur} → front 검출 {row['position']}"
            rc.refresh_row(self.cfg, row)
            rc.write_plan(self.sess_dir, self.rows)
            try:  # 사람이 읽는 계획표도 같이 (trial_practice.sh 가 이 표를 보여 줌)
                write_sheet(self.sess_dir, self.cfg, rc.read_meta(self.sess_dir), self.rows)
            except Exception as e:
                self.note(f"계획표(r12_sheet.md) 갱신 실패: {e!r}")
            self.ev({"ev": "override", "ep": ep, "key": key, "before": before, "after": {k: row.get(k, "") for k in rc.PLAN_FIELDS},
                     "run_id": CTX["run_id"]})
            self.safety_ok.pop(ep, None)
            self.note(f"episode {ep}: {msg} → Pan 오차 {row['pan_error_direction']} {row['nominal_pan_error_deg']}° · 주황 선 {float(row['pan_target_deg']):+.1f}°"
                      + (f" · {row['note']}" if row.get("note") else ""), "36")
            self.banner("SETUP" if self.state != ru.RESET else ru.RESET, f"✎ 계획 바꿈 — episode {ep}", msg, *self.row_lines(ep))

        def review_previous(self):
            """p: 이번 실행에서 마지막으로 녹화한 판 확인 — 터미널 요약 + 영상 창에서 축소 영상 다시 보기 (녹화 프로세스가 /dev/shm 에 남긴 것)."""
            if self.state not in ("SETUP", ru.RESET, "WAIT"):
                self.note("p (이전 판 확인) 는 준비·결과 입력 단계에서만 써요")
                return
            last = rc.read_json(os.path.join(self.live, "last_episode.json"))
            if not last:
                self.note("이번 실행에서 녹화한 판이 아직 없어요 (이전 실행의 판: review_videos/episode_NNN.mp4)")
                return
            ep = last.get("ep")
            r = self.row(ep) or {}
            aid = last.get("attempt_id")
            st = "버림" if aid and aid != self.pending and aid not in self.ep_attempt.values() else \
                ("저장 대기" if aid == self.pending else "저장됨")
            self.note(f"이전 판 episode {ep} ({st}) · {r.get('scenario_id', '?')} · {last.get('frames')} 프레임 · "
                      f"{last.get('loop_hz_mean')} Hz · 결과 {self.label_text(aid) or '미입력'} — 영상 창에서 다시 보기", "36")
            self.replay_until = time.time() + float(last.get("duration_s") or 10) + 1.0
            self.write_ui(force=True)

        def show(self, line):
            if line.strip().startswith("[r12] ") and not ru.SHOW_ALL:
                return False
            return super().show(line)

        # ---- 화면 창으로 보내는 상태
        def tick(self):
            super().tick()
            self.viewer_keys()
            self.write_ui()

        def viewer_keys(self):
            """영상 창(r12_viewer)에서 누른 키: live/keys.in 한 줄 = 키 바이트 hex. 터미널 키와 같은 검사(key_allowed)를 거쳐 pty 로."""
            try:
                with open(os.path.join(self.live, "keys.in"), "rb") as f:
                    f.seek(self.key_off)
                    chunk = f.read()
            except FileNotFoundError:
                return
            end = chunk.rfind(b"\n") + 1
            self.key_off += end
            for line in chunk[:end].split():
                try:
                    data = bytes.fromhex(line.decode())
                except ValueError:
                    continue
                if data and CTX.get("master") is not None and self.key_allowed(data):
                    os.write(CTX["master"], data)

        def counts(self):
            out = {}
            for i, r in enumerate(self.rows):
                if r["status"] == rc.EXCLUDED:
                    continue
                d, t = out.get(r["scenario_id"], (0, 0))
                done = (r["status"] == rc.RECORDED) or (i in self.saved_eps)
                out[r["scenario_id"]] = (d + int(done), t + 1)
            return out

        def keys(self):
            st = self.state
            if st == ru.REC:
                r_ = self.row(self.episode)
                return ([("Space", "재정렬 시작 표시 (주황 선에서)")] if r_ and r_.get("error_in_rec") else []) + [
                        ("→ / n", "판 끝 (저장)" if self.is_last() else ("판 끝 → 결과 입력·다음 판 준비" if self.cfg.get("result_entry", True) else "판 끝 → 저장·다음 판 준비")),
                        ("← / r", "이번 판 버리고 다시"),
                        ("Esc / q", "이번 판 저장하고 종료")]
            r1 = bool((self.row(self.setup_ep) or {}).get("r1_setup"))
            go = "→ 두 번 (안전 확인 → 녹화)" if r1 else "→ / n"
            ov = [("s / d", "시나리오 바꾸기 / 오차 방향 바꾸기"), ("k / x", "큐브 자리 K·자유 점 / front 검출 자리")] if r1 else []
            if st == "SETUP":
                return [(go, "녹화 시작 (안전 조건 검사)")] + ov + [("c", f"로봇선 맞추기 (그리퍼를 큐브 바로 위에 두고) · 지금 {self.pan_calib:+.1f}°"),
                        ("p", "이전 판 다시 보기"), ("Esc / q", "녹화 없이 종료"), ("?", "도움말")]
            if st == ru.RESET:
                r1p = bool((self.row(self.attempt_ep.get(self.pending)) or {}).get("r1_setup")) if self.pending else False
                res = ([("1", "첫 파지 성공"), ("2", "재시도 후 성공 (+1)"), ("3", "실패" + (" (재정렬 못 함)" if r1p else ""))] +
                       ([("4", "재정렬 O · 파지 실패")] if r1p else []) + [("0", "결과 지우기")]) if self.cfg.get("result_entry", True) else []
                return res + [("m", "메모"), ("p", "방금 판 다시 보기")] + ov + [
                        ("← / r", "방금 판 버리기"), ("→ / n", "방금 판 저장 → 다음 판 준비 (녹화 안 함)"), ("Esc / q", "방금 판 저장 후 종료")]
            if st in BLOCKED:
                return [("(키 막힘)", "저장 중 — 리더 팔 그대로")]
            return [("Ctrl+C", "비상 정지")]

        def write_ui(self, force=False):
            now = time.monotonic()
            if not force and now - self.last_ui < 0.3:
                return
            self.last_ui = now
            st = self.state
            ep = self.setup_ep if st in ("SETUP", ru.RESET) else self.episode
            label = None
            if st == ru.RESET and self.pending and not self.discard_pending:
                label = self.label_text(self.pending)
            counts = self.counts()
            rc.write_json(os.path.join(self.live, "ui.json"), {
                "preview": CTX["preview"], "preview_source": CTX.get("preview_label", ""), "preview_frames": CTX.get("preview_frames", ""),
                "session": CTX["session"], "type": CTX["type"], "target": sum(t for _, t in counts.values()),
                "done": sum(d for d, _ in counts.values()), "state": st, "episode": ep, "row": self.row(ep) if ep is not None else None,
                "elapsed": time.monotonic() - self.t0, "episode_time": self.episode_time, "label": label,
                "marks": self.marks if st == ru.REC else [], "pan_calib": self.pan_calib,
                "replay": time.time() < self.replay_until,
                "safety_ask": bool(self.safety_ask and self.safety_ask[0] == ep and time.time() - self.safety_ask[1] < 10),
                "safety_ok": bool(self.safety_ok.get(ep)), "program": rc.program_progress(self.cfg, {CTX["session"]: counts}), "memo_mode": self.memo is not None, "memo_text": self.memo or "", "results": self.results[-6:],
                "counts": counts, "keys": self.keys(), "messages": self.messages[-4:], "run_saved": self.saved,
                "invalid_recent": [{"attempt_id": k, "reason": v, "ep": self.attempt_ep.get(k)} for k, v in list(self.invalid_aids.items())[-3:]],
                "last_saved_ep": self.saved_eps[-1] if self.saved_eps else None,
                "rec_aid": self.rec_aid, "review": self.review,
                "save_note": self.save_note, "blocked": self.blocked})

    return R12UI


# ================================================================ 계획 · 상태

def GUARD_PAN(cfg):
    return float((cfg["safety"].get("teleop_guard") or {}).get("pan_cmd_abs_max_deg", 95))


def read_meta_session(sess_dir):
    return (rc.read_json(os.path.join(sess_dir, rc.PLAN_META), {}) or {}).get("session", "")


def protected(session):
    return session.strip("/") in rc.PROTECTED_SESSIONS


def cmd_plan(argv):
    group = opt(argv, "--group")
    force = opt(argv, "--force", flag=True)
    cfgp = opt(argv, "--config")
    cfg = rc.load_config(cfgp)
    g = rc.group_of(cfg, group)
    if protected(g["session"]):
        return fail([f"{g['session']} 은 기존 d2 세션이라 쓰지 않아요."])
    sess = ru.Session(g["session"])
    if os.path.exists(os.path.join(sess.dir, rc.PLAN_CSV)) and not force:
        return fail([f"이미 계획이 있어요: {hpath(os.path.join(sess.dir, rc.PLAN_CSV))}", "다시 만들려면 --force (녹화 전만 허용)."])
    if (rc.dataset_total(sess.dir) or 0) > 0:
        return fail(["이미 녹화된 dataset 이 있어 계획을 다시 만들 수 없어요."])
    rows = rc.make_plan(cfg, group)
    ru.ensure_layout(sess)
    if force and os.path.exists(os.path.join(sess.dir, rc.PLAN_CSV)):
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        for f in (rc.PLAN_CSV, rc.PLAN_META):
            if os.path.exists(os.path.join(sess.dir, f)):
                shutil.copy2(os.path.join(sess.dir, f), os.path.join(sess.dir, f + f".bak_{stamp}"))
    rc.write_plan(sess.dir, rows)
    import hashlib

    meta = {"generator": "r12_collect.py plan v1", "created": datetime.datetime.now().isoformat(timespec="seconds"),
            "group": group, "type": g["type"], "session": g["session"], "repo_id": g["repo_id"], "task_text": cfg["task_text"],
            "episodes": len(rows), "episode_time_s": g.get("episode_time_s", 45), "config_path": cfg["_path"].replace(HOME, "$HOME"),
            "config_sha256": cfg["_sha256"], "plan_sha256": hashlib.sha256(rc.rows_text(rows).encode()).hexdigest(),
            "stats": rc.plan_stats(rows), "scenarios": {k: ({**v, "count": g["scenario_counts"].get(k, 0)} if g.get("scenario_counts") else v)
                                                       for k, v in cfg["scenarios"].items() if v["type"] == g["type"]
                                                       and (not g.get("scenario_counts") or k in g["scenario_counts"])},
            "safety": cfg["safety"], "base_config": cfg["base_config"]}
    rc.write_meta(sess.dir, meta)
    write_sheet(sess.dir, cfg, meta, rows)
    if g.get("planner") == "sg50":
        import sg_plan

        sg_plan.write_sheet(sess.dir, cfg)
        say(f"SG50 배치표 → {hpath(os.path.join(sess.dir, 'sg_plan.md'))} · sg_plan.csv")
    say(f"계획 {group}: {len(rows)}편 → {hpath(os.path.join(sess.dir, rc.PLAN_CSV))}")
    for k, v in meta["stats"].items():
        say(f"  {k}: " + ", ".join(f"{a} {b}" for a, b in sorted(v.items())))
    return 0


def write_sheet(sess_dir, cfg, meta, rows):
    L = [f"# {meta['session']} — {meta['type']} 수집 계획 ({len(rows)}편)", "",
         f"- repo_id `{meta['repo_id']}` · 과제 문장 \"{meta['task_text']}\" (d2 와 같음) · 판 {meta['episode_time_s']} 초",
         f"- 설정 `{meta['config_path']}` (sha256 {meta['config_sha256'][:12]}) · 계획 sha256 {meta['plan_sha256'][:12]}",
         "- 좌우 = 로봇에서 상자를 볼 때. 각도 ↺ 반시계 · ↻ 시계 (위에서 볼 때, d2 와 같은 규칙).",
         "- R1 (4차 지시서) = Pan 재탐색·재정렬 A/B1/B2/B3: 오차 상태(Pan ≈ 큐브 기준 + 명목 오차, 주황 선)는 준비 단계(녹화 안 함)에서 만들고, 녹화는 되돌리는 동작부터.",
         "- 큐브 자리: K = 격자, F = 자유 점 (표시 없음, 대략), X(x,y) = front 검출. 명목 오차·단계·가시성은 후보이며 녹화를 막지 않음 (s/d/k/x 로 바꿔 기록).",
         "- R2 (11-02 정의) = 파지 직전 국소 오차: 준비 단계에서 큐브 근처 자세를 만듦, Pan 목표 없음 (손목 화면 시작 영역).", "",
         "| ep | 시나리오 | 오차 종류 | 큐브 | 각도 | R1 접근 단계 · 손목 | R1 Pan 오차 (방향·명목 크기 → 주황 선 pan) | R2 국소 오차 (종류·크기) |",
         "|---:|---|---|---|---|---|---|---|"]
    for r in rows:
        s = cfg["scenarios"][r["scenario_id"]]
        r1 = (f"{r['pan_error_direction']} {r['nominal_pan_error_deg']}° → {float(r['pan_target_deg']):+.1f}°" if r.get("pan_error_direction") else "—")
        if r.get("approach_stage_expected"):
            r1s = f"{'/'.join(rc.STAGE_KO.get(x, x) for x in r['approach_stage_expected'].split('|'))} · 손목 {rc.VIS_KO.get(r.get('wrist_visibility_target'), '상관없음')}"
        elif r.get("start_pose_type"):
            r1s = f"{rc.POSE_KO.get(r['start_pose_type'])} · {rc.VIS_KO.get(r.get('wrist_visibility_target'), '')}"
        else:
            r1s = "—"
        r2 = (f"{rc.LOCAL_KO.get(r['local_alignment_type'], r['local_alignment_type'])}" + (f" {r['nominal_local_error_cm']} cm" if r.get("nominal_local_error_cm") not in ("", "0", None) else "")
              if r.get("local_alignment_type") else "—")
        L.append(f"| {r['episode_index']} | {r['scenario_id']} | {rc.KIND_KO.get(r.get('error_kind'), s['title'])} | {r['position']} ({r['cube_xy_cm']}) | "
                 f"{rc.angle_label(r['angle'])} | {r1s} | {r1} | {r2} |")
    L += ["", "## 시나리오 설명", ""]
    for sid, s in meta["scenarios"].items():
        L += [f"### {sid} — {s['title']} ({s['count']}편)", f"- 시작 조건: {s['start']}", f"- 오차: {s['offset_mag']}", f"- 목표 동작: {s['demo']}",
              f"- 손목 화면 큐브: {'보여야 함' if s['wrist_expect'] == 'visible' else '가장자리이거나 안 보여도 됨'}", ""]
    with open(os.path.join(sess_dir, "r12_sheet.md"), "w") as f:
        f.write("\n".join(L) + "\n")


def dataset_lengths(sess_dir):
    """dataset meta/episodes 의 length (읽기만). 없으면 {}."""
    import glob

    try:
        import pandas as pd
    except ImportError:
        return {}
    fs = sorted(glob.glob(os.path.join(sess_dir, "dataset", "meta", "episodes", "*", "*.parquet")))
    if not fs:
        return {}
    df = pd.concat([pd.read_parquet(f, columns=["episode_index", "length"]) for f in fs])
    return {int(e): int(n) for e, n in zip(df.episode_index, df.length)}


def sync(sess_dir, cfg, total=None, quiet=False):
    rows = rc.read_plan(sess_dir)
    total = rc.dataset_total(sess_dir) if total is None else total
    total = total or 0
    if total > len(rows):
        say(f"⚠ dataset {total}편이 계획 {len(rows)}줄보다 많아요 — 계획 상태를 바꾸지 않았어요.")
        return rows, []
    lens = dataset_lengths(sess_dir)
    for i, r in enumerate(rows):
        if r["status"] == rc.EXCLUDED:
            continue
        r["status"] = rc.RECORDED if i < total else rc.PLANNED
        r["frames"] = str(lens.get(i, r.get("frames", ""))) if i < total else ""
    rc.write_plan(sess_dir, rows)
    eps, problems = rc.build_episode_rows(sess_dir, cfg, rows, total)
    rc.write_episode_rows(sess_dir, eps)
    if cfg.get("pilot") and rc.group_for_session(cfg, read_meta_session(sess_dir))[1] is not None:  # 파일럿 12편: §8 메타데이터
        rc.write_pilot_rows(sess_dir, rc.build_pilot_rows(sess_dir, cfg, rows, total))
    if cfg.get("sg50") and rc.group_for_session(cfg, read_meta_session(sess_dir))[1] is not None:  # SG50 판 기록 (sg_episodes.csv)
        import sg_plan

        sg_plan.write_episodes(sess_dir, cfg)
        sg_plan.write_sheet(sess_dir, cfg)
    if not quiet:
        say(f"  r12_episodes.csv: {len(eps)}편 · 계획 상태 갱신" + (f" · 확인 필요 {len(problems)}건" if problems else ""))
        for p in problems[:10]:
            say(f"    - {p}")
    return rows, problems


def cmd_status(argv):
    session = opt(argv, "--session")
    cfg = rc.load_config(opt(argv, "--config"))
    sess_dir = rc.session_dir(session)
    rows, problems = sync(sess_dir, cfg, quiet=True)
    att = rc.fold_attempts(rc.read_events(sess_dir))
    total = rc.dataset_total(sess_dir) or 0
    valid = [r for r in rows if r["status"] != rc.EXCLUDED]
    say(f"{session}: dataset {total}편 · 유효 목표 {len(valid)} · 저장 {sum(r['status'] == rc.RECORDED for r in valid)}"
        f" · 제외 {sum(r['status'] == rc.EXCLUDED for r in rows)}")
    by = {}
    for r in valid:
        d = by.setdefault(r["scenario_id"], [0, 0])
        d[1] += 1
        d[0] += r["status"] == rc.RECORDED
    for sid, (d, t) in by.items():
        say(f"  {sid:<12} {d:>2}/{t:<2} " + "■" * d + "□" * (t - d))
    nxt = next((r for r in rows if r["status"] == rc.PLANNED), None)
    if nxt:
        dr = rc.describe_row(cfg, nxt)
        say(f"  다음: episode {nxt['episode_index']} {dr['scenario_id']} · {dr['title']} · {dr['position']} · {dr['angle']}")
    saved = [a for a in att.values() if a["status"] == "saved"]
    lab = [a for a in saved if a.get("label") and a["label"].get("final_success") is not None]
    say(f"  시도 {len(att)} (저장 {len(saved)}, 버림 {sum(a['status'] == 'discarded' for a in att.values())})"
        + (f" · 결과 입력 {len(lab)}/{len(saved)}" if cfg.get("result_entry", True) else " · 결과 입력 안 씀 (result_entry: false)"))
    for p in problems[:10]:
        say(f"  ⚠ {p}")
    return 0


def cmd_menu(argv):
    """R1/R2 메뉴 (11-02 정의): 시나리오마다 시작 조건·목표 동작·진행률, 48편 합계, 녹화 명령."""
    cfgp = opt(argv, "--config")
    cfg = rc.load_config(cfgp)
    prog = {sid: (d, t) for _, sid, d, t in rc.program_progress(cfg)}
    tot = sum(t for d, t in prog.values())
    heads = {"r1_pilot": "R1 = Shoulder Pan 재탐색·재정렬 (A 초기 방향 · B1 접근 중 반전 · B2 지나침 · B3 손목 놓침 — 오차 상태는 준비 단계, 녹화는 되돌리는 동작부터)",
             "r2_pilot": "R2 = 파지 직전 국소 정렬·접근 깊이·닫힘 타이밍 (시작: 준비 단계에서 큐브 근처 오차 자세 · Pan 목표 없음)",
             "pilot12_r1": "R1 = 팔 접힘 지나침 → Pan 복구 (오차 상태는 준비 단계, 녹화는 되돌리는 동작부터)",
             "pilot12_r2p": "R2-P = 열린 그리퍼 접근 교정 (그리퍼 열고 큐브 앞에서 정지 → 연 채 보정 → 한 번 닫기)",
             "pilot12_r2o": "R2-O = 닫힌 그리퍼 재개방 교정 (그리퍼 닫힌 채 큐브 앞에서 정지 → 먼저 열기 → 접근 → 한 번 닫기)",
             "pilot12_rc": "회복 시연 = F1 사선 하강 (열림 · 비스듬히 큐브 앞) · F2 이른 닫힘 (닫힘 · 큐브 위) · F3 정렬 오차 (닫힘 · 옆으로 빗김)"}
    say(({"pilot12": "교정 시연 파일럿 12편", "recovery": "회복 시연 (실제 실패 3 종류)"}.get(cfg.get("pilot"), "교정 시연 파일럿") if cfg.get("pilot") else "R1·R2 파일럿") + f" — 전체 {sum(d for d, t in prog.values())}/{tot} 편")
    for gname in rc.program_groups(cfg):
        head = heads.get(gname, gname)
        g = rc.group_of(cfg, gname)
        part = ([(sid, {**cfg["scenarios"][sid], "count": int(n)}) for sid, n in g["scenario_counts"].items() if int(n) > 0]
                if g.get("scenario_counts") else [(sid, s) for sid, s in rc.scenarios_of(cfg, g["type"])])
        d_, t_ = sum(prog.get(sid, (0, 0))[0] for sid, _ in part), sum(prog.get(sid, (0, 0))[1] for sid, _ in part)
        say(f"\n\x1b[1m[{g.get('pilot_variant') or g['type']}] {head}\x1b[0m  {d_}/{t_}  · 세션 {g['session']}")
        for sid, s in part:
            d, t = prog.get(sid, (0, int(s["count"])))
            say(f"  {sid:<11} {d:>2}/{t:<2} {'■' * d}{'□' * max(0, t - d)}  {s['label']}")
            if s.get("stages"):
                say(f"      접근 단계: {'/'.join(rc.STAGE_KO.get(x, x) for x in s['stages'])} · 손목 화면: {rc.VIS_KO.get(s.get('wrist_visibility'), '상관없음')}"
                    f" · Pan 오차 후보 {'/'.join(f'{v:g}' for v in sorted(set(abs(x) for x in (s.get('pan_offsets_deg') or s.get('travel_offsets_deg') or [0]))))}°"
                    + (" (진행 방향으로 지나침, 좌우 반반, 대략)" if s.get("travel") else " (왼쪽·오른쪽 반반, 대략)"))
            elif s.get("start_pose_type"):
                say(f"      시작 자세: {rc.POSE_KO.get(s['start_pose_type'])} · 손목 화면 목표: {rc.VIS_KO.get(s.get('wrist_visibility'))}"
                    f" · Pan 오차 후보 {'/'.join(f'{abs(v):g}' for v in sorted(set(abs(x) for x in s['pan_offsets_deg'])))}° (왼쪽·오른쪽 반반)")
            if s.get("gripper_start"):
                say(f"      시작 그리퍼: {'열림 (≥ 15)' if s['gripper_start'] == 'open' else '닫힘 (< 15)'}" +
                    (f" · 녹화 중 다시 열기 목표 ≥ {s['reopen_min']}" if s.get("reopen_min") else ""))
            if s.get("approach_depth_category"):
                say(f"      접근 깊이: {rc.DEPTH_KO.get(s['approach_depth_category'])} · 국소 정렬: {rc.LOCAL_KO.get(s.get('local_dir'))}")
            say(f"      시작 조건: {s['start']}")
            say(f"      오차: {s['offset_mag']}")
            say(f"      목표 동작: {s['demo']}")
        cf = f" --config {hpath(cfg['_path'])}" if cfgp else ""
        say(f"  녹화: ~/so101-env/bin/python {hpath(__file__)} record --session {g['session']}{cf}")
        say(f"  미리보기 (로봇 없음): ~/so101-env/bin/python {hpath(__file__)} preview --group {gname}{cf}" if cfgp else
            f"  미리보기 (로봇 없음): ~/so101-env/bin/python {hpath(__file__)} preview --type {g['type']}")
    return 0


def cmd_exclude(argv):
    session = opt(argv, "--session")
    eps = [int(x) for x in (opt(argv, "--episodes") or "").split(",") if x.strip()]
    reason = opt(argv, "--reason")
    if not eps or not reason:
        return fail(["--episodes N[,M] 와 --reason 이 필요해요."])
    sess_dir = rc.session_dir(session)
    rows = rc.read_plan(sess_dir)
    total = rc.dataset_total(sess_dir) or 0
    for e in eps:
        if e >= total or e >= len(rows):
            return fail([f"episode {e} 는 아직 녹화되지 않았어요 (dataset {total}편)."])
        if rows[e]["status"] == rc.EXCLUDED:
            return fail([f"episode {e} 는 이미 제외돼 있어요."])
    for e in eps:
        r = rows[e]
        r["status"], r["note"] = rc.EXCLUDED, reason
        rows.append({**{k: r.get(k, "") for k in rc.PLAN_FIELDS}, "episode_index": len(rows), "status": rc.PLANNED,
                     "retake_of": str(e), "frames": "", "note": ""})
        rc.append_event(sess_dir, {"ev": "excluded", "ep": e, "reason": reason})
    rc.write_plan(sess_dir, rows)
    say(f"제외 {eps} → 재촬영 줄 {len(eps)}개 추가 (dataset 은 그대로, 학습 때 제외 목록으로 뺌)")
    return 0


def cmd_label(argv):
    session = opt(argv, "--session")
    ep = int(opt(argv, "--episode"))
    result = opt(argv, "--result")
    retry = opt(argv, "--retry")
    notes = opt(argv, "--notes")
    sess_dir = rc.session_dir(session)
    att = rc.fold_attempts(rc.read_events(sess_dir))
    cand = [a for a in att.values() if a["status"] == "saved" and a.get("ep") == ep]
    if not cand:
        return fail([f"episode {ep} 의 저장 기록이 없어요 (r12_attempts.jsonl)."])
    a = cand[-1]
    lab = dict(a.get("label") or {})
    if result is None and notes is None:
        result = input(f"episode {ep} 결과 [1 첫 파지 성공 / 2 재시도 후 성공 / 3 실패]: ").strip()
        notes = input("메모 (없으면 Enter): ").strip()
    if result:
        lab.update({"1": {"first_grasp_success": True, "final_success": True, "retry_count": 0},
                    "2": {"first_grasp_success": False, "final_success": True, "retry_count": int(retry or 1)},
                    "3": {"first_grasp_success": False, "final_success": False, "retry_count": int(retry or 0)},
                    "4": {"first_grasp_success": False, "final_success": False, "retry_count": int(retry or 0)}}[result])
        pr = rc.read_plan(sess_dir)
        if ep < len(pr) and (pr[ep].get("start_pose_type") or pr[ep].get("approach_stage_expected")):  # R1 재정렬 완료: 1·2·4 = 예, 3 = 아니오
            lab["recovery_completed"] = result in ("1", "2", "4")
    if notes is not None:
        lab["operator_notes"] = notes
    rc.append_event(sess_dir, {"ev": "label", "attempt_id": a["attempt_id"], "via": "label 명령", **lab})
    say(f"episode {ep}: {lab}")
    return 0


# ================================================================ 녹화 (실제 · preview)

def cmd_qa(argv):
    """r12 QA + SG 설정 (sg50 블록) 이면 판 단계 확인 (sg_phase.py: Pan 정렬 → 찾기 → 그리퍼 열림 → 닫기)."""
    code = __import__("r12_qa").main(argv)
    cfgp = opt(argv, "--config")
    if cfgp and (rc.load_config(cfgp).get("sg50")) and "--session" in argv:
        print()
        __import__("sg_phase").main(["--session", opt(argv, "--session")])
    return code


def post_labels(ui):
    """마지막 판처럼 reset 단계가 없어 결과를 못 넣은 저장 판을 터미널에서 묻는다. result_entry: false 면 묻지 않음."""
    if not ui.cfg.get("result_entry", True):
        return
    for ep in ui.saved_eps:
        aid = ui.ep_attempt.get(ep)
        if not aid or aid in ui.labels:
            continue
        r1 = bool((ui.row(ep) or {}).get("r1_setup"))
        try:
            r = input(f"\nepisode {ep} 결과 [1 첫 파지 성공 / 2 재시도 후 성공 / 3 실패" + (" (재정렬 못 함) / 4 재정렬 O·파지 실패" if r1 else "")
                      + " / Enter 나중에]: ").strip()
        except EOFError:
            return
        if r not in (("1", "2", "3", "4") if r1 else ("1", "2", "3")):
            say(f"  나중에: r12_collect.py label --session {CTX['session']} --episode {ep}")
            continue
        ui.pending = aid
        ui.set_label(r)
        try:
            m = input("  메모 (없으면 Enter): ").strip()
        except EOFError:
            m = ""
        if m:
            ui.labels[aid]["operator_notes"] = m
            rc.append_event(CTX["sess_dir"], {"ev": "label", "attempt_id": aid, **ui.labels[aid]})


def cmd_record(argv, preview=False):
    cfgp = opt(argv, "--config")
    cfg = rc.load_config(cfgp)
    no_viewer = opt(argv, "--no-viewer", flag=True)
    sim_err = opt(argv, "--simulate-connect-error", flag=True) if preview else False
    keep_viewer = opt(argv, "--keep-viewer", flag=True)
    scale = opt(argv, "--scale", "1.0")
    geometry = opt(argv, "--viewer-geometry")
    num = opt(argv, "--num")
    camera_mode = opt(argv, "--camera-mode", "auto")
    if preview:
        typ = opt(argv, "--type", "R2").upper()
        src = opt(argv, "--source", "d2")
        n_prev = opt(argv, "--episodes", "3")
        # 2026-11-09: 재생할 기존 녹화 (세션 · 판) — 기본은 이전과 같음 (redbox_t1_known ep5). 예: --preview-session practice/sg50_pilot3 --preview-episode 12
        prev_sess = opt(argv, "--preview-session")
        prev_ep = opt(argv, "--preview-episode")
        prev_dir = None
        if prev_sess:  # 재생 원본은 실제 ~/so101_runs 에서 읽기만 (preview 세션 · 기록은 임시 폴더 그대로)
            m_ = re.match(r"^(practice|main|main_k8)/([a-z0-9_]+)$", prev_sess.strip("/"))
            if not m_:
                return fail([f"--preview-session 형식: <practice|main|main_k8>/<이름> (받은 값 {prev_sess})"])
            prev_dir = os.path.join(os.path.expanduser("~/so101_runs"), m_.group(1), m_.group(2))
            if not os.path.isdir(os.path.join(prev_dir, "review_videos")) or not os.path.isdir(os.path.join(prev_dir, "dataset")):
                return fail([f"재생할 영상 · dataset 이 없어요: {hpath(prev_dir)}"])
        group = opt(argv, "--group") or next(n for n, g in cfg["groups"].items() if g["type"] == typ)
        g = rc.group_of(cfg, group)
        session = g["session"]
        sess = ru.Session(session)
        if not os.path.exists(os.path.join(sess.dir, rc.PLAN_CSV)):
            if cmd_plan(["--group", group] + (["--config", cfgp] if cfgp else [])):
                return 1
    else:
        session = opt(argv, "--session")
        if not session:
            return fail(["--session 이 필요해요 (예: main_k8/r2_pregrasp_pilot)."])
        if protected(session):
            return fail([f"{session} 은 기존 d2 세션이라 쓰지 않아요."])
        group, g = rc.group_for_session(cfg, session)
        if g is None:
            return fail([f"{session} 이 설정 groups 에 없어요 ({', '.join(x['session'] for x in cfg['groups'].values())})."])
        sess = ru.Session(session)
    if argv:
        return fail([f"모르는 옵션: {' '.join(argv)}", "lerobot 옵션은 이 스크립트가 d2 와 같게 만들어요 (직접 넣지 않음)."])
    sess_dir = sess.dir
    if not os.path.exists(os.path.join(sess_dir, rc.PLAN_CSV)):
        return fail([f"계획이 없어요: {hpath(os.path.join(sess_dir, rc.PLAN_CSV))}",
                     f"먼저: ~/so101-env/bin/python {hpath(__file__)} plan --group {group}"])
    meta = rc.read_meta(sess_dir)
    if meta.get("session") != session or meta.get("repo_id") != g["repo_id"]:
        return fail(["계획(r12_plan_meta.json)의 세션·repo_id 가 설정과 달라요."])
    if not os.isatty(sys.stdin.fileno()):
        return fail(["터미널에서 직접 실행해 주세요 (키 입력을 받아야 해요)."])
    if not preview:
        miss = [d for d in ("/dev/so101_follower", "/dev/so101_leader", "/dev/cam_front", "/dev/cam_wrist") if not os.path.exists(d)]
        if miss:
            return fail([f"장치가 없어요: {', '.join(miss)} — lerobot 을 실행하지 않았어요.",
                         "USB·전원 연결을 확인하세요 (udev 이름: ls -l /dev/so101_* /dev/cam_*)."])
        # 2026-11-03: 정책 추론 · 다른 녹화 · 텔레오퍼레이션이 같은 팔을 동시에 움직이지 않게 (읽기만 해서 확인)
        conf = rc.robot_conflicts()
        if conf:
            return fail(["로봇·카메라를 쓰는 다른 프로세스가 있어요 — 녹화를 시작하지 않았어요 (동시 명령 방지)."]
                        + [f"pid {c['pid']}: {c['cmd']}" + (f"  (장치 {', '.join(c['devices'])})" if c["devices"] else "") for c in conf[:6]]
                        + ["그 프로그램을 먼저 끝낸 뒤 다시 실행하세요 (예: 다른 터미널의 eval_ui · lerobot-record · teleoperate)."])

    # ---- dataset 상태 (새로 / 이어 찍기) — preview 는 dataset 을 만들지 않는다
    if preview:
        current = sum(r["status"] == rc.RECORDED for r in rc.read_plan(sess_dir))
        resume = False
    else:
        has = os.path.exists(sess.dataset)
        current = rc.dataset_total(sess_dir) if has else 0
        if has and current == 0 and not os.path.isdir(os.path.join(sess.dataset, "data")) \
                and not os.path.isdir(os.path.join(sess.dataset, "videos")):
            # 이전 실행이 첫 판 저장 전에 끝나 meta 만 남은 빈 dataset → 지우지 않고 이름만 바꿔 옆으로 치움 (2026-10-30)
            stamp = datetime.datetime.fromtimestamp(os.path.getmtime(sess.dataset)).strftime("%Y%m%d_%H%M%S")
            aside = f"{sess.dataset}_empty_{stamp}"
            os.rename(sess.dataset, aside)
            say(f"[r12] 이전 실행이 첫 판 저장 전에 끝나 빈 dataset(meta 만, 0편)이 있었어요 → {hpath(aside)} 로 옮기고 새로 시작해요.")
            has, current = False, 0
        if current is None:
            return fail([f"dataset 정보를 못 읽었어요: {hpath(sess.dataset)}/meta/info.json"])
        resume = has
    rows, _ = sync(sess_dir, cfg, total=current, quiet=True)
    if any(r["status"] == rc.EXCLUDED for r in rows[current:]):
        return fail(["아직 안 찍힌 줄이 excluded 예요 — r12_plan.csv 를 확인하세요."])
    remaining = len(rows) - current
    if remaining <= 0:
        return fail([f"이미 목표를 채웠어요 ({current}/{len(rows)}줄)."])
    n_run = min(int(num), remaining) if num else remaining
    if preview:
        n_run = min(int(n_prev), remaining)
    first = rc.describe_row(cfg, rows[current])
    say(f"\n{'PREVIEW · ' if preview else ''}{session} ({g['type']}) · 계획 {len(rows)}줄 · 지금 {current}편 · 이번 실행 {n_run}편 "
        f"(episode {current}–{current + n_run - 1})" + (" · 이어 찍기" if resume else ""))
    say(f"첫 판 episode {current}: {first['scenario_id']} · {first['title']} · 큐브 {first['position']} · 각도 {first['angle']}")

    setup_max = int(cfg["safety"].get("setup_max_s", 3600))
    args = list(D2_ARGS) + [f"--dataset.repo_id={g['repo_id']}", f"--dataset.single_task={cfg['task_text']}",
                            f"--dataset.episode_time_s={g.get('episode_time_s', 45)}", f"--dataset.reset_time_s={setup_max}",
                            f"--dataset.num_episodes={n_run}"]
    if resume:
        args = ["--resume=true"] + args
    if preview:
        args = [f"--preview-source={src}", f"--preview-start={current}"] + (["--simulate-connect-error"] if sim_err else []) \
            + ([f"--preview-session={prev_dir}"] if prev_dir else []) + ([f"--preview-episode={int(prev_ep)}"] if prev_ep else []) \
            + [a for a in args if a.startswith("--dataset.")]
    else:
        args.append(f"--dataset.root={sess.dataset}")

    # ---- 녹화 전 점검 (record_ui 와 같은 읽기 전용 점검 + R1/R2 체크리스트)
    extra = [*cfg.get("checklist", {}).get(g.get("pilot_variant") or g["type"], cfg.get("checklist", {}).get(g["type"], [])),  # R1/R2 혼동 방지 (11-02)
             f"첫 판(episode {current}) 큐브를 {first['position']} 에 각도 {first['angle']} 로 놓았나요?",
             "준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요",
             "→ 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작",
             "필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음)"]
    if preview:
        say("\n[preview] 녹화 전 장치 점검은 건너뜀 (장치를 쓰지 않음). 체크리스트만 보여 줘요:")
        for c in extra:
            say(f"  □ {c}")
        check_notes = ["- preview: 장치 점검 생략"]
    else:
        check_notes, _, go = ru.precheck(camera_mode, extra)
        if not go:
            say("취소했어요. lerobot 을 실행하지 않았어요.")
            return 1

    # ---- 실행 기록 (record_ui 와 같은 sidecar → 후처리의 notes 결과 표)
    now = datetime.datetime.now()
    run_id = now.strftime("%Y%m%d_%H%M%S")
    live = rc.live_dir_for(run_id + ("_preview" if preview else ""))
    for f in os.listdir(live):
        os.unlink(os.path.join(live, f))
    os.makedirs(ru.LOG_DIR, exist_ok=True)
    log_path = os.path.join(ru.LOG_DIR, f"record_{run_id}.log")
    side_path = log_path[:-4] + ".json"
    exe = FAKE if preview else ENTRY
    wrapper_cmd = shlex.join([VENV_PY, os.path.abspath(__file__), "preview" if preview else "record"] + sys.argv[2:])
    run = {"run_id": run_id, "started": now.strftime("%Y-%m-%d %H:%M"), "mode": "이어 찍기" if resume else "새 녹화",
           "session": session, "camera_mode": camera_mode, "wrapper_cmd": wrapper_cmd, "lerobot_args": args, "log": log_path,
           "episodes_before": current, "target_episodes": str(len(rows)), "layout": os.path.join(sess_dir, rc.PLAN_CSV),
           "r12": {"group": group, "type": g["type"], "entry": exe, "preview": preview, "live": live},
           "code_version": rc.code_version(), "config": cfg["_path"].replace(HOME, "$HOME"), "config_sha256": cfg["_sha256"],
           "config_extends_sha256": cfg.get("_extends_sha256", ""),
           "teleop_guard": (cfg["safety"].get("teleop_guard") or {}).get("enabled", False)}
    if cfg.get("sg50"):  # SG50: 녹화 시작 때 카메라 H · 서보 보정 파일 해시 (판 기록 sg_episodes.csv 가 run_id 로 읽음)
        import sg_plan

        run["sg50_calib"] = sg_plan.calib_versions(cfg)
    with open(side_path, "w") as f:
        json.dump(run, f, ensure_ascii=False, indent=1)
    ru.ensure_layout(sess)
    if not preview:
        section = "\n".join(["", f"### {run['started']} · {run['mode']} (R1/R2 r12_collect) <!-- run:{run_id} -->", "",
                             "**녹화 전 점검**", *check_notes, "", "**명령**", "```bash", wrapper_cmd.replace(HOME, "$HOME"), "```",
                             "실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):",
                             "```bash", shlex.join([exe] + args).replace(HOME, "$HOME"), "```", f"- 원본 로그: `{hpath(log_path)}`",
                             f"- 계획: `{hpath(os.path.join(sess_dir, rc.PLAN_CSV))}` · 이번 실행 episode {current}–{current + n_run - 1}", ""])
        with open(sess.notes, "a") as f:
            f.write(section)

    os.environ.update(R12_LIVE_DIR=live, R12_CONFIG=cfg["_path"], R12_RUN_ID=run_id,
                      R12_START_DIR=os.path.join(sess_dir, rc.START_FRAMES_DIR))
    CTX.update(cfg=cfg, rows=rows, sess_dir=sess_dir, session=session, type=g["type"], live=live, run_id=run_id, preview=preview,
               code_version=run.get("code_version", ""))
    if preview:
        CTX["preview_frames"] = "더미 영상" if src == "dummy" else "기존 녹화 영상 재생"
    viewer = None
    if not no_viewer and os.environ.get("DISPLAY"):
        if geometry:
            rc.write_json(os.path.join(live, "viewer_geometry.json"), {"geometry": geometry})
        vlog = open(os.path.join(live, "viewer.log"), "w")
        viewer = subprocess.Popen([VENV_PY, SG_VIEWER if cfg.get("viewer") == "sg" else VIEWER, "--live", live, "--scale", scale], stdout=vlog, stderr=vlog,
                                  env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        say(f"[r12] 영상 창을 열었어요 (pid {viewer.pid}). 키는 이 터미널이나 영상 창 어디서 눌러도 돼요.")
    elif not no_viewer:
        say("[r12] DISPLAY 가 없어 영상 창 없이 진행해요 (터미널 배너만).")

    ru.LEROBOT_RECORD = exe
    ru.UI = make_ui_class()
    _fork = ru.pty.fork

    def _fork_keep_master():  # 영상 창에서 누른 키를 터미널 키와 같은 길로 lerobot 에 넘기려고 pty master 를 기억
        pid, m = _fork()
        if pid:
            CTX["master"] = m
        return pid, m
    ru.pty = types.SimpleNamespace(fork=_fork_keep_master)
    if preview:
        CTX["preview_label"] = "로봇·카메라 연결 없음"
    status, ui = ru.run_lerobot(args, log_path)
    if preview:
        src_info = rc.read_json(os.path.join(live, "preview_source.json"), {}) or {}
        CTX["preview_label"] = src_info.get("label", "")

    run.update(exit_code=status, interrupted=ui.interrupted, saved=ui.saved, ended=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
               episodes_after=(current + ui.saved) if preview else rc.dataset_total(sess_dir))
    with open(side_path, "w") as f:
        json.dump(run, f, ensure_ascii=False, indent=1)
    post_labels(ui)
    say("\n── 기록 정리 ──")
    sync(sess_dir, cfg, total=(current + ui.saved) if preview else None)
    if not preview:
        if status == 0 and not ui.interrupted:
            rcode = subprocess.call([VENV_PY, os.path.join(SCRIPTS, "record_ui.py"), "--postprocess", session])
            if rcode != 0:
                say(f"⚠ 후처리 실패 (코드 {rcode}). 다시: python3 {hpath(os.path.join(SCRIPTS, 'record_ui.py'))} --postprocess {session}")
        else:
            ru.abnormal_help(sess, status, ui, log_path, args)
        say(f"품질 검사 (읽기만): ~/so101-env/bin/python {hpath(os.path.abspath(__file__))} qa --session {session}")
    else:
        say(f"[preview] 기록은 임시 폴더에만: {sess_dir}")
    if viewer is not None and not keep_viewer:
        viewer.terminate()
    return status if status >= 0 else 128 - status


def cmd_preview(argv):
    """로봇 없이 같은 UI 를 실행. 세션·로그는 임시 폴더 (기본 /tmp/r12_preview_<시각>) — ~/so101_runs 를 건드리지 않음."""
    root = opt(argv, "--root") or os.path.join("/tmp", f"r12_preview_{datetime.datetime.now():%Y%m%d_%H%M%S}")
    os.makedirs(root, exist_ok=True)
    os.environ["RECORD_UI_RUNS"] = os.path.join(root, "runs")
    os.environ["RECORD_UI_LOG_DIR"] = os.path.join(root, "logs")
    load_mods()
    assert os.path.abspath(ru.RUNS_ROOT).startswith(os.path.abspath(root)), "preview 가 실제 세션 폴더를 가리킴"
    assert os.path.abspath(rc.RUNS_ROOT).startswith(os.path.abspath(root))
    say(f"[preview] 임시 폴더 {root} — 로봇·카메라·lerobot 을 쓰지 않아요.")
    return cmd_record(argv, preview=True)


# ================================================================ 환경 확인 · 품질 검사

def cmd_check(argv):
    cfg = rc.load_config(opt(argv, "--config"))
    ok = True
    say("── 환경 확인 (장치를 열지 않음) ──")
    for p in (cfg["_path"], rc._expand(cfg["base_config"]), rc._expand(cfg["safety"]["calibration"]), ENTRY, FAKE, VIEWER,
              os.path.join(SCRIPTS, "record_ui.py")):
        e = os.path.exists(p)
        ok &= e
        say(f"  {'✓' if e else '✗'} {hpath(p)}")
    for d in ("/dev/so101_follower", "/dev/so101_leader", "/dev/cam_front", "/dev/cam_wrist"):
        say(f"  {'✓' if os.path.exists(d) else '·'} {d} {'있음' if os.path.exists(d) else '없음 (녹화 때 필요)'}")
    lim = rc.calib_limits(cfg)
    say("  관절 한계 (follower 캘리브레이션 → °): " + ", ".join(f"{rc.SHORT[j]} {lo:+.1f}/{hi:+.1f}" for j, (lo, hi) in lim.items()))
    say(f"  DISPLAY={os.environ.get('DISPLAY') or '없음'}")
    # lerobot record 모듈과 진입점이 맞는지 (모듈만 불러옴 — 로봇·카메라 연결 없음)
    import inspect
    import importlib

    lr = importlib.import_module("lerobot.scripts.lerobot_record")
    need = ["robot", "events", "fps", "teleop_action_processor", "robot_action_processor", "robot_observation_processor",
            "dataset", "teleop", "control_time_s", "single_task", "display_data", "display_mode", "display_compressed_images", "timer"]
    import ast

    fn = next(n for n in ast.walk(ast.parse(inspect.getsource(lr))) if isinstance(n, ast.FunctionDef) and n.name == "record_loop")
    got = [a.arg for a in fn.args.args + fn.args.kwonlyargs]  # @safe_stop_image_writer 로 감싸여 있어 소스에서 읽음
    sig_ok = got == need
    ok &= sig_ok
    say(f"  {'✓' if sig_ok else '✗'} lerobot record_loop 인자 = 진입점이 가정한 것" + ("" if sig_ok else f" (실제 {got})"))
    import lerobot

    say(f"  lerobot {getattr(lerobot, '__version__', '?')}")
    src = inspect.getsource(lr.record)
    for frag in ("record_loop(", "log_say(\"Reset the environment\"", "dataset.save_episode()", "events[\"rerecord_episode\"]"):
        f_ok = frag in src
        ok &= f_ok
        say(f"  {'✓' if f_ok else '✗'} record() 안에 {frag}")
    say("확인 끝: " + ("문제 없음" if ok else "빠진 것이 있어요"))
    return 0 if ok else 1


def main():
    argv = sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd == "preview":
        return cmd_preview(rest)
    load_mods()
    fn = {"menu": cmd_menu, "plan": cmd_plan, "status": cmd_status, "record": cmd_record, "label": cmd_label, "exclude": cmd_exclude,
          "check": cmd_check, "qa": cmd_qa,
          "sync": lambda a: (sync(rc.session_dir(opt(a, "--session")), rc.load_config(opt(a, "--config"))), 0)[1]}.get(cmd)
    if fn is None:
        return fail([f"모르는 명령: {cmd}"])
    try:
        return fn(rest)
    except rc.PlanError as e:
        return fail([str(e)])


if __name__ == "__main__":
    sys.exit(main())
