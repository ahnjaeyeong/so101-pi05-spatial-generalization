import sys, numpy as np
sys.path.insert(0, "/home/user/so101_runs/main_k8/sgft01_real_eval/overshoot_diag/scripts")
import o1_real_chain as O, b1_bias as BB
info, em, d3 = O.load_ds(f"{O.P3}/dataset")
rows = []
for ep in range(3, 43):
    e = d3[d3.episode_index == ep].sort_values("frame_index")
    st = np.stack(e["observation.state"].values).astype(float); ac = np.stack(e["action"].values).astype(float)
    ci = O.sg_phase.analyze(st, ac, 30)["_idx"]["close"]
    P = BB.tip(st[:, :5]); Pa = BB.tip(ac[:, :5])
    pc = P[ci]
    D = np.array([BB.decomp(pc, p - pc) for p in P[: ci + 1]])     # out, side, up rel. close pose
    w = D[max(0, ci - 30): ci + 1]                                  # last 1 s
    v = D[ci] - D[max(0, ci - 15)]                                  # last 0.5 s displacement
    pre = D[max(0, ci - 90): ci + 1]
    # overshoot-return: before close, position was beyond final by > 0.3 cm then came back
    over_out = pre[:, 0].max(); under_out = pre[:, 0].min()
    over_side = pre[:, 1].max(); under_side = pre[:, 1].min()
    rows.append(dict(ep=ep, v_out=v[0], v_side=v[1], v_up=v[2], max_out=over_out, min_out=under_out, max_side=over_side, min_side=under_side))
import pandas as pd
R = pd.DataFrame(rows)
print("last 0.5 s displacement into close (cm): median out %+.2f side %+.2f up %+.2f" % tuple(R[["v_out","v_side","v_up"]].median()))
print("  frac moving outward (>+0.1) %.2f inward (<-0.1) %.2f" % ((R.v_out>0.1).mean(), (R.v_out<-0.1).mean()))
print("  frac moving pan+ side (>+0.1) %.2f pan- (<-0.1) %.2f" % ((R.v_side>0.1).mean(), (R.v_side<-0.1).mean()))
print("  frac moving down (<-0.1) %.2f up (>+0.1) %.2f" % ((R.v_up<-0.1).mean(), (R.v_up>0.1).mean()))
print("last 3 s before close: went beyond final OUTWARD by >0.3 cm then came back: %d/40 ; approached from outside... min_out<-0.3 (came from inside): %d/40" % ((R.max_out>0.3).sum(), (R.min_out<-0.3).sum()))
print("  side: beyond pan+ >0.3 then back %d/40 ; beyond pan- %d/40" % ((R.max_side>0.3).sum(), (R.min_side<-0.3).sum()))
print("median max_out %.2f  median min_out %.2f" % (R.max_out.median(), R.min_out.median()))
print("---- longer view")
rr=[]
for ep in range(3, 43):
    e = d3[d3.episode_index == ep].sort_values("frame_index")
    st = np.stack(e["observation.state"].values).astype(float); ac = np.stack(e["action"].values).astype(float)
    ci = O.sg_phase.analyze(st, ac, 30)["_idx"]["close"]
    P = BB.tip(st[:, :5]); pc = P[ci]
    D = np.array([BB.decomp(pc, p - pc) for p in P[: ci + 1]])
    dist = np.linalg.norm(D, axis=1)
    far = np.where(dist > 1.0)[0]; a = far[-1] if len(far) else 0          # last frame >1 cm away
    near = np.where(dist > 0.3)[0]; b = near[-1] if len(near) else 0       # last frame >0.3 cm away
    dirv = D[a]                                                            # where it came from (rel. final), at 1 cm
    seg = D[a:ci+1, 0]; over = seg.max()                                   # after entering 1 cm: beyond outward
    rr.append(dict(ep=ep, dwell=(ci-b)/30, t1=(ci-a)/30, from_out=dirv[0], from_side=dirv[1], from_up=dirv[2], over_out=over, over_side=D[a:ci+1,1].max() if dirv[1]<0 else -D[a:ci+1,1].min()))
Q = pd.DataFrame(rr)
print("dwell (within 0.3 cm before close) s: median %.2f [p25 %.2f, p75 %.2f]" % (Q.dwell.median(), Q.dwell.quantile(.25), Q.dwell.quantile(.75)))
print("time from 1 cm to close s: median %.2f" % Q.t1.median())
print("came from (position at 1 cm, rel final): out median %+.2f (frac inside<0: %.2f) side %+.2f up %+.2f (frac above: %.2f)" % (Q.from_out.median(), (Q.from_out<0).mean(), Q.from_side.median(), Q.from_up.median(), (Q.from_up>0).mean()))
print("after entering 1 cm: went beyond final outward by >0.2 cm: %d/40 (median %.2f)" % ((Q.over_out>0.2).sum(), Q.over_out.median()))
