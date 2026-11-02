"""front 영상 → 큐브 탁자 좌표 → 기준 pan (pe). 새 구현 없이 기존 함수를 묶기만 한다 (읽기만).

재사용:
  - 빨강 검출: diag_grasp_bias/common.py red_mask (= so101_boxpick/scripts/pregrasp_angles.red_mask_rgb) + blobs
  - 화면 → 탁자: common.px_to_cm (config/redbox8_layouts.yaml camera.front_640x480.H_cm_to_px 의 역행렬)
      H 는 2026-10-22 K1–K8 에 놓은 2.5 cm 큐브 8 개의 검출 중심으로 맞춘 '큐브 중심 높이 면' 변환 (재투영 평균 2 px ≈ 0.2 cm).
  - 큐브 한 개 넓이 모델: config detection.cube_area_px (a = c0 + c1·v + c2·u + c3·v², front px)
  - 기준 pan: data_coverage_audit/scripts/ac.py — pe = PAN_SIGN · bearing(x, y) + PAN_OFF,
      bearing = atan2(y − by, x − bx), 베이스 (bx, by) = (−30.55, 11.18) · PAN_OFF −0.75° (d2 사람 256 편 첫 파지 pan 으로 맞춘 값, 실측 아님)
좌표계: config 'C frame', 단위 cm. 원점 = 상자 로봇쪽 벽 바깥면의 로봇 기준 오른쪽 끝. x = 로봇 → 상자 (+), y = 로봇 왼쪽 (+).
pan 부호: + = 로봇 오른쪽 (pan_sign −1).
정책 행동 · 파지 위치는 쓰지 않는다 (판 시작 사진만).
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

D2 = Path.home() / "so101_runs/main_k8/d2"
sys.path.insert(0, str(D2 / "data_coverage_audit/scripts"))
import ac  # noqa: E402

C = ac.C
DET = C.CFG.get("detection", {})
AREA_MODEL = DET.get("cube_area_px", [786.9, 1.303, -0.015, 0.0])
MIN_AREA = int(DET.get("min_blob_area_px", 100))
VALID = D2 / "pan_inference_diagnostic/tables/p10_validation_summary.json"
METHOD = ("front 시작 사진 → HSV 빨강 마스크 (pregrasp_angles.red_mask_rgb) → 가장 큰 덩어리 중심 (u, v) px → "
          "config H_cm_to_px 역변환 (큐브 중심 높이 면) → C frame (x, y) cm")


def area_expected(u, v):
    c0, c1, c2, c3 = AREA_MODEL
    return c0 + c1 * v + c2 * u + c3 * v * v


def pe(x, y):
    return float(ac.PAN_SIGN * ac.bearing(x, y) + ac.PAN_OFF)


def radius(x, y):
    return float(math.hypot(x - ac.BASE[0], y - ac.BASE[1]))


def detect(rgb):
    """rgb (H, W, 3) → dict: n_blobs, u, v, area, area_ratio (검출 / 한 개 기대), second_ratio (둘째 / 첫째), x, y (cm). 없으면 n_blobs 0."""
    b = C.blobs(C.red_mask(rgb), MIN_AREA)
    if not b:
        return {"n_blobs": 0}
    b = sorted(b, key=lambda t: -t[0])
    a, (u, v), _, _ = b[0]
    x, y = C.px_to_cm(u, v)
    return {"n_blobs": len(b), "u": u, "v": v, "area": a, "area_ratio": a / area_expected(u, v),
            "second_ratio": (b[1][0] / a) if len(b) > 1 else 0.0, "x": x, "y": y}


def validation():
    """p10 결과 (좌표 오차 · 사람 파지 pan 산포). 없으면 None."""
    return json.loads(VALID.read_text()) if VALID.exists() else None


# 상태 (2026-10-29 사용자 지시로 나눔). 정답 pan (pe) 은 valid_* 에서만 낸다.
#   invalid_detection  : 빨강 없음 · 넓이 비 0.5–1.6 밖 · 둘째 덩어리 ≥ 0.3 배 · 시작 사진 없음
#   invalid_calibration: 카메라 이동 (상자 사각형 > 6 px, p07 에서 판정) · H 적용 범위 밖 (아래 CALIB)
#   valid_near_K       : 위 둘이 아니고 가장 가까운 K 명목 자리에서 NEAR_K_CM 이내 — 좌표 정확도를 K 판 128 편으로 검증한 범위
#   valid_off_K        : 위 둘이 아니고 K 에서 NEAR_K_CM 보다 멂 — XY · pe 를 저장하되 좌표 정확도는 **검증되지 않음**
NEAR_K_CM = 3.0
# H 적용 범위: 보정 · 학습 중 탁자 위 큐브가 실제로 관측된 범위 (학습 256 편 x −33.6 … −5.0, y −14.0 … 35.9 에 1 cm 여유).
#   x > −5 (상자 앞 벽 근처) 는 config 에 '렌즈 왜곡 · 높이 차로 덜 정확' 이라 적힌 곳 → 적용 범위 밖으로 둔다.
CALIB = {"x_min": -35.0, "x_max": -5.0, "y_min": -15.0, "y_max": 37.0}
VALID_STATES = ("valid_near_K", "valid_off_K")


def estimate(rgb, train_xy=None, known=None):
    """판 시작 front 영상 → 좌표 · pe · 불확실성 · 상태 dict (상태는 위 4 가지)."""
    d = detect(rgb)
    out = {"coord_method": METHOD, "coord_frame": "C frame (config/redbox8_layouts.yaml), cm", "pe_method":
           "pe = −bearing(base −30.55, 11.18) − 0.75° (ac.py, 사람 첫 파지 256 편 맞춤)", **{f"det_{k}": v for k, v in d.items()}}
    det_why, cal_why = [], []
    if d["n_blobs"] == 0:
        det_why.append("빨강 덩어리 없음")
    else:
        if not 0.5 <= d["area_ratio"] <= 1.6:
            det_why.append(f"넓이 / 한 개 기대 {d['area_ratio']:.2f} (0.5–1.6 밖: 가림 · 손 · 여러 개)")
        if d["second_ratio"] >= 0.3:
            det_why.append(f"둘째 빨강 덩어리 {d['second_ratio']:.2f} 배")
    V = validation()
    if d["n_blobs"]:
        x, y = d["x"], d["y"]
        r = radius(x, y)
        out.update(cube_x=x, cube_y=y, radius_cm=r, pe_candidate=pe(x, y), deg_per_cm_tangential=math.degrees(1 / r))
        if not (CALIB["x_min"] <= x <= CALIB["x_max"] and CALIB["y_min"] <= y <= CALIB["y_max"]):
            cal_why.append(f"(x, y) = ({x:.1f}, {y:.1f}) 가 H 적용 범위 {CALIB} 밖")
        if V:
            s_xy = V["coord_err_cm"]["rms_2d"]
            out["coord_sigma_cm"] = s_xy
            out["pe_sigma_coord_deg"] = math.degrees(s_xy / math.sqrt(2) / r)  # 접선 성분만 pan 에 들어감
            out["pe_sigma_grasp_deg"] = V["human_grasp"]["resid_sd_cv_deg"]
        if known:
            k, dk = min(((k, math.hypot(x - kx, y - ky)) for k, (kx, ky) in known.items()), key=lambda t: t[1])
            out.update(nearest_K=k, dist_K_cm=dk)
        if train_xy is not None and len(train_xy):
            dd = np.hypot(train_xy[:, 0] - x, train_xy[:, 1] - y)
            out.update(dist_nearest_train_cm=float(dd.min()), n_train_within_3cm=int((dd <= 3).sum()))
    if det_why:
        st = "invalid_detection"
    elif cal_why:
        st = "invalid_calibration"
    elif out.get("dist_K_cm", 0.0) <= NEAR_K_CM:
        st = "valid_near_K"
    else:
        st = "valid_off_K"
    out["coord_status"] = st
    out["coord_status_reason"] = "; ".join(det_why + cal_why)
    out["coord_accuracy_validated"] = st == "valid_near_K"
    out["pe_sigma_coord_note"] = ("K 판 128 편 검증값" if st == "valid_near_K" else
                                  "K 판 검증값을 그대로 쓴 참고치 — 이 자리 (off-K) 의 좌표 정확도는 검증되지 않음" if st == "valid_off_K" else "")
    out["pe"] = out.get("pe_candidate") if st in VALID_STATES else None  # invalid 면 정답각을 주지 않음
    if d["n_blobs"]:
        out.update(cube_yaw(rgb, (d["x"], d["y"])))
    return out


def cube_yaw(rgb, xy_cm):
    """참고 정보: 큐브 회전각 (so101_boxpick/scripts/cube_angle.measure_at 재사용, ↺ +, (−45, 45]). pe 계산에는 쓰지 않는다."""
    try:
        import cv2
        sys.path.insert(0, str(Path.home() / "so101_boxpick/scripts"))
        import cube_angle as CA
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        cam = C.CFG["camera"]["front_640x480"]
        m = CA._masks(bgr, C.CFG).get("red")
        if m is None:
            return {"cube_yaw_deg": None, "cube_yaw_note": "설정에 red 색 범위 없음"}
        a, conf = CA.measure_at(m, cam["H_cm_to_px"], cam["camera_xy_cm"], xy_cm, img=bgr)
        return {"cube_yaw_deg": a, "cube_yaw_conf": conf if a is not None else None, "cube_yaw_note": "" if a is not None else conf}
    except Exception as e:  # noqa: BLE001
        return {"cube_yaw_deg": None, "cube_yaw_note": repr(e)}
