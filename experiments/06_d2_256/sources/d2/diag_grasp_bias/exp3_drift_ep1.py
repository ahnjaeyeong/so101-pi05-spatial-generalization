"""실험 3: try3_filt ep1 (dataset ep1 = filter_log episode 2) 의 pan 흐름(시작 예측 19.7° → 첫 닫힘 28.7°)을 단계별로 나눈다.

단계 (틱마다):
  model   : 오프라인 재계획. RTC merge 마다 그 추론이 본 관측(= merge 틱 − real_delay) 으로 chunk 를 다시 계산
            (RTC 안내 없음, 고정 noise 8개, step 5). index real_delay … real_delay+19 가 그 merge 뒤 실제로 나간 구간에 해당.
  raw     : 실제 action queue 에서 나온 값 (filter_log raw_*, RTC 이어붙이기 결과)
  out     : arm_filter 뒤 값 (= dataset action)
  sent    : out 을 현재 state ±8° 로 자른 값 (max_relative_target, robots/utils.py:93-116 과 같은 식, 기록 state 로 재계산)
  state   : 팔로워 실제 위치
대응: dataset frame j = filter_log cmd 행 j = tick j+10 (앞 10틱 starved). merge 틱 k 의 관측 = frame k − real_delay − 10.
출력: exp3/ticks.csv, exp3/replans.npz, exp3/merges.csv
사용: nice -n 19 env PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python exp3_drift_ep1.py [--gpu 0]
"""
import argparse

import numpy as np
import pandas as pd

import common as C

RUN = C.D2 / "eval/rollouts/20261026_140246_20k_t1_try3_filt"
OUT = C.OUT / "exp3"
EP_DS, EP_LOG, OFF = 1, 2, 10


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gpu", type=int, default=1)
    ap.add_argument("--n_noise", type=int, default=8)
    args = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    L = pd.read_csv(RUN / "filter_log.csv")
    L = L[L.episode == EP_LOG]
    cmd = L[L.event == "cmd"].reset_index(drop=True)
    s, a = C.load_parquet(RUN / "dataset")[EP_DS]
    assert len(cmd) == len(a) and np.abs(cmd[[f"out_{j}" for j in C.JOINTS]].values - a).max() < 1e-3
    tk = pd.DataFrame({"frame": np.arange(len(a)), "t": np.arange(len(a)) / 30})
    for j in C.JOINTS:
        tk[f"raw_{j}"], tk[f"out_{j}"], tk[f"state_{j}"] = cmd[f"raw_{j}"], cmd[f"out_{j}"], cmd[f"state_{j}"]
        tk[f"sent_{j}"] = np.clip(tk[f"out_{j}"], tk[f"state_{j}"] - 8, tk[f"state_{j}"] + 8)
    mg = L[L.event.str.startswith("merge")].copy()
    mg["real_delay"] = mg.event.str.extract(r"real_delay=(\d+)")[0].astype(int)
    mg["qsize_before"] = mg.event.str.extract(r"qsize_before=(\d+)")[0].astype(int)
    mg["frame_merge"] = mg.tick - OFF
    mg["frame_obs"] = (mg.tick - mg.real_delay - OFF).clip(lower=0)
    mg = mg[["tick", "frame_merge", "frame_obs", "real_delay", "qsize_before"]].reset_index(drop=True)
    tk.to_csv(OUT / "ticks.csv", index=False)
    mg.to_csv(OUT / "merges.csv", index=False)
    print(f"ticks {len(tk)}, merges {len(mg)}", flush=True)
    if not args.gpu:
        return
    import probe_core as PC
    from policy_probe import load_obs
    cache = {}
    fr = mg.frame_obs.tolist()
    F, W = load_obs(RUN / "dataset", [(EP_DS, f) for f in fr], cache)
    S = s[fr]
    E = PC.Engine("020000", n_noise=args.n_noise)
    ch = E.chunks(F, W, S, steps=(5, 10))
    np.savez_compressed(OUT / "replans.npz", s5=ch[5], s10=ch[10], frame_obs=np.array(fr))
    print(f"gpu_busy_s {E.gpu_busy_s:.0f}", flush=True)


if __name__ == "__main__":
    main()
