#!/usr/bin/env bash
# 공식 lerobot-edit-dataset (0.6.2) 로 HIL 데이터 → intervention 열 제거 · 병합 시험 (가짜 데이터셋, CPU). 결과: _out/convert/RESULT.txt
set -u
cd "$(dirname "$0")"
O=_out/convert; rm -rf $O; mkdir -p $O
E="env -u DISPLAY CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 nice -n 19 $HOME/so101-env/bin/lerobot-edit-dataset"
{
$E --repo_id=oxr/rollout_hil_fake_S1_normal --root=_out/S1_normal/dataset --new_repo_id=oxr/hil_fake_S1_noint --new_root=$O/S1_noint --operation.type=remove_feature '--operation.feature_names=[intervention]' > $O/rm1.log 2>&1; echo "remove_feature S1 rc=$?"
$E --repo_id=oxr/rollout_hil_fake_S7_adapter_normal --root=_out/S7_adapter_normal/dataset --new_repo_id=oxr/hil_fake_S7_noint --new_root=$O/S7_noint --operation.type=remove_feature '--operation.feature_names=[intervention]' > $O/rm7.log 2>&1; echo "remove_feature S7 rc=$?"
$E --new_repo_id=oxr/hil_fake_merged --new_root=$O/merged --operation.type=merge '--operation.repo_ids=[oxr/hil_fake_S1_noint, oxr/hil_fake_S7_noint]' "--operation.roots=[$O/S1_noint, $O/S7_noint]" > $O/merge.log 2>&1; echo "merge (둘 다 intervention 제거) rc=$?"
$E --new_repo_id=oxr/hil_fake_merged_mixed --new_root=$O/merged_mixed --operation.type=merge '--operation.repo_ids=[oxr/hil_fake_S1_noint, oxr/rollout_hil_fake_S7_adapter_normal]' "--operation.roots=[$O/S1_noint, _out/S7_adapter_normal/dataset]" > $O/merge_mixed.log 2>&1; echo "merge (한쪽만 intervention 있음) rc=$? : $(grep -o 'ValueError: Same features is expected' $O/merge_mixed.log | head -1)"
PYTHONDONTWRITEBYTECODE=1 $HOME/so101-env/bin/python - <<'PY'
import json, glob
import pyarrow.parquet as pq
d2 = json.load(open('/home/user/so101_runs/main_k8/d2/dataset/meta/info.json'))
for n in ['S1_noint', 'S7_noint', 'merged']:
    p = f'_out/convert/{n}'
    i = json.load(open(p + '/meta/info.json'))
    cols = set()
    for f in glob.glob(p + '/data/*/*.parquet'):
        cols |= set(pq.read_schema(f).names)
    print(f"{n}: episodes {i['total_episodes']} frames {i['total_frames']} · feature 이름 = d2 {set(i['features']) == set(d2['features'])} · "
          f"parquet intervention 열 {'intervention' in cols} · stats intervention {'intervention' in json.load(open(p + '/meta/stats.json'))}")
PY
} | tee $O/RESULT.txt
