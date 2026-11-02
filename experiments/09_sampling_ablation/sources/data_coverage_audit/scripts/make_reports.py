"""notes/NN.md 의 {{FACTS:NN}} 자리에 _facts/NN.md (스크립트가 만든 측정 사실) 를 넣어 최종 보고서를 만든다.
사용: python3 make_reports.py
"""
import re
from pathlib import Path

AUD = Path(__file__).resolve().parent.parent
MAP = {"01": "01_dataset_inventory.md", "02": "02_servo_timeline_readme.md", "03": "03_initial_state_analysis.md", "04": "04_cube_position_coverage.md",
       "05": "05_action_timeline_analysis.md", "06": "06_roll_error_coverage.md", "07": "07_policy_vs_demonstration.md",
       "08": "08_additional_data_recommendation.md", "09": "09_analysis_summary.md", "10": "10_reference_so101_compare.md", "handoff": "analysis_handoff.md"}
for k, name in MAP.items():
    src = AUD / "notes" / f"{k}.md"
    if not src.exists():
        continue
    txt = src.read_text()
    txt = re.sub(r"\{\{FACTS:(\w+)\}\}", lambda m: (AUD / "_facts" / f"{m.group(1)}.md").read_text(), txt)
    (AUD / name).write_text(txt)
    print(name)
