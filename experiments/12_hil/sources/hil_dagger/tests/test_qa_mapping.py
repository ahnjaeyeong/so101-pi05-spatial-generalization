"""hil_qa.py 의 표시 → episode 매핑 검사 (S7 · S8 · S10 가짜 세션)."""
import csv
import subprocess
import sys
from pathlib import Path

H = Path(__file__).resolve().parent
# (reset, type, recovery_done, first_grasp, final_task, 변환 제외 사유)
EXPECT = {
    "S10_adapter_start_paused_reset": [("True", "미입력", "미입력", "미입력", "미입력", "원위치 구간(r)"),
                                       ("False", "R1", "예", "ok", "미입력", "최종 결과 미입력"),
                                       ("True", "미입력", "미입력", "미입력", "미입력", "원위치 구간(r)")],
    "S12_adapter_rtc_fault": [("False", "R2", "예", "ok", "success", "")],
    "S15_adapter_normal_end_home": [("False", "R1", "예", "ok", "success", "")],
    "S8_adapter_esc_in_correction": [("False", "미입력", "미입력", "미입력", "미입력", "교정 도중 세션 종료 · 최종 결과 미입력")],
    "S13_adapter_leader_fault": [("False", "미입력", "미입력", "미입력", "미입력", "교정 도중 세션 종료 · 최종 결과 미입력")],
    "S14_adapter_follower_fault": [("False", "미입력", "미입력", "미입력", "미입력", "교정 도중 세션 종료 · 최종 결과 미입력")],
}
ok = True
for s, exp in EXPECT.items():
    subprocess.run([sys.executable, str(H.parent / "tools/hil_qa.py"), str(H / "_out" / s)], check=True, capture_output=True)
    rows = list(csv.DictReader(open(H / "_out" / s / "qa/hil_qa.csv")))
    got = [(r["reset_segment"], r["type"], r["recovery_done"], r["first_grasp"], r["final_task"], r["변환_제외_사유"]) for r in rows]
    p = got == exp
    ok &= p
    print(f"{'PASS' if p else 'FAIL'} QA_mapping {s} got={got}")
print("QA_MAPPING_ALL_PASS" if ok else "QA_MAPPING_FAIL")
sys.exit(0 if ok else 1)
