"""P0 오프라인 재생 시뮬레이터 — 로봇 없이 녹화된 관측을 시간 순서대로 정책에 넣어 추론 방식별 '명령 흐름'을 만든다.

⚠ 열린 루프(open-loop) 재생이다. 관측은 녹화된 것 그대로이며, 시뮬레이션한 명령이 로봇 자세를 바꿔도 다음 관측은
  바뀌지 않는다. 실제 폐루프 성공률·안전성은 이 결과로 확정할 수 없다.

추론 방식 (모두 lerobot 0.6.2 의 실제 정책·전처리·후처리 코드 사용):
  sync : SyncInferenceEngine 과 같다. 50개 chunk 를 다 쓰면 그 자리에서 추론 → 추론 시간만큼 명령 없음(hold)
  rtc  : RTCInferenceEngine._rtc_loop 의 로직을 시뮬레이션 시계로 재현. 실제 클래스 ActionQueue·LatencyTracker,
         _estimate_rtc_delay·_normalize_prev_actions_length, policy.predict_action_chunk(inference_delay, prev_chunk_left_over)
         (= guided denoising) 를 그대로 호출. 스레드 대신: 추론 시작 틱의 관측 사용 → 측정한 실제 추론 시간(벽시계)을
         틱으로 환산한 만큼 큐에서 계속 소비 → 끝난 틱에 queue.merge(new_delay, idx_before)
  ramp : jinnymo/VLASH 방식. chunk 끝 overlap(8) 틱 전에 다음 추론 시작(state ← 현재 chunk 마지막 action),
         전환 시 새 chunk 앞 8개를 w=(i+1)/(n+1) 로 이전 마지막 action 과 섞음
지연: 각 추론의 실제 벽시계 시간(전처리+추론+후처리)을 재서 틱으로 환산 (LAT_SCALE 배, 기본 1.0).
난수: 추론 호출 순번 k 마다 torch.manual_seed(1000 + k) — 같은 방식·같은 순번이면 같은 노이즈.

사용: python -I replay_sim.py <out_dir> [config_name ...]
"""

import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import torch

from lerobot.configs.policies import PreTrainedConfig
from lerobot.configs.types import RTCAttentionSchedule
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.policies.factory import make_pre_post_processors
from lerobot.policies.pi05.modeling_pi05 import PI05Policy
from lerobot.policies.rtc import ActionQueue, LatencyTracker
from lerobot.policies.rtc.configuration_rtc import RTCConfig
from lerobot.rollout.inference.rtc import _estimate_rtc_delay, _normalize_prev_actions_length

HOME = Path.home()
CKPT = HOME / "so101_runs/main/redbox_all/train/32_20000/pi05_expert_bs32_20k/checkpoints/020000/pretrained_model"
FPS = 30.0
DT = 1.0 / FPS
QUEUE_THRESHOLD = 30  # RTCInferenceConfig 기본값
OVERLAP = 8  # ramp
LAT_SCALE = float(__import__("os").environ.get("LAT_SCALE", "1.0"))
# 지연 스파이크 주입: SPIKE_EVERY 번째 추론마다 지연 × SPIKE_MULT (실제 cubemark RTC 최대 0.7–0.8 s 재현용)
SPIKE_EVERY = int(__import__("os").environ.get("SPIKE_EVERY", "0"))
SPIKE_MULT = float(__import__("os").environ.get("SPIKE_MULT", "1.0"))

CONFIGS = {
    "sync_s10": dict(kind="sync", steps=10),
    "sync_s5": dict(kind="sync", steps=5),
    "rtc_h10_lin_s10": dict(kind="rtc", steps=10, h=10, sched="LINEAR"),
    "rtc_h10_exp_s10": dict(kind="rtc", steps=10, h=10, sched="EXP"),
    "rtc_h20_lin_s10": dict(kind="rtc", steps=10, h=20, sched="LINEAR"),
    "rtc_h20_exp_s10": dict(kind="rtc", steps=10, h=20, sched="EXP"),
    "rtc_h10_lin_s5": dict(kind="rtc", steps=5, h=10, sched="LINEAR"),
    "rtc_h10_exp_s5": dict(kind="rtc", steps=5, h=10, sched="EXP"),
    "rtc_h20_lin_s5": dict(kind="rtc", steps=5, h=20, sched="LINEAR"),
    "rtc_h20_exp_s5": dict(kind="rtc", steps=5, h=20, sched="EXP"),
    "rtc_h30_exp_s5": dict(kind="rtc", steps=5, h=30, sched="EXP"),
    "rtc_h30_lin_s5": dict(kind="rtc", steps=5, h=30, sched="LINEAR"),
    "ts100_rtc_h20_exp_s5": dict(kind="rtc_ts", steps=5, h=20, sched="EXP", speed=1.0),
    "ts80_rtc_h20_exp_s5": dict(kind="rtc_ts", steps=5, h=20, sched="EXP", speed=0.8),
    "ts60_rtc_h20_exp_s5": dict(kind="rtc_ts", steps=5, h=20, sched="EXP", speed=0.6),
    "ramp_s10": dict(kind="ramp", steps=10),
    "ramp_s5": dict(kind="ramp", steps=5),
}


def episode_sources():
    """(이름, repo, root, from_idx, to_idx, task, has_gt)."""
    srcs = []
    r = Path(__import__("os").environ.get("ROLLOUT_DS", str(HOME / "so101_runs/main/redbox_all/eval/rollouts/20261019_091114_20k_t1_test1/dataset")))
    srcs.append((__import__("os").environ.get("ROLLOUT_NAME", "rollout_20k_t1"), "oxr/rollout_x", str(r), None, None, True))
    # 학습 에피소드: 6개 그룹에서 길이가 그룹 중앙값에 가장 가까운 1편씩 (사람 action = GT)
    root = HOME / "so101_runs/main/redbox_all/dataset"
    meta = LeRobotDataset("oxr/so101_redbox_all", root=str(root)).meta
    ep = meta.episodes
    env_eps = __import__("os").environ.get("TRAIN_EPS")
    if env_eps:  # 쉼표로 준 에피소드 목록 (그룹 = ep // 64)
        for e in [int(x) for x in env_eps.split(",")]:
            srcs.append((f"train_g{e // 64}_ep{e}", "oxr/so101_redbox_all", str(root), e, None, True))
        return srcs
    for g in range(6):
        lens = [(int(ep[e]["length"]), e) for e in range(g * 64, (g + 1) * 64)]
        med = np.median([l for l, _ in lens])
        _, e = min(lens, key=lambda x: abs(x[0] - med))
        srcs.append((f"train_g{g}_ep{e}", "oxr/so101_redbox_all", str(root), int(e), None, True))
    return srcs


class Source:
    def __init__(self, name, repo, root, episode):
        self.name = name
        # 녹화된 rollout 은 추론으로 멈춘 시간이 프레임에 없다 → 멈춤(hold) 동안 관측을 진행시키지 않는다.
        # 사람 조작 에피소드는 연속 30 Hz 이므로 멈춤 동안에도 시간이 흐른다.
        self.stall_advances = not name.startswith("rollout")
        self.ds = LeRobotDataset(repo, root=root, episodes=None if episode is None else [episode])
        if episode is None:
            self.lo, self.hi = 0, len(self.ds)
        else:
            e = self.ds.meta.episodes[episode]
            self.lo, self.hi = int(e["dataset_from_index"]), int(e["dataset_to_index"])
        cols = self.ds.hf_dataset.select_columns(["index", "action", "observation.state"])[:]
        idx = np.asarray(cols["index"])
        order = np.argsort(idx)
        self.idx = idx[order]
        self.action = np.stack(cols["action"])[order].astype(np.float64)
        self.state = np.stack(cols["observation.state"])[order].astype(np.float64)
        self.n = min(len(self.idx), int(__import__("os").environ.get("MAX_TICKS", "1000000")))
        self._cache = {}

    def obs(self, t):
        t = min(t, self.n - 1)
        if t not in self._cache:
            item = self.ds[t]
            self._cache[t] = {k: v for k, v in item.items() if k.startswith("observation") or k == "task"}
        return self._cache[t]


def load_policy():
    cfg = PreTrainedConfig.from_pretrained(str(CKPT))
    policy = PI05Policy.from_pretrained(str(CKPT), config=cfg).to("cuda").eval()
    pre, post = make_pre_post_processors(cfg, pretrained_path=str(CKPT))
    return policy, pre, post


def set_mode(policy, c):
    policy.config.num_inference_steps = c["steps"]
    if c["kind"] in ("rtc", "rtc_ts"):
        policy.config.rtc_config = RTCConfig(enabled=True, execution_horizon=c["h"], max_guidance_weight=10.0,
                                             prefix_attention_schedule=RTCAttentionSchedule[c["sched"]])
    else:
        policy.config.rtc_config = None
    policy.init_rtc_processor()
    policy.model.rtc_processor = policy.rtc_processor


class Infer:
    def __init__(self, policy, pre, post):
        self.policy, self.pre, self.post = policy, pre, post
        self.k = 0
        self.log = []

    def __call__(self, obs, delay=None, prev=None, state_override=None):
        torch.manual_seed(1000 + self.k)
        self.k += 1
        o = dict(obs)
        if state_override is not None:
            o["observation.state"] = torch.as_tensor(state_override, dtype=torch.float32)
        torch.cuda.synchronize(); t0 = time.perf_counter()
        batch = self.pre(o)
        if delay is None:
            act = self.policy.predict_action_chunk(batch)
        else:
            act = self.policy.predict_action_chunk(batch, inference_delay=delay, prev_chunk_left_over=prev)
        original = act.squeeze(0).clone()
        processed = self.post(act).squeeze(0)
        torch.cuda.synchronize(); lat = (time.perf_counter() - t0) * LAT_SCALE
        if SPIKE_EVERY and self.k % SPIKE_EVERY == 0:
            lat *= SPIKE_MULT
        return original, processed.cpu().double().numpy(), lat


def run_sync(src, inf):
    cmds, switch, hold, lats, t, last = [], [], 0, [], 0, None
    tick = 0
    obs_t = []
    while t < src.n:
        _, chunk, lat = inf(src.obs(t))
        lats.append(lat)
        stall = math.ceil(lat / DT)
        # 추론 동안 로봇에는 새 명령 없음 → 직전 명령 유지 (첫 chunk 전에는 명령 없음)
        for _ in range(stall):
            if t >= src.n: break
            cmds.append(last if last is not None else np.full(6, np.nan)); obs_t.append(t); hold += 1
            t += 1 if src.stall_advances else 0
        switch.append(len(cmds))
        for a in chunk:
            if t >= src.n: break
            cmds.append(a); obs_t.append(t); last = a; t += 1
    return dict(cmds=np.array(cmds), obs_t=np.array(obs_t), switch=np.array(switch), hold=hold, lats=lats,
                n_infer=len(lats))


def run_rtc(src, inf, c):
    rcfg = inf.policy.config.rtc_config
    queue = ActionQueue(rcfg)
    tracker = LatencyTracker()
    cmds, obs_t, merges, lats, delays, starved = [], [], [], [], [], 0
    pending = None  # (finish_tick, original, processed, new_delay, idx_before)
    count = 0
    last = None
    for t in range(src.n):
        # 1) 진행 중 추론이 이 틱에 끝나면 merge (실제 스레드에서 끝나는 시점)
        if pending is not None and t >= pending[0]:
            _, original, processed, new_delay, idx_before = pending
            queue.merge(original, torch.as_tensor(processed), new_delay, idx_before)
            merges.append(len(cmds)); pending = None
        # 2) 백그라운드 스레드: 큐가 threshold 이하이고 추론 중이 아니면 이 틱의 관측으로 시작
        if pending is None and queue.qsize() <= QUEUE_THRESHOLD:
            idx_before = queue.get_action_index()
            prev = queue.get_left_over()
            has_prev = prev is not None and prev.numel() > 0
            delay = _estimate_rtc_delay(latency=tracker.max(), time_per_step=DT, mode=rcfg.mode,
                                        training_max_delay=0, has_previous_actions=has_prev)
            prev = _normalize_prev_actions_length(prev, target_steps=rcfg.execution_horizon) if has_prev else None
            original, processed, lat = inf(src.obs(t), delay=delay, prev=prev)
            new_delay = math.ceil(lat / DT)
            count += 1
            if count <= 1:
                tracker.reset()  # 엔진과 같이 첫 추론은 지연 추적에서 제외
            else:
                tracker.add(lat)
            lats.append(lat); delays.append((delay, new_delay))
            pending = (t + new_delay, original, processed, new_delay, idx_before)
        # 3) 제어 루프: 큐에서 하나 꺼내 보냄. 없으면 starved (직전 명령 유지)
        a = queue.get()
        if a is None:
            starved += 1
            cmds.append(last if last is not None else np.full(6, np.nan))
        else:
            last = a.double().numpy(); cmds.append(last)
        obs_t.append(t)
    return dict(cmds=np.array(cmds), obs_t=np.array(obs_t), switch=np.array(merges), hold=starved, lats=lats,
                delays=delays, n_infer=len(lats))


def run_rtc_ts(src, inf, c):
    """RTC + 시간 배율 s (30 Hz 유지). 매 틱 재생 위치 p 를 s action 만큼 전진, 인접 두 action 을 선형 보간해 보낸다.
    action 은 위치 p 가 지나갈 때만 큐에서 꺼낸다(건너뛰기 없음) → 큐 소비 속도 = s action/틱.
    지연 추정은 action 단위로 환산(latency × s / dt). merge 의 실제 지연은 lerobot 그대로(min(지연 틱, 소비 action 수)).
    관측도 s 배속으로 진행 (팔이 s 배로 느리게 움직이면 장면도 s 배로 느리게 변한다는 근사). obs_t = 그 틱의 관측 인덱스."""
    sp = float(c["speed"])
    rcfg = inf.policy.config.rtc_config
    queue = ActionQueue(rcfg)
    tracker = LatencyTracker()
    cmds, obs_t, merges, lats, delays, starved = [], [], [], [], [], 0
    pending, count, last = None, 0, None
    popped = []          # 꺼낸 action (전역 순서)
    pos = 0.0            # 재생 위치 (popped 인덱스 기준, 실수)
    t_obs = 0.0
    tick = 0
    while int(t_obs) < src.n:
        ot = int(t_obs)
        if pending is not None and tick >= pending[0]:
            _, original, processed, new_delay, idx_before = pending
            queue.merge(original, torch.as_tensor(processed), new_delay, idx_before)
            merges.append(len(cmds)); pending = None
        if pending is None and queue.qsize() <= QUEUE_THRESHOLD:
            idx_before = queue.get_action_index()
            prev = queue.get_left_over()
            has_prev = prev is not None and prev.numel() > 0
            delay = _estimate_rtc_delay(latency=tracker.max() * sp, time_per_step=DT, mode=rcfg.mode,
                                        training_max_delay=0, has_previous_actions=has_prev)
            prev = _normalize_prev_actions_length(prev, target_steps=rcfg.execution_horizon) if has_prev else None
            original, processed, lat = inf(src.obs(ot), delay=delay, prev=prev)
            new_delay = math.ceil(lat / DT)
            count += 1
            if count <= 1: tracker.reset()
            else: tracker.add(lat)
            lats.append(lat); delays.append((delay, new_delay))
            pending = (tick + new_delay, original, processed, new_delay, idx_before)
        # 보간에 필요한 action (floor(pos)+1 까지) 을 큐에서 꺼냄
        need = int(math.floor(pos)) + 2
        while len(popped) < need:
            a = queue.get()
            if a is None: break
            popped.append(a.double().numpy())
        i = int(math.floor(pos))
        if len(popped) >= i + 2:
            w = pos - i
            last = popped[i] * (1 - w) + popped[i + 1] * w
            cmds.append(last); pos += sp
        elif len(popped) == i + 1 and last is not None:
            starved += 1; cmds.append(last)   # 다음 action 이 아직 없음 → 직전 명령 유지
        else:
            starved += 1; cmds.append(last if last is not None else np.full(6, np.nan))
        obs_t.append(ot); t_obs += sp; tick += 1
    return dict(cmds=np.array(cmds), obs_t=np.array(obs_t), switch=np.array(merges), hold=starved, lats=lats,
                delays=delays, n_infer=len(lats))


def run_ramp(src, inf):
    """VLASH/jinnymo: n_action_steps=50, overlap 8 틱 전에 다음 추론(state ← 현재 chunk 마지막 action), 전환 때 8개 선형 ramp."""
    cmds, obs_t, switch, lats, hold = [], [], [], [], 0
    _, cur, lat = inf(src.obs(0)); lats.append(lat)
    t = 0
    stall = math.ceil(lat / DT)
    for _ in range(min(stall, src.n)):
        cmds.append(np.full(6, np.nan)); obs_t.append(t); hold += 1
        t += 1 if src.stall_advances else 0
    nxt, ready_at = None, None
    while t < src.n:
        switch.append(len(cmds))
        for i in range(len(cur)):
            if t >= src.n: break
            if i == len(cur) - OVERLAP:
                _, nxt, lat = inf(src.obs(t), state_override=cur[-1]); lats.append(lat)
                ready_at = t + math.ceil(lat / DT)
            cmds.append(cur[i]); obs_t.append(t); t += 1
        if t >= src.n: break
        waited = 0
        while t + waited < ready_at and t < src.n:  # overlap 안에 못 끝나면 직전 명령 유지
            cmds.append(cur[-1]); obs_t.append(t); hold += 1
            if src.stall_advances: t += 1
            else: waited += 1
        last = cur[-1]
        n = min(OVERLAP, len(nxt))
        for i in range(n):
            w = (i + 1) / (n + 1)
            nxt[i] = last * (1 - w) + nxt[i] * w
        cur = nxt
    return dict(cmds=np.array(cmds), obs_t=np.array(obs_t), switch=np.array(switch), hold=hold, lats=lats,
                n_infer=len(lats))


def main():
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    names = sys.argv[2:] or list(CONFIGS)
    policy, pre, post = load_policy()
    srcs = [Source(n, repo, root, e) for n, repo, root, e, _, _ in episode_sources()]
    for s in srcs:
        np.savez_compressed(out / f"src_{s.name}.npz", action=s.action, state=s.state)
    print("sources", [(s.name, s.n) for s in srcs], flush=True)
    for name in names:
        c = CONFIGS[name]
        set_mode(policy, c)
        inf = Infer(policy, pre, post)
        t0 = time.time(); res = {}
        for s in srcs:
            inf.k = 0  # 소스마다 같은 난수 순서
            r = (run_sync(s, inf) if c["kind"] == "sync" else run_rtc(s, inf, c) if c["kind"] == "rtc"
                 else run_rtc_ts(s, inf, c) if c["kind"] == "rtc_ts" else run_ramp(s, inf))
            res[s.name] = r
        np.savez_compressed(out / f"run_{name}.npz", **{f"{sn}|{k}": np.asarray(v, dtype=object if k == "delays" else None)
                                                         for sn, r in res.items() for k, v in r.items() if k != "delays"})
        meta = {sn: {"n_infer": r["n_infer"], "hold_or_starved": r["hold"], "lat_ms_median": 1000 * float(np.median(r["lats"])),
                     "lat_ms_p95": 1000 * float(np.percentile(r["lats"], 95)), "delays": r.get("delays", [])[:400]} for sn, r in res.items()}
        json.dump({"config": c, "lat_scale": LAT_SCALE, "sources": meta}, open(out / f"run_{name}.json", "w"))
        print(f"{name}: {time.time() - t0:.0f}s " + " ".join(f"{sn}:inf{m['n_infer']}/hold{m['hold_or_starved']}/lat{m['lat_ms_median']:.0f}ms"
                                                      for sn, m in meta.items()), flush=True)


if __name__ == "__main__":
    main()
