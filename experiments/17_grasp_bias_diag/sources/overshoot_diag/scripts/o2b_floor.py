#!/home/user/so101-env/bin/python
"""o2 보조: 같은 입력 8 개를 한 batch 로 (o2 A 와 같은 batch 크기) — batch 안 수치 차이 바닥, K=1 재현 차이. → ../data/floor.json"""
import json, os, pathlib, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import o2_reinfer as O
sys.path.insert(0, O.VD)
import v_common as V, v02_engine as E
V.CKPT = pathlib.Path(O.CK)
C = {json.loads(x)["chunk_id"]: json.loads(x) for x in open(f"{O.R}/diag/chunks.jsonl") if x.strip()}
meta = json.load(open(os.path.join(O.OUT, "reinfer_meta.json")))
eng = E.Engine(n_noise=8)
out = []
for m in meta["chunks"][::11]:
    cid = m["chunk"]; z = np.load(f"{O.R}/diag/chunks/c{cid:05d}.npz")
    f = O.rgb(f"{O.R}/diag/obs/c{cid:05d}_front.png"); w = O.rgb(f"{O.R}/diag/obs/c{cid:05d}_wrist.png")
    kw = dict(prefix=z["prefix"], delay=C[cid].get("inference_delay"), noise=z["noise"])
    A8 = eng.run(C[cid]["obs_state"], [(f, w)] * 8, **kw)[:, 0]
    A1 = eng.run(C[cid]["obs_state"], [(f, w)], **kw)[0, 0]
    out.append(dict(chunk=cid, in_batch_max=float(np.abs(A8 - A8[0]).max()), k1_vs_saved=float(np.abs(A1 - z["processed"]).max()),
                    k8_vs_saved=float(np.abs(A8[0] - z["processed"]).max())))
    print(out[-1], flush=True)
json.dump(out, open(os.path.join(O.OUT, "floor.json"), "w"), indent=1)
