#!/usr/bin/env bash
# rft01 실물 파일럿 시험 전체 (로봇 · 카메라 연결 없음). GPU 를 쓴다 — 실물 평가 · 학습 중에는 돌리지 말 것.
set -u
cd "$(dirname "$0")"
PY="$HOME/so101-env/bin/python"; export PYTHONDONTWRITEBYTECODE=1
OUT="../logs/tests/run_$(date +%Y%m%d_%H%M%S)"; mkdir -p "$OUT"; rc=0
for sc in normal_timeout user_next r2stop fault ctrl_c ctrl_c2 rerecord fault_off series_home series_ctrl_c; do
  echo "== $sc"; nice -n 19 "$PY" test_fake_pilot_e2e.py --scenario "$sc" > "$OUT/$sc.log" 2>&1 || rc=1
  grep -E "^(PASS|FAIL|INFO [A-Za-z])|ALL_PASS|SOME_FAIL" "$OUT/$sc.log" | grep -v "^INFO 20" | cut -c1-400
done
for t in test_units.py test_safe_home.py test_ui_keys.py; do [ -f "$t" ] && { echo "== $t"; "$PY" "$t" > "$OUT/${t%.py}.log" 2>&1 || rc=1; grep -E "^(PASS|FAIL)|ALL_PASS|SOME_FAIL" "$OUT/${t%.py}.log"; }; done
echo "== test_series.sh"; bash test_series.sh > "$OUT/test_series.log" 2>&1 || rc=1; grep -E "^(PASS|FAIL)|ALL_PASS|SOME_FAIL" "$OUT/test_series.log"
echo "logs: $OUT"; [ $rc -eq 0 ] && echo TESTS_ALL_PASS || echo TESTS_SOME_FAIL; exit $rc
