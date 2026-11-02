"""분석 3 (CPU): wrist_roll state 가 Action Expert 에 닿는 경로를 실제 전처리기로 확인한다.
모델 가중치는 읽지 않는다 (preprocessor + tokenizer 만). 로봇·카메라 연결 없음. 학습 코드·데이터 변경 없음.

확인 항목
  P1  정규화: d2 020000 preprocessor 의 state q01/q99 로 [-1,1] 변환 — 학습 데이터 · 평가 롤아웃 범위 밖 비율 (잘라내기 없음)
  P2  이산화: 256 구간, roll 1 구간 = (q99-q01)/256 도. 범위 밖이면 '-1' / '255'
  P3  토큰화: 실제 프롬프트 문자열 → PaliGemma tokenizer 토큰. 숫자 자릿수 분해, roll 토큰 위치, 길이 변화, 잘림(200) 여부
  P4  주의 마스크: prefix(영상+문장) 는 서로 양방향, suffix(행동) 는 prefix 전체를 본다 — make_att_2d_masks 로 장난감 입력 확인
  P5  학습 ↔ 추론 같은 전처리기 (train_config 의 normalization · tokenizer 설정 = 저장된 preprocessor)
출력: c3_state_path.json, 화면 요약.
사용: PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python c3_state_path.py
"""
import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch

HOME = Path.home()
D2 = HOME / "so101_runs/main_k8/d2"
CK = D2 / "train/32_20000/pi05_expert_bs32_20k/checkpoints/020000/pretrained_model"
OUT = D2 / "action_bottleneck"
JOINTS = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
TASK = "pick up the red cube and put it in the brown box"


def load_states(ds):
    files = sorted(glob.glob(str(Path(ds) / "data/*/*.parquet")))
    df = pd.concat([pd.read_parquet(f, columns=["episode_index", "frame_index", "observation.state"]) for f in files])
    return np.stack(df["observation.state"].values).astype(np.float32), df["episode_index"].values


def main():
    from lerobot.policies.factory import make_pre_post_processors
    from lerobot.policies.pi05.configuration_pi05 import PI05Config
    from lerobot.policies.pi05.modeling_pi05 import make_att_2d_masks

    cfg = PI05Config.from_pretrained(str(CK))
    pre, _ = make_pre_post_processors(cfg, pretrained_path=str(CK), preprocessor_overrides={"device_processor": {"device": "cpu"}})
    norm = [s for s in pre.steps if type(s).__name__ == "NormalizerProcessorStep"][0]
    st = norm._tensor_stats["observation.state"]  # noqa: SLF001
    q01, q99 = st["q01"].numpy(), st["q99"].numpy()
    res = {"q01": q01.tolist(), "q99": q99.tolist(), "bin_deg": ((q99 - q01) / 256).tolist()}

    # P1/P2 학습 · 평가 state 범위
    S_tr, _ = load_states(D2 / "dataset")
    evs = {}
    for d in sorted(glob.glob(str(D2 / "eval/rollouts/*/dataset"))):
        evs[Path(d).parent.name] = load_states(d)[0]
    def stats(S):
        z = 2 * (S - q01) / (q99 - q01) - 1
        b = np.digitize(z, bins=np.linspace(-1, 1, 257)[:-1]) - 1
        return dict(n=len(S), frac_below=(z < -1).mean(0).round(4).tolist(), frac_above=(z > 1).mean(0).round(4).tolist(),
                    roll_min=float(S[:, 4].min()), roll_max=float(S[:, 4].max()),
                    roll_bins_used=int(len(np.unique(b[:, 4]))), tok_minus1=int((b == -1).sum()))
    res["train"] = stats(S_tr)
    res["eval"] = {k: stats(v) for k, v in evs.items()}

    # P3 실제 프롬프트 → 토큰. 대표 state 몇 개 + roll 만 바꾼 것
    tok = [s for s in pre.steps if type(s).__name__ == "TokenizerProcessorStep"][0]
    tk = tok.input_tokenizer if hasattr(tok, "input_tokenizer") else tok.tokenizer
    examples = []
    base = np.median(S_tr, 0).astype(np.float32)
    for roll in (-57.0, -30.0, -10.0, 0.0, 0.3, 10.0, 30.0, 55.0, -70.0):
        s = base.copy()
        s[4] = roll
        batch = {"observation.state": torch.from_numpy(s[None]), "task": [TASK],
                 "observation.images.front": torch.zeros(1, 3, 480, 640), "observation.images.wrist": torch.zeros(1, 3, 480, 640)}
        b = pre(batch)
        ids = b["observation.language.tokens"][0]
        m = b["observation.language.attention_mask"][0].bool()
        pieces = tk.convert_ids_to_tokens(ids[m].tolist())
        text = tk.decode(ids[m].tolist())
        st_part = text.split("State: ")[1].split(";")[0]
        # roll 숫자(5번째)의 토큰 위치 (문장 안 위치, prefix 안 위치 = 512 + 문장 위치)
        i0 = pieces.index("State") if "State" in pieces else [i for i, p in enumerate(pieces) if "State" in p][0]
        examples.append(dict(roll_deg=roll, state_str=st_part, n_lang_tokens=int(m.sum()),
                             state_tokens=pieces[i0:i0 + 40][:40]))
    res["token_examples"] = examples
    # 숫자 토큰이 한 자리씩인지: 0–255 각각 토큰 수
    nd = [len(tk(" " + str(k), add_special_tokens=False)["input_ids"]) for k in range(-1, 256)]
    res["tokens_per_number"] = {str(k): n for k, n in zip(range(-1, 256), nd)}
    res["tokens_per_number_hist"] = {str(v): int(c) for v, c in zip(*np.unique(nd, return_counts=True))}

    # 학습 프레임 전체의 문장 토큰 길이 분포 (state 자릿수에 따라 위치가 움직이는지)
    z = 2 * (S_tr - q01) / (q99 - q01) - 1
    bins = np.digitize(z, bins=np.linspace(-1, 1, 257)[:-1]) - 1
    lens_digits = np.vectorize(lambda k: len(str(k)))(bins)
    pre_roll_chars = lens_digits[:, :4].sum(1)  # roll 앞 숫자들의 글자 수 → roll 토큰 위치 변동
    res["train_roll_pos_offset_digits"] = {str(v): int(c) for v, c in zip(*np.unique(pre_roll_chars, return_counts=True))}
    res["train_roll_ndigits"] = {str(v): int(c) for v, c in zip(*np.unique(lens_digits[:, 4], return_counts=True))}

    # P4 주의 마스크 (prefix 3 토큰 + suffix 2 토큰 장난감)
    pad = torch.ones(1, 5, dtype=torch.bool)
    att = torch.tensor([[0, 0, 0, 1, 0]], dtype=torch.bool)
    M = make_att_2d_masks(pad, att)[0].int().tolist()
    res["att2d_toy(prefix3_suffix2)"] = M

    # P5 train_config 와 저장 preprocessor 일치
    tc = json.load(open(CK / "train_config.json"))
    pc = tc["policy"]
    res["train_config_policy"] = {k: pc.get(k) for k in ("normalization_mapping", "tokenizer_max_length", "max_state_dim",
                                                          "use_proprioceptive_memory", "train_expert_only", "freeze_vision_encoder",
                                                          "n_obs_steps", "use_relative_actions")}
    res["saved_pre_steps"] = [type(s).__name__ for s in pre.steps]
    json.dump(res, open(OUT / "c3_state_path.json", "w"), indent=1, ensure_ascii=False)

    print("roll q01/q99", q01[4], q99[4], "bin_deg", round(res["bin_deg"][4], 3))
    print("train", {k: res["train"][k] for k in ("frac_below", "frac_above", "roll_bins_used", "tok_minus1")})
    for k, v in res["eval"].items():
        print("eval", k, v)
    for ex in examples:
        print(ex["roll_deg"], "|", ex["state_str"], "| n_lang", ex["n_lang_tokens"], "|", " ".join(ex["state_tokens"][:30]))
    print("tokens per number hist", res["tokens_per_number_hist"])
    print("roll ndigits", res["train_roll_ndigits"], "pre-roll chars", res["train_roll_pos_offset_digits"])
    print("att toy", M)
    print(res["train_config_policy"])
    print(res["saved_pre_steps"])


if __name__ == "__main__":
    sys.exit(main())
