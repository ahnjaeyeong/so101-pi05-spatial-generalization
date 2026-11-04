"""r04 프레임 가중 (CPU). 로봇 연결 없음.

목표: 교정 (R1+R2 승인 16 편) 표본 비중 ≈ 20 %, d2 ≈ 80 % (작업 지시 4 절 제안). 시간 구간 가중 · loss 가중 없음.
방식: train_weighted.py 와 같은 정수 프레임 가중 (프레임을 w 번 반복한 목록을 epoch 마다 randperm).
  d2 프레임 w = 1, 승인 교정 프레임 w = W (편 · 유형 구분 없이 같은 값 → 교정 안의 R1 : R2 비는 승인 프레임 수 비 그대로).
  W = round(0.25 · N_d2 / N_corr) — 기대 비중 W·N_corr / (N_d2 + W·N_corr).
  제외 편 (병합 256–259, 275) 프레임은 w = 1 로 두지만 `--dataset.episodes` 목록에 없으므로 sampler 가 아예 쓰지 않는다 (r05 에서 확인).
출력: weights/weights_rc16_W{W}.npy (병합 전역 index 순서, int64), tables/r04_weights_summary.json
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

RF = Path.home() / "so101_runs/main_k8/d2/recovery_ft"


def main():
    M = pd.read_csv(RF / "manifest/training_manifest.csv")
    E = pd.read_parquet(RF / "dataset/meta/episodes/chunk-000/file-000.parquet").set_index("episode_index")
    total = int(json.load(open(RF / "dataset/meta/info.json"))["total_frames"])
    use = M[M.approved]
    n_d2 = int(use[use.group == "d2"].length.sum())
    n_corr = int(use[use.group != "d2"].length.sum())
    W = int(round(0.25 * n_d2 / n_corr))
    w = np.ones(total, dtype=np.int64)
    for r in use[use.group != "d2"].itertuples():
        a, b = int(E.loc[r.merged_episode, "dataset_from_index"]), int(E.loc[r.merged_episode, "dataset_to_index"])
        assert b - a == r.length
        w[a:b] = W
    (RF / "weights").mkdir(exist_ok=True)
    p = RF / f"weights/weights_rc16_W{W}.npy"
    np.save(p, w)
    tot = n_d2 + W * n_corr
    per = {g: int(use[use.group == g].length.sum()) for g in ("d2", "R1", "R2")}
    summ = dict(W=W, weights_file=str(p), weights_sha256=hashlib.sha256(p.read_bytes()).hexdigest(), frames=per, weighted_list_len=tot,
                expected_share={g: (per[g] * (1 if g == "d2" else W)) / tot for g in per},
                expected_samples_1000x32={g: 32000 * (per[g] * (1 if g == "d2" else W)) / tot for g in per},
                expected_exposure_per_frame_1000x32={g: 32000 * (1 if g == "d2" else W) / tot for g in per},
                natural_share_without_weight={g: per[g] / (n_d2 + n_corr) for g in per})
    (RF / "tables/r04_weights_summary.json").write_text(json.dumps(summ, indent=1))
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
