"""팔 관절 전용 후처리 필터 + RTC 지연·추종 감시 (rollout_logged.py 에서 사용). 2026-10-19.

근거: ~/so101_runs/redbox_all/eval/p0_offline_replay/report.md (P0 열린 루프 재생, 'ema50vc_arm').

필터 (팔 5관절만, 그리퍼는 손대지 않음)
  1단계 EMA   : e[t] = α·x[t] + (1−α)·e[t−1]      — 기준: 직전 'EMA 출력' (실제 관절 상태 아님)
                 단 |x[t] − e[t−1]| > ema_reset(10°) 인 관절은 e[t] = x[t] (P0 와 같은 규칙)
  2단계 속도 제한: y[t] = y[t−1] + clip(e[t] − y[t−1], ±vmax_j / multiplier)
                 — 기준: 직전 '보낸 명령'(필터 출력). vmax_j = 사람 조작 action 의 관절별 |Δ| p99.5 (°/프레임, 30 Hz)
  에피소드 시작(reset) 뒤 첫 프레임:
     init="state"        → e, y 를 그 순간의 실제 관절 상태(Present_Position 관측)로 시작 → 첫 명령도 속도 제한을 받는다 (기본)
     init="first_action" → 첫 정책 action 을 그대로 통과 (P0 시뮬레이터와 같은 규칙, 검증용)
  필터 다음에 lerobot 의 max_relative_target(8°) clamp 가 그대로 적용된다 — 기준: 보낼 때 다시 읽은 실제 위치.
  두 제한은 기준이 달라 충돌하지 않고 차례로 걸린다 (필터 = 명령의 변화 속도, clamp = 명령과 실제 위치의 거리).

감시 (RolloutGuard) — mode off|warn|stop
  starve : 에피소드 첫 명령 '이후' 큐가 비어 명령을 못 보낸 틱이 연속 starve_ticks 이상 (기본 15 = 0.5 s)
  startup: 에피소드 시작 뒤 첫 명령이 나오기까지 startup_ticks 이상 (기본 150 = 5 s).
           첫 chunk 는 콜드 스타트라 0.7–0.8 s(약 22틱) 걸리므로 starve 와 따로 센다 (2026-10-19 실물 첫 시도에서 starve 15 로 오중단)
  stale  : RTC 가 merge 한 chunk 의 실제 지연이 stale_ticks 이상 (기본 30 = queue_threshold — 그 사이 큐가 비었을 수 있음).
           에피소드 첫 chunk(아직 명령을 보내기 전)의 merge 는 제외
  horizon: RTC 지연 추정(delay)이 execution_horizon 이상인 추론이 연속 horizon_count 번 (guidance 가 실행 구간을 못 덮음)
  stall  : 어떤 팔 관절이 |명령 − 실제| > 8° 인데 |Δ실제| < 0.3°/프레임 인 틱이 연속 stall_ticks 이상 (기본 20) → 충돌·끼임 의심
  warn 은 로그만, stop 은 로그 + rollout 종료 요청 (lerobot 표준 종료 경로: 처음 자세로 3 s 보간 복귀 → 토크 끄고 연결 해제).
"""

from __future__ import annotations

import csv
import logging
import threading
import time

import numpy as np

logger = logging.getLogger("lerobot.rollout_logged.arm_filter")

# 사람 조작 action 의 관절별 |프레임 간 변화| p99.5 (°/프레임) — redbox_all 384편 188,530 프레임에서 계산
# (P0 analyze_runs.py 의 VC_TEL, float32 값 그대로. 반올림하면 P0 와 최대 0.05° 어긋남)
VMAX_TELEOP_P995 = {
    "shoulder_pan": 2.4615383,
    "shoulder_lift": 4.1318703,
    "elbow_flex": 4.21978,
    "wrist_flex": 4.57143,
    "wrist_roll": 3.4285736,
}


def joint_name(key: str) -> str:
    return key.removesuffix(".pos")


class ArmFilter:
    def __init__(self, keys, alpha=0.5, ema_reset=10.0, vmax=None, init="state", multiplier=1, enabled=True):
        if not 0.0 < alpha <= 1.0:
            raise ValueError(f"alpha must be in (0, 1], got {alpha}")
        if init not in ("state", "first_action"):
            raise ValueError(f"init must be 'state' or 'first_action', got {init}")
        self.keys = list(keys)
        names = [joint_name(k) for k in self.keys]
        self.arm_idx = np.array([i for i, n in enumerate(names) if "gripper" not in n], dtype=int)
        vmax = VMAX_TELEOP_P995 if vmax is None else vmax
        missing = [names[i] for i in self.arm_idx if names[i] not in vmax]
        if missing:
            raise ValueError(f"no velocity limit for arm joints {missing}")
        self.vmax = np.array([vmax[names[i]] for i in self.arm_idx], dtype=float) / max(int(multiplier), 1)
        self.alpha, self.ema_reset, self.init, self.enabled = float(alpha), float(ema_reset), init, bool(enabled)
        self.reset()

    def reset(self):
        self._ema = None
        self._out = None

    def step(self, x, present=None):
        """x: 이번 정책 action (keys 순서, °). present: 같은 순서의 실제 관절 상태 또는 None.
        반환: (출력 배열, info dict). 그리퍼 등 팔이 아닌 값은 x 그대로."""
        x = np.asarray(x, dtype=float)
        out = x.copy()
        info = {"ema_reset": np.zeros(len(self.arm_idx), bool), "vclip": np.zeros(len(self.arm_idx), bool), "init": ""}
        if not self.enabled:
            return out, info
        xa = x[self.arm_idx]
        if self._ema is None:
            if self.init == "state" and present is not None and np.all(np.isfinite(np.asarray(present, float)[self.arm_idx])):
                self._ema = np.asarray(present, float)[self.arm_idx].copy()
                self._out = self._ema.copy()
                info["init"] = "state"
            else:
                self._ema, self._out = xa.copy(), xa.copy()
                info["init"] = "first_action"
                return out, info
        jump = np.abs(xa - self._ema) > self.ema_reset
        ema = np.where(jump, xa, self.alpha * xa + (1 - self.alpha) * self._ema)
        d = ema - self._out
        y = self._out + np.clip(d, -self.vmax, self.vmax)
        info["ema_reset"], info["vclip"] = jump, np.abs(d) > self.vmax
        self._ema, self._out = ema, y
        out[self.arm_idx] = y
        return out, info


class RolloutGuard:
    def __init__(self, mode="off", starve_ticks=15, stale_ticks=30, horizon=None, horizon_count=10,
                 stall_ticks=20, stall_err=8.0, stall_speed=0.3, on_stop=None, startup_ticks=150):
        if mode not in ("off", "warn", "stop"):
            raise ValueError(f"guard mode must be off|warn|stop, got {mode}")
        self.mode, self.on_stop = mode, on_stop
        self.starve_ticks, self.stale_ticks, self.horizon, self.horizon_count = starve_ticks, stale_ticks, horizon, horizon_count
        self.startup_ticks = startup_ticks
        self.stall_ticks, self.stall_err, self.stall_speed = stall_ticks, stall_err, stall_speed
        self.lock = threading.Lock()
        self.events = []
        self.reset()

    def reset(self):
        with self.lock:
            self.starved_run = 0
            self.startup_run = 0
            self.started = False  # 이번 에피소드에 명령을 한 번이라도 보냈나
            self.horizon_run = 0
            self.stall_run = None
            self.prev_state = None
            self.tripped = False

    def _trip(self, kind, msg):
        self.events.append((time.time(), kind, msg))
        if self.mode == "off":
            return
        if self.mode == "warn":
            logger.warning("GUARD %s: %s", kind, msg)
            return
        logger.error("GUARD STOP %s: %s — rollout 종료 요청 (lerobot 표준 종료: 처음 자세로 복귀 후 토크 해제)", kind, msg)
        if not self.tripped:
            self.tripped = True
            if self.on_stop is not None:
                self.on_stop(kind, msg)

    def on_starved(self):
        with self.lock:
            if not self.started:  # 첫 chunk 대기 (콜드 스타트 포함)
                self.startup_run += 1
                if self.startup_run == self.startup_ticks:
                    self._trip("startup", f"no first action after {self.startup_run} ticks")
                return
            self.starved_run += 1
            if self.starved_run == self.starve_ticks:
                self._trip("starve", f"{self.starved_run} consecutive ticks without an action")

    def on_command(self, cmd, state, arm_idx):
        with self.lock:
            self.started = True
            self.starved_run = 0
            if state is None:
                return
            state = np.asarray(state, float)
            if self.prev_state is not None:
                err = np.abs(np.asarray(cmd, float)[arm_idx] - state[arm_idx])
                spd = np.abs(state[arm_idx] - self.prev_state[arm_idx])
                stuck = (err > self.stall_err) & (spd < self.stall_speed)
                self.stall_run = np.where(stuck, (self.stall_run if self.stall_run is not None else 0) + 1, 0)
                if (self.stall_run >= self.stall_ticks).any():
                    j = int(np.argmax(self.stall_run))
                    self._trip("stall", f"arm joint #{int(arm_idx[j])} error {err[j]:.1f}° while moving {spd[j]:.2f}°/frame for {int(self.stall_run[j])} ticks")
                    self.stall_run[:] = 0
            self.prev_state = state

    def on_delay_estimate(self, delay):
        with self.lock:
            if self.horizon is None:
                return
            self.horizon_run = self.horizon_run + 1 if delay >= self.horizon else 0
            if self.horizon_run == self.horizon_count:
                self._trip("horizon", f"RTC delay estimate {delay} >= execution_horizon {self.horizon} for {self.horizon_run} inferences")

    def on_merge(self, real_delay, idx_diff, qsize_before):
        with self.lock:
            if not self.started:  # 에피소드 첫 chunk — 콜드 스타트 지연은 stale 아님
                return
            if real_delay >= self.stale_ticks:
                self._trip("stale", f"merged chunk latency {real_delay} ticks (consumed {idx_diff}, queue before merge {qsize_before})")


class TimeScaler:
    """실행 속도 배율 (30 Hz 유지). 매 틱 재생 위치를 speed action 만큼 전진시키고 인접 두 action 을 선형 보간 (팔·그리퍼 동일).
    action 은 위치가 지나갈 때만 꺼낸다 (건너뛰기 없음). 다음 action 이 아직 없으면 None (위치 멈춤 → 명령 없음).
    P0 시뮬레이터 replay_sim.run_rtc_ts 와 같은 규칙 (그쪽은 action 이 없을 때 직전 명령을 기록, 여기선 명령을 보내지 않음)."""

    def __init__(self, speed):
        if not 0.3 <= speed <= 1.0:
            raise ValueError(f"exec_speed must be in [0.3, 1.0], got {speed}")
        self.speed = float(speed)
        self.reset()

    def reset(self):
        self.popped = []
        self.pos = 0.0

    def next(self, pop):
        """pop(): 엔진에서 action 하나 꺼냄 (없으면 None). 반환: 보간 action 또는 None."""
        i = int(np.floor(self.pos))
        while len(self.popped) < i + 2:
            a = pop()
            if a is None:
                break
            self.popped.append(a)
        if len(self.popped) < i + 2:
            return None
        w = self.pos - i
        out = self.popped[i] * (1 - w) + self.popped[i + 1] * w
        self.pos += self.speed
        if i >= 1:  # 지난 action 정리 (상대 인덱스 유지)
            del self.popped[:i]
            self.pos -= i
        return out


class FilterLog:
    """틱마다 한 줄: 필터 전·후 action, 실제 상태, 필터 동작, 감시 상태."""

    def __init__(self, path, keys):
        self.f = open(path, "w", newline="")
        self.w = csv.writer(self.f)
        names = [joint_name(k) for k in keys]
        self.w.writerow(["wall", "episode", "tick", "event"] + [f"raw_{n}" for n in names] + [f"out_{n}" for n in names]
                        + [f"state_{n}" for n in names] + ["ema_reset_mask", "vclip_mask", "init", "ts_pos"])
        self.n = 0
        self.lock = threading.Lock()  # RTC 스레드(merge)와 제어 루프가 함께 쓴다

    def row(self, episode, tick, event, raw=None, out=None, state=None, info=None, ts_pos=""):
        raw = [] if raw is None else [f"{v:.4f}" for v in raw]
        out = [] if out is None else [f"{v:.4f}" for v in out]
        state = [] if state is None else [f"{v:.4f}" for v in state]
        k = max(len(raw), len(out), len(state), 6)
        pad = lambda a: a + [""] * (k - len(a))
        m = lambda b: "".join("1" if x else "0" for x in b) if b is not None else ""
        with self.lock:
            self._write(episode, tick, event, pad(raw), pad(out), pad(state), info, m, ts_pos)

    def _write(self, episode, tick, event, raw, out, state, info, m, ts_pos=""):
        self.w.writerow([f"{time.time():.4f}", episode, tick, event] + raw + out + state
                        + [m(info.get("ema_reset")) if info else "", m(info.get("vclip")) if info else "", info.get("init", "") if info else "", ts_pos])
        self.n += 1
        if self.n % 150 == 0:
            self.f.flush()

    def close(self):
        with self.lock:
            self.f.flush()
            self.f.close()
