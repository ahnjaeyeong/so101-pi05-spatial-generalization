"""1단계: 학습 데이터(d2 256편)와 실물 평가 롤아웃의 '파지 순간' 표를 만든다 (읽기만).

나오는 파일 (이 폴더):
  grasp_train.csv  — d2 판마다 첫 파지: 큐브 위치(QA positions.csv, 첫 front 프레임 + H), 파지 프레임, 관절(state·action),
                     pan 잔차, FK 집게 끝 위치(C frame, 학습 전체로 맞춘 강체 변환), 집게 끝 − 큐브 오차(반지름·접선), wrist 영상 큐브 중심
  grasp_eval.csv   — 롤아웃 판마다 닫힘 이벤트 전부(재시도 포함): 같은 항목 + 이벤트 번호
  fk_fit.json      — FK(base_link) → C frame 강체 변환과 학습 잔차

부호: pan_res = pan(state) − pan 기대값(큐브 방향).  + = 큐브보다 로봇 오른쪽(= front 영상 왼쪽)을 향함.
      tan_err = 집게 끝 − 큐브 의 접선 성분(cm).  + = 로봇 왼쪽(반시계).  rad_err + = 큐브보다 멀리.
사용: PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python grasp_table.py
"""
import json
import math

import numpy as np
import pandas as pd

import common as C

EVAL_RUNS = sorted((C.D2 / "eval/rollouts").glob("*/dataset"))


def wrist_cube(ds, ep, f, cache):
    """닫힘 2 프레임 전 wrist 영상의 가장 큰 빨강 덩어리 중심 (u, v 는 0–1) · 넓이 비율."""
    try:
        fr = C.frames(ds, ep, "wrist", f - 2, f - 2, cache)
    except Exception:
        return None
    if not fr:
        return None
    img = fr[0]
    b = C.blobs(C.red_mask(img), 60)
    if not b:
        return None
    a, (u, v), _, _ = max(b, key=lambda t: t[0])
    h, w = img.shape[:2]
    return dict(wu=u / w, wv=v / h, warea=a / (w * h))


def front_cube(ds, ep, f, cache, ref_area=None):
    """front 프레임 f 의 빨강 덩어리 (가장 큰 것, ref_area 가 있으면 넓이 0.5–1.6 배만) → (x, y) cm, 넓이."""
    fr = C.frames(ds, ep, "front", f, f, cache)
    if not fr:
        return None
    b = C.blobs(C.red_mask(fr[0]), 80)
    if ref_area:
        b = [t for t in b if 0.5 * ref_area <= t[0] <= 1.6 * ref_area]
    if not b:
        return None
    a, (u, v), _, _ = max(b, key=lambda t: t[0])
    x, y = C.px_to_cm(u, v)
    return dict(x=x, y=y, area=a, u=u, v=v)


def row_for(s, a, f, cube):
    r = {f"s_{j}": s[f, i] for i, j in enumerate(C.JOINTS)}
    r.update({f"a_{j}": a[f, i] for i, j in enumerate(C.JOINTS)})
    if cube is not None:
        x, y = cube
        r.update(cube_x=x, cube_y=y, bearing=C.bearing(x, y), range_cm=C.rng(x, y),
                 pan_exp=C.pan_expected(x, y))
        r["pan_res"] = s[f, 0] - r["pan_exp"]
        r["pan_res_action"] = a[f, 0] - r["pan_exp"]
    return r


def main():
    cache = {}
    known = C.load_known()
    # ---------- 학습 ----------
    pos = C.d2_positions()
    data = C.load_parquet(C.D2 / "dataset")
    assert len(pos) == len(data) == 256, (len(pos), len(data))
    rows = []
    for e, p in enumerate(pos):
        s, a = data[e]
        if p["frames_plan"] and p["frames_plan"] != len(s):
            raise SystemExit(f"d2 ep{e} 길이 {len(s)} ≠ layout frames {p['frames_plan']} ({p['session']} ep{p['src_ep']})")
        f = C.first_grasp(s[:, C.GRIP])
        r = dict(ep=e, group=p["group"], task=p["group"][:2], mode=p["group"][2], src=p["session"], src_ep=p["src_ep"],
                 layout_id=p["layout_id"], n_frames=len(s), grasp_f=f, grasp_t=None if f is None else f / 30)
        kk = p["layout_id"].split("-")[0][3:] if p["group"].endswith("K") else ""
        r["K"] = kk if kk in known else ""
        if f is not None:
            r.update(row_for(s, a, f, p["red"]))
            w = wrist_cube(C.D2 / "dataset", e, f, cache)
            if w:
                r.update(w)
        rows.append(r)
    T = pd.DataFrame(rows)

    # FK → C frame 강체 변환 (학습 첫 파지 전체)
    ok = T.grasp_f.notna() & T.cube_x.notna()
    P, _ = C.fk_xy(T.loc[ok, [f"s_{j}" for j in C.JOINTS[:5]]].values)
    A = P[:, :2] * 100.0
    B = T.loc[ok, ["cube_x", "cube_y"]].values
    R, t = C.fit_rigid2d(A, B)
    fit = dict(R=R.tolist(), t=t.tolist(), rot_deg=math.degrees(math.atan2(R[1, 0], R[0, 0])))

    def tip_cols(df):
        Pd, _ = C.fk_xy(df[[f"s_{j}" for j in C.JOINTS[:5]]].values)
        tip = (R @ (Pd[:, :2] * 100.0).T).T + t
        df["tip_x"], df["tip_y"], df["tip_z_cm"] = tip[:, 0], tip[:, 1], Pd[:, 2] * 100.0
        d = tip - df[["cube_x", "cube_y"]].values
        ur = (df[["cube_x", "cube_y"]].values - C.BASE)
        ur = ur / np.linalg.norm(ur, axis=1, keepdims=True)
        ut = np.stack([-ur[:, 1], ur[:, 0]], 1)  # 반시계 = 로봇 왼쪽
        df["rad_err"], df["tan_err"] = (d * ur).sum(1), (d * ut).sum(1)
        df["tip_bearing"] = [C.bearing(x, y) for x, y in tip]
        return df

    Tok = tip_cols(T[ok].copy())
    T = T.merge(Tok[["ep", "tip_x", "tip_y", "tip_z_cm", "rad_err", "tan_err", "tip_bearing"]], on="ep", how="left")
    fit["train_resid_cm_median"] = float(np.median(np.hypot(Tok.rad_err, Tok.tan_err)))
    fit["train_tan_err_mean"] = float(Tok.tan_err.mean())
    fit["note"] = "FK 는 so101_new_calib.urdf, 변환은 학습 첫 파지에 맞춘 것이라 학습 평균 오차는 0 근처가 되도록 맞춰져 있다."
    T.to_csv(C.OUT / "grasp_train.csv", index=False)

    # 학습 사람 파지의 큐브→관절 근사 (kNN, 큐브 위치 가까운 8편 평균) — 평가 이벤트의 '사람이라면' 관절
    Xtr = Tok[["cube_x", "cube_y"]].values
    Jtr = Tok[[f"s_{j}" for j in C.JOINTS[:5]]].values

    def human_joints(x, y, k=8):
        d = np.hypot(Xtr[:, 0] - x, Xtr[:, 1] - y)
        idx = np.argsort(d)[:k]
        return Jtr[idx].mean(0), float(d[idx].mean())

    # ---------- 평가 롤아웃 ----------
    erows = []
    traj = {}
    for ds in EVAL_RUNS:
        run = ds.parent.name
        ed = C.load_parquet(ds)
        for e, (s, a) in ed.items():
            traj[f"{run}|{e}|state"], traj[f"{run}|{e}|action"] = s, a
            c0 = front_cube(ds, e, 0, cache)
            evs = C.close_events(s[:, C.GRIP])
            for k, f in enumerate(evs):
                # 시도 직전 큐브 위치: f 에서 거꾸로 front 에서 큐브가 시작 넓이로 보이는 가장 늦은 프레임 (30 프레임 간격)
                cnow = None
                for g in range(f, max(-1, f - 300), -15):
                    cnow = front_cube(ds, e, g, cache, ref_area=c0["area"] if c0 else None)
                    if cnow:
                        cnow["frame"] = g
                        break
                cube = (c0["x"], c0["y"]) if k == 0 or cnow is None else (cnow["x"], cnow["y"])
                r = dict(run=run, ep=e, event=k, frame=f, t=f / 30, n_frames=len(s),
                         start_x=c0["x"] if c0 else None, start_y=c0["y"] if c0 else None,
                         cube_src="start" if (k == 0 or cnow is None) else f"front f{cnow['frame']}")
                r.update(row_for(s, a, f, cube))
                hj, hd = human_joints(*cube)
                for i, j in enumerate(C.JOINTS[:5]):
                    r[f"human_{j}"] = hj[i]
                    r[f"d_{j}"] = s[f, i] - hj[i]
                r["human_knn_dist_cm"] = hd
                dk = {kk: math.hypot(cube[0] - v[0], cube[1] - v[1]) for kk, v in known.items()}
                r["nearest_K"], r["nearest_K_cm"] = min(dk.items(), key=lambda t: t[1])
                w = wrist_cube(ds, e, f, cache)
                if w:
                    r.update(w)
                erows.append(r)
    E = pd.DataFrame(erows)
    if len(E):
        E = tip_cols(E)
        # 가장 가까운 K 로 끌렸는지: 집게 끝 방향이 큐브 방향과 가까운 K 방향 중 어느 쪽에 가까운가
        E["K_bearing"] = [C.bearing(*known[k]) for k in E.nearest_K]
    E.to_csv(C.OUT / "grasp_eval.csv", index=False)
    np.savez(C.OUT / "eval_traj.npz", **traj)  # plots.py 용 (시스템 python3 에 parquet 엔진 없음)
    json.dump(fit, open(C.OUT / "fk_fit.json", "w"), indent=1, ensure_ascii=False)
    print(f"train {len(T)} (grasp found {T.grasp_f.notna().sum()}, cube {T.cube_x.notna().sum()}), eval events {len(E)}")
    print(json.dumps(fit, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
