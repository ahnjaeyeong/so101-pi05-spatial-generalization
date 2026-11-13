#!/home/user/so101-env/bin/python
"""재현 확인 (CPU): 복사본으로 다시 돌린 sgft01 010000 height_*.json 을 원본 ../../data/height.json 과 비교.
장면 목록이 같고, 열림 n39 Cc 바깥이 소수 둘째 자리까지 +0.96 [+0.78, +1.14] 이면 rc 0, 아니면 rc 2.
  PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python s0_repro_check.py ../data/height_sgft01_010000.json"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from s1_open_summary import summ  # noqa: E402

orig = os.path.join(HERE, "..", "..", "data", "height.json")
A, B = json.load(open(orig)), json.load(open(sys.argv[1]))
key = lambda m: (m["kind"], m["ep"], m.get("chunk"), m["frame"])
same_scenes = [key(m) for m in A["scenes"]] == [key(m) for m in B["scenes"]]
d = max(abs(np.array(A["res"][i][k]) - np.array(B["res"][i][k])).max() for i in range(len(A["res"])) for k in ("O", "Cc", "Zc")) if same_scenes else None
s = summ(sys.argv[1])
c = [round(x, 2) for x in s["Cc_out"][:3]]
ok = same_scenes and s["n_robot_open"] == 39 and c == [0.96, 0.78, 1.14]
print(json.dumps(dict(same_scenes=same_scenes, n_scenes=(len(A["scenes"]), len(B["scenes"])), max_abs_diff_cm=d,
                      Cc_out_open=s["Cc_out"], expected=[0.96, 0.78, 1.14], ok=ok), ensure_ascii=False, default=float))
sys.exit(0 if ok else 2)
