#!/home/user/so101-env/bin/python
"""sg_phase.analyze 합성 궤적 시험 (dataset · 로봇 없음).  PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python tests/test_sg_phase.py"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import sg_phase  # noqa: E402

FPS = 30


def traj(open_at, reach=(2.0, 5.0), pan=(0.5, 1.5), close_at=9.0, descend=True, reopen=False, n=14.0):
    t = np.arange(int(n * FPS)) / FPS
    st = np.zeros((len(t), 6))
    st[:, 0] = np.interp(t, pan, [0, 60])
    st[:, 1] = np.interp(t, reach, [-100, -20]) + (np.interp(t, [open_at + 0.5, close_at - 0.5], [0, 20]) if descend else 0)
    st[:, 2] = np.interp(t, reach, [95, 40])
    st[:, 3] = 75
    a = np.ones(len(t))
    a[(t >= open_at) & (t < close_at)] = 35
    a[(t >= close_at)] = 8
    a[(t >= 11.5) & (t < 12)] = 30  # 상자에 놓기
    a[t >= 12] = 1
    if reopen:
        a[(t >= close_at + 0.5) & (t < close_at + 1.0)] = 35
    st[:, 5] = a
    return st, np.column_stack([st[:, :5], a])


def main():
    res = []

    def ok(t):
        res.append(t)
    r = sg_phase.analyze(*traj(open_at=6.0), FPS)
    assert r["flags"] == [] and r["open_events"] == 2 and abs(r["open_s"] - 6.0) < 0.05 and r["open_stage"] == "팔 뻗은 뒤", r
    ok("팔 뻗고 멈춘 뒤 열림 (예비1 방식): 표시 없음 · 열린 단계 '팔 뻗은 뒤' · 열림 2 번")
    r = sg_phase.analyze(*traj(open_at=1.8, reach=(3.0, 6.0)), FPS)
    assert r["flags"] == [] and r["open_stage"].startswith("찾기"), r
    ok("Pan 정렬 끝 · 큰 팔 뻗기 전 열림 (예비2 방식): 표시 없음 · 열린 단계 '찾기'")
    r = sg_phase.analyze(*traj(open_at=3.5), FPS)
    assert any("움직이는 중에 열림" in f for f in r["flags"]), r
    ok("팔 뻗는 중에 열림 → '팔이 움직이는 중에 열림'")
    r = sg_phase.analyze(*traj(open_at=1.0), FPS)
    assert r["flags"] == [] and r["open_stage"].startswith("찾기"), r
    ok("숄더팬 정렬 중 · 직후 열림 (2026-11-06 순서: 팬 → 열기 → 찾기 → 이동) → 표시 없음 · 열린 단계 '찾기'")
    r = sg_phase.analyze(*traj(open_at=6.0, reopen=True), FPS)
    assert any("다시 열림" in f for f in r["flags"]), r
    ok("닫은 뒤 다시 열림 → '다시 열림 (열림 3 번)'")
    st, ac = traj(open_at=6.0)
    ac[:, 5] = 1
    r = sg_phase.analyze(st, ac, FPS)
    assert r["flags"] == ["그리퍼 열림 없음"], r
    ok("그리퍼를 안 열면 '그리퍼 열림 없음'")
    for o in res:
        print("  ✓", o)
    print(f"PASS {len(res)} 항목")
    return 0


if __name__ == "__main__":
    sys.exit(main())
