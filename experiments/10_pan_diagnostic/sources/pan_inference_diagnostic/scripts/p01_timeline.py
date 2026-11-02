"""p01 기존 d2 실물 실행 로그 → 틱별 시간축 (읽기만 함, CPU).

입력: d2/eval/rollouts/2026*/ (dataset, debug.log, filter_log.csv 가 있으면)
출력:
  tables/p01_ticks.parquet   — run, ep, frame, wall, chunk_id, chunk_idx, raw_*, out_*, sent_*, clamp_*, state_*
  tables/p01_merges.csv      — chunk 마다 merge 프레임, real_delay(로그), 적용 delay, 추론 지연(로그), 직전 merge 간격
  tables/p01_align.json      — 실행별 대응 방법·정합 잔차
값의 출처 (열 이름 접미사로 구분하지 않고 여기와 03 문서에 적는다):
  raw   = action queue 에서 꺼낸 값 (RTC 이어붙이기 뒤, 필터 전). filt 실행: filter_log raw_*. 필터 없는 실행: dataset action (= 같은 값)
  out   = arm_filter 뒤 (= dataset action)
  sent  = max_relative_target 8° clamp 뒤 실제 Goal_Position. clamp 경고(debug.log)가 있는 틱·관절은 'safe goal_pos', 나머지는 out
  state = 그 틱 시작에 읽은 Present_Position (= dataset observation.state)
대응:
  filt 실행: filter_log 의 cmd 행 j = dataset frame j (값 일치 검사), merge 행의 tick → 다음 cmd 행이 merge 뒤 첫 프레임
  필터 없는 실행: debug.log clamp 경고의 original goal_pos 를 dataset action 과 값으로 맞춰 (프레임, 시각) 기준점을 만들고
                 판마다 시각 = a + b·프레임 직선으로 맞춘 뒤 merge 시각을 프레임으로 바꿈 (잔차는 p01_align.json)
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python p01_timeline.py
"""
import ast
import datetime as dt
import glob
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

D2 = Path.home() / "so101_runs/main_k8/d2"
OUT = D2 / "pan_inference_diagnostic"
TAB = OUT / "tables"
J = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
TS = re.compile(r"^(\d\d):(\d\d):(\d\d)\.(\d{3}) (\w+) (\S+): (.*)$")


def load_ds(run):
    df = pd.concat([pd.read_parquet(f) for f in glob.glob(f"{run}/dataset/data/*/*.parquet")])
    out = {}
    for e, g in df.groupby("episode_index"):
        g = g.sort_values("frame_index")
        out[int(e)] = (np.stack(g["observation.state"].values).astype(float), np.stack(g["action"].values).astype(float))
    return out


def run_date(run):
    m = re.search(r"(\d{8})_\d{6}", run.name)
    return dt.datetime.strptime(m.group(1), "%Y%m%d")


def parse_debug(path, day):
    """debug.log → merge·clamp 사건 (wall = epoch 초, 로컬 시각 기준)."""
    lines = Path(path).read_text(errors="replace").splitlines()
    ev, i = [], 0
    pend = {}
    while i < len(lines):
        m = TS.match(lines[i])
        if not m:
            i += 1
            continue
        hh, mm, ss, ms, lvl, name, msg = m.groups()
        wall = (day + dt.timedelta(hours=int(hh), minutes=int(mm), seconds=int(ss), milliseconds=int(ms))).timestamp()
        if "Relative goal position magnitude" in msg:
            body = []
            i += 1
            while i < len(lines) and not TS.match(lines[i]):
                body.append(lines[i])
                i += 1
            d = ast.literal_eval("\n".join(body))
            ev.append(dict(kind="clamp", wall=wall, clamp={k: (v["original goal_pos"], v["safe goal_pos"]) for k, v in d.items()}))
            continue
        if name.endswith("action_queue"):
            r = re.search(r"Indexes diff is not equal to real delay\. indexes_diff=(\d+), real_delay=(\d+)", msg)
            if r:
                pend["idx_diff"] = int(r.group(1))
            r = re.search(r"real_delay: (\d+), clamped_delay: (\d+)", msg)
            if r:
                pend["real_delay"], pend["clamped_delay"] = int(r.group(1)), int(r.group(2))
        r = re.search(r"RTC inference latency=([\d.]+)s, queue=(\d+)", msg)
        if r:
            ev.append(dict(kind="merge", wall=wall, latency_s=float(r.group(1)), queue_after=int(r.group(2)), **pend))
            pend = {}
        if "Resetting RTC inference state" in msg:
            ev.append(dict(kind="reset", wall=wall))
        i += 1
    return ev


def build_filt(run, ds, dbg):
    L = pd.read_csv(run / "filter_log.csv")
    rows, merges, align = [], [], {}
    clamps = [e for e in dbg if e["kind"] == "clamp"]
    dmerge = [e for e in dbg if e["kind"] == "merge"]
    for epl, g in L.groupby("episode"):
        e = int(epl) - 1
        s, a = ds[e]
        g = g.reset_index(drop=True)
        cmd = g[g.event == "cmd"].reset_index(drop=True)
        assert len(cmd) == len(a), (run.name, e, len(cmd), len(a))
        err = np.abs(cmd[[f"out_{j}" for j in J]].values - a).max()
        err_s = np.abs(cmd[[f"state_{j}" for j in J]].values - s).max()
        align[f"{run.name}/{e}"] = dict(method="filter_log", out_vs_action_max=float(err), state_max=float(err_s))
        cid, cidx, chunk_of, idx_of = -1, 0, [], []
        mrow = []
        for _, r in g.iterrows():
            if r.event.startswith("merge"):
                cid += 1
                rd = int(re.search(r"real_delay=(\d+)", r.event).group(1))
                idd = int(re.search(r"idx_diff=(\d+)", r.event).group(1))
                qb = int(re.search(r"qsize_before=(\d+)", r.event).group(1))
                applied = min(rd, idd)  # action_queue._check_and_resolve_delays
                cidx = applied
                mrow.append(dict(chunk_id=cid, wall=r.wall, real_delay_log=rd, idx_diff=idd, applied_delay=applied, qsize_before=qb))
            elif r.event == "cmd":
                chunk_of.append(cid)
                idx_of.append(cidx)
                cidx += 1
        # merge 프레임 = merge 뒤 첫 cmd 행 번호
        cmd_wall = cmd.wall.values
        M = pd.DataFrame(mrow)
        M["merge_frame"] = np.searchsorted(cmd_wall, M.wall.values)
        # debug.log 의 추론 지연 (시각 최근접, 1 s 안)
        dw = np.array([d["wall"] for d in dmerge])
        lat = []
        for w in M.wall.values:
            k = int(np.argmin(np.abs(dw - w))) if len(dw) else -1
            lat.append(dmerge[k]["latency_s"] if k >= 0 and abs(dw[k] - w) < 1.0 else np.nan)
        M["latency_s"] = lat
        M["run"], M["ep"] = run.name, e
        merges.append(M)
        T = pd.DataFrame(dict(run=run.name, ep=e, frame=np.arange(len(a)), wall=cmd_wall, chunk_id=chunk_of, chunk_idx=idx_of))
        for k, j in enumerate(J):
            T[f"raw_{j}"] = cmd[f"raw_{j}"].values
            T[f"out_{j}"] = a[:, k]
            T[f"sent_{j}"] = a[:, k]
            T[f"clamp_{j}"] = False
            T[f"state_{j}"] = s[:, k]
        apply_clamps(T, clamps, by_wall=True)
        rows.append(T)
    return rows, merges, align


def apply_clamps(T, clamps, by_wall, fit=None):
    """clamp 경고를 프레임에 붙인다. original goal_pos 가 그 프레임 out 과 같아야 한다 (1e-3)."""
    n_ok = n_bad = 0
    out = {j: T[f"out_{j}"].values for j in J}
    w = T.wall.values
    for c in clamps:
        if w[0] - 1 > c["wall"] or c["wall"] > w[-1] + 1:
            continue
        # 후보: 시각 ±0.2 s 안 프레임 중 값이 맞는 것
        cand = np.where(np.abs(w - c["wall"]) < 0.2)[0]
        hit = [f for f in cand if all(abs(out[j][f] - c["clamp"][j][0]) < 1e-3 for j in c["clamp"])]
        if len(hit) != 1:
            n_bad += 1
            continue
        f = hit[0]
        for j, (_, safe) in c["clamp"].items():
            T.loc[T.index[f], f"sent_{j}"] = safe
            T.loc[T.index[f], f"clamp_{j}"] = True
        n_ok += 1
    T.attrs["clamp_matched"], T.attrs["clamp_unmatched"] = n_ok, n_bad


def build_nofilt(run, ds, dbg):
    """필터 없는 실행: clamp 경고 값으로 프레임↔시각 기준점을 만든다."""
    clamps = [e for e in dbg if e["kind"] == "clamp"]
    dmerge = [e for e in dbg if e["kind"] == "merge"]
    rows, merges, align = [], [], {}
    # 판 경계: dataset 판 순서대로, 첫 chunk(queue_after=50) merge 로 시작
    starts = [k for k, d in enumerate(dmerge) if d["queue_after"] == 50]
    for e in sorted(ds):
        s, a = ds[e]
        k0 = starts[e]
        k1 = starts[e + 1] if e + 1 < len(starts) else len(dmerge)
        em = dmerge[k0:k1]
        t0 = em[0]["wall"]
        anchors = []
        for c in clamps:
            if c["wall"] < t0 - 0.5:
                continue
            fr = np.where(np.all([np.abs(a[:, J.index(j)] - v[0]) < 1e-3 for j, v in c["clamp"].items()], axis=0))[0]
            if len(fr) == 1:
                anchors.append((int(fr[0]), c["wall"]))
        anchors = np.array(anchors, float)
        anchors = anchors[anchors[:, 1] <= em[-1]["wall"] + 2.0] if len(anchors) else anchors
        b, a0 = np.polyfit(anchors[:, 0], anchors[:, 1], 1)
        res = anchors[:, 1] - (a0 + b * anchors[:, 0])
        align[f"{run.name}/{e}"] = dict(method="clamp_anchor_linear", n_anchor=len(anchors), s_per_frame=float(b),
                                        resid_ms_p50=float(np.median(np.abs(res)) * 1e3), resid_ms_max=float(np.abs(res).max() * 1e3),
                                        first_merge_to_frame0_s=float(a0 - t0))
        wall = a0 + b * np.arange(len(a))
        M = pd.DataFrame(em)
        M["chunk_id"] = np.arange(len(M))
        M["merge_frame"] = np.ceil((M.wall.values - a0) / b).astype(int).clip(0)
        M.loc[0, "merge_frame"] = 0
        rd = M.get("real_delay", pd.Series([np.nan] * len(M))).values
        cd = M.get("clamped_delay", pd.Series([np.nan] * len(M))).values
        M["real_delay_log"], M["applied_delay"] = rd, cd
        M["run"], M["ep"] = run.name, e
        merges.append(M.drop(columns=[c for c in ("kind", "real_delay", "clamped_delay") if c in M]))
        cid = np.searchsorted(M.merge_frame.values, np.arange(len(a)), side="right") - 1
        cidx = np.array([int(M.applied_delay.values[c]) + f - int(M.merge_frame.values[c]) for f, c in enumerate(cid)])
        T = pd.DataFrame(dict(run=run.name, ep=e, frame=np.arange(len(a)), wall=wall, chunk_id=cid, chunk_idx=cidx))
        for k, j in enumerate(J):
            T[f"raw_{j}"] = a[:, k]
            T[f"out_{j}"] = a[:, k]
            T[f"sent_{j}"] = a[:, k]
            T[f"clamp_{j}"] = False
            T[f"state_{j}"] = s[:, k]
        apply_clamps(T, clamps, by_wall=True)
        rows.append(T)
    return rows, merges, align


def main():
    TAB.mkdir(parents=True, exist_ok=True)
    rows, merges, align = [], [], {}
    for run in sorted(Path(p) for p in glob.glob(str(D2 / "eval/rollouts/2026*"))):
        ds = load_ds(run)
        dbg = parse_debug(run / "debug.log", run_date(run))
        if (run / "filter_log.csv").exists():
            r, m, al = build_filt(run, ds, dbg)
        else:
            r, m, al = build_nofilt(run, ds, dbg)
        for T in r:
            al[f"{run.name}/{int(T.ep.iloc[0])}"].update(clamp_matched=T.attrs.get("clamp_matched"), clamp_unmatched=T.attrs.get("clamp_unmatched"))
        rows += r
        merges += m
        align.update(al)
    T = pd.concat(rows, ignore_index=True)
    M = pd.concat(merges, ignore_index=True)
    M["merge_interval_s"] = M.groupby(["run", "ep"]).wall.diff()
    T.to_parquet(TAB / "p01_ticks.parquet", index=False)
    M.to_csv(TAB / "p01_merges.csv", index=False)
    json.dump(align, open(TAB / "p01_align.json", "w"), indent=1)
    print(T.groupby(["run", "ep"]).size())
    print(json.dumps(align, indent=1))
    print(M.groupby(["run", "ep"]).agg(n=("chunk_id", "size"), lat=("latency_s", "median"), iv=("merge_interval_s", "median"),
                                       d=("applied_delay", "median")))


if __name__ == "__main__":
    main()
