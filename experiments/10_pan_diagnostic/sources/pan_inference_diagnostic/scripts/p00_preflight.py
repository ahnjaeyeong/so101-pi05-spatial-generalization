"""p00 실물 파일럿 직전 점검 (읽기만, CPU). 로봇 · 카메라 장치를 열지 않는다 (경로 존재만 본다).

점검:
  1) d2 020000 pretrained_model 파일 sha256 = sampling_ablation/ops/d2_sha256.json (10-27 기록) 과 같은가
  2) 평가 코드 sha256: rollout_logged.py (8fcd4b6b…) · diag_log.py (b1425bab…) · arm_filter.py · eval_ui.py (기록만)
  3) lerobot 설치 파일 (rtc · pi05 · rollout · so_follower · feetech · action_queue) 이 pip RECORD 의 sha256 과 같은가 (설치 뒤 수정 없음)
  4) eval_ui --check (CUDA 숨김, 하드웨어 연결 전 멈춤) 출력의 RTC · queue · filter · fps · max_relative_target · 체크포인트
  5) 학습 상태: sampling_ablation 큐 정지 (QUEUE_STOPPED), 학습 프로세스 없음, run_A2r 실행권한 없음, A2 004000 있음
  6) 실행 환경: GPU compute 프로세스, 다른 lerobot 프로세스, twin 컨테이너, 장치 경로 존재, 디스크 여유
출력: pan_inference_diagnostic/preflight/preflight_<시각>.json, 화면 요약 (OK / FAIL / INFO)
사용: PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python p00_preflight.py
"""
import base64
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

HOME = Path.home()
D2 = HOME / "so101_runs/main_k8/d2"
OUT = D2 / "pan_inference_diagnostic/preflight"
CK = D2 / "train/32_20000/pi05_expert_bs32_20k/checkpoints/020000/pretrained_model"
SA = D2 / "sampling_ablation"
EXPECT_CODE = {"rollout_logged.py": "8fcd4b6b", "diag_log.py": "b1425bab"}
LEROBOT_PARTS = ("lerobot/policies/rtc/", "lerobot/policies/pi05/", "lerobot/rollout/", "lerobot/robots/so_follower/",
                 "lerobot/motors/feetech/", "lerobot/scripts/lerobot_rollout.py", "lerobot/processor/normalize_processor.py")
res = {"time": f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S}", "checks": []}


def sha(p, b64=False):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 24), b""):
            h.update(blk)
    return base64.urlsafe_b64encode(h.digest()).rstrip(b"=").decode() if b64 else h.hexdigest()


def add(name, ok, detail):
    res["checks"].append({"name": name, "status": ok, "detail": detail})
    print(f"[{ok:4}] {name}: {detail if isinstance(detail, str) else json.dumps(detail, ensure_ascii=False, default=str)[:400]}", flush=True)


# 1 체크포인트
rec = json.loads((SA / "ops/d2_sha256.json").read_text())["files"]
bad, n = [], 0
for p, v in rec.items():
    if "/checkpoints/020000/pretrained_model/" not in p:
        continue
    n += 1
    if not os.path.exists(p) or os.path.getsize(p) != v["size"] or sha(p) != v["sha256"]:
        bad.append(p)
add("d2 020000 pretrained_model sha256 (10-27 기록과 비교)", "OK" if n and not bad else "FAIL", f"{n} 파일, 다름 {len(bad)} {bad}")
cfg = json.loads((CK / "config.json").read_text())
add("d2 020000 config", "INFO", {k: cfg.get(k) for k in ("type", "chunk_size", "n_action_steps", "num_inference_steps", "max_action_dim",
                                                           "normalization_mapping", "rtc_config")})

# 2 평가 코드
code = {}
for f in ("rollout_logged.py", "diag_log.py", "arm_filter.py"):
    code[f] = sha(D2 / "eval" / f)
code["eval_ui.py"] = sha(HOME / "so101_boxpick/scripts/eval_ui.py")
mism = [f for f, pre in EXPECT_CODE.items() if not code[f].startswith(pre)]
add("평가 코드 sha256", "OK" if not mism else "FAIL", {k: v[:12] for k, v in code.items()} | {"mismatch": mism})
res["code_sha256"] = code

# 3 lerobot 설치 파일 vs RECORD
sp = Path(subprocess.run([str(HOME / "so101-env/bin/python"), "-c", "import lerobot,os;print(os.path.dirname(os.path.dirname(lerobot.__file__)))"],
                         capture_output=True, text=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1")).stdout.strip())
recs = list(sp.glob("lerobot-*.dist-info/RECORD"))
checked, diff = 0, []
if recs:
    for line in recs[0].read_text().splitlines():
        parts = line.rsplit(",", 2)
        if len(parts) != 3 or not parts[1].startswith("sha256=") or not parts[0].startswith(LEROBOT_PARTS):
            continue
        p = sp / parts[0]
        checked += 1
        if not p.exists() or sha(p, b64=True) != parts[1][7:]:
            diff.append(parts[0])
add("lerobot 설치 파일 = pip RECORD", "OK" if recs and checked and not diff else ("INFO" if not recs else "FAIL"),
    f"{recs[0].parent.name if recs else 'RECORD 없음'} · 확인 {checked} 파일 · 다름 {diff}")

# 4 eval_ui --check
env = dict(os.environ, CUDA_VISIBLE_DEVICES="", ROLLOUT_DIAG="1", PYTHONDONTWRITEBYTECODE="1")
r = subprocess.run(["python3", "scripts/eval_ui.py", "--session", "main_k8/d2", "--tag", "pan_diag", "--episodes", "12",
                    "--inference.rtc.prefix_attention_schedule=EXP", "--inference.queue_threshold=30", "--arm_filter=true", "--check"],
                   cwd=HOME / "so101_boxpick", capture_output=True, text=True, env=env, timeout=600)
line = next((x for x in r.stdout.splitlines() if "CHECK_OK" in x), "")
want = {"policy": str(CK), "mode='guided'": None, "prefix_attention_schedule=<RTCAttentionSchedule.EXP": None, "max_guidance_weight=10.0": None,
        "execution_horizon=20": None, "queue_threshold=30": None, "max_relative_target=8.0": None, "fps=30.0": None,
        "'arm_filter': True": None, "'alpha': 0.5": None, "'guard': 'off'": None, "'exec_speed': 1.0": None, "enabled=True": None}
miss = [k if v is None else f"{k}={v}" for k, v in want.items() if (v or k) not in line]
add("eval_ui --check (ROLLOUT_DIAG=1)", "OK" if line and not miss and r.returncode == 0 else "FAIL", line.strip()[:600] + (f" · 없음 {miss}" if miss else ""))
add("num_inference_steps (eval_ui 기본 인자)", "INFO", "eval_ui INFER_DEFAULTS --policy.num_inference_steps=5 (코드 고정, 명령에서 덮어쓰지 않음)"
    if "--policy.num_inference_steps=5" in (HOME / "so101_boxpick/scripts/eval_ui.py").read_text() else "찾지 못함")

# 5 학습 상태
ps = subprocess.run(["pgrep", "-af", "lerobot_train|lerobot-train|train_weighted|run_queue.sh"], capture_output=True, text=True).stdout.strip()
ps = "\n".join(x for x in ps.splitlines() if "pgrep" not in x)
a2 = SA / "runs/A2_s2001/checkpoints"
add("sampling_ablation 정지", "OK" if (SA / "runs/QUEUE_STOPPED").exists() and not ps and not os.access(SA / "runs/run_A2r_s2001.sh", os.X_OK) else "FAIL",
    {"QUEUE_STOPPED": (SA / "runs/QUEUE_STOPPED").read_text().strip() if (SA / "runs/QUEUE_STOPPED").exists() else None,
     "train_procs": ps or "없음", "run_A2r_exec": os.access(SA / "runs/run_A2r_s2001.sh", os.X_OK),
     "A2_ckpts": sorted(x.name for x in a2.iterdir()), "A2_last": os.readlink(a2 / "last") if (a2 / "last").is_symlink() else None,
     "A2r_dir": (SA / "runs/A2r_s2001").exists(), "A0_s2002_dir": (SA / "runs/A0_s2002").exists()})

# 6 실행 환경
gpu = subprocess.run(["nvidia-smi", "--query-compute-apps=pid,process_name,used_memory", "--format=csv,noheader"], capture_output=True, text=True).stdout.strip()
add("GPU compute 프로세스", "OK" if not gpu else "FAIL", gpu or "없음")
lr = subprocess.run(["pgrep", "-af", "lerobot-(record|rollout|teleoperate)|record_ui.py|eval_ui.py"], capture_output=True, text=True).stdout.strip()
lr = "\n".join(x for x in lr.splitlines() if "pgrep" not in x)
add("다른 lerobot 프로세스", "OK" if not lr else "FAIL", lr or "없음")
try:
    dk = subprocess.run(["docker", "ps", "--format", "{{.Names}}"], capture_output=True, text=True, timeout=10).stdout.split()
except Exception:
    dk = []
add("twin 컨테이너", "OK" if not any("twin" in x for x in dk) else "FAIL", ", ".join(dk) or "없음")
dev = {d: os.path.exists(d) for d in ("/dev/so101_follower", "/dev/cam_front", "/dev/cam_wrist")}
add("장치 경로 (존재만, 열지 않음)", "OK" if all(dev.values()) else "FAIL", dev)
free = shutil.disk_usage(D2).free / 1e9
add("디스크 여유", "OK" if free > 10 else "FAIL", f"{free:.1f} GB")
add("ROLLOUT_DIAG_DIR 환경변수", "OK" if not os.environ.get("ROLLOUT_DIAG_DIR") else "FAIL",
    os.environ.get("ROLLOUT_DIAG_DIR") or "없음 → diag 는 실행 폴더/diag/ 에 쓰임 (eval_ui 가 ROLLOUT_FILTER_LOG 를 실행 폴더로 둠)")

OUT.mkdir(parents=True, exist_ok=True)
f = OUT / f"preflight_{datetime.datetime.now():%Y%m%d_%H%M%S}.json"
f.write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
nf = sum(c["status"] == "FAIL" for c in res["checks"])
print(f"\n{'ALL_OK' if nf == 0 else f'FAIL {nf}'} → {f}")
