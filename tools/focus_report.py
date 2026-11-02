#!/usr/bin/env python3
"""Per-topic completeness table for the items asked in the 11-02 audit.
Reads inventory/INVENTORY.csv (current) and the SOURCES_MANIFEST.csv of a base git ref
(default: main) to show what was registered before vs. now.
Usage: python3 tools/focus_report.py [base_ref]   -> inventory/FOCUS_TABLE.md"""
import csv, io, os, re, subprocess, sys
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
base = sys.argv[1] if len(sys.argv) > 1 else "main"
old = subprocess.run(["git", "show", f"{base}:SOURCES_MANIFEST.csv"], cwd=REPO, capture_output=True, text=True).stdout
old_src = {r["source_path"] for r in csv.DictReader(io.StringIO(old))} if old else set()
rows = list(csv.DictReader(open(f"{REPO}/inventory/INVENTORY.csv", encoding="utf-8")))

TOPICS = [
    ("카메라 이동 전 사진 (옛 front, ~10-21)", r"(/main/(redbox_|cubemark).*/setup_photos/|/practice/(practice_10|practice_50|redbox_t[123][kr]_pilot)/setup_photos/|/Desktop/(cam_front|redbox_K_위치_(녹화화면|카메라)|redbox_카메라)|/main/redbox_all/eval/eval_(ab|space)/.*/start_(front|wrist)\.png$|/main/redbox_all/eval/rollouts/.*/start_images/|/practice/practice_50/eval/rollouts/.*/start_images/|/cubemark_v1/eval/rollouts/.*/start_images/|camera_settings/)"),
    ("카메라 이동 후 사진 (새 front, 10-22~)", r"(/main_k8/redbox_.*/setup_photos/|redbox_k8_t3k_pilot/setup_photos/|/main_k8/setting/|/k8/(front_|recheck_|cubes|box|ruler|proposed_numbering)|/main_k8/d2/eval/rollouts/.*/(start_images/|diag/obs/)|/practice/r[12]_.*/setup_photos/)"),
    ("카메라 보정·좌표계", r"(layouts.*\.yaml$|heldout_h\.yaml$|/range_check/|/calibration_backup|/k8/(k8_result|cam_model|cam_fit|fit\d?\.|fit\d\.json|make_k8)|plan_homography|위치_평면도|위치_카메라확인|번호_카메라|/k8/ang/|/k8/hard/)"),
    ("공간 일반화 히트맵·위치 분포", r"(heatmap|히트맵|space_map|분포_|position_map|zones_guide|qa/positions\.csv$|space_trials\.csv$)"),
    ("Shoulder Pan / Wrist Roll 시계열", r"(servo_data\.json$|servo_(시간|K별)\.png$|_action_state\.png$|pan_timeline|fig6_pilot_pan|02_servo_timeline|p01_ticks|q01b?_ticks|p08_human_pan|q04c_human_pan|roll_alignment|/k8/roll/|roll_hist|roll_vs_)"),
    ("명령값 vs 실제 관절값", r"(filter_log\.csv$|/trials/.*/ticks\.csv$|/diag/ticks\.csv$|ticks_chain\.csv$|real_command_compare|/eval.*/dataset/data/.*\.parquet$|p18_(fk_ticks|joints|paths)|analysis\.json$)"),
    ("RTC / Action 로그", r"(/eval.*/(debug|console)\.log$|/trials/.*/(inferences\.csv|chunks\.npz)$|/diag/(chunks\.jsonl|manifest\.json|summary\.json|verify\.json|chunks/))"),
    ("Action Expert 분석 그래프·표", r"/(action_bottleneck|sampling_ablation/eval)/.*\.(png|json|csv|md)$"),
]
lines = ["| 항목 | 로컬 원본 | 이전 GitHub (main) | 현재 직접 등록 | 축약·변환 반영 | 해시만 기록 | 누락 (매핑 없음) |",
         "|---|---|---|---|---|---|---|"]
for name, pat in TOPICS:
    sel = [r for r in rows if re.search(pat, r["source_path"])]
    n = len(sel)
    before = sum(r["source_path"] in old_src for r in sel)
    c = {s: sum(r["status"] == s for r in sel) for s in ("in_repo", "derived", "archived", "unmapped")}
    lines.append(f"| {name} | {n} | {before} | {c['in_repo']} | {c['derived']} | {c['archived']} | {c['unmapped']} |")
out = "\n".join(lines) + "\n"
open(f"{REPO}/inventory/FOCUS_TABLE.md", "w", encoding="utf-8").write(out)
print(out)
