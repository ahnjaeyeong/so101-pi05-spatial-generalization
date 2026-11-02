import pandas as pd, numpy as np, json
ST='/home/user/so101_runs/main/redbox_all/eval/eval_ab/20261019_A_vs_B'
pos=json.load(open(f'{ST}/study.json'))['positions']
D=pd.read_csv('/tmp/claude-2001/-home-user/a503e28d-bef9-4614-b1f4-e109c6c55501/scratchpad/ana/cube_offsets.csv')
T=pd.read_csv(f'{ST}/results/trials.csv', encoding='utf-8-sig').set_index('trial')
# 실제 위치 = 가장 가까운 K
K={k:np.array(v['front_px']) for k,v in pos.items()}
D['actual']=[min(K,key=lambda k: np.hypot(r.cx-K[k][0],r.cy-K[k][1])) for r in D.itertuples()]
D['off']=[np.hypot(r.cx-K[r.actual][0],r.cy-K[r.actual][1]) for r in D.itertuples()]
D['dx']=[r.cx-K[r.actual][0] for r in D.itertuples()]; D['dy']=[r.cy-K[r.actual][1] for r in D.itertuples()]
D['offK']=D.off>15
J=['shoulder_pan','shoulder_lift','elbow_flex','wrist_flex','wrist_roll','gripper']
out=[]
for r in D.itertuples():
    t=pd.read_csv(f"{ST}/trials/{T.loc[r.trial,'dir']}/ticks.csv"); c=t[t.event=='cmd'].reset_index(drop=True)
    g=c.state_gripper.to_numpy(); opened=np.where(g>15)[0]
    if len(opened)==0: out.append([np.nan]*7); continue
    i0=opened[0]; cl=np.where((np.arange(len(g))>i0)&(g<np.maximum.accumulate(g)-10))[0]   # 최대 개방 대비 10° 이상 닫힌 첫 틱
    i=cl[0] if len(cl) else len(g)-1
    out.append([c.t[i]]+[c[f'state_{j}'][i] for j in J[:5]]+[g[:i+1].max()])
O=pd.DataFrame(out,columns=['t_close']+[j[:5] for j in J[:5]]+['g_open_max']); D=pd.concat([D,O],axis=1)
pd.set_option('display.width',250)
print(D[['trial','cond','pos','actual','off','dx','dy','fs','ok','t_close','shoul','shoul.1' if 'shoul.1' in D else 'elbow','wrist','g_open_max']].round(1).to_string() if False else '')
cols=['trial','cond','actual','offK','dx','dy','fs','ok','t_close','shoul','elbow','wrist','g_open_max']
D2=D.copy(); D2.columns=list(D.columns[:-7])+['t_close','pan','lift','elbow','wflex','wroll','g_open_max']
print(D2[['trial','cond','pos','actual','offK','dx','dy','fs','ok','t_close','pan','lift','elbow','wflex','wroll','g_open_max']].round(1).sort_values(['actual','offK','trial']).to_string())
D2.to_csv('/tmp/claude-2001/-home-user/a503e28d-bef9-4614-b1f4-e109c6c55501/scratchpad/ana/trial_table.csv',index=False)
print()
for k in sorted(K):
    s=D2[D2.actual==k]
    on=s[~s.offK]; off=s[s.offK]
    print(f"{k}: on-K n={len(on)} first {on.fs.sum()} final {on.ok.sum()} pan@close {on.pan.mean():.1f}±{on.pan.std():.1f} | off n={len(off)} first {off.fs.sum()} final {off.ok.sum()} dx,dy {list(zip(off.dx.round(0),off.dy.round(0)))} pan@close {list(off.pan.round(1))}")
on=D2[~D2.offK]; off=D2[D2.offK]
print(f"ALL on-K: n={len(on)} first {on.fs.sum()}/{len(on)} final {on.ok.sum()}/{len(on)} | off-K: n={len(off)} first {off.fs.sum()}/{len(off)} final {off.ok.sum()}/{len(off)}")
for c in 'AB':
    a=on[on.cond==c]; b=off[off.cond==c]
    print(f" {c}: on-K first {a.fs.sum()}/{len(a)} final {a.ok.sum()}/{len(a)} | off-K first {b.fs.sum()}/{len(b)} final {b.ok.sum()}/{len(b)}")
