#!/home/user/so101-env/bin/python
"""저장된 실물 녹화 (읽기만) 의 한 프레임으로 영상 창을 띄워 화면을 찍는다 — 로봇 · 녹화 · lerobot 없음.
임시 live 폴더에 frames.u8 · status.json · ui.json 을 만들어 r12_viewer 가 실제 녹화 때와 같은 방식으로 읽게 한다.

  PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python tests/render_saved_episode.py --session main_k8/r12_pilot12_r2p --episode 0 \\
      --frame 195 --state RESET --out /tmp/x.png [--keys F6,F6] [--hist 0] [--config config/r12_pilot12.yaml]
  --keys = 창 키 (viewer_cmd.json: F4 디버그 · F5/F6 단계 · F9 관찰 · F10 확인) · --hist N = 녹화 중이면 N 프레임 전부터 관절 기록을 흘려 자동 단계를 실제처럼
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import tempfile
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
COLL = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(COLL, "tools"))
sys.path.insert(0, os.path.expanduser("~/so101_boxpick/scripts"))
import r12_common as rc  # noqa: E402
import r12_guide as G  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", required=True)
    ap.add_argument("--episode", type=int, required=True)
    ap.add_argument("--frame", type=int, required=True)
    ap.add_argument("--state", default="RESET")
    ap.add_argument("--out", required=True)
    ap.add_argument("--config", default=os.path.join(COLL, "config", "r12_pilot12.yaml"))
    ap.add_argument("--scale", default="0.8")
    ap.add_argument("--keys", default="")
    ap.add_argument("--hist", type=int, default=0)
    ap.add_argument("--screen", default="")
    ap.add_argument("--label", default="")
    ap.add_argument("--plan-group", default="", help="화면 확인용: 이 그룹 계획 줄을 씀 (영상 · 관절은 --session 저장 판 것, 큐브 위치는 계획과 무관)")
    ap.add_argument("--plan-index", type=int, default=0)
    a = ap.parse_args()
    import pandas as pd
    import record_ui as ru

    cfg = rc.load_config(a.config)
    sess = rc.session_dir(a.session)
    ds = os.path.join(sess, "dataset")
    info = json.load(open(os.path.join(ds, "meta", "info.json")))
    _, eps, cams = ru.load_meta(ds)
    er = eps[eps.episode_index == a.episode].iloc[0]
    d = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(os.path.join(ds, "data", "*", "*.parquet")))])
    g = d[d.episode_index == a.episode].sort_values("frame_index")
    S, A = np.stack(g["observation.state"].values), np.stack(g["action"].values)
    imgs, thumbs = {}, []
    for cam in cams:
        t0 = float(er[f"videos/{cam}/from_timestamp"])
        imgs[cam.split(".")[-1]] = next(ru.iter_frames(ru.video_path(ds, info, cam, er), t0 + a.frame / 30, t0 + (a.frame + 1) / 30, 30))
        if cam.endswith("wrist"):
            thumbs = [f[::4, ::4] for k, f in enumerate(ru.iter_frames(ru.video_path(ds, info, cam, er), t0, t0 + len(g) / 30, 30)) if k % 10 == 0]
    live = tempfile.mkdtemp(prefix="r12_render_")
    fr = rc.LiveFrames(live, create=True)
    fr.put(0, imgs["front"])
    fr.put(1, imgs["wrist"])
    fr.bump()
    names = [f"{j}.pos" for j in rc.JOINTS]
    st = {"t": time.time() + 3600, "phase": "after_rec", "state": dict(zip(names, map(float, S[a.frame]))), "action": dict(zip(names, map(float, A[a.frame]))),
          "checks": [], "fps": 30, "loop_hz": 30.0, "guard": {"enabled": True, "gap": 1.0}}
    rc.write_json(os.path.join(live, "status.json"), st)
    plan = rc.read_plan(sess)
    row = rc.describe_row(cfg, rc.make_plan(cfg, a.plan_group)[a.plan_index] if a.plan_group else plan[a.episode])
    review = G.review_episode(A[:, 5], S[:, 5], thumbs, cfg)
    ui = {"state": a.state, "episode": a.episode, "session": a.session, "target": len(plan), "done": 2, "row": row, "review": review,
          "keys": [], "results": [], "label": a.label, "program": [], "rec_aid": "render", "elapsed": a.frame / 30, "episode_time": 45}
    rc.write_json(os.path.join(live, "ui.json"), ui)
    env = dict(os.environ, R12_CONFIG=a.config, PYTHONDONTWRITEBYTECODE="1", R12_NO_OPEN="1")
    if a.screen:
        env["R12_SCREEN"] = a.screen
    p = subprocess.Popen([sys.executable, os.path.join(COLL, "tools", "r12_viewer.py"), "--live", live, "--scale", a.scale], env=env)
    # 창이 뜨고 크기 맞춤 (1.5 s) 이 끝난 뒤에만 찍는다 — 일찍 찍으면 창 밖 화면 (다른 창) 이 섞일 수 있음
    for _ in range(100):
        time.sleep(0.1)
        if os.path.exists(os.path.join(live, "viewer_ready.json")):
            break
    if a.hist and a.state == "REC":  # 녹화 중 관절 기록을 차례로 흘려 자동 단계 추정이 실제처럼 쌓이게 (화면 갱신 ~15 Hz)
        for k in range(max(0, a.frame - a.hist), a.frame + 1, 2):
            rc.write_json(os.path.join(live, "status.json"), dict(st, t=time.time() + 3600, state=dict(zip(names, map(float, S[k]))),
                                                                  action=dict(zip(names, map(float, A[k])))))
            fr.bump()
            time.sleep(0.07)
    if a.keys:
        rc.write_json(os.path.join(live, "viewer_cmd.json"), {"keys": [k for k in a.keys.split(",") if k]})
    for _ in range(30):  # 실제 녹화처럼 영상 순번을 계속 올림 (같은 장면 — '영상 갱신 안 됨' 표시가 나오지 않게)
        fr.bump()
        time.sleep(0.1)
    rc.write_json(os.path.join(live, "snap_request.json"), {"path": os.path.abspath(a.out)})
    for _ in range(150):
        fr.bump()
        time.sleep(0.1)
        if os.path.exists(os.path.join(live, "snap_done.json")):
            break
    p.terminate()
    print(json.dumps({"out": a.out, "done": rc.read_json(os.path.join(live, "snap_done.json")), "review": review,
                      "perf": rc.read_json(os.path.join(live, "viewer_perf.json"))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
