#!/usr/bin/env bash
# redbox_all pi05_expert_bs32_20k 실물 평가 + 녹화 + 분석.  ※ 팔에 토크가 걸리고, 모델 로딩(약 3분)이 끝나면 바로 움직인다.
# 사용: [TASK=t1] [STEP=020000] [N_EP=1] [EP_S=3600] [RESET_S=3600] ./run_rollout.sh <tag> <추론 옵션...>
#   TASK = t1 · t3 → "pick up the red cube and put it in the brown box" (기본 t1)
#          t2      → "put all the red cubes in the brown box"
#   STEP = 체크포인트 (005000 · 010000 · 015000 · 020000, 기본 020000)
#   판·리셋 시간은 기본 1시간 = 사실상 제한 없음. 끝났으면 n 또는 → 로 넘긴다.
#   예) TASK=t1 ./run_rollout.sh test1
#   팔 관절 필터·감시 (2026-10-19, rollout_logged.py 가 처리, 기본은 둘 다 꺼짐):
#       --arm_filter=true [--arm_filter.alpha=0.5] [--arm_filter.init=state]   --rollout_guard=off|warn|stop
#       켜면 $RUN/filter_log.csv 에 틱마다 필터 전·후 action·실제 상태가 남고, dataset action 은 필터 후 값.
#       --exec_speed=0.8  실행 속도 80% (30 Hz 유지, RTC 큐 안 위치 보간, 팔·그리퍼 같이, RTC 전용). 기본 1.0
#   P0 추천 (오프라인 근거, 실물 미검증):
#       ./run_rollout.sh rtc20_filt --inference.type=rtc --inference.rtc.execution_horizon=20 \
#         --inference.rtc.prefix_attention_schedule=EXP --policy.num_inference_steps=5 --arm_filter=true --rollout_guard=stop
# 실행 중 키 (이 터미널에 포커스): n 또는 → = 지금 판/리셋 끝내고 다음으로, r 또는 ← = 이번 판 다시,
#   q 또는 Esc = 이번 판 저장하고 종료.  Ctrl+C 는 녹화 중인 판이 저장되지 않으니 비상시에만.
# 결과: eval/rollouts/<시각>_<스텝>_<task>_<tag>/ — console.log, debug.log, dataset/(관측·행동), analysis.json, ep*_action_state.png
set -uo pipefail
N_EP=${N_EP:-1}; EP_S=${EP_S:-3600}; RESET_S=${RESET_S:-3600}
TAG=${1:?"tag 를 주세요 (예: test1)"}; shift
TASK=${TASK:-t1}
case "$TASK" in
  t1|t3) SENTENCE="pick up the red cube and put it in the brown box" ;;
  t2)    SENTENCE="put all the red cubes in the brown box" ;;
  *) echo "TASK 는 t1 · t2 · t3 중 하나: $TASK"; exit 1 ;;
esac
EVAL=$HOME/so101_runs/main/redbox_all/eval
STEP=${STEP:-020000}; SK=$((10#$STEP / 1000))k
CKPT=$HOME/so101_runs/main/redbox_all/train/32_20000/pi05_expert_bs32_20k/checkpoints/$STEP/pretrained_model
[ -f "$CKPT/model.safetensors" ] || { echo "체크포인트 없음: $CKPT"; exit 1; }
RUN=$EVAL/rollouts/$(date +%Y%m%d_%H%M%S)_${SK}_${TASK}_$TAG
mkdir -p "$RUN"
echo "TASK=$TASK STEP=$STEP N_EP=$N_EP $0 $TAG $*" > "$RUN/command.txt"
cd "$EVAL"

# 시작 자세 기록만 (읽기만, 토크 안 건드림, 묻지 않음). 실패해도 계속.
PYTHONDONTWRITEBYTECODE=1 "$HOME/so101-env/bin/python" "$EVAL/pose_check.py" --yes --out "$RUN/pose_check.txt" >/dev/null 2>&1 || true
echo "체크포인트 $STEP · $TASK \"$SENTENCE\" · 판 ${N_EP}개 · 판 최대 ${EP_S}초 — 로딩(약 2–3분)이 끝나면 바로 움직입니다."
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
  --dataset.repo_id="oxr/rollout_redbox_all_bs32_20k_${SK}_${TASK}_$TAG" \
  --dataset.root="$RUN/dataset" \
  --dataset.no_stamp=true \
  "--dataset.single_task=$SENTENCE" \
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
