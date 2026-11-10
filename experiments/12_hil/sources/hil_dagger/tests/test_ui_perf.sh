#!/usr/bin/env bash
# UI 성능: 같은 S7 조작을 tap 없이 3 번 · tap+화면(headless) 3 번 → lerobot Cadence 요약 비교 + 480×640 tap/그리기 벤치. 결과 _out_perf/PERF.md
set -u
cd "$(dirname "$0")"
P=_out_perf; rm -rf $P; mkdir -p $P
for i in 1 2 3; do
  for mode in notap tap; do
    if [ $mode = notap ]; then X="HIL_TEST_NO_TAP=1"; else X="HIL_TEST_NO_TAP=0"; fi
    env -u DISPLAY -u WAYLAND_DISPLAY CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 $X nice -n 19 timeout 240 \
      "$HOME/so101-env/bin/python" test_dagger_fake_e2e.py S7_adapter_normal $P/${mode}_$i > $P/${mode}_$i.console.log 2>&1
  done
done
for d in $P/notap_* $P/tap_*; do [ -d "$d" ] && PYTHONDONTWRITEBYTECODE=1 "$HOME/so101-env/bin/python" check_results.py $d > /dev/null 2>&1; done
PYTHONDONTWRITEBYTECODE=1 "$HOME/so101-env/bin/python" bench_ui.py $P
