#!/home/user/so101-env/bin/python
"""SG50 화면 예시 만들기 (로봇 · 카메라 없음). sg_viewer.Screen 이 Tk 창에 넣는 그림과 같은 그림을 PNG 로.

입력: d2 실제 판 하나의 같은 시각 front · wrist 원본 프레임 (dataset AV1 영상, 읽기만) + 그 프레임의 팔로워 관절값.
  손목 프레임에는 [합성] 흰 사각형 스티커를 붙인 경우와 안 붙인 경우를 쓴다 (실제 스티커 영상은 아직 없음).
상태 · ui 는 가짜 live 폴더 (임시) 에 r12 와 같은 형식으로 씀. 정렬 참고는 임시 참조 파일 (설정 파일은 건드리지 않음).

  PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python tests/shot_sg.py OUT_DIR
"""

import glob
import json
import os
import sys
import tempfile
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(os.path.dirname(HERE), "tools")
sys.path.insert(0, TOOLS)
sys.path.insert(0, HERE)
D2 = os.path.expanduser("~/so101_runs/main_k8/d2")


def frame_pair(ep, t):
    import av
    import pandas as pd

    m = pd.concat([pd.read_parquet(f) for f in glob.glob(f"{D2}/dataset/meta/episodes/*/*.parquet")])
    r = m[m.episode_index == ep].iloc[0]
    out = {}
    for cam in ("front", "wrist"):
        k = f"videos/observation.images.{cam}"
        p = f"{D2}/dataset/{k}/chunk-{int(r[f'{k}/chunk_index']):03d}/file-{int(r[f'{k}/file_index']):03d}.mp4"
        t0 = float(r[f"{k}/from_timestamp"])
        c = av.open(p)
        s = c.streams.video[0]
        c.seek(int((t0 + t - 1.0) / float(s.time_base)), stream=s, backward=True)
        for f in c.decode(s):
            if float(f.pts * s.time_base) >= t0 + t - 1e-3:
                out[cam] = f.to_ndarray(format="rgb24")
                break
        c.close()
    fs = sorted(glob.glob(f"{D2}/dataset/data/*/*.parquet"))
    d = pd.concat([pd.read_parquet(f, columns=["observation.state", "episode_index", "frame_index"]) for f in fs])
    st = d[(d.episode_index == ep) & (d.frame_index == int(round(t * 30)))]["observation.state"].iloc[0]
    names = ["shoulder_pan.pos", "shoulder_lift.pos", "elbow_flex.pos", "wrist_flex.pos", "wrist_roll.pos", "gripper.pos"]
    return out["front"], out["wrist"], dict(zip(names, [float(x) for x in st]))


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    import pandas as pd

    import r12_common as rc
    import sg_sticker as sgs
    from test_sg_sticker import paste_sticker, sticker_spot

    T = pd.read_csv(f"{D2}/diag_grasp_bias/grasp_train.csv")
    cand = T[T.layout_id.str.contains("K3")].iloc[0]
    ep, tg = int(cand.ep), float(cand.grasp_t)
    P = sgs.load_params(None)
    best = None
    for dt in (2.5, 2.0, 1.5, 1.2, 1.0):
        f, w, st = frame_pair(ep, tg - dt)
        d = sgs.detect(w, P)
        if d.get("cube") and not d["cube"]["touches_edge"] and (best is None or d["cube"]["area_px"] > best[3]["cube"]["area_px"]):
            best = (f, w, st, d, dt)
    f, w, st, d, dt = best
    side = max(8, int(0.28 * np.sqrt(d["cube"]["area_px"])))
    c = sticker_spot(w, side)
    w_stk = paste_sticker(w, c, side)
    cfg_path = os.path.join(os.path.dirname(HERE), "config", "sg50.yaml")
    os.environ["R12_CONFIG"] = cfg_path
    cfg = rc.load_config(cfg_path)
    import sg_plan
    import sg_viewer as sgv

    rows = sg_plan.make_rows(cfg, "sg50_main")
    row4 = rc.describe_row(cfg, rows[4])  # ep4 = K3 · P3
    row0 = rc.describe_row(cfg, rows[0])
    info = {"d2_episode": ep, "t_s": round(tg - dt, 2), "layout": cand.layout_id, "synthetic_sticker_center_px": list(c), "side_px": side}
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["SG_STICKER_REF"] = os.path.join(tmp, "ref.json")
        sgs.REF_PATH = os.environ["SG_STICKER_REF"]
        ds = sgs.detect(w_stk, P)
        sgs.add_ref({"kind": "box", "u": round(ds["sticker"]["u"] + 0.03, 3), "v": round(ds["sticker"]["v"] - 0.02, 3), "half_u": 0.04,
                     "half_v": 0.04, "cube_area_px": int(ds["cube"]["area_px"] * 1.35), "note": "화면 예시용 임시 참조 (실제 예비 시연 아님)",
                     "source": {"manual": True}})
        live = os.path.join(tmp, "live")
        os.makedirs(live)
        fr = rc.LiveFrames(live, create=True)

        def put(front, wrist, ui, phase, state, seq_bumps=1):
            fr.put(0, front), fr.put(1, wrist)
            for _ in range(seq_bumps):
                fr.bump()
            rc.write_json(os.path.join(live, "status.json"), {"t": time.time(), "phase": phase, "ep": ui["episode"], "run_id": "20261105_170000",
                                                              "loop_hz": 29.9, "rec_frames": 214 if phase == "rec" else 0, "late_ticks": 0,
                                                              "stall_ticks": {"front": 0, "wrist": 0}, "state": state, "action": state})
            rc.write_json(os.path.join(live, "ui.json"), ui)

        base_ui = {"session": "main_k8/sg50_main", "done": 4, "target": 48, "preview": False}
        shots = []
        # 1 녹화 중 · 검출 · 참조 (큰 창)
        scr = sgv.Screen(live, cfg)
        scr.P = P
        put(f, w_stk, {**base_ui, "state": "REC", "episode": 4, "row": row4}, "rec", st)
        scr.poll()
        scr.render(1800, 470).save(os.path.join(out, "sg_rec_detected_1800x470.png"))
        shots.append(("sg_rec_detected_1800x470.png", scr.det["status"]))
        scr.debug = True  # 디버그 화면 (F5) — 좌표 · 검출 수치
        scr.render(1400, 860).save(os.path.join(out, "sg_debug_rec_1400x860.png"))
        shots.append(("sg_debug_rec_1800x470.png", scr.det["status"]))
        scr.debug = False
        # 2 같은 장면 작은 창 (크기 바꿔도 같은 자리)
        scr.render(1200, 330).save(os.path.join(out, "sg_rec_detected_1200x330.png"))
        shots.append(("sg_rec_detected_1200x330.png", scr.det["status"]))
        # 2b 저장 중 · 2c 결과 입력 (다음 판 위치 = ep5 계획)
        row5 = rc.describe_row(cfg, rows[5])
        put(f, w_stk, {**base_ui, "state": "SAVING", "episode": 4, "row": row4}, "after_rec", st)
        scr.poll()
        scr.render(1800, 470).save(os.path.join(out, "sg_saving_1800x470.png"))
        shots.append(("sg_saving_1800x470.png", scr.det["status"]))
        put(f, w_stk, {**base_ui, "state": "RESET", "episode": 5, "row": row5}, "setup", st)
        scr.poll()
        scr.render(1800, 470).save(os.path.join(out, "sg_reset_next_1800x470.png"))
        shots.append(("sg_reset_next_1800x470.png", scr.det["status"]))
        # 3 스티커 없음 (실제 프레임 그대로) → 미검출
        put(f, w, {**base_ui, "state": "REC", "episode": 4, "row": row4}, "rec", st)
        scr.poll()
        scr.render(1800, 470).save(os.path.join(out, "sg_rec_no_sticker_1800x470.png"))
        shots.append(("sg_rec_no_sticker_1800x470.png", scr.det["status"]))
        # 4 준비 단계 · 시작 자세 목표와 다름 (P0 목표, d2 접근 중 자세)
        scr2 = sgv.Screen(live, cfg)
        scr2.P = P
        put(f, w_stk, {**base_ui, "state": "SETUP", "episode": 0, "row": row0}, "setup", st)
        scr2.poll()
        scr2.render(1800, 470).save(os.path.join(out, "sg_setup_pose_1800x470.png"))
        shots.append(("sg_setup_pose_1800x470.png", scr2.det["status"]))
        # 5 영상 멈춤: 새 프레임 없이 0.8 s
        time.sleep(0.8)
        rc.write_json(os.path.join(live, "status.json"), {"t": time.time(), "phase": "rec", "ep": 4, "run_id": "20261105_170000", "loop_hz": 29.9,
                                                          "rec_frames": 230, "late_ticks": 0, "stall_ticks": {"front": 0, "wrist": 0}, "state": st})
        rc.write_json(os.path.join(live, "ui.json"), {**base_ui, "state": "REC", "episode": 4, "row": row4})
        scr2.poll()  # scr2 는 마지막 프레임 순번을 이미 봄 → 새 프레임 없음 0.8 s
        scr2.render(1800, 470).save(os.path.join(out, "sg_stale_1800x470.png"))
        shots.append(("sg_stale_1800x470.png", "stale" if scr2.health.stale(time.time()) else "fresh"))
        del fr
    with open(os.path.join(out, "shots.json"), "w") as fh:
        json.dump({"source": info, "shots": shots, "note": "front · wrist = d2 같은 판 같은 시각 원본 프레임. 스티커 = [합성]. 참조 = 화면 예시용 임시"}, fh,
                  ensure_ascii=False, indent=1)
    print(json.dumps({"source": info, "shots": shots}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
