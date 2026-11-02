"""레퍼런스(aswinkumar99) vs 우리 d2 사람 시연: 파지 직전 좌우(pan) 교정 동작 비교 — 관절 데이터만 (영상·GPU 안 씀).

파지 이벤트 = 팔로워 그리퍼 닫힘 (d2 diag common.close_events). 단일 물체 과제는 첫 닫힘만, 레퍼런스 T2(스펀지 여러 개)는 모든 닫힘.
닫힘 프레임 c 기준 지표 (state = 팔로워, action = 리더):
  net1s       |pan(c) − pan(c−30)|                      마지막 1 s 동안 pan 순변화 (°)
  path1s      Σ|Δpan| (c−30 … c)                        마지막 1 s pan 이동 거리 (왕복 포함)
  path05s     Σ|Δpan| (c−15 … c)
  settle_s    pan 이 최종값 ±2° 안에 계속 머문 시간 (c 에서 거꾸로, 그 구간 시작까지)
  done_1s     (pan(c−30) − pan(seg0)) / (pan(c) − pan(seg0))  — 이 구간 pan 회전 중 1 s 전까지 끝난 비율 (회전 > 10° 인 이벤트만)
  rev15       c−45 … c 에서 pan 속도(3프레임 평균) 부호 바뀜 횟수 (|v| > 0.15 °/프레임 인 점만)
  lead1s      mean |action pan − state pan| (c−30 … c)     리더가 팔로워보다 앞선 정도
  roll_path1s Σ|Δwrist_roll| (c−30 … c)
  speed_c     팔 5관절 속도 노름 평균 (c−5 … c, °/s)
  lat_path1s_cm ≈ path1s × r × π/180, r = FK(so101_new_calib.urdf) 집게 끝 수평 거리 (캘리브레이션 규약 차 ±약 4 cm → 근사)
구간 시작 seg0 = 앞 이벤트 뒤 그리퍼가 다시 열린 프레임 (첫 이벤트는 움직이기 시작한 프레임).
출력: demo_kinematics_events.csv, demo_kinematics_summary.csv
사용: PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python demo_kinematics.py
"""
import glob
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HOME = Path.home()
sys.path.insert(0, str(HOME / "so101_runs/main_k8/d2/diag_grasp_bias"))
import common as C  # noqa: E402

OUT = Path(__file__).resolve().parent
REF = HOME / "so101_runs/reference/aswinkumar99_so101_pick_place"


def load(ds):
    files = sorted(glob.glob(str(Path(ds) / "data/*/*.parquet")))
    df = pd.concat([pd.read_parquet(f, columns=["episode_index", "frame_index", "action", "observation.state"]) for f in files])
    out = {}
    for e, g in df.groupby("episode_index"):
        g = g.sort_values("frame_index")
        out[int(e)] = (np.stack(g["observation.state"].values).astype(float), np.stack(g["action"].values).astype(float))
    return out


def move_start(a, thr=2.0):
    mv = np.where(np.abs(a[:, :5] - a[0, :5]).max(1) > thr)[0]
    return int(mv[0]) if len(mv) else 0


def events(s, a, multi):
    ev = C.close_events(s[:, 5])
    if not ev:
        return []
    if not multi:
        f = C.first_grasp(s[:, 5])
        ev = [f] if f is not None else ev[:1]
    out, seg0 = [], move_start(a)
    for k, c in enumerate(ev):
        out.append((k, seg0, c))
        # 다음 구간 시작: c 뒤 그리퍼가 닫힌 바닥에서 15 이상 다시 열린 첫 프레임
        g = s[:, 5]
        j = c
        while j < len(g) - 1 and g[j] < g[c] + 15:
            j += 1
        seg0 = j
    return out


def metrics(s, a, k, seg0, c):
    import fk
    if c < 46:
        return None
    pan = s[:, 0]
    r = {}
    r["net1s"] = abs(pan[c] - pan[c - 30])
    r["path1s"] = np.abs(np.diff(pan[c - 30: c + 1])).sum()
    r["path05s"] = np.abs(np.diff(pan[c - 15: c + 1])).sum()
    j = c
    while j > seg0 and abs(pan[j] - pan[c]) <= 2.0:
        j -= 1
    r["settle_s"] = (c - j) / 30
    rot = pan[c] - pan[seg0]
    r["seg_rot"] = rot
    r["done_1s"] = (pan[c - 30] - pan[seg0]) / rot if abs(rot) > 10 and c - 30 > seg0 else np.nan
    v = np.convolve(np.diff(pan[c - 45: c + 1]), np.ones(3) / 3, mode="valid")
    v = v[np.abs(v) > 0.15]
    r["rev15"] = int((np.diff(np.sign(v)) != 0).sum())
    r["lead1s"] = np.abs(a[c - 30: c + 1, 0] - pan[c - 30: c + 1]).mean()
    r["roll_path1s"] = np.abs(np.diff(s[c - 30: c + 1, 4])).sum()
    r["speed_c"] = np.linalg.norm(np.diff(s[c - 5: c + 1, :5], axis=0), axis=1).mean() * 30
    p, _ = fk.fk(s[[c], :5])
    rr = math.hypot(p[0, 0], p[0, 1]) * 100
    r["r_cm"] = rr
    r["lat_path1s_cm"] = r["path1s"] * rr * math.pi / 180
    r["lat_net1s_cm"] = r["net1s"] * rr * math.pi / 180
    r["event"], r["seg_len_s"] = k, (c - seg0) / 30
    return r


def main():
    groups = []
    d2 = load(C.D2 / "dataset")
    for e, (s, a) in d2.items():
        grp = ["T1K", "T1R", "T3K", "T3R"][e // 64]
        groups.append(("ours_d2", grp, e, s, a, False))
    for task, multi in (("task1-single-sponge-no-distractors", False), ("task2-multiple-sponges-no-distractors", True),
                        ("task3-single-sponge-with-distractors", False)):
        for split, tag in (("fixed-locations", "K"), ("random-locations", "R")):
            dd = load(REF / task / split)
            for e, (s, a) in dd.items():
                groups.append(("ref", f"T{task[4]}{tag}", e, s, a, multi))
    rows = []
    for src, grp, e, s, a, multi in groups:
        for k, seg0, c in events(s, a, multi):
            m = metrics(s, a, k, seg0, c)
            if m:
                rows.append(dict(src=src, group=grp, ep=e, frame=c, **m))
    E = pd.DataFrame(rows)
    E.to_csv(OUT / "demo_kinematics_events.csv", index=False)
    cols = ["net1s", "path1s", "path05s", "settle_s", "done_1s", "rev15", "lead1s", "roll_path1s", "speed_c", "r_cm", "lat_path1s_cm", "lat_net1s_cm", "seg_len_s"]
    S = E.groupby(["src", "group"])[cols].median().round(2)
    S.insert(0, "n_events", E.groupby(["src", "group"]).size())
    S.to_csv(OUT / "demo_kinematics_summary.csv")
    pd.set_option("display.width", 250)
    print(S.to_string())
    # 비율 지표
    E["late_lateral_ge2"] = E.net1s >= 2.0
    E["any_rev"] = E.rev15 >= 1
    print(E.groupby(["src", "group"])[["late_lateral_ge2", "any_rev"]].mean().round(2).to_string())
    late_windows(E, {(src, grp, e): (s, a) for src, grp, e, s, a, _ in groups})


def late_windows(E, arrays):
    """마지막 3 s 지표 → demo_roll_late.csv (구간 > 0.5 s), demo_late_direction.csv (구간 > 3.5 s)."""
    r1, r2 = [], []
    for _, r in E.iterrows():
        s, _ = arrays[(r.src, r.group, r.ep)]
        c = int(r.frame)
        seg0 = c - int(round(r.seg_len_s * 30))
        pan = s[:, 0]
        if r.seg_len_s > 0.5:
            w = lambda k: pan[max(seg0, c - k): c + 1]  # noqa: E731
            p3 = w(90)
            r1.append(dict(src=r.src, group=r.group, roll_change=abs(s[c, 4] - s[seg0, 4]), roll_at_c=s[c, 4],
                           net3s=abs(p3[-1] - p3[0]), path3s=np.abs(np.diff(p3)).sum(), net2s=abs(w(60)[-1] - w(60)[0])))
        if r.seg_len_s > 3.5:
            rot, late = pan[c] - pan[seg0], pan[c] - pan[c - 90]
            ok = abs(late) >= 1 and abs(rot) > 5
            v = np.convolve(np.diff(pan[c - 90: c + 1]), np.ones(3) / 3, mode="valid")
            v = v[np.abs(v) > 0.15]
            r2.append(dict(src=r.src, group=r.group, late=abs(late), same_dir=(np.sign(late) == np.sign(rot)) if ok else np.nan,
                           opp_dir=(np.sign(late) != np.sign(rot)) if ok else np.nan, rev3s=int((np.diff(np.sign(v)) != 0).sum())))
    X, Y = pd.DataFrame(r1), pd.DataFrame(r2)
    X.to_csv(OUT / "demo_roll_late.csv", index=False)
    Y.to_csv(OUT / "demo_late_direction.csv", index=False)
    print(X.groupby(["src", "group"]).agg(n=("net3s", "size"), roll_change_med=("roll_change", "median"), roll_c_sd=("roll_at_c", "std"),
                                         net3s_med=("net3s", "median"), path3s_med=("path3s", "median"),
                                         frac_net2s_ge2=("net2s", lambda v: (v >= 2).mean()),
                                         frac_net3s_ge3=("net3s", lambda v: (v >= 3).mean())).round(2).to_string())
    print(Y.groupby(["src", "group"]).agg(n=("late", "size"), late_ge1=("late", lambda v: (v >= 1).mean()), same_dir=("same_dir", "mean"),
                                         opp_dir=("opp_dir", "mean"), rev3s_ge1=("rev3s", lambda v: (v >= 1).mean())).round(2).to_string())


if __name__ == "__main__":
    main()
