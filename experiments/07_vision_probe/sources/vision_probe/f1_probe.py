"""F1 probe 학습·평가 (CPU 만). f1_extract.py 의 특징(있으면) + CPU 기준선.

데이터: labels_v2 probe_ok 7,810 프레임, folds.json 5-fold (판 분리 + 위치 hold-out + 3 cm 완충, f1_leak_check 통과).
타깃: 영상 좌표 (rel_u_cm, rel_v_cm) · 탁자 좌표 (tan_cm, rad_cm, roll 보정, 큐브 − 집게).
roll 비교 4가지:
  img       특징 → (rel_u, rel_v)
  tab       특징 → (tan, rad) 직접 (roll 정보 없음)
  img→rot   img 예측을 roll 로 회전 (labels_v2 와 같은 식)
  tab+roll  [특징, 특징·sinθ, 특징·cosθ] (PCA 64 위에서) → (tan, rad)
probe:
  ridge   토큰마다 고정 무작위 사영(1152 또는 256 → 16) 후 256 토큰 펼침 (4,096 차원) → ridge, α 는 train 안 판 단위 3-fold
  patch   PCA 64 토큰 → 토큰 공유 선형 회귀로 패치 점유(빨강 마스크 비율) 예측 → 고정 읽기(가중 패치 중심·크기) → rel/tan (작은 선형 보정)
          (처음 설계한 end-to-end softmax 주의 probe 는 합성 자료에서 퇴화해 바꿈 — 실험 기록은 f1_결과.md)
  mean    토큰 평균 → ridge
기준선 (특징 없이, CPU): wrist RGB 32×24 · front RGB 32×24 · wrist 빨강 마스크 64×48 · state 6관절(+roll sin/cos) · 섞은 라벨
지표 (test fold 를 모두 모아): MAE (cm), R², 닫힘까지 시간 구간별 MAE, Known/Random test, 판 단위 bootstrap 95% CI
위치 추종 민감도 g_rep: 편집 프레임(meta src=edit)에서 (예측(+) − 예측(−)) / (가한 이동), 그 판이 test 인 fold 의 모델로
출력: f1_results/<세트>.json, f1_results/summary.csv
사용: nice -n 19 env PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python f1_probe.py --sets baselines           (지금 가능)
      nice -n 19 env PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python f1_probe.py --sets all                 (특징 추출 뒤)
"""
import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HOME = Path.home()
sys.path.insert(0, str(HOME / "so101_runs/main_k8/d2/diag_grasp_bias"))
import common as C  # noqa: E402

OUT = Path(__file__).resolve().parent
RES = OUT / "f1_results"
FEAT = OUT / "f1_features"
TGT_IMG, TGT_TAB = ["rel_u_cm", "rel_v_cm"], ["tan_cm", "rad_cm"]
ALPHAS = [1e-1, 1e0, 1e1, 1e2, 1e3, 1e4, 1e5]
RNG = np.random.default_rng(0)


def theta(roll):
    return np.radians(-5.5 + 0.91 * np.asarray(roll))


def img_to_tab(pu, pv, roll):
    th = theta(roll)
    return -(pu * np.sin(th) - pv * np.cos(th)), -(pu * np.cos(th) + pv * np.sin(th))


# ---------------- ridge ----------------
def ridge_fit(X, Y, alpha):
    mu, sd = X.mean(0), X.std(0) + 1e-6
    Z = (X - mu) / sd
    ym = Y.mean(0)
    n, d = Z.shape
    if d <= n:
        W = np.linalg.solve(Z.T @ Z + alpha * np.eye(d), Z.T @ (Y - ym))
    else:
        W = Z.T @ np.linalg.solve(Z @ Z.T + alpha * np.eye(n), Y - ym)
    return mu, sd, W, ym


def ridge_pred(m, X):
    mu, sd, W, ym = m
    return ((X - mu) / sd) @ W + ym


def ridge_fit_multi(X, Y, alphas):
    """ridge_fit 과 같은 해를 여러 α 에 대해 (Gram 고유분해 한 번)."""
    mu, sd = X.mean(0), X.std(0) + 1e-6
    Z = ((X - mu) / sd).astype(np.float64)
    ym = Y.mean(0)
    Yc = Y - ym
    n, d = Z.shape
    if d <= n:
        ev, V = np.linalg.eigh(Z.T @ Z)
        b = V.T @ (Z.T @ Yc)
        return [(mu, sd, V @ (b / (ev + a)[:, None]), ym) for a in alphas]
    ev, U = np.linalg.eigh(Z @ Z.T)
    c = U.T @ Yc
    return [(mu, sd, Z.T @ (U @ (c / (ev + a)[:, None])), ym) for a in alphas]


def ridge_cv(X, Y, groups):
    """α: train 안 판 단위 3-fold."""
    ug = np.unique(groups)
    RNG.shuffle(ug)
    parts = np.array_split(ug, 3)
    err = np.zeros(len(ALPHAS))
    for p in parts:
        te = np.isin(groups, p)
        for i, m in enumerate(ridge_fit_multi(X[~te], Y[~te], ALPHAS)):
            err[i] += np.abs(ridge_pred(m, X[te]) - Y[te]).sum()
    ba = ALPHAS[int(np.argmin(err))]
    return ridge_fit(X, Y, ba), ba


# ---------------- patch(점유) probe ----------------
# 처음 설계한 end-to-end soft-argmax probe 는 합성 자료에서 큐브 토큰을 피해 가는 퇴화 해로 수렴해서 (합성 MAE ≈ 라벨 SD) 바꿨다.
# 토큰마다 선형 회귀로 '이 패치를 큐브가 덮는 비율'을 예측 (빨강 마스크로 감독) → 고정된 읽기(가중 패치 중심·넓이)로 큐브 중심·크기
# → labels_v2 와 같은 식으로 rel_u/rel_v (cm) → roll 로 tan/rad. 마지막에 train 에서 맞춘 작은 선형 보정 (5개 입력).
GRID_UV = None


def grid_uv():
    """토큰 (16×16, 행 우선) 중심의 640×480 원본 px 좌표."""
    gy, gx = np.meshgrid(np.arange(16), np.arange(16), indexing="ij")
    u = (gx.ravel() * 14 + 7) / 0.35
    v = (gy.ravel() * 14 + 7 - 28) / 0.35
    return u, v


def occ_readout(occ, fit):
    """occ (n,256) 예측 점유 → (u, v, area) 640 px. 음수는 0 으로, 가장 큰 값의 30% 미만은 버림."""
    u, v = grid_uv()
    o = np.clip(occ, 0, None)
    o = np.where(o >= 0.3 * o.max(1, keepdims=True), o, 0)
    s = o.sum(1) + 1e-6
    cu, cv = (o * u).sum(1) / s, (o * v).sum(1) / s
    area = np.clip(s * 40.0 ** 2, 400, None)
    return cu, cv, area


def occ_features(cu, cv, area, roll, fit):
    inv = 1 / np.sqrt(area)
    us, vs = np.polyval(fit["ref_fit_u"], inv), np.polyval(fit["ref_fit_v"], inv)
    pxcm = np.sqrt(area) / 2.5
    ru, rv = (cu - us) / pxcm, (cv - vs) / pxcm
    tn, rd = img_to_tab(ru, rv, roll)
    return ru, rv, tn, rd


def patch_probe(Ttr, Otr, Tte, gtr):
    """Ttr (n,256,d) 토큰, Otr (n,256) 점유 → Tte 의 점유 예측. 토큰 공유 ridge (모든 토큰 같은 w)."""
    Xf = Ttr.reshape(-1, Ttr.shape[-1])
    yf = Otr.reshape(-1, 1)
    sub = np.random.default_rng(0).choice(len(Xf), min(len(Xf), 200000), replace=False)
    groups = np.repeat(gtr, 256)[sub]
    m, a = ridge_cv(Xf[sub], yf[sub], groups)
    return ridge_pred(m, Tte.reshape(-1, Tte.shape[-1])).reshape(len(Tte), 256), a


# ---------------- 특징 만들기 ----------------
def token_project(T, k=16, seed=0):
    rng = np.random.default_rng(seed)
    P = rng.standard_normal((T.shape[-1], k)).astype(np.float32) / math.sqrt(k)
    out = np.empty((T.shape[0], T.shape[1] * k), np.float32)
    for i in range(0, len(T), 512):
        out[i:i + 512] = (np.asarray(T[i:i + 512], np.float32) @ P).reshape(min(512, len(T) - i), -1)
    return out


class LazyRows:
    """T(ii) 를 필요할 때만 읽는 (n,256,d) 행 묶음 (메모리 절약용, pca_tokens 입력)."""
    def __init__(self, T, ii):
        self.T, self.ii = T, np.asarray(ii)
        self.shape = (len(self.ii),) + T(self.ii[:1]).shape[1:]

    def __len__(self):
        return len(self.ii)

    def __getitem__(self, s):
        return self.T(self.ii[s])

    def __iter__(self):
        for i in range(0, len(self.ii), 512):
            yield from self.T(self.ii[i:i + 512])


def pca_tokens(Tr, Te, k=64):
    """train 토큰으로 PCA → (n,256,k)."""
    flat = np.asarray(Tr[:: max(1, len(Tr) // 1500)], np.float32).reshape(-1, Tr.shape[-1])
    mu = flat.mean(0)
    _, _, Vt = np.linalg.svd(flat[np.random.default_rng(0).choice(len(flat), min(60000, len(flat)), replace=False)] - mu, full_matrices=False)
    V = Vt[:k].T
    tr = np.stack([(np.asarray(x, np.float32) - mu) @ V for x in Tr])
    te = np.stack([(np.asarray(x, np.float32) - mu) @ V for x in Te])
    return tr, te


def baseline_features(rows, kind, cache):
    import cv2
    out = []
    for _, r in rows.iterrows():
        cam = "front" if kind == "front_rgb" else "wrist"
        img = C.frames(C.D2 / "dataset", int(r.ep), cam, int(r.frame), int(r.frame), cache)[0]
        if kind in ("wrist_rgb", "front_rgb"):
            out.append(cv2.resize(img, (32, 24), interpolation=cv2.INTER_AREA).astype(np.float32).ravel() / 255)
        elif kind == "wrist_mask":
            out.append(cv2.resize(C.red_mask(img).astype(np.float32), (64, 48), interpolation=cv2.INTER_AREA).ravel() / 255)
    return np.stack(out)


# ---------------- 평가 ----------------
def metrics(Y, P, rows, names):
    r = {}
    for j, n in enumerate(names):
        e = P[:, j] - Y[:, j]
        r[n] = dict(mae=float(np.abs(e).mean()), r2=float(1 - (e ** 2).sum() / ((Y[:, j] - Y[:, j].mean()) ** 2).sum()))
        eps = rows.ep.values
        ue = np.unique(eps)
        bs = []
        for _ in range(500):
            pick = RNG.choice(ue, len(ue))
            idx = np.concatenate([np.where(eps == p)[0] for p in pick])
            bs.append(np.abs(e[idx]).mean())
        r[n]["mae_ci"] = [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
        for lo, hi in ((0, 1), (1, 2), (2, 3)):
            m = (rows.t_to_close.values > lo - 1e-9) & (rows.t_to_close.values <= hi)
            r[n][f"mae_{lo}_{hi}s"] = float(np.abs(e[m]).mean()) if m.any() else None
        for md in ("K", "R"):
            m = rows.group.str.endswith(md).values
            r[n][f"mae_{md}"] = float(np.abs(e[m]).mean()) if m.any() else None
    return r


def run_cv(name, Xfun, rows, folds, probe, O=None, fit=None):
    """Xfun(idx_train, idx_test) → (Xtr, Xte). 4가지 roll 변형을 모두 계산.
    probe = ridge | mean : 특징 → 타깃 ridge.
    probe = patch        : Xfun 이 토큰 (n,256,d) 을 주고 O (n,256) 점유로 감독 → 고정 읽기 → 작은 선형 보정."""
    preds = {k: np.full((len(rows), 2), np.nan) for k in ("img", "tab", "img_rot", "tab_roll")}
    alphas = []
    for fo in folds:
        tr = np.where(rows.ep.isin(fo["train_eps"]).values)[0]
        te = np.where(rows.ep.isin(fo["test_eps"]).values)[0]
        Xtr, Xte = Xfun(tr, te)
        g = rows.ep.values[tr]
        rtr, rte = rows.roll.values[tr], rows.roll.values[te]
        thr, the = theta(rtr)[:, None], theta(rte)[:, None]
        if probe == "patch":
            occ_te, a = patch_probe(Xtr, O[tr], Xte, g)
            occ_tr, _ = patch_probe(Xtr, O[tr], Xtr, g)      # 보정용 (train 안 예측)
            alphas.append(a)
            ftr = np.stack(occ_features(*occ_readout(occ_tr, fit), rtr, fit), 1)
            fte = np.stack(occ_features(*occ_readout(occ_te, fit), rte, fit), 1)
            # img: 읽은 (ru, rv) → 보정. tab(roll 없음): (ru, rv) → tan/rad. img_rot: img 보정값을 roll 로 회전. tab_roll: roll 항 포함
            m, _ = ridge_cv(ftr[:, :2], rows[TGT_IMG].values[tr], g)
            preds["img"][te] = ridge_pred(m, fte[:, :2])
            m, _ = ridge_cv(ftr[:, :2], rows[TGT_TAB].values[tr], g)
            preds["tab"][te] = ridge_pred(m, fte[:, :2])
            pu, pv = preds["img"][te, 0], preds["img"][te, 1]
            preds["img_rot"][te] = np.stack(img_to_tab(pu, pv, rte), 1)
            Atr = np.hstack([ftr, ftr[:, :2] * np.sin(thr), ftr[:, :2] * np.cos(thr), np.sin(thr), np.cos(thr)])
            Ate = np.hstack([fte, fte[:, :2] * np.sin(the), fte[:, :2] * np.cos(the), np.sin(the), np.cos(the)])
            m, _ = ridge_cv(Atr, rows[TGT_TAB].values[tr], g)
            preds["tab_roll"][te] = ridge_pred(m, Ate)
            continue
        for key, tg in (("img", TGT_IMG), ("tab", TGT_TAB)):
            m, a = ridge_cv(Xtr, rows[tg].values[tr], g)
            alphas.append(a)
            preds[key][te] = ridge_pred(m, Xte)
        pu, pv = preds["img"][te, 0], preds["img"][te, 1]
        preds["img_rot"][te] = np.stack(img_to_tab(pu, pv, rte), 1)
        # tab+roll: PCA 64 위에서 [z, z sinθ, z cosθ]
        mu = Xtr.mean(0)
        _, _, Vt = np.linalg.svd(Xtr - mu, full_matrices=False)
        V = Vt[:64].T
        ztr, zte = (Xtr - mu) @ V, (Xte - mu) @ V
        Atr = np.hstack([ztr, ztr * np.sin(thr), ztr * np.cos(thr), np.sin(thr), np.cos(thr)])
        Ate = np.hstack([zte, zte * np.sin(the), zte * np.cos(the), np.sin(the), np.cos(the)])
        m, _ = ridge_cv(Atr, rows[TGT_TAB].values[tr], g)
        preds["tab_roll"][te] = ridge_pred(m, Ate)
    tested = ~np.isnan(preds["img"][:, 0])
    R = rows[tested].reset_index(drop=True)
    out = {"name": name, "probe": probe, "n_test_frames": int(tested.sum()), "alphas": [float(a) for a in alphas]}
    out["img"] = metrics(R[TGT_IMG].values, preds["img"][tested], R, TGT_IMG)
    for k in ("tab", "img_rot", "tab_roll"):
        out[k] = metrics(R[TGT_TAB].values, preds[k][tested], R, TGT_TAB)
    return out, preds


def occupancy_grids(rows, cam, cache):
    """프레임마다 224 입력 기준 16×16 패치의 빨강 점유 비율 (π0.5 와 같은 resize_with_pad 로 줄인 영상의 마스크)."""
    import torch
    from lerobot.policies.common.vla_utils import resize_with_pad_torch
    out = np.zeros((len(rows), 256), np.float32)
    for i, (_, r) in enumerate(rows.iterrows()):
        img = C.frames(C.D2 / "dataset", int(r.ep), cam, int(r.frame), int(r.frame), cache)[0]
        t = resize_with_pad_torch(torch.from_numpy(img).float().div(255)[None], 224, 224)[0].numpy()
        m = C.red_mask((t * 255).round().astype(np.uint8)).astype(np.float32) / 255
        out[i] = m.reshape(16, 14, 16, 14).mean((1, 3)).ravel()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sets", default="baselines")
    ap.add_argument("--keys", default=None, help="features 세트 중 일부만 (쉼표 구분, 예: kv_w:5:1,sig_w13)")
    ap.add_argument("--tag", default=None, help="summary_<tag>.csv (병렬 실행 시 파일 충돌 방지)")
    args = ap.parse_args()
    RES.mkdir(exist_ok=True)
    L = pd.read_csv(OUT / "labels_v2.csv", low_memory=False)
    rows = L[L.probe_ok.astype(bool)].reset_index(drop=True)
    folds = json.load(open(OUT / "folds.json"))["folds"]
    summary = []

    def save(res):
        json.dump(res, open(RES / f"{res['name']}_{res['probe']}.json", "w"), indent=1)
        for k in ("img", "tab", "img_rot", "tab_roll"):
            tg = TGT_IMG if k == "img" else TGT_TAB
            summary.append(dict(name=res["name"], probe=res["probe"], variant=k, **{f"{t}_mae": res[k][t]["mae"] for t in tg},
                                **{f"{t}_r2": res[k][t]["r2"] for t in tg}))
        pd.DataFrame(summary).to_csv(RES / f"summary_{args.tag or args.sets}.csv", index=False)
        print(res["name"], res["probe"], {k: {t: (round(res[k][t]["mae"], 3), round(res[k][t]["r2"], 2)) for t in res[k]}
                                          for k in ("img", "tab", "img_rot", "tab_roll")}, flush=True)

    t0 = time.time()
    if args.sets in ("baselines", "all"):
        cache = {}
        bdir = OUT / "f1_baselines"
        bdir.mkdir(exist_ok=True)
        for kind in ("wrist_rgb", "wrist_mask", "front_rgb"):
            p = bdir / f"{kind}.npy"
            if not p.exists():
                np.save(p, baseline_features(rows, kind, cache))
            X = np.load(p)
            res, _ = run_cv(kind, lambda tr, te, X=X: (X[tr], X[te]), rows, folds, "ridge")
            save(res)
        fit = json.load(open(OUT / "folds.json"))
        for cam in ("wrist", "front"):
            p = bdir / f"occ_{cam}.npy"
            if not p.exists():
                np.save(p, occupancy_grids(rows, cam, cache))
        occ_w = np.load(bdir / "occ_wrist.npy")
        # 상한 대조: '토큰 특징' 자리에 실제 점유 자체(1차원)를 넣은 patch probe → 읽기 방식의 한계
        res, _ = run_cv("oracle_occupancy_wrist", lambda tr, te: (occ_w[tr][..., None], occ_w[te][..., None]), rows, folds, "patch", O=occ_w, fit=fit)
        save(res)
        S = rows[[f"s_{j}" for j in C.JOINTS]].values.astype(np.float32)
        th = theta(rows.roll.values)
        S = np.hstack([S, np.sin(th)[:, None], np.cos(th)[:, None]])
        res, _ = run_cv("state", lambda tr, te: (S[tr], S[te]), rows, folds, "ridge")
        save(res)
        # 섞은 라벨: 판 단위로 라벨 묶음을 섞음 (wrist_mask 특징)
        sh = rows.copy()
        ue = sh.ep.unique()
        perm = dict(zip(ue, RNG.permutation(ue)))
        for t in TGT_IMG + TGT_TAB:
            mean_by_ep = sh.groupby("ep")[t].transform("mean")
            sh[t] = sh.ep.map(perm).map(sh.groupby("ep")[t].mean()).values + (sh[t] - mean_by_ep).sample(frac=1, random_state=0).values
        X = np.load(bdir / "wrist_mask.npy")
        res, _ = run_cv("shuffled_labels_wrist_mask", lambda tr, te: (X[tr], X[te]), sh, folds, "ridge")
        save(res)
    if args.sets in ("features", "all"):
        M = pd.read_csv(FEAT / "meta.csv")
        tr_rows = M[(M.src == "train") & M.valid].reset_index(drop=True)
        assert len(tr_rows) == len(rows) and (tr_rows.ep.values == rows.ep.values).all() and (tr_rows.frame.values == rows.frame.values).all()
        idx = tr_rows.row.values
        fit = json.load(open(OUT / "folds.json"))
        occ_w, occ_f = [np.load(OUT / "f1_baselines" / f"occ_{c}.npy") for c in ("wrist", "front")]
        sets = [("sig_w26", "wrist SigLIP last"), ("sig_w13", "wrist SigLIP L13"), ("sig_f26", "front SigLIP last")]
        sets += [(f"kv_w:{li}:{kv}", f"wrist Gemma L{l} {'K' if kv == 0 else 'V'}") for li, l in enumerate([0, 3, 7, 11, 14, 17]) for kv in (0, 1)]
        sets += [(f"kv_f:{li}:1", f"front Gemma L{l} V") for li, l in enumerate([0, 3, 7, 11, 14, 17]) if l in (0, 11, 17)]
        if args.keys:
            sets = [s for s in sets if s[0] in args.keys.split(",")]
        for key, label in sets:
            if ":" in key:
                arr, li, kv = key.split(":")
                A = np.load(FEAT / f"{arr}.npy", mmap_mode="r")
                T = lambda ii, A=A, li=int(li), kv=int(kv): np.asarray(A[idx[ii], li, kv], np.float32)  # noqa: E731
            else:
                A = np.load(FEAT / f"{key}.npy", mmap_mode="r")
                T = lambda ii, A=A: np.asarray(A[idx[ii]], np.float32)  # noqa: E731
            flat = None
            for probe in ("ridge", "mean", "patch"):
                if probe == "ridge":
                    if flat is None:
                        flat = np.concatenate([token_project(T(np.arange(i, min(len(rows), i + 512)))) for i in range(0, len(rows), 512)])
                    res, _ = run_cv(key.replace(":", "_"), lambda tr, te: (flat[tr], flat[te]), rows, folds, "ridge")
                elif probe == "mean":
                    mp = np.stack([T(np.arange(i, min(len(rows), i + 512))).mean(1) for i in range(0, len(rows), 512)]).reshape(len(rows), -1) \
                        if False else np.concatenate([T(np.arange(i, min(len(rows), i + 512))).mean(1) for i in range(0, len(rows), 512)])
                    res, _ = run_cv(key.replace(":", "_"), lambda tr, te: (mp[tr], mp[te]), rows, folds, "mean")
                else:
                    O = occ_w if ("_w" in key or key.startswith("kv_w")) else occ_f
                    res, _ = run_cv(key.replace(":", "_"), lambda tr, te: pca_tokens(LazyRows(T, tr), LazyRows(T, te)), rows, folds, "patch", O=O, fit=fit)
                res["label"] = label
                save(res)
        # 편집 세트 g_rep 과 평가 롤아웃은 f1_sensitivity.py (특징 추출 뒤)
    print(f"done {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
