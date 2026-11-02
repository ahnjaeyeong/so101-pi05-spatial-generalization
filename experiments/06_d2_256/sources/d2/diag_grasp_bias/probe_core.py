"""오프라인 정책 추론 공통부 (2차 분석, 2026-10-26). 로봇·카메라에 연결하지 않는다.

policy_probe.Probe 와 다른 점
  - 체크포인트를 인자로 받는다.
  - 고정 noise 은행: seed s 의 noise 는 관측과 무관하게 같다 → 조건 사이 차이를 같은 noise 로 비교 (common random numbers).
  - prefix(PaliGemma, 영상+문장+state) 를 한 번만 계산하고 noise 여러 개·step 수 여러 개로 denoise 만 반복
    (sample_actions 와 같은 계산. denoise_step 이 KV cache 를 clone 하므로 재사용해도 같다 — check_equivalence 로 확인).
  - 메모리 보호: 배치마다 /proc/meminfo MemAvailable 이 MIN_AVAIL_GB 보다 작으면 기다린다 (d4 학습 보호).
    GPU 를 쓴 시간(초)을 gpu_busy_s 에 누적해 학습 지연 추정에 쓴다.
"""
import time

import numpy as np

import common as C

TASK = "pick up the red cube and put it in the brown box"
CKPT_ROOT = C.D2 / "train/32_20000/pi05_expert_bs32_20k/checkpoints"
MIN_AVAIL_GB = 25.0


def mem_available_gb():
    for line in open("/proc/meminfo"):
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) / 1024 / 1024
    return 0.0


class Engine:
    def __init__(self, step="020000", n_noise=8, noise_seed=1234):
        import torch
        from lerobot.policies.factory import make_pre_post_processors
        from lerobot.policies.pi05.modeling_pi05 import PI05Policy
        self.torch = torch
        self.ckpt = CKPT_ROOT / step / "pretrained_model"
        while mem_available_gb() < MIN_AVAIL_GB + 10:
            print(f"[mem] {mem_available_gb():.1f} GB available — waiting before model load", flush=True)
            time.sleep(30)
        self.policy = PI05Policy.from_pretrained(str(self.ckpt)).to("cuda").eval()
        self.pre, self.post = make_pre_post_processors(self.policy.config, pretrained_path=str(self.ckpt),
                                                       preprocessor_overrides={"device_processor": {"device": "cuda"}})
        cfg = self.policy.config
        g = torch.Generator(device="cpu").manual_seed(noise_seed)
        self.noise_bank = torch.randn((n_noise, cfg.chunk_size, cfg.max_action_dim), generator=g)
        self.gpu_busy_s = 0.0

    def _prefix(self, front, wrist, state):
        torch = self.torch
        from lerobot.policies.pi05.modeling_pi05 import make_att_2d_masks, prepare_attention_masks_4d
        from lerobot.utils.constants import OBS_LANGUAGE_ATTENTION_MASK, OBS_LANGUAGE_TOKENS
        batch = {
            "observation.images.front": torch.from_numpy(np.ascontiguousarray(front)).cuda().float().div(255).permute(0, 3, 1, 2),
            "observation.images.wrist": torch.from_numpy(np.ascontiguousarray(wrist)).cuda().float().div(255).permute(0, 3, 1, 2),
            "observation.state": torch.from_numpy(np.asarray(state, np.float32)).cuda(),
            "task": [TASK] * len(state),
        }
        b = self.pre(batch)
        images, img_masks = self.policy._preprocess_images(b)
        m = self.policy.model
        pe, ppm, pam = m.embed_prefix(images, img_masks, b[OBS_LANGUAGE_TOKENS], b[OBS_LANGUAGE_ATTENTION_MASK], None, None)
        att4 = prepare_attention_masks_4d(make_att_2d_masks(ppm, pam))
        pos = torch.cumsum(ppm, dim=1) - 1
        m.paligemma_with_expert.paligemma.model.language_model.config._attn_implementation = "eager"  # noqa: SLF001
        _, kv = m.paligemma_with_expert.forward(attention_mask=att4, position_ids=pos, past_key_values=None,
                                                inputs_embeds=[pe, None], use_cache=True)
        return b, ppm, kv

    def chunks(self, front, wrist, state, noise_idx=None, steps=(5,), bs=8):
        """→ dict steps → (n_noise, N, 50, 6) 도(°). noise_idx: 쓸 noise 은행 번호 (기본 전부)."""
        torch = self.torch
        from lerobot.policies.common.flow_matching import euler_integrate
        noise_idx = list(range(len(self.noise_bank))) if noise_idx is None else list(noise_idx)
        out = {s: [] for s in steps}
        m = self.policy.model
        for i in range(0, len(state), bs):
            while mem_available_gb() < MIN_AVAIL_GB:
                print(f"[mem] {mem_available_gb():.1f} GB available — pausing", flush=True)
                time.sleep(20)
            t0 = time.time()
            with torch.inference_mode():
                _, ppm, kv = self._prefix(front[i:i + bs], wrist[i:i + bs], state[i:i + bs])
                n = ppm.shape[0]
                per = {s: [] for s in steps}
                for k in noise_idx:
                    noise = self.noise_bank[k][None].repeat(n, 1, 1).cuda()
                    for s in steps:
                        x = euler_integrate(lambda xt, t: m.denoise_step(prefix_pad_masks=ppm, past_key_values=kv, x_t=xt, timestep=t),
                                            noise, s)
                        a = self.post(x[:, :, :6])
                        per[s].append(a.float().cpu().numpy())
            torch.cuda.synchronize()
            self.gpu_busy_s += time.time() - t0
            for s in steps:
                out[s].append(np.stack(per[s]))
        return {s: np.concatenate(v, axis=1) for s, v in out.items()}

    def check_equivalence(self, front, wrist, state):
        """prefix 재사용 경로 == policy.predict_action_chunk(noise=…) 인지 (같은 noise)."""
        torch = self.torch
        mine = self.chunks(front, wrist, state, noise_idx=[0], steps=(5,))[5][0]
        self.policy.config.num_inference_steps = 5
        batch = {
            "observation.images.front": torch.from_numpy(np.ascontiguousarray(front)).cuda().float().div(255).permute(0, 3, 1, 2),
            "observation.images.wrist": torch.from_numpy(np.ascontiguousarray(wrist)).cuda().float().div(255).permute(0, 3, 1, 2),
            "observation.state": torch.from_numpy(np.asarray(state, np.float32)).cuda(),
            "task": [TASK] * len(state),
        }
        with torch.inference_mode():
            b = self.pre(batch)
            ref = self.post(self.policy.predict_action_chunk(b, noise=self.noise_bank[0][None].repeat(len(state), 1, 1).cuda()))
        ref = ref.float().cpu().numpy()
        return float(np.abs(mine - ref).max())


def build_grid(T, F1, W1, S1, step_cm=3.0):
    """policy_probe 'grid' 와 같은 합성: 큐브 없는 front 중앙값 + 가장 가까운 학습 큐브 조각. → (front, wrist, state, info)."""
    import cv2
    bg = np.median(F1, axis=0).astype(np.uint8)
    novis = [i for i in range(len(W1)) if not C.blobs(C.red_mask(W1[i]), 60)]
    wbg = np.median(W1[novis], axis=0).astype(np.uint8)
    S0 = np.median(S1, axis=0)
    patches = []
    for i in range(len(F1)):
        b = C.blobs(C.red_mask(F1[i]), 80)
        if not b:
            continue
        a, (u, v), li, lab = max(b, key=lambda t: t[0])
        blob = cv2.dilate((lab == li).astype(np.uint8), np.ones((7, 7), np.uint8))
        ys, xs = np.nonzero(blob)
        patches.append(dict(x=T["cube_x"][i], y=T["cube_y"][i], ys=ys - int(round(v)), xs=xs - int(round(u)), pix=F1[i][ys, xs]))
    pts = np.array([[p["x"], p["y"]] for p in patches])
    hull = cv2.convexHull(pts.astype(np.float32))
    xs = np.arange(np.floor(pts[:, 0].min()) - 1, pts[:, 0].max() + 1.01, step_cm)
    ys = np.arange(np.floor(pts[:, 1].min()) - 1, pts[:, 1].max() + 1.01, step_cm)
    grid = [(x, y) for x in xs for y in ys if cv2.pointPolygonTest(hull, (float(x), float(y)), True) >= -2.0]
    Fg, info = [], []
    for x, y in grid:
        k = int(np.argmin(np.hypot(pts[:, 0] - x, pts[:, 1] - y)))
        p = patches[k]
        u, v = C.cm_to_px(x, y)
        img = bg.copy()
        yy, xx = p["ys"] + int(round(v)), p["xs"] + int(round(u))
        ok = (yy >= 0) & (yy < img.shape[0]) & (xx >= 0) & (xx < img.shape[1])
        img[yy[ok], xx[ok]] = p["pix"][ok]
        Fg.append(img)
        info.append(dict(x=x, y=y))
    return np.stack(Fg), np.repeat(wbg[None], len(Fg), 0), np.repeat(S0[None], len(Fg), 0), info
