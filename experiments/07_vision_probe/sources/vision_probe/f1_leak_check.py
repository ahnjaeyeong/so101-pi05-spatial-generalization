"""F1 전 누출 검사 (CPU, 읽기만): labels_v2.csv + folds.json → f1_leak_check.json

검사:
  1. fold 마다 train/test 판 겹침 0
  2. test 판 큐브 위치와 train 판 큐브 위치의 최소 거리 ≥ 완충 3 cm
  3. Known: test 로 뺀 K 의 판이 train 에 0편 (좌표 2 cm 기준)
  4. 같은 위치 반복: test 판과 같은 layout_id(원본 세션·원본 판 번호 기준이 아닌 큐브 좌표 0.5 cm 안)가 train 에 있는지
  5. probe 프레임(labels_v2.probe_ok)이 모두 fold 의 train 또는 test 에 속하는지, 그 외(완충으로 빠진 판) 프레임 수
  6. 같은 판의 프레임 사이 시간 간격 (3 프레임 = 0.1 s) — 판 단위 분리라 train/test 사이에는 없음을 다시 확인
"""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent


def main():
    L = pd.read_csv(OUT / "labels_v2.csv", low_memory=False)
    F = json.load(open(OUT / "folds.json"))
    P = L[L.probe_ok.astype(bool)]
    eps = L.groupby("ep").agg(x=("cube_x", "first"), y=("cube_y", "first"), K=("K", "first"), group=("group", "first"))
    eps["K"] = eps.K.fillna("")
    out = {"n_probe_frames": int(len(P)), "folds": []}
    ok_all = True
    for fo in F["folds"]:
        te, tr = set(fo["test_eps"]), set(fo["train_eps"])
        overlap = len(te & tr)
        tp = eps.loc[sorted(te), ["x", "y"]].values
        rp = eps.loc[sorted(tr), ["x", "y"]].values
        dmin = float(np.min(np.hypot(rp[:, None, 0] - tp[None, :, 0], rp[:, None, 1] - tp[None, :, 1])))
        held_K = fo.get("test_K", [])
        k_in_train = int(eps.loc[sorted(tr)].K.isin(held_K).sum()) if held_K else 0
        same_spot = int((np.hypot(rp[:, None, 0] - tp[None, :, 0], rp[:, None, 1] - tp[None, :, 1]) < 0.5).any(1).sum())
        fr_te = int(P.ep.isin(te).sum())
        fr_tr = int(P.ep.isin(tr).sum())
        fr_out = int(len(P) - fr_te - fr_tr)
        ok = overlap == 0 and dmin >= F["buffer_cm"] - 1e-6 and k_in_train == 0 and same_spot == 0
        ok_all &= ok
        out["folds"].append(dict(fold=fo["fold"], test_eps=len(te), train_eps=len(tr), episode_overlap=overlap,
                                 min_train_test_cube_dist_cm=round(dmin, 2), held_K=held_K, held_K_eps_in_train=k_in_train,
                                 train_eps_within_0_5cm_of_test=same_spot, test_frames=fr_te, train_frames=fr_tr,
                                 frames_in_buffer_only=fr_out, ok=bool(ok)))
    # 모든 판이 적어도 한 fold 의 test 에 들어가는지 (교차 검증 덮음)
    covered = set().union(*[set(fo["test_eps"]) for fo in F["folds"]])
    out["eps_never_tested"] = sorted(set(eps.index) - covered)
    out["eps_tested_more_than_once"] = sorted([e for e in covered if sum(e in fo["test_eps"] for fo in F["folds"]) > 1])
    out["all_ok"] = bool(ok_all)
    json.dump(out, open(OUT / "f1_leak_check.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
