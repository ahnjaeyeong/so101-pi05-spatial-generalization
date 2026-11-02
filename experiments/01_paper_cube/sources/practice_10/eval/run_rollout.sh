#!/usr/bin/env bash
# practice_10 pi05_2k 실물 평가 + 녹화 + 분석.  ※ 팔에 토크가 걸리고, 모델 로딩(약 3분)이 끝나면 바로 움직인다.
# 사용: [N_EP=2] [EP_S=3600] [RESET_S=3600] ./run_rollout.sh <tag> <추론 옵션...>
#   판·리셋 시간은 기본 1시간 = 사실상 제한 없음. 끝났으면 n 또는 → 로 넘긴다.
#   예) ./run_rollout.sh rtc_h20 --inference.type=rtc --inference.rtc.execution_horizon=20
# 실행 중 키 (이 터미널에 포커스): n 또는 → = 지금 판/리셋 끝내고 다음으로, r 또는 ← = 이번 판 다시,
#   q 또는 Esc = 이번 판 저장하고 종료.  Ctrl+C 는 녹화 중인 판이 저장되지 않으니 비상시에만.
# 결과: eval/rollouts/<시각>_<tag>/ — console.log, debug.log(RTC 지연·제한 경고), dataset/(관측·행동), analysis.json, ep*_action_state.png
set -uo pipefail
N_EP=${N_EP:-2}; EP_S=${EP_S:-3600}; RESET_S=${RESET_S:-3600}
TAG=${1:?"tag 를 주세요 (예: rtc_h20)"}; shift
EVAL=$HOME/so101_runs/practice/practice_10/eval
CKPT=$HOME/so101_runs/practice/practice_10/train/pi05_2k/checkpoints/002000/pretrained_model
RUN=$EVAL/rollouts/$(date +%Y%m%d_%H%M%S)_$TAG
mkdir -p "$RUN"
echo "$0 $TAG $*" > "$RUN/command.txt"
cd "$EVAL"

# 시작 자세 기록만 (읽기만, 토크 안 건드림, 묻지 않음). 실패해도 계속.
PYTHONDONTWRITEBYTECODE=1 "$HOME/so101-env/bin/python" "$EVAL/pose_check.py" --yes --out "$RUN/pose_check.txt" >/dev/null 2>&1 || true
echo "판 ${N_EP}개 · 판 최대 ${EP_S}초 · 리셋 최대 ${RESET_S}초 — 로딩(약 2–3분)이 끝나면 바로 움직입니다."
echo "키 (이 터미널에서): n/→ = 이 판(또는 리셋) 끝내고 다음으로 · r/← = 이 판 다시 · q/Esc = 저장하고 종료"

ROLLOUT_DEBUG_LOG=$RUN/debug.log PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
"$HOME/so101-env/bin/python" "$EVAL/rollout_logged.py" \
  --strategy.type=episodic \
  --policy.path="$CKPT" \
  --robot.type=so101_follower \
  --robot.port=/dev/so101_follower \
  --robot.id=my_arm \
  --robot.max_relative_target=8 \
  '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG"}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG"} }' \
  --dataset.repo_id="oxr/rollout_practice10_pi05_2k_$TAG" \
  --dataset.root="$RUN/dataset" \
  --dataset.no_stamp=true \
  '--dataset.single_task=pick up the red cube and put it in the brown box' \
  --dataset.num_episodes="$N_EP" \
  --dataset.episode_time_s="$EP_S" \
  --dataset.reset_time_s="$RESET_S" \
  --dataset.push_to_hub=false \
  --fps=30 \
  --play_sounds=false \
  --display_data=false \
  "$@" 2>&1 | tee -i "$RUN/console.log"
echo "lerobot-rollout 종료 코드: ${PIPESTATUS[0]}"

# 분석 (녹화 결과를 읽기만 함). 저장된 판이 없으면 건너뜀.
if ! ls "$RUN"/dataset/data/*/*.parquet >/dev/null 2>&1; then echo "저장된 판 없음: $RUN"; exit 1; fi
PYTHONDONTWRITEBYTECODE=1 "$HOME/so101-env/bin/python" "$EVAL/analyze_rollout.py" "$RUN"
PYTHONDONTWRITEBYTECODE=1 python3 "$EVAL/plot_rollout.py" "$RUN"
echo "결과: $RUN"
