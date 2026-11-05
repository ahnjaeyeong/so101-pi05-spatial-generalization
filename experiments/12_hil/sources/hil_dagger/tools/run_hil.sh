#!/usr/bin/env bash
# HIL 교정 수집 (실물) — 사용자가 직접 실행. Claude 는 실행하지 않는다 (팔 토크 · 실물 동작).
# 아직 실물 시험 승인 전: docs/00_보고서.md §10 의 '실물 시험 전 조건' 을 모두 확인한 뒤에만 쓴다.
#
# 사용:  tools/run_hil.sh <tag> [추가 --hil.* / lerobot 옵션]
#        DRY=1 tools/run_hil.sh <tag>   → 명령만 출력 (장치 · 모델 안 건드림)
#
# 구성: lerobot 0.6.2 `lerobot-rollout --strategy.type=dagger` (교정만 녹화 = 공식 기본) + tools/hil_dagger_entry.py adapter
#       추론 설정 = d2 평가와 같음 (RTC · horizon 20 · EXP · steps 5 · queue 30 · max_relative_target 8)
#       팔 필터 OFF (2026-11-04 사용자 결정; rollout_logged 기본). --rollout_guard=warn 은 filter_log 기록용 (명령 안 바꿈).
#       자동 시작 자세 복귀 없음: --return_to_initial_position=false + adapter A11 (종료 때 home/release/hold 직접 선택).
#       정책 오류 (A10): 첫 추론 오류에서 정책 명령 차단 · RTC 큐 무효화 · 정지 — 그 세션에서는 정책 재개 불가.
#       수집자 화면 (A12 + tools/hil_viewer.py): adapter 가 /dev/shm/hil_<tag>_<pid> 에 상태 · 영상 사실값을 쓰고, 화면은 읽기만 한다.
#       화면은 별도 프로세스 (python3) — 키를 받지 않고 (키는 이 터미널에서), 꺼지거나 죽어도 제어에 영향 없음. VIEWER=0 이면 화면 없이.
set -uo pipefail
TAG=${1:?"tag 를 주세요 (예: pilot1)"}; shift
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(dirname "$HERE")
STEP=${STEP:-020000}
CKPT=${CKPT:-$HOME/so101_runs/main_k8/d2/train/32_20000/pi05_expert_bs32_20k/checkpoints/$STEP/pretrained_model}
SENTENCE="pick up the red cube and put it in the brown box"
SESS=$ROOT/sessions/$(date +%Y%m%d_%H%M%S)_$TAG
N=${N:-50}
TAP=/dev/shm/hil_${TAG}_$$

CMD=(env ROLLOUT_DEBUG_LOG="$SESS/debug.log" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
  "$HOME/so101-env/bin/python" "$HERE/hil_dagger_entry.py"
  --strategy.type=dagger --strategy.num_episodes="$N"
  --policy.path="$CKPT"
  --inference.type=rtc --inference.rtc.execution_horizon=20 --inference.rtc.prefix_attention_schedule=EXP
  --policy.num_inference_steps=5 --inference.queue_threshold=30
  --rollout_guard=warn
  --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm --robot.max_relative_target=8
  '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG"}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG"} }'
  --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader
  --dataset.repo_id="oxr/rollout_hil_k8_d2_${STEP}_$TAG" --dataset.root="$SESS/dataset" --dataset.no_stamp=true
  "--dataset.single_task=$SENTENCE" --dataset.num_episodes="$N" --dataset.push_to_hub=false
  --fps=30 --play_sounds=false --display_data=false --return_to_initial_position=false
  --hil.events="$SESS/hil_events.jsonl" --hil.start_paused=true --hil.leader_goal_sync=true
  --hil.correction_max_relative_target=keep --hil.debounce_s=0.8 --hil.pre_s=3 --hil.keyboard=terminal
  --hil.tap="$TAP" --hil.tap_hz=10
  "$@")

VCMD=(python3 "$HERE/hil_viewer.py" --tap "$TAP")
if [ "${DRY:-0}" = "1" ]; then printf '%q ' "${CMD[@]}"; echo; echo "# 화면:"; printf '%q ' "${VCMD[@]}"; echo; exit 0; fi

# GPU 학습 · 평가 체인이 돌고 있으면 시작하지 않는다 (같은 Jetson GPU)
if pgrep -f "train_recovery.py|eval_chain.sh|lerobot_train|lerobot-train" >/dev/null; then
  echo "중단: GPU 학습/평가 프로세스가 돌고 있음 → 끝난 뒤 실행"; pgrep -af "train_recovery.py|eval_chain.sh|lerobot_train|lerobot-train" | cut -c1-150; exit 1
fi
[ -f "$CKPT/model.safetensors" ] || { echo "체크포인트 없음: $CKPT"; exit 1; }
mkdir -p "$SESS"
printf '%q ' "${CMD[@]}" > "$SESS/command.txt"; echo >> "$SESS/command.txt"
cat <<EOF
세션: $SESS
로딩(2–3분) 뒤 리더가 follower 자세로 2 초 동안 움직이고 '정지(PAUSED)' 로 기다립니다 (리더에서 손을 떼고 기다리기).
키 (이 터미널): Space 정책 시작/정지 · Tab 교정 시작/끝(끝 = 저장) · m 복구 완료 · 1/2/3 = R1/R2/R2-O
               g/h 첫 파지 성공/실패 · b/f 최종(상자 안) 성공/실패 · r 원위치 구간 · Esc 종료
정책 추론 오류가 나면 정책 명령을 끊고 정지합니다 (그 세션에서는 Space 재개 안 됨; Tab 교정 · Esc 종료만).
종료(Esc · 오류 · Ctrl+C) 뒤 자동 복귀는 없습니다. follower 는 마지막 목표 자세를 토크로 버티고, 터미널에서
  home (시작 자세로 3 초 이동 뒤 토크 끄기) / release (지금 자세에서 토크 끄기 — 팔을 받친 뒤) / hold (토크 켠 채 종료, Enter)
중에서 고릅니다.
EOF
VPID=""
if [ "${VIEWER:-1}" = "1" ] && [ -n "${DISPLAY:-}" ]; then
  "${VCMD[@]}" > "$SESS/viewer.log" 2>&1 &
  VPID=$!
  echo "수집자 화면 pid $VPID — 화면은 보기만 합니다. 키는 이 터미널 창을 클릭한 뒤 누르세요."
fi
cd "$SESS" && "${CMD[@]}" 2>&1 | tee -i "$SESS/console.log"
echo "lerobot-rollout 종료 코드: ${PIPESTATUS[0]}"
[ -n "$VPID" ] && kill "$VPID" 2>/dev/null
rm -rf "$TAP"
[ -d "$SESS/dataset/data" ] && PYTHONDONTWRITEBYTECODE=1 "$HOME/so101-env/bin/python" "$HERE/hil_qa.py" "$SESS" | tail -30
