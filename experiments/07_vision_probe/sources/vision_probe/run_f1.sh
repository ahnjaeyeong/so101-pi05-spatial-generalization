#!/usr/bin/env bash
# F1 본 실행 (d4 학습이 끝난 뒤). 로봇 연결 없음 · 학습 없음 · 기존 파일 수정 없음.
#   1) 누출 검사  2) GPU 특징 추출 (약 1만 프레임, 저장 약 50 GB)  3) probe (CPU)  4) 민감도 g_rep · 평가 롤아웃 (CPU)
# d4 가 아직 돌고 있으면 f1_extract.py 가 시작하지 않고 멈춘다.
set -euo pipefail
cd "$(dirname "$0")"
PY="env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 $HOME/so101-env/bin/python"
$PY f1_leak_check.py | tail -3
$PY f1_extract.py --device cuda 2>&1 | grep -v -i "warn\|vision emb" | tee f1_extract.log
nice -n 19 $PY f1_probe.py --sets features 2>&1 | grep -v Warning | tee f1_probe_features.log
nice -n 19 $PY f1_sensitivity.py 2>&1 | grep -v Warning | tee f1_sensitivity.log
echo "F1 끝: f1_results/"
