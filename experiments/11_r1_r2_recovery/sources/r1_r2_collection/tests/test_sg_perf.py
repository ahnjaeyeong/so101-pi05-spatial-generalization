#!/home/user/so101-env/bin/python
"""검출 표시 On/Off 에서 녹화 루프 · 저장 프레임 비교 (로봇 · 카메라 없음).

실제 lerobot 0.6.2 record() + r12_record_entry (화면 탭) 를 가짜 로봇 (test_entry_stub 의 장치 차단 · StubRobot) 으로 돌린다.
가짜 로봇은 실제 d2 손목 · front 프레임 ([합성] 흰 스티커를 붙인 것 포함) 을 차례로 내보낸다 → 화면 프로세스가 실제로 검출을 돌림.
조건마다 같은 길이 판을 녹화하고 저장된 dataset 프레임 수 · rec_end (loop Hz · 늦은 틱) 를 비교:
  A 화면 없음 · B 화면 (검출 끔) · C 화면 (검출 켬). 화면은 별도 프로세스 (sg_viewer.py --bench, Tk 화면과 같은 50 ms 주기).

  PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python tests/test_sg_perf.py [--root DIR] [--secs 12] [--reps 2]
"""

import datetime
import glob
import json
import os
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = sys.argv[sys.argv.index("--root") + 1] if "--root" in sys.argv else f"/tmp/sg_perf_{datetime.datetime.now():%Y%m%d_%H%M%S}"
SECS = float(sys.argv[sys.argv.index("--secs") + 1]) if "--secs" in sys.argv else 12.0
REPS = int(sys.argv[sys.argv.index("--reps") + 1]) if "--reps" in sys.argv else 2
sys.argv = [sys.argv[0], "--root", ROOT]  # test_entry_stub 가 import 때 --root 를 읽음
sys.path.insert(0, HERE)
import test_entry_stub as T  # noqa: E402  (ROOT · R12_LIVE_DIR 설정, 장치 차단 함수 · 가짜 로봇)

TOOLS = T.TOOLS
VENV = os.path.expanduser("~/so101-env/bin/python")
LIVE = os.environ["R12_LIVE_DIR"]


def load_frames(n=90):
    import av

    sys.path.insert(0, TOOLS)
    import sg_sticker as sgs
    from test_sg_sticker import paste_sticker, sticker_spot

    P = sgs.load_params(None)
    base = os.path.expanduser("~/so101_runs/main_k8/d2/dataset/videos")
    out = []
    cw = av.open(sorted(glob.glob(f"{base}/observation.images.wrist/chunk-000/*.mp4"))[0])
    cf = av.open(sorted(glob.glob(f"{base}/observation.images.front/chunk-000/*.mp4"))[0])
    for k, (fw, ff) in enumerate(zip(cw.decode(video=0), cf.decode(video=0))):
        if k % 4:
            continue
        w, f = fw.to_ndarray(format="rgb24"), ff.to_ndarray(format="rgb24")
        d = sgs.detect(w, P)
        if d.get("cube") and d["cube"]["area_px"] > 2500 and len(out) % 2 == 0:
            side = max(8, int(0.28 * np.sqrt(d["cube"]["area_px"])))
            c = sticker_spot(w, side)
            if c is not None:
                w = paste_sticker(w, c, side)
        out.append((f, w))
        if len(out) >= n:
            break
    cw.close()
    cf.close()
    return out


FRAMES = []


class FrameRobot(T.StubRobot):
    def get_observation(self):
        self.n += 1
        f, w = FRAMES[self.n % len(FRAMES)]
        return {**{k: float(v) for k, v in self.pose.items()}, "front": f, "wrist": w}


def main():
    FRAMES.extend(load_frames())
    T.StubRobot = FrameRobot  # run_record 가 만드는 가짜 로봇 (connect 전 assert 는 그대로 — FrameRobot 은 StubRobot 하위)
    T.block_hardware()
    import lerobot.scripts.lerobot_record as lr
    import r12_record_entry as entry

    orig_connect = T.StubRobot.connect
    entry.install(lr)
    base = ["--robot.type=so101_follower", "--robot.port=/nonexistent/so101_follower", "--robot.id=sg_perf_test",
            '--robot.cameras={ front: {type: opencv, index_or_path: /nonexistent/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG"}, '
            'wrist: {type: opencv, index_or_path: /nonexistent/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG"} }',
            "--teleop.type=so101_leader", "--teleop.port=/nonexistent/so101_leader", "--teleop.id=sg_perf_test",
            "--dataset.single_task=pick up the red cube and put it in the brown box", f"--dataset.episode_time_s={SECS + 30}",
            "--dataset.reset_time_s=3600", "--dataset.push_to_hub=false", "--dataset.no_stamp=true", "--play_sounds=false",
            "--display_data=true"]
    conds = [c for _ in range(REPS) for c in ("A_no_viewer", "B_viewer_det_off", "C_viewer_det_on")]
    rows = []
    for k, cond in enumerate(conds):
        ds = os.path.join(ROOT, f"ds_{k}_{cond}")
        res = {}
        viewer = None
        if cond != "A_no_viewer":
            cmd = [VENV, os.path.join(TOOLS, "sg_viewer.py"), "--live", LIVE, "--bench", str(SECS + 6), "--size", "1400x860"]
            if cond == "B_viewer_det_off":
                cmd.append("--no-det")
            viewer = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                      env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1", R12_CONFIG=os.path.join(os.path.dirname(HERE), "config", "sg50.yaml")))

        def script(ev, q, robot):
            T.expect(q, "setup_start", ep=0, timeout=60)
            robot.pose = dict(T.SAFE)
            time.sleep(1.0)
            T.press(ev, "right")
            T.expect(q, "rec_start", ep=0)
            time.sleep(SECS)
            T.press(ev, "right")
            res["rec_end"] = T.expect(q, "rec_end", ep=0)
            T.expect(q, "setup_start", timeout=30)
            T.press(ev, "esc")

        T.run_record(lr, entry, base + [f"--dataset.repo_id=test/sg_perf_{k}", f"--dataset.root={ds}", "--dataset.num_episodes=2"], script)
        vperf = None
        if viewer is not None:
            out, _ = viewer.communicate(timeout=60)
            vperf = json.loads([ln for ln in out.splitlines() if ln.startswith("{")][-1])
        import pandas as pd

        fs = sorted(glob.glob(os.path.join(ds, "data", "*", "*.parquet")))
        df = pd.concat([pd.read_parquet(f) for f in fs])
        ts = df.timestamp.values
        e = res["rec_end"]
        row = {"cond": cond, "saved_frames": len(df), "rec_end_frames": e["frames"], "loop_hz_mean": e["loop_hz_mean"],
               "late_ticks": e["late_ticks"], "frame_index_contiguous": bool((np.diff(df.frame_index.values) == 1).all()),
               "timestamp_step_ok": bool(np.allclose(np.diff(ts), 1 / 30, atol=1e-4)),
               "viewer": vperf}
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)
    T.StubRobot.connect = orig_connect
    with open(os.path.join(ROOT, "sg_perf_results.json"), "w") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    # 판정: 모든 조건에서 저장 프레임 = rec_end 프레임, frame_index 연속, 늦은 틱 ≤ 1%, C 에서 실제 검출이 돌았음
    for r in rows:
        assert r["saved_frames"] == r["rec_end_frames"] and r["frame_index_contiguous"] and r["timestamp_step_ok"], r
        assert r["late_ticks"] <= 0.01 * r["rec_end_frames"], r
        if r["cond"] == "C_viewer_det_on":
            assert r["viewer"]["detect_runs"] > 50, r
    print(f"PASS · 결과 {os.path.join(ROOT, 'sg_perf_results.json')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
