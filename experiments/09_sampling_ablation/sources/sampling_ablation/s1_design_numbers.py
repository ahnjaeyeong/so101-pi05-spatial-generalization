"""A0–A3 표본 강화 설계용 수치 (CPU, 읽기만). d2 데이터셋 · 체크포인트 · 학습 코드는 바꾸지 않는다. 로봇 · GPU 안 씀.

읽기: d2/dataset parquet (state), diag_grasp_bias/grasp_train.csv (닫힘 프레임, 큐브 위치, 그룹),
      vision_probe/labels_v2.csv (닫힘 3 s 안 10 프레임마다 roll · tan 라벨), action_bottleneck/c5_eval_neighbors.csv (평가 정책 프레임),
      d2 020000 scheduler/optimizer 설정 (train_config.json).
계산
  W  프레임 구간 (정지 · 접근 · 정렬 · 닫힘 뒤) 과 roll 15° × tan 0.5 cm 칸 → 실험별 프레임 가중치 (A0 · A1 · A2 · A3)
  S  실험별 구간 · 그룹 · 칸 등급 비율, Kish 유효 표본 수 (프레임 · 판), 노출 횟수, 상위 판 · K 별 쏠림
  E  칸 표 (판 수) · 빈 칸 목록 · 평가 정책 프레임이 빈 칸에 있는 수
  P  판 단위 큐브 방향 (bearing 15°) × 닫힘 roll (15°) 표, K / R 별
  U  미학습 Random 평가 위치 후보 (학습 큐브 256 개에서 ≥ 2 cm — ≥ 3 cm 자리는 볼록 껍질 안에 없음, 학습 위치 볼록 껍질 안, 어려운 영역 · 화면 끝 밖) + 큐브 각도별 필요 손목 회전
  L  LR 스케줄 선택지별 LR 곡선 · 적분 (lerobot CosineDecayWithWarmup 식 그대로)
출력: s1_design_numbers.json, s1_frames.parquet (프레임별 구간 · 칸 · 가중치), s1_cells.csv, s1_untrained_candidates.csv
사용: PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python s1_design_numbers.py
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HOME = Path.home()
D2 = HOME / "so101_runs/main_k8/d2"
OUT = D2 / "sampling_ablation"
sys.path.insert(0, str(D2 / "diag_grasp_bias"))
import common as C  # noqa: E402
import cube_angle as ca  # noqa: E402

FPS = 30
BS, STEPS = 32, 4000                    # 설계안 기본값 (5 절)
D2_SAMPLES = 32 * 20000                 # d2 가 이미 본 표본 수
MOVE_DEG = 3.0                          # 움직이기 시작 = 관절 0–4 중 하나가 첫 프레임에서 3° 넘게 벗어난 첫 프레임
ALIGN_PRE, ALIGN_POST = 3 * FPS, 15     # 정렬 구간 = 닫힘 3 s 전 ~ 닫힘 + 0.5 s
RB = np.arange(-60, 61, 15)
TB = np.arange(-2.5, 2.01, 0.5)
CELL_C, CELL_CAP = 40, 8                # A2 칸 가중 = clip(round(40 / 판 수), 1, 8)
A3_CAPS = (6, 8, 12)                    # A3 상한 완화 후보
U_MIN, N_U, NB_CM = 2.0, 8, 5.0   # 미학습 위치: 학습 큐브에서 ≥ 2 cm, 8 곳, 이웃 = 5 cm 안 학습 판
TIERS = [(0, 0, "없음"), (1, 4, "희소 1–4판"), (5, 14, "얇음 5–14판"), (15, 10 ** 6, "보통 ≥15판")]
W90 = lambda a: ((a + 45) % 90) - 45  # noqa: E731


def tier(n):
    for lo, hi, nm in TIERS:
        if lo <= n <= hi:
            return nm


def move_start(s):
    d = np.abs(s[:, :5] - s[0, :5]).max(1)
    i = np.flatnonzero(d > MOVE_DEG)
    return int(i[0]) if len(i) else 0


def build_frames():
    data = C.load_parquet(D2 / "dataset")
    T = pd.read_csv(D2 / "diag_grasp_bias/grasp_train.csv")
    L = pd.read_csv(D2 / "vision_probe/labels_v2.csv")
    P = L[L.probe_ok].copy()
    P["roll_bin"] = pd.cut(P.roll, RB)
    P["tan_bin"] = pd.cut(P.tan_cm, TB)
    kmap = L.dropna(subset=["K"]).groupby("ep").K.first().to_dict()
    rows = []
    for e, (s, _) in data.items():
        n = len(s)
        gf = int(T.loc[e, "grasp_f"])
        ms = move_start(s)
        ph = np.full(n, "닫힘 뒤", dtype=object)
        ph[:ms] = "정지"
        ph[ms:max(ms, gf - ALIGN_PRE)] = "접근"
        ph[max(ms, gf - ALIGN_PRE):gf + ALIGN_POST] = "정렬"
        lab = P[P.ep == e].sort_values("frame")
        cell_r = np.full(n, None, dtype=object)
        cell_t = np.full(n, None, dtype=object)
        if len(lab):
            lf = lab.frame.values
            for f in range(max(0, gf - ALIGN_PRE), min(n, gf + 1)):
                j = int(np.argmin(np.abs(lf - f)))
                if abs(lf[j] - f) <= 5:
                    cell_r[f], cell_t[f] = str(lab.roll_bin.iloc[j]), str(lab.tan_bin.iloc[j])
        rows.append(pd.DataFrame(dict(ep=e, frame=np.arange(n), group=T.loc[e, "group"], mode=T.loc[e, "mode"],
                                      K=kmap.get(e, ""), phase=ph, roll=s[:, 4], cell_roll=cell_r, cell_tan=cell_t,
                                      ms=ms, gf=gf)))
    F = pd.concat(rows, ignore_index=True)
    return F, T, P


def cell_table(P):
    cnt = P.groupby(["roll_bin", "tan_bin"], observed=False).ep.nunique().unstack(fill_value=0)
    cnt.index = cnt.index.astype(str)
    cnt.columns = cnt.columns.astype(str)
    return cnt


def weights(F, cnt):
    """A0 균일 · A1 접근+정렬 ×3 · A2 Random ×2 × 칸 가중 clip(round(40 / 판 수), 1, 8) · A3 = A1 × A2 (요인 곱, 상한 없음).
    참고 변형: A2r Random ×2 만, A2m 약한 칸 가중 clip(round(15 / 판 수), 1, 4) × Random 2, A3m = min(A1 × A2m, 8)."""
    F["n_cell"] = [int(cnt.loc[r, t]) if r is not None and r != "nan" and t != "nan" else -1
                   for r, t in zip(F.cell_roll, F.cell_tan)]
    a1 = np.where(F.phase.isin(["접근", "정렬"]), 3, 1)
    rnd = np.where(F["mode"] == "R", 2, 1)
    cw = np.where(F.n_cell > 0, np.clip(np.round(CELL_C / np.maximum(F.n_cell, 1)), 1, CELL_CAP), 1)
    cwm = np.where(F.n_cell > 0, np.clip(np.round(15 / np.maximum(F.n_cell, 1)), 1, 4), 1)
    F["w_A0"] = 1
    F["w_A1"] = a1
    F["w_A2"] = (rnd * cw).astype(int)
    F["w_A3"] = (a1 * rnd * cw).astype(int)
    F["w_A2r"] = rnd
    F["w_A2m"] = (rnd * cwm).astype(int)
    F["w_A3m"] = np.minimum(a1 * rnd * cwm, 8).astype(int)
    for cap in A3_CAPS:                                 # A3 완화: A1 × A2 에 상한 (사용자 10-27)
        F[f"w_A3c{cap}"] = np.minimum(a1 * rnd * cw, cap).astype(int)
    return F


def summarize(F, arm):
    w = F[f"w_{arm}"].values.astype(float)
    p = w / w.sum()
    draws = BS * STEPS
    expo = draws * p
    W_e = F.assign(w=w).groupby("ep").w.sum()
    pe = W_e / W_e.sum()
    lab = F.n_cell >= 0
    tiers = F.loc[lab].assign(p=p[lab.values], tier=[tier(n) for n in F.loc[lab, "n_cell"]]).groupby("tier").p.sum()
    kshare = F.assign(p=p)[F.K != ""].groupby("K").p.sum()
    out = dict(
        frames=len(F), sum_w=float(w.sum()),
        phase_share={k: round(float(v), 4) for k, v in F.assign(p=p).groupby("phase").p.sum().items()},
        group_share={k: round(float(v), 4) for k, v in F.assign(p=p).groupby("group").p.sum().items()},
        mode_share={k: round(float(v), 4) for k, v in F.assign(p=p).groupby("mode").p.sum().items()},
        label_window_tier_share={k: round(float(v), 4) for k, v in tiers.items()},
        ess_frames=round(float(w.sum() ** 2 / (w ** 2).sum()), 0),
        ess_frames_frac=round(float(w.sum() ** 2 / (w ** 2).sum() / len(F)), 3),
        ess_episodes=round(float(W_e.sum() ** 2 / (W_e ** 2).sum()), 1),
        top10_episode_share=round(float(pe.sort_values(ascending=False).iloc[:10].sum()), 4),
        max_episode_share=round(float(pe.max()), 4),
        K_share={k: round(float(v), 4) for k, v in kshare.items()},
        exposure_this_run=dict(mean=round(float(expo.mean()), 2), p50=round(float(np.median(expo)), 2),
                               p99=round(float(np.quantile(expo, .99)), 2), max=round(float(expo.max()), 2)),
        exposure_cumulative_max=round(float(D2_SAMPLES / len(F) + expo.max()), 2),
        align_frames_exposure=round(float(expo[(F.phase == "정렬").values].mean()), 2),
        rare_frames_exposure=round(float(expo[((F.n_cell >= 1) & (F.n_cell <= 4)).values].mean()), 2)
        if ((F.n_cell >= 1) & (F.n_cell <= 4)).any() else None,
    )
    return out


def position_table(T):
    T = T.copy()
    T["bear"] = [C.bearing(x, y) for x, y in zip(T.cube_x, T.cube_y)]
    T["bear_bin"] = pd.cut(T.bear, np.arange(-105, 106, 15)).astype(str)
    T["roll_bin"] = pd.cut(T.s_wrist_roll, RB).astype(str)
    res = {}
    for m in ("K", "R"):
        t = T[T["mode"] == m].groupby(["bear_bin", "roll_bin"]).size().unstack(fill_value=0)
        res[m] = t
    return T, res


class MPath:
    """다각형 안 판정 (ray casting) — matplotlib 없이."""

    def __init__(self, poly):
        self.p = np.asarray(poly, float)

    def contains_points(self, pts):
        x, y = pts[:, 0], pts[:, 1]
        ins = np.zeros(len(pts), bool)
        q = self.p
        for i in range(len(q)):
            (x1, y1), (x2, y2) = q[i], q[i - 1]
            c = ((y1 > y) != (y2 > y)) & (x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1)
            ins ^= c
        return ins


def untrained_candidates(T):
    from scipy.spatial import ConvexHull
    xy = T[["cube_x", "cube_y"]].values
    hull = MPath(xy[ConvexHull(xy).vertices])
    hz = [MPath(np.array(z["polygon"])) for z in C.CFG["workspace"].get("hard_zones_cm", [])]
    gx = np.arange(xy[:, 0].min(), xy[:, 0].max() + 1e-6, 0.5)
    gy = np.arange(xy[:, 1].min(), xy[:, 1].max() + 1e-6, 0.5)
    G = np.array([(x, y) for x in gx for y in gy])
    ins = hull.contains_points(G)
    nohz = ~np.any([z.contains_points(G) for z in hz], axis=0) if hz else np.ones(len(G), bool)
    vpx = np.array([C.cm_to_px(x, y)[1] for x, y in G])
    onscreen = vpx >= ca.MIN_Y_PX + 10
    dmin = np.sqrt(((G[:, None, :] - xy[None]) ** 2).sum(-1)).min(1)
    ok = ins & nohz & onscreen
    res = dict(grid_cm=0.5, hull_points=int(ins.sum()), usable=int(ok.sum()),
               frac_ge3=float((dmin[ok] >= 3).mean()), frac_ge4=float((dmin[ok] >= 4).mean()),
               frac_ge5=float((dmin[ok] >= 5).mean()), dmin_usable_max=float(dmin[ok].max()))
    res["dmin_usable_pct"] = {q: round(float(np.quantile(dmin[ok], q / 100)), 2) for q in (50, 90, 99)}
    sel = ok & (dmin >= U_MIN)
    res["frac_ge_U_MIN"] = float(sel[ok].mean())
    cand, cd = G[sel], dmin[sel]
    pick = []
    if len(cand):
        pick = [int(np.argmax(cd))]
        while len(pick) < min(N_U, len(cand)):
            d = np.sqrt(((cand[:, None] - cand[pick][None]) ** 2).sum(-1)).min(1)
            pick.append(int(np.argmax(d)))
    ks = C.load_known()
    kxy = np.array(list(ks.values()))
    kn = list(ks.keys())
    Rxy = T.loc[T["mode"] == "R", ["cube_x", "cube_y"]].values
    neut = float(C.ROB["wrist_roll_neutral_deg"])
    rows = []
    for i, j in enumerate(pick):
        x, y = cand[j]
        b = C.bearing(x, y)
        dk = np.hypot(*(kxy - [x, y]).T)
        dn = np.hypot(*(xy - [x, y]).T)
        nb_roll = T.s_wrist_roll.values[dn <= NB_CM]
        r = dict(id=f"U{i + 1}", x_cm=round(float(x), 1), y_cm=round(float(y), 1), bearing=round(b, 1),
                 range_cm=round(C.rng(x, y), 1), d_train_min=round(float(cd[j]), 1),
                 nearest_K=kn[int(np.argmin(dk))], d_K=round(float(dk.min()), 1),
                 d_R=round(float(np.hypot(*(Rxy - [x, y]).T).min()), 1),
                 front_px=[round(v) for v in C.cm_to_px(x, y)], n_train_within_nb=int(len(nb_roll)),
                 train_roll_within_nb=sorted(round(float(v)) for v in nb_roll))
        for a in ("0", "L30", "R30", "45"):
            need = W90(ca.target_deg(a) - b)
            roll = need + neut
            r[f"need_{a}"] = round(need, 1)
            r[f"novel_{a}"] = round(float(np.min(np.abs(nb_roll - roll))), 1) if len(nb_roll) else None
        rows.append(r)
    return res, pd.DataFrame(rows)


def rare_target(F):
    """희소(1–4판) · 얇음(5–14판) 칸 프레임을 전체 표본의 s 만큼 뽑으려면 필요한 배수 · 노출 (나머지 가중 1)."""
    m = ((F.n_cell >= 1) & (F.n_cell <= 14)).values
    n_r, n = int(m.sum()), len(F)
    out = dict(frames=n_r, eps=int(F[m].ep.nunique()), base_share=round(n_r / n, 4))
    for s in (0.01, 0.025, 0.05, 0.10):
        k = s * (n - n_r) / ((1 - s) * n_r)
        w = np.where(m, k, 1.0)
        out[f"share_{s}"] = dict(mult=round(k, 1), exposure_per_rare_frame_4k=round(BS * STEPS * k / w.sum(), 1),
                                ess_frac=round(float(w.sum() ** 2 / (w ** 2).sum() / n), 3))
    return out


def lr_curve(peak, decay_lr, warm, decay, steps, offset=0):
    """lerobot CosineDecayWithWarmupSchedulerConfig.build 그대로 (자동 축소 포함). offset = 재개 시작 step."""
    aw, ad = warm, decay
    if steps < decay:
        sf = steps / decay
        aw, ad = int(warm * sf), steps
    out = []
    for t in range(offset, steps):
        if t < aw:
            lam = (1 / (aw + 1) - 1) * (1 - t / aw) + 1 if t > 0 else 1 / (aw + 1)
        else:
            st = min(t, ad)
            lam = (1 - decay_lr / peak) * 0.5 * (1 + math.cos(math.pi * st / ad)) + decay_lr / peak
        out.append(peak * lam)
    return np.array(out)


def lr_options():
    d2 = lr_curve(2.5e-5, 2.5e-6, 1000, 30000, 20000)
    opts = {
        "d2 원래 (0→20k)": d2,
        "R1 재개 --steps 24000 (그대로)": lr_curve(2.5e-5, 2.5e-6, 1000, 30000, 24000, offset=20000),
        "R2 재개 --steps 24000 --scheduler.num_decay_steps 20000": lr_curve(2.5e-5, 2.5e-6, 1000, 20000, 24000, offset=20000),
        "F1 새 FT peak 1e-5 · warmup 200 · cosine→2.5e-6 / 4k": lr_curve(1e-5, 2.5e-6, 200, 4000, 4000),
        "F2 새 FT peak 2.5e-5 · warmup 200 · cosine→2.5e-6 / 4k": lr_curve(2.5e-5, 2.5e-6, 200, 4000, 4000),
        "F3 새 FT 일정 2.5e-6 (warmup 200)": np.r_[np.linspace(2.5e-6 / 201, 2.5e-6, 200), np.full(3800, 2.5e-6)],
    }
    tot = float(d2.sum())
    return {k: dict(first=float(v[0]), at_100=float(v[min(100, len(v) - 1)]), mean=float(v.mean()), last=float(v[-1]),
                    integral=float(v.sum()), frac_of_d2_integral=round(float(v.sum()) / tot, 4)) for k, v in opts.items()}


def main():
    F, T, P = build_frames()
    cnt = cell_table(P)
    cnt.to_csv(OUT / "s1_cells.csv")
    F = weights(F, cnt)
    res = dict(constants=dict(BS=BS, STEPS=STEPS, MOVE_DEG=MOVE_DEG, ALIGN=[-ALIGN_PRE, ALIGN_POST], CELL_C=CELL_C,
                              CELL_CAP=CELL_CAP, d2_epochs=round(D2_SAMPLES / len(F), 3)))
    res["phase_len_s"] = {k: (F[F.phase == k].groupby("ep").size() / FPS).describe().round(2).to_dict()
                          for k in ("정지", "접근", "정렬", "닫힘 뒤")}
    res["label_cover"] = dict(align_frames=int((F.phase == "정렬").sum()), labelled=int((F.n_cell >= 0).sum()),
                              labelled_eps=int(F[F.n_cell >= 0].ep.nunique()))
    res["arms"] = {a: summarize(F, a) for a in ("A0", "A1", "A2", "A3", "A2r", "A2m", "A3m") + tuple(f"A3c{c}" for c in A3_CAPS)}
    # 칸 표 · 빈 칸 · 평가 정책 프레임
    E = pd.read_csv(D2 / "action_bottleneck/c5_eval_neighbors.csv")
    E["roll_bin"] = pd.cut(E.roll, RB).astype(str)
    E["tan_bin"] = pd.cut(E.tan_cm, TB).astype(str)
    ecnt = E.groupby(["roll_bin", "tan_bin"]).size()
    e_out = int(E.tan_bin.eq("nan").sum() + E.roll_bin.eq("nan").sum())
    cells = []
    for r in cnt.index:
        for t in cnt.columns:
            n = int(cnt.loc[r, t])
            cells.append(dict(roll=r, tan=t, eps=n, tier=tier(n), eval_frames=int(ecnt.get((r, t), 0)),
                              w_A2=int(np.clip(round(CELL_C / n), 1, CELL_CAP)) if n else 0))
    Cdf = pd.DataFrame(cells)
    res["cells"] = dict(n=len(Cdf), by_tier=Cdf.groupby("tier").size().to_dict(),
                        eval_frames_by_tier=Cdf.groupby("tier").eval_frames.sum().to_dict(),
                        eval_frames_outside_grid=e_out, eval_frames_total=len(E),
                        rare_eps_unique=int(F[(F.n_cell >= 1) & (F.n_cell <= 4)].ep.nunique()))
    res["cells_table"] = Cdf.to_dict("records")
    # 판 단위 방향 × roll
    T2, pt = position_table(T)
    res["position_roll"] = {m: dict(rows=list(t.index), cols=list(t.columns), table=t.values.tolist()) for m, t in pt.items()}
    allc = sorted(set(T2.bear_bin) | set()), sorted(set(T2.roll_bin))
    both = T2.groupby(["bear_bin", "roll_bin"]).size().unstack(fill_value=0)
    res["position_roll"]["all"] = dict(rows=list(both.index), cols=list(both.columns), table=both.values.tolist())
    del allc
    # 미학습 위치
    ures, U = untrained_candidates(T)
    U.to_csv(OUT / "s1_untrained_candidates.csv", index=False)
    res["untrained"] = ures | dict(candidates=U.to_dict("records"))
    res["rare_target"] = rare_target(F)
    res["lr"] = lr_options()
    F.drop(columns=["cell_roll", "cell_tan"]).assign(cell_roll=F.cell_roll.astype(str), cell_tan=F.cell_tan.astype(str)) \
        .to_parquet(OUT / "s1_frames.parquet")
    json.dump(res, open(OUT / "s1_design_numbers.json", "w"), indent=1, ensure_ascii=False, default=str)
    for k in ("constants", "phase_len_s", "label_cover"):
        print(k, json.dumps(res[k], ensure_ascii=False))
    for a, v in res["arms"].items():
        print(a, json.dumps(v, ensure_ascii=False))
    print("cells", json.dumps(res["cells"], ensure_ascii=False))
    for m in ("K", "R"):
        print(m, "\n", pt[m].to_string())
    print("rare_target", json.dumps(res["rare_target"], ensure_ascii=False))
    print("untrained", json.dumps(ures, ensure_ascii=False))
    print(U.to_string())
    for k, v in res["lr"].items():
        print(k, json.dumps(v))


if __name__ == "__main__":
    main()
