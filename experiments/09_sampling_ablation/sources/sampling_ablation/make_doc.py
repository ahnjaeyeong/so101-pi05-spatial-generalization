"""실험설계_본문.md 의 {{T1}}…{{T5}} 자리에 s2_tables.md 의 표를 넣어 실험설계.md 를 만든다."""
from pathlib import Path

D = Path(__file__).parent
t = (D / "s2_tables.md").read_text()
parts = {b.split(".")[0].replace("표 ", "T"): "#### " + b.strip() for b in t.split("### ")[1:]}
doc = (D / "실험설계_본문.md").read_text()
for k, v in parts.items():
    doc = doc.replace("{{" + k + "}}", v)
assert "{{" not in doc
(D / "실험설계.md").write_text(doc)
print(len(doc.splitlines()), "lines")
