"""09 외부 SO-101 실험 (aswinkumar99, 공개 관절 데이터) vs d2 사람 시연 — 같은 코드 · 같은 지표 (읽기만 함, 관절 parquet 만; 영상 없음)
입력: ~/so101_runs/reference/aswinkumar99_so101_pick_place/task{1,2,3}-*/{fixed,random}-locations (HF 데이터셋과 같음, aswin_task2_compare 확인)
출력 tables/a09_*.csv/json, _facts/09.md

이벤트 = 팔로워 그리퍼 닫힘 (diag common.close_events). 단일 물체 과제 (task1, task3, 우리 d2) = 첫 닫힘만, task2 (스펀지 여러 개) = 모든 닫힘.
구간 시작 seg0 = 첫 이벤트는 onset (리더 2°), 다음 이벤트는 앞 닫힘 뒤 그리퍼가 다시 열린 프레임 (aswin_task2_compare 와 같음).
목표 pan = 닫힘 순간 pan (외부 데이터에는 물체 위치가 없어서 두 쪽 모두 같은 정의).
절대 관절값은 캘리브레이션이 달라 비교하지 않고 SD · 범위 · 시간 지표만 비교한다.
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python a09_reference_compare.py
"""
import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd

import ac

REF = Path.home() / "so101_runs/reference/aswinkumar99_so101_pick_place"


def load(ds):
    files = sorted(glob.glob(str(Path(ds) / "data/*/*.parquet")))
    df = pd.concat([pd.read_parquet(f, columns=["episode_index", "frame_index", "action", "observation.state"]) for f in files])
    out = {}
    for e, g in df.groupby("episode_index"):
        g = g.sort_values("frame_index")
        out[int(e)] = (np.stack(g["observation.state"].values).astype(float), np.stack(g["action"].values).astype(float))
    return out


def events(s, a, multi):
    g = s[:, 5]
    cev = ac.C.close_events(g)
    if not cev:
        return []
    cev = cev if multi else cev[:1]
    on = ac.onset(a[:, :5], 2.0) or 0
    segs = []
    prev = None
    for k, c in enumerate(cev):
        if k == 0:
            s0 = on
        else:
            bottom = g[prev:c].min() if c > prev else g[prev]
            op = np.where(g[prev:c] >= bottom + 8)[0]
            s0 = prev + int(op[0]) if len(op) else prev
        if c - s0 >= 15:
            segs.append((k, s0, c))
        prev = c
    return segs


def metrics(s, s0, c):
    pan, roll = s[:, 0], s[:, 4]
    need = pan[c] - pan[s0]
    r = dict(seg_s=(c - s0) / ac.FPS, pan_need=need, roll_change=roll[c] - roll[s0])
    if abs(need) >= 5:
        frac = (pan[s0:c + 1] - pan[s0]) / need
        for kk in (0.5, 0.9):
            i = np.where(frac >= kk)[0]
            r[f"pan_t{int(kk * 100)}_s"] = i[0] / ac.FPS if len(i) else np.nan
    else:
        r["pan_t50_s"] = r["pan_t90_s"] = np.nan
    r["pan_reach2_frac"] = (ac.first_reach_index(pan, c, 2, s0) - s0) / max(1, c - s0)
    r["pan_settle2_before_s"] = (c - ac.settle_index(pan, c, 2, s0)) / ac.FPS
    for sec in (5, 3, 1):
        a = max(s0, c - sec * ac.FPS)
        r[f"pan_net{sec}"] = abs(pan[c] - pan[a])
        r[f"pan_path{sec}"] = float(np.abs(np.diff(pan[a:c + 1])).sum())
        r[f"roll_net{sec}"] = abs(roll[c] - roll[a])
        for j, nm in ((1, "lift"), (2, "elbow"), (3, "wflex")):
            r[f"{nm}_net{sec}"] = abs(s[c, j] - s[a, j])
    r["roll_settle2_before_s"] = (c - ac.settle_index(roll, c, 2, s0)) / ac.FPS
    return r


def main():
    sets = []
    for tdir, tname in (("task1-single-sponge-no-distractors", "ref T1"), ("task2-multiple-sponges-no-distractors", "ref T2"),
                        ("task3-single-sponge-with-distractors", "ref T3")):
        for loc, ln in (("fixed-locations", "K"), ("random-locations", "R")):
            p = REF / tdir / loc
            if p.exists():
                sets.append((f"{tname}{ln}", p, tname == "ref T2"))
    rows, starts = [], []
    for name, p, multi in sets:
        D = load(p)
        for e, (s, a) in D.items():
            starts.append(dict(set=name, ep=e, **{f"s0_{j}": s[0, i] for i, j in enumerate(ac.JOINTS)}))
            for k, s0, c in events(s, a, multi):
                rows.append(dict(set=name, ep=e, event=k, **{f"seg0_{j}": s[s0, i] for i, j in enumerate(ac.JOINTS)},
                                 **{f"c_{j}": s[c, i] for i, j in enumerate(ac.JOINTS)}, **metrics(s, s0, c)))
    # 우리 d2
    data = ac.load_d2()
    E = pd.read_csv(ac.TAB / "a02_events.csv")
    for e in range(256):
        s, a = data[e][0], data[e][1]
        nm = f"d2 {E.group[e][:2]}{E.group[e][2]}"
        starts.append(dict(set=nm, ep=e, **{f"s0_{j}": s[0, i] for i, j in enumerate(ac.JOINTS)}))
        s0, c = int(E.onset[e]), int(E.grasp[e])
        rows.append(dict(set=nm, ep=e, event=0, **{f"seg0_{j}": s[s0, i] for i, j in enumerate(ac.JOINTS)},
                         **{f"c_{j}": s[c, i] for i, j in enumerate(ac.JOINTS)}, **metrics(s, s0, c)))
    R = pd.DataFrame(rows)
    S = pd.DataFrame(starts)
    R.to_csv(ac.TAB / "a09_events.csv", index=False)
    S.to_csv(ac.TAB / "a09_starts.csv", index=False)
    order = [n for n, _, _ in sets] + ["d2 T1K", "d2 T1R", "d2 T3K", "d2 T3R"]
    # 1. 판 시작 상태 SD
    st = S.groupby("set")[[f"s0_{j}" for j in ac.J5]].std().reindex(order)
    st.columns = [c[3:] for c in st.columns]
    st.insert(0, "n_eps", S.groupby("set").size().reindex(order))
    # 2. 접근 구간 시작 상태 SD (task2 는 두 번째 이후 이벤트가 앞 파지 뒤에서 시작)
    sg = R.groupby("set")[[f"seg0_{j}" for j in ac.J5]].std().reindex(order)
    sg.columns = [c[5:] for c in sg.columns]
    sg.insert(0, "n_events", R.groupby("set").size().reindex(order))
    # 3. 닫힘 순간 SD (물체 위치 분포의 관절 대리값)
    cg = R.groupby("set")[[f"c_{j}" for j in ac.J5]].agg(["std", lambda x: x.max() - x.min()]).reindex(order)
    cg.columns = [f"{a[2:]}_{'sd' if b == 'std' else 'range'}" for a, b in cg.columns]
    # 4. 시간 지표 (중앙값)
    keys = ["seg_s", "pan_t50_s", "pan_t90_s", "pan_reach2_frac", "pan_settle2_before_s", "roll_settle2_before_s", "pan_net3", "pan_path3", "pan_net1",
            "roll_net5", "roll_net3", "lift_net3", "elbow_net3", "wflex_net3"]
    tm = R.groupby("set")[keys].median().reindex(order)
    tm.insert(0, "n", R.groupby("set").size().reindex(order))
    rc = R.assign(abs_roll=R.roll_change.abs()).groupby("set").agg(abs_roll_change_med=("abs_roll", "median"),
                                                                    abs_roll_gt30=("abs_roll", lambda x: float((x > 30).mean()))).reindex(order)
    out = dict(sets=order)
    json.dump(out, open(ac.TAB / "a09_reference.json", "w"), indent=1)
    t = ["## 측정 사실 (스크립트 생성: `scripts/a09_reference_compare.py`)\n",
         "[SO-101 외부 실험] = aswinkumar99 공개 데이터셋 (로컬 사본 `~/so101_runs/reference/aswinkumar99_so101_pick_place`, 관절 parquet 만, 영상 · 물체 좌표 없음). "
         "[자체 실험] = d2. 두 쪽 모두 같은 스크립트 · 같은 이벤트 정의. 절대 관절값은 캘리브레이션이 달라 비교하지 않는다.\n",
         "### 9.1 판 시작 프레임 관절 SD (°)\n", ac.md_table(st, {"n_eps": "{:.0f}"}, index=True), "\n",
         "### 9.2 접근 구간 시작 상태 SD (°) — 외부 T2 는 앞 파지 · 놓기 뒤 위치에서 다음 접근이 시작\n", ac.md_table(sg, {"n_events": "{:.0f}"}, index=True), "\n",
         "### 9.3 닫힘 순간 관절 SD · 범위 (°) — 물체 위치 분포의 관절 대리값\n", ac.md_table(cg, "{:.1f}", index=True), "\n",
         "### 9.4 접근 시간 지표 (이벤트 중앙값)\n",
         "pan_t50/t90 = 구간 시작 뒤 pan 이 그 이벤트 총회전의 50/90% 를 넘긴 시간 (|총회전| ≥ 5° 이벤트). pan_reach2_frac = 최종 ±2° 에 처음 들어온 시점 / 구간 길이. "
         "*_net3 = 마지막 3 s 순변화 (°).\n", ac.md_table(tm, {"n": "{:.0f}"}, index=True), "\n",
         "### 9.5 wrist roll 변화 (구간 시작 → 닫힘)\n", ac.md_table(rc, {"abs_roll_gt30": "{:.0%}"}, index=True), "\n"]
    ac.write_facts("09.md", "\n".join(t))
    print("\n".join(t))


if __name__ == "__main__":
    main()
