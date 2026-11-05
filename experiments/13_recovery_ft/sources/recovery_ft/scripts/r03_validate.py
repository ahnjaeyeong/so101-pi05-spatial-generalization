"""r03 학습 전 데이터 검증 (CPU). 로봇 연결 없음. 사본 · 원본 모두 읽기만.

작업 지시 3 절 1–10 + 정규화 범위. 하나라도 FAIL 이면 종료 코드 1 (학습 시작 안 함). WARN 은 기록만.
  V1  LeRobot v3.0: 사본을 LeRobotDataset(episodes=manifest 272) 로 열기, 편 수 · 프레임 수
  V2  FPS 30 (info · 영상 meta)
  V3  front/wrist 영상 feature 동일 (사본 = d2 = R1 = R2), 영상 파일 sha256 = 원본 (merge_map)
  V4  state/action 이름 순서 · 단위 (feature names 동일, 값 범위 d2 와 비교)
  V5  그리퍼: state ↔ action 의미 (닫힘 · 열림 값 범위, action→state 지연 상관) d2 와 비교
  V6  task 문장 · task_index 동일
  V7  편 경계 · action chunk 경계: frame_index 0..L−1, index 연속, from/to index, 끝 근처 action_is_pad,
      사본 프레임 값 = 원본 값 (모든 프레임 action · state · timestamp), 영상 표본 프레임 사본 = 원본 (같은 디코더)
  V8  timestamp = frame_index/30, 영상 구간 길이 = 편 길이/30
  V9  제외 편이 학습 목록 · sampler 에 없음
  V10 시작 action ↔ state 물리 일관성: 편 첫 프레임 |action − state| (관절별) 를 d2 256 편 분포와 비교
  N   정규화: 사본 stats.json = d2 stats.json = d2 020000 normalizer; R1/R2 값이 d2 q01–q99 밖인 비율
출력: tables/r03_*.csv, logs/r03_validate.log (stdout)
사용: CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 nice -n 10 ~/so101-env/bin/python scripts/r03_validate.py
"""
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

os.environ.setdefault("HF_HUB_OFFLINE", "1")
HOME = Path.home()
RF = HOME / "so101_runs/main_k8/d2/recovery_ft"
DS = RF / "dataset"
CK = HOME / "so101_runs/main_k8/d2/train/32_20000/pi05_expert_bs32_20k/checkpoints/020000/pretrained_model"
J = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
RES = []


def rec(code, status, detail):
    RES.append(dict(check=code, status=status, detail=detail))
    print(f"[{status}] {code}: {detail}", flush=True)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_data(root):
    return pd.concat([pd.read_parquet(p) for p in sorted((Path(root) / "data").rglob("*.parquet"))], ignore_index=True).sort_values("index").reset_index(drop=True)


def load_eps(root):
    return pd.concat([pd.read_parquet(p) for p in sorted((Path(root) / "meta/episodes").rglob("*.parquet"))], ignore_index=True).sort_values("episode_index").reset_index(drop=True)


def main():
    import torch
    from lerobot.datasets.lerobot_dataset import LeRobotDataset
    man = json.loads((RF / "manifest/training_manifest.json").read_text())
    M = pd.read_csv(RF / "manifest/training_manifest.csv")
    train_eps = man["train_episodes_merged"]
    excl = man["excluded_merged"]
    info = json.load(open(DS / "meta/info.json"))
    roots = {g: Path(man["sources"][g]["root"]) for g in man["merge_order"]}
    sinfo = {g: json.load(open(roots[g] / "meta/info.json")) for g in roots}

    # V1
    ds = LeRobotDataset("oxr/so101_k8_d2_rc16", root=DS, episodes=train_eps)
    exp_frames = int(M[M.approved].length.sum())
    ok = ds.num_episodes == 272 and ds.num_frames == exp_frames and info["codebase_version"] == "v3.0"
    rec("V1", "PASS" if ok else "FAIL", f"v{info['codebase_version']} LeRobotDataset 열림, 학습 편 {ds.num_episodes} (기대 272), 프레임 {ds.num_frames} (기대 {exp_frames}); 사본 전체 {info['total_episodes']} 편 {info['total_frames']} 프레임")
    # V2
    fps_ok = info["fps"] == 30 and all(s["fps"] == 30 for s in sinfo.values()) and all(
        info["features"][c]["info"]["video.fps"] == 30 for c in ("observation.images.front", "observation.images.wrist"))
    rec("V2", "PASS" if fps_ok else "FAIL", f"fps 사본 {info['fps']}, 원본 {[s['fps'] for s in sinfo.values()]}, 영상 30")
    # V3
    feq = all(s["features"] == info["features"] for s in sinfo.values())
    mm = json.loads((RF / "manifest/merge_map.json").read_text())["files"]
    vbad = [k for k, v in mm.items() if k.startswith("videos/") and sha(DS / k) != sha(v)]
    rec("V3", "PASS" if feq and not vbad else "FAIL", f"features (영상 포함) 사본=d2=R1=R2: {feq}; 영상 파일 {sum(k.startswith('videos/') for k in mm)} 개 sha256 = 원본 (불일치 {len(vbad)})")
    # V4/V6
    names_ok = all(info["features"][k]["names"] == [f"{j}.pos" for j in J] for k in ("action", "observation.state"))
    tasks_ok = list(pd.read_parquet(DS / "meta/tasks.parquet").index) == [man["task"]]
    rec("V6", "PASS" if tasks_ok else "FAIL", f"tasks.parquet = ['{man['task']}']")

    D = load_data(DS)
    E = load_eps(DS)
    D["group"] = M.set_index("merged_episode").group.reindex(D.episode_index).values
    # V7 경계 + 값 일치
    bad = []
    for _, e in E.iterrows():
        sl = D.iloc[int(e.dataset_from_index):int(e.dataset_to_index)]
        if not ((sl.episode_index == e.episode_index).all() and (sl.frame_index.values == np.arange(e.length)).all() and len(sl) == e.length):
            bad.append(int(e.episode_index))
    idx_ok = (D["index"].values == np.arange(len(D))).all() and (D.task_index == 0).all()
    val_bad = []
    off = 0
    for g in man["merge_order"]:
        S = load_data(roots[g])
        T = D.iloc[off:off + len(S)]
        for col in ("action", "observation.state"):
            if not np.array_equal(np.stack(S[col].values), np.stack(T[col].values)):
                val_bad.append(f"{g}:{col}")
        for col in ("timestamp", "frame_index"):
            if not np.array_equal(S[col].values, T[col].values):
                val_bad.append(f"{g}:{col}")
        if not (np.array_equal(S.episode_index.values + int(M[M.group == g].merged_episode.min()), T.episode_index.values)):
            val_bad.append(f"{g}:episode_index")
        off += len(S)
    rec("V7a", "PASS" if not bad and idx_ok and not val_bad else "FAIL",
        f"편 경계 이상 {bad}; index 0..{len(D) - 1} 연속 · task_index 0: {idx_ok}; 원본과 값 다른 열 {val_bad} (모든 프레임 action · state · timestamp · frame_index 비교)")
    # V8
    ts_err = float(np.abs(D.timestamp.values - D.frame_index.values / 30.0).max())
    vd = max(float(np.abs((E[f"videos/{c}/to_timestamp"] - E[f"videos/{c}/from_timestamp"]) - E.length / 30.0).max()) for c in ("observation.images.front", "observation.images.wrist"))
    rec("V8", "PASS" if ts_err < 1e-3 and vd < 1.5 / 30 else "FAIL", f"max |timestamp − frame_index/30| {ts_err:.2e} s; max |영상 구간 − 길이/30| {vd:.4f} s (원본 QA: 녹화 중 센 프레임 = 저장 줄 수)")
    # V9
    inter = set(train_eps) & set(excl)
    in_ds = set(int(x) for x in np.unique(ds.hf_dataset["episode_index"]))
    rec("V9", "PASS" if not inter and not (in_ds & set(excl)) and len(train_eps) == 272 else "FAIL",
        f"학습 목록 ∩ 제외 = {sorted(inter)}; 열린 dataset 안 episode_index 에 제외 편 {sorted(in_ds & set(excl))} (sampler 는 r05 에서 다시 확인)")

    # V7b 영상 · chunk 경계 (같은 디코더로 사본 vs 원본)
    dts = {"action": [i / 30 for i in range(50)]}
    dsd = LeRobotDataset("oxr/so101_k8_d2_rc16", root=DS, episodes=train_eps, delta_timestamps=dts)
    srcds = {g: LeRobotDataset(man["sources"][g]["repo_id"], root=roots[g], delta_timestamps=dts) for g in roots}
    rng = np.random.default_rng(0)
    pick = list(M[(M.group != "d2") & M.approved].itertuples()) + list(M[(M.group == "d2")].iloc[rng.choice(256, 12, replace=False)].itertuples())
    vbad, pad_bad, n_cmp = [], [], 0
    for r in pick:
        fi = int(E.loc[r.merged_episode, "dataset_from_index"])
        L = int(r.length)
        for t in (0, L // 2, L - 1, L - 10):
            a = dsd[dsd.absolute_to_relative_idx[fi + t] if dsd.absolute_to_relative_idx is not None else fi + t]
            sfi = int(load_eps(roots[r.group]).loc[r.source_episode, "dataset_from_index"])
            b = srcds[r.group][sfi + t]
            for k in ("observation.images.front", "observation.images.wrist", "action", "observation.state", "action_is_pad"):
                if not torch.equal(a[k], b[k]):
                    vbad.append(f"{r.group}{r.source_episode}@{t}:{k}")
            n_cmp += 1
            npad = int(a["action_is_pad"].sum())
            if npad != max(0, 50 - (L - t)):
                pad_bad.append(f"{r.group}{r.source_episode}@{t}: pad {npad}")
    rec("V7b", "PASS" if not vbad and not pad_bad else "FAIL",
        f"{n_cmp} 표본 프레임 (R1/R2 승인 16 편 전부 + d2 12 편 × 처음 · 가운데 · 끝 · 끝−10): 영상 · action chunk · state 사본 = 원본, 불일치 {vbad[:5]}; action_is_pad = 편 끝 넘는 칸 수 (이상 {pad_bad[:5]})")

    # V4 값 범위 · V5 그리퍼 · V10 시작 일관성
    st = json.load(open(DS / "meta/stats.json"))
    q01s, q99s = np.array(st["observation.state"]["q01"]), np.array(st["observation.state"]["q99"])
    q01a, q99a = np.array(st["action"]["q01"]), np.array(st["action"]["q99"])
    rows = []
    U = D[D.episode_index.isin(train_eps)]
    for g, G in U.groupby("group"):
        S = np.stack(G["observation.state"].values)
        A = np.stack(G["action"].values)
        r = dict(group=g, frames=len(G))
        for i, j in enumerate(J):
            r[f"{j}_state_min"], r[f"{j}_state_max"] = float(S[:, i].min()), float(S[:, i].max())
            r[f"{j}_out_q_state"] = float(((S[:, i] < q01s[i]) | (S[:, i] > q99s[i])).mean())
            r[f"{j}_out_q_action"] = float(((A[:, i] < q01a[i]) | (A[:, i] > q99a[i])).mean())
        rows.append(r)
    R = pd.DataFrame(rows)
    R.to_csv(RF / "tables/r03_ranges.csv", index=False)
    out_max = R[[c for c in R.columns if c.startswith(tuple(J)) and "out_q" in c]].max(axis=1)
    rec("V4", "PASS" if names_ok else "FAIL", f"state/action 이름 순서 {J} (단위 = lerobot so_follower 관절 °, 그리퍼 0–100, 세 dataset 같은 calibration id my_arm/my_leader 녹화 명령); "
        + "; ".join(f"{r.group} d2 q01–q99 밖 최대 비율 {o:.4f}" for r, o in zip(R.itertuples(), out_max)))
    # 그리퍼
    grows = []
    for ep, G in U.groupby("episode_index"):
        s = np.stack(G["observation.state"].values)[:, 5]
        a = np.stack(G["action"].values)[:, 5]
        lagc = [np.corrcoef(a[:len(a) - k], s[k:])[0, 1] if np.std(a) > 1 and np.std(s) > 1 else np.nan for k in range(0, 16)]
        grows.append(dict(episode=ep, group=G.group.iloc[0], s_min=s.min(), s_max=s.max(), a_min=a.min(), a_max=a.max(),
                          best_lag=int(np.nanargmax(lagc)) if np.isfinite(lagc).any() else -1, corr_best=np.nanmax(lagc) if np.isfinite(lagc).any() else np.nan,
                          start_s=s[0], start_a=a[0]))
    Gr = pd.DataFrame(grows)
    Gr.to_csv(RF / "tables/r03_gripper.csv", index=False)
    gs = Gr.groupby("group").agg(s_min_med=("s_min", "median"), a_min_med=("a_min", "median"), s_max_med=("s_max", "median"), a_max_med=("a_max", "median"),
                                 lag_med=("best_lag", "median"), corr_med=("corr_best", "median"))
    d2lag = Gr[Gr.group == "d2"].best_lag
    new = Gr[Gr.group != "d2"]
    g_ok = new.best_lag.between(d2lag.quantile(0.01), d2lag.quantile(0.99)).all() and (new.corr_best > 0.9).all()
    rec("V5", "PASS" if g_ok else "WARN", "그리퍼 (state · action 같은 0–100 눈금, 큰 값 = 열림): " + gs.round(2).to_string().replace("\n", " | ")
        + f"; R1/R2 action→state 최적 지연이 d2 1–99% 안 · 상관 > 0.9: {g_ok}")
    # V10 시작
    srows = []
    for ep, G in U.groupby("episode_index"):
        s0 = np.asarray(G["observation.state"].iloc[0])
        a0 = np.asarray(G["action"].iloc[0])
        srows.append(dict(episode=ep, group=G.group.iloc[0], **{f"d_{j}": float(a0[i] - s0[i]) for i, j in enumerate(J)}))
    Sd = pd.DataFrame(srows)
    Sd.to_csv(RF / "tables/r03_start_action_minus_state.csv", index=False)
    d2s = Sd[Sd.group == "d2"]
    lim = {j: float(np.percentile(np.abs(d2s[f"d_{j}"]), 99)) for j in J}
    flag = []
    for r in Sd[Sd.group != "d2"].itertuples():
        for j in J:
            v = getattr(r, f"d_{j}")
            if abs(v) > max(lim[j], 5.0):
                flag.append(f"ep{r.episode}:{j} {v:+.1f}")
    rec("V10", "PASS" if not flag else "WARN", "첫 프레임 |action − state| d2 p99 (°): " + ", ".join(f"{j} {lim[j]:.1f}" for j in J)
        + f"; R1/R2 에서 max(d2 p99, 5°) 넘는 것: {flag if flag else '없음'}; R1/R2 최대 " + ", ".join(f"{j} {np.abs(Sd[Sd.group != 'd2'][f'd_{j}']).max():.1f}" for j in J))
    # N 정규화
    from safetensors.numpy import load_file
    n = load_file(str(CK / "policy_preprocessor_step_3_normalizer_processor.safetensors"))
    nd = max(float(np.abs(np.asarray(st[f][s], dtype=np.float32) - n[f"{f}.{s}"]).max()) for f in ("observation.state", "action") for s in ("q01", "q99", "mean", "std", "min", "max"))
    same = sha(DS / "meta/stats.json") == sha(roots["d2"] / "meta/stats.json")
    rec("N", "PASS" if same and nd == 0 else "FAIL", f"사본 stats.json = d2 stats.json (sha256): {same}; d2 020000 normalizer 와 state/action 통계 최대 차 {nd} (QUANTILES q01/q99 사용); 영상 VISUAL=IDENTITY")
    pd.DataFrame(RES).to_csv(RF / "tables/r03_checks.csv", index=False)
    fails = [r for r in RES if r["status"] == "FAIL"]
    print("VALIDATE_FAIL" if fails else "VALIDATE_OK", f"(FAIL {len(fails)}, WARN {sum(r['status'] == 'WARN' for r in RES)})")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
