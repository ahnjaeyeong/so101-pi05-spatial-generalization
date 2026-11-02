"""p03 기존 5판의 merge 마다 오프라인 재계획 (GPU, 로봇·카메라 연결 없음, 체크포인트 읽기만).

**재구성 값이다 — 실물에서 기록된 chunk 가 아니다.**
- 관측: dataset 의 AV1 디코드 영상 + observation.state, 프레임 = p01 의 obs_frame (merge 프레임 − 적용 delay, ±1 틱 근사).
  chunk 0 은 frame 0 (실제 관측은 그 직전 정지 상태, dataset 에 없음).
- RTC 안내 없음 (prev_chunk_left_over 없이) — 실물에서는 앞 chunk 남은 부분으로 안내했다. 실물 noise 는 기록되지 않아 고정 noise 8개 (seed 1234, diag_grasp_bias 와 같은 은행).
- num_inference_steps 5 (실물과 같음). d2 020000.
비교 대상: 같은 chunk 의 실제 실행 구간 raw (p01_ticks, queue 출력).
출력: tables/p03_replan_<run>_ep<e>.npz (chunks (8, n_chunk, 50, 6) °, obs_frame, merge_frame, delay), p03_run.log
사용: nice -n 19 env PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python p03_offline_replan.py
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

D2 = Path.home() / "so101_runs/main_k8/d2"
sys.path.insert(0, str(D2 / "diag_grasp_bias"))
import common as C  # noqa: E402
import probe_core as PC  # noqa: E402
from policy_probe import load_obs  # noqa: E402

TAB = D2 / "pan_inference_diagnostic/tables"


def main():
    T = pd.read_parquet(TAB / "p01_ticks.parquet")
    M = pd.read_csv(TAB / "p01_merges.csv")
    E = PC.Engine("020000", n_noise=8)
    t_all = time.time()
    for (run, e), g in T.groupby(["run", "ep"]):
        out = TAB / f"p03_replan_{run}_ep{e}.npz"
        if out.exists():
            print("skip (있음)", out.name, flush=True)
            continue
        n = len(g)
        mm = M[(M.run == run) & (M.ep == e)].sort_values("chunk_id")
        mm = mm[mm.merge_frame < n]
        d = mm.applied_delay.fillna(0).astype(int).values
        mf = mm.merge_frame.astype(int).values
        fo = np.where(mm.chunk_id.values == 0, 0, np.clip(mf - d, 0, n - 1))
        cache = {}
        ds = D2 / "eval/rollouts" / run / "dataset"
        F, W = load_obs(ds, [(int(e), int(f)) for f in fo], cache)
        S = g[[f"state_{j}" for j in C.JOINTS]].values[fo].astype(np.float32)
        ch = E.chunks(F, W, S, steps=(5,))[5]
        np.savez_compressed(out, chunks=ch, obs_frame=fo, merge_frame=mf, delay=d, chunk_id=mm.chunk_id.values)
        print(f"{run} ep{e}: {len(fo)} chunks, gpu_busy_s {E.gpu_busy_s:.0f}", flush=True)
    print(f"done wall {time.time() - t_all:.0f}s gpu_busy_s {E.gpu_busy_s:.0f}", flush=True)


if __name__ == "__main__":
    main()
