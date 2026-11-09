#!/home/user/so101-env/bin/python
"""SG50 수집 — 손목 영상에서 빨간 큐브와 그 위 흰 스티커 위치 찾기 (영상 처리만, 학습 모델 없음).

원칙
  - 입력 영상(RGB uint8)은 읽기만 한다. 표시는 화면용 복사본에만 그린다 (sg_viewer.py). 이 모듈은 그리지 않는다.
  - 프레임마다 따로 판단한다. 이전 프레임 위치를 이어 붙이거나 '마지막 위치'를 현재처럼 돌려주지 않는다.
  - 흰 탁자 · 반투명 흰 손가락 끝 · 반사를 스티커로 잡지 않도록, 후보는 빨간 큐브 볼록 껍질 안의 흰 덩어리로 제한하고
    (1) 둘레가 빨강으로 둘러싸였는지 (2) 같은 흰 덩어리가 껍질 밖 흰 영역 (탁자 · 손가락) 과 이어졌는지 (3) 크기 · 모양을 본다.
  - 결과 status: detected (하나) · uncertain (후보가 모호 · 잘림 · 바깥과 이어짐) · none (큐브는 있으나 스티커 후보 없음) · no_cube.

좌표
  - px: 원본 손목 영상 픽셀 (640×480), 원점 = 왼쪽 위, x 오른쪽 · y 아래.
  - u, v: px 를 영상 폭 · 높이로 나눈 값 (0–1), 같은 원점 (r12 의 wrist u/v 와 같은 정의).
  - 손목 화면에서 로봇 좌우 빗김은 주로 v (위·아래) 로 보인다 (r12 12_recovery_usage.md §6, 2026-11-04 확인).

CLI
  sg_sticker.py image  PNG [PNG ...] [--out DIR]                 # 이미지 파일 검출 → JSON (+ --out 이면 표시 복사본 PNG)
  sg_sticker.py annotate --session S [--episodes 0,1] [--force]  # 녹화 dataset 손목 영상 → <세션>/sg_sticker/ep###.csv (dataset 은 읽기만)
  sg_sticker.py set-ref --session S --episode N --t SEC [--kind point|box] [--note "..."]   # 예비 시연 장면 → 참조 (새 버전, 덮어쓰지 않음)
  sg_sticker.py set-ref --uv U,V [--kind point|box] --note "..."  # 손으로 참조점
  sg_sticker.py refs                                              # 참조 버전 목록 · 활성
  sg_sticker.py set-ref --image WRIST.png --name 닫힘 [--add] [--kind point|box]   # 저장한 손목 원본 이미지 → 참조 (--add = 지금 활성에 더함)
  sg_sticker.py use-ref ref-v2 | ref-v1,ref-v2 | none            # 활성 참조 바꾸기 (여러 개 가능, none = 표시 안 함)
"""

import hashlib
import json
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DETECT_VERSION = "sticker-v1"
PARAMS_PATH = os.environ.get("SG_STICKER_PARAMS") or os.path.join(ROOT, "config", "sg_sticker.json")  # 시험 때만 env 로 바꿈
REF_PATH = os.environ.get("SG_STICKER_REF") or os.path.join(ROOT, "config", "sg_sticker_ref.json")
HOME = os.path.expanduser("~")

# 기본값 — config/sg_sticker.json 이 있으면 그 값으로 덮어씀 (버전 · sha256 을 결과에 남김)
DEFAULTS = {
    # 빨강: redbox8_layouts.yaml detection.colors.red 와 같은 범위 (front 기준으로 정한 값; 손목 실측 범위는 doc 13 §3)
    "red_hsv": [{"h": [160, 180], "s": [90, 255], "v": [60, 255]}, {"h": [0, 1], "s": [90, 255], "v": [60, 255]}],
    "cube_min_area_px": 800,      # 이보다 작은 빨강 = 큐브 없음 (손목 근접 큐브는 수천 px²)
    "merge_gap_px": 30,           # 손가락이 큐브를 가로질러 둘로 나뉜 빨강 덩어리를 합치는 거리
    "merge_min_frac": 0.10,       # 합칠 덩어리의 최소 크기 (가장 큰 것 대비)
    "white_s_max": 60,            # 흰색 = 채도 ≤ 이 값 · 밝기 ≥ white_v_min
    "white_v_min": 150,
    "hull_erode_px": 2,           # 큐브 윤곽 바로 안쪽 경계 번짐 제외
    "min_area_px": 30,
    "min_area_frac": 0.004,       # 스티커 넓이 / 큐브 껍질 넓이
    "max_area_frac": 0.40,
    "min_solidity": 0.70,         # 반사 줄무늬 · 찢긴 모양 제외
    "min_circularity": 0.0,       # 4π·넓이/둘레² (원 = 1). 0 = 안 봄. 둥근 스티커면 config/sg_sticker.json 에서 올림
    "ring_px": 5,                 # 둘레 띠 두께
    "ring_red_min": 0.40,         # 둘레 띠 중 빨강 비율 (껍질 밖 띠는 빨강 아님으로 셈)
    "ring_in_reject": 0.60,       # 둘레 띠 중 큐브 껍질 안 비율 — 이보다 작으면 큐브 윤곽에 걸친 흰 조각 (손가락 끝 · 탁자) → 뺌
    "ring_in_min": 0.90,          # 이보다 작으면 (뺄 정도는 아님) 불확실
    "outside_frac_max": 0.15,     # 같은 흰 덩어리 중 껍질 밖 비율 — 넘으면 탁자 · 손가락과 이어진 것
    "outside_frac_reject": 0.50,  # 이 이상이면 후보에서 뺌 (사이 = 불확실)
    "ambiguity_ratio": 0.60,      # 둘째 후보 점수 / 첫째 ≥ 이 값 → 불확실
    "edge_margin_px": 3,          # 영상 가장자리에 닿으면 잘렸을 수 있음 → 불확실
}

STATUS_KO = {"detected": "검출", "uncertain": "불확실", "none": "미검출", "no_cube": "큐브 없음"}


def load_params(path=""):
    path = PARAMS_PATH if path == "" else path  # None = 기본값만 (설정 파일 무시)
    p = dict(DEFAULTS)
    sha = "defaults"
    if path and os.path.exists(path):
        with open(path, "rb") as f:
            raw = f.read()
        sha = hashlib.sha256(raw).hexdigest()[:12]
        user = json.loads(raw)
        p.update({k: v for k, v in user.items() if not k.startswith("_")})
    p["_sha"] = sha
    p["_version"] = f"{DETECT_VERSION}+{sha}"
    return p


def _hsv_mask(hsv, ranges):
    import cv2

    m = np.zeros(hsv.shape[:2], np.uint8)
    for r in ranges:
        m |= cv2.inRange(hsv, np.array([r["h"][0], r["s"][0], r["v"][0]], np.uint8),
                         np.array([r["h"][1], r["s"][1], r["v"][1]], np.uint8))
    return m


def _cube_mask(red, P):
    """빨강 마스크 → 큐브 덩어리 (가장 큰 것 + 가까운 큰 조각) 마스크, 점들. 없으면 (None, None)."""
    import cv2

    n, lab, st, _ = cv2.connectedComponentsWithStats(red)
    if n <= 1:
        return None, None
    order = sorted(range(1, n), key=lambda i: -st[i, 4])
    big = order[0]
    if st[big, 4] < P["cube_min_area_px"]:
        return None, None
    x, y, w, h = st[big, :4]
    keep = [big]
    g = P["merge_gap_px"]
    for i in order[1:]:
        if st[i, 4] < P["merge_min_frac"] * st[big, 4]:
            break
        xi, yi, wi, hi = st[i, :4]
        gap = max(0, max(xi - (x + w), x - (xi + wi))), max(0, max(yi - (y + h), y - (yi + hi)))
        if max(gap) <= g:
            keep.append(i)
    m = np.isin(lab, keep).astype(np.uint8)
    return m, len(keep)


def detect(img_rgb, P=None):
    """RGB uint8 (H×W×3) → 결과 dict. img_rgb 는 바꾸지 않는다."""
    import cv2

    P = P or load_params()
    t0 = time.perf_counter()
    H, W = img_rgb.shape[:2]
    out = {"version": P["_version"], "img_size": [W, H], "status": "no_cube", "reason": "", "cube": None, "sticker": None,
           "candidates": []}
    hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
    red = _hsv_mask(hsv, P["red_hsv"])
    red = cv2.morphologyEx(red, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    cube, nparts = _cube_mask(red, P)
    if cube is None:
        out["reason"] = "빨간 큐브 안 보임 (또는 너무 작음)"
        out["ms"] = round((time.perf_counter() - t0) * 1000, 2)
        return out
    pts = cv2.findNonZero(cube)
    hull = cv2.convexHull(pts)
    hull_m = np.zeros((H, W), np.uint8)
    cv2.fillConvexPoly(hull_m, hull, 1)
    hull_area = int(hull_m.sum())
    M = cv2.moments(cube, binaryImage=True)
    ccx, ccy = M["m10"] / M["m00"], M["m01"] / M["m00"]
    bx, by, bw, bh = cv2.boundingRect(pts)
    em = P["edge_margin_px"]
    cube_edge = bool(bx <= em or by <= em or bx + bw >= W - em or by + bh >= H - em)
    out["cube"] = {"px": [round(ccx, 1), round(ccy, 1)], "u": round(ccx / W, 4), "v": round(ccy / H, 4), "area_px": int(cube.sum()),
                   "hull_area_px": hull_area, "bbox": [int(bx), int(by), int(bw), int(bh)], "parts": nparts,
                   "touches_edge": cube_edge, "hull": hull.reshape(-1, 2).tolist()}

    white = ((hsv[..., 1] <= P["white_s_max"]) & (hsv[..., 2] >= P["white_v_min"])).astype(np.uint8)
    e = P["hull_erode_px"]
    inner = cv2.erode(hull_m, np.ones((2 * e + 1, 2 * e + 1), np.uint8)) if e > 0 else hull_m
    cand = white & inner
    n, lab, st, cen = cv2.connectedComponentsWithStats(cand)
    # 같은 흰 덩어리가 껍질 밖으로 이어지는지: 영상 전체 흰 마스크의 덩어리 번호로 봄
    nw, wlab, wst, _ = cv2.connectedComponentsWithStats(white)
    rk = P["ring_px"]
    kern = np.ones((2 * rk + 1, 2 * rk + 1), np.uint8)
    cands = []
    for i in range(1, n):
        area = int(st[i, 4])
        if area < P["min_area_px"]:
            continue
        x, y, w, h = (int(v) for v in st[i, :4])
        comp = (lab == i).astype(np.uint8)
        frac = area / max(hull_area, 1)
        cnts, _ = cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnt = max(cnts, key=cv2.contourArea)
        ha = cv2.contourArea(cv2.convexHull(cnt))
        solidity = float(area / ha) if ha > 0 else 0.0
        per = cv2.arcLength(cnt, True)
        circ = float(4 * math.pi * cv2.contourArea(cnt) / per ** 2) if per > 0 else 0.0
        hper = cv2.arcLength(cv2.convexHull(cnt), True)  # 껍질 둥근 정도 — 경계가 들쭉날쭉해도 (흐림 · 비스듬) 원이면 높음, 가는 조각은 낮음
        hcirc = float(4 * math.pi * ha / hper ** 2) if hper > 0 else 0.0
        ring = (cv2.dilate(comp, kern) & (1 - comp)).astype(bool)
        ring_red = float(red[ring].astype(bool).mean()) if ring.any() else 0.0
        ring_in = float(hull_m[ring].astype(bool).mean()) if ring.any() else 0.0
        wid = np.unique(wlab[comp.astype(bool)])
        wid = wid[wid > 0]
        wsum = int(wst[wid, 4].sum()) if len(wid) else area
        wout = int(((np.isin(wlab, wid)) & (hull_m == 0)).sum()) if len(wid) else 0
        outside = wout / max(wsum, 1)
        at_edge = bool(x <= em or y <= em or x + w >= W - em or y + h >= H - em)
        rej = []
        if frac < P["min_area_frac"]:
            rej.append("작음")
        if frac > P["max_area_frac"]:
            rej.append("큼")
        if solidity < P["min_solidity"]:
            rej.append("모양")
        if (hcirc < P["min_hull_circularity"]) if P.get("min_hull_circularity") else (circ < P.get("min_circularity", 0.0)):
            rej.append("둥글지 않음")
        if ring_red < P["ring_red_min"]:
            rej.append("둘레 빨강 부족")
        if ring_in < P["ring_in_reject"]:
            rej.append("큐브 윤곽에 걸침")
        if outside >= P["outside_frac_reject"]:
            rej.append("바깥 흰 영역과 이어짐")
        score = (min(frac / 0.03, 1.0) * solidity * ring_red * (1 - min(outside, 1.0))) if not rej else 0.0
        cands.append({"px": [round(float(cen[i][0]), 1), round(float(cen[i][1]), 1)], "area_px": area, "area_frac": round(frac, 4),
                      "bbox": [x, y, w, h], "solidity": round(solidity, 3), "circularity": round(circ, 3), "hull_circularity": round(hcirc, 3), "ring_red": round(ring_red, 3), "ring_in": round(ring_in, 3),
                      "outside_frac": round(outside, 3), "at_edge": at_edge, "score": round(score, 4), "reject": rej,
                      "contour": cnt.reshape(-1, 2).tolist()})
    cands.sort(key=lambda c: -c["score"])
    out["candidates"] = cands
    ok = [c for c in cands if not c["reject"]]
    if not ok:
        out["status"] = "none"
        out["reason"] = "큐브 안 흰 후보 없음" if not cands else "후보 모두 제외 (" + ", ".join(sorted({r for c in cands for r in c["reject"]})) + ")"
    else:
        best = ok[0]
        why = []
        if len(ok) > 1 and ok[1]["score"] >= P["ambiguity_ratio"] * best["score"]:
            why.append(f"후보 {len(ok)}개 비슷함")
        if best["at_edge"]:
            why.append("영상 가장자리 (잘렸을 수 있음)")
        if best["ring_in"] < P["ring_in_min"]:
            why.append(f"큐브 윤곽 가까이 ({best['ring_in']:.0%} 둘러싸임)")
        if best["outside_frac"] > P["outside_frac_max"]:
            why.append(f"바깥 흰 영역과 일부 이어짐 ({best['outside_frac']:.0%})")
        out["status"] = "uncertain" if why else "detected"
        out["reason"] = " · ".join(why)
        x, y = best["px"]
        out["sticker"] = {"px": [x, y], "u": round(x / W, 4), "v": round(y / H, 4), "area_px": best["area_px"],
                          "bbox": best["bbox"], "contour": best["contour"],
                          # 큐브 껍질 상자 안 상대 위치 (0–1, 왼쪽 위 원점) — 스티커가 큐브의 어느 쪽에 보이는지
                          "in_cube": [round((x - bx) / max(bw, 1), 3), round((y - by) / max(bh, 1), 3)]}
    out["ms"] = round((time.perf_counter() - t0) * 1000, 2)
    return out


# ---------------------------------------------------------------- 참조 (정렬 참고 — 자동 판정 아님)

def read_refs(path=None):
    path = path or REF_PATH
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"active": None, "refs": {}}


def active_refs(path=None):
    """활성 참조 목록 (active = 버전 하나 또는 목록 — 예: 닫힘 · 열림 두 개)."""
    d = read_refs(path)
    a = d.get("active")
    a = [a] if isinstance(a, str) else (a or [])
    return [{"version": v, **d["refs"][v]} for v in a if v in d.get("refs", {})]


def active_ref(path=None):
    r = active_refs(path)
    return r[0] if r else None


def _write_refs(d, path=None):
    path = path or REF_PATH
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def add_ref(entry, path=None, activate=True):
    path = path or REF_PATH
    d = read_refs(path)
    refs = d.setdefault("refs", {})
    n = 1 + max([int(k.split("-v")[-1]) for k in refs if k.startswith("ref-v")] or [0])
    ver = f"ref-v{n}"
    refs[ver] = {**entry, "created": time.strftime("%Y-%m-%d %H:%M:%S")}
    if activate == "add":  # 지금 활성 목록에 더함
        cur = d.get("active")
        cur = [cur] if isinstance(cur, str) else list(cur or [])
        d["active"] = cur + [ver]
    elif activate:
        d["active"] = ver
    _write_refs(d, path)
    return ver


def cube_angle(hull_px):
    """큐브 윤곽 (px 점들) 의 화면 기울기 ° — 최소 사각형 변 각도를 [−45, 45) 로 접음 (정사각 큐브는 90° 마다 같음).
    화면 좌표 (y 아래) 기준이라 값이 커지면 화면에서 시계 방향."""
    import cv2

    (_, _), (_, _), a = cv2.minAreaRect(np.array(hull_px, np.float32))
    return ((a + 45.0) % 90.0) - 45.0


def target_compare(det, ref):
    """지금 큐브 ↔ 닫기 자리 목표 (kind target). 판정 아님 — 화면 안내용.
    반환: du, dv (지금 − 목표, 0–1), size (√넓이 비, 1 = 같음), dangle (목표 − 지금 °, + = 화면 시계 방향으로 돌려야 함), ok{u,v,size,angle}, all."""
    if not ref or not det or not det.get("cube") or not det["cube"].get("hull"):
        return None
    c = det["cube"]
    tol = ref.get("tol") or {}
    du, dv = c["u"] - ref["u"], c["v"] - ref["v"]
    size = math.sqrt(c["area_px"] / max(ref["area_px"], 1))
    dang = ((ref["angle"] - cube_angle(c["hull"]) + 45.0) % 90.0) - 45.0
    ok = {"u": abs(du) <= tol.get("u", 0.02), "v": abs(dv) <= tol.get("v", 0.02), "size": abs(size - 1) <= tol.get("size", 0.05),
          "angle": abs(dang) <= tol.get("angle", 3.0)}
    return {"du": round(du, 3), "dv": round(dv, 3), "size": round(size, 3), "dangle": round(dang, 1), "ok": ok, "all": all(ok.values()),
            "edge": bool(c.get("touches_edge"))}


def ref_compare(det, ref):
    """현재 검출 ↔ 참조 (표시용 글). 판정 없음. 반환 dict: du, dv (u·v 차이), inside (영역 안?), size_ratio (큐브 넓이 비)."""
    if ref and ref.get("kind") == "target":
        t = target_compare(det, ref)
        return None if t is None else {"du": t["du"], "dv": t["dv"], "inside": t["all"], "size_ratio": round(t["size"] ** 2, 2), "dangle": t["dangle"]}
    if ref and ref.get("kind") == "cross":  # 큐브 중심 십자 (주황 점선): 큐브 중심 ↔ 십자 교점
        if not det or not det.get("cube"):
            return None
        c = det["cube"]
        du, dv = c["u"] - ref["u"], c["v"] - ref["v"]
        inside = abs(du) <= ref.get("half_u", 0.03) and abs(dv) <= ref.get("half_v", 0.03)
        ratio = round(c["area_px"] / ref["cube_area_px"], 2) if ref.get("cube_area_px") else None
        return {"du": round(du, 3), "dv": round(dv, 3), "inside": bool(inside), "size_ratio": ratio}
    if not ref or not det or det.get("status") not in ("detected", "uncertain") or not det.get("sticker"):
        return None
    s = det["sticker"]
    du, dv = s["u"] - ref["u"], s["v"] - ref["v"]
    if ref.get("kind") == "box":
        inside = abs(du) <= ref["half_u"] and abs(dv) <= ref["half_v"]
    else:
        inside = math.hypot(du, dv * det["img_size"][1] / det["img_size"][0]) <= ref.get("r", 0.04)
    ratio = None
    if ref.get("cube_area_px") and det.get("cube"):
        ratio = round(det["cube"]["area_px"] / ref["cube_area_px"], 2)
    return {"du": round(du, 3), "dv": round(dv, 3), "inside": bool(inside), "size_ratio": ratio}


# ---------------------------------------------------------------- dataset 읽기 (읽기만)

def _episodes(sess_dir):
    import glob

    import pandas as pd

    fs = sorted(glob.glob(os.path.join(sess_dir, "dataset", "meta", "episodes", "*", "*.parquet")))
    if not fs:
        raise SystemExit(f"dataset meta/episodes 가 없어요: {sess_dir}/dataset")
    return pd.concat([pd.read_parquet(f) for f in fs]).sort_values("episode_index")


def wrist_frames(sess_dir, episode):
    """(frame_index, timestamp, rgb) — 녹화 dataset 손목 영상에서 한 판. 영상 파일은 읽기만."""
    import av

    df = _episodes(sess_dir)
    r = df[df.episode_index == episode]
    if r.empty:
        raise SystemExit(f"episode {episode} 없음")
    r = r.iloc[0]
    k = "videos/observation.images.wrist"
    path = os.path.join(sess_dir, "dataset", k, f"chunk-{int(r[f'{k}/chunk_index']):03d}", f"file-{int(r[f'{k}/file_index']):03d}.mp4")
    t0, t1 = float(r[f"{k}/from_timestamp"]), float(r[f"{k}/to_timestamp"])
    with open(os.path.join(sess_dir, "dataset", "meta", "info.json")) as f:
        fps = json.load(f)["fps"]
    n = int(r["length"])
    c = av.open(path)
    try:
        s = c.streams.video[0]
        c.seek(max(0, int((t0 - 1.0) / float(s.time_base))), stream=s, backward=True)
        for fr in c.decode(s):
            ts = float(fr.pts * s.time_base)
            if ts < t0 - 0.5 / fps:
                continue
            if ts >= t1 - 0.5 / fps:
                break
            fi = int(round((ts - t0) * fps))
            if 0 <= fi < n:
                yield fi, round(fi / fps, 4), fr.to_ndarray(format="rgb24")
    finally:
        c.close()


def episode_states(sess_dir, episode):
    import glob

    import pandas as pd

    fs = sorted(glob.glob(os.path.join(sess_dir, "dataset", "data", "*", "*.parquet")))
    d = pd.concat([pd.read_parquet(f, columns=["observation.state", "frame_index", "episode_index"]) for f in fs])
    d = d[d.episode_index == episode].sort_values("frame_index")
    return {int(fi): [float(x) for x in s] for fi, s in zip(d.frame_index, d["observation.state"])}


ANNOT_FIELDS = ["episode_index", "frame_index", "timestamp", "status", "reason", "sticker_u", "sticker_v", "sticker_px_x", "sticker_px_y",
                "sticker_area_px", "cube_u", "cube_v", "cube_area_px", "cube_touches_edge", "n_candidates", "n_accepted",
                "ref_version", "ref_du", "ref_dv", "ref_inside", "ref_size_ratio", "detect_version", "params_sha"]


def cmd_annotate(argv):
    import csv

    sys.path.insert(0, HERE)
    import r12_common as rc

    sess = argv[argv.index("--session") + 1]
    sess_dir = rc.session_dir(sess)
    P = load_params()
    ref = active_ref()
    df = _episodes(sess_dir)
    eps = [int(e) for e in argv[argv.index("--episodes") + 1].split(",")] if "--episodes" in argv else list(df.episode_index)
    od = os.path.join(sess_dir, "sg_sticker")
    os.makedirs(od, exist_ok=True)
    summ = {"session": sess, "detect_version": P["_version"], "params": {k: v for k, v in P.items() if not k.startswith("_")},
            "ref": ref, "created": time.strftime("%Y-%m-%d %H:%M:%S"), "episodes": {},
            "coords": "u,v = 원본 손목 영상 640×480 픽셀 / 폭·높이 (0–1), 원점 왼쪽 위. dataset 은 읽기만 함."}
    for e in eps:
        path = os.path.join(od, f"ep{e:03d}.csv")
        if os.path.exists(path) and "--force" not in argv:
            print(f"  ep{e}: 이미 있음 (--force 로 다시)")
            continue
        cnt = {}
        n = 0
        tmp = path + ".tmp"
        with open(tmp, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=ANNOT_FIELDS)
            w.writeheader()
            for fi, ts, img in wrist_frames(sess_dir, e):
                d = detect(img, P)
                cmp_ = ref_compare(d, ref) or {}
                s, c = d.get("sticker") or {}, d.get("cube") or {}
                w.writerow({"episode_index": e, "frame_index": fi, "timestamp": ts, "status": d["status"], "reason": d["reason"],
                            "sticker_u": s.get("u", ""), "sticker_v": s.get("v", ""),
                            "sticker_px_x": (s.get("px") or ["", ""])[0], "sticker_px_y": (s.get("px") or ["", ""])[1],
                            "sticker_area_px": s.get("area_px", ""), "cube_u": c.get("u", ""), "cube_v": c.get("v", ""),
                            "cube_area_px": c.get("area_px", ""), "cube_touches_edge": c.get("touches_edge", ""),
                            "n_candidates": len(d["candidates"]), "n_accepted": sum(not x["reject"] for x in d["candidates"]),
                            "ref_version": ref["version"] if ref else "", "ref_du": cmp_.get("du", ""), "ref_dv": cmp_.get("dv", ""),
                            "ref_inside": cmp_.get("inside", ""), "ref_size_ratio": cmp_.get("size_ratio", ""),
                            "detect_version": P["_version"], "params_sha": P["_sha"]})
                cnt[d["status"]] = cnt.get(d["status"], 0) + 1
                n += 1
        os.replace(tmp, path)
        summ["episodes"][str(e)] = {"frames": n, **cnt}
        print(f"  ep{e}: {n} 프레임 · " + " · ".join(f"{STATUS_KO[k]} {v}" for k, v in sorted(cnt.items())))
    old = {}
    sp = os.path.join(od, "summary.json")
    if os.path.exists(sp):
        with open(sp) as f:
            old = json.load(f).get("episodes", {})
    summ["episodes"] = {**old, **summ["episodes"]}
    with open(sp, "w") as f:
        json.dump(summ, f, ensure_ascii=False, indent=1)
    print(f"→ {od}")
    return 0


def _set_target(argv, entry):
    """set-ref --kind target (--session S --episodes 0,3 | --image WRIST.png) [--tol-uv 0.02] [--tol-size 0.05] [--tol-angle 3] [--name ..] [--add]"""
    import glob

    tu = float(argv[argv.index("--tol-uv") + 1]) if "--tol-uv" in argv else 0.02
    ts_ = float(argv[argv.index("--tol-size") + 1]) if "--tol-size" in argv else 0.05
    ta = float(argv[argv.index("--tol-angle") + 1]) if "--tol-angle" in argv else 3.0
    if "--image" in argv:  # 2026-11-06: 손목 원본 사진 한 장 (사용자가 잡을 자세를 잡은 순간) 의 큐브 윤곽
        from PIL import Image

        fn = os.path.abspath(argv[argv.index("--image") + 1])
        P = load_params()
        d = detect(np.array(Image.open(fn).convert("RGB")), P)
        c = d.get("cube")
        if not c or c.get("touches_edge"):
            print(f"그 사진에서 큐브를 온전히 못 찾았어요 ({d['reason']}) — 목표로 쓰지 않음")
            return 1
        with open(fn, "rb") as f:
            sha = hashlib.sha256(f.read()).hexdigest()[:16]
        entry.update(u=c["u"], v=c["v"], area_px=int(c["area_px"]), angle=round(cube_angle(c["hull"]), 2),
                     hull=[[round(x / 640.0, 4), round(y / 480.0, 4)] for x, y in c["hull"]], tol={"u": tu, "v": tu, "size": ts_, "angle": ta},
                     meaning="닫기 자리 목표 (화면 안내) — 사진 한 장의 큐브 윤곽. 자동 판정 · 자동 동작 아님",
                     source={"image": fn.replace(HOME, "~"), "image_sha256": sha, "detect_version": P["_version"]})
        ver = add_ref(entry, activate="add" if "--add" in argv else True)
        print(f"참조 {ver} (닫기 자리 목표, 사진: u {c['u']:.3f} v {c['v']:.3f} 넓이 {c['area_px']} 기울기 {entry['angle']:+.1f}°) 저장 · 활성 → {REF_PATH}")
        return 0

    import pandas as pd

    sys.path.insert(0, HERE)
    import r12_common as rc
    import sg_phase

    sess = argv[argv.index("--session") + 1]
    eps = [int(x) for x in argv[argv.index("--episodes") + 1].split(",")]
    sess_dir = rc.session_dir(sess)
    df = pd.concat([pd.read_parquet(p) for p in sorted(glob.glob(os.path.join(sess_dir, "dataset", "data", "*", "*.parquet")))])
    P = load_params()
    per = []
    for ep in eps:
        e = df[df.episode_index == ep].sort_values("frame_index")
        r = sg_phase.analyze(np.stack(e["observation.state"].values), np.stack(e["action"].values), 30)
        ci = (r.get("_idx") or {}).get("close")
        if ci is None:
            print(f"ep{ep}: 닫기 시작을 못 찾았어요 — 목표로 쓰지 않음")
            return 1
        want = set(range(max(0, ci - 15), ci + 1))
        got = []
        for fi, ts, img in wrist_frames(sess_dir, ep):
            if fi in want:
                d = detect(img, P)
                c = d.get("cube")
                if c and not c.get("touches_edge"):
                    got.append((c["u"], c["v"], c["area_px"], cube_angle(c["hull"]), c["hull"], fi))
            if fi > ci:
                break
        if len(got) < 5:
            print(f"ep{ep}: 닫기 직전 큐브 검출 {len(got)}/16 — 목표로 쓰지 않음")
            return 1
        arr = np.array([g[:4] for g in got], float)
        med = np.median(arr, 0)
        k = int(np.argmin(np.abs(arr - med).sum(1)))
        per.append({"ep": ep, "close_s": round(ci / 30, 2), "u": float(med[0]), "v": float(med[1]), "area_px": float(med[2]), "angle": float(med[3]),
                    "hull": got[k][4]})
        print(f"  ep{ep}: 닫기 {ci / 30:.2f} s · 큐브 u {med[0]:.3f} v {med[1]:.3f} 넓이 {med[2]:.0f} 기울기 {med[3]:+.1f}° ({len(got)} 프레임)")
    u, v = float(np.mean([p["u"] for p in per])), float(np.mean([p["v"] for p in per]))
    area, ang = float(np.mean([p["area_px"] for p in per])), float(np.mean([p["angle"] for p in per]))
    b = per[0]  # 윤곽 모양은 첫 판 것을 평균 중심 · 넓이로 옮김
    sc = math.sqrt(area / b["area_px"])
    W, H = 640.0, 480.0
    hull = [[round((b["u"] * W + (x - b["u"] * W) * sc + (u - b["u"]) * W) / W, 4), round((b["v"] * H + (y - b["v"] * H) * sc + (v - b["v"]) * H) / H, 4)]
            for x, y in b["hull"]]
    tu = float(argv[argv.index("--tol-uv") + 1]) if "--tol-uv" in argv else 0.02
    ts_ = float(argv[argv.index("--tol-size") + 1]) if "--tol-size" in argv else 0.05
    ta = float(argv[argv.index("--tol-angle") + 1]) if "--tol-angle" in argv else 3.0
    entry.update(u=round(u, 4), v=round(v, 4), area_px=round(area), angle=round(ang, 2), hull=hull, tol={"u": tu, "v": tu, "size": ts_, "angle": ta},
                 meaning="닫기 자리 목표 (화면 안내) — 고른 판들의 닫기 직전 큐브 윤곽 평균. 자동 판정 · 자동 동작 아님",
                 source={"session": sess, "episodes": per and [{k: p[k] for k in ("ep", "close_s", "u", "v", "area_px", "angle")} for p in per],
                         "detect_version": P["_version"], "close_def": "sg_phase 닫기 시작 직전 0.5 s 중앙값"})
    ver = add_ref(entry, activate="add" if "--add" in argv else True)
    print(f"참조 {ver} (닫기 자리 목표 u {u:.3f} v {v:.3f} 넓이 {area:.0f} 기울기 {ang:+.1f}°, 허용 ±{tu} · ±{ts_:.0%} · ±{ta}°) 저장 · 활성 → {REF_PATH}")
    return 0


def cmd_set_ref(argv):
    kind = argv[argv.index("--kind") + 1] if "--kind" in argv else "point"
    note = argv[argv.index("--note") + 1] if "--note" in argv else ""
    entry = {"kind": kind, "note": note, "meaning": "정렬 참고 — 자동 성공 판정 아님. 접근 높이 · 거리 · 자세가 다르면 같은 자리가 정답이 아닐 수 있음"}
    if "--name" in argv:
        entry["name"] = argv[argv.index("--name") + 1]
    if kind == "target":  # 닫기 자리 목표: 녹화 판들의 '닫기 시작' 직전 0.5 s 큐브 윤곽 (sg_phase 와 같은 정의)
        return _set_target(argv, entry)
    if "--uv" in argv:
        u, v = (float(x) for x in argv[argv.index("--uv") + 1].split(","))
        entry.update(u=u, v=v, source={"manual": True})
    elif "--image" in argv:  # 카메라 미리보기 등에서 저장한 손목 원본 PNG
        from PIL import Image

        fn = os.path.abspath(argv[argv.index("--image") + 1])
        P = load_params()
        d = detect(np.array(Image.open(fn).convert("RGB")), P)
        if kind == "cross":  # 큐브 중심 십자 — 스티커 없이 큐브만 있으면 됨
            if not d.get("cube"):
                print(f"그 이미지에서 큐브를 못 찾았어요 ({d['reason']}) — 참조로 쓰지 않았어요.")
                return 1
            with open(fn, "rb") as f:
                sha = hashlib.sha256(f.read()).hexdigest()[:16]
            c = d["cube"]
            entry.update(u=c["u"], v=c["v"], px=c["px"], cube_area_px=c["area_px"], half_u=0.03, half_v=0.03,
                         source={"image": fn.replace(HOME, "~"), "image_sha256": sha, "detect_version": P["_version"], "point": "cube_center"})
            ver = add_ref(entry, activate="add" if "--add" in argv else True)
            print(f"참조 {ver} (큐브 중심 십자 u {c['u']:.4f} v {c['v']:.4f}) 저장 · 활성 → {REF_PATH}")
            return 0
        if d["status"] != "detected":
            print(f"그 이미지 검출 상태가 '{STATUS_KO[d['status']]}' ({d['reason']}) — 참조로 쓰지 않았어요.")
            return 1
        s = d["sticker"]
        with open(fn, "rb") as f:
            sha = hashlib.sha256(f.read()).hexdigest()[:16]
        entry.update(u=s["u"], v=s["v"], px=s["px"], cube_area_px=d["cube"]["area_px"], sticker_area_px=s["area_px"],
                     source={"image": fn.replace(HOME, "~"), "image_sha256": sha, "detect_version": P["_version"]})
    else:
        sys.path.insert(0, HERE)
        import r12_common as rc

        sess = argv[argv.index("--session") + 1]
        ep = int(argv[argv.index("--episode") + 1])
        t = float(argv[argv.index("--t") + 1])
        sess_dir = rc.session_dir(sess)
        P = load_params()
        best = None
        for fi, ts, img in wrist_frames(sess_dir, ep):
            if best is None or abs(ts - t) < abs(best[1] - t):
                best = (fi, ts, img)
            if ts > t + 0.1:
                break
        fi, ts, img = best
        d = detect(img, P)
        if d["status"] != "detected":
            print(f"그 프레임 (ep{ep} {ts:.2f}s) 검출 상태가 '{STATUS_KO[d['status']]}' ({d['reason']}) — 참조로 쓰지 않았어요. 다른 시각을 고르세요.")
            return 1
        st = episode_states(sess_dir, ep).get(fi)
        s = d["sticker"]
        entry.update(u=s["u"], v=s["v"], cube_area_px=d["cube"]["area_px"], sticker_area_px=s["area_px"],
                     joints=dict(zip(["pan", "lift", "elbow", "wflex", "wroll", "grip"], [round(x, 1) for x in st])) if st else None,
                     source={"session": sess, "episode": ep, "frame_index": fi, "timestamp": ts, "detect_version": P["_version"]})
    if kind == "box":
        pad_u = float(argv[argv.index("--half-u") + 1]) if "--half-u" in argv else 0.05
        pad_v = float(argv[argv.index("--half-v") + 1]) if "--half-v" in argv else 0.05
        entry.update(half_u=pad_u, half_v=pad_v)
    else:
        entry["r"] = float(argv[argv.index("--r") + 1]) if "--r" in argv else 0.04
    ver = add_ref(entry, activate="add" if "--add" in argv else True)
    print(f"참조 {ver} 저장 · 활성 → {REF_PATH}")
    print(json.dumps(entry, ensure_ascii=False, indent=1))
    return 0


def cmd_image(argv):
    from PIL import Image

    out = argv[argv.index("--out") + 1] if "--out" in argv else None
    files = [a for a in argv if not a.startswith("--") and a != out]
    P = load_params()
    for fn in files:
        img = np.array(Image.open(fn).convert("RGB"))
        d = detect(img, P)
        brief = {k: d[k] for k in ("status", "reason", "ms")}
        brief["sticker_uv"] = [d["sticker"]["u"], d["sticker"]["v"]] if d["sticker"] else None
        print(os.path.basename(fn), json.dumps(brief, ensure_ascii=False))
        if out:
            import sg_viewer

            os.makedirs(out, exist_ok=True)
            im = sg_viewer.draw_wrist(Image.fromarray(img), d, active_ref(), 1.0)
            im.save(os.path.join(out, os.path.splitext(os.path.basename(fn))[0] + "_det.png"))
    return 0


def main():
    argv = sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd == "annotate":
        return cmd_annotate(rest)
    if cmd == "set-ref":
        return cmd_set_ref(rest)
    if cmd == "image":
        sys.path.insert(0, HERE)
        return cmd_image(rest)
    if cmd == "refs":
        print(json.dumps(read_refs(), ensure_ascii=False, indent=1))
        return 0
    if cmd == "use-ref":
        d = read_refs()
        vs = [] if rest[0] == "none" else rest[0].split(",")
        bad = [v for v in vs if v not in d.get("refs", {})]
        if bad:
            print(f"없는 버전: {bad}")
            return 1
        d["active"] = vs[0] if len(vs) == 1 else (vs or None)
        _write_refs(d)
        print(f"활성 참조 = {d['active']}")
        return 0
    print(f"모르는 명령: {cmd}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
