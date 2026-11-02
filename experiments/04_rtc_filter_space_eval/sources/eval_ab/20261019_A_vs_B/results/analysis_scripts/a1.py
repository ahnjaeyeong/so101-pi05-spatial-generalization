import pandas as pd, numpy as np, json, glob, math
ST='/home/user/so101_runs/main/redbox_all/eval/eval_ab/20261019_A_vs_B'
T=pd.read_csv(f'{ST}/results/trials.csv', encoding='utf-8-sig')
T['fs']=(T.first_grasp=='success').astype(int); T['ok']=(T.final=='success').astype(int)
print(T[['trial','order','rep','position','condition','run','duration_s','stop_reason','first_grasp','final','attempts','failure_type','note']].to_string())
# 짝: 같은 rep·position
P=T.pivot_table(index=['rep','position'], columns='condition', values=['fs','ok','order'], aggfunc='first')
for m in ['fs','ok']:
    a=P[(m,'A')]; b=P[(m,'B')]
    n10=int(((a==1)&(b==0)).sum()); n01=int(((a==0)&(b==1)).sum())
    k=min(n10,n01); n=n10+n01; p=min(1,2*sum(math.comb(n,i) for i in range(k+1))/2**n) if n else 1
    print(f"{m}: pairs A✓B✗ {n10} · A✗B✓ {n01} · both✓ {int(((a==1)&(b==1)).sum())} · both✗ {int(((a==0)&(b==0)).sum())} · McNemar exact p={p:.3f}")
# 순서 효과
P2=P.copy(); first=np.where(P2[('order','A')]<P2[('order','B')],'A first','B first')
for m in ['fs','ok']:
    for f in ['A first','B first']:
        s=P2[first==f]; print(m, f, 'A', int(s[(m,'A')].sum()), 'B', int(s[(m,'B')].sum()), 'of', len(s))
# 시간 추세 (실행 순서)
T=T.sort_values('started'); T['idx']=range(1,len(T)+1)
for lo,hi in [(1,10),(11,20),(21,30),(31,40)]:
    s=T[(T.idx>=lo)&(T.idx<=hi)]
    print(f"trials {lo}-{hi}: first {s.fs.sum()}/{len(s)} final {s.ok.sum()}/{len(s)}  A first {s[s.condition=='A'].fs.sum()}/{(s.condition=='A').sum()} B first {s[s.condition=='B'].fs.sum()}/{(s.condition=='B').sum()}")
print(T.groupby('run')[['fs','ok']].agg(['sum','count']))
print(T.groupby('rep')[['fs','ok']].sum())
# 실패유형 × 위치
f=T[T.fs==0]; print(pd.crosstab(f.position, f.failure_type.fillna('')))
print('duration success median', T[T.ok==1].groupby('condition').duration_s.median().to_dict(), 'first-success duration median', T[T.fs==1].groupby('condition').duration_s.median().to_dict())
print('time limit:', T[T.stop_reason.str.contains('time', na=False)][['trial','condition','position','stop_reason','final']].to_string())
