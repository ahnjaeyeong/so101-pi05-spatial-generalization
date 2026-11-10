"""HIL 수집자 화면 — 미리보기 상태 (가짜 사실값 + 합성 영상). 실물 · tap · 로봇 명령 없음. 화면 상단에 PREVIEW 로 표시된다."""

from __future__ import annotations

import hil_ui_render as R

BASE = {"session": "running", "phase": "paused", "pending": None, "in_transition": False, "transition": None, "last_transition": None,
        "transition_age": None, "leader_torque": True, "policy_active": False, "last_policy_send_age": None, "policy_since_pause": False,
        "fault": None, "follower_io_error": None, "episodes_saved": 3, "frames_in_current": 0, "marks_current": [], "type_current": None,
        "last_saved": None, "end_menu": None, "end_choice": None, "clamp_deg": 8.0, "start_paused": True, "since_transition_end": 1.5}

FAULT = {"kind": "inference_error", "msg": "RTC inference error (1/10): CUDA error", "handled": True, "rtc_qsize_before": 30, "rtc_qsize_after": 0}
SAVED_OK = {"episode": 3, "frames": 212, "marks": ["type_R2", "recovery_done", "first_grasp_ok", "final_success"], "ended_during_correction": False}
SAVED_MISSING = {"episode": 4, "frames": 160, "marks": ["type_R1"], "ended_during_correction": False}

# (이름, 사실값 덮어쓰기, 손목 합성 장면)
STATES = [
    ("01_policy_wait", {}, {"grip": "open", "cube": [0.36, 0.3]}),
    ("02_policy_running", {"phase": "autonomous", "policy_active": True, "last_policy_send_age": 0.03, "leader_torque": False,
                           "last_transition": ["paused", "autonomous"]}, {"grip": "open", "cube": [0.36, 0.2], "cut": "top"}),
    ("03_stop_requested", {"phase": "autonomous", "pending": "pause_resume", "policy_active": True, "last_policy_send_age": 0.03,
                           "leader_torque": False}, {"grip": "open", "cube": [0.36, 0.17], "cut": "top"}),
    ("04_leader_aligning", {"in_transition": True, "transition": ["autonomous", "paused"], "transition_age": 0.9, "leader_torque": True,
                            "policy_active": False}, {"grip": "open", "cube": [0.36, 0.17], "cut": "top"}),
    ("05_human_ready", {"last_transition": ["autonomous", "paused"]}, {"grip": "open", "cube": [0.36, 0.17], "cut": "top"}),
    ("06_correcting_R1", {"phase": "correcting", "last_transition": ["paused", "correcting"], "leader_torque": False,
                          "marks_current": ["type_R1"], "type_current": "R1", "frames_in_current": 45}, R.GUIDES["R1"][1][1]),
    ("07_correcting_R2", {"phase": "correcting", "last_transition": ["paused", "correcting"], "leader_torque": False,
                          "marks_current": ["type_R2", "recovery_done"], "type_current": "R2", "frames_in_current": 88}, R.GUIDES["R2"][2][1]),
    ("08_correcting_R2O", {"phase": "correcting", "last_transition": ["paused", "correcting"], "leader_torque": False,
                           "marks_current": ["type_R2O", "recovery_done", "first_grasp_ok"], "type_current": "R2-O", "frames_in_current": 130},
     R.GUIDES["R2-O"][3][1]),
    ("09_result", {"last_transition": ["correcting", "paused"], "last_saved": SAVED_OK, "episodes_saved": 4}, {"grip": "grasp", "cube": list(R.T)}),
    ("10_fault_locked", {"fault": FAULT, "last_transition": ["autonomous", "paused"], "policy_since_pause": True},
     {"grip": "open", "cube": [0.4, 0.35]}),
    ("11_end_menu", {"session": "teardown", "end_menu": {"options": ["home", "release", "hold"], "follower_ok": True}, "last_saved": SAVED_OK},
     {"grip": "open", "cube": [0.36, 0.3]}),
    # 추가 (경계 상태)
    ("12_stop_confirming", {"in_transition": True, "transition": ["autonomous", "paused"], "transition_age": 0.05, "leader_torque": False,
                            "policy_active": False}, {"grip": "open", "cube": [0.36, 0.17], "cut": "top"}),
    ("13_uncertain", {"last_transition": ["autonomous", "paused"], "policy_since_pause": True}, {"grip": "open", "cube": [0.36, 0.17], "cut": "top"}),
    ("14_correcting_no_type", {"phase": "correcting", "last_transition": ["paused", "correcting"], "leader_torque": False,
                               "frames_in_current": 12}, {"grip": "open", "cube": [0.36, 0.17], "cut": "top"}),
    ("15_result_review_needed", {"last_transition": ["correcting", "paused"], "last_saved": SAVED_MISSING, "episodes_saved": 5},
     {"grip": "grasp", "cube": list(R.T)}),
    ("16_end_menu_follower_fault", {"session": "teardown", "end_menu": {"options": ["release", "hold"], "follower_ok": False},
                                    "follower_io_error": "send_action: ConnectionError: [TxRxResult] There is no status packet"},
     {"grip": "open", "cube": [0.36, 0.3]}),
    ("17_unknown_stale", {"_stale": True}, None),
]


def raw_for(name, now):
    for n, over, scene in STATES:
        if n == name:
            raw = {**BASE, **over}
            raw["t"] = now - (5.0 if over.get("_stale") else 0.05)
            return raw, scene
    raise KeyError(name)


def frames_for(scene, code):
    if scene is None:
        return {"wrist": None, "front": None}
    return {"wrist": R.synth_wrist(scene, (640, 480)), "front": R.synth_front(code, (320, 240))}
