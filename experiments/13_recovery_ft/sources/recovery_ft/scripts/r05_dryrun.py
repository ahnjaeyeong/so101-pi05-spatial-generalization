"""r05 사전 dry-run (작업 지시 6 절). 로봇 연결 없음. 정식 학습 step 에 합산하지 않으며 체크포인트를 저장하지 않는다.

모드
  sampler (CPU): 정식 run 과 같은 인자로 dataset (episodes=manifest 272) 을 열고, lerobot_train 과 같은 인자로 가중 sampler 를 만든 뒤
                 epoch 0 순서의 앞 steps×batch (= 32,000) 표본을 계산 → 묶음 (d2/R1/R2) · 시나리오 · 편별 노출, 제외 편 0 확인.
                 결과는 tables/r05_expected_sampled_abs_idx.npy (학습 뒤 실제 기록과 비교) · tables/r05_sampler_exposure.csv.
  grad (GPU)   : 정식 run 인자 파일 그대로 (output_dir · job_name · steps=1 · save_checkpoint=false 만 바꿈) train_recovery.main() →
                 lerobot_train.train() 진입. update_policy 를 바꿔 끼워 첫 호출에서:
                   1) 실제 sampler batch 의 key · shape · dtype (front/wrist 영상, state, action, task token)
                   2) 유형별 batch (R1 · RC-F1 · RC-F2 · RC-F3 각 8 개, 같은 preprocessor) 로 forward(reduction='none') → 유형별 loss 유한성
                   3) 실제 batch 로 forward + backward → 모듈별 requires_grad · grad 존재 (freeze 대상에 grad 가 없어야 함)
                   4) optimizer.step 하지 않고 zero_grad 후 DryRunStop 으로 끝냄 (가중치 · 체크포인트 변화 없음)
                 GPU 최대 메모리 (torch.cuda.max_memory_allocated) 기록.
출력: tables/r05_*.csv|json, logs/r05_*.log
"""
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HOME = Path.home()
RF = HOME / "so101_runs/main_k8/d2/recovery_ft"
RUN_ID = "rft01_d2rc16_W5_1k_s2001"
sys.path.insert(0, str(RF / "scripts"))


def run_args():
    return (RF / f"runs/{RUN_ID}.args").read_text().split("\n")[:-1]


def argval(name, argv):
    for a in argv:
        if a.startswith(f"--{name}="):
            return a.split("=", 1)[1]


def mode_sampler():
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    import train_recovery as TR
    from lerobot.datasets.lerobot_dataset import LeRobotDataset
    from lerobot.datasets.sampler import EpisodeAwareSampler
    argv = run_args()
    eps = TR.parse_list(argval("dataset.episodes", argv))
    seed, steps, bs = int(argval("seed", argv)), int(argval("steps", argv)), int(argval("batch_size", argv))
    w = np.load(RF / "weights/weights_rc16_W5.npy")
    ds = LeRobotDataset(argval("dataset.repo_id", argv), root=argval("dataset.root", argv), episodes=eps)
    Cls = TR.TW.make_weighted_sampler_class(EpisodeAwareSampler, w)
    s = Cls(ds.meta.episodes["dataset_from_index"], ds.meta.episodes["dataset_to_index"], episode_indices_to_use=ds.episodes,
            drop_n_first_frames=0, drop_n_last_frames=0, shuffle=True, seed=seed, absolute_to_relative_idx=ds.absolute_to_relative_idx)
    import torch
    order = torch.randperm(s._num_frames, generator=s._epoch_generator(0)).numpy()
    n = steps * bs
    absidx = s._expanded[order[:n]]
    # 같은 위치에 대해 sampler 가 돌려주는 상대 index 가 dataset 의 그 프레임인지 표본 확인
    it = s._iter_epoch(0, 0)
    first = [next(it) for _ in range(256)]
    rel_ok = all(int(ds.hf_dataset[int(r)]["index"]) == int(a) for r, a in zip(first, absidx[:256]))
    np.save(RF / "tables/r05_expected_sampled_abs_idx.npy", absidx.astype(np.int64))
    M = pd.read_csv(RF / "manifest/training_manifest.csv")
    E = ds.meta.episodes
    ep_of = np.empty(int(json.load(open(RF / "dataset/meta/info.json"))["total_frames"]), dtype=np.int64)
    for i in range(len(E["episode_index"])):
        ep_of[E["dataset_from_index"][i]:E["dataset_to_index"][i]] = E["episode_index"][i]
    sep = ep_of[absidx]
    Mi = M.set_index("merged_episode")
    cnt = pd.Series(sep).value_counts()
    rows = []
    for e, r in Mi.iterrows():
        c = int(cnt.get(e, 0))
        if r.group == "d2" and r.approved:
            continue
        lo, hi = int(E["dataset_from_index"][e]), int(E["dataset_to_index"][e])
        touched = len(np.unique(absidx[(absidx >= lo) & (absidx < hi)]))
        rows.append(dict(merged_episode=e, group=r.group, source_episode=r.source_episode, scenario=r.scenario, approved=r.approved, length=r.length,
                         samples=c, exposure_per_frame=c / r.length, frames_touched_frac=touched / r.length, tags=r.tags))
    X = pd.DataFrame(rows)
    X.to_csv(RF / "tables/r05_sampler_exposure.csv", index=False)
    grp = pd.Series(Mi.group.reindex(sep).values).value_counts()
    d2_eps_seen = int(np.sum(Mi.group.reindex(cnt.index).values == "d2"))
    summ = dict(n_samples=n, by_group={k: int(v) for k, v in grp.items()}, share={k: float(v / n) for k, v in grp.items()},
                by_scenario={k: int(v) for k, v in X[X.approved].groupby("scenario").samples.sum().items()},
                excluded_samples=int(X[~X.approved].samples.sum()), d2_episodes_seen=d2_eps_seen,
                corr_frames_touched_frac=float((X[X.approved].frames_touched_frac * X[X.approved].length).sum() / X[X.approved].length.sum()),
                sampler_num_positions=int(s._num_frames), relative_index_maps_to_same_frame_first256=bool(rel_ok),
                all_272_in_expanded=bool(set(np.unique(ep_of[s._expanded])) == set(eps)))
    (RF / "tables/r05_sampler_summary.json").write_text(json.dumps(summ, indent=1, ensure_ascii=False))
    print(json.dumps(summ, indent=1, ensure_ascii=False))
    print(X.to_string())
    ok = summ["excluded_samples"] == 0 and rel_ok and summ["all_272_in_expanded"] and all(summ["by_scenario"].get(k, 0) > 0 for k in ("R1-FOLD-OVER", "RC-F1", "RC-F2", "RC-F3-L", "RC-F3-R"))
    print("SAMPLER_OK" if ok else "SAMPLER_FAIL")
    sys.exit(0 if ok else 1)


class DryRunStop(Exception):
    pass


def mode_grad():
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    import torch
    import lerobot.scripts.lerobot_train as LT
    import train_recovery as TR
    from torch.utils.data import default_collate
    ts = time.strftime("%Y%m%d_%H%M%S")
    name = f"_dryrun_grad_{ts}"
    argv = [a for a in run_args() if not a.startswith(("--output_dir=", "--job_name=", "--steps=", "--log_freq="))]
    argv += [f"--output_dir={RF / 'runs' / name}", f"--job_name={name}", "--steps=1", "--log_freq=1", "--save_checkpoint=false"]
    os.environ["RF_WEIGHTS"] = str(RF / "weights/weights_rc16_W5.npy")
    os.environ["RF_RUN_NAME"] = name
    stash = {}
    orig_ds, orig_pp = LT.make_train_eval_datasets, LT.make_pre_post_processors

    def ds_wrap(cfg):
        d, e = orig_ds(cfg)
        stash["ds"] = d
        return d, e

    def pp_wrap(*a, **k):
        pre, post = orig_pp(*a, **k)
        stash["pre"] = pre
        return pre, post

    def upd(train_metrics, policy, batch, optimizer, grad_clip_norm, accelerator, lr_scheduler=None, lock=None, sample_weighter=None):
        out = {}
        out["batch"] = {k: dict(shape=list(v.shape), dtype=str(v.dtype)) for k, v in batch.items() if torch.is_tensor(v)}
        out["batch_nontensor"] = {k: (type(v).__name__, (v[:1] if isinstance(v, list) else str(v)[:80])) for k, v in batch.items() if not torch.is_tensor(v)}
        if "index" in batch:
            M = pd.read_csv(RF / "manifest/training_manifest.csv")
            E = stash["ds"].meta.episodes
            idx = batch["index"].cpu().numpy()
            fr = np.asarray(E["dataset_from_index"])
            ep = np.searchsorted(fr, idx, side="right") - 1
            out["first_batch_groups"] = pd.Series(M.set_index("merged_episode").group.reindex(np.asarray(E["episode_index"])[ep]).values).value_counts().to_dict()
        unwrapped = accelerator.unwrap_model(policy)
        # 2) 유형별 batch
        ds, pre = stash["ds"], stash["pre"]
        M = pd.read_csv(RF / "manifest/training_manifest.csv")
        E = ds.meta.episodes
        rng = np.random.default_rng(0)
        typed = {}
        for key, sel in (("d2", M.group == "d2"), ("R1", M.scenario == "R1-FOLD-OVER"), ("RC-F1", M.scenario == "RC-F1"),
                         ("RC-F2", M.scenario == "RC-F2"), ("RC-F3", M.scenario.isin(["RC-F3-L", "RC-F3-R"]))):
            eps = M[sel & M.approved].merged_episode.to_numpy()
            items = []
            for e in rng.choice(eps, 8, replace=True):
                lo, hi = int(E["dataset_from_index"][e]), int(E["dataset_to_index"][e])
                a = int(rng.integers(lo, hi))
                items.append(ds[ds.absolute_to_relative_idx[a] if ds.absolute_to_relative_idx is not None else a])
            b = default_collate(items)
            for ck in ("observation.images.front", "observation.images.wrist"):
                if b[ck].dtype == torch.uint8:
                    b[ck] = b[ck].float() / 255.0
            b = pre(b)
            torch.manual_seed(0)
            with torch.no_grad(), accelerator.autocast():
                l, _ = policy(b, reduction="none")
            l = l.float().reshape(len(items), -1).mean(1).cpu().numpy() if l.dim() > 0 else np.array([float(l)])
            typed[key] = dict(n=len(items), loss_mean=float(l.mean()), loss_min=float(l.min()), loss_max=float(l.max()), finite=bool(np.isfinite(l).all()),
                              state_shape=list(b["observation.state"].shape), action_shape=list(b["action"].shape))
        out["typed_loss_at_d2_020000"] = typed
        # 3) 실제 batch forward + backward, grad 검사
        policy.train()
        torch.cuda.reset_peak_memory_stats()
        with accelerator.autocast():
            loss, _ = policy(batch)
        accelerator.backward(loss)
        out["loss_first_batch"] = float(loss.detach().float())
        groups = {}
        for n_, p in unwrapped.named_parameters():
            g = ".".join(n_.split(".")[:4]) if n_.startswith("model.paligemma") else ".".join(n_.split(".")[:2])
            d = groups.setdefault(g, dict(n_params=0, n_tensors=0, requires_grad=0, grad_present=0, grad_nonzero=0, frozen_with_grad=0))
            d["n_params"] += p.numel()
            d["n_tensors"] += 1
            d["requires_grad"] += int(p.requires_grad)
            has = p.grad is not None
            d["grad_present"] += int(has)
            d["grad_nonzero"] += int(has and bool(p.grad.detach().abs().sum() > 0))
            d["frozen_with_grad"] += int((not p.requires_grad) and has)
        G = pd.DataFrame(groups).T
        G.to_csv(RF / "tables/r05_grad_groups.csv")
        out["grad_groups"] = G.to_dict(orient="index")
        out["learnable_params"] = int(sum(p.numel() for p in unwrapped.parameters() if p.requires_grad))
        out["total_params"] = int(sum(p.numel() for p in unwrapped.parameters()))
        out["frozen_with_grad_total"] = int(G.frozen_with_grad.sum())
        out["trainable_without_grad_tensors"] = int((G.requires_grad - G.grad_present).sum())
        out["vision_tower_training_mode"] = bool(unwrapped.model.paligemma_with_expert.paligemma.model.vision_tower.training)
        out["paligemma_training_mode"] = bool(unwrapped.model.paligemma_with_expert.paligemma.training)
        out["config"] = dict(train_expert_only=unwrapped.config.train_expert_only, freeze_vision_encoder=unwrapped.config.freeze_vision_encoder,
                             chunk_size=unwrapped.config.chunk_size, n_action_steps=unwrapped.config.n_action_steps,
                             max_state_dim=unwrapped.config.max_state_dim, max_action_dim=unwrapped.config.max_action_dim,
                             tokenizer_max_length=unwrapped.config.tokenizer_max_length)
        out["optimizer_lr_now"] = [g["lr"] for g in optimizer.param_groups]
        out["optimizer_param_count"] = int(sum(p.numel() for g in optimizer.param_groups for p in g["params"]))
        out["gpu_max_mem_allocated_GiB_fwd_bwd"] = torch.cuda.max_memory_allocated() / 2 ** 30
        out["normalizer_stats_equal_d2_020000"] = None
        try:
            from safetensors.numpy import load_file
            ck = load_file(str(TR.TW.D2_CK / "pretrained_model/policy_preprocessor_step_3_normalizer_processor.safetensors"))
            st = [s for s in pre.steps if type(s).__name__.startswith("Normalizer")][0]
            mx = 0.0
            for f in ("observation.state", "action"):
                for k in ("q01", "q99"):
                    mx = max(mx, float(np.abs(st._tensor_stats[f][k].detach().cpu().numpy() - ck[f"{f}.{k}"]).max()))
            out["normalizer_stats_equal_d2_020000"] = mx
        except Exception as ex:  # 기록만
            out["normalizer_stats_equal_d2_020000"] = f"check error: {ex!r}"
        optimizer.zero_grad()
        (RF / "tables/r05_grad_check.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))
        print(json.dumps({k: v for k, v in out.items() if k != "grad_groups"}, indent=1, ensure_ascii=False, default=str), flush=True)
        print(G.to_string(), flush=True)
        raise DryRunStop("dry-run 끝 (optimizer.step 안 함)")

    LT.make_train_eval_datasets = ds_wrap
    LT.make_pre_post_processors = pp_wrap
    LT.update_policy = upd
    sys.argv = ["train_recovery.py"] + argv
    try:
        TR.main()
    except DryRunStop as e:
        print("GRAD_DRYRUN_DONE", e)


if __name__ == "__main__":
    {"sampler": mode_sampler, "grad": mode_grad}[sys.argv[1]]()
