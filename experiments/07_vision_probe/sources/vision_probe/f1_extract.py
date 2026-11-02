"""F1 특징 추출 (로봇 연결 없음, 학습 없음, 체크포인트·데이터 읽기만).

모델: d2 체크포인트 020000 (vision tower · projector · Gemma 는 pi05_base 와 bit 단위 같음 — 실험설계.md A1).
입력 전처리: d2 preprocessor (state 정규화·토큰화) + modeling_pi05._preprocess_images (resize_with_pad 224, ×2−1) — 정책과 같은 경로.
저장 (float16 memmap, f1_features[_smoke]/):
  sig_{w,f}{13,26}  SigLIP vision_model hidden_states[13] · last_hidden_state(26층 뒤 post-layernorm), wrist(w)/front(f) 256 토큰 × 1152
  kv_{w,f}          Gemma 층 LAYERS 의 K·V (prefix forward 의 KV cache, RoPE 적용 뒤 = action expert 가 읽는 값), (N, 6, 2, 256 토큰, 256)
  meta.csv          행 = 프레임·편집 조건·라벨
프레임:
  train  labels_v2.csv 의 probe_ok (7,810)
  edit   T1 128편 × (c−30, c−60): wrist 큐브 영상 u·v ±1 cm 상당 이동 (exp2 move_blob), front 큐브 접선 ±2 cm (보일 때)
  eval   d2 실물 평가 롤아웃: 닫힘 이벤트마다 3 s 전 ~ 닫힘, 3 프레임 간격, 큐브 보이는 프레임 (같은 라벨 규칙)
d4 보호: --device cuda 이고 d4 학습 프로세스(pid 파일)가 살아 있으면 시작하지 않는다 (--allow-concurrent 로만 무시).
사용:
  시험 (CPU, 3 프레임):  nice -n 19 env PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python f1_extract.py --device cpu --limit 3
  본 실행 (d4 끝난 뒤):  PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python f1_extract.py --device cuda
"""
import argparse
import json
import math
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HOME = Path.home()
sys.path.insert(0, str(HOME / "so101_runs/main_k8/d2/diag_grasp_bias"))
import common as C  # noqa: E402

OUT = Path(__file__).resolve().parent
CKPT = C.D2 / "train/32_20000/pi05_expert_bs32_20k/checkpoints/020000/pretrained_model"
D4_PID = HOME / "so101_runs/main_k8/d4/train/32_20000/pi05_expert_bs32_20k.pid"
TASK = "pick up the red cube and put it in the brown box"
LAYERS = [0, 3, 7, 11, 14, 17]
SIG_LAYER_MID = 13


def d4_alive():
    try:
        pid = int(open(D4_PID).read().strip())
        cmd = open(f"/proc/{pid}/cmdline", "rb").read().decode(errors="ignore")
        return "lerobot-train" in cmd, pid
    except (OSError, ValueError):
        return False, None


def ref_point(area, fit):
    inv = 1 / np.sqrt(area)
    return np.polyval(fit["ref_fit_u"], inv), np.polyval(fit["ref_fit_v"], inv)


def label_from(cu, cv, area, roll, fit):
    """labels_v2 와 같은 규칙: rel (영상, cm), tan/rad (roll 보정, 큐브 − 집게)."""
    us, vs = ref_point(area, fit)
    pxcm = math.sqrt(area) / 2.5
    ru, rv = (cu - us) / pxcm, (cv - vs) / pxcm
    th = math.radians(-5.5 + 0.91 * roll)
    tan = -(ru * math.sin(th) - rv * math.cos(th))
    rad = -(ru * math.cos(th) + rv * math.sin(th))
    return dict(rel_u_cm=ru, rel_v_cm=rv, tan_cm=tan, rad_cm=rad, px_per_cm=pxcm)


def build_items(limit=None):
    """프레임 목록 (source, ds, ep, frame, edit, 라벨). 영상 편집 내용은 extract 에서 만든다."""
    import exp2_sensitivity as X2  # noqa: F401  (move_blob)
    fit = json.load(open(OUT / "folds.json"))
    L = pd.read_csv(OUT / "labels_v2.csv", low_memory=False)
    P = L[L.probe_ok.astype(bool)].reset_index(drop=True)
    items = []
    for _, r in P.iterrows():
        items.append(dict(src="train", ds=str(C.D2 / "dataset"), ep=int(r.ep), frame=int(r.frame), edit="none",
                          t_to_close=r.t_to_close, roll=r.roll, rel_u_cm=r.rel_u_cm, rel_v_cm=r.rel_v_cm, tan_cm=r.tan_cm, rad_cm=r.rad_cm,
                          cube_x=r.cube_x, cube_y=r.cube_y, group=r.group, K=r.K if isinstance(r.K, str) else ""))
    T = pd.read_csv(C.OUT / "grasp_train.csv")
    for e in [e for e in range(256) if T.loc[e, "task"] == "T1"]:
        c = int(T.loc[e, "grasp_f"])
        for lag in (30, 60):
            row = P[(P.ep == e) & (P.frame == c - lag)]
            if row.empty:
                continue
            r = row.iloc[0]
            base = dict(src="edit", ds=str(C.D2 / "dataset"), ep=e, frame=c - lag, t_to_close=lag / 30, roll=r.roll,
                        cube_x=r.cube_x, cube_y=r.cube_y, group=r.group, K=r.K if isinstance(r.K, str) else "")
            for ed in ("w_base", "wu+", "wu-", "wv+", "wv-", "f+", "f-"):
                items.append(dict(base, edit=ed))
    E = pd.read_csv(C.OUT / "grasp_eval.csv")
    for (run, e), g in E.groupby(["run", "ep"]):
        for _, ev in g.iterrows():
            c = int(ev.frame)
            for f in range(max(0, c - 90), c + 1, 3):
                items.append(dict(src="eval", ds=str(C.D2 / "eval/rollouts" / run / "dataset"), ep=int(e), frame=f, edit="none",
                                  t_to_close=(c - f) / 30, run=run, event=int(ev.event), cube_x=ev.cube_x, cube_y=ev.cube_y))
    if limit:   # 시험: 종류마다 섞어서 (train 몇 개 + 편집 한 묶음 7개 + eval 몇 개)
        tr = [x for x in items if x["src"] == "train"][:limit]
        ed = [x for x in items if x["src"] == "edit"][:7]
        ev = [x for x in items if x["src"] == "eval"][-limit:]
        items = tr + ed + ev
    return items, fit


def make_images(it, cache, fit, data_cache):
    """(front, wrist, state, 라벨 갱신 dict) — 편집 포함."""
    import exp2_sensitivity as X2
    fr = C.frames(it["ds"], it["ep"], "front", it["frame"], it["frame"], cache)[0]
    wr = C.frames(it["ds"], it["ep"], "wrist", it["frame"], it["frame"], cache)[0]
    if it["ds"] not in data_cache:
        data_cache[it["ds"]] = C.load_parquet(it["ds"])
    s = data_cache[it["ds"]][it["ep"]][0][it["frame"]]
    upd = {"roll": float(s[4])}
    bw = X2.find_blob(wr, None, min_area=200)
    if it["src"] in ("eval", "edit"):
        if bw is None:
            return None
        lab = label_from(bw[1][0], bw[1][1], bw[0], s[4], fit)
        upd.update(lab)
        upd["imposed_du_cm"] = upd["imposed_dv_cm"] = upd["imposed_tan_cm"] = 0.0
    ed = it["edit"]
    if ed in ("wu+", "wu-", "wv+", "wv-"):
        pxcm = math.sqrt(bw[0]) / 2.5
        du = (1 if ed == "wu+" else -1 if ed == "wu-" else 0) * pxcm
        dv = (1 if ed == "wv+" else -1 if ed == "wv-" else 0) * pxcm
        wr = X2.move_blob(wr, bw[2], du, dv)
        lab = label_from(bw[1][0] + du, bw[1][1] + dv, bw[0], s[4], fit)
        upd.update(lab)
        upd["imposed_du_cm"], upd["imposed_dv_cm"] = du / pxcm, dv / pxcm
    elif ed in ("f+", "f-"):
        x, y = it["cube_x"], it["cube_y"]
        u0, v0 = C.cm_to_px(x, y)
        bf = X2.find_blob(fr, (u0, v0))
        if bf is None:
            return None
        ur = np.array([x, y]) - C.BASE
        ur /= np.linalg.norm(ur)
        ut = np.array([-ur[1], ur[0]])
        sg = 1 if ed == "f+" else -1
        nx, ny = np.array([x, y]) + sg * 2.0 * ut
        u1, v1 = C.cm_to_px(nx, ny)
        fr = X2.move_blob(fr, bf[2], u1 - u0, v1 - v0)
        upd["imposed_tan_cm"] = 2.0 * sg      # 큐브가 로봇 왼쪽(+)으로 2 cm — 물리적으로는 tan(큐브−집게) +2
    return fr, wr, s, upd


def kv_layers(kv, layers):
    out = []
    for li in layers:
        if hasattr(kv, "layers"):
            k, v = kv.layers[li].keys, kv.layers[li].values
        else:
            k, v = kv.key_cache[li], kv.value_cache[li]
        out.append((k, v))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--bs", type=int, default=8)
    ap.add_argument("--allow-concurrent", action="store_true")
    args = ap.parse_args()
    alive, pid = d4_alive()
    if args.device == "cuda" and alive and not args.allow_concurrent:
        raise SystemExit(f"d4 학습(pid {pid})이 실행 중이라 GPU 추출을 시작하지 않습니다. 끝난 뒤 다시 실행하거나 --allow-concurrent.")
    import torch
    from lerobot.policies.factory import make_pre_post_processors
    from lerobot.policies.pi05.modeling_pi05 import make_att_2d_masks, prepare_attention_masks_4d
    from lerobot.policies.pi05.modeling_pi05 import PI05Policy
    from lerobot.utils.constants import OBS_LANGUAGE_ATTENTION_MASK, OBS_LANGUAGE_TOKENS
    if args.device == "cpu":
        torch.set_num_threads(4)
    sub = OUT / ("f1_features_smoke" if args.limit else "f1_features")
    sub.mkdir(exist_ok=True)
    items, fit = build_items(args.limit)
    N = len(items)
    t0 = time.time()
    policy = PI05Policy.from_pretrained(str(CKPT)).to(args.device).eval()
    pre, _ = make_pre_post_processors(policy.config, pretrained_path=str(CKPT),
                                      preprocessor_overrides={"device_processor": {"device": args.device}})
    print(f"model loaded {time.time() - t0:.0f}s, items {N}", flush=True)
    mm = {}
    for cam in ("w", "f"):
        for lay in (SIG_LAYER_MID, 26):
            mm[f"sig_{cam}{lay}"] = np.lib.format.open_memmap(sub / f"sig_{cam}{lay}.npy", "w+", np.float16, (N, 256, 1152))
        mm[f"kv_{cam}"] = np.lib.format.open_memmap(sub / f"kv_{cam}.npy", "w+", np.float16, (N, len(LAYERS), 2, 256, 256))
    m = policy.model
    vis = m.paligemma_with_expert.paligemma.model.vision_tower.vision_model
    cache, dcache, meta = {}, {}, []
    gpu_s = 0.0
    for i0 in range(0, N, args.bs):
        batch, keep = [], []
        for j in range(i0, min(N, i0 + args.bs)):
            r = make_images(items[j], cache, fit, dcache)
            if r is None:
                meta.append(dict(items[j], row=j, valid=False))
                continue
            fr, wr, s, upd = r
            meta.append(dict(items[j], **upd, row=j, valid=True))
            batch.append((fr, wr, s))
            keep.append(j)
        if not batch:
            continue
        tb = time.time()
        with torch.inference_mode():
            F = torch.from_numpy(np.stack([b[0] for b in batch])).to(args.device).float().div(255).permute(0, 3, 1, 2)
            W = torch.from_numpy(np.stack([b[1] for b in batch])).to(args.device).float().div(255).permute(0, 3, 1, 2)
            S = torch.from_numpy(np.stack([b[2] for b in batch]).astype(np.float32)).to(args.device)
            b = pre({"observation.images.front": F, "observation.images.wrist": W, "observation.state": S, "task": [TASK] * len(batch)})
            images, img_masks = policy._preprocess_images(b)   # [front, wrist] (config.image_features 순서)
            for cam, img in (("f", images[0]), ("w", images[1])):
                grab = {}
                # transformers 5.5 에서 output_hidden_states 가 None 을 돌려줘서, 13번째 층 출력(= hidden_states[13])을 hook 으로 받는다
                hk = vis.encoder.layers[SIG_LAYER_MID - 1].register_forward_hook(
                    lambda _m, _i, o: grab.__setitem__("mid", o[0] if isinstance(o, tuple) else o))
                try:
                    with torch.autocast("cuda", dtype=torch.bfloat16, enabled=args.device == "cuda"):
                        o = vis(pixel_values=img.float())
                finally:
                    hk.remove()
                mm[f"sig_{cam}{SIG_LAYER_MID}"][keep] = grab["mid"].float().cpu().numpy().astype(np.float16)
                mm[f"sig_{cam}26"][keep] = o.last_hidden_state.float().cpu().numpy().astype(np.float16)
            pe, ppm, pam = m.embed_prefix(images, img_masks, b[OBS_LANGUAGE_TOKENS], b[OBS_LANGUAGE_ATTENTION_MASK], None, None)
            att4 = prepare_attention_masks_4d(make_att_2d_masks(ppm, pam))
            pos = torch.cumsum(ppm, dim=1) - 1
            m.paligemma_with_expert.paligemma.model.language_model.config._attn_implementation = "eager"  # noqa: SLF001
            _, kv = m.paligemma_with_expert.forward(attention_mask=att4, position_ids=pos, past_key_values=None,
                                                    inputs_embeds=[pe, None], use_cache=True)
            for li, (k, v) in enumerate(kv_layers(kv, LAYERS)):
                k, v = k[:, 0], v[:, 0]     # (B, seq, 256), KV head 1개
                mm["kv_f"][keep, li, 0] = k[:, 0:256].float().cpu().numpy().astype(np.float16)
                mm["kv_f"][keep, li, 1] = v[:, 0:256].float().cpu().numpy().astype(np.float16)
                mm["kv_w"][keep, li, 0] = k[:, 256:512].float().cpu().numpy().astype(np.float16)
                mm["kv_w"][keep, li, 1] = v[:, 256:512].float().cpu().numpy().astype(np.float16)
        if args.device == "cuda":
            torch.cuda.synchronize()
        gpu_s += time.time() - tb
        if (i0 // args.bs) % 50 == 0:
            print(f"{i0 + len(batch)}/{N} · {time.time() - t0:.0f}s · compute {gpu_s:.0f}s · prefix len {pe.shape[1]}", flush=True)
    for a in mm.values():
        a.flush()
    pd.DataFrame(meta).sort_values("row").to_csv(sub / "meta.csv", index=False)
    json.dump(dict(ckpt=str(CKPT), layers=LAYERS, sig_mid=SIG_LAYER_MID, n=N, device=args.device, compute_s=gpu_s,
                   wall_s=time.time() - t0, d4_alive_at_start=alive), open(sub / "extract_meta.json", "w"), indent=1)
    print("done", N, f"compute {gpu_s:.0f}s", flush=True)


if __name__ == "__main__":
    main()
