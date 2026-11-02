"""p17 독립 안전 정지 조건 후보의 오프라인 평가 (읽기만, CPU). **제어 코드는 바꾸지 않는다 — 기록에 조건을 대 보기만 한다.**

후보 (모두 필터 · RTC 와 무관하게 '정책 출력 (queue raw)' 과 '실제 위치' 만 본다):
  S1 관절 위치 범위: 팔 관절 state 가 d2 학습 시연 전체 state 범위 밖으로 3° 넘게 나감
  S2 명령 범위: queue raw 명령이 학습 범위 밖으로 10° 넘게 나간 틱이 5 틱 연속
  S3 한계 버팀: 팔 관절 |raw − state| > 8° 이고 |Δstate| < 0.3°/틱 인 틱이 15 틱 (0.5 s) 연속 (guard 의 stall 과 같은 뜻이지만 필터 out 이 아닌 raw 기준)
  S4 큐브 놓치고 계속 회전: 아직 쥔 적 없는 구간 (그리퍼 ≥ 9 로 1 s 유지한 닫힘 전) 에서 손목 영상에 큐브가 1 s 넘게 안 보이고,
     그동안 pan 이 한 방향으로 30° 넘게 움직임 (손목 영상 0.2 s 간격 검사)
  S4b S4 와 같되 '그 전에 손목 영상에 큐브가 0.4 s 이상 보인 적이 있음' (본 뒤 놓침) 을 더한 것
  S5 목표 넘어 회전: 판 시작 사진 좌표로 정한 pe (정책 행동 안 씀) 를 지나 '시작 → pe 방향' 으로 30° 넘게 더 간 pan state
판마다 각 조건이 처음 걸린 시각과, 그때 pan state. pan 이 −105° 에 처음 닿은 시각과 비교.
대상: diag 기록 실행 4 개 (파일럿 2 · K1 필터 켬/끔 2) 의 모든 시도 (버린 시도 포함).
출력: filter_ab/p17_safety_offline.csv, p17_train_range.json
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python p17_safety_stop_offline.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import cube_coords as CC  # noqa: E402
import p14_grasp_analysis as P14  # noqa: E402

ac, C = CC.ac, CC.C
D2 = CC.D2
AB = D2 / "pan_inference_diagnostic/filter_ab"
ROLL = D2 / "eval/rollouts"
RUNS = ["20261029_155513_32_20000_20k_pan_diag", "20261029_160831_32_20000_20k_pan_diag",
        "20261029_170219_32_20000_20k_filt_on", "20261029_170818_32_20000_20k_filt_off"]
J = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]


def first_run(mask, n):
    run = 0
    for i, m in enumerate(mask):
        run = run + 1 if m else 0
        if run >= n:
            return i - n + 1
    return None


def main():
    import p07_new_eval_analysis as P7
    D = ac.load_d2()
    allst = np.concatenate([v[0] for v in D.values()])
    lo, hi = allst.min(0), allst.max(0)
    json.dump({j: [float(lo[k]), float(hi[k])] for k, j in enumerate(J)}, open(AB / "p17_train_range.json", "w"), indent=1)
    cache, rows = {}, []
    for run in RUNS:
        R = ROLL / run
        FL = pd.read_csv(R / "filter_log.csv", dtype={"vclip_mask": str, "ema_reset_mask": str})
        FL = FL[FL.event == "cmd"]
        att = P7.attempts(R)
        eps = sorted(FL.episode.unique())
        amap = dict(zip(eps, att)) if len(att) == len(eps) else {e: (k, "?") for k, e in enumerate(eps)}
        for e in eps:
            f = FL[FL.episode == e].sort_values("tick").reset_index(drop=True)
            raw = f[[f"raw_{j}" for j in J]].values.astype(float)
            st = f[[f"state_{j}" for j in J]].values.astype(float)
            n = len(f)
            ds_ep, status = amap[e]
            r = dict(run=run[-24:], episode=int(e), ds_ep=ds_ep, attempt=status, n_ticks=n, pan_min=float(st[:, 0].min()), pan_max=float(st[:, 0].max()))
            hit = np.where(st[:, 0] <= -105)[0]
            r["t_pan_le_m105_s"] = float(hit[0] / 30) if len(hit) else None
            arm = slice(0, 5)
            s1 = np.where(((st[:, arm] < lo[arm] - 3) | (st[:, arm] > hi[arm] + 3)).any(1))[0]
            r["S1_s"] = float(s1[0] / 30) if len(s1) else None
            s2 = first_run(((raw[:, arm] < lo[arm] - 10) | (raw[:, arm] > hi[arm] + 10)).any(1), 5)
            r["S2_s"] = None if s2 is None else s2 / 30
            dst = np.vstack([np.zeros((1, 6)), np.abs(np.diff(st, axis=0))])
            s3 = first_run(((np.abs(raw[:, arm] - st[:, arm]) > 8) & (dst[:, arm] < 0.3)).any(1), 15)
            r["S3_s"] = None if s3 is None else s3 / 30
            # S4: 저장된 시도만 dataset 영상이 있다
            r["S4_s"] = None
            if status == "saved":
                g = st[:, 5]
                cl = C.close_events(g)
                held_t = next((c for c in cl if g[c:c + 30].min() >= 9), n)
                vis = []
                for fr in range(0, min(held_t, n), 6):
                    w = P14.wrist_measure(C.frames(R / "dataset", ds_ep, "wrist", fr, fr, cache)[0])
                    vis.append((fr, bool(w.get("w_vis"))))
                fr_all = [v[0] for v in vis]
                r["S4b_s"] = None
                seen = 0
                for q in range(len(vis)):
                    seen = seen + 1 if vis[q][1] else seen
                    if vis[q][1] or seen < 2 or r["S4b_s"] is not None:
                        continue
                    k = q
                    while k < len(vis) and not vis[k][1]:
                        k += 1
                    a, b = fr_all[q], fr_all[k - 1]
                    if b - a >= 30:
                        for t2 in range(a + 30, b + 1):
                            if abs(st[t2, 0] - st[a, 0]) >= 30:
                                r["S4b_s"] = t2 / 30
                                break
                for q in range(len(vis)):
                    if vis[q][1]:
                        continue
                    k = q
                    while k < len(vis) and not vis[k][1]:
                        k += 1
                    a, b = fr_all[q], fr_all[k - 1]
                    if b - a >= 30:
                        seg = st[a:b + 1, 0]
                        d = np.diff(seg)
                        mono = max(d[d < 0].sum() * -1, d[d > 0].sum())
                        if abs(seg[-1] - seg[0]) >= 30 and mono >= 30:
                            # 1 s 지난 뒤 처음 30° 를 넘긴 틱
                            for t2 in range(a + 30, b + 1):
                                if abs(st[t2, 0] - st[a, 0]) >= 30:
                                    r["S4_s"] = t2 / 30
                                    break
                            if r["S4_s"] is not None:
                                break
                r["held_t_s"] = held_t / 30 if held_t < n else None
                img = R / "start_images" / f"ep{ds_ep:03d}_front.png"
                if img.exists():
                    import cv2
                    c = CC.estimate(cv2.cvtColor(cv2.imread(str(img)), cv2.COLOR_BGR2RGB))
                    if c.get("pe") is not None:
                        pe, s0 = c["pe"], st[0, 0]
                        sg = np.sign(pe - s0)
                        over = sg * (st[:, 0] - pe)
                        k5 = np.where(over > 30)[0]
                        r.update(pe=pe, max_overshoot=float(over.max()), S5_s=float(k5[0] / 30) if len(k5) else None)
            for k in ("S1", "S2", "S3", "S4", "S4b", "S5"):
                r.setdefault(f"{k}_s", None)
                t = r[f"{k}_s"]
                r[f"{k}_pan"] = float(st[int(t * 30), 0]) if t is not None else None
            rows.append(r)
            print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()}, flush=True)
    P = pd.DataFrame(rows)
    P.to_csv(AB / "p17_safety_offline.csv", index=False)
    print({j: (round(float(lo[k]), 1), round(float(hi[k]), 1)) for k, j in enumerate(J)})


if __name__ == "__main__":
    main()
