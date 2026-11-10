"""HIL 세션 QA (읽기 전용). 사용: python hil_qa.py <session_dir>   (session_dir 안에 dataset/ 와 hil_events.jsonl)

출력: <session_dir>/qa/hil_qa.csv · hil_qa.md. 원본 dataset · events 는 읽기만 한다.
판별을 하지 않고 측정값과 표시 키 기록, 작업 지시 §8 에 따른 '변환 제외 사유' 만 적는다.
표시 필드 (2026-11-04 사용자 결정): 복구 완료 (m) · 첫 파지 (g 성공 / h 실패) · 최종 작업 (b 상자 안 성공 / f 실패).
변환 제외 사유: 원위치 구간 (r) · 교정 도중 세션 종료 (Esc · 오류 · Ctrl+C) · 최종 실패 (f) · 최종 결과 미입력 · 15 frame 미만.
"""

from __future__ import annotations

import csv
import glob
import json
import sys
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

J = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
D2_TASK = "pick up the red cube and put it in the brown box"


def main():
    sess = Path(sys.argv[1])
    ds = sess / "dataset"
    import pandas as pd

    df = pd.concat([pq.read_table(f).to_pandas() for f in sorted(glob.glob(str(ds / "data/*/*.parquet")))], ignore_index=True)
    meta = pd.concat([pq.read_table(f).to_pandas() for f in sorted(glob.glob(str(ds / "meta/episodes/*/*.parquet")))], ignore_index=True)
    tasks = pq.read_table(ds / "meta/tasks.parquet").to_pandas()
    task_names = {int(r["task_index"]): (r["task"] if "task" in r else r.name) for _, r in tasks.reset_index().iterrows()}
    info = json.loads((ds / "meta/info.json").read_text())
    fps = info["fps"]
    evs = [json.loads(x) for x in (sess / "hil_events.jsonl").read_text().splitlines()] if (sess / "hil_events.jsonl").exists() else []

    per = {}
    last_snap = None
    for e in evs:
        if e["kind"] == "transition":
            if e.get("pre_pause_snapshot"):
                last_snap = e["pre_pause_snapshot"]
            if e["old"] == "paused" and e["new"] == "correcting":
                ep = e.get("episodes_saved")
                per.setdefault(ep, {})["start_snapshot"] = last_snap
                per[ep]["start_follower"] = e.get("follower")
                per[ep]["start_leader_after"] = e.get("leader_after")
                per[ep]["start_wall"] = e["wall"]
                last_snap = None
            if e["old"] == "correcting" and e["new"] == "paused":
                per.setdefault(e.get("episodes_saved"), {})["frames_at_end"] = e.get("frames_in_current")
        elif e["kind"] == "mark":
            ep = e.get("episodes_saved")
            d = per.setdefault(ep, {})
            mk = e["mark"]
            if mk.startswith("type_"):
                d["type"] = mk[5:].replace("R2O", "R2-O")
            elif mk in ("recovery_done", "recovery_end"):
                d.setdefault("recovery_done_frames", []).append(e.get("frames_in_current"))
            elif mk in ("first_grasp_ok", "first_grasp_fail"):
                d.setdefault("first_grasp", "ok" if mk.endswith("ok") else "fail")  # 첫 표시만
            elif mk in ("final_success", "final_fail"):
                d["final"] = "success" if mk == "final_success" else "fail"  # 마지막 표시
            elif mk == "reset_segment":
                d["reset"] = True
        elif e["kind"] == "session_end" and e.get("ended_during_correction"):
            per.setdefault((e.get("episodes_saved") or 1) - 1, {})["ended_during_correction"] = True

    rows = []
    for ep in sorted(df["episode_index"].unique()):
        sub = df[df.episode_index == ep]
        a = np.stack(sub["action"].to_numpy())
        s = np.stack(sub["observation.state"].to_numpy())
        m = meta[meta.episode_index == ep].iloc[0]
        d = per.get(int(ep), {})
        ts = sub["timestamp"].to_numpy()
        vid_dur = {c: float(m[f"videos/observation.images.{c}/to_timestamp"] - m[f"videos/observation.images.{c}/from_timestamp"]) for c in ("front", "wrist")}
        r = {
            "episode": int(ep), "frames": len(sub), "duration_s": round(len(sub) / fps, 2),
            "intervention_all_true": bool(np.all(np.stack(sub["intervention"].to_numpy()).astype(bool))) if "intervention" in sub else "",
            "task_is_d2": all(task_names.get(int(t)) == D2_TASK for t in sub["task_index"].unique()),
            "timestamp_step_ok": bool(np.allclose(np.diff(ts), 1 / fps, atol=1e-4)) if len(ts) > 1 else True,
            "video_minus_data_s_front": round(vid_dur["front"] - len(sub) / fps, 3), "video_minus_data_s_wrist": round(vid_dur["wrist"] - len(sub) / fps, 3),
            "type": d.get("type", "미입력"),
            "recovery_done": "예" if d.get("recovery_done_frames") else "미입력",
            "recovery_done_frame": ";".join(str(x) for x in d.get("recovery_done_frames", [])),
            "first_grasp": d.get("first_grasp", "미입력"), "final_task": d.get("final", "미입력"),
            "reset_segment": bool(d.get("reset", False)),
            "ended_during_correction": bool(d.get("ended_during_correction", False)),
            "first_frame_action_minus_state_max_arm_deg": round(float(np.abs(a[0, :5] - s[0, :5]).max()), 2),
            "first_frame_action_minus_state_gripper": round(float(a[0, 5] - s[0, 5]), 2),
            "max_action_minus_state_arm_deg": round(float(np.abs(a[:, :5] - s[:, :5]).max()), 2),
            # max_relative_target=8 이면 follower 명령은 present±8° 로 잘리지만 저장 action 은 clamp 전 리더 값 → 이 차이가 커진다
            "frames_action_minus_state_arm_gt8": int((np.abs(a[:, :5] - s[:, :5]).max(axis=1) > 8.0).sum()),
            "gripper_action_min": round(float(a[:, 5].min()), 1), "gripper_action_max": round(float(a[:, 5].max()), 1),
            "gripper_state_min": round(float(s[:, 5].min()), 1),
            "start_pan_state": round(float(s[0, 0]), 1),
            "pre_pause_snapshot": d.get("start_snapshot") or "", "start_wall": d.get("start_wall", ""),
        }
        why = []
        if r["reset_segment"]:
            why.append("원위치 구간(r)")
        if r["ended_during_correction"]:
            why.append("교정 도중 세션 종료")
        if r["final_task"] == "fail":
            why.append("최종 실패(f)")
        elif r["final_task"] == "미입력" and not r["reset_segment"]:
            why.append("최종 결과 미입력")
        if r["frames"] < 15:
            why.append("15 frame 미만")
        r["변환_제외_사유"] = " · ".join(why)
        rows.append(r)

    out = sess / "qa"
    out.mkdir(exist_ok=True)
    with open(out / "hil_qa.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    cols = ["episode", "frames", "duration_s", "type", "recovery_done", "recovery_done_frame", "first_grasp", "final_task", "reset_segment",
            "ended_during_correction",
            "first_frame_action_minus_state_max_arm_deg", "max_action_minus_state_arm_deg", "frames_action_minus_state_arm_gt8", "gripper_action_min", "gripper_action_max", "intervention_all_true", "task_is_d2",
            "timestamp_step_ok", "video_minus_data_s_front", "변환_제외_사유"]
    L = [f"# HIL QA — {sess.name} (hil_qa.py 자동 생성, 측정값만)", "", f"판 {len(rows)} · fps {fps} · events {len(evs)} 줄", "",
         "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    L += ["| " + " | ".join(str(r[c]) for c in cols) + " |" for r in rows]
    (out / "hil_qa.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
