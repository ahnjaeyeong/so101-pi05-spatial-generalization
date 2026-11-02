"""01 데이터 구조 조사 (읽기만 함). 출력: tables/a01_inventory.json, tables/a01_cadence_per_episode.csv, tables/a01_video_sync_sample.csv

- 파일 · 스키마 · dtype · 단위 (코드 근거는 json 'code_refs')
- timestamp 간격 · frame_index 연속 · NaN · 영상 구간 길이 = 데이터 프레임 수
- 녹화 로그 (record_ui sidecar) 의 판별 실제 주기 (Cadence 줄) → d2 episode 에 연결
- 영상 표본 해독 (16편 × 2 카메라): 해독 프레임 수, 연속 같은 프레임 (차이 < 0.5/255) 비율 — 팔이 움직이는 동안만
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python a01_inventory.py
"""
import glob
import json
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import ac

SIDE = Path.home() / ".local/state/record_ui"
CAD_RE = re.compile(r"Cadence \(episode (\d+)\): ([\d.]+) Hz vs 30 Hz target · (\d+) ticks, ([\d.]+) s measured · (\d+)/(\d+) ticks over the "
                    r"33.3 ms budget \(work mean ([\d.]+) ms, worst ([\d.]+) ms\)")


def cadence(T, lens):
    """세션 원본 ep → Cadence. 같은 세션의 여러 실행 중 마지막에 저장된 것 (재녹화 없음: 세션 ep 번호는 실행마다 이어짐)."""
    rows = []
    for js in sorted(SIDE.glob("record_2026102[23]_*.json")):
        d = json.load(open(js))
        sess = d["session"].split("/")[-1]
        if not d["session"].startswith("main_k8/"):
            continue
        log = Path(d["log"])
        if not log.exists():
            continue
        txt = log.read_text(errors="replace")
        rs = {}
        for k in ("max_relative_target", "position_p_coefficient", "position_i_coefficient", "position_d_coefficient", "use_degrees"):
            m = re.search(rf"'{k}': ([^,\n}}]+)", txt)
            rs[k] = m.group(1).strip() if m else None
        for m in CAD_RE.finditer(txt):
            rows.append(dict(session=sess, run=d["run_id"], src_ep=int(m.group(1)), hz=float(m.group(2)), ticks=int(m.group(3)),
                             measured_s=float(m.group(4)), over_budget=int(m.group(5)), n_intervals=int(m.group(6)),
                             work_mean_ms=float(m.group(7)), work_worst_ms=float(m.group(8)), **{f"cfg_{k}": v for k, v in rs.items()}))
    Cd = pd.DataFrame(rows)
    M = T[["ep", "group", "session", "src_ep"]].merge(Cd, on=["session", "src_ep"], how="left")
    M["length"] = M.ep.map(lens)
    M["ticks_eq_length"] = M.ticks == M.length
    return M


def video_sample(data, E, eps):
    import av  # noqa: F401
    import record_ui
    info, meta, cams = record_ui.load_meta(str(ac.DS))
    rows = []
    for e in eps:
        s = data[e][0]
        n = len(s)
        sp = np.r_[0, np.abs(np.diff(s[:, :5], axis=0)).max(1) * ac.FPS]   # °/s, 관절 5개 중 최대
        for cam in cams:
            row = meta[meta.episode_index == e].iloc[0]
            t0 = float(row[f"videos/{cam}/from_timestamp"])
            t1 = float(row[f"videos/{cam}/to_timestamp"])
            fr = list(record_ui.iter_frames(record_ui.video_path(str(ac.DS), info, cam, row), t0, t1, info["fps"]))
            small = np.stack([f[::8, ::8].astype(np.float32) for f in fr])
            d = np.abs(np.diff(small, axis=0)).mean((1, 2, 3))
            m = min(len(d), n - 1)
            moving = sp[1:m + 1] > 20
            rows.append(dict(ep=e, group=E.loc[e, "group"], cam=cam.split(".")[-1], n_data=n, n_decoded=len(fr),
                             frames_moving=int(moving.sum()), dup_moving=int(((d[:m] < 0.5) & moving).sum()),
                             exact_moving=int(((d[:m] < 0.05) & moving).sum()), exact_all=int((d < 0.05).sum()),
                             d_moving_p05=float(np.percentile(d[:m][moving], 5)) if moving.any() else None,
                             dup_all=int((d < 0.5).sum()), diff_median=float(np.median(d))))
            print(e, cam, len(fr), n, rows[-1]["dup_moving"], flush=True)
    return pd.DataFrame(rows)


def main():
    out = {}
    data = ac.load_d2()
    T = ac.cube_table()
    meta = ac.episodes_meta()
    info = json.load(open(ac.DS / "meta/info.json"))
    out["files"] = {str(Path(p).relative_to(ac.DS)): os.path.getsize(p) for p in sorted(glob.glob(str(ac.DS / "**/*"), recursive=True)) if os.path.isfile(p)}
    out["info"] = dict(codebase_version=info["codebase_version"], fps=info["fps"], total_episodes=info["total_episodes"], total_frames=info["total_frames"],
                       robot_type=info["robot_type"], features={k: dict(dtype=v["dtype"], shape=v["shape"], names=v.get("names")) for k, v in info["features"].items()},
                       video=info["features"]["observation.images.front"]["info"])
    # timestamp · frame_index · NaN
    gaps, nonc, nan_s, nan_a, ts_frame = [], 0, 0, 0, []
    for e, (s, a, ts, fi, ix) in data.items():
        dt = np.diff(ts)
        gaps.append((dt.min(), dt.max()))
        nonc += int((np.diff(fi) != 1).sum()) + int(fi[0] != 0)
        nan_s += int(np.isnan(s).sum())
        nan_a += int(np.isnan(a).sum())
        ts_frame.append(float(np.abs(ts - fi / ac.FPS).max()))
    g = np.array(gaps)
    out["timestamp"] = dict(dt_min=float(g[:, 0].min()), dt_max=float(g[:, 1].max()), frame_index_noncontiguous=nonc,
                            max_abs_ts_minus_frameidx_over_fps=float(max(ts_frame)), nan_state=nan_s, nan_action=nan_a)
    # 영상 구간 길이
    vd = []
    for _, r in meta.iterrows():
        n = int(r["length"])
        for cam in ("front", "wrist"):
            span = (r[f"videos/observation.images.{cam}/to_timestamp"] - r[f"videos/observation.images.{cam}/from_timestamp"]) * ac.FPS
            vd.append(abs(span - n))
    out["video_span_minus_length_frames_max"] = float(max(vd))
    lens = {e: len(v[0]) for e, v in data.items()}
    # 값의 해상도 (서보 1 tick = 360/4096°?)
    s_all = np.concatenate([v[0] for v in data.values()])
    a_all = np.concatenate([v[1] for v in data.values()])
    res = {}
    for j, nm in enumerate(ac.JOINTS):
        u = np.unique(np.round(s_all[:, j], 5))
        res[nm] = dict(state_min_step=float(np.min(np.diff(u))) if len(u) > 1 else None, n_unique_state=int(len(u)),
                       state_min=float(s_all[:, j].min()), state_max=float(s_all[:, j].max()),
                       action_min=float(a_all[:, j].min()), action_max=float(a_all[:, j].max()))
    out["value_resolution"] = res
    # 녹화 주기
    M = cadence(T, lens)
    M.to_csv(ac.TAB / "a01_cadence_per_episode.csv", index=False)
    ok = M.hz.notna()
    out["cadence"] = dict(n_matched=int(ok.sum()), ticks_eq_length=int(M.ticks_eq_length.sum()), hz_min=float(M.hz.min()), hz_max=float(M.hz.max()),
                          hz_median=float(M.hz.median()), over_budget_total=int(M.over_budget.sum()), intervals_total=int(M.n_intervals.sum()),
                          eps_with_over_budget=int((M.over_budget > 0).sum()), work_worst_ms_max=float(M.work_worst_ms.max()),
                          work_mean_ms_median=float(M.work_mean_ms.median()),
                          robot_cfg={k: sorted(M[k].dropna().unique().tolist()) for k in M.columns if k.startswith("cfg_")})
    # 캘리브레이션 파일
    cal = {}
    for p in [Path.home() / ".cache/huggingface/lerobot/calibration/robots/so_follower/my_arm.json",
              Path.home() / ".cache/huggingface/lerobot/calibration/teleoperators/so_leader/my_leader.json"]:
        cal[p.name] = dict(path=str(p), mtime=pd.Timestamp(os.path.getmtime(p), unit="s").isoformat(), content=json.load(open(p)))
    out["calibration"] = cal
    # 영상 표본
    rs = np.random.default_rng(0)
    eps = []
    for grp in ("T1K", "T1R", "T3K", "T3R"):
        eps += sorted(rs.choice(T.index[T.group == grp].values, 4, replace=False).tolist())
    V = video_sample(data, T, eps)
    V.to_csv(ac.TAB / "a01_video_sync_sample.csv", index=False)
    out["video_sample"] = dict(eps=eps, decoded_eq_data=int((V.n_decoded == V.n_data).sum()), n=len(V),
                               dup_moving_total=int(V.dup_moving.sum()), exact_moving_total=int(V.exact_moving.sum()),
                               exact_moving_by_cam=V.groupby("cam").exact_moving.sum().astype(int).to_dict(), frames_moving_total=int(V.frames_moving.sum()),
                               dup_moving_by_cam=V.groupby("cam").apply(lambda d: [int(d.dup_moving.sum()), int(d.frames_moving.sum())]).to_dict())
    # 큐브 표
    out["cube_table"] = dict(n=len(T), cube_xy_found=int(T.cube_x.notna().sum()), yaw_measured=int(T.yaw_meas.notna().sum()),
                             yaw_measured_by_group=T.groupby("group").yaw_meas.apply(lambda s: int(s.notna().sum())).to_dict(),
                             wrist_need_qa=int(T.wrist_need_qa.notna().sum()))
    T.to_csv(ac.TAB / "a01_cube_table.csv", index=False)
    json.dump(out, open(ac.TAB / "a01_inventory.json", "w"), indent=1, ensure_ascii=False, default=str)
    print(json.dumps({k: v for k, v in out.items() if k not in ("files", "calibration", "value_resolution")}, indent=1, ensure_ascii=False, default=str)[:4000])


if __name__ == "__main__":
    sys.path.insert(0, str(Path.home() / "so101_boxpick/scripts"))
    main()
