"""Action Expert 병목 분석 공통부 (2026-10-27). 로봇·카메라 연결 없음. 학습 코드·데이터·체크포인트는 읽기만 한다.

diag_grasp_bias/probe_core.Engine 과 같은 계산 (고정 noise 은행 + prefix 1회 계산 + euler_integrate 로 denoise) 에 더해
  - device 인자 (CPU 시험용)
  - prefix 토큰 가리기 (knockout): Action Expert 가 prefix 의 roll 숫자 토큰 / state 숫자 토큰 전체를 못 보게
    prefix_pad_masks 를 False 로 바꾼다. prefix 안(영상·문장 사이) 계산은 그대로 — Expert 의 직접 읽기만 막는다.
  - Expert 내부 기록 (capture): 지정한 denoise step (기본 첫 step) 에서 층마다 (a) 50 행동 토큰 평균 hidden, (b) 행동 토큰 → prefix 묶음
    (front · wrist · 과제 문장 · state 숫자 · roll 숫자 · 나머지 문장) 주의 질량 (head · 토큰 평균).
  - d4 보호: MemAvailable 하한 + d4 step 속도 감시 (watchdog) — 기준의 2 배보다 느리면 기다린다.
"""
import re
import sys
import time
from pathlib import Path

import numpy as np

HOME = Path.home()
D2 = HOME / "so101_runs/main_k8/d2"
AB = D2 / "action_bottleneck"
sys.path.insert(0, str(D2 / "diag_grasp_bias"))
import common as C  # noqa: E402

TASK = "pick up the red cube and put it in the brown box"
CKPT_ROOT = D2 / "train/32_20000/pi05_expert_bs32_20k/checkpoints"
D4_LOG = HOME / "so101_runs/main_k8/d4/train/32_20000/pi05_expert_bs32_20k.log"
MIN_AVAIL_GB = 25.0
N_IMG_TOK = 256
Q01_ROLL, Q99_ROLL = -57.01099, 55.163967


def mem_available_gb():
    for line in open("/proc/meminfo"):
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) / 1024 / 1024
    return 0.0


def d4_step_time():
    """d4 로그 끝의 tqdm 'xx.xxs/step' 마지막 값 (없으면 None)."""
    try:
        with open(D4_LOG, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 4000))
            tail = f.read().decode(errors="ignore")
        v = re.findall(r"(\d+)/20000 \[[^\]]*?([\d.]+)s/step\]", tail)
        return (int(v[-1][0]), float(v[-1][1])) if v else None
    except OSError:
        return None


class Watchdog:
    """d4 가 기준(시작 때 값)의 ratio 배보다 느려지면 기다린다. 기다린 시간은 wait_s 에 누적."""

    def __init__(self, ratio=2.0, base=10.1):
        st = d4_step_time()
        self.base = min(st[1], base) if st else base     # d4 단독 속도 ~10.1 s/step (10-27 로그)
        self.ratio = ratio
        self.wait_s = 0.0
        self.log = []

    def check(self):
        while mem_available_gb() < MIN_AVAIL_GB:
            print(f"[mem] {mem_available_gb():.1f} GB available — pausing", flush=True)
            time.sleep(20)
            self.wait_s += 20
        st = d4_step_time()
        if st:
            self.log.append((time.time(), st[0], st[1]))
        if self.base and st and st[1] > self.ratio * self.base:
            print(f"[d4] {st[1]:.1f} s/step > {self.ratio}x base {self.base:.1f} — waiting 60 s", flush=True)
            time.sleep(60)
            self.wait_s += 60


def number_token_spans(pieces):
    """'State:' 다음 숫자들의 토큰 위치 (문장 토큰 번호). → list of lists (숫자마다 토큰 번호), state 구간 전체."""
    try:
        i = next(k for k, p in enumerate(pieces) if p.endswith("State"))
    except StopIteration:
        return [], []
    j = i + 1
    while j < len(pieces) and pieces[j] in (":", "▁:"):
        j += 1
    nums = []
    k = j
    while k < len(pieces) and ";" not in pieces[k]:
        p = pieces[k]
        if p.startswith("▁") or not nums:     # '▁' = 새 숫자 시작 (단독이면 숫자 없음, '▁-' 는 음수 부호)
            nums.append([] if p == "▁" else [k])
        else:
            nums[-1].append(k)
        k += 1
    state_span = list(range(i, k + 1))
    return nums, state_span


class Engine:
    def __init__(self, step="020000", device="cuda", n_noise=4, noise_seed=1234, ckpt_root=CKPT_ROOT):
        import torch
        from lerobot.policies.factory import make_pre_post_processors
        from lerobot.policies.pi05.modeling_pi05 import PI05Policy
        self.torch = torch
        self.device = device
        self.ckpt = Path(ckpt_root) / step / "pretrained_model"
        while mem_available_gb() < MIN_AVAIL_GB + 10:
            print(f"[mem] {mem_available_gb():.1f} GB available — waiting before model load", flush=True)
            time.sleep(30)
        self.policy = PI05Policy.from_pretrained(str(self.ckpt)).to(device).eval()
        self.pre, self.post = make_pre_post_processors(self.policy.config, pretrained_path=str(self.ckpt),
                                                       preprocessor_overrides={"device_processor": {"device": device}})
        tok = [s for s in self.pre.steps if type(s).__name__ == "TokenizerProcessorStep"][0]
        self.tk = tok.input_tokenizer if hasattr(tok, "input_tokenizer") else tok.tokenizer
        cfg = self.policy.config
        g = torch.Generator(device="cpu").manual_seed(noise_seed)
        self.noise_bank = torch.randn((n_noise, cfg.chunk_size, cfg.max_action_dim), generator=g)
        self.gpu_busy_s = 0.0
        self.n_img = len(cfg.image_features) * N_IMG_TOK
        self._cap = None
        self._hooks = []

    # ---------- prefix ----------
    def _batch(self, front, wrist, state):
        torch = self.torch
        dev = self.device
        return {
            "observation.images.front": torch.from_numpy(np.ascontiguousarray(front)).to(dev).float().div(255).permute(0, 3, 1, 2),
            "observation.images.wrist": torch.from_numpy(np.ascontiguousarray(wrist)).to(dev).float().div(255).permute(0, 3, 1, 2),
            "observation.state": torch.from_numpy(np.asarray(state, np.float32)).to(dev),
            "task": [TASK] * len(state),
        }

    def _prefix(self, front, wrist, state):
        torch = self.torch
        from lerobot.policies.pi05.modeling_pi05 import make_att_2d_masks, prepare_attention_masks_4d
        from lerobot.utils.constants import OBS_LANGUAGE_ATTENTION_MASK, OBS_LANGUAGE_TOKENS
        b = self.pre(self._batch(front, wrist, state))
        images, img_masks = self.policy._preprocess_images(b)  # noqa: SLF001
        m = self.policy.model
        pe, ppm, pam = m.embed_prefix(images, img_masks, b[OBS_LANGUAGE_TOKENS], b[OBS_LANGUAGE_ATTENTION_MASK], None, None)
        att4 = prepare_attention_masks_4d(make_att_2d_masks(ppm, pam))
        pos = torch.cumsum(ppm, dim=1) - 1
        m.paligemma_with_expert.paligemma.model.language_model.config._attn_implementation = "eager"  # noqa: SLF001
        _, kv = m.paligemma_with_expert.forward(attention_mask=att4, position_ids=pos, past_key_values=None,
                                                inputs_embeds=[pe, None], use_cache=True)
        return b, ppm, kv

    def token_groups(self, b):
        """배치마다 prefix 토큰 묶음 번호 (front, wrist, task, state, roll, other)."""
        from lerobot.utils.constants import OBS_LANGUAGE_ATTENTION_MASK, OBS_LANGUAGE_TOKENS
        ids = b[OBS_LANGUAGE_TOKENS].cpu().numpy()
        am = b[OBS_LANGUAGE_ATTENTION_MASK].cpu().numpy().astype(bool)
        out = []
        for i in range(len(ids)):
            pieces = self.tk.convert_ids_to_tokens(ids[i][am[i]].tolist())
            nums, span = number_token_spans(pieces)
            off = self.n_img
            roll = [off + k for k in nums[4]] if len(nums) >= 6 else []
            state = [off + k for k in span]
            n_lang = int(am[i].sum())
            task = [off + k for k in range(n_lang) if off + k not in state]
            out.append(dict(front=list(range(0, N_IMG_TOK)), wrist=list(range(N_IMG_TOK, 2 * N_IMG_TOK)), task=task,
                            state=state, roll=roll, n_numbers=len(nums), roll_tokens=[pieces[k - off] for k in roll]))
        return out

    # ---------- capture hooks ----------
    def _install(self):
        exp = self.policy.model.paligemma_with_expert.gemma_expert.model
        self._layers = exp.layers

        def h_out(idx):
            def f(mod, inp, out):
                if self._cap is None or not self._cap["on"]:
                    return
                hs = out[0] if isinstance(out, tuple) else out
                self._cap["hidden"][idx] = hs[:, -50:].float().mean(1).cpu().numpy()
            return f

        def h_attn(idx):
            def f(mod, inp, out):
                if self._cap is None or not self._cap["on"] or not isinstance(out, tuple) or out[1] is None:
                    return
                w = out[1].float()                       # (B, H, 50, prefix+50)
                self._cap["attn"][idx] = w.mean(1).mean(1).cpu().numpy()   # (B, prefix+50)
            return f

        for i, L in enumerate(self._layers):
            self._hooks.append(L.register_forward_hook(h_out(i)))
            self._hooks.append(L.self_attn.register_forward_hook(h_attn(i)))

    def chunks(self, front, wrist, state, knock=None, noise_idx=None, steps=5, bs=8, capture=False, watchdog=None, cap_step=1):
        """→ (n_noise, N, 50, 6) 도. knock: 길이 N 의 list ('roll' | 'state' | None).
        capture=True 면 (hidden (N, 18, 1024), attn_mass (N, 18, 7), groups) 도 돌려준다 (noise 0, denoise step cap_step —
        기본 1 = 순수 noise 입력 단계: 고정 noise 이므로 기록값은 prefix 만의 함수)."""
        torch = self.torch
        from lerobot.policies.common.flow_matching import euler_integrate
        noise_idx = list(range(len(self.noise_bank))) if noise_idx is None else list(noise_idx)
        knock = knock or [None] * len(state)
        if capture and not self._hooks:
            self._install()
        out, H, A, GR = [], [], [], []
        m = self.policy.model
        nL = len(m.paligemma_with_expert.gemma_expert.model.layers)
        for i in range(0, len(state), bs):
            if watchdog:
                watchdog.check()
            t0 = time.time()
            with torch.inference_mode():
                b, ppm, kv = self._prefix(front[i:i + bs], wrist[i:i + bs], state[i:i + bs])
                groups = self.token_groups(b)
                ppm_k = ppm.clone()
                for j, kn in enumerate(knock[i:i + bs]):
                    if kn in ("roll", "state"):
                        ppm_k[j, groups[j][kn]] = False
                n = ppm.shape[0]
                per = []
                for kk, k in enumerate(noise_idx):
                    noise = self.noise_bank[k][None].repeat(n, 1, 1).to(self.device)
                    cap_this = capture and kk == 0
                    stepc = {"i": 0}
                    if cap_this:
                        self._cap = {"on": False, "hidden": [None] * nL, "attn": [None] * nL}

                    def fn(xt, t, cap_this=cap_this, stepc=stepc):
                        stepc["i"] += 1
                        if cap_this:
                            self._cap["on"] = stepc["i"] == cap_step
                        return m.denoise_step(prefix_pad_masks=ppm_k, past_key_values=kv, x_t=xt, timestep=t)
                    x = euler_integrate(fn, noise, steps)
                    if cap_this:
                        cap = self._cap
                        self._cap = None
                        H.append(np.stack(cap["hidden"], 1))
                        mass = []
                        P = ppm.shape[1]
                        for j in range(n):
                            g = groups[j]
                            rows = []
                            for li in range(nL):
                                a = cap["attn"][li][j] if cap["attn"][li] is not None else np.full(P + 50, np.nan)
                                st_other = [q for q in g["state"] if q not in g["roll"]]
                                rows.append([a[g["front"]].sum(), a[g["wrist"]].sum(), a[g["task"]].sum(), a[st_other].sum(),
                                             a[g["roll"]].sum(), a[P:].sum(), a[:P][~ppm[j].cpu().numpy()].sum()])
                            mass.append(rows)
                        A.append(np.array(mass))
                        GR.extend(groups)
                    per.append(self.post(x[:, :, :6]).float().cpu().numpy())
            if self.device == "cuda":
                torch.cuda.synchronize()
            self.gpu_busy_s += time.time() - t0
            out.append(np.stack(per))
        ch = np.concatenate(out, axis=1)
        if capture:
            return ch, np.concatenate(H), np.concatenate(A), GR
        return ch


# ---------- 기하 (vision_probe 라벨 규약) ----------
def M_img2tab(roll_deg):
    """영상 축 상대 위치 (rel_u, rel_v) cm → 탁자 (tan, rad) cm. θ = 0.91·roll − 5.5° (splits.py)."""
    th = np.radians(-5.5 + 0.91 * np.asarray(roll_deg, float))
    s, c = np.sin(th), np.cos(th)
    return np.array([[-s, c], [-c, -s]]).transpose(*([2, 0, 1] if np.ndim(th) else [0, 1]))


def ref_point_fit():
    """기준점 u*(d), v*(d) = a + b/√넓이 (splits.py 와 같은 맞춤) 계수를 labels_v2 에서 되찾는다."""
    import pandas as pd
    L = pd.read_csv(D2 / "vision_probe/labels_v2.csv", usecols=["carea", "u_star", "v_star"]).dropna()
    x = 1 / np.sqrt(L.carea.values)
    return np.polyfit(x, L.u_star.values, 1), np.polyfit(x, L.v_star.values, 1)


def tip_fn():
    import json
    fit = json.load(open(D2 / "diag_grasp_bias/fk_fit.json"))
    Rm, tv = np.array(fit["R"]), np.array(fit["t"])

    def tip(j5):
        p, _ = C.fk_xy(np.atleast_2d(j5))
        return (Rm @ (p[:, :2] * 100).T).T + tv
    return tip


def load_g1(names=("g1", "g1b", "g1c"), hidden=False):
    """G1 결과 디렉터리들을 합친다 (d4 정지 전 g1 = ep 0–31, 정지 뒤 g1c = ep 32–127). → rows, chunks[, hidden]"""
    import pandas as pd
    R, Cs, Hs = [], [], []
    for nm in names:
        d = AB / nm
        if not (d / "rows.csv").exists():
            continue
        r = pd.read_csv(d / "rows.csv")
        c = np.load(d / "chunks.npy", mmap_mode="r")
        n = min(len(r), c.shape[1])
        R.append(r.iloc[:n])
        Cs.append(np.asarray(c[:, :n], np.float32))
        if hidden:
            Hs.append(np.load(d / "expert_hidden.npy", mmap_mode="r")[:n])
    rows = pd.concat(R, ignore_index=True)
    ch = np.concatenate(Cs, axis=1)
    return (rows, ch, np.concatenate([np.asarray(h) for h in Hs])) if hidden else (rows, ch)
