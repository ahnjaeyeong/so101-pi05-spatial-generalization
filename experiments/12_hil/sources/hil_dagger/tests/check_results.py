"""가짜 장치 e2e 결과 검사 · 측정. 사용: python check_results.py <out_root> [scenario ...] → <out_root>/<scen>/result.json, <out_root>/SUMMARY.md"""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

J = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
D2_INFO = Path.home() / "so101_runs/main_k8/d2/dataset/meta/info.json"


def load_ds(root):
    files = sorted(glob.glob(str(root / "data/*/*.parquet")))
    if not files:
        return None, None
    import pandas as pd
    df = pd.concat([pq.read_table(f).to_pandas() for f in files], ignore_index=True)
    info = json.loads((root / "meta/info.json").read_text())
    return df, info


def check(out: Path):
    raw = json.loads((out / "raw.json").read_text())
    W = [w for w in raw["follower_writes"] if w.get("kind") == "write"]
    L = raw["leader_events"]
    E = raw["engine_events"]
    C = {c["cid"]: c for c in raw["chunks"]}
    ops = raw["ops"]
    res = {"scenario": out.name, "checks": {}, "measures": {}}

    def chk(name, ok, detail=""):
        res["checks"][name] = {"pass": bool(ok), "detail": detail}

    m = res["measures"]
    m["wall_s"] = round(raw["wall_s"], 1)
    m["main_exception"] = (raw["err"].get("main") or "").strip().splitlines()[-1:] or None
    m["script_exception"] = (raw["err"].get("script") or "").strip().splitlines()[-1:] or None
    m["n_writes_by_origin"] = {}
    for w in W:
        m["n_writes_by_origin"][w["origin"]] = m["n_writes_by_origin"].get(w["origin"], 0) + 1

    # 1. 단일 writer: 모든 follower 쓰기가 MainThread
    threads = sorted({w["thread"] for w in W})
    chk("C1_single_writer_thread", threads == ["MainThread"], f"threads={threads}")

    # 2. 정책 명령은 AUTONOMOUS 에서만
    bad = [w for w in W if w["origin"] == "policy" and w["phase"] != "autonomous"]
    chk("C2_policy_cmd_only_in_autonomous", not bad, f"violations={len(bad)}")

    # 3. 사람 명령(teleop)은 CORRECTING 에서만, 그때 리더 토크 꺼짐
    tw = [w for w in W if w["origin"] == "teleop"]
    chk("C3_teleop_cmd_only_in_correcting_with_leader_free", all(w["phase"] == "correcting" and w["leader_torque"] is False for w in tw),
        f"teleop writes={len(tw)}")
    unk = [w["origin"] for w in W if w["origin"].startswith("other")]
    chk("C3b_no_unclassified_writes", not unk, f"{sorted(set(unk))[:3]}")

    # 4. 정책 구간에서 리더 토크 꺼짐 (사람이 놓은 리더가 정책을 따라 움직이지 않음)
    pw = [w for w in W if w["origin"] == "policy"]
    chk("C4_leader_free_during_autonomous", all(w["leader_torque"] is False for w in pw), f"policy writes={len(pw)}")

    # 5. 재개 뒤 stale chunk 없음: 재개 reset 이후의 정책 쓰기는 reset 뒤 시작한 chunk 에서만 (official = 미필터 → wrist_roll 로 chunk 식별)
    resumes = [e for e in E if e["kind"] == "reset" and e["phase"] == "autonomous" and e["t"] > 0]
    stale = []
    if not raw["adapter"]:
        for r in resumes:
            ep_after = r["epoch_before"] + 1
            nxt = [e["t"] for e in E if e["kind"] == "pause" and e["t"] > r["t"]]
            t_end = min(nxt) if nxt else 1e9
            for w in pw:
                if r["t"] < w["t"] < t_end:
                    cid = int(round(w["goal"]["wrist_roll"] / 0.01))
                    c = C.get(cid)
                    if c is None or c["epoch_start"] is None or c["epoch_start"] < ep_after:
                        stale.append((round(w["t"], 3), cid, None if c is None else c["epoch_start"], ep_after))
        chk("C5_no_stale_chunk_after_resume", not stale and resumes, f"resumes={len(resumes)} stale={stale[:3]}")
    # 정지 시점 큐 길이 · in-flight chunk
    pauses = [e for e in E if e["kind"] == "pause"]
    m["rtc_qsize_at_pause"] = [e["qsize_before"] for e in pauses]
    inflight = []
    for p in pauses:
        inflight.append(sum(1 for c in C.values() if c["t_start"] < p["t"] < c["t_end"]))
    m["inflight_chunks_at_pause"] = inflight
    # 정지 뒤 첫 정책 쓰기 없음 (다음 resume 까지)
    after_pause = []
    for p in pauses:
        nxt = [r["t"] for r in resumes if r["t"] > p["t"]]
        t_end = min(nxt) if nxt else 1e9
        after_pause += [w for w in pw if p["t"] < w["t"] < t_end]
    chk("C6_no_policy_cmd_between_pause_and_resume", not after_pause, f"n={len(after_pause)}")

    # 7. 리더 동기화: 정지 → 리더 토크 on → 리더가 follower 마지막 명령으로 이동 (2 s blocking) → Tab 에 torque off
    ton = [e for e in L if e["kind"] == "torque_on"]
    toff = [e for e in L if e["kind"] == "torque_off"]
    m["leader_torque_on_phases"] = [e["phase"] for e in ton]
    m["leader_torque_off_phases"] = [e["phase"] for e in toff]
    gaps = []
    for e in toff:
        if e["phase"] != "correcting":
            continue
        prev = [w for w in W if w["t"] <= e["t"]]
        if not prev:
            continue
        fp = prev[-1]["present"]
        gaps.append({j: round(e["present"][j] - fp[j], 2) for j in J})
    m["handover_leader_minus_follower_at_tab_deg"] = gaps
    # 첫 teleop 쓰기에서 follower goal 의 변화 (점프)
    jumps = []
    for i, w in enumerate(W):
        if w["origin"] == "teleop" and i > 0 and W[i - 1]["origin"] != "teleop":
            jumps.append({j: round(w["goal"][j] - W[i - 1]["goal"][j], 2) for j in J})
    m["first_teleop_goal_jump_deg"] = jumps
    # 정지 순간 follower present 와 마지막 정책 명령 차이 (hold = 마지막 명령 유지)
    lags = []
    for p in pauses:
        prev = [w for w in pw if w["t"] <= p["t"]]
        if prev:
            lags.append({j: round(prev[-1]["goal"][j] - prev[-1]["present"][j], 2) for j in J})
    m["last_policy_cmd_minus_present_at_pause_deg"] = lags
    # follower 쓰기 공백 (리더 이동 blocking)
    ts = [w["t"] for w in W]
    gaps_t = [(round(ts[i - 1], 2), round(ts[i] - ts[i - 1], 2)) for i in range(1, len(ts)) if ts[i] - ts[i - 1] > 0.2]
    m["follower_write_gaps_over_0.2s"] = gaps_t
    # CORRECTING → PAUSED torque on 뒤 리더 이동량 (goal 레지스터 해석에 따라 다름)
    snap = []
    for e in ton:
        if e["phase"] == "paused" and any(t["phase"] == "correcting" and t["t"] < e["t"] for t in toff):
            snap.append({j: round(e["goal"][j] - e["present"][j], 2) for j in J})
    m["leader_goal_minus_present_at_torque_on_after_correction"] = snap
    m["leader_disconnect"] = [e for e in L if e["kind"] == "disconnect"]
    m["follower_disconnect"] = [w for w in raw["follower_writes"] if w.get("kind") == "disconnect"]
    homes = [w for w in W if w["origin"] == "home"]
    m["home_writes"] = len(homes)
    if homes:
        m["home_move_deg"] = {j: round(homes[-1]["goal"][j] - homes[0]["present"][j], 2) for j in J}

    # 8. 데이터셋
    df, info = load_ds(out / "dataset")
    if df is None:
        m["dataset"] = None
    else:
        eps = sorted(df["episode_index"].unique().tolist())
        m["dataset"] = {"episodes": len(eps), "frames_per_ep": [int((df.episode_index == e).sum()) for e in eps],
                        "features": sorted(info["features"].keys()), "fps": info["fps"],
                        "intervention_all_true": bool(np.all(np.stack(df["intervention"].to_numpy()).astype(bool))) if "intervention" in df else None,
                        "tasks": json.loads(json.dumps(sorted(set(df["task_index"].tolist()))))}
        d2 = json.loads(D2_INFO.read_text())
        extra = sorted(set(info["features"]) - set(d2["features"]))
        missing = sorted(set(d2["features"]) - set(info["features"]))
        dt = {k: (info["features"][k]["dtype"], d2["features"][k]["dtype"]) for k in info["features"] if k in d2["features"]
              and info["features"][k]["dtype"] != d2["features"][k]["dtype"]}
        m["dataset"]["vs_d2"] = {"extra": extra, "missing": missing, "dtype_diff": dt,
                                 "names_equal": info["features"]["action"]["names"] == d2["features"]["action"]["names"]}
        # 녹화 action = 리더 읽기? pan 범위 확인
        a = np.stack(df["action"].to_numpy())
        s = np.stack(df["observation.state"].to_numpy())
        m["dataset"]["per_ep_pan_action_range"] = [[round(float(a[df.episode_index == e, 0].min()), 1), round(float(a[df.episode_index == e, 0].max()), 1)] for e in eps]
        m["dataset"]["per_ep_first_frame_action_minus_state"] = [
            {j: round(float(a[df.episode_index == e][0, i] - s[df.episode_index == e][0, i]), 2) for i, j in enumerate(J)} for e in eps]
        tsx = df["timestamp"].to_numpy()
        m["dataset"]["timestamp_step_ok"] = bool(all(np.allclose(np.diff(tsx[df.episode_index == e]), 1 / 30, atol=1e-4) for e in eps))
    res["ops"] = [o for o in ops if o["kind"] in ("phase_after_tab_in_auto", "phase_after_double_space", "inject", "adapter_patch")]

    # 어댑터 기록
    evp = out / "hil_events.jsonl"
    if evp.exists():
        evs = [json.loads(x) for x in evp.read_text().splitlines()]
        kinds = {}
        for e in evs:
            kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
        m["hil_events_kinds"] = kinds
        m["hil_transitions"] = [(e["old"], e["new"], e.get("blocking_s"), e.get("frames_in_current"), e.get("episodes_saved"), e.get("rtc_qsize"),
                                 bool(e.get("pre_pause_snapshot"))) for e in evs if e["kind"] == "transition"]
        m["hil_marks"] = [(e["mark"], e["phase"], e.get("frames_in_current"), e.get("episodes_saved")) for e in evs if e["kind"] == "mark"]
        m["hil_key_dropped"] = [(e["event"], e["phase"], e.get("in_transition"), e.get("since_last_transition_s"), e.get("reason")) for e in evs if e["kind"] == "key_dropped"]
        end = [e for e in evs if e["kind"] == "session_end"]
        m["hil_session_end"] = {k: end[-1].get(k) for k in ("phase_at_end", "ended_during_correction", "episodes_saved", "frames_in_current")} if end else None
        snaps = sorted((out / "snapshots").glob("*.npz")) if (out / "snapshots").exists() else []
        m["hil_snapshots"] = []
        for p in snaps:
            z = np.load(p)
            m["hil_snapshots"].append({"file": p.name, "n": int(len(z["t"])), "span_s": round(float(z["t"][-1] - z["t"][0]), 2),
                                       "front": list(z["front"].shape) if "front" in z else None})
        fl = out / "filter_log.csv"
        if fl.exists():
            import pandas as pd
            f = pd.read_csv(fl, comment="#")
            m["filter_log_rows"] = int(len(f))
            m["filter_log_cmd_rows"] = int((f["event"] == "cmd").sum())
            m["filter_log_raw_vs_out_max_abs_diff"] = float((f.loc[f["event"] == "cmd", [c for c in f.columns if c.startswith("out_")]].to_numpy() - f.loc[f["event"] == "cmd", [c for c in f.columns if c.startswith("raw_")]].to_numpy()).__abs__().max()) if (f["event"] == "cmd").any() else None
            m["filter_log_episodes"] = sorted(set(int(x) for x in f["episode"]))
    # ---- 2026-11-04 v2 추가 검사 ----
    evs = []
    if (out / "hil_events.jsonl").exists():
        evs = [json.loads(x) for x in (out / "hil_events.jsonl").read_text().splitlines()]
    t0 = raw.get("rec_t0")

    def ft(e):  # 이벤트 perf → 가짜 시계
        return e["perf"] - t0 if (t0 is not None and "perf" in e) else None

    homes = [w for w in W if w["origin"] == "home"]
    fails = raw.get("policy_fail_t") or []
    if fails:
        tf = fails[0]
        aft = [w for w in pw if w["t"] > tf]
        m["first_inference_error_t"] = round(tf, 3)
        m["policy_writes_after_first_error"] = len(aft)
        m["policy_write_span_after_first_error_s"] = round(aft[-1]["t"] - tf, 3) if aft else 0.0
        # follower 팔 이동량: 오류 순간 → 1.0 s 뒤 (present)
        def pres_at(t):
            prev = [w for w in raw["follower_writes"] if w.get("kind") == "write" and w["t"] <= t]
            return prev[-1]["present"] if prev else None
        p0, p1 = pres_at(tf), pres_at(tf + 1.0)
        if p0 and p1:
            m["follower_arm_motion_after_error_1s_deg"] = round(max(abs(p1[j] - p0[j]) for j in J[:5]), 2)
    lat = [e for e in evs if e["kind"] == "policy_fault"]
    hnd = [e for e in evs if e["kind"] == "policy_fault_handled"]
    if lat:
        tl = ft(lat[0])
        m["fault_latch_t"] = round(tl, 3)
        m["latch_after_first_error_s"] = round(tl - fails[0], 4) if fails else None
        m["policy_writes_after_latch"] = sum(1 for w in pw if w["t"] > tl)
        if hnd:
            th = ft(hnd[0])
            m["fault_handled_after_latch_s"] = round(th - tl, 4)
            m["policy_writes_after_handled"] = sum(1 for w in pw if w["t"] > th)
            m["fault_handled"] = {k: hnd[0].get(k) for k in ("rtc_qsize_before", "rtc_qsize_after", "epoch_before", "epoch_after")}
            fh = [w for w in W if w["origin"] == "fault_hold"]
            m["fault_hold_writes"] = len(fh)
        chk("A10a_no_policy_cmd_after_fault", hnd and m["policy_writes_after_handled"] == 0 and m["policy_writes_after_latch"] <= 1
            and m["policy_writes_after_first_error"] <= 1,
            f"after first error={m.get('policy_writes_after_first_error')} after latch={m['policy_writes_after_latch']} after handled={m.get('policy_writes_after_handled')}")
        chk("A10b_rtc_queue_invalidated", hnd and hnd[0]["rtc_qsize_after"] == 0 and hnd[0]["epoch_after"] == hnd[0]["epoch_before"] + 1,
            str(m.get("fault_handled")))
        resumed = [e for e in E if e["kind"] == "resume" and e["t"] > tl]
        chk("A10c_no_resume_after_fault", not resumed and any(o["kind"] == "phase_after_space_attempt" and o["phase"] == "paused" for o in ops),
            f"engine.resume() calls after latch={len(resumed)}")
    if raw["adapter"]:
        ch = [e for e in evs if e["kind"] == "end_choice"]
        m["end_choice"] = ch[-1] if ch else None
        fd = m["follower_disconnect"]
        choice = ch[-1]["choice"] if ch else None
        if choice == "home":
            te = ft(ch[-1])
            chk("A11_home_only_after_user_choice", homes and all(w["t"] > te for w in homes), f"home writes={len(homes)} first={homes[0]['t'] if homes else None} choice_t={te}")
        else:
            chk("A11_no_auto_return", not homes and ch, f"home writes={len(homes)} choice={choice}")
        if choice == "hold":
            chk("A11_hold_keeps_torque", fd and fd[-1]["torque_off"] is False and (not m["leader_disconnect"] or m["leader_disconnect"][-1]["torque_off"] is False),
                f"follower torque_off={[d['torque_off'] for d in fd]} leader={[d['torque_off'] for d in m['leader_disconnect']]}")
        if out.name.startswith("S16"):
            mk = [e["mark"] for e in evs if e["kind"] == "mark"]
            ks = [e["event"] for e in evs if e["kind"] == "key"]
            chk("A14_terminal_keys_and_menu", ch and ch[-1]["source"] == "tty" and ch[-1]["choice"] == "release" and fd and fd[-1]["torque_off"] is True
                and mk == ["type_R1", "recovery_done", "first_grasp_ok", "final_success"] and ks.count("pause_resume") == 2 and ks.count("correction") == 2
                and "esc" in ks, f"choice={ch[-1] if ch else None} marks={mk} keys={ks}")
        rlo = [e for e in evs if e["kind"] == "rollout_logged"]
        af = rlo[0].get("opts", {}).get("arm_filter") if rlo else None
        chk("A12_arm_filter_off", af is False and m.get("filter_log_raw_vs_out_max_abs_diff") in (0.0, None),
            f"arm_filter opt={af} |out-raw| max={m.get('filter_log_raw_vs_out_max_abs_diff')}")
    # 교정 action 저장값 vs clamp (교정 판이 있으면 항상 측정)
    df_, _ = load_ds(out / "dataset")
    reads = raw.get("leader_reads") or []
    if df_ is not None and tw and reads:
        acts = np.stack(df_.sort_values("index")["action"].to_numpy())
        n = min(len(acts), len(tw))
        rt = np.array([r[0] for r in reads])
        d_leader, d_goal, step = [], [], []
        for i in range(n):
            w = tw[i]
            k = int(np.searchsorted(rt, w["t"], side="right")) - 1
            lr = reads[k][1]
            d_leader.append(max(abs(acts[i][jj] - lr[j]) for jj, j in enumerate(J)))
            d_goal.append(max(abs(acts[i][jj] - w["goal"][j]) for jj, j in enumerate(J)))
        prev_present = [max(abs(w["goal"][j] - w["present_read"][j]) for j in J) for w in tw if "present_read" in w]
        m["correction_frames_vs_teleop_writes"] = [len(acts), len(tw)]
        m["action_minus_leader_read_max"] = round(float(max(d_leader)), 4)
        m["action_minus_sent_goal_max"] = round(float(max(d_goal)), 2)
        m["frames_action_ne_sent_goal(>0.5deg)"] = int(sum(1 for x in d_goal if x > 0.5))
        m["sent_goal_minus_prev_present_max"] = round(float(max(prev_present)), 2) if prev_present else None
        if out.name.startswith("S11"):
            chk("A13_saved_action_is_leader_reading_pre_clamp", m["action_minus_leader_read_max"] < 1e-3 and m["frames_action_ne_sent_goal(>0.5deg)"] > 0,
                f"|action−leader| max {m['action_minus_leader_read_max']} · |action−sent goal| max {m['action_minus_sent_goal_max']} · frames differ {m['frames_action_ne_sent_goal(>0.5deg)']}")
            chk("A13b_sent_goal_clamped_8deg", m["sent_goal_minus_prev_present_max"] is not None and m["sent_goal_minus_prev_present_max"] <= 8.0 + 1e-6,
                f"max |sent goal − present read by clamp| = {m['sent_goal_minus_prev_present_max']}")

    inj = [o for o in ops if o["kind"] == "inject"]
    if inj:
        ti = inj[0]["t"]
        after = [w for w in pw if w["t"] > ti]
        m["inject"] = {"what": inj[0]["what"], "policy_writes_after_inject": len(after),
                       "last_policy_write_after_inject_s": round(after[-1]["t"] - ti, 2) if after else None,
                       "teleop_writes_after_inject": sum(1 for w in tw if w["t"] > ti),
                       "home_writes_after_inject": sum(1 for w in W if w["origin"] == "home" and w["t"] > ti)}
    if raw["adapter"]:
        ap = [o for o in ops if o["kind"] == "adapter_patch"]
        chk("A1_dagger_uses_guarded_rollout_logged_send", ap and ap[0].get("dagger_send_name") == "guarded_send" and ap[0]["core_send_module"] == "rollout_logged",
            str(ap[0] if ap else None))
        n_cmd = m.get("filter_log_cmd_rows")
        chk("A1b_every_policy_write_passed_filter", n_cmd is not None and n_cmd == len(pw), f"filter cmd rows={n_cmd} policy writes={len(pw)}")
        mrt = {}
        for w in W:
            mrt.setdefault(w["origin"], set()).add(w.get("mrt"))
        m["max_relative_target_by_origin"] = {k: sorted(v, key=str) for k, v in mrt.items()}
        want_teleop = {8.0}
        first_space = [o["t"] for o in ops if o["kind"] == "key" and o["name"] == "space"]
        if out.name.startswith("S10"):
            pre = [w for w in pw if first_space and w["t"] < first_space[0]]
            chk("A9_no_policy_cmd_before_first_space", not pre and [o for o in ops if o["kind"] == "phase_at_start" and o["phase"] == "paused"],
                f"policy writes before first Space={len(pre)}")
            chk("A9_first_tab_no_jump", jumps and max(abs(v) for v in jumps[0].values()) < 1.0, f"first teleop goal jump={jumps[:1]}")
        chk("A8_clamp_8_in_all_phases", mrt.get("teleop", want_teleop) == want_teleop and mrt.get("policy", {8.0}) == {8.0} and mrt.get("home", {8.0}) == {8.0},
            str(m["max_relative_target_by_origin"]))
        snaps = m["leader_goal_minus_present_at_torque_on_after_correction"]
        chk("A7_no_leader_snap_after_correction", all(max(abs(v) for v in d.values()) < 0.5 for d in snaps), f"{snaps}")
    return res


def main():
    root = Path(sys.argv[1])
    scens = sys.argv[2:] or sorted(p.name for p in root.iterdir() if (p / "raw.json").exists())
    rows = []
    for s in scens:
        r = check(root / s)
        (root / s / "result.json").write_text(json.dumps(r, ensure_ascii=False, indent=1, default=float))
        n_fail = sum(not c["pass"] for c in r["checks"].values())
        rows.append((s, len(r["checks"]), n_fail, r))
        print(f"== {s}: checks {len(r['checks']) - n_fail}/{len(r['checks'])} pass")
        for k, c in r["checks"].items():
            print(f"   {'PASS' if c['pass'] else 'FAIL'} {k} {c['detail']}")
    lines = ["# 가짜 장치 e2e 결과 (check_results.py 자동 생성)", "", "| 시나리오 | 검사 통과 | 예외 |", "|---|---|---|"]
    for s, n, f, r in rows:
        lines.append(f"| {s} | {n - f}/{n} | {r['measures']['main_exception'] or '-'} |")
    (root / "SUMMARY.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
