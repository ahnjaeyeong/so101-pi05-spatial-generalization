"""학습 전 CPU 검증 (GPU · 로봇 없음, 모델 가중치 적재 없음). 결과: checks/check_cpu.json, 통과하면 checks/CPU_CHECK_OK.

T1  A0 표집 순서 == lerobot 원래 EpisodeAwareSampler (seed 2001 · 2002, epoch 0 · 1 전체)
T2  A1 · A2 · A2r 실제 표집 확률 == 설계 (가중 목록 한 epoch: 프레임별 정확히 일치; 학습 128,000 draw: 구간 · K/R · 칸 등급 몫 차)
T3  50-step action chunk == 원본 parquet 프레임 (lerobot make_dataset 로 실제 학습 cfg 그대로, A2 sampler 가 뽑은 index + 판 끝 프레임)
T4  정규화 통계: 학습 때 주입될 dataset.meta.stats == d2 020000 normalizer / unnormalizer safetensors
T5  출력 경로 · 가드: 계획된 5 실행은 통과, 위험한 인자 (d2/d4 폴더, heldout, resume, 다른 checkpoint) 는 거부
T6  H 격리: 가중 생성 · launcher · 계획 파일이 heldout 을 읽지 않음, 가드가 heldout 거부, heldout 데이터셋 없음/있음 기록
T7  학습 설정: expert-only · vision 동결 · LR 곡선 (warmup 200, peak 1e-5, 4000 에서 2.5e-6, 자동 축소 없음) · chunk 50
사용: CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 nice -n 10 ~/so101-env/bin/python check_cpu.py
"""
import glob
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

SA = Path(__file__).parent
sys.path.insert(0, str(SA))
import plan_runs as PR  # noqa: E402
import train_weighted as TW  # noqa: E402

OUT = SA / "checks"
OUT.mkdir(exist_ok=True)
RES = {"time": time.strftime("%F %T")}
FAIL = []


def rec(name, ok, **kw):
    RES[name] = dict(ok=bool(ok), **kw)
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {json.dumps(kw, ensure_ascii=False, default=str)[:600]}", flush=True)
    if not ok:
        FAIL.append(name)


def episodes_meta():
    e = pd.read_parquet(sorted(glob.glob(str(PR.D2_DS / "meta/episodes/*/*.parquet")))[0],
                        columns=["episode_index", "dataset_from_index", "dataset_to_index"])
    return e.sort_values("episode_index")


def samplers(arm, seed):
    from lerobot.datasets.sampler import EpisodeAwareSampler
    e = episodes_meta()
    w = np.load(SA / f"weights/weights_{arm}.npy")
    W = TW.make_weighted_sampler_class(EpisodeAwareSampler, w)
    kw = dict(episode_indices_to_use=None, shuffle=True, seed=seed, absolute_to_relative_idx=None)
    a = EpisodeAwareSampler(e.dataset_from_index.tolist(), e.dataset_to_index.tolist(), **kw)
    b = W(e.dataset_from_index.tolist(), e.dataset_to_index.tolist(), **kw)
    return a, b, w


def t1():
    out = {}
    ok = True
    for seed in (2001, 2002):
        a, b, _ = samplers("A0", seed)
        for ep in range(2):
            x = np.fromiter(a._iter_epoch(ep, 0), np.int64)
            y = np.fromiter(b._iter_epoch(ep, 0), np.int64)
            same = len(x) == len(y) and bool((x == y).all())
            out[f"seed{seed}_epoch{ep}"] = dict(n=len(x), identical=same, first5=x[:5].tolist())
            ok &= same
    rec("T1_A0_order_identical", ok, **out)


def t2():
    F = pd.read_parquet(SA / "s1_frames.parquet")
    idx = pd.concat([pd.read_parquet(f, columns=["index", "episode_index", "frame_index"])
                     for f in sorted(glob.glob(str(PR.D2_DS / "data/*/*.parquet")))])
    F = F.merge(idx, left_on=["ep", "frame"], right_on=["episode_index", "frame_index"]).set_index("index").sort_index()
    F["tier"] = np.select([F.n_cell < 0, F.n_cell <= 4, F.n_cell <= 14], ["칸없음", "희소", "얇음"], "보통")
    out, ok = {}, True
    draws = 32 * 4000
    for arm in ("A0", "A1", "A2", "A2r"):
        _, b, w = samplers(arm, 2001)
        ep0 = np.fromiter(b._iter_epoch(0, 0), np.int64)
        cnt = np.bincount(ep0, minlength=len(w))
        exact = bool((cnt == w).all())                       # 한 epoch 에 프레임 i 가 정확히 w_i 번
        it = b._iter_epoch(0, 0)
        tr = np.fromiter((next(it) for _ in range(draws)), np.int64) if draws <= len(ep0) else \
            np.r_[ep0, np.fromiter(b._iter_epoch(1, 0), np.int64)][:draws]
        p_des = w / w.sum()
        dev = {}
        for col in ("phase", "mode", "tier"):
            des = pd.Series(p_des, index=F.index).groupby(F[col]).sum()
            act = F.loc[tr, col].value_counts(normalize=True).reindex(des.index, fill_value=0)
            dev[col] = {k: [round(100 * des[k], 2), round(100 * act[k], 2)] for k in des.index}
        maxdev = max(abs(v[0] - v[1]) for d in dev.values() for v in d.values())
        ok_arm = exact and maxdev <= 0.3
        ok &= ok_arm
        out[arm] = dict(list_len=len(ep0), epoch_counts_equal_weights=exact, draws=draws,
                        max_share_dev_pp=round(maxdev, 3), shares_design_vs_draws=dev)
    rec("T2_sampling_probabilities", ok, **out)


def build_cfg(name="CHECK_tmp_never_created", seed=2001):
    import lerobot.scripts.lerobot_train as LT  # 학습과 같은 import 경로 (policy config 등록)
    from lerobot.configs import parser
    from lerobot.configs.train import TrainPipelineConfig

    LT.register_third_party_plugins()

    @parser.wrap()
    def get(cfg: TrainPipelineConfig):
        return cfg

    old = sys.argv
    sys.argv = ["lerobot-train"] + PR.train_args(name, seed)
    try:
        cfg = get()
        cfg.validate()
    finally:
        sys.argv = old
    return cfg


def t3(cfg):
    from lerobot.datasets.factory import make_dataset
    ds = make_dataset(cfg)
    data = {}
    for f in sorted(glob.glob(str(PR.D2_DS / "data/*/*.parquet"))):
        d = pd.read_parquet(f, columns=["index", "episode_index", "frame_index", "action", "observation.state"])
        data[f] = d
    D = pd.concat(data.values()).set_index("index").sort_index()
    A = np.stack(D.action.values).astype(np.float32)
    S = np.stack(D["observation.state"].values).astype(np.float32)
    e = episodes_meta().set_index("episode_index")
    _, b, w = samplers("A2", 2001)
    pick = list(np.fromiter(b._iter_epoch(0, 0), np.int64)[:16])
    pick += [int(i) for i in np.flatnonzero(w >= 12)[:4]]                 # 가장 큰 가중 프레임
    pick += [int(e.dataset_to_index.iloc[k]) - j for k in (0, 100, 255) for j in (1, 25)]  # 판 끝 근처 (padding)
    rows, ok = [], True
    for gi in pick:
        it = ds[gi]
        ep, fr = int(it["episode_index"]), int(it["frame_index"])
        s0, s1 = int(e.dataset_from_index[ep]), int(e.dataset_to_index[ep])
        want = np.array([A[min(gi + k, s1 - 1)] for k in range(50)])
        pad_want = np.array([gi + k >= s1 for k in range(50)])
        got = it["action"].numpy()
        pad_got = it["action_is_pad"].numpy().astype(bool)
        st_ok = np.allclose(it["observation.state"].numpy(), S[gi], atol=1e-5)
        a_ok = got.shape == (50, 6) and np.allclose(got[~pad_want], want[~pad_want], atol=1e-5)
        p_ok = bool((pad_got == pad_want).all())
        idx_ok = s0 + fr == gi and int(D.loc[gi, "episode_index"]) == ep
        imgs = {k: tuple(v.shape) for k, v in it.items() if k.startswith("observation.images")}
        good = a_ok and p_ok and st_ok and idx_ok
        ok &= good
        rows.append(dict(index=gi, ep=ep, frame=fr, n_pad=int(pad_want.sum()), action_ok=a_ok, pad_ok=p_ok,
                         state_ok=st_ok, index_ok=idx_ok, max_abs_diff=float(np.abs(got[~pad_want] - want[~pad_want]).max()),
                         images=imgs))
    rec("T3_action_chunk_alignment", ok, n=len(rows), delta_action=str(cfg.policy.action_delta_indices)[:40],
        fails=[r for r in rows if not (r["action_ok"] and r["pad_ok"] and r["state_ok"] and r["index_ok"])],
        sample=rows[:3] + rows[-3:])
    return ds


def t4(ds):
    from safetensors.torch import load_file
    pre = load_file(str(PR.D2_CK / "pretrained_model/policy_preprocessor_step_3_normalizer_processor.safetensors"))
    post = load_file(str(PR.D2_CK / "pretrained_model/policy_postprocessor_step_0_unnormalizer_processor.safetensors"))
    st = ds.meta.stats
    diffs, n = {}, 0
    for nm, t in list(pre.items()) + [(f"post:{k}", v) for k, v in post.items()]:
        key = nm.split(":", 1)[-1]
        feat, stat = key.rsplit(".", 1)
        if feat not in st or stat not in st[feat]:
            diffs[nm] = "dataset stats 에 없음"
            continue
        ref = torch.as_tensor(np.asarray(st[feat][stat]), dtype=t.dtype).reshape(t.shape)
        d = float((ref - t).abs().max())
        n += 1
        if d > 0:
            diffs[nm] = d
    rec("T4_normalization_stats_identical", not diffs and n > 0, compared=n, diffs=diffs,
        keys=sorted(pre)[:12])


def t5():
    out, ok = {}, True
    for name, arm, seed in PR.RUNS:
        errs, _ = TW.guard(PR.train_args(name, seed), SA / f"weights/weights_{arm}.npy", check_procs=False, full_hash=False)
        out[name] = errs or "OK"
        ok &= not errs
    base = PR.train_args("X_probe", 2001)
    bad_cases = {
        "output_dir=d2 학습 폴더": [a if not a.startswith("--output_dir=") else
                                f"--output_dir={Path.home()}/so101_runs/main_k8/d2/train/32_20000/X" for a in base],
        "output_dir=d4 폴더": [a if not a.startswith("--output_dir=") else
                             f"--output_dir={Path.home()}/so101_runs/main_k8/d4/train/X" for a in base],
        "output_dir=이미 있는 runs": [a if not a.startswith("--output_dir=") else f"--output_dir={SA}/weights" for a in base],
        "dataset.root=heldout": [a if not a.startswith("--dataset.root=") else
                                 f"--dataset.root={Path.home()}/so101_runs/main_k8/heldout_h/dataset" for a in base],
        "resume": base + ["--resume=true"],
        "policy.path=d4 005000": [a if not a.startswith("--policy.path=") else
                                  f"--policy.path={Path.home()}/so101_runs/main_k8/d4/train/32_20000/pi05_expert_bs32_20k/checkpoints/005000/pretrained_model"
                                  for a in base],
    }
    for k, argv in bad_cases.items():
        errs, _ = TW.guard(argv, SA / "weights/weights_A0.npy", check_procs=False, full_hash=False)
        out[f"거부:{k}"] = errs or "통과됨(문제)"
        ok &= bool(errs)
    errs, _ = TW.guard(PR.train_args("A0_s2001", 2001), SA / "weights/weights_A0.npy", check_procs=True, full_hash=False)
    out["d4_or_other_training_running_now"] = errs
    paths = [Path(a.split("=", 1)[1]).resolve() for n, _, s in PR.RUNS for a in PR.train_args(n, s) if a.startswith("--output_dir=")]
    out["output_dirs"] = [str(p) for p in paths]
    out["any_exists"] = [str(p) for p in paths if p.exists()]
    ok &= not out["any_exists"] and len(set(paths)) == len(paths)
    rec("T5_output_paths_and_guards", ok, **out)


def t6():
    files = ["s1_design_numbers.py", "make_weights.py", "train_weighted.py", "plan_runs.py"]
    # H 데이터 경로 (heldout_h 폴더 · repo) 를 코드가 가리키는지 — 설명 문구 '(heldout)' 은 제외
    reads_heldout = {f: any(t in (SA / f).read_text() for t in ("heldout_h", "so101_k8_heldout")) for f in files}
    # train_weighted 은 'heldout' 을 거부하는 문자열로만 가짐 → 읽기 코드가 아닌지 확인
    tw_lines = [ln.strip() for ln in (SA / "train_weighted.py").read_text().splitlines() if "heldout" in ln.lower()]
    man = json.load(open(SA / "weights/manifest.json"))
    h_dir = Path.home() / "so101_runs/main_k8/heldout_h"
    ok = not any(v for k, v in reads_heldout.items() if k != "train_weighted.py") and man["dataset"] == str(PR.D2_DS) \
        and all("heldout" not in a.lower() for n, _, s in PR.RUNS for a in PR.train_args(n, s))
    rec("T6_H_isolation", ok, files_mentioning_heldout=reads_heldout, train_weighted_heldout_lines=tw_lines,
        weights_source=man["source"], weights_dataset=man["dataset"], heldout_dataset_exists=h_dir.exists(),
        note="H 는 가중 계산 · LR · step · checkpoint 선택에 쓰지 않음 (판정은 4000 고정). 가드가 heldout 경로를 거부 (T5).")


def t7(cfg):
    p = cfg.policy
    sch = cfg.scheduler
    m = torch.nn.Linear(1, 1)
    opt = torch.optim.AdamW(m.parameters(), lr=cfg.optimizer.lr)
    lr_s = sch.build(opt, cfg.steps)
    lrs = []
    for s in range(cfg.steps):
        lrs.append(opt.param_groups[0]["lr"])
        opt.step()
        lr_s.step()
    lrs = np.array(lrs)
    out = dict(train_expert_only=p.train_expert_only, freeze_vision_encoder=p.freeze_vision_encoder, dtype=p.dtype,
               gradient_checkpointing=p.gradient_checkpointing, chunk_size=p.chunk_size, n_action_steps=p.n_action_steps,
               pretrained_path=str(p.pretrained_path), steps=cfg.steps, batch_size=cfg.batch_size, seed=cfg.seed,
               save_freq=cfg.save_freq, resume=cfg.resume, image_transforms=cfg.dataset.image_transforms.enable,
               optimizer=dict(lr=cfg.optimizer.lr, betas=cfg.optimizer.betas, wd=cfg.optimizer.weight_decay,
                              clip=cfg.optimizer.grad_clip_norm),
               scheduler=dict(type=sch.type, warmup=sch.num_warmup_steps, decay=sch.num_decay_steps, peak=sch.peak_lr,
                              decay_lr=sch.decay_lr),
               lr_at={k: float(lrs[k]) for k in (0, 100, 199, 200, 1000, 2000, 3000, 3999)}, lr_max=float(lrs.max()),
               lr_argmax=int(lrs.argmax()))
    ok = (p.train_expert_only and p.freeze_vision_encoder and p.chunk_size == 50 and cfg.steps == 4000 and cfg.batch_size == 32
          and cfg.save_freq == 2000 and not cfg.resume and abs(lrs.max() - 1e-5) < 1e-7 and 199 <= lrs.argmax() <= 201
          and sch.num_warmup_steps == 200 and sch.num_decay_steps == 4000 and abs(sch.peak_lr - 1e-5) < 1e-12
          and abs(lrs[-1] - 2.5e-6) < 2e-8 and Path(p.pretrained_path).resolve() == PR.D2_CK / "pretrained_model")
    rec("T7_training_config", ok, **out)


def main():
    t1()
    t2()
    cfg = build_cfg()
    t7(cfg)
    t5()
    t6()
    ds = t3(cfg)
    t4(ds)
    bad = TW.verify_hashes(full=True)
    rec("T8_d2_files_unchanged", not bad, changed=bad)
    RES["fail"] = FAIL
    json.dump(RES, open(OUT / "check_cpu.json", "w"), indent=1, ensure_ascii=False, default=str)
    ok_file = OUT / "CPU_CHECK_OK"
    if FAIL:
        ok_file.unlink(missing_ok=True)
        print("FAIL:", FAIL)
        sys.exit(1)
    ok_file.write_text(time.strftime("%F %T") + "\n")
    print("ALL PASS")


if __name__ == "__main__":
    os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
    main()
