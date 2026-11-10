"""성능 요약: _out_perf 의 Cadence 요약 (tap 없음 vs tap+화면) + 480×640 프레임 tap 쓰기 · 화면 그리기 벤치 (CPU). 결과 <dir>/PERF.md"""
import io
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H.parent / "tools"))
P = Path(sys.argv[1])
rows = []
for f in sorted(P.glob("*.console.log")):
    t = f.read_text(errors="replace")
    m = re.search(r"effective cadence: ([\d.]+) Hz over ([\d.]+) s measured", t)
    o = re.search(r"ticks over the [\d.]+ ms work budget: (\d+)/(\d+) \(([\d.]+)%\) — work mean ([\d.]+) ms, worst ([\d.]+) ms", t)
    sl = re.search(r"ticks whose cadence slipped outside the loop body[^:]*: (\d+)", t)
    st = re.search(r"ticks with no action to send[^:]*: (\d+)", t)
    rows.append({"run": f.stem.replace(".console", ""), "hz": float(m.group(1)) if m else None, "over": f"{o.group(1)}/{o.group(2)}" if o else None,
                 "work_mean_ms": float(o.group(4)) if o else None, "work_worst_ms": float(o.group(5)) if o else None,
                 "slipped": int(sl.group(1)) if sl else None, "starved": int(st.group(1)) if st else None})
    ev = P / f.stem.replace(".console", "") / "S7_adapter_normal/hil_events.jsonl"
    if ev.exists():
        ts = [json.loads(x) for x in ev.read_text().splitlines() if '"tap_stats"' in x]
        if ts:
            rows[-1]["tap_mean_ms"], rows[-1]["tap_p99_ms"], rows[-1]["tap_max_ms"] = ts[-1]["mean_ms"], ts[-1]["p99_ms"], ts[-1]["max_ms"]
    res = P / f.stem.replace(".console", "") / "S7_adapter_normal/result.json"
    if res.exists():
        r = json.loads(res.read_text())
        rows[-1]["checks"] = f"{sum(c['pass'] for c in r['checks'].values())}/{len(r['checks'])}"

# 480×640 tap 쓰기 벤치 (adapter _tap_loop 의 영상 경로와 같은 연산: 1/2 축소 + np.save + 원자적 교체)
d = Path(tempfile.mkdtemp(dir="/dev/shm"))
rng = np.random.default_rng(0)
imgs = [rng.integers(0, 255, (480, 640, 3), dtype=np.uint8) for _ in range(4)]
tw = []
for i in range(200):
    t0 = time.perf_counter()
    for cam, img in (("wrist", imgs[i % 4]), ("front", imgs[(i + 1) % 4])):
        small = np.ascontiguousarray(img[::2, ::2])
        buf = io.BytesIO()
        np.save(buf, small)
        tmp = d / f"{cam}.npy.tmp"
        tmp.write_bytes(buf.getvalue())
        os.replace(tmp, d / f"{cam}.npy")
    tw.append(time.perf_counter() - t0)
for f in d.iterdir():
    f.unlink()
d.rmdir()
# 그리기 벤치 (화면 프로세스): 240×320 프레임 2 장 + 교정 중 상태
import hil_ui_preview as PV  # noqa: E402
import hil_ui_render as R  # noqa: E402
import hil_ui_state as U  # noqa: E402

raw, _ = PV.raw_for("07_correcting_R2", time.perf_counter())
fr = {"wrist": imgs[0][::2, ::2], "front": imgs[1][::2, ::2]}
rw = []
for i in range(40):
    raw["t"] = time.perf_counter()
    t0 = time.perf_counter()
    R.render(U.derive(raw, raw["t"]), raw, fr, "LIVE")
    rw.append(time.perf_counter() - t0)
a, b = np.array(tw) * 1000, np.array(rw) * 1000
L = ["# UI 성능 (bench_ui.py 자동 생성)", "", "## 같은 조작 (S7) — lerobot Cadence 요약 (30 Hz 목표, 33.3 ms 예산)", "",
     "| 실행 | 실효 Hz | 예산 넘은 틱 | 틱 작업 평균 ms | 최악 ms | 루프 밖 밀림 틱 | 명령 없는 틱 | tap 1 회 mean / p99 / max ms | 검사 |", "|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    tp = f"{r.get('tap_mean_ms', '-')} / {r.get('tap_p99_ms', '-')} / {r.get('tap_max_ms', '-')}"
    L.append(f"| {r['run']} | {r['hz']} | {r['over']} | {r['work_mean_ms']} | {r['work_worst_ms']} | {r['slipped']} | {r['starved']} | {tp} | {r.get('checks', '-')} |")
for mode in ("notap", "tap"):
    sel = [r for r in rows if r["run"].startswith(mode) and r["hz"]]
    if sel:
        L.append(f"| **{mode} 평균** | {np.mean([r['hz'] for r in sel]):.2f} | | {np.mean([r['work_mean_ms'] for r in sel]):.2f} | {np.mean([r['work_worst_ms'] for r in sel]):.2f} | {np.mean([r['slipped'] for r in sel]):.1f} | | | |")
L += ["", "## 480×640 프레임 기준 (CPU, Jetson)", "",
      f"- tap 영상 쓰기 (front+wrist, 1/2 축소 + np.save + 교체, /dev/shm): mean {a.mean():.2f} ms · p99 {np.percentile(a, 99):.2f} ms · max {a.max():.2f} ms (n 200) — 10 Hz 기준 초당 {a.mean() * 10:.1f} ms",
      f"- 화면 그리기 1 장 (1400×940, 240×320 프레임 2 장, 교정 중 화면, 별도 프로세스): mean {b.mean():.1f} ms · p99 {np.percentile(b, 99):.1f} ms · max {b.max():.1f} ms (n 40)",
      "", "가짜 장치 시험의 카메라는 64×48 이다. 실제 480×640 카메라 · π0.5 GPU 추론과 함께 돌 때의 제어 주기는 측정하지 않았다 (실물 미검증)."]
(P / "PERF.md").write_text("\n".join(L) + "\n")
print("\n".join(L))
