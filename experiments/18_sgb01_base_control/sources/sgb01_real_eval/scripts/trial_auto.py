"""시행 하나의 자동 지표 (읽기만, CPU, 로봇 · 카메라 연결 없음). post_trial.sh 가 r2_analyze 뒤에 부른다.

입력: eval_ui 실행 폴더 (판 1 개). 원본 실행 폴더에는 쓰지 않는다.
출력: <세션>/reports/<run>/trial_auto.json · trial_auto.md   (이미 있으면 덮어쓰지 않고 _<시각> 붙임)

값 종류: [기록] 파일에서 그대로 · [자동 후보] 규칙으로 계산한 후보 (사용자 판정 아님 — record_trial.py 에서 사용자가 따로 입력)
  run · 모델 · SHA · 코드 SHA          [기록] trial_manifest.json (run_trial.sh)
  큐브 위치 · 각도                     [기록] r2_safety.csv plan_check (시작 front 사진 cube_coords.estimate) + reports/<run>/episodes.csv
  시작 관절값                          [기록] dataset 첫 frame observation.state (+ pose_check.txt)
  영상 · state/action                 [기록] dataset/videos · dataset/data parquet · filter_log.csv 경로
  첫 닫힘 결과 · 빈 닫힘               [자동 후보] reports/<run>/events.csv (r2_analyze T4: grasp / empty / undetermined)
  Pan 방향 반전                        [자동 후보] present pan (dataset observation.state) 을 시작 pan → 큐브 방위 pe (r2_safety episode_start) 방향으로
                                      투영한 진행량이 최대치에서 REV_DEG 이상 되돌아가면 반전 1 회 (히스테리시스). 첫 닫힘 (T2) 전 · 판 전체 따로.
  Wrist 큐브 재획득                    [자동 후보] 손목 영상 3 frame 마다 빨강 검출 (r2_analyze.wrist_measure_bbox = p14 와 같음).
                                      보임 ≥ 0.3 s 뒤 안 보임 ≥ LOST_S → '놓침', 그 뒤 다시 보임 ≥ 0.3 s → '재획득'. 첫 파지 (T4 grasp 의 T2) 전까지만.
  안전 개입                            [기록] r2_safety.csv STOP · fault_latch.csv FAULT · eval_ui console (Ctrl+C) · results.csv
사용: PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python trial_auto.py <run 폴더> [--ep 0] [--out <폴더>]
"""
import argparse
import csv
import datetime
import glob
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

S_DIR = Path(__file__).resolve().parents[1]
K8 = Path.home() / "so101_runs/main_k8"
R2S = K8 / "r2_grasp_diagnostic/scripts"
REV_DEG = 5.0      # 반전 히스테리시스 (°)
REV_MIN_TRAVEL = 5.0  # 반전으로 세기 전 최소 진행 (°)
LOST_S = 1.0
SEEN_S = 0.3
STEP = 3


def read_csv(p):
    return list(csv.DictReader(open(p, newline=""))) if os.path.exists(p) else []


def pan_reversals(pan, s0, pe, n_end=None):
    """진행량 = d·(pan − s0), d = sign(pe − s0). 반전 = 진행 최대치에서 REV_DEG 이상 되돌아감 (그 뒤 새 최소에서 다시 REV_DEG 진행하면 재개)."""
    if pe is None or not np.isfinite(pe) or len(pan) == 0:
        return None
    d = 1.0 if pe >= s0 else -1.0
    p = d * (np.asarray(pan[:n_end] if n_end else pan) - s0)
    ev, mode, ext, i_ext = [], "fwd", p[0], 0
    for i, x in enumerate(p):
        if mode == "fwd":
            if x > ext:
                ext, i_ext = x, i
            elif ext >= REV_MIN_TRAVEL and ext - x >= REV_DEG:
                ev.append({"i_peak": int(i_ext), "pan_peak": float(pan[i_ext]), "progress_peak": float(ext), "i_detect": int(i)})
                mode, ext, i_ext = "back", x, i
        else:
            if x < ext:
                ext, i_ext = x, i
            elif x - ext >= REV_DEG:
                ev[-1].update(i_back_min=int(i_ext), pan_back_min=float(pan[i_ext]), back_deg=float(ev[-1]["progress_peak"] - ext))
                mode, ext, i_ext = "fwd", x, i
    if ev and mode == "back":
        ev[-1].update(i_back_min=int(i_ext), pan_back_min=float(pan[i_ext]), back_deg=float(ev[-1]["progress_peak"] - ext))
    past = d * (np.asarray(pan) - pe)
    return {"direction_to_target": "+" if d > 0 else "−", "n_reversals": len(ev), "events": ev,
            "max_past_target_deg": float(past.max()), "i_max_past": int(past.argmax()), "pan_min": float(np.min(pan)), "pan_max": float(np.max(pan))}


def wrist_segments(vis_idx, vis, fps=30):
    """vis: 표본 frame 들의 보임 여부. 반환 (놓침 구간 목록, 재획득 여부)."""
    lost, seen_run, gap_start, seen_before = [], 0, None, False
    reacq = False
    need_seen = max(1, int(round(SEEN_S * fps / STEP)))
    need_lost = max(1, int(round(LOST_S * fps / STEP)))
    run_v, run_nv = 0, 0
    cur_lost = None
    for k, (i, v) in enumerate(zip(vis_idx, vis)):
        if v:
            run_v += 1
            run_nv = 0
            if run_v >= need_seen:
                if cur_lost is not None:
                    cur_lost["reacquired_i"] = int(vis_idx[k - need_seen + 1])
                    lost.append(cur_lost)
                    reacq = True
                    cur_lost = None
                seen_before = True
        else:
            run_nv += 1
            run_v = 0
            if seen_before and run_nv >= need_lost and cur_lost is None:
                cur_lost = {"lost_i": int(vis_idx[k - need_lost + 1])}
    if cur_lost is not None:
        cur_lost["reacquired_i"] = None
        lost.append(cur_lost)
    return lost, reacq, seen_before


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--ep", type=int, default=0, help="dataset 판 번호 (파일럿은 run 마다 1 판 = 0)")
    ap.add_argument("--out", help="출력 폴더 (기본 <세션>/reports/<run>)")
    ap.add_argument("--no-wrist", action="store_true")
    a = ap.parse_args()
    run = Path(a.run).resolve()
    out = Path(a.out) if a.out else S_DIR / "reports" / run.name
    if str(out.resolve()).startswith(str(run)):
        raise SystemExit("출력 경로가 원본 run 폴더 안 — 거부")
    out.mkdir(parents=True, exist_ok=True)
    R = {"run_id": run.name, "run_dir": str(run), "ep": a.ep, "notes": []}

    man = run / "trial_manifest.json"
    R["manifest"] = json.loads(man.read_text()) if man.exists() else None
    if R["manifest"] is None:
        R["notes"].append("trial_manifest.json 없음 (run_trial.sh 로 실행한 run 이 아님)")

    ui = [r for r in read_csv(run / "results.csv") if int(r.get("ep", -1)) == a.ep]
    R["eval_ui"] = ui[0] if ui else None

    # dataset
    pq = sorted(glob.glob(str(run / "dataset/data/*/*.parquet")))
    df = pd.concat([pd.read_parquet(p) for p in pq]) if pq else pd.DataFrame()
    df = df[df.episode_index == a.ep] if len(df) else df
    if len(df):
        st = np.stack(df["observation.state"].values)
        R["start_joints"] = dict(zip(["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"], st[0].round(2).tolist()))
        R["n_frames"] = int(len(df))
    else:
        st = np.zeros((0, 6))
        R["start_joints"], R["n_frames"] = None, 0
        R["notes"].append("dataset 프레임 없음")
    R["paths"] = {"dataset": str(run / "dataset"), "videos": sorted(str(Path(p).relative_to(run)) for p in glob.glob(str(run / "dataset/videos/**/*.mp4"), recursive=True)),
                  "parquet": [str(Path(p).relative_to(run)) for p in pq], "filter_log": "filter_log.csv" if (run / "filter_log.csv").exists() else None,
                  "pose_check": "pose_check.txt" if (run / "pose_check.txt").exists() else None, "diag": "diag" if (run / "diag").exists() else None}
    R["pose_check_txt"] = (run / "pose_check.txt").read_text()[-1500:] if (run / "pose_check.txt").exists() else None

    # r2_safety · fault_latch
    rs = read_csv(run / "r2_safety.csv")
    # v3 (11-05) 연속 세션 run (판 여러 개): r2_safety 의 episode 열 = 정책 루프 순번 (버린 판 없으면 dataset 판 번호와 같음)
    rs = [r for r in rs if r.get("episode") in ("", None) or str(r.get("episode")) == str(a.ep)]
    pe, s0 = None, None
    for r in rs:
        if r["event"] == "episode_start":
            for tok in r["detail"].split():
                if tok.startswith("pe="):
                    pe = float(tok[3:]) if tok[3:] else None
                if tok.startswith("start_pan="):
                    s0 = float(tok[10:])
    R["pe_source"] = "r2_safety.csv episode_start" if pe is not None else None
    if pe is None:  # 옛 run (r2_safety 없음): 시작 front 사진에서 r2_safety.pe_from_front 와 같은 계산
        img = run / "start_images" / f"ep{a.ep:03d}_front.png"
        if img.exists():
            sys.path.insert(0, str(K8 / "r2_grasp_diagnostic/eval"))
            import cv2
            import r2_safety as RS
            pe, why = RS.pe_from_front(cv2.cvtColor(cv2.imread(str(img)), cv2.COLOR_BGR2RGB))
            R["pe_source"] = f"start_images front (pe_from_front: {why})"
    R["pe_start_photo"], R["start_pan"] = pe, s0
    R["plan_check"] = [r["detail"] for r in rs if r["event"] == "plan_check"]
    R["plan_check_warn"] = [r["action"] for r in rs if r["event"] == "plan_check" and r["action"]]
    R["safety_stops"] = [{k: r[k] for k in ("tick", "rule", "detail", "cmd_pan", "present_pan", "qsize_before", "qsize_after", "action")} for r in rs if r["event"] == "STOP"]
    R["safety_warns"] = [{k: r[k] for k in ("tick", "rule", "detail")} for r in rs if r["event"] == "warn"]
    R["n_blocked_r2"] = sum(1 for r in rs if r["event"] == "blocked")
    fl = read_csv(run / "fault_latch.csv")
    R["fault_events"] = [{k: r[k] for k in ("event", "kind", "tick", "msg", "qsize_before", "qsize_after", "since_fault_s")} for r in fl if r["event"].startswith("FAULT")]
    es_p = run / "end_state.json"  # v2 end_hold
    R["end_state"] = json.loads(es_p.read_text()) if es_p.exists() else None
    eh = read_csv(run / "end_hold.csv")
    R["end_hold_events"] = [r["event"] for r in eh]
    con = (run / "console.log").read_bytes().decode("utf-8", "replace") if (run / "console.log").exists() else ""
    R["console_flags"] = {"ctrl_c": ("KeyboardInterrupt" in con), "traceback": ("Traceback" in con), "rtc_error": ("RTC inference error" in con),
                          "fatal": ("Fatal error in RTC thread" in con), "r2_safety_stop": ("R2_SAFETY STOP" in con), "fault_latch": ("FAULT_LATCH" in con)}

    # r2_analyze 결과
    ev = [r for r in read_csv(out / "events.csv")]
    eps = [r for r in read_csv(out / "episodes.csv") if str(r.get("ds_ep")) == str(a.ep)]
    R["cube"] = {k: eps[0].get(k) for k in ("cube_x", "cube_y", "cube_yaw_deg", "coord_status", "nearest_K", "dist_K_cm", "angle_class", "plan_label",
                                           "position_group")} if eps else None
    if not eps:
        R["notes"].append("reports/<run>/episodes.csv 없음 — post_trial.sh 의 r2_analyze 먼저")
    evs = [r for r in ev if str(r.get("ds_ep")) == str(a.ep)]
    evs.sort(key=lambda r: int(r["close_k"]))
    first = evs[0] if evs else None
    i_first_grasp = next((int(r["T2_i"]) for r in evs if r["T4"] == "grasp"), None)
    pre = [r for r in evs if i_first_grasp is None or int(r["T2_i"]) < i_first_grasp]
    R["closes"] = [{k: r.get(k) for k in ("close_k", "T2_i", "T2_s", "T4", "T4_bottom", "after_first_grasp")} for r in evs]
    R["auto"] = {"first_close_T4": first["T4"] if first else "no_close",
                 "first_close_T2_s": float(first["T2_s"]) if first else None,
                 "n_closes": len(evs),
                 "n_empty_before_first_grasp": sum(1 for r in pre if r["T4"] == "empty"),
                 "any_grasp": i_first_grasp is not None, "first_grasp_T2_i": i_first_grasp}

    # Pan 반전
    pan = st[:, 0] if len(st) else np.zeros(0)
    s0_ = s0 if s0 is not None else (float(pan[0]) if len(pan) else None)
    n_pre = int(first["T2_i"]) if first else None
    R["auto"]["pan_pre_first_close"] = pan_reversals(pan, s0_, pe, n_pre) if s0_ is not None else None
    R["auto"]["pan_whole"] = pan_reversals(pan, s0_, pe) if s0_ is not None else None

    # Wrist 재획득
    if not a.no_wrist and len(df):
        sys.path.insert(0, str(R2S))
        sys.path.insert(0, str(K8 / "d2/diag_grasp_bias"))
        import common as C
        import r2_analyze as RA
        n_end = i_first_grasp if i_first_grasp is not None else len(df)
        cache = {}
        imgs = C.frames(run / "dataset", a.ep, "wrist", 0, max(0, n_end - 1), cache) if n_end > 0 else []
        idx = list(range(0, len(imgs), STEP))
        vis = [bool(RA.wrist_measure_bbox(imgs[i]).get("vis")) for i in idx]
        lost, reacq, seen = wrist_segments(idx, vis)
        R["auto"]["wrist"] = {"frames_checked": len(idx), "until_i": int(n_end), "seen_any": seen, "visible_frac": float(np.mean(vis)) if vis else None,
                              "lost_segments": lost, "reacquired": reacq}
    else:
        R["auto"]["wrist"] = None

    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    multi = len({r.get("ep") for r in read_csv(run / "results.csv")}) > 1
    jp = out / (f"trial_auto_ep{a.ep}.json" if multi else "trial_auto.json")
    if jp.exists():
        jp = out / f"trial_auto_{stamp}.json"
    jp.write_text(json.dumps(R, indent=1, ensure_ascii=False, default=float))
    A, m = R["auto"], R["manifest"] or {}
    pr, pw, wr = A.get("pan_pre_first_close") or {}, A.get("pan_whole") or {}, A.get("wrist") or {}
    md = [f"# 자동 지표 — {run.name}", "", "값: [기록] 파일 그대로 · [자동 후보] 규칙 계산 (사용자 판정 아님)", "",
          f"- 시행 {m.get('trial')} · 모델 {m.get('model_name')} · SHA-256 {m.get('model_sha256')}",
          f"- 계획 {((m.get('plan_row') or {}).get('condition'))} · 시작 사진 확인 [기록]: {R['plan_check'][0] if R['plan_check'] else '없음'}",
          f"- 시작 관절 [기록]: {R['start_joints']}",
          f"- eval_ui 판정 [기록]: {(R['eval_ui'] or {}).get('verdict')} · 길이 {(R['eval_ui'] or {}).get('seconds')} s · frame {R['n_frames']}",
          f"- 첫 닫힘 [자동 후보]: {A['first_close_T4']} (T2 {A['first_close_T2_s']} s) · 닫힘 {A['n_closes']} 회 · 첫 파지 전 빈 닫힘 {A['n_empty_before_first_grasp']} 회",
          f"- Pan 반전 [자동 후보, 히스테리시스 {REV_DEG}°]: 첫 닫힘 전 {pr.get('n_reversals')} 회 · 판 전체 {pw.get('n_reversals')} 회 · "
          f"pe {pe} 지나침 최대 {None if not pw else round(pw['max_past_target_deg'], 1)}° · pan 범위 {None if not pw else (round(pw['pan_min'], 1), round(pw['pan_max'], 1))}",
          f"- Wrist [자동 후보, 첫 파지 전]: 보인 비율 {wr.get('visible_frac')} · 놓침 {len(wr.get('lost_segments') or [])} 구간 · 재획득 {wr.get('reacquired')}",
          f"- 안전 [기록]: r2_safety STOP {len(R['safety_stops'])} · FAULT {len(R['fault_events'])} · 차단 {R['n_blocked_r2']} · console {R['console_flags']}",
          f"- 종료 [기록, end_hold]: {None if not R['end_state'] else {k: R['end_state'].get(k) for k in ('ended_by', 'max_abs_diff_deg', 'torque_left_on', 'auto_return_blocked_calls')}}",
          f"- 비고: {R['notes']}"]
    (out / jp.name.replace(".json", ".md")).write_text("\n".join(md) + "\n")
    print("\n".join(md))
    print("OUT", jp)


if __name__ == "__main__":
    main()
