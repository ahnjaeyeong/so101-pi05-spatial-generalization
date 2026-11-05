#!/home/user/so101-env/bin/python
"""시각 시연 가이드 (2026-11-03, 파일럿 12편 · 먼저 R2-P) — d2 사람 성공 시연 참고 · 단계 · 녹화 뒤 검토 표시.

원칙 (작업 지시):
  - 참고 값은 d2 사람 시연의 실제 기록값 (관절 · 리더 그리퍼 명령 · 팔로워 그리퍼 · 영상) 이다. 임의 목표값 · 3D 궤적을 만들지 않는다.
  - 화면 좌표를 로봇 이동 방향으로 바꾸는 화살표를 만들지 않는다. 닫기 영역은 참고일 뿐, '닫아도 안전' 판정을 하지 않는다.
  - 단계는 사용자가 고른다 (영상 창 F5/F6, 단계 칸 클릭). 자동 추정은 보조 표시.
  - R1 의 큰 Pan 복구 · R2-O 재개방은 d2 에 없는 상황 — 그 단계에는 d2 참고를 '정답' 으로 보여 주지 않는다 (단계 설정 ref: none).

참고 색인 만들기 (오프라인, d2 dataset 읽기만, 한 번):
  PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python tools/r12_guide.py build
  → reference/d2_ref_index.json · reference/d2_ref_traj.npz · reference/frames/ep###_<key>_{front,wrist}.jpg (git 에 넣지 않음)

키프레임 정의 (d2 판마다, 30 fps 프레임 번호):
  k_close = 리더 그리퍼 명령 첫 닫힘 시작 (r2_common.close_onsets — below_review 의 사람 T2 와 같은 규칙)
  k_open  = k_close 전 마지막으로 리더 그리퍼 명령이 15 미만 → 15 이상이 된 프레임 (그리퍼 열기)
  k_opened = k_open 뒤 팔로워 그리퍼가 처음으로 (k_open … k_close 최대값의 90 %) 이상이 된 프레임 (그리퍼 다 열림)
  k_reach = k_open … k_close 사이에서 팔 관절 (pan · lift · elbow · wflex) 속도가 마지막으로 15 °/s 를 넘은 다음 프레임 (팔 접근이 거의 멈춤)
  k_grasp = k_close 뒤 1.5 s 안에서 팔로워 그리퍼가 바닥 (최소 + 0.5) 에 처음 닿은 프레임 · 바닥 ≥ 8 = 쥠 (r2_common GRIP_HOLD_MIN)
  k_done  = 판 마지막 프레임 (쉬는 자세)
"""

import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import r12_common as rc  # noqa: E402

REF_DIR = os.path.join(rc.ROOT, "reference")
INDEX = os.path.join(REF_DIR, "d2_ref_index.json")
TRAJ = os.path.join(REF_DIR, "d2_ref_traj.npz")
FRAMES = os.path.join(REF_DIR, "frames")
D2_DS = os.path.expanduser("~/so101_runs/main_k8/d2/dataset")
A04 = os.path.expanduser("~/so101_runs/main_k8/d2/data_coverage_audit/tables/a04_cube_positions.csv")
R2_SCRIPTS = os.path.expanduser("~/so101_runs/main_k8/r2_grasp_diagnostic/scripts")
GB_DIR = os.path.expanduser("~/so101_runs/main_k8/d2/diag_grasp_bias")
KEYS = [("k_open", "열기 시작"), ("k_opened", "다 열림"), ("k_reach", "접근 멈춤"), ("k_close", "닫기 시작"),
        ("k_grasp", "파지"), ("k_done", "작업 완료")]
KEY_KO = dict(KEYS)
HOLD_MIN, EMPTY_MAX = 8.0, 5.0      # r2_common GRIP_HOLD_MIN · GRIP_EMPTY_MAX (닫힌 뒤 팔로워 바닥: ≥ 8 쥠, ≤ 5 빈 닫힘)
OPEN_MIN = 15.0
REACH_SPEED = 15.0                  # °/s
THUMB = (320, 240)


# ================================================================ 색인 만들기 (오프라인)
def keyframes(S, A, close_onsets, fps=30):
    """d2 한 판 → {key: frame} 와 그리퍼 바닥. 닫힘이 없으면 None."""
    ev = close_onsets(A[:, 5])
    if not ev:
        return None
    k2 = int(ev[0][0])
    g = A[: k2 + 1, 5]
    up = np.where((g[:-1] < OPEN_MIN) & (g[1:] >= OPEN_MIN))[0]
    k_open = int(up[-1] + 1) if len(up) else 0
    sp = np.abs(np.diff(S[:, :4], axis=0)).max(axis=1) * fps
    fast = [j for j in range(k_open, k2) if sp[j] > REACH_SPEED]
    k_reach = min(k2, fast[-1] + 1) if fast else k_open
    seg = S[k_open: k2 + 1, 5]
    k_opened = k_open + int(np.argmax(seg >= 0.9 * seg.max())) if len(seg) else k_open
    win = S[k2: min(len(S), k2 + int(1.5 * fps)), 5]
    bottom = float(win.min())
    k_grasp = k2 + int(np.argmax(win <= bottom + 0.5))
    return {"k_open": k_open, "k_opened": int(k_opened), "k_reach": int(max(k_reach, k_opened)), "k_close": k2, "k_grasp": int(k_grasp), "k_done": len(S) - 1}, bottom


def build(argv=None):
    import csv

    import cv2

    sys.path.insert(0, R2_SCRIPTS)
    sys.path.insert(0, GB_DIR)
    sys.path.insert(0, os.path.join(rc.HOME, "so101_boxpick", "scripts"))
    import common as GB  # diag_grasp_bias (읽기만)
    import r2_common as R2C

    cfg = rc.load_config()
    pos = {int(r["ep"]): r for r in csv.DictReader(open(A04))}
    data = GB.load_parquet(D2_DS)
    os.makedirs(FRAMES, exist_ok=True)
    cache, index, traj = {}, [], {}
    t0 = __import__("time").time()
    for e in sorted(data):
        S, A = data[e]
        kf = keyframes(S, A, R2C.close_onsets)
        if kf is None:
            continue
        ks, bottom = kf
        p = pos.get(e, {})
        ent = {"ep": e, "group": p.get("group", ""), "cube_x": float(p["cube_x"]), "cube_y": float(p["cube_y"]),
               "yaw_code": p.get("yaw_plan_code", ""), "yaw_meas": p.get("yaw_meas", ""), "n": len(S), "fps": 30,
               "grasp_bottom": round(bottom, 1), "grasped": bottom >= HOLD_MIN,
               "open_lead_s": round((ks["k_close"] - ks["k_open"]) / 30, 2), "keys": {}}
        for k, f in ks.items():
            imgs = {cam: GB.frames(D2_DS, e, cam, f, f, cache)[0] for cam in rc.CAMS}
            vis = rc.vision(imgs["front"], imgs["wrist"], cfg)
            w = vis["wrist"]
            files = {}
            for cam, im in imgs.items():
                fn = f"ep{e:03d}_{k}_{cam}.jpg"
                cv2.imwrite(os.path.join(FRAMES, fn), cv2.cvtColor(cv2.resize(im, THUMB, interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2BGR),
                            [cv2.IMWRITE_JPEG_QUALITY, 85])
                files[cam] = fn
            ent["keys"][k] = {"frame": int(f), "t_rel_close_s": round((f - ks["k_close"]) / 30, 2),
                              "state": [round(float(x), 1) for x in S[f]], "grip_cmd": round(float(A[f, 5]), 1),
                              "wrist": ({"u": round((w["dx"] + 1) / 2, 3), "v": round((w["dy"] + 1) / 2, 3), "area": w["area_px"],
                                         "edge": bool(w.get("touches_edge")), "bbox": w["bbox"]} if w.get("detected") else None),
                              "files": files}
        a, b = max(0, ks["k_open"] - 30), min(len(S), ks["k_grasp"] + 60)
        sl = slice(a, b, 3)
        traj[f"ep{e:03d}"] = np.column_stack([(np.arange(len(S))[sl] - ks["k_close"]) / 30.0, S[sl, :6], A[sl, 5]]).astype(np.float32)
        index.append(ent)
        if e % 32 == 0:
            print(f"  ep {e} … {__import__('time').time() - t0:.0f}s", flush=True)
    meta = {"source": D2_DS, "positions": A04, "n": len(index), "keys": KEYS, "traj_cols": ["t_rel_close_s", *rc.JOINTS, "grip_cmd"],
            "rules": __doc__.split("키프레임 정의")[1].strip(), "built": __import__("datetime").datetime.now().isoformat(timespec="seconds")}
    rc.write_json(INDEX, {"meta": meta, "episodes": index})
    np.savez_compressed(TRAJ, **traj)
    print(f"참고 색인 {len(index)}편 → {INDEX} ({__import__('time').time() - t0:.0f}s)")
    return 0


# ================================================================ 참고 시연 고르기
_IDX = {}


def load_index():
    if "idx" not in _IDX:
        d = rc.read_json(INDEX)
        _IDX["idx"] = d
        try:
            _IDX["traj"] = np.load(TRAJ)
        except OSError:
            _IDX["traj"] = None
    return _IDX["idx"]


def ref_traj(ep):
    load_index()
    t = _IDX.get("traj")
    return None if t is None or f"ep{ep:03d}" not in t.files else t[f"ep{ep:03d}"]


def match_quality(dist_cm, angle_same):
    """참고 시연 일치 정도 (불확실성 표시). 근거: 큐브 자리 · 각도 코드만 비교 — 접근 자세 · roll 은 비교하지 않음."""
    if dist_cm <= 2.0 and angle_same:
        return "high", "높음 (자리 2 cm 안 · 같은 각도)"
    if dist_cm <= 4.0:
        return "medium", f"보통 (자리 {dist_cm:.1f} cm" + (" · 같은 각도)" if angle_same else " · 각도 다름)")
    return "low", f"낮음 (가장 가까운 성공 시연이 {dist_cm:.1f} cm 떨어짐 — 참고만)"


def select_refs(xy, angle_code, n=5):
    """큐브 탁자 좌표 (cm) · 각도 코드 (0 · L30 · R30 · 45) → 가까운 d2 성공 시연 후보 n 개 (점수 = 거리 + 각도 다르면 3 cm)."""
    idx = load_index()
    if not idx:
        return []
    out = []
    for e in idx["episodes"]:
        if not e.get("grasped"):
            continue
        d = math.hypot(e["cube_x"] - xy[0], e["cube_y"] - xy[1])
        same = str(e.get("yaw_code")) == str(angle_code)
        q, qt = match_quality(d, same)
        out.append({"ep": e["ep"], "dist_cm": round(d, 2), "angle_same": same, "score": d + (0 if same else 3.0), "quality": q,
                    "quality_text": qt, "entry": e})
    out.sort(key=lambda r: r["score"])
    return out[:n]


def ref_image_path(entry, key, cam):
    f = ((entry.get("keys") or {}).get(key) or {}).get("files", {}).get(cam)
    return os.path.join(FRAMES, f) if f else None


# ================================================================ 단계 (설정 guide_stages)
def stages_of(cfg, sid):
    return list((cfg["scenarios"].get(sid) or {}).get("guide_stages") or [])


def auto_stage(stages, phase, hist, vis):
    """자동 단계 추정 (보조). stages = guide_stages · phase = 수집 UI 상태 · hist = 이번 녹화의 [(grip_cmd, grip_state, pan, lift)] ·
    vis = 손목 검출. 반환 (단계 index, 근거 글). R2-P 규칙 (stage key: start · approach · preclose · close · done)."""
    keys = [s["key"] for s in stages]

    def at(k, why):
        return (keys.index(k) if k in keys else 0), why

    if phase in ("SETUP", "WAIT", "START", "ARMED", "BLOCK"):
        return at("start", "준비 단계")
    if phase in ("RESET", "SAVING", "FINAL", "DONE"):
        return at("done", "녹화 끝")
    if not hist:
        return at("start", "녹화 시작")
    H = np.asarray(hist, float)
    ev = rc.close_events(H[:, 0])
    win = 15  # 닫힘 뒤 약 1.5 s (화면 갱신 ~10 Hz 표본)
    bottoms = [float(H[k: k + win, 1].min()) for k, _, _ in ev]
    hold = next((i for i, b in enumerate(bottoms) if b >= HOLD_MIN), None)
    if hold is not None:  # 파지됨 → 그 뒤 팔이 많이 움직였으면 작업 완료 단계
        k = ev[hold][0]
        moved = max(abs(H[-1, 2] - H[k, 2]), abs(H[-1, 3] - H[k, 3]))
        return at("done", f"파지 뒤 팔 이동 {moved:.0f}°") if moved > 15 else at("close", f"파지 (팔로워 그리퍼 {bottoms[hold]:.0f})")
    if ev:
        if bottoms[-1] <= EMPTY_MAX:
            return at("approach", "빈 파지 의심 (팔로워 바닥 ≤ 5) — 다시 열고 정렬") if H[-1, 0] >= OPEN_MIN else \
                at("close", "닫힘 · 빈 파지 의심 (팔로워 바닥 ≤ 5)")
        return at("close", "닫는 중")
    rel = rc.wrist_relation((vis or {}).get("wrist"))
    if rel == "in_zone":
        return at("preclose", "손목 큐브가 닫기 영역 안 (2D 참고)")
    moved = max(np.abs(H[:, 2:4] - H[0, 2:4]).max(), 0)
    return at("approach", f"팔 이동 {moved:.0f}°") if moved > 2 else at("start", "녹화 시작 · 아직 정지")


# ================================================================ 녹화 뒤 검토 표시 (자동 · 보조)
def review_episode(grip_cmd, grip_state, thumbs_wrist=None, cfg=None, fps=30, every=10):
    """방금 녹화한 판의 그리퍼 명령 · 팔로워 그리퍼 열 → 검토 표시 [(level, code, 글)]. level 'warn' = 사람 확인 필요.
    첫 닫힘 뒤 1.5 s 안 팔로워 바닥 ≤ 5 = 빈 파지 의심 · 5–8 = 확인 필요 (r2_common 규칙). 파지 전 닫힘 횟수.
    thumbs_wrist (every 프레임마다 축소 손목 영상) 가 있으면 첫 닫힘 때 큐브가 화면 경계에서 잘렸는지."""
    out = []
    g, s = np.asarray(grip_cmd, float), np.asarray(grip_state, float)
    n = min(len(g), len(s))
    if n < 3:
        return out
    g, s = g[:n], s[:n]
    ev = rc.close_events(g)
    if not ev:
        out.append(("info", "no_close", "녹화 중 그리퍼 닫힘 없음"))
        return out
    first_hold = None
    for i, (k, peak, _) in enumerate(ev):
        b = float(s[k: min(n, k + int(1.5 * fps))].min())
        if b >= HOLD_MIN:
            first_hold = i
            break
    k0 = ev[0][0]
    b0 = float(s[k0: min(n, k0 + int(1.5 * fps))].min())
    if b0 <= EMPTY_MAX:
        out.append(("warn", "empty_first_close", f"첫 닫힘 빈 파지 의심 @ {k0 / fps:.1f}s (팔로워 그리퍼 바닥 {b0:.1f} ≤ {EMPTY_MAX:g})"))
    elif b0 < HOLD_MIN:
        out.append(("warn", "uncertain_first_close", f"첫 닫힘 확인 필요 @ {k0 / fps:.1f}s (팔로워 바닥 {b0:.1f}, 5–8)"))
    nb = first_hold if first_hold is not None else len(ev)
    if nb >= 1:
        out.append(("warn", "closes_before_grasp", f"파지 전에 실패한 닫힘 {nb}번" + ("" if first_hold is not None else " (파지 확인 안 됨)")))
    if thumbs_wrist is not None and len(thumbs_wrist):
        j = min(len(thumbs_wrist) - 1, int(round(k0 / every)))
        im = np.asarray(thumbs_wrist[j])
        b = rc.find_red(im, cfg, min_area=10, open_px=1) if cfg else None
        if b:
            _, cx, cy, (x, y, bw, bh) = b[0]
            h, w = im.shape[:2]
            sides = [nm for nm, c in (("위", y <= 1), ("아래", y + bh >= h - 1), ("왼쪽", x <= 1), ("오른쪽", x + bw >= w - 1)) if c]
            if sides:
                out.append(("warn", "cut_at_first_close", f"첫 닫힘 때 큐브가 손목 화면 {'·'.join(sides)} 경계에서 잘림"))
        else:
            out.append(("info", "not_visible_at_first_close", "첫 닫힘 때 손목 화면 큐브 검출 안 됨"))
    return out


def main():
    a = sys.argv[1:]
    if a and a[0] == "build":
        return build(a[1:])
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
