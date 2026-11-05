#!/usr/bin/env bash
# 가짜 장치 e2e 전체 (CPU 전용, 실물 · GPU 차단). 사용: ./run_all.sh [scenario ...]
set -u
cd "$(dirname "$0")"
OUT=_out
mkdir -p $OUT
SCENS=${*:-"S1_normal S2_key_race S3_esc_in_correction S4_leader_fault S5_rtc_fault S9_follower_write_fault S6a_enable_stale S6b_enable_present S7_adapter_normal S8_adapter_esc_in_correction S10_adapter_start_paused_reset S11_adapter_fast_correction S12_adapter_rtc_fault S13_adapter_leader_fault S14_adapter_follower_fault S15_adapter_normal_end_home S17_adapter_viewer_killed S18_adapter_tap_fault"}
for s in $SCENS; do
  env -u DISPLAY -u WAYLAND_DISPLAY CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 nice -n 19 \
    timeout 240 "$HOME/so101-env/bin/python" test_dagger_fake_e2e.py "$s" $OUT > $OUT/$s.console.log 2>&1
  echo "$s rc=$? $(grep -c MOCK_OK $OUT/$s.console.log) MOCK_OK lines; $(tail -1 $OUT/$s.console.log | cut -c1-120)"
done
# S16: 실제 터미널(pty) 키 경로 + 종료 메뉴 입력
env -u DISPLAY -u WAYLAND_DISPLAY PYTHONDONTWRITEBYTECODE=1 "$HOME/so101-env/bin/python" test_pty_terminal.py | tail -1
PYTHONDONTWRITEBYTECODE=1 "$HOME/so101-env/bin/python" check_results.py $OUT
PYTHONDONTWRITEBYTECODE=1 "$HOME/so101-env/bin/python" test_qa_mapping.py
PYTHONDONTWRITEBYTECODE=1 "$HOME/so101-env/bin/python" make_facts.py $OUT > /dev/null && echo "FACTS: $OUT/FACTS.md"
# UI 시험 (2026-11-04): 상태 판정 단위 시험 + tap 기록 vs 가짜 장치 기록
env -u DISPLAY CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 "$HOME/so101-env/bin/python" test_ui_state.py 2>/dev/null | tail -1
PYTHONDONTWRITEBYTECODE=1 "$HOME/so101-env/bin/python" test_ui_e2e.py $OUT | grep -v "^PASS"
