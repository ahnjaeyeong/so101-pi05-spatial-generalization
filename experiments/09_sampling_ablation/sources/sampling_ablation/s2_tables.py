"""s1_design_numbers.json → 설계 문서용 markdown 표 (s2_tables.md). 숫자는 json 에서만 가져온다."""
import json
from pathlib import Path

import pandas as pd

OUT = Path(__file__).parent
r = json.load(open(OUT / "s1_design_numbers.json"))
L = []
A = r["arms"]
arms = ["A0", "A1", "A2", "A2r", "A3", "A3c12"]
ref = ["A3c8", "A3c6", "A2m"]


def pct(x):
    return f"{100 * x:.1f}"


L.append("### 표 1. 실험별 표본 비율 (뽑힐 확률, %) · 유효 표본 수\n")
L.append("| 항목 | " + " | ".join(arms) + " | 참고 " + " | 참고 ".join(ref) + " |")
L.append("|---|" + "---|" * (len(arms) + len(ref)))
rows = [("구간 정지", lambda v: pct(v["phase_share"].get("정지", 0))),
        ("구간 접근", lambda v: pct(v["phase_share"].get("접근", 0))),
        ("구간 정렬 (닫힘 −3 s ~ +0.5 s)", lambda v: pct(v["phase_share"].get("정렬", 0))),
        ("구간 닫힘 뒤", lambda v: pct(v["phase_share"].get("닫힘 뒤", 0))),
        ("K 판 / R 판", lambda v: f"{pct(v['mode_share']['K'])} / {pct(v['mode_share']['R'])}"),
        ("T1K · T1R · T3K · T3R", lambda v: " · ".join(pct(v["group_share"][g]) for g in ("T1K", "T1R", "T3K", "T3R"))),
        ("K 하나당 (최소–최대)", lambda v: f"{pct(min(v['K_share'].values()))}–{pct(max(v['K_share'].values()))}"),
        ("정렬 라벨 칸: 보통 ≥15판", lambda v: pct(v["label_window_tier_share"].get("보통 ≥15판", 0))),
        ("정렬 라벨 칸: 얇음 5–14판", lambda v: pct(v["label_window_tier_share"].get("얇음 5–14판", 0))),
        ("정렬 라벨 칸: 희소 1–4판", lambda v: pct(v["label_window_tier_share"].get("희소 1–4판", 0))),
        ("유효 프레임 수 (Kish) / 비율", lambda v: f"{int(v['ess_frames']):,} / {v['ess_frames_frac']:.2f}"),
        ("유효 판 수 (Kish, 판 합계 가중)", lambda v: f"{v['ess_episodes']:.0f}"),
        ("상위 10 판 몫 / 최대 판 몫", lambda v: f"{pct(v['top10_episode_share'])} / {pct(v['max_episode_share'])}"),
        ("4k step 노출 (프레임당 중앙 / 99 % / 최대)", lambda v: f"{v['exposure_this_run']['p50']} / {v['exposure_this_run']['p99']} / {v['exposure_this_run']['max']}"),
        ("정렬 프레임 평균 노출 / 희소 칸 프레임 평균 노출", lambda v: f"{v['align_frames_exposure']} / {v['rare_frames_exposure']}"),
        ("d2 5.19 epoch 포함 누적 최대 노출", lambda v: f"{v['exposure_cumulative_max']}")]
for nm, f in rows:
    L.append(f"| {nm} | " + " | ".join(f(A[a]) for a in arms + ref) + " |")

L.append("\n### 표 2. roll 15° × tan 0.5 cm 칸 — 닫힘 3 s 안 사람 판 수 (괄호 = 평가 정책 프레임 수)\n")
L.append("표기: **0** = 기존 데이터에 없음 (재표집으로 만들 수 없음), *n* = 희소 1–4판 (A2 가중 ×8), 5–14 = 얇음, ≥15 = 보통.\n")
C = pd.DataFrame(r["cells_table"])
tans = list(dict.fromkeys(C.tan))
rolls = list(dict.fromkeys(C.roll))
L.append("| roll \\ tan (cm) | " + " | ".join(tans) + " |")
L.append("|---|" + "---|" * len(tans))
for ro in rolls:
    cells = []
    for t in tans:
        x = C[(C.roll == ro) & (C.tan == t)].iloc[0]
        s = "**0**" if x.eps == 0 else (f"*{x.eps}*" if x.eps <= 4 else str(x.eps))
        if x.eval_frames:
            s += f" ({x.eval_frames})"
        cells.append(s)
    L.append(f"| {ro} | " + " | ".join(cells) + " |")
c = r["cells"]
L.append(f"\n- 칸 {c['n']} 개: 없음 {c['by_tier'].get('없음', 0)}, 희소 {c['by_tier'].get('희소 1–4판', 0)}, 얇음 {c['by_tier'].get('얇음 5–14판', 0)}, 보통 {c['by_tier'].get('보통 ≥15판', 0)}. 희소 칸 프레임을 가진 판 {c['rare_eps_unique']} 개.")
L.append(f"- 평가 정책 프레임 (d2 20k try3 · filt, 닫힘 3 s 안, QC 통과) {c['eval_frames_total']} 개: 보통 칸 {c['eval_frames_by_tier'].get('보통 ≥15판', 0)}, 얇음 {c['eval_frames_by_tier'].get('얇음 5–14판', 0)}, 희소 {c['eval_frames_by_tier'].get('희소 1–4판', 0)}, 없음 {c['eval_frames_by_tier'].get('없음', 0)}, 표 밖 (tan ≤ −2.5 또는 > 2.0 cm) {c['eval_frames_outside_grid']}.")
rt = r["rare_target"]
L.append(f"- 얇음+희소 칸 프레임 {rt['frames']:,} 개 ({rt['eps']} 판), 균일 표집에서 몫 {pct(rt['base_share'])} %. 이 몫을 s 로 올리는 데 필요한 배수 (나머지 1): " +
         ", ".join(f"{float(k[6:]) * 100:g} % → ×{v['mult']} (4k step 프레임당 노출 {v['exposure_per_rare_frame_4k']}, 유효 비율 {v['ess_frac']})" for k, v in rt.items() if k.startswith("share_")) + ".")

L.append("\n### 표 3. 판 단위 큐브 방향 (bearing 15°) × 닫힘 순간 wrist_roll state (15°) — 판 수, K / R\n")
for m in ("K", "R"):
    t = r["position_roll"][m]
    lo = lambda b: float(b.strip("([").split(",")[0]) if b != "nan" else 1e9  # noqa: E731
    ci = sorted(range(len(t["cols"])), key=lambda i: lo(t["cols"][i]))
    ri = sorted(range(len(t["rows"])), key=lambda i: lo(t["rows"][i]))
    cols = [t["cols"][i] for i in ci]
    t = dict(rows=[t["rows"][i] for i in ri], table=[[t["table"][i][j] for j in ci] for i in ri])
    L.append(f"**{m}**\n")
    L.append("| bearing \\ roll | " + " | ".join(cols) + " |")
    L.append("|---|" + "---|" * len(cols))
    for rn, row in zip(t["rows"], t["table"]):
        L.append(f"| {rn} | " + " | ".join("**0**" if v == 0 else str(v) for v in row) + " |")
    L.append("")

u = r["untrained"]
L.append("### 표 4. 미학습 위치 후보 (학습 큐브 256 개에서 ≥ 2 cm, 학습 위치 볼록 껍질 안, 어려운 영역 · 화면 끝 제외)\n")
L.append(f"- 0.5 cm 격자 {u['usable']:,} 점 중 가장 가까운 학습 큐브까지: 중앙값 {u['dmin_usable_pct']['50']} cm, 90 % {u['dmin_usable_pct']['90']}, 99 % {u['dmin_usable_pct']['99']}, 최대 {u['dmin_usable_max']:.2f} cm. ≥ 3 cm 인 점 {u['frac_ge3']:.0%}, ≥ 2 cm {u['frac_ge_U_MIN']:.1%}.")
L.append("- 필요 회전 need = wrap90(큐브 각도 − bearing) (check_dataset.roll_check 와 같은 식), 새로움 = |need + 중립(−1.5°) − 5 cm 안 학습 판 닫힘 roll| 의 최솟값.\n")
L.append("| id | x, y (cm) | bearing | 최근접 학습 / K / R (cm) | 5 cm 안 학습 판 | need 0 (새로움) | need L30 | need R30 | need 45 |")
L.append("|---|---|---|---|---|---|---|---|---|")
for x in u["candidates"]:
    nv = lambda a: f"{x[f'need_{a}']} ({x[f'novel_{a}']})"  # noqa: E731
    L.append(f"| {x['id']} | {x['x_cm']}, {x['y_cm']} | {x['bearing']} | {x['d_train_min']} / {x['nearest_K']} {x['d_K']} / {x['d_R']} | {x['n_train_within_nb']} | {nv('0')} | {nv('L30')} | {nv('R30')} | {nv('45')} |")

L.append("\n### 표 5. LR 선택지 (lerobot CosineDecayWithWarmup 식, 4k step)\n")
L.append("| 선택지 | 첫 step | 100 step | 평균 | 마지막 | 적분 (Σ lr) | d2 20k 적분 대비 |")
L.append("|---|---|---|---|---|---|---|")
for k, v in r["lr"].items():
    L.append(f"| {k} | {v['first']:.2e} | {v['at_100']:.2e} | {v['mean']:.2e} | {v['last']:.2e} | {v['integral']:.4f} | {v['frac_of_d2_integral']:.3f} |")
(OUT / "s2_tables.md").write_text("\n".join(L) + "\n")
print("\n".join(L))
