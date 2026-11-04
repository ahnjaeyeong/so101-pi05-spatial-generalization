"""e01 학습 전후 오프라인 재추론 (GPU). 로봇 · 카메라 연결 없음 — robot 클래스를 만들지 않고 정책 predict_action_chunk 만 부른다.

같은 관측 · 같은 noise · 같은 추론 코드로 체크포인트만 바꾼다. 기존 엔진을 **수정 없이 import**:
  vd_20261103_01/scripts/v02_engine.Engine  (num_inference_steps 5, RTC guided EXP, max_guidance_weight 10, execution_horizon 20,
                                             noise = torch.randn((64,50,32), seed 2026)[:N] — q02 · vd 와 같은 bank; q02 는 앞 32 개, vd · demo 는 앞 16 개)
  v_common.CKPT 만 이 프로세스 안에서 --ckpt 로 바꾼다 (파일 수정 없음).
상태 묶음 (모두 기존 표에서 읽기만):
  q02  : offline_pan_reversal_filter_off q02_seed_resample.select() 223 상태 (A0 · B1 전체 chunk + 18 판 S1–S7) — R1 지표 (T1–T6)
         U = prefix 없음 (모델 Raw), G = 기록 prefix · inference_delay (실물 경로) [재구성]
  vd_b : vd_20261103_01 tables/b_states.csv 168 상태 (실물 첫 파지 28 판, A_base = 원본 영상만) — R2 · 정상 파지 지표, G · U
  vd_h : vd_20261103_01 tables/h_states.csv 96 상태 (d2 사람 32 편 H_init · H_reach · H_preclose, prefix 없음) [in-sample]
  demo : 새 R1/R2 세션 dataset 프레임 (원본 읽기만). 승인 16 편 [in-sample: 새 체크포인트 학습에 씀] +
         제외 5 편 (R1 ep0–3 녹화 안 지나침 뒤 복구, RC ep11) [학습 미사용 — 같은 세션 · 작업자라 진짜 held-out 아님]
출력: eval/raw/<tag>/{q02,vd_b,vd_h,demo}.npz (키별 (N,50,6) float32), eval/raw/<tag>/meta.json (ckpt sha256, 시간, 재현 차)
재현 확인 (--ckpt 가 d2 020000 일 때): q02_seed_pan.npz (pan, 앞 N seed) · vd b_raw · h_raw (A_base, 16 seed) 와 차 기록.
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 10 ~/so101-env/bin/python scripts/e01_reinfer.py --ckpt <.../pretrained_model> --tag <이름> [--n_q02 32] [--n_vd 16] [--sets q02,vd_b,vd_h,demo] [--limit K]
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HOME = Path.home()
K8 = HOME / "so101_runs/main_k8"
D2 = K8 / "d2"
RF = D2 / "recovery_ft"
VD = D2 / "visual_dependency/vd_20261103_01"
OPR = D2 / "pan_inference_diagnostic/offline_pan_reversal_filter_off"
D2CK = D2 / "train/32_20000/pi05_expert_bs32_20k/checkpoints/020000/pretrained_model"
for p in (VD / "scripts", OPR / "scripts"):
    sys.path.insert(0, str(p))


def sha(p, bs=1 << 24):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while b := f.read(bs):
            h.update(b)
    return h.hexdigest()


def demo_states():
    """새 세션 dataset 의 재추론 상태 (프레임 · 역할). 기준 = 사람 action chunk (같은 프레임부터 50 개)."""
    import v_common  # noqa: F401  (sys.path 에 diag_grasp_bias 등 추가)
    import common as GB
    M = pd.read_csv(RF / "manifest/training_manifest.csv")
    rows = []
    for r in M[M.group != "d2"].itertuples():
        data = GB.load_parquet(Path(r.source_root))
        s, a = data[int(r.source_episode)]
        L = len(s)
        d = np.abs(a - a[0])
        pan_on = int(np.argmax(d[:, 0] > 2)) if (d[:, 0] > 2).any() else 0
        g_on = int(np.argmax(d[:, 5] > 5)) if (d[:, 5] > 5).any() else 0  # 사람 그리퍼 명령이 처음 5 이상 바뀜 (닫힘 시작 = 열기, 열림 시작 = 닫기)
        if r.group == "R1" and r.approved:
            frames = [("start", 0), ("pre_pan", max(0, pan_on - 10)), ("pan_mid", pan_on + 15)]
        elif r.group == "R1":
            # 녹화 안에서 지나침을 만든 편: 첫 4 s 안 pan 극값 (지나침 끝) 과 그 뒤
            k = int(np.argmax(np.abs(s[:120, 0] - s[0, 0])))
            frames = [("over_peak", k), ("over_peak+0.33", k + 10), ("over_peak+0.67", k + 20)]
        elif r.start_gripper == "closed":
            frames = [("start", 0), ("pre_open", max(0, g_on - 15))]
        else:
            frames = [("start", 0), ("pre_close", max(0, g_on - 30))]
        for role, f in frames:
            if f + 50 > L:
                continue
            rows.append(dict(key=f"{r.group}e{r.source_episode}_{role}", group=r.group, scenario=r.scenario, approved=bool(r.approved),
                             src_root=r.source_root, src_ep=int(r.source_episode), merged_ep=int(r.merged_episode), frame=int(f), role=role,
                             **{f"s_{j}": float(s[f, k]) for k, j in enumerate(["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"])},
                             ref=a[f:f + 50].astype(np.float32)))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--n_q02", type=int, default=32)
    ap.add_argument("--n_vd", type=int, default=16)
    ap.add_argument("--sets", default="q02,vd_b,vd_h,demo")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    ck = Path(a.ckpt).resolve()
    out = RF / "eval/raw" / a.tag
    if out.exists() and any(out.iterdir()):
        sys.exit(f"{out} 이미 있음 — 덮어쓰지 않음")
    out.mkdir(parents=True, exist_ok=True)
    import v_common as V
    V.CKPT = ck  # 이 프로세스 안에서만
    import v02_engine as EN
    t0 = time.time()
    meta = dict(tag=a.tag, ckpt=str(ck), model_sha256=sha(ck / "model.safetensors"), n_noise_q02=a.n_q02, n_noise_vd_demo=a.n_vd, start=time.strftime("%F %T"), sets={}, repro={})
    E = EN.Engine(max(a.n_q02, a.n_vd))
    bank_full = E.bank
    is_base = ck == D2CK.resolve()
    sets = a.sets.split(",")
    if "q02" in sets:
        import q02_seed_resample as Q2
        E.bank, E.N = bank_full[:a.n_q02], a.n_q02
        S = Q2.select()
        if a.limit:
            S = S.head(a.limit)
        store, rep = {}, []
        for _, r in S.iterrows():
            m, z, img, off = EN.load_chunk(r.run, int(r.chunk_id))
            st = m["obs_state"]
            key = f"{r.tag}_c{int(r.chunk_id):05d}"
            U = E.run(st, [(img["front"], img["wrist"])])[0]
            if "prefix" in z.files:
                G = E.run(st, [(img["front"], img["wrist"])], prefix=z["prefix"], delay=m.get("inference_delay"))[0]
            else:
                G = U
            store[f"U_{key}"], store[f"G_{key}"] = U, G
        np.savez_compressed(out / "q02.npz", **store)
        S.to_csv(out / "q02_states.csv", index=False)
        meta["sets"]["q02"] = dict(n_states=len(S), sec=time.time() - t0)
        if is_base:
            Z = np.load(OPR / "tables/q02_seed_pan.npz")
            d = [float(np.abs(store[k][:, :, 0] - Z[k][:a.n_q02]).max()) for k in store if k in Z.files]
            meta["repro"]["q02_pan_vs_q02_seed_pan_first_n"] = dict(n_keys=len(d), max_abs=max(d) if d else None)
        print("q02 done", len(S), f"{time.time() - t0:.0f}s", flush=True)
    E.bank, E.N = bank_full[:a.n_vd], a.n_vd
    if "vd_b" in sets:
        S = pd.read_csv(VD / "tables/b_states.csv")
        if a.limit:
            S = S.head(a.limit)
        store = {}
        for r in S.itertuples():
            m, z, img, off = EN.load_chunk(r.run, int(r.chunk_id))
            st = m["obs_state"]
            G = E.run(st, [(img["front"], img["wrist"])], prefix=z["prefix"] if "prefix" in z.files else None,
                      delay=m.get("inference_delay") if "prefix" in z.files else None)[0]
            U = E.run(st, [(img["front"], img["wrist"])])[0] if "prefix" in z.files else G
            store[f"G_{r.key}"], store[f"U_{r.key}"] = G, U
            store[f"S_{r.key}"] = np.array(st, np.float32)
        np.savez_compressed(out / "vd_b.npz", **store)
        meta["sets"]["vd_b"] = dict(n_states=len(S), sec=time.time() - t0)
        if is_base:
            d = []
            for r in S.itertuples():
                Z = np.load(VD / "tables/b_raw" / f"{r.key}.npz")
                for src in ("G", "U"):
                    n = min(a.n_vd, len(Z[f"{src}_A_base"]))
                    d.append(float(np.abs(store[f"{src}_{r.key}"][:n] - Z[f"{src}_A_base"][:n]).max()))
            meta["repro"]["vd_b_vs_b_raw_A_base"] = dict(n=len(d), max_abs=max(d))
        print("vd_b done", len(S), f"{time.time() - t0:.0f}s", flush=True)
    if "vd_h" in sets:
        import common as GB
        S = pd.read_csv(VD / "tables/h_states.csv")
        if a.limit:
            S = S.head(a.limit)
        store, cache = {}, {}
        for r in S.itertuples():
            f = GB.frames(V.D2 / "dataset", r.ep, "front", r.frame, r.frame, cache)[0]
            w = GB.frames(V.D2 / "dataset", r.ep, "wrist", r.frame, r.frame, cache)[0]
            st = [getattr(r, f"s_{j}") for j in V.J]
            store[f"G_{r.key}"] = E.run(st, [(f, w)])[0]
            store[f"S_{r.key}"] = np.array(st, np.float32)
        np.savez_compressed(out / "vd_h.npz", **store)
        meta["sets"]["vd_h"] = dict(n_states=len(S), sec=time.time() - t0)
        if is_base:
            d = []
            for r in S.itertuples():
                Z = np.load(VD / "tables/h_raw" / f"{r.key}.npz")
                n = min(a.n_vd, len(Z["G_A_base"]))
                d.append(float(np.abs(store[f"G_{r.key}"][:n] - Z["G_A_base"][:n]).max()))
            meta["repro"]["vd_h_vs_h_raw_A_base"] = dict(n=len(d), max_abs=max(d))
        print("vd_h done", len(S), f"{time.time() - t0:.0f}s", flush=True)
    if "demo" in sets:
        import common as GB
        rows = demo_states()
        if a.limit:
            rows = rows[:a.limit]
        store, cache = {}, {}
        for r in rows:
            f = GB.frames(r["src_root"], r["src_ep"], "front", r["frame"], r["frame"], cache)[0]
            w = GB.frames(r["src_root"], r["src_ep"], "wrist", r["frame"], r["frame"], cache)[0]
            st = [r[f"s_{j}"] for j in V.J]
            store[f"G_{r['key']}"] = E.run(st, [(f, w)])[0]
            store[f"S_{r['key']}"] = np.array(st, np.float32)
            store[f"REF_{r['key']}"] = r["ref"]
        np.savez_compressed(out / "demo.npz", **store)
        pd.DataFrame([{k: v for k, v in r.items() if k != "ref"} for r in rows]).to_csv(out / "demo_states.csv", index=False)
        meta["sets"]["demo"] = dict(n_states=len(rows), sec=time.time() - t0)
        print("demo done", len(rows), f"{time.time() - t0:.0f}s", flush=True)
    meta["end"] = time.strftime("%F %T")
    meta["total_sec"] = time.time() - t0
    (out / "meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    print(json.dumps(meta["repro"], ensure_ascii=False), flush=True)
    print("E01_DONE", a.tag, f"{time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
