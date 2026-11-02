#!/usr/bin/env bash
# R1·R2 시험 연습 (본 파일럿 세션과 분리).
#   R1 = practice/r1_try3 4판 (4차 지시서: A 초기 방향 · B1 접근 중 반전 · B2 지나침 · B3 손목 놓침 1판씩, K 2 · 자유 점 2, 좌우 2/2)
#        (그 전 기록: r1_trial 오전 3판, r1_try 오후 4판, r1_try2 3차 정의 2판 — 그대로 둠)
#   R2 = practice/r2_trial 3판
# 실제 로봇이 움직인다: 사용자가 자기 터미널에서 직접 실행 (키 입력·영상 창 필요).
#   bash ~/so101_runs/main_k8/r1_r2_collection/trial_practice.sh          # R1 4판 → (확인) → R2 3판
#   bash ~/so101_runs/main_k8/r1_r2_collection/trial_practice.sh r1       # R1 만 (r2 = R2 만)
#   TRIAL_PREVIEW=1 bash ~/so101_runs/main_k8/r1_r2_collection/trial_practice.sh   # 로봇 없이 같은 순서 (preview)
set -u
PY=$HOME/so101-env/bin/python
T=$HOME/so101_runs/main_k8/r1_r2_collection/tools
WHICH=${1:-both}
export PYTHONDONTWRITEBYTECODE=1

run_one() {  # $1 = r1 | r2
  local grp sess up n
  case "$1" in
    r1) grp=r1_try3;  sess=practice/r1_try3 ;;
    r2) grp=r2_trial; sess=practice/r2_trial ;;
  esac
  up=$(echo "$1" | tr a-z A-Z)
  n=$(grep -cE '^\| [0-9]+ \|' "$HOME/so101_runs/$sess/r12_sheet.md")
  echo
  echo "════════ $up 시험 연습 ${n}판 — 세션 $sess ════════"
  grep -E '^\| [0-9]+ \|' "$HOME/so101_runs/$sess/r12_sheet.md" | sed 's/^/  /'
  if [[ "$1" == r1 ]]; then
    echo "  (선택) 첫 판 준비 때 그리퍼를 큐브 바로 위에 두고 c = 로봇 선(하늘색) 보정"
    echo "  준비 (녹화 안 함): 큐브 놓기 (F = 표시 없는 자유 점, 대략) → 그리퍼 열기 → 시나리오의 오차 자세 (주황 선 쪽, B 는 팔 일부 폄)"
    echo "         조건이 달라도 녹화됨 (◇ 경고) · 바꾸기: s 시나리오 · d 오차 방향 · k 큐브 자리 · x front 검출 자리"
    echo "         → 두 번 (첫 번째 = 안전 확인). 빨간 ✗ = 안전 조건 (|pan|>95°·Pan 한계 10° 안·리더−팔로워 25°·관절값 없음) 만 녹화를 막음"
    echo "  녹화: 되돌리는 동작부터 → 접근·파지 → 상자 → 쉬는 자세 → 오른쪽 화살표"
    echo "  결과: 1 · 2 · 3 (재정렬 못 함) · 4 (재정렬 O·파지 실패) · p 다시 보기 → 오른쪽 화살표 = 저장 → 다음 판 준비 (저장 중 리더 그대로)"
  else
    echo "  준비: 큐브 각도 → 그리퍼 열고 손목 화면 주황 영역에 큐브가 오게 → 오른쪽 화살표"
  fi
  if [[ -n "${TRIAL_PREVIEW:-}" ]]; then
    "$PY" "$T/r12_collect.py" preview --group "$grp" --episodes "$n"
    return
  fi
  "$PY" "$T/r12_collect.py" record --session "$sess"
  if [[ -f "$HOME/so101_runs/$sess/dataset/meta/info.json" ]]; then
    "$PY" "$T/r12_collect.py" qa --session "$sess"
  fi
  "$PY" "$T/r12_collect.py" status --session "$sess"
}

"$PY" "$T/r12_collect.py" check || { echo "환경 확인 실패 — 멈춤"; exit 1; }
case "$WHICH" in
  r1) run_one r1 ;;
  r2) run_one r2 ;;
  both)
    run_one r1
    read -r -p $'\nR2 시험 연습 3판을 이어서 할까요? [Enter = 예 / n = 그만] ' a
    [[ "$a" == n* ]] || run_one r2 ;;
  *) echo "인자: r1 | r2 | (없음 = 둘 다)"; exit 2 ;;
esac
