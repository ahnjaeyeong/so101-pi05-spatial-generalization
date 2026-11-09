import sys, numpy as np, pandas as pd
sys.path.insert(0, "/home/user/so101_runs/main_k8/sgft01_real_eval/overshoot_diag/scripts")
import o1_real_chain as O, b1_bias as BB
info, em, d = O.load_ds("/home/user/so101_runs/main_k8/d2/dataset")
R=[]
for ep in sorted(d.episode_index.unique()):
    e = d[d.episode_index == ep].sort_values("frame_index")
    st = np.stack(e["observation.state"].values).astype(float); ac = np.stack(e["action"].values).astype(float)
    g = ac[:,5]; g0 = np.median(g[:30]); 
    # close = first frame after the gripper has opened (> start+10) where action drops by >10 from its running max
    mx = np.maximum.accumulate(g); idx = np.where((mx > g0 + 10) & (g < mx - 10))[0]
    if not len(idx): continue
    ci = idx[0]
    ks = range(max(0,ci-30), ci-5)
    D = [BB.decomp(BB.tip(st[k:k+1,:5])[0], BB.tip(ac[k:k+1,:5])[0]-BB.tip(st[k:k+1,:5])[0]) for k in ks]
    J = (ac[list(ks),:5]-st[list(ks),:5]).mean(0)
    R.append(list(np.mean(D,0))+list(J))
R=pd.DataFrame(R,columns=["out","side","up","pan","lift","elbow","wflex","wroll"])
print("d2 n", len(R), "leader-follower last 1 s before close, median:"); print(R.median().round(2).to_string())
print("frac side>0 (pan+): %.2f" % (R.side>0).mean())
