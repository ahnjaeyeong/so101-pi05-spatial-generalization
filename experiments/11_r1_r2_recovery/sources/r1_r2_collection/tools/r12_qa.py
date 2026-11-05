#!/home/user/so101-env/bin/python
"""R1/R2 세션 품질 검사 — dataset 은 읽기만. 보고서: <세션>/qa/r12_qa_report.md · <세션>/qa/r12_qa.csv

  ~/so101-env/bin/python r12_qa.py --session main_k8/r2_pregrasp_pilot [--dataset DIR] [--out DIR]
(r12_collect.py qa --session ... 와 같음.) 보고서에는 잰 값과 판정 규칙만 적는다 (해석·권고 없음).
"""

import csv
import datetime
import glob
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.expanduser("~"), "so101_boxpick", "scripts"))
import r12_common as rc  # noqa: E402

D2_DATASET = os.path.expanduser("~/so101_runs/main_k8/d2/dataset")
FEATURE_KEYS = ("action", "observation.state", "observation.images.front", "observation.images.wrist", "timestamp",
                "frame_index", "episode_index", "index", "task_index")
# 판정 규칙 (보고서에 그대로 적음)
RULES = {
    "len_min_s": 3.0,                # 이보다 짧으면 ⚠
    "jump_deg": 20.0,                # 한 프레임 사이 팔 관절 변화가 이보다 크면 ⚠ (상태·명령 각각)
    "dt_tol_s": 1e-3,                # timestamp 간격 − 1/fps 허용
    "start_shift_deg": 5.0,          # 준비 때 자세 → 첫 녹화 프레임 이동이 이보다 크면 ⚠
    "front_dist_cm": 2.5,            # 첫 화면 front 큐브 ↔ 계획 K 거리
    "end_lift_max": -90.0,           # 끝 프레임 = 쉬는 자세 판정 (d2 마지막 프레임 p5–p95: lift −103.1…−102.7, elbow 92.0…96.1)
    "end_elbow_min": 85.0,
    "grip_open": 15.0, "grip_closed": 10.0,   # 처음 닫힘 = 명령 그리퍼가 열림(>15) 뒤 <10
}


def opt(argv, name, default=None):
    for i, a in enumerate(argv):
        if a == name and i + 1 < len(argv):
            return argv[i + 1]
        if a.startswith(name + "="):
            return a.split("=", 1)[1]
    return default


def first_frames(dataset, info, eps_row, cams):
    import record_ui as ru

    out = {}
    for cam in cams:
        p = ru.video_path(dataset, info, cam, eps_row)
        t0 = float(eps_row[f"videos/{cam}/from_timestamp"])
        for f in ru.iter_frames(p, t0, t0 + 0.5, info["fps"]):
            out[cam.split(".")[-1]] = f
            break
    return out


def compat(dataset):
    import pandas as pd

    info = json.load(open(os.path.join(dataset, "meta", "info.json")))
    d2 = json.load(open(os.path.join(D2_DATASET, "meta", "info.json")))
    rows = []
    for k in FEATURE_KEYS:
        same = json.dumps(info["features"].get(k), sort_keys=True) == json.dumps(d2["features"].get(k), sort_keys=True)
        rows.append((f"features.{k}", "같음" if same else "다름"))
    rows.append(("features 이름 집합", "같음" if set(info["features"]) == set(d2["features"]) else
                 f"다름 ({sorted(set(info['features']) ^ set(d2['features']))})"))
    for k in ("fps", "robot_type", "codebase_version"):
        rows.append((k, f"{info.get(k)} (d2 {d2.get(k)})" + (" 같음" if info.get(k) == d2.get(k) else " 다름")))
    t = list(pd.read_parquet(os.path.join(dataset, "meta", "tasks.parquet")).index)
    t2 = list(pd.read_parquet(os.path.join(D2_DATASET, "meta", "tasks.parquet")).index)
    rows.append(("tasks", f"{t} " + ("= d2" if t == t2 else f"≠ d2 {t2}")))
    return info, rows


def integrity(dataset, info, eps, data, cams, ep_meta):
    """저장 무결성 (읽기만): 판 번호 중복·빠짐, 판 길이 = 데이터 줄 수, 전역 index 연속, 영상 파일 존재·구간, 메타데이터 판 ID 중복.
    반환 [(항목, 결과)] — 결과 앞의 ⚠ 는 확인 대상."""
    import record_ui as ru

    out = []
    ei = sorted(int(e) for e in eps["episode_index"])
    out.append(("dataset 판 번호", f"{len(ei)}개 · " + ("0.." + str(len(ei) - 1) + " 연속, 중복 없음" if ei == list(range(len(ei)))
                                                    else f"⚠ 중복/빠짐 {ei}")))
    out.append(("info.json total_episodes", f"{info.get('total_episodes')}" + ("" if info.get("total_episodes") == len(ei) else " ⚠ 판 수와 다름")))
    bad = [int(er["episode_index"]) for _, er in eps.iterrows() if int(er["length"]) != int((data.episode_index == er["episode_index"]).sum())]
    out.append(("판 길이 = 데이터 줄 수", "모두 같음" if not bad else f"⚠ 다름 {bad}"))
    idx = np.sort(data["index"].values.astype(int))
    out.append(("전역 index", "0.." + str(len(idx) - 1) + " 연속" if (idx == np.arange(len(idx))).all() else "⚠ 끊김/중복"))
    fr_bad = [int(e) for e, g in data.groupby("episode_index") if (np.sort(g["frame_index"].values) != np.arange(len(g))).any()]
    out.append(("판 안 frame_index", "모두 0..길이−1 연속" if not fr_bad else f"⚠ 끊김 {fr_bad}"))
    miss, span = [], []
    for _, er in eps.iterrows():
        for cam in cams:
            p = ru.video_path(dataset, info, cam, er)
            if not os.path.exists(p):
                miss.append(f"ep{int(er['episode_index'])} {cam.split('.')[-1]}")
            n_v = (float(er[f"videos/{cam}/to_timestamp"]) - float(er[f"videos/{cam}/from_timestamp"])) * info["fps"]
            if abs(n_v - int(er["length"])) > 1.5:
                span.append(f"ep{int(er['episode_index'])} {cam.split('.')[-1]} {n_v:.0f}≠{int(er['length'])}")
    out.append(("영상 파일 (front·wrist)", "모두 있음" if not miss else f"⚠ 없음 {miss}"))
    out.append(("영상 구간 프레임 수 = 판 길이", "모두 같음 (±1)" if not span else f"⚠ {span}"))
    ids = [m.get("episode_id") for m in ep_meta.values() if m.get("episode_id")]
    out.append(("r12_episodes.csv episode_id", f"{len(ids)}개 · " + ("중복 없음" if len(ids) == len(set(ids)) else "⚠ 중복")))
    nfr = [e for e, m in ep_meta.items() if str(m.get("frames", "")).isdigit() and int(m["frames"]) != int((data.episode_index == e).sum())]
    out.append(("녹화 중 센 프레임 = 저장 줄 수", "모두 같음" if not nfr else f"⚠ 다름 ep {nfr}"))
    return out


# ================================================================ 파일럿 12편 QA (작업 지시 §9) — dataset 으로 다시 잼, 읽기만
PILOT_Q = {"q1": "시작 상태가 의도한 실패 상태와 비슷한가 (근사)", "q2": "R1: 필요한 방향으로 Pan 수정이 기록됐나",
           "q3": "R2-P: 그리퍼를 연 채 접근했나 (닫기 전까지 열림)", "q4": "R2-O: 그리퍼를 충분히 다시 열었나 (먼저 열고 접근)",
           "q5": "정렬 뒤 한 번의 닫힘으로 파지했나", "q6": "불필요한 동작 (Pan 왕복 · 경로 길이)",
           "q7": "영상 · state · action 시간 일치", "q8": "d2 와 독립 보존"}


def _pilot_one(cfg, pr, S, A, fps, first_vis, armed_state, label, integ_ok):
    """판 하나의 Q1–Q7. 반환 dict (값 · 판정 'ok' / 'check' / 'na')."""
    Q = cfg.get("pilot_qa") or {}
    names = [f"{j}.pos" for j in rc.JOINTS]
    d = rc.describe_row(cfg, pr)
    var = d.get("pilot_variant", "")
    n = len(S)
    gmin = float(Q.get("gripper_open_min", 15))
    ev = rc.close_events(A[:, 5], open_min=gmin, drop_min=float(Q.get("close_drop_min", 8)))
    k_close = ev[0][0] if ev else None
    out = {"variant": var}
    # Q1 — 녹화 첫 프레임 (dataset) 기준 시작 상태 · 실패 상태 비슷함
    ps = rc.pilot_start_checks(cfg, d, dict(zip(names, S[0])), first_vis)
    sim = ps["similarity"]
    out["q1"] = "ok" if sim["total"] and sim["matched"] == sim["total"] else "check"
    out["q1_detail"] = f"{sim['matched']}/{sim['total']}: " + " · ".join(sim["items"])
    gs = d.get("gripper_start")
    if gs:
        g0 = "open" if S[0, 5] >= gmin else "closed"
        out["q1_detail"] += f" · 시작 그리퍼 {S[0, 5]:.0f} ({g0}, 조건 {gs})"
        if g0 != gs:
            out["q1"] = "check"
    # Q2 — R1 Pan 수정
    out["q2"], out["q2_detail"] = "na", ""
    if var == "R1":
        ref = rc.pan_ref(cfg, pr["position"])
        err0 = S[0, 0] - ref
        toward = -np.sign(err0) if err0 else 0
        end = k_close if k_close is not None else n
        prog = (S[:end, 0] - S[0, 0]) * toward if end > 0 else np.array([0.0])
        first = next((i for i in range(1, end) if abs(S[i, 0] - S[0, 0]) >= 2.0), None)
        first_dir = "" if first is None else ("toward" if (S[first, 0] - S[0, 0]) * toward > 0 else "away")
        err_c = S[min(end, n - 1), 0] - ref
        ok = float(prog.max()) >= float(Q.get("pan_correction_min_deg", 5)) and abs(err_c) < abs(err0) and first_dir == "toward"
        out["q2"] = "ok" if ok else "check"
        out["q2_detail"] = (f"시작 기준 대비 {err0:+.1f}° → 필요한 방향 {'오른쪽(+)' if toward > 0 else '왼쪽(−)'} · 첫 Pan 이동 {first_dir or '없음'} · "
                            f"최대 수정 {float(prog.max()):.1f}° · 닫기 시작 때 기준 대비 {err_c:+.1f}°")
    # Q3 — R2-P 열린 채 접근
    out["q3"], out["q3_detail"] = "na", ""
    rc_open = var.startswith("RC") and d.get("gripper_start") == "open"      # 11-04 회복 시연 F1
    rc_closed = var.startswith("RC") and d.get("gripper_start") == "closed"  # 11-04 회복 시연 F2 · F3
    if var == "R2-P" or rc_open:
        end = k_close if k_close is not None else n
        frac = float((A[:end, 5] >= gmin).mean()) if end else 0.0
        out["q3"] = "ok" if frac >= 0.95 and S[0, 5] >= gmin else "check"
        out["q3_detail"] = f"닫기 전 리더 그리퍼 ≥ {gmin:g} 비율 {frac:.2f} · 최소 {float(A[:end, 5].min()) if end else float('nan'):.1f}"
    # Q4 — R2-O 다시 열기
    out["q4"], out["q4_detail"] = "na", ""
    if var == "R2-O" or rc_closed:
        rmin = float(d.get("reopen_min") or 25)
        end = k_close if k_close is not None else n
        k_open = next((i for i in range(n) if A[i, 5] >= gmin), None)
        gmax = float(A[:end, 5].max()) if end else float("nan")
        arm_before = float(np.abs(S[:k_open + 1, 1:3] - S[0, 1:3]).max()) if k_open is not None else float("nan")
        ok = A[0, 5] < gmin and k_open is not None and gmax >= rmin
        out["q4"] = "ok" if ok and arm_before <= 5.0 else "check"
        out["q4_detail"] = (f"시작 리더 그리퍼 {A[0, 5]:.0f} · 처음 ≥ {gmin:g} @ {'—' if k_open is None else f'{k_open / fps:.2f}s'} · "
                            f"닫기 전 최대 {gmax:.1f} (목표 ≥ {rmin:g}) · 열기 전 Lift/Elbow 이동 {arm_before:.1f}° (≤ 5 = 먼저 엶)")
    # Q5 — 한 번의 닫힘으로 파지: 팔로워 그리퍼 바닥으로 첫 닫힘 판정 (≥ 8 쥠 · ≤ 5 빈 파지, r2_common 규칙). 상자에 놓은 뒤 닫힘은 세지 않음
    import r12_guide as G

    fs = (label or {}).get("first_grasp_success")
    flags = G.review_episode(A[:, 5], S[:, 5], fps=fps)
    warn = [f for f in flags if f[0] == "warn"]
    b0 = float(S[ev[0][0]: ev[0][0] + int(1.5 * fps), 5].min()) if ev else float("nan")
    out["review"] = flags
    out["q5"] = "ok" if ev and not warn and str(fs) == "True" else "check"
    out["q5_detail"] = (f"첫 닫힘 {ev[0][0] / fps:.2f}s 팔로워 바닥 {b0:.1f}" if ev else "닫힘 없음") + \
        (" · " + " · ".join(f[2] for f in warn) if warn else " · 첫 닫힘에 쥠") + f" · 첫 파지 입력 {fs if fs not in (None, '') else '미입력'}"
    # Q6 — 불필요한 동작
    end = k_close if k_close is not None else n
    seg = S[:max(end, 2), :5]
    path = float(np.abs(np.diff(seg, axis=0)).sum())
    net = float(np.abs(seg[-1] - seg[0]).sum())
    ratio = path / net if net > 1e-6 else float("inf")
    rev = max(0, len(rc._zigzag(list(seg[:, 0]), 3.0)) - 2)
    ok6 = ratio <= float(Q.get("path_ratio_max", 2.5)) and (var != "R1" or rev <= int(Q.get("pan_reversals_max", 2)))
    out["q6"] = "ok" if ok6 else "check"
    out["q6_detail"] = f"닫기 전 팔 관절 경로/순 변위 {ratio:.2f} · Pan 방향 바뀜 {rev}번 (3° 문턱)"
    # Q7 — 시간 일치 (판 안 timestamp 는 main 표, 영상 구간·저장 줄 수는 무결성 표)
    out["q7"] = "ok" if integ_ok else "check"
    out["q7_detail"] = "무결성 표: 영상 구간 = 판 길이 · 녹화 중 센 프레임 = 저장 줄 수 · frame_index 연속" + ("" if integ_ok else " — ⚠ 있음")
    return out


def pilot_qa(cfg, sess_dir, plan, eps, data, fps, dataset, info, cams, ep_meta, integ):
    import record_ui as ru

    integ_ok = not any(str(b).startswith("⚠") for _, b in integ)
    att = rc.fold_attempts(rc.read_events(sess_dir))
    by_ep = {a["ep"]: a for a in att.values() if a["status"] == "saved" and "ep" in a}
    d2_root = os.path.realpath(D2_DATASET)
    real = os.path.realpath(dataset)
    meta = rc.read_meta(sess_dir)
    d2_repos = {"oxr/so101_k8_d2", "oxr/so101_k8_redbox"}  # 이름 비교 (참고)
    indep = (not real.startswith(d2_root) and os.path.basename(os.path.dirname(real)) not in
             {os.path.basename(s) for s in rc.PROTECTED_SESSIONS} and meta.get("repo_id") not in d2_repos)
    out = []
    for _, er in eps.iterrows():
        e = int(er["episode_index"])
        pr = plan[e] if e < len(plan) else None
        if not pr:
            continue
        dd = data[data.episode_index == e].sort_values("frame_index")
        S = np.stack(dd["observation.state"].values).astype(float)
        A = np.stack(dd["action"].values).astype(float)
        try:
            ff = first_frames(dataset, info, er, cams)
            vis = rc.vision(ff.get("front"), ff.get("wrist"), cfg, pr.get("position"))
        except Exception:
            vis = None
        a = by_ep.get(e, {})
        r = {"episode": e, "scenario": pr["scenario_id"], "excluded": pr.get("status") == rc.EXCLUDED,
             **_pilot_one(cfg, pr, S, A, fps, vis, (a.get("armed") or {}).get("state"), a.get("label"), integ_ok)}
        evc = rc.close_events(A[:, 5])
        if evc:  # 첫 닫힘 때 손목 큐브가 화면 경계에서 잘렸나 (영상 프레임)
            try:
                wcam = next(c for c in cams if c.endswith(".wrist"))
                t0 = float(er[f"videos/{wcam}/from_timestamp"])
                k0 = evc[0][0]
                frw = next(ru.iter_frames(ru.video_path(dataset, info, wcam, er), t0 + k0 / fps, t0 + (k0 + 1) / fps, fps), None)
                vw = rc.vision(None, frw, cfg)["wrist"] if frw is not None else {}
                if vw.get("touches_edge"):
                    r["q5"] = "check"
                    r["q5_detail"] += " · 첫 닫힘 때 큐브가 손목 화면 경계에서 잘림"
                    r["review"] = list(r.get("review") or []) + [("warn", "cut_at_first_close", "첫 닫힘 때 큐브가 손목 화면 경계에서 잘림")]
            except Exception as ex:
                r["q5_detail"] += f" · 손목 영상 읽기 실패 {ex!r}"
        r["q8"] = "ok" if indep else "check"
        r["q8_detail"] = f"dataset {real.replace(os.path.expanduser('~'), '~')} · repo_id {meta.get('repo_id')} · d2 dataset 밖"
        lab = a.get("label") or {}
        checks = [r[q] for q in ("q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8") if r[q] != "na"]
        guard = [g.get("reason") for g in a.get("guard", []) if g.get("phase") == "rec"]
        r["guard_in_rec"] = ";".join(guard)
        # 성공해도 학습 적합으로 바로 분류하지 않음: 모든 항목 ok + 결과 성공 + 보호 사건 없음 = 'candidate (사람 검토 필요)'
        r["suitability"] = ("exclude" if r["excluded"] or guard else
                            "candidate_needs_review" if all(c == "ok" for c in checks) and str(lab.get("final_success")) == "True" else "review")
        out.append(r)
    return out


def pilot_report(cfg, prow, out_dir):
    fields = ["episode", "scenario", "variant", "excluded", "suitability", "guard_in_rec"] + \
        [x for q in ("q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8") for x in (q, q + "_detail")]
    with open(os.path.join(out_dir, "r12_pilot_qa.csv"), "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=fields)
        wr.writeheader()
        for r in prow:
            wr.writerow({k: r.get(k, "") for k in fields})
    L = ["", "## 5. 파일럿 12편 QA (작업 지시 §9) — dataset 으로 다시 잼", "",
         "판정: ok = 규칙 통과 · check = 사람이 영상으로 확인 · na = 해당 없음. 'candidate_needs_review' 도 학습 적합 확정이 아님 (사람 검토 필요).", ""]
    L += [f"- {k.upper()} {v}" for k, v in PILOT_Q.items()]
    L += ["", "| ep | 시나리오 | 적합 분류 | Q1 | Q2 | Q3 | Q4 | Q5 | Q6 | Q7 | Q8 |", "|---:|---|---|---|---|---|---|---|---|---|---|"]
    for r in prow:
        L.append(f"| {r['episode']}{' (제외)' if r['excluded'] else ''} | {r['scenario']} | {r['suitability']} | "
                 + " | ".join(r[q] for q in ("q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8")) + " |")
    L += ["", "### 판별 값", ""]
    for r in prow:
        L.append(f"- ep{r['episode']} {r['scenario']}" + (f" · 녹화 중 보호 {r['guard_in_rec']}" if r["guard_in_rec"] else ""))
        for q in ("q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8"):
            if r[q] != "na":
                L.append(f"  - {q.upper()} {r[q]}: {r[q + '_detail']}")
    L += ["", "규칙 (config pilot_qa · pilot_reference): " + json.dumps({**(cfg.get("pilot_qa") or {}), "reference": cfg.get("pilot_reference")}, ensure_ascii=False)]
    return L


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    session = opt(argv, "--session")
    cfg = rc.load_config(opt(argv, "--config"))
    sess_dir = rc.session_dir(session)
    dataset = opt(argv, "--dataset") or os.path.join(sess_dir, "dataset")
    out_dir = opt(argv, "--out") or os.path.join(sess_dir, "qa")
    os.makedirs(out_dir, exist_ok=True)
    import pandas as pd
    import record_ui as ru

    info, comp = compat(dataset)
    fps = info["fps"]
    _, eps, cams = ru.load_meta(dataset)
    if eps is None or len(eps) == 0:
        print(f"품질 검사: 저장된 판이 없어요 ({dataset}) — 건너뜀")
        return 0
    data = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(os.path.join(dataset, "data", "*", "*.parquet")))])
    plan = rc.read_plan(sess_dir)
    meta = rc.read_meta(sess_dir)
    ep_meta = {}
    p = os.path.join(sess_dir, rc.EPISODES_CSV)
    if os.path.exists(p):
        ep_meta = {int(r["episode_index"]): r for r in csv.DictReader(open(p))}
    limits = rc.calib_limits(cfg)
    ep_time = float(meta.get("episode_time_s", 45))
    integ = integrity(dataset, info, eps, data, cams, ep_meta)
    armed_by_attempt = {e.get("attempt_id"): e for e in rc.read_events(sess_dir) if e.get("ev") == "armed"}
    rows = []
    for _, er in eps.iterrows():
        e = int(er["episode_index"])
        d = data[data.episode_index == e].sort_values("frame_index")
        S = np.stack(d["observation.state"].values).astype(float)
        A = np.stack(d["action"].values).astype(float)
        n = len(d)
        pr = plan[e] if e < len(plan) else {}
        if not pr:
            pass  # 계획보다 많은 판 (보고서에 "?" 로)
        sc = cfg["scenarios"].get(pr.get("scenario_id", ""), {})
        m = ep_meta.get(e, {})
        r = {"episode": e, "scenario": pr.get("scenario_id", "?"), "K": pr.get("position", "?"), "angle": pr.get("angle", ""),
             "excluded": pr.get("status") == rc.EXCLUDED, "frames": n, "len_s": round(n / fps, 2), "reasons": []}
        if n / fps < RULES["len_min_s"]:
            r["reasons"].append(f"길이 {n / fps:.1f}s < {RULES['len_min_s']}")
        if n / fps >= ep_time - 0.1:
            r["reasons"].append(f"길이 = 최대 {ep_time:.0f}s (시간 초과로 끝남)")
        dt = np.diff(d["timestamp"].values.astype(float))
        r["dt_max_dev_ms"] = round(float(np.abs(dt - 1 / fps).max()) * 1000, 3) if len(dt) else 0
        if r["dt_max_dev_ms"] > RULES["dt_tol_s"] * 1000:
            r["reasons"].append(f"timestamp 간격 오차 {r['dt_max_dev_ms']} ms")
        if not (np.isfinite(S).all() and np.isfinite(A).all()):
            r["reasons"].append("state/action 에 NaN·inf")
        js = np.abs(np.diff(S[:, :5], axis=0)).max() if n > 1 else 0
        ja = np.abs(np.diff(A[:, :5], axis=0)).max() if n > 1 else 0
        r["max_jump_state"], r["max_jump_action"] = round(float(js), 1), round(float(ja), 1)
        if js > RULES["jump_deg"] or ja > RULES["jump_deg"]:
            r["reasons"].append(f"프레임 사이 관절 변화 state {js:.0f}° / action {ja:.0f}°")
        names = [f"{j}.pos" for j in rc.JOINTS]
        chk = rc.safety_check(dict(zip(names, S[0])), dict(zip(names, A[0])), cfg, limits)
        # 첫 프레임의 리더−팔로워 차이는 '녹화 시작 직후 이미 움직임' 이라 시작 자세 BLOCK 으로 보지 않음 (준비 단계 → 때 검사함)
        r["start_block"] = "; ".join(c[2] for c in chk if c[0] == "BLOCK" and not c[1].startswith("diff_"))
        r["start_warn"] = "; ".join(c[2] for c in chk if c[0] == "WARN")
        if r["start_block"]:
            r["reasons"].append("첫 프레임 시작 자세 검사 BLOCK: " + r["start_block"])
        r["start_state"] = ";".join(f"{rc.SHORT[j]}={v:.1f}" for j, v in zip(rc.JOINTS, S[0]))
        r["start_grip"] = round(float(S[0, 5]), 1)
        sh = m.get("start_shift_deg", "")
        r["start_shift_deg"] = sh
        if sh not in ("", None) and float(sh) > RULES["start_shift_deg"]:
            r["reasons"].append(f"준비 자세 → 첫 프레임 {float(sh):.1f}°")
        g = A[:, 5]
        op = np.where(g > RULES["grip_open"])[0]
        cl = np.where((np.arange(n) > (op[0] if len(op) else n)) & (g < RULES["grip_closed"]))[0] if len(op) else []
        r["first_close_s"] = round(float(cl[0]) / fps, 2) if len(cl) else ""
        if not len(cl):
            r["reasons"].append("그리퍼 닫힘(명령 >15 → <10) 없음")
        end_rest = S[-1, 1] < RULES["end_lift_max"] and S[-1, 2] > RULES["end_elbow_min"]
        r["end_rest"] = bool(end_rest)
        if not end_rest:
            r["reasons"].append(f"끝 프레임이 쉬는 자세 아님 (lift {S[-1, 1]:.0f}, elbow {S[-1, 2]:.0f})")
        # 닫기 시작 순간 손목 영상의 큐브가 '닫기 영역'(d2 사람 시연 주 덩어리) 안이었나
        r["close_zone"] = ""
        zone = rc.wrist_zone()
        if zone and len(cl):
            import r12_wrist_zone as wz

            k = wz.close_onset(A)
            if k is not None:
                try:
                    import record_ui as ru_

                    wcam = next(c for c in cams if c.endswith(".wrist"))
                    t0 = float(er[f"videos/{wcam}/from_timestamp"])
                    fr = next(ru_.iter_frames(ru_.video_path(dataset, info, wcam, er), t0 + k / fps, t0 + (k + 1) / fps, fps), None)
                    vw = rc.vision(None, fr, cfg)["wrist"] if fr is not None else {}
                    okz, hint = rc.zone_status(vw, zone)
                    if vw.get("touches_edge"):  # 잘리면 넓이가 작게 잡혀 '더 진입' 이 틀리게 나옴 (2026-11-03 R2-P ep0)
                        hint = "큐브가 손목 화면 경계에서 잘림 (위치 판정 불확실)"
                    r["close_zone"] = ("영역 안" if okz else hint) + f" @ {k / fps:.1f}s"
                    if not okz:
                        r["reasons"].append(f"닫기 시작 때 손목 큐브가 닫기 영역 밖 ({hint})")
                except Exception as ex:
                    r["close_zone"] = f"읽기 실패 {ex!r}"
        # 11-02 녹화 중 어긋남 (error_in_rec): Space 재정렬 표시 프레임의 pan ↔ 닫기 시작 pan
        r["realign"] = ""
        mk = [int(x) for x in str(m.get("realign_mark_frames", "") or "").split(";") if x.strip().isdigit()]
        if mk:
            f0 = min(mk[0], n - 1)
            import r12_wrist_zone as wz

            kc = wz.close_onset(A)
            r["realign"] = f"Space @ {f0 / fps:.1f}s pan {S[f0, 0]:+.1f}°" + (f" → 닫기 시작 pan {S[kc, 0]:+.1f}° (차이 {S[f0, 0] - S[kc, 0]:+.1f}°)" if kc is not None else "")
        elif sc.get("error_in_rec"):
            r["realign"] = "Space 없음"
            r["reasons"].append("재정렬 표시(Space) 없음 — 어긋남 구간을 나중에 자를 수 없음")
        try:
            ff = first_frames(dataset, info, er, cams)
            v = rc.vision(ff.get("front"), ff.get("wrist"), cfg, pr.get("position"))
        except Exception as ex:  # 영상 읽기 실패도 기록
            v = {"error": repr(ex)}
        r["angle_first"] = ""
        if ff.get("front") is not None and pr.get("position"):
            try:
                am = rc.measure_angle(ff["front"], cfg, pr["position"], pr["angle"])
                r["angle_first"] = am["text"]
                if am.get("meas") is not None and not am["ok"]:
                    r["reasons"].append(f"첫 화면 큐브 각도 범위 밖 ({am['text']})")
            except Exception as ex:
                r["angle_first"] = f"못 잼 {ex!r}"
        w, f = v.get("wrist", {}), v.get("front", {})
        r["wrist_first"] = (f"dx={w['dx']:+.2f} dy={w['dy']:+.2f} area={w['area_px']}" + (" edge" if w.get("touches_edge") else "")) \
            if w.get("detected") else ("안 보임" if "error" not in v else v["error"])
        if not w.get("detected") and sc.get("wrist_expect", "visible") == "visible":
            r["reasons"].append("첫 화면 손목 카메라에 큐브 없음 (시나리오는 보여야 함)")
        reg = rc.start_region(sc)
        r["r2_start_region"] = ""
        if reg and sc.get("local_dir") != "near_aligned":  # R2 (11-02): 첫 화면 손목 큐브가 시나리오 시작 영역 안인가
            rin = rc.in_region(w, reg)
            r["r2_start_region"] = {True: "영역 안", False: "영역 밖", None: "큐브 안 보임"}[rin]
            if rin is not True:
                r["reasons"].append(f"첫 화면 손목 큐브가 R2 시작 영역({sc.get('local_dir')}) 밖/안 보임")
        r["error_kind"] = sc.get("error_kind", "")
        # R1 (3·4차): 첫 프레임 시작 상태 + 복구 측정 (dataset state 의 pan 열 · 손목 영상 10 프레임마다 · 준비 단계 pan 은 armed 사건)
        r["r1_start"] = r["r1_recovery"] = ""
        if pr.get("approach_stage_expected") or pr.get("start_pose_type"):
            st0 = dict(zip(names, S[0]))
            cal = float(m.get("pan_calib_deg") or 0)
            ref = rc.pan_ref(cfg, pr["position"]) + cal
            perr = S[0, 0] - ref
            stg, prog = rc.approach_stage(cfg, st0, pr["position"])
            wv, fv = rc.wrist_visibility(w if "error" not in v else None), rc.front_visibility(f if "error" not in v else None)
            exp = [x for x in (pr.get("approach_stage_expected") or "").split("|") if x]
            r["r1_start"] = (f"{rc.STAGE_KO.get(stg)} ({prog}) · Pan {S[0, 0]:+.1f}° = 기준 {ref:+.1f}° {perr:+.1f}° "
                             f"(계획 {pr.get('pan_error_direction')} {pr.get('nominal_pan_error_deg')}°) · 손목 {rc.VIS_KO.get(wv)} · front {fv}")
            if exp and stg not in exp:
                r["reasons"].append(f"시나리오 조건: 첫 프레임 접근 단계 {rc.STAGE_KO.get(stg)} (계획 {'/'.join(rc.STAGE_KO.get(x, x) for x in exp)})")
            if rc.visibility_matches(pr.get("wrist_visibility_target"), wv) is False:
                r["reasons"].append(f"시나리오 조건: 첫 화면 손목 큐브 {rc.VIS_KO.get(wv)} (계획 {rc.VIS_KO.get(pr.get('wrist_visibility_target'))})")
            if fv == "not_detected":
                r["reasons"].append("첫 화면 front 에 큐브 없음 (R1 은 front 로 목표 식별)")
            if m.get("start_safety_confirmed") not in ("yes",):
                r["reasons"].append("시작 자세 안전 확인 기록 없음")
            arm = armed_by_attempt.get(m.get("attempt_id"), {})
            rec = rc.pan_recovery(S[:, 0], fps, ref, arm.get("setup_pan"), A[:, 5])
            seen = []
            try:
                wcam = next(c for c in cams if c.endswith(".wrist"))
                t0 = float(er[f"videos/{wcam}/from_timestamp"])
                for kk, fr_ in enumerate(ru.iter_frames(ru.video_path(dataset, info, wcam, er), t0, t0 + n / fps, fps)):
                    if kk % 10 == 0:
                        seen.append(bool(rc.find_red(fr_, cfg, min_area=150)))
            except Exception as ex:
                seen = []
                r["reasons"].append(f"손목 영상 읽기 실패 {ex!r}")
            w0, reacq, tre = rc.wrist_reacquire(seen, 10 / fps)
            ecl = rec.get("pan_error_at_grasp_deg")
            ecl = None if ecl in ("", None) else ecl
            r["r1_recovery"] = (f"준비 때 {rec.get('setup_pan_motion')} · 녹화 첫 이동 {rec.get('first_pan_move_dir')} {rec.get('first_pan_move_deg', 0):+.1f}° · "
                                + (f"반전 {rec['pan_reversal_kind']} @{rec['pan_reversal_t_s']:+.2f}s ({rec['pan_change_before_reversal_deg']:+.1f}° → {rec['pan_change_after_reversal_deg']:+.1f}°)"
                                   if rec.get("pan_reversal") else "반전 없음")
                                + " · 손목 " + ("처음부터 보임" if w0 else f"다시 찾음 @{tre}s" if reacq else "못 찾음" if w0 is False else "?")
                                + (f" · 파지 시작 {rec['grasp_start_t_s']}s Pan 오차 {ecl:+.1f}°" if ecl is not None else " · 파지 시작 못 찾음"))
            r.update({f"rec_{k_}": rec.get(k_, "") for k_ in ("first_pan_move_dir", "pan_reversal", "pan_reversal_t_s")},
                     rec_cube_reacquired=reacq if reacq is not None else "", rec_pan_error_at_close=round(float(ecl), 1) if ecl is not None else "")
            if rec.get("first_pan_move_dir") == "away":
                r["reasons"].append(f"녹화 첫 Pan 이동이 큐브에서 멀어짐 ({rec.get('first_pan_move_deg', 0):+.1f}°) — 틀린 방향 이동이 녹화됨?")
            if w0 is False and not reacq:
                r["reasons"].append("손목 화면에서 큐브를 다시 찾지 못함 (10 프레임마다 검사)")
        r["front_first_cm"] = ",".join(str(x) for x in f["xy_cm"]) if f.get("detected") else "안 보임"
        r["front_dist_planned_cm"] = f.get("dist_planned_cm", "")
        if f.get("detected") and f.get("dist_planned_cm", 0) > RULES["front_dist_cm"]:
            r["reasons"].append(f"front 큐브 ↔ 계획 {pr.get('position')} {f['dist_planned_cm']:.1f} cm")
        r["wrist_dx"] = w.get("dx", "")
        r["first_grasp_success"] = m.get("first_grasp_success", "")
        r["final_success"] = m.get("final_success", "")
        r["retry_count"] = m.get("retry_count", "")
        r["operator_notes"] = m.get("operator_notes", "")
        if not m:
            r["reasons"].append("r12_episodes.csv 줄 없음")
        elif r["final_success"] in ("", "None"):
            r["reasons"].append("결과 미입력")
        elif r["final_success"] == "False":
            r["reasons"].append("최종 실패로 입력됨")
        for k in ("late_ticks", "camera_stall_ticks"):
            if m.get(k) not in ("", None, "0"):
                r["reasons"].append(f"{k} {m.get(k)}")
        r["ok"] = not r["reasons"]
        rows.append(r)

    pilot_rows = pilot_qa(cfg, sess_dir, plan, eps, data, fps, dataset, info, cams, ep_meta, integ) if cfg.get("pilot") else []

    # ---- 분포
    valid = [r for r in rows if not r["excluded"]]
    by_sc, by_k, by_a, by_dir = {}, {}, {}, {}
    for r in valid:
        by_sc[r["scenario"]] = by_sc.get(r["scenario"], 0) + 1
        by_k[r["K"]] = by_k.get(r["K"], 0) + 1
        by_a[r["angle"]] = by_a.get(r["angle"], 0) + 1
        dr = plan[r["episode"]]["offset_dir"] if r["episode"] < len(plan) else "계획 없음"
        by_dir[dr] = by_dir.get(dr, 0) + 1
    target = {}
    for pr in plan:
        if pr["status"] != rc.EXCLUDED:
            target[pr["scenario_id"]] = target.get(pr["scenario_id"], 0) + 1
    # 손목 dx 부호 (시나리오별) — 좌/우 시나리오의 영상 쪽 일관성 확인용 측정값
    dx_by = {}
    for r in valid:
        if r["wrist_dx"] != "":
            dx_by.setdefault(r["scenario"], []).append(float(r["wrist_dx"]))

    fields = ["episode", "scenario", "K", "angle", "excluded", "ok", "frames", "len_s", "dt_max_dev_ms", "max_jump_state",
              "max_jump_action", "start_state", "start_grip", "start_shift_deg", "start_block", "start_warn", "first_close_s",
              "end_rest", "close_zone", "error_kind", "r1_start", "r1_recovery", "rec_first_pan_move_dir", "rec_pan_reversal",
              "rec_pan_reversal_t_s", "rec_cube_reacquired", "rec_pan_error_at_close", "realign", "r2_start_region", "angle_first", "wrist_first", "front_first_cm", "front_dist_planned_cm", "first_grasp_success", "final_success",
              "retry_count", "operator_notes", "reasons"]
    with open(os.path.join(out_dir, "r12_qa.csv"), "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=fields)
        wr.writeheader()
        for r in rows:
            wr.writerow({**{k: r.get(k, "") for k in fields}, "reasons": " | ".join(r["reasons"])})

    L = [f"# R1/R2 품질 검사 — {session}", "", f"- 만든 시각: {datetime.datetime.now():%Y-%m-%d %H:%M} · dataset `{dataset.replace(os.path.expanduser('~'), '~')}` (읽기만)",
         f"- 계획 `{rc.PLAN_CSV}` {len(plan)}줄 (유효 {sum(target.values())}) · 저장 {len(rows)}편 · 제외 표시 {sum(r['excluded'] for r in rows)}편",
         f"- 문제 없음 {sum(r['ok'] for r in valid)}/{len(valid)} (제외 판 빼고)", "", "## 1. d2 와 형식 비교", "", "| 항목 | 결과 |", "|---|---|"]
    L += [f"| {a} | {b} |" for a, b in comp]
    L += ["", "### 저장 무결성", "", "| 항목 | 결과 |", "|---|---|"] + [f"| {a} | {b} |" for a, b in integ]
    L += ["", "## 2. 수량", "", "| 시나리오 | 저장 | 계획 |", "|---|---:|---:|"]
    L += [f"| {k} | {by_sc.get(k, 0)} | {t} |" for k, t in target.items()]
    L += ["", "| K | 편수 |", "|---|---:|"] + [f"| {k} | {v} |" for k, v in sorted(by_k.items())]
    L += ["", "| 각도 | 편수 |", "|---|---:|"] + [f"| {rc.angle_label(k)} | {v} |" for k, v in sorted(by_a.items())]
    L += ["", "| 어긋남 방향 | 편수 |", "|---|---:|"] + [f"| {k} | {v} |" for k, v in sorted(by_dir.items())]
    L += ["", "손목 카메라 첫 화면 큐브 중심 dx (화면 가로, −1 왼쪽 … +1 오른쪽):", "", "| 시나리오 | n | 평균 | 최소 | 최대 |", "|---|---:|---:|---:|---:|"]
    L += [f"| {k} | {len(v)} | {np.mean(v):+.2f} | {min(v):+.2f} | {max(v):+.2f} |" for k, v in dx_by.items()]
    L += ["", "## 3. 판별", "", "| ep | 시나리오 | K | 길이 s | 처음 닫힘 s | 시작 조건 (R1 자세·Pan 오차·가시성 · R2 손목 시작 영역) | 닫기 시작 때 손목 큐브 | 시작 그리퍼 | 시작 이동° | 손목 첫 화면 | front↔계획 cm | 첫 파지 | 최종 | 재시도 | 문제 |",
          "|---:|---|---|---:|---:|---|---|---:|---:|---|---:|---|---|---:|---|"]
    for r in rows:
        L.append(f"| {r['episode']}{' (제외)' if r['excluded'] else ''} | {r['scenario']} | {r['K']} | {r['len_s']} | {r['first_close_s']} | {(r['r1_start'] + ' / ' + r['r1_recovery']) if r['r1_start'] else (r['realign'] or r['r2_start_region'] or '—')} | {r['close_zone']} | "
                 f"{r['start_grip']} | {r['start_shift_deg']} | {r['wrist_first']} | {r['front_dist_planned_cm']} | {r['first_grasp_success']} | "
                 f"{r['final_success']} | {r['retry_count']} | {'; '.join(r['reasons']) or '—'} |")
    L += ["", "## 4. 판정 규칙", ""] + [f"- `{k}` = {v}" for k, v in RULES.items()]
    L += ["- 닫기 영역 = config/r12_wrist_zone.json close_zone (d2 256편 닫기 시작 순간 손목 큐브 중심, 주 덩어리 p10–p90 · 넓이 최소). 닫기 시작 = 명령 그리퍼가 열린 뒤 처음 <10 이 되기 전 계속 줄어들기 시작한 프레임.",
          "- 시작 자세 검사 = r12_common.safety_check (설정 safety 절; 관절 캘리브레이션 한계, |pan|, 그리퍼 열림, 리더−팔로워 차이). FK·TCP 위치는 쓰지 않음.",
          "- 큐브 검출 = redbox8_layouts.yaml detection.colors.red HSV. front 좌표 = 같은 설정의 H (큐브 중심 평면). 물리적 접근 깊이는 측정하지 않음."]
    if pilot_rows:
        L += pilot_report(cfg, pilot_rows, out_dir)
    with open(os.path.join(out_dir, "r12_qa_report.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"품질 검사: 문제 없음 {sum(r['ok'] for r in valid)}/{len(valid)} → {os.path.join(out_dir, 'r12_qa_report.md')}")
    for r in rows:
        if r["reasons"]:
            print(f"  ep{r['episode']:<3} {r['scenario']:<9} " + " | ".join(r["reasons"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
