"""01 · 02 사실 문서 (a00 · a01 · a02 결과 json/csv 를 표로). 출력 _facts/01.md, _facts/02.md
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python a08_facts_0102.py
"""
import json

import numpy as np
import pandas as pd

import ac


def main():
    I = json.load(open(ac.TAB / "a01_inventory.json"))
    M = json.load(open(ac.TAB / "a00_tcp_model.json"))
    BF = json.load(open(ac.TAB / "a00_base_fit.json"))
    V = pd.read_csv(ac.TAB / "a01_video_sync_sample.csv")
    Cd = pd.read_csv(ac.TAB / "a01_cadence_per_episode.csv")
    L = pd.read_csv(ac.TAB / "a02_lag.csv")
    E = pd.read_csv(ac.TAB / "a02_events.csv")
    files = I["files"]
    fsum = pd.DataFrame([dict(kind=k.split("/")[0] + ("/" + k.split("/")[1] if k.startswith("videos") else ""), path=k, MB=v / 1e6) for k, v in files.items()])
    fs = fsum.groupby("kind").agg(files=("path", "size"), MB=("MB", "sum")).reset_index()
    feat = pd.DataFrame([dict(column=k, dtype=v["dtype"], shape=str(v["shape"]), names=", ".join(v["names"]) if isinstance(v["names"], list) and len(v["names"]) <= 6 else str(v["names"])[:40])
                         for k, v in I["info"]["features"].items()])
    res = pd.DataFrame([dict(joint=k, **v) for k, v in I["value_resolution"].items()])
    ts = I["timestamp"]
    cad = I["cadence"]
    vs = I["video_sample"]
    t = ["## 측정 사실 (스크립트 생성: `scripts/a01_inventory.py`, `a00_tcp_model.py`, `a08_facts_0102.py`)\n",
         "### 1.1 파일\n", f"- 경로 `~/so101_runs/main_k8/d2/dataset` (LeRobot {I['info']['codebase_version']}, robot_type {I['info']['robot_type']}), "
         f"{I['info']['total_episodes']} 편 · {I['info']['total_frames']:,} 프레임 · fps {I['info']['fps']}.\n",
         ac.md_table(fs, {"files": "{:.0f}", "MB": "{:.1f}"}), "\n",
         "### 1.2 스키마 (meta/info.json)\n", ac.md_table(feat), "\n",
         f"- 영상: {I['info']['video']['video.codec']} {I['info']['video']['video.pix_fmt']}, g={I['info']['video']['video.g']}, crf={I['info']['video']['video.crf']}, 640×480, 30 fps.",
         "- 원본 세션 메타 (d2 에는 없음, 세션 폴더에 있음): `layout.csv` (계획 배치 · 각도 · 상태), `qa/positions.csv` (front 첫 화면 큐브 위치 cm), `qa_report.md` (잰 각도 · 손목 필요/돌림), "
         "`qa/servo_data.json` (관절 요약), record_ui sidecar 로그 (`~/.local/state/record_ui/record_*.log|json`).\n",
         "### 1.3 각 열의 의미 · 단위 (코드 근거)\n",
         "| 열 | 의미 | 근거 |\n|---|---|---|",
         "| observation.state | 팔로워 서보 `Present_Position` (sync_read), 프레임 처음에 읽음 | lerobot `robots/so_follower/so_follower.py:204-207` |",
         "| action | 리더 팔 위치 (teleop.get_action) — 같은 tick 에 팔로워 `Goal_Position` 으로 그대로 보냄 (절대 목표, 상대 변화량 아님) | `scripts/lerobot_record.py:320-368` (데이터셋에는 자르기 전 action_values 를 저장), `so_follower.py:229-253` |",
         f"| max_relative_target | 녹화 256편 모두 {cad['robot_cfg']['cfg_max_relative_target']} → 보낸 목표 = 저장된 action | sidecar 로그 |",
         f"| 위치 PID | P {cad['robot_cfg']['cfg_position_p_coefficient']} · I {cad['robot_cfg']['cfg_position_i_coefficient']} · D {cad['robot_cfg']['cfg_position_d_coefficient']} | sidecar 로그 |",
         f"| 단위 | 관절 5개 °(use_degrees={cad['robot_cfg']['cfg_use_degrees']}: (raw − (range_min+range_max)/2) × 360/4095), 그리퍼 0–100 (RANGE_0_100) | `so_follower.py:71-80` |",
         "| timestamp | frame_index / 30 (기록 시각이 아니라 계산값) | 데이터: 아래 1.4 |",
         "| 큐브 위치 | 데이터셋에 없음. 세션 QA 가 front 첫 화면 빨강 중심을 config H 로 역산 (C frame cm) | `check_dataset.py`, `qa/positions.csv` |",
         "| 큐브 각도 | 데이터셋에 없음. 계획 = layout.csv angles, 잰 값 = QA cube_angle (front 첫 화면) | `qa_report.md` |",
         "| 속도 · 전류 · 온도 · 전압 · 부하 · 실제 보낸 목표의 서보 측 값 | **기록 없음** (데이터셋 열 · sidecar 로그 모두) | info.json, 로그 |\n",
         "### 1.4 시간 · 동기화\n",
         f"- timestamp 간격 {ts['dt_min']:.6f}–{ts['dt_max']:.6f} s; |timestamp − frame_index/30| 최대 {ts['max_abs_ts_minus_frameidx_over_fps']:.2e}; frame_index 불연속 {ts['frame_index_noncontiguous']}; NaN state {ts['nan_state']} · action {ts['nan_action']}.",
         f"- 영상 구간 길이 (to − from) × 30 − 데이터 프레임 수: 최대 {I['video_span_minus_length_frames_max']:.1e} 프레임.",
         f"- 실제 루프 주기 (record_ui 로그 'Cadence' 줄, 판별): {cad['n_matched']}/256 편 연결, tick 수 = 프레임 수 {cad['ticks_eq_length']}/256. "
         f"{cad['hz_min']:.2f}–{cad['hz_max']:.2f} Hz (중앙값 {cad['hz_median']:.2f}); 33.3 ms 예산 넘긴 tick {cad['over_budget_total']}/{cad['intervals_total']:,}; "
         f"작업 시간 평균 중앙값 {cad['work_mean_ms_median']:.1f} ms, 최악 {cad['work_worst_ms_max']:.1f} ms. 프레임별 실제 시각은 기록되지 않음.",
         f"- 영상 해독 표본 16편 × 2 카메라: 해독 프레임 수 = 데이터 프레임 수 {vs['decoded_eq_data']}/{vs['n']}. 팔이 움직이는 프레임 (관절 속도 > 20°/s) 중 앞 프레임과 거의 같은 (평균 차 < 0.05/255, 1/8 축소) 프레임: "
         f"{', '.join(f'{k} {v}' for k, v in vs['exact_moving_by_cam'].items())} / 카메라당 {V[V.cam == 'front'].frames_moving.sum()} (중복 · 멈춘 프레임 후보).",
         "- 카메라 영상은 `read_latest()` (비동기 최신 프레임) 이라 state 읽기와 같은 tick 에 묶이지만 촬영 시각은 기록되지 않는다 → 영상-관절 사이 지연은 측정 불가.\n",
         "### 1.5 값 해상도 · 범위 (전 프레임)\n", ac.md_table(res, {"n_unique_state": "{:.0f}", "state_min_step": "{:.4f}"}), "\n",
         "### 1.6 캘리브레이션\n"]
    for k, v in I["calibration"].items():
        t.append(f"- `{v['path']}` (수정 {v['mtime'][:19]}): " + "; ".join(f"{j} homing {c['homing_offset']} range {c['range_min']}–{c['range_max']}" for j, c in v["content"].items()))
    t += ["\n### 1.7 좌표계 · TCP (a00_tcp_model)\n",
          "- C frame (config redbox8_layouts.yaml): x = 로봇 → 상자 (+), y = 로봇 왼쪽 (+), cm. 원점 = 상자 로봇쪽 벽 바깥면 로봇 오른쪽 끝 (C 의 y 는 ±0.5 cm 추정).",
          f"- 베이스: config ({BF['config']['base_xy_cm'][0]}, {BF['config']['base_xy_cm'][1]}), pan 오프셋 {BF['config']['pan_offset_deg']}° (T1-K 48편 맞춤) → 첫 파지 pan 잔차 SD {BF['config_resid_sd_deg']:.2f}°, "
          f"평균 {BF['config_resid_mean_deg']:+.2f}°, bearing 과 상관 {BF['config_corr_bearing']:.2f}. 이 감사는 256편으로 다시 맞춘 ({BF['base_xy_cm'][0]:.2f}, {BF['base_xy_cm'][1]:.2f}), "
          f"오프셋 {BF['pan_offset_deg']:.2f}° 사용 (5-fold CV 잔차 SD {BF['cv_resid_sd_deg']:.2f}°, bearing 상관 {BF['cv_corr_bearing']:.2f}). 실측 베이스 위치는 없다.",
          "- TCP 모델 비교 (파지 순간, 큐브 중심 대비 cm):\n",
          ac.md_table(pd.DataFrame([dict(model=k, **{kk: vv for kk, vv in v.items() if not isinstance(vv, list)}) for k, v in M.items() if k.startswith("M")])), "\n",
          f"- 채택 = M2 + 반지름 편향 dA {M['dA_cm']:.2f} cm (CV). URDF (so101_new_calib) 의 pan 축은 base_link 원점에서 3.88 cm 떨어져 있어, 기존 fk_fit (base_link 를 강체 변환) 은 bearing 에 비례하는 접선 오차 (상관 −0.88) 를 만든다. "
          "URDF 옆 오프셋 부호를 뒤집은 M2 가 roll 상관을 없앤다 (M1 −0.84 → M2 −0.05) — URDF wrist_roll 방향과 lerobot 보정 방향의 차이로 보이나 확인 안 됨.",
          f"- 측정 바닥 (사람 파지 순간): 접선 SD {M['M2_dA_cv']['tan_sd']:.2f} cm (|.| 중앙값 {M['M2_dA_cv']['tan_abs_p50']:.2f}, 90% {M['M2_dA_cv']['tan_abs_p90']:.2f}), 반지름 SD {M['M2_dA_cv']['rad_sd']:.2f} cm. "
          f"큐브 위치 추정 오차 (Known 잰 − 계획) 중앙값 {M['known_meas_minus_plan_cm']['p50']:.2f}, 90% {M['known_meas_minus_plan_cm']['p90']:.2f} cm 가 이 안에 포함된다.",
          "- 판 안 상대 이동 (TCP(t) − TCP(c)) 은 판별 고정 편향이 빠지므로 바닥보다 작은 변화도 비교할 수 있다 (a05: wrist 영상 라벨과 상관 −0.73, 기울기 −0.92 @ 닫힘 2–3 s 전).\n"]
    ac.write_facts("01.md", "\n".join(t))
    # 02
    lg = L.groupby("joint").agg(lag_frames_med=("lag_frames", "median"), lag_frames_p90=("lag_frames", lambda s: s.quantile(.9)), lag_corr_med=("lag_corr", "median"),
                                err_mean=("err_mean", "median"), err_abs_mean_moving=("err_abs_mean_moving", "median"), err_abs_p95=("err_abs_p95", "median"),
                                err_mean_static=("err_mean_static", "median")).reindex(ac.JOINTS).reset_index()
    t2 = ["## 측정 사실 (스크립트 생성: `scripts/a02_timeline.py`, `a08_facts_0102.py`)\n",
          "### 2.1 파일\n",
          "- `02_servo_timeline.parquet`: 740,052 행 = 123,342 프레임 × 서보 6. 열: episode_id, task_type, frame_index, timestamp, relative_time, servo_name, unit, "
          "measured_position (state), commanded_position (action), action_value (= commanded_position, 녹화 때 자르기 없음), position_delta (측정 위치 직전 프레임 차), "
          "estimated_velocity (측정 위치 중앙 차분 × 30, **추정값**), velocity_is_estimate, tracking_error_cmd_minus_meas, phase, front_video / front_video_ts, wrist_video / wrist_video_ts "
          "(해당 프레임을 꺼낼 mp4 경로 (dataset 기준) 와 그 파일 안 시각 s).",
          "- `tables/a02_frames.parquet`: 프레임별 넓은 표 (관절 state/action/속도, TCP x/y/z, 큐브 대비 e_t/e_r, action 기반 TCP, 구간).",
          "- `tables/a05_frames_rel.parquet`: 위 + 최종 파지 TCP 기준 r_t/r_r/r_z, 관절별 TCP 기여.",
          "- `tables/a02_events.csv`: 판별 이벤트 프레임 (onset, pan_reach/settle ±1/2/3°, reach ±1/2/3 cm, close_start, grasp, lift, release) · 파지 순간 · −5/−3/−2/−1 s 상태.\n",
          "### 2.2 명령 (action) → 측정 (state) 지연 · 추종 오차 (판별 값의 중앙값)\n",
          "lag = 속도 상호상관 최대 지연 (프레임, 0–15). err = action − state (°). moving = |속도| > 10°/s (그리퍼 20).\n",
          ac.md_table(lg), "\n",
          "### 2.3 이벤트 검출\n",
          f"- 첫 파지 (check_dataset.first_grasp) 256/256, 기존 grasp_train.csv 와 같은 프레임 {int((E.grasp == E.grasp_prev).sum())}/256.",
          f"- 들어올림 (TCP z ≥ z(c) + 3 cm) 256/256; 놓기 (그리퍼 + 5) {int(E.release.notna().sum())}/256.",
          f"- 첫 닫힘 뒤 들어올리기 전 닫힘 수 = 1 인 판 {int((E.n_close_before_lift == 1).sum())}/256 (사람 재파지 없음). 첫 닫힘 뒤 그리퍼 state 중앙값 {E.g_hold.min():.1f}–{E.g_hold.max():.1f} "
          f"(빈 닫힘이면 ≈ 1), state − action {E.g_gap.min():.1f}–{E.g_gap.max():.1f} → 256편 모두 첫 닫힘에서 큐브를 쥠.",
          f"- 판 길이 {E.len_s.min():.1f}–{E.len_s.max():.1f} s (중앙값 {E.len_s.median():.1f}); onset {E.onset.median() / 30:.2f} s; 첫 파지 {E.grasp.median() / 30:.2f} s (중앙값).\n"]
    ac.write_facts("02.md", "\n".join(t2))
    print("\n".join(t))
    print("\n".join(t2))


if __name__ == "__main__":
    main()
