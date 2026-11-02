"""image_quality.py 결과 분석 (CPU, 읽기만) → iq_summary.json + 화면 출력.
  1) 단계·카메라별 크기·밝기·대비·흐림 (π0.5 224 입력 기준과 640 원본)
  2) 라벨 오차 vs 품질
     front: Known 판 start 프레임 큐브 중심 → H → cm, K 좌표와의 거리 (K 에 놓은 오차 ±0.5 cm 포함)
     wrist: labels_v2 마지막 3 s 라벨(rel_u/v_cm)을 판마다 시간 2차식으로 맞춘 잔차 크기 (검출 흔들림 대리값)
     → 품질 3분위별 중앙값 + Spearman
  3) 학습 vs 평가 분포: 평가 판 값의 학습 분포 백분위
  front 224 입력에서 1 cm 이동이 몇 px 인지: H 의 국소 야코비안 × 0.35
"""
import json, math, sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
sys.path.insert(0, str(Path.home() / "so101_runs/main_k8/d2/diag_grasp_bias"))
import common as C  # noqa: E402
OUT = Path(__file__).resolve().parent


def px_per_cm_front(x, y):
    u0, v0 = C.cm_to_px(x, y); u1, v1 = C.cm_to_px(x + 0.5, y); u2, v2 = C.cm_to_px(x, y + 0.5)
    return float((math.hypot(u1 - u0, v1 - v0) + math.hypot(u2 - u0, v2 - v0)) / 2 / 0.5)


def tert(d, q, y):
    d = d[[q, y]].dropna()
    if len(d) < 30:
        return None
    b = pd.qcut(d[q], 3, labels=["low", "mid", "high"], duplicates="drop")
    rho, p = stats.spearmanr(d[q], d[y])
    return dict(n=len(d), by_tertile={str(k): float(v) for k, v in d.groupby(b, observed=True)[y].median().items()}, spearman=float(rho), p=float(p))


def main():
    D = pd.read_csv(OUT / "iq_frames.csv", low_memory=False)
    S = {}
    tr = D[D.src == "train"]
    # front 224: 1 cm = ? px
    st = tr[(tr.cam == "front") & (tr.phase == "start")]
    ppc = np.array([px_per_cm_front(x, y) for x, y in zip(st.cube_x, st.cube_y)])
    S["front_px_per_cm_640"] = dict(median=float(np.median(ppc)), p10=float(np.percentile(ppc, 10)), p90=float(np.percentile(ppc, 90)))
    S["front_px_per_cm_224"] = {k: v * 0.35 for k, v in S["front_px_per_cm_640"].items()}
    w = tr[(tr.cam == "wrist") & tr.o_area.notna()]
    S["wrist_px_per_cm_224_by_phase"] = {ph: float((np.sqrt(g.o_area) / 2.5 * 0.35).median()) for ph, g in w.groupby("phase")}
    # 2a front label error (Known)
    K = C.load_known()
    f = st[st.group.str.endswith("K") & st.o_u.notna()].copy()
    errs = []
    for _, r in f.iterrows():
        x, y = C.px_to_cm(r.o_u, r.o_v)
        k = min(K, key=lambda q: math.hypot(x - K[q][0], y - K[q][1]))
        errs.append(math.hypot(x - K[k][0], y - K[k][1]))
    f["front_err_cm"] = errs
    S["front_label_err_cm"] = dict(n=len(f), median=float(np.median(errs)), p90=float(np.percentile(errs, 90)))
    S["front_err_vs_quality"] = {q: tert(f, q, "front_err_cm") for q in ("m_w", "o_cube_V", "o_dE", "o_edge_grad_per_dE", "o_lapvar")}
    # 2b wrist label jitter
    L = pd.read_csv(OUT / "labels_v2.csv", low_memory=False)
    L = L[L.probe_ok.astype(bool)].copy()
    res = []
    for e, g in L.groupby("ep"):
        if len(g) < 8:
            continue
        t = g.t_to_close.values
        for col in ("rel_u_cm", "rel_v_cm"):
            b = np.polyfit(t, g[col].values, 2)
            g = g.assign(**{col + "_res": g[col].values - np.polyval(b, t)})
        res.append(g)
    R = pd.concat(res)
    R["jitter_cm"] = np.hypot(R.rel_u_cm_res, R.rel_v_cm_res)
    S["wrist_label_jitter_cm"] = dict(n=len(R), median=float(R.jitter_cm.median()), p90=float(R.jitter_cm.quantile(.9)))
    wq = tr[tr.cam == "wrist"][["ep", "frame", "m_w", "o_cube_V", "o_dE", "o_edge_grad_per_dE", "o_lapvar", "arm_speed"]]
    J = R.merge(wq, on=["ep", "frame"])
    S["wrist_jitter_vs_quality"] = {q: tert(J, q, "jitter_cm") for q in ("m_w", "o_cube_V", "o_dE", "o_edge_grad_per_dE", "o_lapvar", "arm_speed")}
    S["shift224_vs_quality"] = {cam: {q: tert(tr[tr.cam == cam], q, "centroid_shift_px640") for q in ("m_w", "o_cube_V", "o_dE")} for cam in ("front", "wrist")}
    # 3 train vs eval
    ev = D[D.src == "eval"]
    cols = ["o_img_V_mean", "o_bg_V", "o_bg_RG", "o_bg_BG", "o_cube_V", "o_cube_S", "o_dE", "o_edge_grad_per_dE", "o_lapvar", "m_w"]
    comp = {}
    for cam in ("front", "wrist"):
        for ph in ("start", "pre3", "pre1"):
            t_ = tr[(tr.cam == cam) & (tr.phase == ph)]
            e_ = ev[(ev.cam == cam) & (ev.phase == ph)]
            comp[f"{cam}|{ph}"] = {c: dict(train_p05=float(t_[c].quantile(.05)), train_med=float(t_[c].median()), train_p95=float(t_[c].quantile(.95)),
                                           eval_vals=[None if pd.isna(v) else round(float(v), 3) for v in e_[c]],
                                           eval_pctile=[None if pd.isna(v) else round(float((t_[c] < v).mean() * 100), 1) for v in e_[c]])
                                   for c in cols}
            comp[f"{cam}|{ph}"]["eval_eps"] = [f"{r[9:15]}e{e}" for r, e in zip(e_.run, e_.ep)]
    S["train_vs_eval"] = comp
    warm = ev[ev.phase.str.startswith("f0")].pivot_table(index=["run", "ep", "cam"], columns="phase", values=["o_bg_BG", "o_bg_RG", "o_img_V_mean"])
    S["eval_first3s"] = {str(k): {f"{a}|{b}": round(float(v), 3) for (a, b), v in row.items()} for k, row in warm.iterrows()}
    json.dump(S, open(OUT / "iq_summary.json", "w"), indent=1, ensure_ascii=False)
    return S


if __name__ == "__main__":
    S = main()
    for k in ("front_px_per_cm_224", "wrist_px_per_cm_224_by_phase", "front_label_err_cm", "front_err_vs_quality", "wrist_label_jitter_cm", "wrist_jitter_vs_quality", "shift224_vs_quality"):
        print(k, json.dumps(S[k], ensure_ascii=False))
