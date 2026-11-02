"""p09 파일럿 여러 실행 (예: U3 1 판 실행 + 나머지 11 판 실행) 을 판 순서대로 모은다 (읽기만, CPU).

입력: 실행 폴더들 (각각 p07 → analysis_pan/ 이 있어야 함), --labels (저장된 판 순서대로의 위치 이름, 실행 순서를 따라 이어 붙임)
  위치 이름은 기록용 이름일 뿐이다. 좌표는 판마다 시작 front 사진에서 잰 값 (p07 · cube_coords) 만 쓴다.
  K1–K8 이름 = 표시된 K 자리에 놓은 판 (group K, 사진 좌표가 K 명목에서 2 cm 넘게 벗어나면 group K_off). 그 밖 (U1–U8 등) = 작업 범위 안 임의 자리 (group free, 지정 좌표 없음).
  K 판은 '사진 좌표 − K 명목 좌표' (photo_minus_K_cm) 를 함께 낸다 = 이 실행 안의 좌표 역산 점검.
출력: pan_inference_diagnostic/pilot/ (환경변수 P09_OUT 로 바꿀 수 있음)
  pilot_episodes.csv   판별: 이름 · group · 사진 좌표 (x, y) · coord_status · 불확실성 · 학습 위치 / K 까지 거리 · pe · need
                       최초 chunk (판 첫 chunk = RTC 안내 없는 Action Expert 출력, 실측): 방향 · index 29/49 이동 · 비율 · index 49 − pe · 30–49 계획
                       첫 닫힘 전 chunk 중앙: 실행된 index (≈10–29) 이동 비율 · 계획 30–49 · RTC 뒤 − RTC 끔 (반사실) 차
                       역전 (기록 · RTC 끔) · 서보 (지연 · |Goal − Present| · clamp) · 첫 닫힘 때 pan − pe (부호 · 절댓값 · z)
  pilot_summary.json   coord_status 별 (valid_near_K · valid_off_K · invalid_detection · invalid_calibration) · 이름 묶음 (K / K_off / free) 별 · 전체 중앙값.
                       pe 가 필요한 지표는 valid_* 판만 (n_pe_ok). 좌표 불확실성 (pe_sigma_coord_deg) 과 사람 파지 산포 (pe_sigma_grasp_deg) 는 따로 낸다
사용: PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python p09_pilot_summary.py --runs <RUN1> <RUN2> \
        --labels U3,K1,U2,U5,K3,U6,U7,K6,U4,U1,K7,U8
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__import__("os").environ.get("P09_OUT", Path.home() / "so101_runs/main_k8/d2/pan_inference_diagnostic/pilot"))
COLS = ["label", "group", "run", "ds_ep", "cube_x", "cube_y", "cube_yaw_deg", "coord_status", "coord_status_reason", "coord_sigma_cm", "pe_sigma_coord_deg",
        "pe_sigma_grasp_deg", "pe_sigma_coord_note", "coord_accuracy_validated", "photo_minus_K_cm", "nearest_K", "dist_K_cm", "dist_nearest_train_cm", "n_train_within_3cm", "box_shift_px",
        "pe", "need", "verdict", "memo", "first_chunk_move29", "first_chunk_move49", "first_chunk_dir29", "first_chunk_dir29_ok",
        "first_chunk_idx29", "first_chunk_idx49", "first_chunk_gain29", "first_chunk_gain49", "first_chunk_idx49_minus_pe", "first_chunk_plan_30_49_frac",
        "pre_close_exec_move_frac_med", "pre_close_plan_30_49_frac_med", "pre_close_gain_idx29_med", "pre_close_off_gain_idx29_med",
        "rtc_minus_off_exec_last_abs_med", "first_dir_ok", "seam_min", "n_seam_le_m5", "back_max", "n_back_ge5", "off_seam_min", "off_back_max",
        "servo_lag_ticks", "sent_minus_present_moving_p50", "sent_minus_present_moving_p95", "pan_clamp_ticks",
        "onset_s", "first_close_s", "pan_err_at_close_sg", "pan_abs_err_at_close", "pan_err_at_close_over_sigma_coord", "pan_err_at_close_over_sigma_grasp", "state_t90_s", "n_close", "n_chunks"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--labels", "--positions", dest="labels", required=True)
    a = ap.parse_args()
    pos = a.labels.split(",")
    rows = []
    for run in a.runs:
        run = Path(run).expanduser().resolve()
        E = pd.read_csv(run / "analysis_pan/episodes.csv")
        E = E[E.attempt != "discarded"].sort_values("ds_ep")
        for _, r in E.iterrows():
            d = r.to_dict()
            d["run"] = run.name
            rows.append(d)
    if len(rows) != len(pos):
        print(f"주의: 저장된 판 {len(rows)} 개 vs 이름 {len(pos)} 개 — 앞에서부터 짝지음")
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    import cube_coords as CC
    for d, p in zip(rows, pos):
        d["label"], d["group"] = p, ("K" if p in CC.ac.KNOWN else "free")
        if p in CC.ac.KNOWN and not pd.isna(d.get("cube_x")):
            kx, ky = CC.ac.KNOWN[p]
            d["photo_minus_K_cm"] = float(np.hypot(d["cube_x"] - kx, d["cube_y"] - ky))
            if d["photo_minus_K_cm"] > 2.0:  # K 검증 최대 2.3 cm, p90 1.0 cm — 표시 자리에서 벗어나 놓인 판은 K 묶음에서 뺀다
                d["group"] = "K_off"
    D = pd.DataFrame(rows[: len(pos)])
    OUT.mkdir(exist_ok=True)
    D[[c for c in COLS if c in D] + [c for c in D.columns if c not in COLS]].to_csv(OUT / "pilot_episodes.csv", index=False)
    num = [c for c in COLS if c in D and pd.api.types.is_numeric_dtype(D[c])]
    def summ(x):
        return {"n": int(len(x)), "n_pe_ok": int(x.coord_status.isin(["valid_near_K", "valid_off_K"]).sum()) if "coord_status" in x else 0,
                **{c: (float(x[c].median()) if x[c].notna().any() else None) for c in num}}
    S = {"by_label_group": {g: summ(x) for g, x in D.groupby("group")},
         "by_coord_status": {g: summ(x) for g, x in D.groupby("coord_status")} if "coord_status" in D else {},
         "all": summ(D),
         "coord_status_counts": D.coord_status.value_counts().to_dict() if "coord_status" in D else {},
         "note": "valid_off_K 의 pe 는 좌표 정확도가 검증되지 않은 자리의 값 (K 판 검증 RMS 0.65 cm 는 K 자리 기준). "
                 "invalid_* 판은 pe 지표에서 빠지고 raw chunk · RTC · 서보 지표에는 남는다."}
    json.dump(S, open(OUT / "pilot_summary.json", "w"), indent=1, default=float)
    pd.set_option("display.width", 250, "display.max_columns", 60)
    print(D[[c for c in COLS if c in D]].round(2).T.to_string())
    keep = ("n", "n_pe_ok", "first_chunk_gain29", "pre_close_exec_move_frac_med", "pan_abs_err_at_close", "photo_minus_K_cm")
    print(json.dumps({"by_coord_status": {g: {k: v for k, v in s.items() if k in keep} for g, s in S["by_coord_status"].items()},
                      "by_label_group": {g: {k: v for k, v in s.items() if k in keep} for g, s in S["by_label_group"].items()},
                      "coord_status_counts": S["coord_status_counts"]}, indent=1, default=float))
    print("pe 지표는 valid_near_K · valid_off_K 판만 (off-K 는 좌표 정확도 미검증). raw chunk · RTC · 서보 지표는 모든 판.")


if __name__ == "__main__":
    main()
