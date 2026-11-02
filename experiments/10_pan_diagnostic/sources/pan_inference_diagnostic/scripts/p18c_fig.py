"""p18c 그림 (시스템 python3): figs/fig8_k1_descent_paths.png — 닫힘 이벤트마다 하강 구간 FK 상대 경로 (수평 순이동 방향 vs 높이).
FK 는 상대 이동만 · 이 그림은 '명령 · 실제 관절이 만드는 FK 경로 모양' 이지 측정된 TCP 궤적이 아니다.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

OUT = Path.home() / "so101_runs/main_k8/d2/pan_inference_diagnostic"
BLUE, ORANGE, AQUA, YELLOW, INK2, GRID, SURF = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "axes.grid": True, "grid.color": GRID, "axes.spines.top": False,
                     "axes.spines.right": False, "font.size": 9, "axes.unicode_minus": False})
from matplotlib import font_manager  # noqa: E402
for nm in ("NanumGothic", "Noto Sans CJK KR", "Noto Sans KR"):
    if any(nm in f.name for f in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = nm
        break
D = pd.read_csv(OUT / "filter_ab/p18_fk_ticks.csv")
S = pd.read_csv(OUT / "filter_ab/p18_paths.csv")
ev = D[["tag", "event", "cond", "bottom"]].drop_duplicates().sort_values(["cond", "tag", "event"], ascending=[False, True, True])
fig, axs = plt.subplots(2, 4, figsize=(16, 7.5))
for ax, (_, e) in zip(axs.ravel(), ev.iterrows()):
    for nm, c, lw in (("rtc", YELLOW, 1.2), ("out", AQUA, 1.6), ("present", BLUE, 2.4), ("cf_out", ORANGE, 1.2)):
        d = D[(D.tag == e.tag) & (D.event == e.event) & (D.signal == nm)]
        if not len(d):
            continue
        h = np.hypot(d.radial, d.tangential)
        ax.plot(h, d.dz, color=c, lw=lw, label={"rtc": "RTC 뒤 명령", "out": "필터 뒤 명령 (켬)", "present": "실제 관절 (FK)", "cf_out": "반사실: 끔 명령에 필터"}[nm])
        ax.plot(h.iloc[-1], d.dz.iloc[-1], "o", color=c, ms=5)
    t = S[(S.tag == e.tag) & (S.event == e.event) & (S.signal == "present")].iloc[0]
    r = S[(S.tag == e.tag) & (S.event == e.event) & (S.signal == "rtc")].iloc[0]
    res = "쥠" if e.bottom >= 9 else "빈 닫힘"
    ax.set_title(f"{e.tag} #{e.event} 필터 {e.cond} · {res}\n실제 기울기 {t.tilt_deg:.0f}° · 명령 {r.tilt_deg:.0f}°", fontsize=9)
    ax.set_xlabel("수평 이동 크기 (cm, FK 상대)")
    ax.set_ylabel("높이 변화 (cm, FK 상대)")
    ax.set_xlim(-0.2, 4.5)
    ax.set_ylim(-4.5, 0.6)
for ax in axs.ravel()[len(ev):]:
    ax.axis("off")
axs.ravel()[0].legend(fontsize=7, frameon=False, loc="lower right")
h = [l for l in axs.ravel()[5].get_lines() if not l.get_label().startswith("_")]
axs.ravel()[5].legend(h, [l.get_label() for l in h], fontsize=7, frameon=False, loc="lower right")
fig.suptitle("K1 첫 닫힘 전 하강 구간 (높이 최고점 → 그리퍼 닫힘 명령): FK 상대 경로. 세로로 곧으면 수직 하강, 오른쪽으로 누우면 사선. 측정 궤적 아님", fontsize=10)
fig.tight_layout()
fig.savefig(OUT / "figs/fig8_k1_descent_paths.png", dpi=120)
print("ok")
