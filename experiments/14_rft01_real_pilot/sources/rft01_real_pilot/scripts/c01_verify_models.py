"""c01 — Baseline (d2 020000) 과 Fine-tuned (rft01 001000) 체크포인트 · normalizer · 추론 설정 · Action 범위 검증 (읽기 전용, CPU).

로봇 · 카메라 · GPU 를 쓰지 않는다. 체크포인트 폴더에는 쓰지 않는다 (읽기만).
출력: logs/c01_verify_models.json · logs/c01_verify_models.md (덮어쓰지 않음: 있으면 _<시각> 붙임)

검사:
  M1 model.safetensors SHA-256 재계산 = recovery_ft/logs/post/p01_ckpt_sha256.json 기록값
  M2 000500 체크포인트 존재 + SHA-256 (보존 확인, 이번 파일럿에서 실행하지 않음)
  M3 config.json 차이 (학습 설정 키 외 차이 0 이어야 함)
  M4 policy_preprocessor.json · policy_postprocessor.json byte 동일
  M5 normalizer / unnormalizer safetensors 의 모든 텐서 값 동일 (np.array_equal)
  M6 tokenizer.json byte 동일, tokenizer_config.json 차이 목록, 같은 과제 문장 토큰화 결과 동일 (eval 과 같은 호출 인자)
  M7 Action 범위: recovery_ft 오프라인 재추론 배열 (같은 상태 · 같은 noise) 에서 관절별 예측 범위 · chunk 안 step 간 최대 변화 비교 [재추론]
"""
import datetime
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HOME = Path.home()
K8 = HOME / "so101_runs/main_k8"
BASE = K8 / "d2/train/32_20000/pi05_expert_bs32_20k/checkpoints/020000/pretrained_model"
RFT = K8 / "d2/recovery_ft/runs/rft01_d2rc16_W5_1k_s2001/checkpoints"
FT = RFT / "001000/pretrained_model"
FT500 = RFT / "000500/pretrained_model"
SHA_REC = K8 / "d2/recovery_ft/logs/post/p01_ckpt_sha256.json"
RAW = K8 / "d2/recovery_ft/eval/raw"
STATS = K8 / "d2/dataset/meta/stats.json"
OUT = Path(__file__).resolve().parents[1] / "logs"
TASK = "pick up the red cube and put it in the brown box"
J = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
TRAIN_KEYS = {"pretrained_path", "optimizer_lr", "scheduler_warmup_steps", "scheduler_decay_steps", "scheduler_decay_lr"}


def sha256(p, bs=1 << 24):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while True:
            b = f.read(bs)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def flat(d, pre=""):
    out = {}
    for k, v in d.items():
        kk = f"{pre}{k}"
        if isinstance(v, dict):
            out.update(flat(v, kk + "."))
        else:
            out[kk] = v
    return out


def main():
    R, ok = {}, True

    def chk(name, cond, detail):
        nonlocal ok
        ok = ok and bool(cond)
        R[name] = {"pass": bool(cond), "detail": detail}
        print(f"{'PASS' if cond else 'FAIL'} {name} {json.dumps(detail, ensure_ascii=False, default=str)[:400]}", flush=True)

    rec = json.loads(SHA_REC.read_text())
    sb, sf = sha256(BASE / "model.safetensors"), sha256(FT / "model.safetensors")
    chk("M1_sha256", sb == rec["d2_020000"] and sf == rec["001000"] and sf.startswith("620c4598") and sf.endswith("db712af9"),
        {"baseline_020000": sb, "rft01_001000": sf, "recorded": {k: rec[k] for k in ("d2_020000", "001000")}})
    s5 = sha256(FT500 / "model.safetensors") if (FT500 / "model.safetensors").exists() else None
    chk("M2_000500_preserved", s5 == rec["000500"], {"path": str(FT500), "sha256": s5})

    cb, cf = flat(json.loads((BASE / "config.json").read_text())), flat(json.loads((FT / "config.json").read_text()))
    diff = {k: (cb.get(k), cf.get(k)) for k in sorted(set(cb) | set(cf)) if cb.get(k) != cf.get(k)}
    non_train = {k: v for k, v in diff.items() if k.split(".")[-1] not in TRAIN_KEYS}
    infer_keys = ["chunk_size", "n_action_steps", "num_inference_steps", "normalization_mapping.ACTION", "normalization_mapping.STATE",
                  "max_state_dim", "max_action_dim", "tokenizer_max_length", "dtype", "rtc_config", "input_features.observation.state.shape",
                  "output_features.action.shape", "image_resolution"]
    chk("M3_config_diff_train_keys_only", not non_train,
        {"diff": diff, "non_training_diff": non_train, "inference_keys_both": {k: cb.get(k) for k in infer_keys if k in cb}})

    same_json = {f: (BASE / f).read_bytes() == (FT / f).read_bytes() for f in ("policy_preprocessor.json", "policy_postprocessor.json")}
    chk("M4_processor_json_identical", all(same_json.values()), same_json)

    from safetensors.numpy import load_file
    tens = {}
    for f in ("policy_preprocessor_step_3_normalizer_processor.safetensors", "policy_postprocessor_step_0_unnormalizer_processor.safetensors"):
        a, b = load_file(str(BASE / f)), load_file(str(FT / f))
        neq = [k for k in sorted(set(a) | set(b)) if k not in a or k not in b or not np.array_equal(a[k], b[k])]
        tens[f] = {"n_tensors": len(a), "not_equal": neq,
                   "action_q01": a.get("action.q01", np.array([])).round(2).tolist(), "action_q99": a.get("action.q99", np.array([])).round(2).tolist()}
    chk("M5_normalizer_values_identical", all(not v["not_equal"] for v in tens.values()), tens)

    tok_same = (BASE / "tokenizer/tokenizer.json").read_bytes() == (FT / "tokenizer/tokenizer.json").read_bytes()
    tcb, tcf = json.loads((BASE / "tokenizer/tokenizer_config.json").read_text()), json.loads((FT / "tokenizer/tokenizer_config.json").read_text())
    tdiff = {k: (tcb.get(k), tcf.get(k)) for k in sorted(set(tcb) | set(tcf)) if tcb.get(k) != tcf.get(k)}
    from transformers import AutoTokenizer
    pp = json.loads((BASE / "policy_preprocessor.json").read_text())
    tcfg = [s for s in pp["steps"] if s["registry_name"] == "tokenizer_processor"][0]["config"]
    kw = dict(max_length=tcfg["max_length"], padding=tcfg["padding"], truncation=tcfg["truncation"], padding_side=tcfg["padding_side"], return_tensors="np")
    # pi05 프롬프트 형식 (state 토큰 포함) 은 pi05_prepare_state_tokenizer 가 만든다 — 여기서는 과제 문장 + 같은 형식 예시 문자열 두 개를 비교
    texts = [TASK, f"Task: {TASK}, State: 128 64 200 12 99 3;\nAction: "]
    ids = {}
    for name, p in (("base", BASE), ("ft", FT)):
        t = AutoTokenizer.from_pretrained(str(p / "tokenizer"))
        ids[name] = [t(x, **kw) for x in texts]
    tok_eq = all(np.array_equal(ids["base"][i]["input_ids"], ids["ft"][i]["input_ids"]) and
                 np.array_equal(ids["base"][i]["attention_mask"], ids["ft"][i]["attention_mask"]) for i in range(len(texts)))
    chk("M6_tokenizer_same_output", tok_same and tok_eq,
        {"tokenizer.json_identical": tok_same, "tokenizer_config_diff": tdiff, "call_kwargs": {k: v for k, v in kw.items() if k != "return_tensors"},
         "n_tokens_task": int(ids["base"][0]["attention_mask"].sum()), "ids_equal_all_texts": tok_eq})

    # M7 Action 범위 [재추론]: 같은 상태 · 같은 noise 의 예측 chunk (°, 정규화 해제 뒤)
    st = json.loads(STATS.read_text())["action"]
    rows = {}
    for tag in ("d2_020000", "rft01_001000"):
        acc = {"G": [], "U": []}
        for setn in ("q02", "vd_b", "vd_h"):
            z = np.load(RAW / tag / f"{setn}.npz")
            for k in z.files:
                if k[:2] in ("G_", "U_"):
                    acc[k[0]].append(z[k].reshape(-1, 50, 6))
        rows[tag] = {}
        for g, lst in acc.items():
            A = np.concatenate(lst, 0)
            d = np.abs(np.diff(A, axis=1))
            rows[tag][g] = {"n_chunks": int(A.shape[0]), "min": A.min((0, 1)).round(2).tolist(), "max": A.max((0, 1)).round(2).tolist(),
                            "p01": np.percentile(A, 1, (0, 1)).round(2).tolist(), "p99": np.percentile(A, 99, (0, 1)).round(2).tolist(),
                            "step_delta_p99": np.percentile(d, 99, (0, 1)).round(3).tolist(), "step_delta_max": d.max((0, 1)).round(3).tolist(),
                            "pan_abs_gt_104_frac": float((np.abs(A[..., 0]) > 104).mean())}
    cmp = {}
    for g in ("G", "U"):
        b, f = rows["d2_020000"][g], rows["rft01_001000"][g]
        cmp[g] = {"n_chunks_equal": b["n_chunks"] == f["n_chunks"],
                  "max_minus_base": (np.array(f["max"]) - np.array(b["max"])).round(2).tolist(),
                  "min_minus_base": (np.array(f["min"]) - np.array(b["min"])).round(2).tolist(),
                  "step_delta_max_ratio": (np.array(f["step_delta_max"]) / np.maximum(np.array(b["step_delta_max"]), 1e-6)).round(2).tolist()}
    # 규칙 (v2, 11-05): 020000 자체가 A0/B1 상태에서 학습 범위 밖 pan (−132°) 을 예측하므로 학습 범위가 아니라 020000 과 비교한다.
    #   rft01 의 관절별 min/max 가 020000 의 min−5° … max+5° 안 · chunk 안 step 간 최대 변화가 020000 의 1.25 배 이하 · |pan|>104 비율이 020000 + 1 %p 이하
    within = all(rows["rft01_001000"][g]["min"][i] >= rows["d2_020000"][g]["min"][i] - 5 and
                 rows["rft01_001000"][g]["max"][i] <= rows["d2_020000"][g]["max"][i] + 5 and
                 cmp[g]["step_delta_max_ratio"][i] <= 1.25 for g in ("G", "U") for i in range(6))
    pan_ok = all(rows["rft01_001000"][g]["pan_abs_gt_104_frac"] <= rows["d2_020000"][g]["pan_abs_gt_104_frac"] + 0.01 for g in ("G", "U"))
    chk("M7_action_range_reinfer", within and pan_ok and all(c["n_chunks_equal"] for c in cmp.values()),
        {"train_action_min": [round(x, 1) for x in st["min"]], "train_action_max": [round(x, 1) for x in st["max"]],
         "rule": "rft01 min/max ⊂ 020000 min−5 … max+5 · step 변화 최대 ≤ 1.25× · |pan|>104 비율 ≤ 020000+1%p (같은 상태 · 같은 noise)",
         "per_model": rows, "compare": cmp})

    OUT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    jp = OUT / "c01_verify_models.json"
    if jp.exists():
        jp = OUT / f"c01_verify_models_{stamp}.json"
    meta = {"time": stamp, "baseline": str(BASE), "finetuned": str(FT), "all_pass": ok, "joints": J}
    jp.write_text(json.dumps({"meta": meta, "checks": R}, indent=1, ensure_ascii=False, default=str))
    print(("ALL_PASS" if ok else "SOME_FAIL"), jp, flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
