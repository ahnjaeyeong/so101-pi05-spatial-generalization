#!/home/user/so101-env/bin/python
"""d2 사람 시연에서 '닫기 시작한 순간' 손목 영상의 큐브 위치를 재서 닫기 영역을 만든다 (dataset 읽기만).

  PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python r12_wrist_zone.py [--dataset ~/so101_runs/main_k8/d2/dataset]
출력: config/r12_wrist_zone.json (영역 p10–p90 · p5–p95, 판별 값), 표준 출력에 요약.
닫기 시작 = 처음 열린 뒤(명령 그리퍼 >15) 명령 그리퍼가 처음 <10 이 되는 프레임에서 거꾸로, 명령이 계속 줄어들던 첫 프레임.
방향: 그 1 s 전 프레임의 손목 큐브 dx 와 (그때 pan − 닫을 때 pan) 의 상관·기울기로 '화면 좌우 ↔ pan 부호' 를 잰다.
"""

import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.expanduser("~/so101_boxpick/scripts"))
import r12_common as rc  # noqa: E402

OUT = os.path.join(os.path.dirname(HERE), "config", "r12_wrist_zone.json")


def close_onset(A):
    op = np.where(A[:, 5] > 15)[0]
    if not len(op):
        return None
    j = next((i for i in range(op[0], len(A)) if A[i, 5] < 10), None)
    if j is None:
        return None
    k = j
    while k - 1 > op[0] and A[k - 1, 5] > A[k, 5] + 0.3:
        k -= 1
    return k


def main():
    import glob

    import pandas as pd
    import record_ui as ru

    ds = os.path.expanduser(sys.argv[sys.argv.index("--dataset") + 1]) if "--dataset" in sys.argv else \
        os.path.expanduser("~/so101_runs/main_k8/d2/dataset")
    cfg = rc.load_config()
    info, eps, cams = ru.load_meta(ds)
    cam = next(c for c in cams if c.endswith(".wrist"))
    data = pd.concat([pd.read_parquet(f, columns=["observation.state", "action", "episode_index", "frame_index"])
                      for f in sorted(glob.glob(os.path.join(ds, "data", "*", "*.parquet")))])
    fps = info["fps"]
    rows = []
    for _, er in eps.iterrows():
        e = int(er["episode_index"])
        d = data[data.episode_index == e].sort_values("frame_index")
        A = np.stack(d["action"].values).astype(float)
        S = np.stack(d["observation.state"].values).astype(float)
        k = close_onset(A)
        if k is None or k < 31:
            continue
        p = ru.video_path(ds, info, cam, er)
        t0 = float(er[f"videos/{cam}/from_timestamp"])
        got = {}
        for idx in (k, k - 30):
            for f in ru.iter_frames(p, t0 + idx / fps, t0 + idx / fps + 0.5 / fps + 1e-3, fps):
                got[idx] = f
                break
        if k not in got:
            continue
        h, w = got[k].shape[:2]
        b = rc.find_red(got[k], cfg, min_area=150)
        r = {"ep": e, "k": k, "t_close_s": round(k / fps, 2), "pan_close": S[k, 0], "grip_open": float(A[:k, 5].max())}
        if b:
            a, cx, cy, bb = b[0]
            r.update(u=cx / w, v=cy / h, area=a / (w * h), edge=bool(bb[0] <= 2 or bb[1] <= 2 or bb[0] + bb[2] >= w - 2 or bb[1] + bb[3] >= h - 2))
        if k - 30 in got:
            b2 = rc.find_red(got[k - 30], cfg, min_area=150)
            if b2:
                r.update(u_1s=b2[0][1] / w, v_1s=b2[0][2] / h, area_1s=b2[0][0] / (w * h), dpan_1s=S[k - 30, 0] - S[k, 0])
        rows.append(r)
    df = pd.DataFrame(rows)
    det = df.dropna(subset=["u"])
    q = lambda c, a, b: [round(float(np.percentile(det[c], a)), 3), round(float(np.percentile(det[c], b)), 3)]  # noqa: E731
    out = {"source": ds.replace(os.path.expanduser("~"), "~"), "made": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
           "definition": "닫기 시작 프레임의 손목 영상 빨강 큐브 중심 (u = x/640, v = y/480), 넓이 = px/(640·480)",
           "n_episodes": int(len(eps)), "n_close": int(len(df)), "n_detected": int(len(det)),
           "u_p10_p90": q("u", 10, 90), "v_p10_p90": q("v", 10, 90), "area_p10_p90": q("area", 10, 90),
           "u_p5_p95": q("u", 5, 95), "v_p5_p95": q("v", 5, 95), "area_p5_p95": q("area", 5, 95),
           "u_median": round(float(det.u.median()), 3), "v_median": round(float(det.v.median()), 3),
           "area_median": round(float(det.area.median()), 4), "edge_share": round(float(det.edge.mean()), 3)}
    main_ = det[det.area > 0.08]  # 주 덩어리 (닫기 시작 때 큐브가 가까이 크게 보임). 나머지는 늦은·두 번째 닫기가 많음
    # 2026-10-30: 축마다 p10–p90 이면 사람 시연 t1_known 의 52% 만 영역 안 → 주 덩어리 p2.5–p97.5 (주 덩어리 90%, 전체 77%)
    zu = [round(float(np.percentile(main_.u, 2.5)), 3), round(float(np.percentile(main_.u, 97.5)), 3)]
    zv = [round(float(np.percentile(main_.v, 2.5)), 3), round(float(np.percentile(main_.v, 97.5)), 3)]
    inside = (det.u.between(*zu)) & (det.v.between(*zv)) & (det.area >= 0.08)
    out["close_zone"] = {"rule": "area > 0.08 인 판 (주 덩어리)의 u·v p2.5–p97.5, area 최소 0.08",
                         "n": int(len(main_)), "share": round(len(main_) / len(det), 3), "u": zu, "v": zv, "area_min": 0.08,
                         "coverage": {"main": round(float(inside[det.area > 0.08].mean()), 3), "all": round(float(inside.mean()), 3)},
                         "t_close_median_s": {"main": round(float(main_.t_close_s.median()), 2),
                                              "rest": round(float(det[det.area <= 0.08].t_close_s.median()), 2)}}
    m = df.dropna(subset=["u_1s", "dpan_1s"])
    m = m[(m.dpan_1s.abs() > 1.0)]
    if len(m) >= 10:
        slope = float(np.polyfit(m.dpan_1s, m.u_1s - m.u.fillna(m.u_1s), 1)[0])
        out["pan_vs_u_1s_before"] = {"n": int(len(m)), "corr": round(float(np.corrcoef(m.dpan_1s, m.u_1s - m.u.fillna(m.u_1s))[0, 1]), 3),
                                     "slope_u_per_deg": round(slope, 4),
                                     "meaning": "닫기 1 s 전 pan 이 닫을 때보다 +1° 면 손목 화면 큐브 u 가 slope 만큼 이동"}
    a1 = df.dropna(subset=["area_1s", "v_1s", "area"])
    out["v_vs_area_1s_before"] = {"n": int(len(a1)), "corr": round(float(np.corrcoef(a1.v_1s, a1.area_1s)[0, 1]), 3) if len(a1) > 2 else None}
    out["per_episode"] = [{k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()} for r in rows]
    with open(OUT, "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "per_episode"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
