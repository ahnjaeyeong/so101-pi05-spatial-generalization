import csv, sys, statistics as st
from collections import Counter
from scipy.stats import fisher_exact, binomtest, mannwhitneyu
B="/home/user/so101_runs/main/redbox_all/eval/eval_space/"
def load(s):
    rows=list(csv.DictReader(open(B+s+"/results/space_trials.csv",encoding="utf-8-sig")))
    plan={r["trial"]:r for r in csv.DictReader(open(B+s+"/plan.csv",encoding="utf-8-sig"))}
    for r in rows: r["_plan"]=plan[r["trial"]]
    return rows
a,b=load("20261020_space"),load("20261022_space_30k")
f=lambda v: float(v) if v not in ("",None) else None
for name,R in (("20k",a),("30k",b)):
    n=len(R); fg=sum(int(r["first"]) for r in R); fi=sum(int(r["final"]) for r in R)
    att=[int(r["attempts"]) for r in R if r["attempts"]]
    print(f"{name}: n={n} first {fg}/{n} final {fi}/{n} attempts mean {st.mean(att):.2f} median {st.median(att)}")
    print("   attempts dist", sorted(Counter(att).items()))
    print("   stop", Counter(r["stop_reason"] for r in R))
    sd=[f(r["duration_s"]) for r in R if r["final"]=="1"]
    print(f"   success duration median {st.median(sd):.1f}s mean {st.mean(sd):.1f}")
    ft=Counter(); [ft.update(x for x in r["failure_type"].split(";") if x) for r in R]
    print("   failure types", ft.most_common())
    for k in ("droll_abs","robot_r_cm","cube_yaw_abs","dist_k_cm","wrist_first_seen_s"):
        v=[f(r[k]) for r in R if f(r[k]) is not None]; print(f"   {k} median {st.median(v):.1f} (n={len(v)})")
    print("   droll sign neg", sum(1 for r in R if f(r["droll"]) is not None and f(r["droll"])<0), "/", sum(1 for r in R if f(r["droll"]) is not None))
print("Fisher first", fisher_exact([[22,18],[12,28]]), "final", fisher_exact([[30,10],[29,11]]))
# paired by (position, rep)
ka={(r["position"],r["rep"]):r for r in a}; kb={(r["position"],r["rep"]):r for r in b}
common=sorted(set(ka)&set(kb)); print("paired slots", len(common))
for key in ("first","final"):
    t=Counter((ka[c][key],kb[c][key]) for c in common); print(key,"(20k,30k)",dict(t))
    n10,n01=t[("1","0")],t[("0","1")]
    if n10+n01: print("  McNemar exact p", binomtest(n10,n10+n01).pvalue)
# droll bins for 30k
for name,R in (("20k",a),("30k",b)):
    for lo,hi in ((0,30),(30,60),(60,999)):
        S=[r for r in R if f(r["droll_abs"]) is not None and lo<=f(r["droll_abs"])<hi]
        print(name,f"droll {lo}-{hi}",len(S),"first",sum(int(r["first"]) for r in S),"final",sum(int(r["final"]) for r in S))
    for lo,hi in ((0,21),(21,24),(24,99)):
        S=[r for r in R if f(r["robot_r_cm"]) is not None and lo<=f(r["robot_r_cm"])<hi]
        print(name,f"r {lo}-{hi}",len(S),"first",sum(int(r["first"]) for r in S),"final",sum(int(r["final"]) for r in S))
x=[f(r["droll_abs"]) for r in a if r["droll_abs"]]; y=[f(r["droll_abs"]) for r in b if r["droll_abs"]]
print("droll_abs 20k vs 30k MWU", mannwhitneyu(x,y))
print("first-fail failure types 30k:")
for r in b:
    if r["first"]=="0": print("  ",r["trial"],r["position"],r["final"],r["attempts"],r["failure_type"],r["note"],"droll",r["droll"],"r",r["robot_r_cm"])
print("---- close-time features (median) by study x first")
for name,R in (("20k",a),("30k",b)):
    for fv in ("1","0"):
        S=[r for r in R if r["first"]==fv]
        out=[]
        for k in ("t_close","wrist_dy_close","wrist_dx_close","wrist_area_close","wrist_flex_close","shoulder_lift_close","elbow_flex_close","front_hidden_frac"):
            v=[f(r[k]) for r in S if f(r[k]) is not None]
            out.append(f"{k}={st.median(v):.2f}(n{len(v)})" if v else f"{k}=NA")
        print(name,"first",fv,len(S)," ".join(out))
for name,R in (("20k",a),("30k",b)):
    v=[f(r["t_close"]) for r in R if f(r["t_close"]) is not None]
    print(name,"t_close all median",st.median(v))
x=[f(r["t_close"]) for r in a if f(r["t_close"]) is not None]; y=[f(r["t_close"]) for r in b if f(r["t_close"]) is not None]
print("t_close MWU",mannwhitneyu(x,y))
x=[f(r["wrist_dy_close"]) for r in a if f(r["wrist_dy_close"]) is not None]; y=[f(r["wrist_dy_close"]) for r in b if f(r["wrist_dy_close"]) is not None]
print("wrist_dy_close MWU",st.median(x),st.median(y),mannwhitneyu(x,y))
print("first fail with 얕은파지/큐브밀림 tag: 20k",sum(1 for r in a if r['first']=='0' and ('얕은' in r['failure_type'] or '밀림' in r['failure_type'])),"/",sum(1 for r in a if r['first']=='0'),
      " 30k",sum(1 for r in b if r['first']=='0' and ('얕은' in r['failure_type'] or '밀림' in r['failure_type'])),"/",sum(1 for r in b if r['first']=='0'))
print("trials with 큐브 밀림 tag: 20k",sum('밀림' in r['failure_type'] for r in a)," 30k",sum('밀림' in r['failure_type'] for r in b))
print("trials with 얕은 파지 tag: 20k",sum('얕은' in r['failure_type'] for r in a)," 30k",sum('얕은' in r['failure_type'] for r in b))
