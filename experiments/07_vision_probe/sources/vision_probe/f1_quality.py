"""F1-E 영상 품질 변형 특징 추출 (로봇 연결 없음, 학습 없음, 체크포인트·데이터 읽기만).

f1_extract.py 와 같은 모델·전처리·저장 형식. 입력 영상만 바꾼다 (실험설계_부록_영상품질.md 1(b)).
  wrist 변형: labels_v2 probe_ok 에서 1,000 프레임 (seed 0) × {orig, b0.8, b1.2, blur1, blur2}
    b×: RGB × 배율 (0–255 자름).  blur σ: 224 입력 기준 σ px → 640 원본에 σ·640/224 로 가우시안
  front 변형: T1+T3 256편 × 프레임 {0, 30, 60} × {orig, crop1.6}
    crop1.6: 640×480 에서 400×300 창을 잘라 640×480 로 키움. 창 중심 = 학습 큐브 위치(front px) 범위의 중심.
    표적 = 탁자 위 큐브 위치 cube_x, cube_y (cm). 창 밖 큐브는 meta 의 in_crop=False.
출력: f1_quality_features/ (sig_{w,f}{13,26}, kv_{w,f}, meta.csv, extract_meta.json)
사용: PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python f1_quality.py --device cuda [--allow-concurrent] [--limit n]
"""
import argparse
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f1_extract as FE  # noqa: E402

C = FE.C
OUT = FE.OUT
N_WRIST = 1000
W_VARIANTS = ["orig", "b0.8", "b1.2", "blur1", "blur2"]
F_VARIANTS = ["orig", "crop1.6"]
F_FRAMES = [0, 30, 60]
CROP_W, CROP_H = 400, 300


def crop_window():
    T = pd.read_csv(C.OUT / "grasp_train.csv")
    uv = np.array([C.cm_to_px(a, b) for a, b in zip(T.cube_x, T.cube_y)])
    cu = (uv[:, 0].min() + uv[:, 0].max()) / 2
    cv = (uv[:, 1].min() + uv[:, 1].max()) / 2
    u0 = int(round(np.clip(cu - CROP_W / 2, 0, 640 - CROP_W)))
    v0 = int(round(np.clip(cv - CROP_H / 2, 0, 480 - CROP_H)))
    return u0, v0


def build_items(limit=None):
    L = pd.read_csv(OUT / "labels_v2.csv", low_memory=False)
    P = L[L.probe_ok.astype(bool)].reset_index(drop=True)
    pick = np.sort(np.random.default_rng(0).choice(len(P), N_WRIST, replace=False))
    items = []
    for i in pick:
        r = P.iloc[i]
        for v in W_VARIANTS:
            items.append(dict(src="wrist_q", variant=v, ds=str(C.D2 / "dataset"), ep=int(r.ep), frame=int(r.frame),
                              t_to_close=r.t_to_close, roll=r.roll, rel_u_cm=r.rel_u_cm, rel_v_cm=r.rel_v_cm,
                              tan_cm=r.tan_cm, rad_cm=r.rad_cm, cube_x=r.cube_x, cube_y=r.cube_y, group=r.group))
    T = pd.read_csv(C.OUT / "grasp_train.csv")
    u0, v0 = crop_window()
    for e in range(256):
        u, v = C.cm_to_px(T.loc[e, "cube_x"], T.loc[e, "cube_y"])
        inc = bool(u0 + 20 <= u <= u0 + CROP_W - 20 and v0 + 20 <= v <= v0 + CROP_H - 20)
        for f in F_FRAMES:
            for var in F_VARIANTS:
                items.append(dict(src="front_q", variant=var, ds=str(C.D2 / "dataset"), ep=e, frame=f, t_to_close=np.nan,
                                  cube_x=T.loc[e, "cube_x"], cube_y=T.loc[e, "cube_y"], group=T.loc[e, "group"],
                                  task=T.loc[e, "task"], in_crop=inc))
    if limit:
        w = [x for x in items if x["src"] == "wrist_q"][:limit * len(W_VARIANTS)]
        f = [x for x in items if x["src"] == "front_q"][:limit * len(F_VARIANTS)]
        items = w + f
    return items


def transform(img, variant):
    if variant.startswith("blur"):
        s = float(variant[4:]) * 640 / 224
        return cv2.GaussianBlur(img, (0, 0), sigmaX=s, sigmaY=s)
    if variant.startswith("b"):
        return np.clip(img.astype(np.float32) * float(variant[1:]), 0, 255).astype(np.uint8)
    if variant == "crop1.6":
        u0, v0 = crop_window()
        return cv2.resize(img[v0:v0 + CROP_H, u0:u0 + CROP_W], (640, 480), interpolation=cv2.INTER_LINEAR)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--bs", type=int, default=8)
    ap.add_argument("--allow-concurrent", action="store_true")
    args = ap.parse_args()
    alive, pid = FE.d4_alive()
    if args.device == "cuda" and alive and not args.allow_concurrent:
        raise SystemExit(f"d4 학습(pid {pid})이 실행 중이라 GPU 추출을 시작하지 않습니다. 끝난 뒤 다시 실행하거나 --allow-concurrent.")
    import torch
    from lerobot.policies.factory import make_pre_post_processors
    from lerobot.policies.pi05.modeling_pi05 import PI05Policy, make_att_2d_masks, prepare_attention_masks_4d
    from lerobot.utils.constants import OBS_LANGUAGE_ATTENTION_MASK, OBS_LANGUAGE_TOKENS
    if args.device == "cpu":
        torch.set_num_threads(4)
    sub = OUT / ("f1_quality_smoke" if args.limit else "f1_quality_features")
    sub.mkdir(exist_ok=True)
    items = build_items(args.limit)
    N = len(items)
    t0 = time.time()
    policy = PI05Policy.from_pretrained(str(FE.CKPT)).to(args.device).eval()
    pre, _ = make_pre_post_processors(policy.config, pretrained_path=str(FE.CKPT),
                                      preprocessor_overrides={"device_processor": {"device": args.device}})
    print(f"model loaded {time.time() - t0:.0f}s, items {N}, crop window {crop_window()}", flush=True)
    mm = {}
    for cam in ("w", "f"):
        for lay in (FE.SIG_LAYER_MID, 26):
            mm[f"sig_{cam}{lay}"] = np.lib.format.open_memmap(sub / f"sig_{cam}{lay}.npy", "w+", np.float16, (N, 256, 1152))
        mm[f"kv_{cam}"] = np.lib.format.open_memmap(sub / f"kv_{cam}.npy", "w+", np.float16, (N, len(FE.LAYERS), 2, 256, 256))
    m = policy.model
    vis = m.paligemma_with_expert.paligemma.model.vision_tower.vision_model
    cache, dcache, meta = {}, {}, []
    gpu_s = 0.0
    for i0 in range(0, N, args.bs):
        batch, keep = [], []
        for j in range(i0, min(N, i0 + args.bs)):
            it = items[j]
            fr = C.frames(it["ds"], it["ep"], "front", it["frame"], it["frame"], cache)[0]
            wr = C.frames(it["ds"], it["ep"], "wrist", it["frame"], it["frame"], cache)[0]
            if it["ds"] not in dcache:
                dcache[it["ds"]] = C.load_parquet(it["ds"])
            s = dcache[it["ds"]][it["ep"]][0][it["frame"]]
            if it["src"] == "wrist_q":
                wr = transform(wr, it["variant"])
            else:
                fr = transform(fr, it["variant"])
            meta.append(dict(it, row=j, valid=True, roll=float(s[4])))
            batch.append((fr, wr, s))
            keep.append(j)
        tb = time.time()
        with torch.inference_mode():
            F = torch.from_numpy(np.stack([b[0] for b in batch])).to(args.device).float().div(255).permute(0, 3, 1, 2)
            W = torch.from_numpy(np.stack([b[1] for b in batch])).to(args.device).float().div(255).permute(0, 3, 1, 2)
            S = torch.from_numpy(np.stack([b[2] for b in batch]).astype(np.float32)).to(args.device)
            b = pre({"observation.images.front": F, "observation.images.wrist": W, "observation.state": S, "task": [FE.TASK] * len(batch)})
            images, img_masks = policy._preprocess_images(b)
            for cam, img in (("f", images[0]), ("w", images[1])):
                grab = {}
                hk = vis.encoder.layers[FE.SIG_LAYER_MID - 1].register_forward_hook(
                    lambda _m, _i, o: grab.__setitem__("mid", o[0] if isinstance(o, tuple) else o))
                try:
                    with torch.autocast("cuda", dtype=torch.bfloat16, enabled=args.device == "cuda"):
                        o = vis(pixel_values=img.float())
                finally:
                    hk.remove()
                mm[f"sig_{cam}{FE.SIG_LAYER_MID}"][keep] = grab["mid"].float().cpu().numpy().astype(np.float16)
                mm[f"sig_{cam}26"][keep] = o.last_hidden_state.float().cpu().numpy().astype(np.float16)
            pe, ppm, pam = m.embed_prefix(images, img_masks, b[OBS_LANGUAGE_TOKENS], b[OBS_LANGUAGE_ATTENTION_MASK], None, None)
            att4 = prepare_attention_masks_4d(make_att_2d_masks(ppm, pam))
            pos = torch.cumsum(ppm, dim=1) - 1
            m.paligemma_with_expert.paligemma.model.language_model.config._attn_implementation = "eager"  # noqa: SLF001
            _, kv = m.paligemma_with_expert.forward(attention_mask=att4, position_ids=pos, past_key_values=None,
                                                    inputs_embeds=[pe, None], use_cache=True)
            for li, (k, v) in enumerate(FE.kv_layers(kv, FE.LAYERS)):
                k, v = k[:, 0], v[:, 0]
                mm["kv_f"][keep, li, 0] = k[:, 0:256].float().cpu().numpy().astype(np.float16)
                mm["kv_f"][keep, li, 1] = v[:, 0:256].float().cpu().numpy().astype(np.float16)
                mm["kv_w"][keep, li, 0] = k[:, 256:512].float().cpu().numpy().astype(np.float16)
                mm["kv_w"][keep, li, 1] = v[:, 256:512].float().cpu().numpy().astype(np.float16)
        if args.device == "cuda":
            torch.cuda.synchronize()
        gpu_s += time.time() - tb
        if (i0 // args.bs) % 50 == 0:
            print(f"{i0 + len(batch)}/{N} · {time.time() - t0:.0f}s · compute {gpu_s:.0f}s", flush=True)
    for a in mm.values():
        a.flush()
    pd.DataFrame(meta).sort_values("row").to_csv(sub / "meta.csv", index=False)
    json.dump(dict(ckpt=str(FE.CKPT), layers=FE.LAYERS, n=N, device=args.device, compute_s=gpu_s, wall_s=time.time() - t0,
                   crop_window=list(crop_window()) + [CROP_W, CROP_H], d4_alive_at_start=alive),
              open(sub / "extract_meta.json", "w"), indent=1)
    print("done", N, f"compute {gpu_s:.0f}s", flush=True)


if __name__ == "__main__":
    main()
