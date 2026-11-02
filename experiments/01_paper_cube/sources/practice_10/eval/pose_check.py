"""팔로워 현재 자세를 읽기만 해서 학습 데이터 시작 자세와 비교한다 (토크·설정 쓰기 없음).

lerobot-rollout 은 연결 순간의 자세를 "처음 자세"로 잡고, 판 사이 리셋도 그 자세로 돌아간다.
그래서 시작 자세가 학습 데이터와 다르면 정책이 처음부터 본 적 없는 자세에서 출발한다.

실행: PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python pose_check.py [--tol 10] [--yes]
- 버스: 포트 열기 + ping/펌웨어 읽기(handshake) + Present_Position 읽기만. disconnect() 를 쓰지 않고
  포트만 닫는다 (disconnect 는 기본으로 토크를 끄는 쓰기를 함).
- 종료 코드: 0 = 계속, 1 = 중단
"""

import argparse
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from lerobot.robots.so_follower import SOFollower, SOFollowerRobotConfig

DATASET = Path.home() / "so101_runs/practice/practice_10/dataset"
JOINTS = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]

ap = argparse.ArgumentParser()
ap.add_argument("--port", default="/dev/so101_follower")
ap.add_argument("--id", default="my_arm")
ap.add_argument("--tol", type=float, default=10.0, help="학습 시작 자세 범위에서 벗어나도 되는 정도 (°)")
ap.add_argument("--yes", action="store_true", help="묻지 않고 결과만 출력")
ap.add_argument("--out", type=Path, help="출력 내용을 이 파일에도 저장")
args = ap.parse_args()

df = pd.concat(pd.read_parquet(f, columns=["episode_index", "frame_index", "observation.state"])
               for f in glob.glob(str(DATASET / "data/*/*.parquet")))
starts = np.stack(df.sort_values("frame_index").groupby("episode_index").first()["observation.state"].to_numpy())
lo, hi, mean = starts.min(0), starts.max(0), starts.mean(0)

robot = SOFollower(SOFollowerRobotConfig(port=args.port, id=args.id, use_degrees=True))
bus = robot.bus
bus.connect()  # openPort + handshake(ping, 펌웨어 읽기)
try:
    pos = bus.sync_read("Present_Position")
finally:
    bus.port_handler.closePort()  # 토크는 그대로 둠

lines = []


def say(msg=""):
    print(msg, flush=True)
    lines.append(msg)
    if args.out:
        args.out.write_text("\n".join(lines) + "\n")


say(f"{'joint':14s} {'지금':>8s} {'학습 시작 평균':>14s} {'학습 범위':>16s}  판정")
bad = []
for i, j in enumerate(JOINTS):
    v = float(pos[j])
    off = max(lo[i] - v, v - hi[i], 0.0)
    ok = off <= args.tol
    if not ok:
        bad.append(j)
    say(f"{j:14s} {v:8.1f} {mean[i]:14.1f} {lo[i]:7.1f} ~ {hi[i]:6.1f}  {'OK' if ok else f'벗어남 {off:.0f}°'}")

if not bad:
    say("시작 자세 OK")
    sys.exit(0)
say(f"\n⚠ 학습 데이터 시작 자세와 다름: {', '.join(bad)}. 팔을 녹화 때 시작 자세(접힌 자세)로 옮긴 뒤 실행하는 걸 권장.")
if args.yes:
    sys.exit(0)
try:
    ans = input("그래도 계속할까요? [y/N] ").strip().lower()
except EOFError:
    ans = ""
say(f"답: {ans or '(없음)'}")
sys.exit(0 if ans == "y" else 1)
