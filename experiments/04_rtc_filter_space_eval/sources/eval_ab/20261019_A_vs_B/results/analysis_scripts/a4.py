import pandas as pd, numpy as np
A='/tmp/claude-2001/-home-user/a503e28d-bef9-4614-b1f4-e109c6c55501/scratchpad/ana'
H=np.array([[3.761925,-9.990971,589.362678],[-7.790239,0.019007,176.820281],[0.006368,0.001593,1.0]]); Hi=np.linalg.inv(H)
def px2cm(x,y):
    v=Hi@np.array([x,y,1.0]); return v[0]/v[2], v[1]/v[2]
D=pd.read_csv(f'{A}/trial_table.csv')
D[['x_cm','y_cm']]=[px2cm(r.cx,r.cy) for r in D.itertuples()]
tr=[]
for g in ['t1_known','t1_random','t2_known','t2_random','t3_known','t3_random']:
    p=pd.read_csv(f'/home/user/so101_runs/main/redbox_{g}/qa/positions.csv'); p=p[(p.color=='red')&(p.excluded.isna())]; p['grp']=g; tr.append(p)
tr=pd.concat(tr); t1=tr[tr.grp.str.startswith('t1')]
K={'K1':(-20.2,31.5),'K2':(-16.2,21.3),'K3':(-7.8,12.7),'K4':(-15.4,2.6)}
rows=[]
for r in D.itertuples():
    d_all=np.hypot(tr.x_cm-r.x_cm, tr.y_cm-r.y_cm); d_t1=np.hypot(t1.x_cm-r.x_cm, t1.y_cm-r.y_cm); dr=np.hypot(t1[t1.grp=='t1_random'].x_cm-r.x_cm, t1[t1.grp=='t1_random'].y_cm-r.y_cm)
    k=K[r.actual]; rows.append(dict(trial=r.trial,cond=r.cond,actual=r.actual,offK=r.offK,x=round(r.x_cm,1),y=round(r.y_cm,1),offK_cm=round(np.hypot(r.x_cm-k[0],r.y_cm-k[1]),1),
        t1R_within2=int((dr<2).sum()), t1R_nearest=round(dr.min(),1), all_red_within2=int((d_all<2).sum()), fs=r.fs, ok=r.ok))
R=pd.DataFrame(rows); print(R[R.offK].to_string()); print()
print('on-K trials: offK_cm median', R[~R.offK].offK_cm.median(), 'max', R[~R.offK].offK_cm.max(), '| off-K offK_cm', sorted(R[R.offK].offK_cm))
print('T1-R episodes total', (t1.grp=='t1_random').sum(), '; all red cube positions', len(tr))
