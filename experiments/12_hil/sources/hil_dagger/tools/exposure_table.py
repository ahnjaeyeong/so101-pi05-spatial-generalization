"""HIL 학습 조건별 표본 노출량 계산 (계산식만, 학습 안 함). 출력: docs/exposure_table.md

S = batch × steps (rft01 과 같은 32 × 1000). 프레임 반복 가중(sampling_ablation/train_weighted.py 방식): 프레임 i 의 뽑힐 확률 ∝ w_i.
기대 노출 (프레임 1개가 학습에 들어가는 횟수) = S · w_i / Σw.
"""
import json
from pathlib import Path

D2 = json.loads((Path.home() / "so101_runs/main_k8/d2/dataset/meta/info.json").read_text())["total_frames"]
RC16 = 129470 - D2  # rft01 manifest 272 판 129,470 frame − d2
S = 32 * 1000
rows = []


def cond(name, groups):
    tot = sum(n * w for n, w in groups.values())
    out = {g: (n, w, round(100 * n * w / tot, 1), round(S * w / tot, 2)) for g, (n, w) in groups.items()}
    rows.append((name, out))


for H in (2000, 4000, 8000):
    cond(f"H1-concat H={H}", {"d2": (D2, 1), "HIL": (H, 1)})
    cond(f"H1-W5 H={H}", {"d2": (D2, 1), "HIL": (H, 5)})
    w_iwr = D2 / H  # IWR: 개입 표본 전체 비중 = 비개입 전체 비중 (α = |D_R|/|D_I|)
    cond(f"H1-IWR50 H={H}", {"d2": (D2, 1), "HIL": (H, w_iwr)})
    cond(f"PH1-W5 H={H}", {"d2": (D2, 1), "R1/RC16": (RC16, 5), "HIL": (H, 5)})
    cond(f"PH1-IWR50 H={H}", {"d2": (D2, 1), "R1/RC16+HIL": (RC16 + H, D2 / (RC16 + H))})
cond("P1 (진행 중 rft01, W5)", {"d2": (D2, 1), "R1/RC16": (RC16, 5)})

L = ["# HIL 학습 조건별 표본 노출량 (tools/exposure_table.py 자동 생성)", "",
     f"d2 frame {D2:,} · R1/RC16 frame {RC16:,} (rft01 manifest 129,470 − d2) · S = 32 × 1000 = {S:,} 표본. H = HIL 교정 frame 수 (가정값).",
     "IWR50 = 개입 프레임 전체 뽑힘 비중 50 % (Mandlekar et al. 2020 의 α=|D_R|/|D_I| 를 프레임 반복 가중으로 근사; 가중이 정수가 아니면 반올림 필요).", "",
     "| 조건 | 그룹: frame 수 · 가중 · 표본 비중 % · frame 당 기대 노출 |", "|---|---|"]
for name, out in rows:
    L.append(f"| {name} | " + " ; ".join(f"{g}: {n:,} · w {w:.2f} · {p} % · {e}" for g, (n, w, p, e) in out.items()) + " |")
p = Path(__file__).resolve().parents[1] / "docs/exposure_table.md"
p.write_text("\n".join(L) + "\n")
print("\n".join(L))
