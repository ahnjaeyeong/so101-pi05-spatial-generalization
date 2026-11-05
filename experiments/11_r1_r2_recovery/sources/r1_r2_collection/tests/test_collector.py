#!/home/user/so101-env/bin/python
"""수집자 모드 (네모 그림 가이드) 시험 — 로봇 · 녹화 · lerobot 없음. 실물 R2-P 세션은 읽기만 (해시로 확인).

A. 그림 · 설정: R2-P AHEAD · DEPTH 의 단계 그림 (4 카드 + ⑤) · 실패 그림 3 (앞쪽 · 옆 · 화면 끝) · 목표 · AHEAD/DEPTH 그림이 다름 · 모두 그려짐
B. 관찰 · 닫힘 안내 규칙 (자동 · 보조): 앞쪽 · 옆 · 잘림 · 참고 위치 안 · 경계 근처/검출 없음/오래된 영상 = 불확실 · A/B/C/U/CLOSED
C. 녹화 뒤 검토 표시: 실물 R2-P ep0/ep1 (dataset 으로 다시 잰 그리퍼 검토) = 빈 파지 의심 · ep2 = 경고 없음 · 학습 판정 열 없음 (11-04 삭제)
   · 실물 세션 파일 바뀌지 않음
D. 영상 창 (DISPLAY 있을 때, 창 숨김): 작업 지시 §13 1–11
   1 AHEAD 그림 · 2 DEPTH 그림 · 3 단계 표시 (지금 · 다음 · 지난) · 4 수동 단계 (F5/F6 · 클릭 · F7) · 5 자동 불확실 → 전환 안 함 · 수동 유지
   6 화면 끝 잘림 · 7 그리퍼 열림/닫힘 · 9 수집자/디버그 (F4) · 11 안전 경고 · BLOCK 두 모드 모두 · 창 전용 키는 녹화로 안 넘김
   + F9 관찰 수동 · F10 사용자 확인 (C) · visual_guide 없는 시나리오 (R2-O) = 이전 화면 · 작은 화면 (R12_SCREEN) 에서 줄여 맞춤
(8 빈 파지 QA 경고 = C · 10 녹화 · 저장 · 결과 입력 회귀 = 기존 시험 + test_collector_preview.py · 12 기록 주기 = test_collector_preview.py)

  PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python tests/test_collector.py
"""

import glob
import hashlib
import json
import os
import sys
import tempfile
import time
import types

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
COLL = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(COLL, "tools"))
sys.path.insert(0, os.path.expanduser("~/so101_boxpick/scripts"))
CFG = os.path.join(COLL, "config", "r12_pilot12.yaml")
os.environ["R12_CONFIG"] = CFG
import r12_common as rc  # noqa: E402
import r12_guide as G  # noqa: E402
import r12_schematic as SC  # noqa: E402

OK = []
R2P_SESSION = "main_k8/r12_pilot12_r2p"


def check(name, cond, detail=""):
    print(f"  {'✓' if cond else '✗'} {name} {detail}", flush=True)
    OK.append(bool(cond))


def wrist_img(u=None, v=None, side=110, bg=200):
    """합성 손목 영상 (480×640 RGB): 밝은 바탕 + 빨간 네모 (중심 u, v · 한 변 side px). 화면 밖은 잘림."""
    im = np.full((480, 640, 3), bg, np.uint8)
    if u is not None:
        cx, cy = int(u * 640), int(v * 480)
        x0, x1 = max(0, cx - side // 2), min(640, cx + side // 2)
        y0, y1 = max(0, cy - side // 2), min(480, cy + side // 2)
        im[y0:y1, x0:x1] = (210, 25, 30)
    return im


def tree_hash(d):
    h = hashlib.sha256()
    for p in sorted(glob.glob(os.path.join(d, "**", "*"), recursive=True)):
        if os.path.isfile(p):
            h.update(p.encode())
            with open(p, "rb") as f:
                h.update(hashlib.sha256(f.read()).digest())
    return h.hexdigest()


def part_a(cfg):
    print("A. 그림 · 설정")
    vgs = {sid: s.get("visual_guide") for sid, s in cfg["scenarios"].items() if s.get("visual_guide")}
    check("visual_guide = R2-P-AHEAD · R2-P-DEPTH 만 (R1 · R2-O 는 설계만)", sorted(vgs) == ["R2-P-AHEAD", "R2-P-DEPTH"], str(sorted(vgs)))
    base = rc.load_config()
    check("기본 설정 (기존 세션) 에는 visual_guide 없음", not any(s.get("visual_guide") for s in base["scenarios"].values()))
    for sid, vg in vgs.items():
        keys = [s["key"] for s in cfg["scenarios"][sid]["guide_stages"]]
        st = vg["stages"]
        check(f"{sid}: 단계 키 = guide_stages · 카드 4 장면 + ⑤ 글", set(st) == set(keys) and all(st[k].get("scene") for k in ("start", "approach", "preclose", "close"))
              and all(st[k].get(x) for k in keys for x in ("now", "next", "dont")), str(keys))
        check(f"{sid}: 실패 그림 3 (ahead · side · edge) + 목표 (in_zone)", [f["key"] for f in vg["failures"]] == ["ahead", "side", "edge"]
              and vg["target"]["key"] == "in_zone")
        check(f"{sid}: 시작 · 정렬 그림 그리퍼 열림 · ④ grasp + 체크 · ② 화살표 + 목표 점선 · ③ 잘림 예시 (inset)",
              st["start"]["scene"]["grip"] == "open" and st["close"]["scene"]["grip"] == "grasp" and st["close"]["scene"]["mark"] == "check"
              and st["approach"]["scene"].get("arrow") and st["approach"]["scene"].get("target")
              and st["preclose"]["scene"]["inset"].get("cut") == "bottom")
    a, d = vgs["R2-P-AHEAD"], vgs["R2-P-DEPTH"]
    check("AHEAD · DEPTH 시작 그림 · 글이 다름 (큐브 위치 · 설명)", a["stages"]["start"]["scene"]["cube"] != d["stages"]["start"]["scene"]["cube"]
          and a["subtitle"] != d["subtitle"] and a["kind"] == "AHEAD" and d["kind"] == "DEPTH")
    check("AHEAD 시작 큐브는 손가락 끝 (v 0.56) 보다 앞 · DEPTH 는 손가락 끝에 걸침",
          a["stages"]["start"]["scene"]["cube"][1] + SC.CUBE_S / 2 < SC.FINGER_TIP_V < d["stages"]["start"]["scene"]["cube"][1] + SC.CUBE_S / 2)
    scenes = [s["scene"] for vg in vgs.values() for s in vg["stages"].values() if s.get("scene")] + \
        [f["scene"] for f in a["failures"]] + [a["target"]["scene"], {"grip": "closed"}]
    t0 = time.perf_counter()
    ims = [SC.render(s, (200, 150)) for s in scenes]
    dt = (time.perf_counter() - t0) / len(ims)
    check("모든 장면 그리기 (200×150) 오류 없음 · 장면당 시간", all(i.size == (200, 150) for i in ims), f"{len(ims)} 장 · {dt * 1000:.1f} ms/장 (캐시돼 한 번만)")
    px = np.asarray(SC.render({"grip": "open", "cube": [0.47, 0.95], "cut": "bottom"}, (200, 150)))
    check("화면 끝 잘림 = 아래 가장자리 빨간 띠", (px[-3, 5:-5, 0] > 180).mean() > 0.9 and (px[-3, 5:-5, 1] < 80).mean() > 0.9)
    lg = SC.legend((500, 120))
    check("범례 그림", lg.size == (500, 120))


def part_b():
    print("B. 관찰 · 닫힘 안내 (자동 · 보조)")
    z = rc.wrist_zone()

    def det(u, v, edge=False):
        return {"detected": True, "dx": 2 * u - 1, "dy": 2 * v - 1, "touches_edge": edge, "bbox": (0, 300, 100, 180 if edge else 100)}

    zc = ((z["u"][0] + z["u"][1]) / 2, (z["v"][0] + z["v"][1]) / 2)
    r = {k: SC.observe(*a) for k, a in {
        "ahead": (det(zc[0], 0.35), z), "side": (det(0.8, zc[1]), z), "edge": (det(zc[0], 0.9, True), z), "in": (det(*zc), z),
        "border": (det(z["u"][1] + 0.01, zc[1]), z), "none": ({"detected": False}, z), "stale": (det(*zc), z, False),
        "below": (det(zc[0], z["v"][1] + 0.08), z)}.items()}
    check("앞쪽 · 옆 · 잘림 · 참고 위치 안 = 확실", [r[k][:2] for k in ("ahead", "side", "edge", "in")] ==
          [("ahead", True), ("side", True), ("edge", True), ("in_zone", True)], str({k: r[k][0] for k in r}))
    check("경계 근처 · 검출 없음 · 오래된 영상 · 아래쪽 (잘리지 않음) = 불확실 (key 없음)",
          all(r[k][0] is None and r[k][1] is False for k in ("border", "none", "stale", "below")))
    cs = {k: SC.close_state(*a)[0] for k, a in {"ahead": ("ahead", True, False, True), "edge": ("edge", True, False, True),
                                                "in": ("in_zone", True, False, True), "user": ("in_zone", True, True, True),
                                                "unc": (None, False, False, True), "closed": ("in_zone", True, True, False)}.items()}
    check("닫힘 안내: 앞쪽/잘림 = A 아직 닫지 마세요 · 참고 위치 안 = B 직접 확인 (자동 '닫기 OK' 없음) · 사람 확인 = C · 불확실 = U · 닫힌 그리퍼 = CLOSED",
          cs == {"ahead": "A", "edge": "A", "in": "B", "user": "C", "unc": "U", "closed": "CLOSED"}, str(cs))
    check("안내 글에 '닫아도 됨' · 'OK' 같은 자동 보증 없음", all("OK" not in t and "닫아도 됨" not in t for _, (t, _) in SC.CLOSE_STATES.items()))


def part_c(cfg):
    print("C. 녹화 뒤 검토 표시 (실물 R2-P, dataset 으로 다시 잼) · 학습 판정 없음 (11-04 삭제)")
    sess = rc.session_dir(R2P_SESSION)
    if not os.path.isdir(os.path.join(sess, "dataset")):
        print("  · 실물 R2-P 세션 없음 — 건너뜀")
        return
    h0 = tree_hash(sess)
    import pandas as pd

    ds = os.path.join(sess, "dataset")
    d = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(os.path.join(ds, "data", "*", "*.parquet")))])
    res = {}
    for e in sorted(set(d.episode_index)):
        g = d[d.episode_index == e].sort_values("frame_index")
        S, A = np.stack(g["observation.state"].values), np.stack(g["action"].values)
        res[e] = {f[1] for f in G.review_episode(A[:, 5], S[:, 5], None, cfg) if f[0] == "warn"}
        print(f"    ep{e}: {sorted(res[e])}")
    check("ep0 · ep1 (첫 빈 파지 뒤 재파지) → 빈 파지 의심 · 파지 전 실패한 닫힘", all({"empty_first_close", "closes_before_grasp"} <= res[e] for e in (0, 1)))
    if 2 in res:
        check("ep2 (첫 닫힘에 쥠) → 경고 없음", not res[2])
    check("학습 판정 열 없음 (r12_pilot_episodes · 11-04 사용자 결정으로 삭제)",
          not any(k in rc.PILOT_FIELDS for k in ("auto_training_verdict", "auto_verdict_reasons", "operator_verdict")))
    check("실물 R2-P 세션 파일 바뀌지 않음 (읽기만)", tree_hash(sess) == h0)


def part_d(cfg):
    print("D. 영상 창 (실제 Viewer, 창 숨김)")
    if not os.environ.get("DISPLAY"):
        print("  · DISPLAY 없음 — 건너뜀")
        return
    import r12_viewer as V
    import r12_viewer_collector as C

    live = tempfile.mkdtemp(prefix="r12_collector_test_")
    fr = rc.LiveFrames(live, create=True)
    E = G.load_index()["episodes"]
    import cv2

    front = cv2.cvtColor(cv2.resize(cv2.imread(G.ref_image_path(E[0], "k_reach", "front")), (640, 480)), cv2.COLOR_BGR2RGB)
    fr.put(0, front)
    names = [f"{j}.pos" for j in rc.JOINTS]
    pose = [10.0, -20.0, 30.0, 60.0, 0.0, 30.0]

    last = {}

    def status(grip=30.0, guard=None, checks=(), pose_=None):
        last.update(grip=grip, guard=guard, checks=checks, pose_=pose_)
        p = list(pose_ or pose)
        p[5] = grip
        rc.write_json(os.path.join(live, "status.json"), {"t": time.time() + 3600, "state": dict(zip(names, p)), "action": dict(zip(names, p)),
                                                           "checks": [list(c) for c in checks], "guard": guard or {"enabled": True, "gap": 0.5}})

    plan = rc.make_plan(cfg, "pilot12_r2p")
    rows = {sid: rc.describe_row(cfg, next(p for p in plan if p["scenario_id"] == sid)) for sid in ("R2-P-AHEAD", "R2-P-DEPTH")}
    r2o = rc.describe_row(cfg, rc.make_plan(cfg, "pilot12_r2o")[0])

    def ui(state="SETUP", row=None, ep=0, aid=None, **kw):
        rc.write_json(os.path.join(live, "ui.json"), {"state": state, "episode": ep, "row": row or rows["R2-P-AHEAD"], "keys": [["→ / n", "녹화 시작"]],
                                                       "results": [], "program": [], "rec_aid": aid, "elapsed": 3.0, "episode_time": 45, **kw})

    def wrist(*a, **k):
        fr.put(1, wrist_img(*a, **k))
        fr.bump()

    status()
    ui()
    wrist(0.47, 0.30)
    v = V.Viewer(live, 0.8)
    v.root.withdraw()

    def frame(n=1):
        for _ in range(n):
            status(**last)  # 녹화 프로세스처럼 틱마다 새 상태 (t 가 바뀜)
            time.sleep(0.002)
            fr.bump()
            v.vis_t = 0
            v.refresh()
        t = v.banner.cget("text")
        return "화면 오류" not in t, t

    def key(k):
        V.Viewer.on_key(v, types.SimpleNamespace(keysym=k, char=""))

    c = v.coll
    good, bt = frame()
    check("1 R2-P AHEAD: 수집자 모드 기본 · 제목 · 보조 정보 (계획 표시) · 단계 그림 4 · 실패 그림 3 + 목표", good and v.layout == ("collector",)
          and c.title.cget("text") == "R2-P | 접근·정렬 교정 — 큐브가 손가락 앞 (접근 부족)"
          and c.sub.cget("text").startswith("아직 큐브를 잡을 위치가 아닙니다 — ") and "AHEAD" in c.info.cget("text")
          and "계획:" in c.info.cget("text") and all(x["img"].cget("image") for x in c.cards) and all(x["img"].cget("image") for x in c.fcards),
          bt[:80])
    check("  머리 아래 녹화 상태 줄 · 안전 띠 · 아래 띠 (지금 · 다음 · 이후 · 하지 말 것) 보임",
          v.top.winfo_manager() == "pack" and v.banner.winfo_manager() == "pack" and c.now.cget("text").startswith("지금:")
          and c.nxt.cget("text").startswith("다음:") and c.dont.cget("text").startswith("✗ 하지 말 것"))
    check("  3 칸 (준비): ① 배치 방법 (순서 · 옆에서 본 거리 그림) · ② 손목 실시간 · ③ 목표 손목 그림 (실시간과 같은 크기)",
          c.p1_title.cget("text").startswith("① 배치 방법") and c.p1_txt.cget("text").startswith("1. ") and c.p1_img.cget("image")
          and c.p3_img.cget("image") and "이렇게 보이면" in c.p3_title.cget("text") and c.wimg.winfo_reqwidth() == c.p3_img.winfo_reqwidth()
          and "1.5–3 cm" in c.p1_txt.cget("text"), c.p1_title.cget("text"))
    ahead_scene = c.vg["stages"]["start"]["scene"]
    ui(row=rows["R2-P-DEPTH"])
    good, bt = frame()
    check("2 R2-P DEPTH: 다른 그림 · 설명 · 보조 정보 DEPTH", good and c.vg["kind"] == "DEPTH" and "DEPTH" in c.info.cget("text")
          and c.vg["stages"]["start"]["scene"] != ahead_scene and "조금 더" in c.sub.cget("text")
          and c.title.cget("text") == "R2-P | 진입 깊이 교정 — 큐브가 손가락 끝에 걸침 (진입 부족)"
          and "겨우 닿는" in c.p1_txt.cget("text") and "걸침" in c.p3_cap.cget("text"))
    ui()
    frame()
    bgs = lambda: [x["frame"].cget("bg") for x in c.cards]  # noqa: E731
    hls = lambda: [x["frame"].cget("highlightbackground") for x in c.cards]  # noqa: E731
    check("3 준비 단계: ① 지금 (주황) · ② 다음 (파랑 테두리) · 위 손목 글 '지금 ①'", v.guide.cur == 0 and bgs()[0] == C.CUR and hls()[1] == C.NXT
          and c.cards[0]["title"].cget("text").startswith("지금"))
    key("F6")
    key("F6")
    frame()
    check("4 F6 두 번 → ③ 수동 · ① ② 지난 (흐림) · ④ 다음", v.guide.manual == 2 and bgs()[2] == C.CUR and bgs()[0] == C.DONE_C and hls()[3] == C.NXT
          and "수동 선택" in c.stage_src.cget("text"))
    key("F5")
    frame()
    check("4 F5 → ②", v.guide.cur == 1)
    c.click_stage(3)
    frame()
    check("4 그림 클릭 → ④", v.guide.cur == 3 and bgs()[3] == C.CUR)
    key("F6")
    frame()
    check("3 ⑤ (상자 → 쉬는 자세) = 카드 아래 줄 '지금'", v.guide.cur == 4 and c.done_line.cget("text").startswith("지금"))
    key("F7")
    frame()
    check("4 F7 → 자동 (준비 = ①)", v.guide.manual is None and v.guide.cur == 0)

    # 5 녹화 중 자동 단계: 팔이 움직임 → ② · 손목 큐브가 참고 위치 안 → ③ 은 0.4 s (6 번) 이어져야 · 잘린 큐브는 ③ 으로 안 바뀜 · 수동 유지
    z = v.zone
    zc = ((z["u"][0] + z["u"][1]) / 2, (z["v"][0] + z["v"][1]) / 2)
    ui("REC", aid="a1")
    wrist(0.47, 0.30)
    frame()
    p2 = list(pose)
    p2[1] += 10
    status(pose_=p2)
    frame(8)
    check("5 녹화 중 팔 이동 → 자동 ② (접근)", v.guide.cur == 1, v.guide.auto_why)
    check("  3 칸 (녹화 중): ① 지금 할 일 = 지금 단계 · ③ 목표 = 닫기 직전 손목 그림", c.p1_title.cget("text").startswith("① 지금 할 일 · ②")
          and "닫기 직전" in c.p3_title.cget("text"), c.p1_title.cget("text"))
    wrist(zc[0], zc[1] + 0.03, side=280)  # 큰 큐브가 화면 아래에서 잘림 (중심은 참고 위치 안)
    frame(10)
    w_ = v.vis.get("wrist") or {}
    check("5 큐브가 참고 위치 안이지만 화면 끝에서 잘림 (검출 불확실) → ③ 으로 자동 전환 안 함",
          w_.get("touches_edge") and rc.wrist_relation(w_) == "in_zone" and v.guide.cur == 1, v.guide.auto_why)
    wrist(*zc, side=110)
    frame(3)
    early = v.guide.cur
    frame(6)
    check("5 참고 위치 안 (잘림 없음) → 3 번 째에는 그대로 · 6 번 이어진 뒤 ③", early == 1 and v.guide.cur == 2, f"{early} → {v.guide.cur}")
    key("F5")
    frame(8)
    check("5 수동 ② 선택 → 자동 추정 (③) 이 달라도 수동 유지", v.guide.cur == 1 and v.guide.manual == 1 and v.guide.auto == 2)
    key("F7")

    # 6 화면 끝 잘림 · 7 그리퍼 · F9 · F10
    ui("REC", aid="a1")
    wrist(0.36, 0.97, side=120)
    frame()
    check("6 큐브가 손목 화면 아래 경계에서 잘림 → '화면 끝에 걸림' 그림 강조 · A 아직 닫지 마세요",
          c.obs[0] == "edge" and c.fcards[2]["frame"].cget("highlightthickness") == 5 and c.close[0] == "A"
          and "화면 끝" in c.c_obs.cget("text"), str(c.obs))
    wrist(*zc)
    frame()
    check("  참고 위치 안 (2D) → B 직접 확인하세요 · 목표 그림 '화면상 비슷함' (판정 아님)", c.close[0] == "B"
          and "직접 확인" in c.c_big.cget("text") and "화면상 비슷함" in c.fcards[3]["tag"].cget("text"))
    wrist(None)
    frame()
    check("  큐브 안 보임 → '큐브 위치 확인 필요' · 빨강/초록 강조 없음", c.close[0] == "U" and "큐브 위치 확인 필요" in c.c_big.cget("text")
          and all(x["frame"].cget("highlightthickness") != 5 for x in c.fcards))
    key("F9")
    frame()
    check("F9 → 수동 '앞쪽에 있음' (자동은 안 보임) · A", c.manual_obs == "ahead" and c.close[0] == "A" and c.fcards[0]["frame"].cget("highlightthickness") == 5
          and "수동" in c.fcards[0]["tag"].cget("text"))
    for _ in range(4):
        key("F9")
    frame()
    check("F9 다섯 번 → 다시 자동", c.manual_obs is None)
    wrist(*zc)
    key("F10")
    frame()
    check("F10 → C 사용자가 확인했습니다 (자동 판정 아님 표시)", c.close[0] == "C" and "자동 판정 아님" in c.c_big.cget("text"))
    c.click_obs(2)
    frame()
    check("실패 그림 클릭 (화면 끝) → 수동 · 사용자 확인 풀림 (A)", c.manual_obs == "edge" and not c.user_ok and c.close[0] == "A")
    ui("REC", aid="a2")
    frame()
    check("새 녹화 (다른 시도) → 수동 관찰 · 확인 표시 풀림", c.manual_obs is None and not c.user_ok)
    status(grip=31.0)
    frame()
    t_open = c.g_txt.cget("text")
    status(grip=2.0)
    frame()
    check("7 그리퍼 31 → '그리퍼 열림' · 2 → '그리퍼 닫힘' + 닫힘 안내 CLOSED", t_open.startswith("그리퍼 열림") and c.g_txt.cget("text").startswith("그리퍼 닫힘")
          and c.close[0] == "CLOSED", f"{t_open} / {c.g_txt.cget('text')}")
    status()

    # 9 모드 · 11 안전
    ui("SETUP", ep=1)
    status(guard={"enabled": True, "gap": 30, "hold": True, "hold_reason": "elbow 리더−팔로워 30°"})
    frame()
    col_banner = v.banner.cget("text")
    key("F4")
    frame()
    dbg_ok = v.layout[0] == "debug" and v.big.winfo_manager() == "pack" and c.header.winfo_manager() == "" and v.guide.strip.winfo_manager() == "pack"
    dbg_banner = v.banner.cget("text")
    check("9 F4 → 디버그 모드 (이전 화면: 단계 띠 · 관절 · d2 참고) · 수집자 칸 숨김", dbg_ok, str(v.layout))
    check("11 명령 보호 경고 = 수집자 · 디버그 모두 안전 띠에 · 띠 보임", "명령 보호" in col_banner and "명령 보호" in dbg_banner
          and v.banner.winfo_manager() == "pack")
    key("F4")
    status(checks=[("BLOCK", "nan", "관절값 NaN")])
    frame()
    check("9 F4 → 수집자 모드로 · 11 준비 BLOCK 사유가 '지금' 줄에 빨갛게", v.layout == ("collector",) and "막힘" in c.now.cget("text")
          and c.now.cget("fg") == C.RED, c.now.cget("text"))
    status()
    check("창 전용 키 (F4 F5 F6 F7 F9 F10) 는 녹화로 안 넘김 (keys.in 없음)", not os.path.exists(os.path.join(live, "keys.in")))
    ui("RESET", label="", review=[["warn", "empty_first_close", "첫 닫힘 빈 파지 의심"]])
    frame()
    rt = c.result.cget("text") + c.now.cget("text") + c.nxt.cget("text") + c.p1_txt.cget("text")
    check("결과 단계: 결과 입력 안내 · 학습 판정 (g/e/v) 문구 없음 (11-04 삭제)", "결과 입력" in c.now.cget("text") and "학습 판정" not in rt
          and "정상 시연" not in rt, rt[:120])
    ui("SETUP", row=r2o)
    frame()
    check("visual_guide 없는 시나리오 (R2-O) → 수집자 모드여도 이전 화면", v.layout[0] == "debug" and v.mode == "collector")
    ui("SETUP")
    frame()
    v.root.update_idletasks()
    w0, h0 = v.root.winfo_reqwidth(), v.root.winfo_reqheight()
    os.environ["R12_SCREEN"] = "1280x720"
    W0 = v.W
    for _ in range(6):  # (root.update() 는 쓰지 않음 — 손으로 부른 refresh 들이 예약한 타이머가 끝없이 돎)
        v.fit_window()
        frame()
    v.root.update_idletasks()
    w1, h1 = v.root.winfo_reqwidth(), v.root.winfo_reqheight()
    del os.environ["R12_SCREEN"]
    check("작은 화면 (1280×720) → 영상 · 그림을 줄여 창이 화면 안에 (잘리지 않음)", v.W < W0 and w1 <= 1280 * 0.98 + 2 and h1 <= 720 * 0.93 + 2,
          f"{w0}×{h0} (영상 {W0}) → {w1}×{h1} (영상 {v.W})")
    good, bt = frame()
    check("줄인 뒤에도 그림 · 상태 그대로 · 그리기 오류 없음", good and v.coll.title.cget("text").startswith("R2-P |") and all(x["img"].cget("image") for x in v.coll.cards), bt[:80])
    tm = sorted(x for k, x in v.refresh_times if k == "collector")
    print(f"    (참고) 창 한 번 그리기: 수집자 중앙 {np.median(tm) * 1000:.1f} ms · 최대 {max(tm) * 1000:.1f} ms (숨긴 창, 검출 포함)")
    v.root.destroy()


def main():
    cfg = rc.load_config(CFG)
    part_a(cfg)
    part_b()
    part_c(cfg)
    part_d(cfg)
    print(("PASS" if all(OK) else "FAIL") + f" {sum(OK)}/{len(OK)}")
    return 0 if all(OK) else 1


if __name__ == "__main__":
    sys.exit(main())
