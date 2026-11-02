"""p00b 계측 실물 실행 1 개의 기록 점검 (읽기만, CPU). 로봇 연결 없음. U3 첫 판 뒤 '나머지 11 판 진행' 판단용.

점검 (FAIL 이 하나라도 있으면 나머지 판을 진행하지 않는다):
  F1 실행 폴더 기본 파일: results.csv · start_images/ep000_{front,wrist}.png · dataset (판 수) · filter_log.csv · debug.log · console.log
  F2 diag 파일: manifest.json · summary.json (정상 종료 때 씀) · chunks.jsonl · ticks.csv · chunks/ · obs/
  F3 summary: 버린 기록 0, wrapper 오류 0
  F4 manifest: 코드 sha256 (rollout_logged 8fcd4b6b · diag_log b1425bab · arm_filter a5307329), 실행 설정
     (policy num_inference_steps 5, RTC guided · EXP · mgw 10 · h 20, queue_threshold 30, checkpoint 020000)
  F5 chunk 마다: npz 에 original (50,6 정규화 = RTC 처리 뒤 Action Expert 출력) · processed (50,6 °) · noise (50,32),
     prefix (판 첫 chunk 는 없음, 나머지는 있음), 관측 PNG front · wrist (480×640×3) 존재, 값 유한
  F6 판 첫 chunk: has_prefix False · qsize_before 0 · applied_delay 0
  F7 ticks.csv 정책 틱 (pop_chunk ≥ 0): 수 = filter_log cmd 행 ≈ dataset 프레임, goal_in · sent · present (6 관절) 빈칸 없음,
     chunk 없는 send 는 판 구간 밖에만 있어야 함 (2026-10-29 U3: 판 뒤 eval_ui 처음 자세 복귀 259 행 — 정책 틱 아님)
  F8 일관성: ticks 의 (chunk, index) → npz processed 값 = filter_log raw (queue 출력) (차 < 1e-3°)
            ticks present_pan ≈ filter_log state pan (같은 판·틱, 중앙 차 < 1°)
  F11 시작 front 사진: 카메라 이동 (상자 사각형 ≤ 6 px, FAIL) · 큐브 좌표 역산 결과 (INFO — invalid_* 이어도 기록 점검은 통과, 그 판만 pe 지표에서 빠짐)
  F10 (p05 결과가 있으면) 기록 입력으로 다시 계산한 chunk = 기록 chunk (|차| ≤ 0.01°)
  F9 시간: 추론 시간 p50 (chunk.jsonl) 200–600 ms, debug.log 'RTC inference latency' 와 같은 범위, 카메라 프레임 나이 p50 < 100 ms
출력: <RUN>/diag/verify.json, 화면 (OK / FAIL / INFO 줄, 마지막 줄 VERIFY_OK 또는 VERIFY_FAIL n)
사용: PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python p00b_verify_run.py <RUN 폴더> [--expect_filter true|false]
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

J = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
CODE = {"eval/rollout_logged.py": "8fcd4b6b", "eval/diag_log.py": "b1425bab", "eval/arm_filter.py": "a5307329"}
out = {"checks": []}


def add(name, ok, detail=""):
    st = ok if isinstance(ok, str) else ("OK" if bool(ok) else "FAIL")
    out["checks"].append({"name": name, "status": st, "detail": detail})
    print(f"[{st:4}] {name}: {detail}", flush=True)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--expect_filter", choices=["true", "false"], default="true", help="이 실행에서 기대하는 --arm_filter 값")
    a = ap.parse_args()
    run = Path(a.run).expanduser().resolve()
    expect_filter = a.expect_filter == "true"
    dg = run / "diag"
    out["run"] = str(run)
    # F1
    need = ["results.csv", "start_images/ep000_front.png", "start_images/ep000_wrist.png", "filter_log.csv", "debug.log", "console.log",
            "dataset/meta/info.json"]
    miss = [f for f in need if not (run / f).exists()]
    add("F1 실행 폴더 기본 파일", not miss, f"없음 {miss}" if miss else "모두 있음")
    info = json.loads((run / "dataset/meta/info.json").read_text()) if (run / "dataset/meta/info.json").exists() else {}
    n_ep, n_fr = info.get("total_episodes"), info.get("total_frames")
    add("F1 dataset", bool(n_ep), f"판 {n_ep} · 프레임 {n_fr}")
    # F2
    miss = [f for f in ("manifest.json", "summary.json", "chunks.jsonl", "ticks.csv", "chunks", "obs") if not (dg / f).exists()]
    add("F2 diag 파일", not miss, f"없음 {miss} (summary.json 이 없으면 정상 종료 전)" if miss else str(dg))
    if not (dg / "chunks.jsonl").exists():
        return finish(run)
    # F3
    if (dg / "summary.json").exists():
        s = json.loads((dg / "summary.json").read_text())
        add("F3 버린 기록 · wrapper 오류", s["dropped"] == {"tick": 0, "chunk": 0} and not s["wrapper_errors"],
            f"written {s['written']} · dropped {s['dropped']} · errors {s['wrapper_errors']} · 제어 감싸기 p50/p99 "
            f"{s['ctl_wrapper_us']['p50']:.0f}/{s['ctl_wrapper_us']['p99']:.0f} µs")
    # F4
    m = json.loads((dg / "manifest.json").read_text())
    shas = {k: v for k, v in m.get("code_sha256", {}).items()}
    bad = [k for k, pre in CODE.items() if not any(p.endswith(k) and (v or "").startswith(pre) for p, v in shas.items())]
    add("F4 코드 sha256 (manifest)", not bad, f"다름 {bad}" if bad else "rollout_logged 8fcd4b6b · diag_log b1425bab · arm_filter a5307329")
    pc, rc = m.get("policy_cfg") or {}, m.get("rollout_cfg", "")
    conds = {"num_inference_steps=5": pc.get("num_inference_steps") == "5", "chunk_size=50": pc.get("chunk_size") == "50",
             "mode='guided'": "mode='guided'" in rc, "EXP": "RTCAttentionSchedule.EXP" in rc, "max_guidance_weight=10.0": "max_guidance_weight=10.0" in rc,
             "execution_horizon=20": "execution_horizon=20" in rc, "queue_threshold=30": "queue_threshold=30" in rc,
             "checkpoint 020000": "checkpoints/020000" in rc, "max_relative_target=8": "max_relative_target=8" in rc,
             f"arm_filter {expect_filter}": bool((m.get("rollout_logged_opts") or {}).get("arm_filter")) == expect_filter}
    add("F4 실행 설정 (manifest)", all(conds.values()), " · ".join(f"{k}{'' if v else ' ✗'}" for k, v in conds.items()))
    # F5 · F6
    metas = [json.loads(x) for x in (dg / "chunks.jsonl").read_text().splitlines()]
    probs, first, shapes = [], [], set()
    import cv2
    for k, mm in enumerate(metas):
        cid = mm["chunk_id"]
        f = dg / "chunks" / f"c{cid:05d}.npz"
        if not f.exists():
            probs.append(f"c{cid} npz 없음")
            continue
        z = np.load(f)
        for key, shp in (("original", (50, 6)), ("processed", (50, 6)), ("noise", (50, 32))):
            if key not in z or z[key].shape != shp or not np.isfinite(z[key]).all():
                probs.append(f"c{cid} {key} {None if key not in z else z[key].shape}")
        is_first = mm["qsize_before"] == 0
        if is_first:
            first.append(dict(chunk=cid, has_prefix=mm["has_prefix"], qsize_before=mm["qsize_before"], applied_delay=mm["applied_delay"],
                              prefix_in_npz="prefix" in z))
        elif "prefix" not in z or not mm["has_prefix"]:
            probs.append(f"c{cid} prefix 없음 (판 첫 chunk 아님)")
        for cam in ("front", "wrist"):
            p = dg / "obs" / f"c{cid:05d}_{cam}.png"
            if not p.exists():
                probs.append(f"c{cid} {cam}.png 없음")
            elif k < 3 or k == len(metas) - 1:
                im = cv2.imread(str(p))
                shapes.add(None if im is None else im.shape)
    add("F5 chunk 기록 (raw/RTC 뒤 chunk · noise · prefix · 관측 PNG)", not probs,
        f"chunk {len(metas)} 개 · PNG 모양 {sorted(map(str, shapes))}" + (f" · 문제 {probs[:8]}" if probs else ""))
    ok6 = bool(first) and all((not r["has_prefix"]) and r["applied_delay"] == 0 and not r["prefix_in_npz"] for r in first)
    add("F6 판 첫 chunk (prefix 없음)", ok6, f"{first}")
    # F7
    TK_all = pd.read_csv(dg / "ticks.csv")
    # 정책 틱 = queue 에서 chunk action 을 꺼내 보낸 틱. pop_chunk < 0 은 정책 밖 send (eval_ui 판 뒤 처음 자세 복귀 HOMING 등).
    TK = TK_all[TK_all.pop_chunk >= 0]
    nc = TK_all[TK_all.pop_chunk < 0]
    in_ep = int(sum(((nc.episode == e) & (nc.wall >= g.wall.min()) & (nc.wall <= g.wall.max())).sum() for e, g in TK.groupby("episode")))
    cols = [f"{p}_{j}" for p in ("goal_in", "sent", "present") for j in J]
    nan = int(TK[cols].isna().sum().sum())
    # 버린 시도 (← 다시 하기) 도 diag 에는 남는다 → dataset 프레임과는 저장된 시도만 비교 (console.log START/SAVED/DISCARD 순서)
    sys.path.insert(0, str(Path(__file__).parent))
    import p07_new_eval_analysis as P7
    att = P7.attempts(run)
    eps = sorted(TK.episode.unique())
    saved_eps = [e for e, a in zip(eps, att) if a[1] == "saved"] if len(att) == len(eps) else eps
    n_saved = int(TK.episode.isin(saved_eps).sum())
    ratio = n_saved / n_fr if n_fr else np.nan
    add("F7 시도 대응 (console START/SAVED/DISCARD ↔ diag 판)", len(att) == len(eps),
        f"시도 {len(att)} (저장 {sum(a[1] == 'saved' for a in att)} · 버림 {sum(a[1] == 'discarded' for a in att)}) · diag 판 {len(eps)}")
    add("F7 ticks.csv 정책 틱 (Goal 입력 · 보낸 Goal · Present)", nan == 0 and 0.9 <= ratio <= 1.1 and in_ep == 0,
        f"저장된 시도의 정책 틱 {n_saved} / dataset 프레임 {n_fr} (비 {ratio:.3f}) · 전체 정책 틱 {len(TK)} · 빈칸 {nan} · "
        f"chunk 없는 send {len(nc)} (판 구간 안 {in_ep} — 0 이어야 함, 나머지는 판 뒤 복귀 등)")
    # F8
    proc = {mm["chunk_id"]: np.load(dg / "chunks" / f"c{mm['chunk_id']:05d}.npz")["processed"] for mm in metas}
    T = TK[TK.pop_chunk >= 0].copy()
    T["chunk_pan"] = [proc[c][i, 0] if c in proc and 0 <= i < 50 else np.nan for c, i in zip(T.pop_chunk, T.pop_idx)]
    FL = pd.read_csv(run / "filter_log.csv", dtype={"vclip_mask": str, "ema_reset_mask": str})
    FL = FL[FL.event == "cmd"][["episode", "tick", "raw_shoulder_pan", "out_shoulder_pan"]]
    T = T.merge(FL, on=["episode", "tick"], how="inner")
    d1 = (T.raw_shoulder_pan - T.chunk_pan).abs()
    d2 = (T.goal_in_shoulder_pan - T.out_shoulder_pan).abs()
    add("F8 chunk 값 = queue 출력 raw (filter_log)", len(T) > 0 and d1.max() < 1e-3,
        f"맞춘 틱 {len(T)} · |raw − chunk| 최대 {d1.max():.2e}° · |goal_in − 필터 out| 최대 {d2.max():.2e}°")
    FS = pd.read_csv(run / "filter_log.csv", dtype={"vclip_mask": str, "ema_reset_mask": str})
    FS = FS[FS.event == "cmd"][["episode", "tick", "state_shoulder_pan"]]
    T2 = TK.merge(FS, on=["episode", "tick"], how="inner")
    dd = (T2.present_shoulder_pan - T2.state_shoulder_pan).abs()
    add("F8 Present (send 때) ≈ 틱 시작 state (filter_log)", len(T2) > 0 and dd.median() < 1.0,
        f"{len(T2)} 틱 · |차| 중앙 {dd.median():.2f}° · p95 {dd.quantile(.95):.2f}° (같은 틱 안 두 번 읽은 값)")
    per = TK.groupby("episode").size().to_dict()
    fsper = FS.groupby("episode").size().to_dict()
    add("F7 정책 틱 행 = filter_log cmd 행 (판마다)", per == fsper, f"정책 틱 {len(TK)} · filter_log cmd {len(FS)} · 판별 다름 {[e for e in set(per) | set(fsper) if per.get(e) != fsper.get(e)]}")
    # F9
    inf = np.array([(mm["t_pred1"] - mm["t_pred0"]) * 1e3 for mm in metas if mm.get("t_pred1") and mm.get("t_pred0")])
    lat = [float(x) for x in re.findall(r"RTC inference latency=([0-9.]+)s", (run / "debug.log").read_text(errors="replace"))]
    fa = [(mm["obs_perf"] - mm["cam_ts"]["front"]) * 1e3 for mm in metas if mm.get("cam_ts") and mm["cam_ts"].get("front")]
    rest = inf[1:] if len(inf) > 1 else inf
    add("F9 추론 시간 · 카메라 나이", len(rest) > 0 and 200 <= np.median(rest) <= 600 and (not fa or np.median(fa) < 100),
        f"predict p50 {np.median(rest):.0f} ms (첫 {inf[0]:.0f}) · debug.log 지연 p50 {np.median(lat) if lat else float('nan'):.2f} s (n {len(lat)}) · "
        f"front 프레임 나이 p50 {np.median(fa) if fa else float('nan'):.1f} ms · inference_delay {sorted({mm.get('inference_delay') for mm in metas}, key=str)}")
    # F11 시작 사진 → 큐브 좌표 역산 · 카메라 이동 (정책 행동 안 씀)
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        import cv2
        import p07_new_eval_analysis as P7
        tr = pd.read_csv(Path.home() / "so101_runs/main_k8/d2/data_coverage_audit/tables/a01_cube_table.csv")[["cube_x", "cube_y"]].values
        for img in sorted((run / "start_images").glob("ep*_front.png")):
            c = P7.start_coords(img, tr)
            sh = P7.box_shift(img)
            add(f"F11 카메라 이동 ({img.name})", sh is not None and sh <= 6, f"상자 사각형 좌우 변의 학습 중앙값 대비 이동 {sh} px (≤ 6 px)")
            add(f"F11 큐브 좌표 역산 ({img.name})", "INFO",
                f"{c['coord_status']} · (x, y) = ({c.get('cube_x', float('nan')):.1f}, {c.get('cube_y', float('nan')):.1f}) cm · pe "
                f"{c['pe'] if c['pe'] is None else round(c['pe'], 1)}° · σ 좌표 {c.get('pe_sigma_coord_deg', float('nan')):.1f}°"
                f"{'' if c.get('coord_accuracy_validated') else ' (미검증 참고치)'} · σ 사람 파지 {c.get('pe_sigma_grasp_deg', float('nan')):.1f}° · "
                f"학습 위치까지 {c.get('dist_nearest_train_cm', float('nan')):.1f} cm · 최근접 {c.get('nearest_K')} {c.get('dist_K_cm', float('nan')):.1f} cm"
                + (f" · {c['coord_status_reason']}" if c["coord_status_reason"] else ""))
    except Exception as ex:  # noqa: BLE001
        add("F11 좌표 역산", "INFO", f"계산 못 함: {ex!r}")
    # F10 (p05 를 먼저 돌렸으면)
    rp = dg / "replay/replay.csv"
    if rp.exists():
        R = pd.read_csv(rp)
        R = R[R.replay_max_abs_deg.notna()] if "replay_max_abs_deg" in R else R.iloc[0:0]
        add("F10 재현 (기록 PNG · state · noise · prefix → 다시 계산 = 기록 chunk)", len(R) == len(metas) and R.replay_max_abs_deg.max() <= 0.01,
            f"{len(R)}/{len(metas)} chunk · |차| 최대 {R.replay_max_abs_deg.max():.2e}° · RTC 끔 반사실 실행 구간 |차| 중앙 "
            f"{R.rtc_effect_pan_exec_absmax.median():.2f}°")
    else:
        add("F10 재현", "INFO", "diag/replay/replay.csv 없음 — p05_replay_check.py 를 먼저 돌리면 함께 점검")
    finish(run)


def finish(run):
    nf = sum(c["status"] == "FAIL" for c in out["checks"])
    (run / "diag").mkdir(exist_ok=True)
    (run / "diag/verify.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))
    print("VERIFY_OK" if nf == 0 else f"VERIFY_FAIL {nf}")


if __name__ == "__main__":
    main()
