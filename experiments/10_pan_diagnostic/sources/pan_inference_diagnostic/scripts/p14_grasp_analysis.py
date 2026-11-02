"""p14 첫 파지 직전 정렬 · 파지 결과 분석 (읽기만, CPU). 파일럿 12 판 + 같은 방법의 사람 시연 256 편 기준.

재사용: pregrasp_angles (손목 영상 빨강 · 볼록도 · 윗면 모서리 각도), pregrasp_review 의 '닫힘 시작' 정의와 '사람 정상 범위' 분류 방식,
        diag_grasp_bias/common (close_events · frames), data_coverage_audit/ac (tcp 극좌표 TCP 모델 · axes), cube_coords (판 시작 사진 좌표).
정의:
  첫 닫힘 c         = common.close_events(state gripper) 의 첫 이벤트 (닫힘이 거의 끝난 프레임)
  닫힘 시작 on      = c 전 2 s 안 그리퍼 최대 열림 프레임 뒤, 그 값보다 3 넘게 줄어든 첫 프레임 (손가락이 큐브에 닿기 전, pregrasp_review 와 같음)
  손목 영상 (on 프레임, dataset 영상): 가장 큰 빨강 덩어리 중심 (u, v: 화면 비율), 넓이 비율, 테두리 걸림, 볼록도, 윗면 모서리 각도 (파지축 대비)
     손목 카메라는 그리퍼에 고정 — 화면 가로 = 파지축 (두 손가락이 화면 아래 좌우), 위 = 그리퍼 앞쪽.
  FK (ac.tcp, 사람 첫 파지로 맞춘 극좌표 TCP 모델): on 프레임 TCP − 큐브 (판 시작 사진 좌표) 의 접선 e_t (+ = 로봇 왼쪽) · 반지름 e_r (+ = 큐브보다 멀리), z
     ※ 모델 기준점은 사람 첫 파지 평균 오차 0 으로 맞춘 것. 기존 Roll×접선 라벨은 쓰지 않는다. 큐브가 닫힘 전에 밀렸으면 틀린다.
  그리퍼 바닥 = c 뒤 1 s 안 state gripper 최솟값. 사람 시연 (큐브를 쥔 값) 11.3–14.4, 빈 닫힘은 시작 값 (≈ 1) 근처.
  들어 올림 = c 뒤 2 s 안 TCP z 최대 − c 의 z ≥ 4 cm (사람 최소 4.3 cm) 이고 그동안 그리퍼 ≥ 9
  놓침 = 들어 올린 뒤, 그리퍼가 쥔 값보다 4 넘게 열리기 (= 놓아줌) 전에 state gripper 가 6 이하로 떨어짐 (미끄러져 빠짐)
  front 확인: c + 1.5 s front 프레임에서 큐브 시작 자리 2.5 cm 안에 빨강 (넓이 ≥ 시작의 0.6 배) 이 보이면 '탁자에 남음'
분류 (사람 5–95 % 범위 기준, 판단할 근거가 없으면 '판단 불가'):
  좌우 (손목 u) : 중앙 / 화면 왼쪽 편향 / 화면 오른쪽 편향 / 판단 불가 (큐브 안 보임 · 테두리 걸림)
  깊이          : 헛잡기 (바닥 ≤ 5) / 얕은 (바닥 > 5 이고 손목 v 가 사람 범위보다 앞쪽 또는 TCP z 가 사람 p95 + 0.5 cm 보다 높음) /
                  깊은 (바닥 ≥ 9, 손목 v · TCP z 모두 사람 범위 안) / 판단 불가
  접촉 · 쥐는 힘은 재지 않았다 (영상 · 관절값으로 알 수 없음).
명령 사슬 (on 전 1 s, 관절별 |차| 중앙): RTC 뒤 chunk vs RTC 끔 반사실 (p05) · 필터 out − raw · clamp sent − goal_in · sent − present
출력: pilot/p14_grasp_pilot.csv, p14_grasp_human.csv, p14_cmd_chain.csv, p14_summary.json, p14_wrist_sheet.jpg
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python p14_grasp_analysis.py
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import cube_coords as CC  # noqa: E402

sys.path.insert(0, str(Path.home() / "so101_boxpick/scripts"))
import pregrasp_angles as PA  # noqa: E402

ac, C = CC.ac, CC.C
D2 = CC.D2
OUT = Path(__import__("os").environ.get("PILOT_DIR", D2 / "pan_inference_diagnostic/pilot"))  # 다른 묶음 (예: filter_ab) 은 PILOT_DIR 로
ROLL = D2 / "eval/rollouts"
J = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
HOLD_MIN, EMPTY_MAX, DROP_MAX, LIFT_CM = 9.0, 5.0, 6.0, 4.0


def onset_of(g, c):
    lo = max(0, c - 60)
    p = lo + int(np.argmax(g[lo:c + 1]))
    k = np.where(g[p:c + 1] < g[p] - 3)[0]
    return (p + int(k[0]) if len(k) else c), float(g[p])


def wrist_measure(img):
    m = PA.red_mask_rgb(img)
    h, w = m.shape
    b = PA.blob_near(m, w / 2, h * 0.45, max_d=w, min_area=300)
    if not b:
        return {"w_vis": False}
    blob, area, (u, v), st = b
    x, y, bw, bh = st[:4]
    edge = bool(x <= 2 or y <= 2 or x + bw >= w - 2 or y + bh >= h - 2)
    sol = PA.solidity(blob)
    ang = PA.top_edge_angle(blob) if (not edge and sol >= 0.92) else None
    return {"w_vis": True, "w_u": u / w, "w_v": v / h, "w_area": area / (w * h), "w_edge": edge, "w_sol": sol, "w_rel_deg": ang}


def grasp_metrics(s, cmd_g, cube_xy):
    """s (n,6) state, cmd_g (n,) 그리퍼 명령 (사람 = 리더 action, 정책 = 보낸 Goal). 반환 dict (프레임 번호 포함)."""
    g = s[:, 5]
    cl = C.close_events(g)
    r = {"n_close": len(cl)}
    if not cl:
        return r
    c = cl[0]
    on, gmax = onset_of(g, c)
    P = ac.tcp(s[:, :5])
    ut, ur = ac.axes(*cube_xy)
    d = P[on, :2] - np.asarray(cube_xy)
    w = slice(c, min(c + 30, len(g)))
    bottom = float(g[w].min())
    lift_w = slice(c, min(c + 61, len(g)))
    z_up = float(P[lift_w, 2].max() - P[c, 2])
    held = bool(g[lift_w].min() >= HOLD_MIN)
    lifted = bool(z_up >= LIFT_CM and held)
    # 놓침: 들어 올린 뒤 (z ≥ c+4 cm 처음 시각 이후) 명령이 열기 전 state ≤ 6
    dropped = None
    if lifted:
        # 들어 올린 뒤: 그리퍼가 쥔 값보다 4 넘게 열리면 '놓아줌' (상자에 넣기), 그 전에 6 이하로 떨어지면 '놓침' (미끄러져 빠짐)
        t_up = c + int(np.argmax(P[c:, 2] - P[c, 2] >= LIFT_CM))
        hold_val = float(np.median(g[c:t_up + 1]))
        dropped, t_end = False, len(g)
        for t in range(t_up, len(g)):
            if g[t] > hold_val + 4:
                t_end = t
                break
            if g[t] <= DROP_MAX:
                dropped, t_end = True, t
                break
        r.update(t_lift=t_up, t_hold_end=t_end, hold_val=hold_val, hold_s=(t_end - t_up) / 30)
    r.update(c=c, on=on, on_to_c=c - on, open_max=gmax, bottom=bottom, z_up=z_up, held_2s=held, lifted=lifted, dropped=dropped,
             e_t=float(d @ ut), e_r=float(d @ ur), z_on=float(P[on, 2]), z_c=float(P[c, 2]),
             roll_on=float(s[on, 4]), wflex_on=float(s[on, 3]), pan_on=float(s[on, 0]), lift_on=float(s[on, 1]), elbow_on=float(s[on, 2]))
    return r


def human():
    D = ac.load_d2()
    A1 = pd.read_csv(ac.TAB / "a01_cube_table.csv")
    cache, rows = {}, []
    for e, (s, a, *_rest) in D.items():
        q = A1[A1.ep == e].iloc[0]
        r = dict(ep=e, group=q.group, mode=q["mode"], cube_x=q.cube_x, cube_y=q.cube_y, yaw=q.yaw_used)
        r.update(grasp_metrics(s, a[:, 5], (q.cube_x, q.cube_y)))
        if "on" in r:
            img = C.frames(D2 / "dataset", e, "wrist", r["on"], r["on"], cache)[0]
            r.update(wrist_measure(img))
        rows.append(r)
    return pd.DataFrame(rows)


def ref_ranges(H):
    q = lambda c, p: float(H[c].quantile(p))  # noqa: E731
    return {"w_u": (q("w_u", .05), q("w_u", .95)), "w_v": (q("w_v", .05), q("w_v", .95)), "w_area": (q("w_area", .05), q("w_area", .95)),
            "z_c": (q("z_c", .05), q("z_c", .95)), "e_t": (q("e_t", .05), q("e_t", .95)), "e_r": (q("e_r", .05), q("e_r", .95)),
            "bottom": (q("bottom", .05), q("bottom", .95)), "w_rel_abs_p90": float(H.w_rel_deg.abs().quantile(.9))}


def classify(r, R):
    out = {}
    if not r.get("w_vis") or r.get("w_edge"):
        out["lr_class"] = "판단 불가"
        out["lr_reason"] = "손목 영상에 큐브 없음" if not r.get("w_vis") else "큐브가 손목 화면 테두리에 걸림"
    else:
        lo, hi = R["w_u"]
        out["lr_class"] = "중앙" if lo - 0.02 <= r["w_u"] <= hi + 0.02 else ("화면 왼쪽 편향" if r["w_u"] < lo - 0.02 else "화면 오른쪽 편향")
    b = r.get("bottom")
    if b is None or (isinstance(b, float) and math.isnan(b)):
        out["depth_class"] = "판단 불가"
    elif b <= EMPTY_MAX:
        out["depth_class"] = "헛잡기"
    else:
        ahead = bool(r.get("w_vis") and not r.get("w_edge") and r["w_v"] < R["w_v"][0] - 0.02)
        high = bool(r["z_c"] > R["z_c"][1] + 0.5)
        if ahead or high:
            out["depth_class"] = "얕은"
            out["depth_reason"] = " · ".join(x for x, f in (("손목 화면에서 큐브가 사람 범위보다 앞쪽", ahead), ("TCP z 가 사람 p95 + 0.5 cm 보다 높음", high)) if f)
        elif b >= HOLD_MIN and r.get("w_vis") and not r.get("w_edge"):
            out["depth_class"] = "깊은"
        else:
            out["depth_class"] = "판단 불가"
            out["depth_reason"] = f"바닥 {b:.1f} (부분 닫힘) 또는 손목 근거 없음"
    if r.get("lifted"):
        out["first_grasp"] = "놓침" if r.get("dropped") else "성공 (들어 올림 · 놓치지 않음)"
    elif r.get("held_2s") is False and b is not None and b > EMPTY_MAX:
        out["first_grasp"] = "쥐었다가 2 s 안에 풀림 / 못 들어 올림"
    else:
        out["first_grasp"] = "실패 (못 쥠 · 못 들어 올림)"
    return out


def cmd_chain(run, ep_diag, on_tick, n_ticks):
    """on 전 1 s (30 틱) 관절별 |차| 중앙."""
    FL = pd.read_csv(ROLL / run / "filter_log.csv", dtype={"vclip_mask": str, "ema_reset_mask": str})
    f = FL[(FL.event == "cmd") & (FL.episode == ep_diag)].sort_values("tick").reset_index(drop=True)
    TK = pd.read_csv(ROLL / run / "diag/ticks.csv")
    t = TK[(TK.episode == ep_diag) & (TK.pop_chunk >= 0)].sort_values("tick").reset_index(drop=True)
    RZ = np.load(ROLL / run / "diag/replay/replay.npz")
    lo, hi = max(0, on_tick - 30), on_tick
    r = {}
    for k, j in enumerate(J):
        raw, out = f[f"raw_{j}"].values[lo:hi], f[f"out_{j}"].values[lo:hi]
        gi, se, pr = t[f"goal_in_{j}"].values[lo:hi], t[f"sent_{j}"].values[lo:hi], t[f"present_{j}"].values[lo:hi]
        off = np.array([RZ[f"rtc_off_c{int(c):05d}"][int(i), k] if f"rtc_off_c{int(c):05d}" in RZ else np.nan
                        for c, i in zip(t.pop_chunk.values[lo:hi], t.pop_idx.values[lo:hi])])
        r[f"rtc_minus_off_{j}"] = float(np.nanmedian(np.abs(raw - off)))
        r[f"filter_{j}"] = float(np.median(np.abs(out - raw)))
        r[f"clamp_{j}"] = float(np.median(np.abs(se - gi)))
        r[f"sent_minus_present_{j}"] = float(np.median(np.abs(se - pr)))
    return r


def main():
    import cv2
    H = human()
    H.to_csv(OUT / "p14_grasp_human.csv", index=False)
    R = ref_ranges(H.dropna(subset=["w_u"]))
    hv = H.dropna(subset=["w_u", "e_t"])
    map_corr = float(np.corrcoef(hv.w_u, hv.e_t)[0, 1])
    P = pd.read_csv(OUT / "pilot_episodes.csv")
    cache, rows, chain, tiles = {}, [], [], []
    for _, p in P.iterrows():
        run = ROLL / p.run
        FL = pd.read_csv(run / "filter_log.csv", dtype={"vclip_mask": str, "ema_reset_mask": str})
        f = FL[(FL.event == "cmd") & (FL.episode == p.episode)].sort_values("tick")
        s = f[[f"state_{j}" for j in J]].values.astype(float)
        TK = pd.read_csv(run / "diag/ticks.csv")
        t = TK[(TK.episode == p.episode) & (TK.pop_chunk >= 0)].sort_values("tick")
        r = dict(label=p.label, group=p.group, run=p.run, ds_ep=int(p.ds_ep), episode=int(p.episode), verdict=p.verdict,
                 cube_x=p.cube_x, cube_y=p.cube_y, cube_yaw_deg=p.get("cube_yaw_deg"))
        r.update(grasp_metrics(s, t.sent_gripper.values.astype(float), (p.cube_x, p.cube_y)))
        if "on" in r:
            ds = run / "dataset"
            img = C.frames(ds, int(p.ds_ep), "wrist", r["on"], r["on"], cache)[0]
            r.update(wrist_measure(img))
            fr0 = C.frames(ds, int(p.ds_ep), "front", r["on"], r["on"], cache)[0]
            d0 = CC.detect(fr0)
            if d0["n_blobs"] and 0.6 <= d0["area_ratio"] <= 1.6:
                r["front_shift_at_on_cm"] = math.hypot(d0["x"] - p.cube_x, d0["y"] - p.cube_y)
            fc = min(r["c"] + 45, len(s) - 1)
            fr1 = C.frames(ds, int(p.ds_ep), "front", fc, fc, cache)[0]
            b = [x for x in C.blobs(C.red_mask(fr1), 80)]
            near = [x for x in b if math.dist(C.px_to_cm(*x[1]), (p.cube_x, p.cube_y)) <= 2.5 and x[0] >= 0.6 * CC.area_expected(*x[1])]
            r["front_cube_on_table_1p5s"] = bool(near)
            tile = cv2.cvtColor(img, cv2.COLOR_RGB2BGR).copy()
            cv2.putText(tile, f"{p.label} on={r['on']}", (8, 28), 0, 0.9, (0, 0, 255), 2)
            tiles.append(cv2.resize(tile, (320, 240)))
            chain.append(dict(label=p.label, **cmd_chain(p.run, int(p.episode), int(r["on"]), len(s))))
        r.update(classify(r, R))
        r["cube_in_wrist_vs_human"] = ("판단 불가 (큐브 안 보임)" if not r.get("w_vis") else
                                       "앞쪽 (덜 다가감)" if r["w_v"] < R["w_v"][0] - 0.02 else
                                       "아래쪽 · 손가락 사이 (화면 아래 가장자리)" if r["w_v"] > R["w_v"][1] + 0.02 else "앞뒤 범위 안")
        if r.get("w_vis") and not r.get("w_edge") and r.get("w_sol", 1) < 0.85:
            r["cube_in_wrist_vs_human"] += f" · 손가락에 가려짐 (볼록도 {r['w_sol']:.2f}, 화면 {'왼쪽' if r['w_u'] < 0.5 else '오른쪽'})"
        if r.get("lifted") and r.get("front_cube_on_table_1p5s"):
            r["first_grasp"] = "판단 불가 (관절은 들어 올림, front 에는 큐브가 탁자에 남음)"
        rows.append(r)
    D = pd.DataFrame(rows)
    D.to_csv(OUT / "p14_grasp_pilot.csv", index=False)
    CH = pd.DataFrame(chain)
    CH.to_csv(OUT / "p14_cmd_chain.csv", index=False)
    while len(tiles) % 4:
        tiles.append(np.zeros_like(tiles[0]))
    cv2.imwrite(str(OUT / "p14_wrist_sheet.jpg"), np.vstack([np.hstack(tiles[i:i + 4]) for i in range(0, len(tiles), 4)]))
    hc = H.dropna(subset=["w_u"]).apply(lambda r: pd.Series(classify(r, R)), axis=1)
    S = {"human_ref_5_95": R, "human_n": int(len(H)), "human_corr_wu_et": map_corr,
         "human_class_counts": {k: hc[k].value_counts().to_dict() for k in ("lr_class", "depth_class", "first_grasp")},
         "human_lifted_frac": float(H.lifted.mean()), "human_dropped_frac": float(H.dropped.dropna().mean()),
         "pilot_class_counts": {k: D[k].value_counts().to_dict() for k in ("lr_class", "depth_class", "first_grasp")},
         "pilot_by_group": {g: {k: x[k].value_counts().to_dict() for k in ("lr_class", "depth_class", "first_grasp")} for g, x in D.groupby("group")}}
    json.dump(S, open(OUT / "p14_summary.json", "w"), indent=1, ensure_ascii=False, default=float)
    pd.set_option("display.width", 250, "display.max_columns", 40)
    print(json.dumps(S, indent=1, ensure_ascii=False, default=float))
    print(D.reindex(columns=["label", "verdict", "n_close", "on_to_c", "bottom", "z_up", "lifted", "dropped", "hold_s", "cube_in_wrist_vs_human", "front_cube_on_table_1p5s", "w_vis", "w_u", "w_v",
             "w_area", "w_rel_deg", "e_t", "e_r", "z_c", "roll_on", "wflex_on", "cube_yaw_deg", "front_shift_at_on_cm", "lr_class", "depth_class",
             "first_grasp"]).round(2).to_string(index=False))
    print(CH.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
