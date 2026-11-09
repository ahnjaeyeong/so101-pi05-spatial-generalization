#!/home/user/so101-env/bin/python
"""SG50 최대거리 확인 (읽기만) — 사용자가 녹화 프로그램 준비 단계 (녹화 안 함) 에서 큐브를 '수직으로 잡을 수 있는 가장 먼 자리' 에 놓고
그리퍼를 수직으로 큐브 바로 위 (닫기 직전 높이) 에 둔 뒤 실행. 실행 중인 화면 프로세스의 공유 폴더 (/dev/shm/r12_live_*) 를
그 프로세스 인자에서 정확히 찾아 읽는다 (가장 최근 폴더를 고르지 않음). 로봇 · 카메라를 열지 않는다.

  ~/so101-env/bin/python sg_reach.py [--label 왼쪽앞] [--live /dev/shm/r12_live_...]
  → <세션>/qa/reach_check.csv 에 한 줄 + front · wrist PNG

기록: 시각 · 라벨 · front 큐브 탁자 좌표 (cm, front H) · 밑동 (설정 base) 까지 거리 · 방향° · 그리퍼 끝 FK (로봇 기준 거리 · 높이) ·
앞뒤 기울기 (sg_fk, + = 손끝이 로봇에서 멀리) · 팔로워 관절값 · 상태 파일 나이.
"""

import csv
import math
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import r12_common as rc  # noqa: E402
import sg_fk  # noqa: E402

FIELDS = ["time", "label", "session", "live", "status_age_s", "front_detected", "cube_x_cm", "cube_y_cm", "base_dist_cm", "bearing_deg",
          "tcp_r_cm", "tcp_z_cm", "tilt_fwd_deg", "tilt_side_deg", "pan", "lift", "elbow", "wflex", "wroll", "grip", "front_png", "wrist_png"]


def find_live():
    out = subprocess.run(["ps", "-eo", "args"], capture_output=True, text=True).stdout.splitlines()
    lives = []
    for ln in out:
        if "/sg_viewer.py" in ln and "--live" in ln and not ln.startswith(("grep", "ugrep")):
            parts = ln.split()
            try:
                lives.append(parts[parts.index("--live") + 1])
            except (ValueError, IndexError):
                pass
    return sorted(set(lives))


def main(argv):
    label = argv[argv.index("--label") + 1] if "--label" in argv else ""
    if "--live" in argv:
        live = argv[argv.index("--live") + 1]
    else:
        lives = find_live()
        if len(lives) != 1:
            print(f"실행 중인 화면 공유 폴더를 하나로 못 찾았어요: {lives or '없음'} — --live 로 지정하세요")
            return 1
        live = lives[0]
    st = rc.read_json(os.path.join(live, "status.json"), {}) or {}
    ui = rc.read_json(os.path.join(live, "ui.json"), {}) or {}
    age = time.time() - float(st.get("t", 0))
    state = st.get("state")
    if not state or age > 2.0:
        print(f"팔로워 관절값이 없거나 오래됨 (나이 {age:.1f} s) — 녹화 프로그램 (record) 준비 단계에서 실행하세요 (카메라 미리보기는 로봇 연결 없음)")
        return 1
    cfg = rc.load_config(os.environ.get("R12_CONFIG") or os.path.join(rc.ROOT, "config", "sg50.yaml"))
    _, front, wrist = rc.LiveFrames(live, create=False).get()
    vis = rc.vision(front, None, cfg)
    f = vis.get("front") or {}
    J = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
    deg = [float(state[f"{j}.pos"]) for j in J]
    p, _ = sg_fk.fk([deg[:5]])
    fwd, side, _ = sg_fk.tool_tilt(state)
    bx, by = rc.base_xy(cfg)
    row = {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "label": label, "session": ui.get("session", ""), "live": live, "status_age_s": round(age, 2),
           "front_detected": bool(f.get("detected")), "tcp_r_cm": round(math.hypot(p[0][0], p[0][1]) * 100, 1), "tcp_z_cm": round(p[0][2] * 100, 1),
           "tilt_fwd_deg": round(fwd, 1), "tilt_side_deg": round(side, 1), **dict(zip(["pan", "lift", "elbow", "wflex", "wroll", "grip"], [round(v, 1) for v in deg]))}
    if f.get("detected"):
        x, y = f["xy_cm"]
        row.update(cube_x_cm=x, cube_y_cm=y, base_dist_cm=round(math.hypot(x - bx, y - by), 1), bearing_deg=round(math.degrees(math.atan2(y - by, x - bx)), 1))
    sess = (ui.get("session") or "").split(" ")[0]
    if "--out" in argv:  # 시험용
        out_dir = argv[argv.index("--out") + 1]
    else:
        out_dir = None
    try:
        if out_dir:
            raise RuntimeError

        out_dir = os.path.join(rc.session_dir(sess), "qa")
    except Exception:
        out_dir = out_dir or os.path.join(rc.session_dir("practice/sg50_pilot3"), "qa")
    os.makedirs(out_dir, exist_ok=True)
    from PIL import Image

    stamp = time.strftime("%H%M%S")
    for cam, img in (("front", front), ("wrist", wrist)):
        fn = os.path.join(out_dir, f"reach_{stamp}_{cam}.png")
        Image.fromarray(img).save(fn)
        row[f"{cam}_png"] = os.path.basename(fn)
    path = os.path.join(out_dir, "reach_check.csv")
    new = not os.path.exists(path)
    with open(path, "a", newline="") as fh:
        w = csv.DictWriter(fh, FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)
    print(f"[{label or '-'}] front 큐브 " + (f"({row['cube_x_cm']}, {row['cube_y_cm']}) cm · 밑동까지 {row['base_dist_cm']} cm · 방향 {row['bearing_deg']:+.0f}°"
                                           if f.get("detected") else "검출 안 됨")
          + f" | 그리퍼 끝 로봇 기준 {row['tcp_r_cm']} cm · 높이 {row['tcp_z_cm']} cm · 앞뒤 기울기 {fwd:+.1f}° | → {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
