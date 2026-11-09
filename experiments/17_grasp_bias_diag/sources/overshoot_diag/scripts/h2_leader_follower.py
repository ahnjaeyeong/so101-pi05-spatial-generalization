import sys, json, numpy as np, pandas as pd
sys.path.insert(0, "/home/user/so101_runs/main_k8/sgft01_real_eval/overshoot_diag/scripts")
import o1_real_chain as O, b1_bias as BB
info, em, d3 = O.load_ds(f"{O.P3}/dataset")
H=[]
for ep in range(3, 43):
    e = d3[d3.episode_index == ep].sort_values("frame_index")
    st = np.stack(e["observation.state"].values).astype(float); ac = np.stack(e["action"].values).astype(float)
    ci = O.sg_phase.analyze(st, ac, 30)["_idx"]["close"]
    for k in range(ci-30, ci-5):   # still phase before close
        p = BB.tip(st[k:k+1, :5])[0]; q = BB.tip(ac[k:k+1, :5])[0]
        H.append([ep] + list(BB.decomp(p, q - p)) + list(ac[k,:5]-st[k,:5]))
H = pd.DataFrame(H, columns=["ep","out","side","up","pan","lift","elbow","wflex","wroll"]).groupby("ep").mean()
print("HUMAN leader(action) - follower(state), last 1 s before close, per-episode median:")
print(H.median().round(2).to_string())
print("frac out>0: %.2f" % (H.out>0).mean())
T=[]
for ep in range(3, 43):
    e = d3[d3.episode_index == ep].sort_values("frame_index")
    st = np.stack(e["observation.state"].values).astype(float); ac = np.stack(e["action"].values).astype(float)
    ci = O.sg_phase.analyze(st, ac, 30)["_idx"]["close"]
    for k in (ci-10, ci-20):
        p = BB.tip(st[k:k+1,:5])[0]; q = BB.tip(ac[k+20:k+21,:5])[0]; q0 = BB.tip(ac[k:k+1,:5])[0]
        T.append(list(BB.decomp(p, q-p)) + list(BB.decomp(p, q0-p)))
T=np.array(T); print("TRAIN target (human scenes ci-10/ci-20): action[k+20]-state[k] out/side/up median", np.median(T[:,:3],0).round(2), " action[k]-state[k]", np.median(T[:,3:],0).round(2))
s=json.load(open("/home/user/so101_runs/main_k8/sgft01_real_eval/overshoot_diag/data/equilibrium_np_s0_summary.json"))["summary"]
for k in ("human","robot"): print(k, "model push at observed image (out, cm):", [round(x,2) for x in s["v"][k]["push_obs"]], " obs dv", [round(x,3) for x in s["v"][k]["obs_err"]])
