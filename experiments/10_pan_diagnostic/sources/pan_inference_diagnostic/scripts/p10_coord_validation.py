"""p10 좌표 역산 정확도 검증 (읽기만, CPU). 로봇 · 카메라 연결 없음. 정책 행동은 쓰지 않는다.

A. d2 학습 256 편 front frame 0 (AV1 디코드) 에 파일럿과 같은 역산 (cube_coords.detect) 을 적용.
   K 판 (T1-K · T3-K 128 편, 사용자가 표시된 K 자리에 놓음) → 검출 좌표 − K 명목 좌표 = 오차 (배치 오차 + 검출 + 보정 포함).
   pan 영향: pe(검출) − pe(K 명목).
B. 같은 판의 기존 QA 검출 (check_dataset → a01_cube_table cube_x/y) 과의 차 = 검출기 차이.
C. 넓이 비 (검출 / config 한 개 기대) 분포 → unknown 규칙 (0.5–1.6) 확인.
D. 카메라 이동 점검: check_dataset.find_box 상자 사각형 (px) 을 학습 (10-22/23) · 실물 평가 (10-26) frame 0 에서 비교.
E. 'XY 만으로 파지 pan 이 정해지는가': 사람 첫 파지 (state gripper 닫힘) pan − pe(검출 좌표)
   - 전체 잔차 SD (pe 의 베이스 · 오프셋은 이 256 편으로 맞춘 값 → ac.py 의 5-fold CV SD 를 함께 보고)
   - 같은 K 자리 안 파지 pan SD (같은 명목 좌표에서 사람마다 다른 정도)
   - 잔차와 손목 roll · 큐브 각도 · 반지름의 상관, 이웃 (k=10, 자기 제외) 잔차 평균으로 줄어드는 정도
출력: tables/p10_frames.csv (256 편), p10_validation_summary.json
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python p10_coord_validation.py
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import cube_coords as CC  # noqa: E402

ac, C = CC.ac, CC.C
D2 = CC.D2
TAB = D2 / "pan_inference_diagnostic/tables"
sys.path.insert(0, str(Path.home() / "so101_boxpick/scripts"))


def box_rect(rgb):
    import cv2
    import check_dataset as cd
    r = cd.find_box(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
    return r


def main():
    A1 = pd.read_csv(ac.TAB / "a01_cube_table.csv")
    known = ac.KNOWN
    cache = {}
    D = ac.load_d2()
    rows = []
    for e in sorted(D):
        F = C.frames(D2 / "dataset", e, "front", 0, 0, cache)[0]
        d = CC.detect(F)
        a = A1[A1.ep == e].iloc[0]
        r = dict(ep=e, group=a.group, mode=a["mode"], plan_K=a.plan_K if isinstance(a.plan_K, str) else "", qa_x=a.cube_x, qa_y=a.cube_y,
                 yaw=a.yaw_used, **{f"det_{k}": v for k, v in d.items()})
        try:
            b = box_rect(F)
            if b is not None:
                r.update(box_x0=b[0], box_y0=b[1], box_x1=b[2], box_y1=b[3])
        except Exception as ex:  # noqa: BLE001
            r["box_err"] = repr(ex)
        st = D[e][0]
        cl = C.close_events(st[:, 5])
        if cl:
            r.update(close_frame=cl[0], pan_close=st[cl[0], 0], roll_close=st[cl[0], 4])
        if r["plan_K"] in known:
            kx, ky = known[r["plan_K"]]
            r.update(K_x=kx, K_y=ky)
        rows.append(r)
        if e % 32 == 0:
            print("ep", e, flush=True)
    F = pd.DataFrame(rows)
    # 실물 평가 (10-26) 상자 사각형 · 큐브 검출 (정답 없음)
    ev = []
    for run in sorted((D2 / "eval/rollouts").glob("2026102*")):
        ds = run / "dataset"
        info = json.loads((ds / "meta/info.json").read_text())
        for e in range(info["total_episodes"]):
            img = C.frames(ds, e, "front", 0, 0, cache)[0]
            b = box_rect(img)
            d = CC.detect(img)
            ev.append(dict(ep=f"{run.name}/{e}", box_x0=b[0] if b else None, box_y0=b[1] if b else None, box_x1=b[2] if b else None,
                           box_y1=b[3] if b else None, **{f"det_{k}": v for k, v in d.items()}))
    EV = pd.DataFrame(ev)
    F.to_csv(TAB / "p10_frames.csv", index=False)
    EV.to_csv(TAB / "p10_eval_frames.csv", index=False)

    ok = F[F.det_n_blobs > 0].copy()
    ok["pe_det"] = [CC.pe(x, y) for x, y in zip(ok.det_x, ok.det_y)]
    K = ok[ok.K_x.notna()].copy()
    K["dx"], K["dy"] = K.det_x - K.K_x, K.det_y - K.K_y
    K["d2"] = np.hypot(K.dx, K.dy)
    K["pe_K"] = [CC.pe(x, y) for x, y in zip(K.K_x, K.K_y)]
    K["dpe"] = K.pe_det - K.pe_K
    K["r"] = [CC.radius(x, y) for x, y in zip(K.K_x, K.K_y)]
    perK = K.groupby("plan_K").agg(n=("d2", "size"), dx_mean=("dx", "mean"), dy_mean=("dy", "mean"), dx_sd=("dx", "std"), dy_sd=("dy", "std"),
                                   d_p50=("d2", "median"), d_max=("d2", "max"), dpe_mean=("dpe", "mean"), dpe_sd=("dpe", "std"),
                                   dpe_absmax=("dpe", lambda v: v.abs().max()), r_cm=("r", "first"))
    perK.to_csv(TAB / "p10_perK.csv")
    qa = np.hypot(ok.det_x - ok.qa_x, ok.det_y - ok.qa_y)

    # E 사람 파지 pan
    H = ok[ok.pan_close.notna()].copy()
    H["resid"] = H.pan_close - H.pe_det
    H["r"] = [CC.radius(x, y) for x, y in zip(H.det_x, H.det_y)]
    xy = H[["det_x", "det_y"]].values
    loo = []
    for i in range(len(H)):
        d = np.hypot(*(xy - xy[i]).T)
        d[i] = np.inf
        nn = np.argsort(d)[:10]
        loo.append(H.resid.values[i] - H.resid.values[nn].mean())
    H["resid_minus_knn"] = loo
    Kpan = H[H.plan_K != ""].groupby("plan_K").pan_close.agg(["size", "std", "min", "max"])
    bf = json.load(open(ac.TAB / "a00_base_fit.json"))
    S = {
        "coord_err_cm": {"n": int(len(K)), "rms_2d": float(np.sqrt((K.d2 ** 2).mean())), "p50": float(K.d2.median()),
                         "p90": float(K.d2.quantile(.9)), "max": float(K.d2.max()), "dx_mean": float(K.dx.mean()), "dy_mean": float(K.dy.mean()),
                         "dx_sd": float(K.dx.std()), "dy_sd": float(K.dy.std()),
                         "note": "K 명목 좌표 대비 — 사람 배치 오차 + 검출 + 보정 (H 는 10-22 K 자리 큐브 8 개로 맞춤: 명목 좌표가 보정에 쓰였음)"},
        "pe_err_from_coord_deg": {"sd": float(K.dpe.std()), "mean": float(K.dpe.mean()), "abs_p90": float(K.dpe.abs().quantile(.9)),
                                  "abs_max": float(K.dpe.abs().max())},
        "detector_vs_qa_cm": {"n": int(qa.notna().sum()), "p50": float(qa.median()), "p90": float(qa.quantile(.9)), "max": float(qa.max())},
        "area_ratio": {"p01": float(ok.det_area_ratio.quantile(.01)), "p50": float(ok.det_area_ratio.median()),
                       "p99": float(ok.det_area_ratio.quantile(.99)), "min": float(ok.det_area_ratio.min()), "max": float(ok.det_area_ratio.max()),
                       "second_ratio_max": float(ok.det_second_ratio.max()), "n_no_blob": int((F.det_n_blobs == 0).sum())},
        "box_rect_px": {"train_median": F[["box_x0", "box_y0", "box_x1", "box_y1"]].median().to_dict() if "box_x0" in F else None,
                        "train_sd": F[["box_x0", "box_y0", "box_x1", "box_y1"]].std().to_dict() if "box_x0" in F else None,
                        "train_by_group_median": F.groupby("group")[["box_x0", "box_y0", "box_x1", "box_y1"]].median().to_dict("index") if "box_x0" in F else None,
                        "eval_1026_median": EV[["box_x0", "box_y0", "box_x1", "box_y1"]].median().to_dict() if len(EV) else None},
        "human_grasp": {"n": int(len(H)), "resid_sd_insample_deg": float(H.resid.std()), "resid_mean_deg": float(H.resid.mean()),
                        "resid_sd_cv_deg": float(bf["cv_resid_sd_deg"]), "resid_abs_p90_deg": float(H.resid.abs().quantile(.9)),
                        "within_K_pan_sd_deg_median": float(Kpan["std"].median()), "within_K_pan_sd_deg_max": float(Kpan["std"].max()),
                        "corr_resid_roll": float(np.corrcoef(H.resid, H.roll_close)[0, 1]),
                        "corr_resid_radius": float(np.corrcoef(H.resid, H.r)[0, 1]),
                        "corr_resid_yaw": float(H[["resid", "yaw"]].dropna().corr().iloc[0, 1]),
                        "resid_minus_knn10_sd_deg": float(np.std(loo)),
                        "note": "pe 의 베이스·오프셋은 이 256 편 첫 파지로 맞춘 값 (in-sample). CV SD 는 ac a00_base_fit.json"},
        "calib_region": {"x_max": -5.0, "max_dist_to_train_cm": 3.0,
                         "note": "config: 상자 근처 (x > −5) 는 렌즈 왜곡·높이 차이로 덜 정확. 학습 큐브 (256 편) 에서 3 cm 넘게 떨어진 곳은 검증 밖"},
        "status_rule": {"max_pe_sigma_coord_deg": 3.0},
    }
    json.dump(S, open(TAB / "p10_validation_summary.json", "w"), indent=1, ensure_ascii=False, default=float)
    pd.set_option("display.width", 220)
    print(json.dumps(S, indent=1, ensure_ascii=False, default=float))
    print(perK.round(2).to_string())
    print(Kpan.round(2).to_string())
    print(EV.round(1).to_string())


if __name__ == "__main__":
    main()
