import json,math,sys,numpy as np
from scipy.optimize import least_squares
S=sys.argv[1]; D=json.load(open(f'{S}/collect.json'))
w90=lambda a:((a+45)%90)-45
tgt=lambda a: float(a[1:])*(1 if a[0]=='L' else -1) if a[0] in 'LR' else float(a)
# 1) 로봇 중심: pan = a*bearing + b,  bearing = atan2(y-y0, x-x0) (앞 +x 에서 왼쪽 +y 로 반시계 +)
P=np.array([[d['x'],d['y'],d['pan']] for d in D])
best=None
for a in (1,-1):
    f=lambda p: a*np.degrees(np.arctan2(P[:,1]-p[1],P[:,0]-p[0]))+p[2]-P[:,2]
    r=least_squares(f,[-40,11,0])
    if best is None or r.cost<best[1].cost: best=(a,r)
a,r=best; x0,y0,b=r.x; res=r.fun
print(f'로봇 중심(추정) C 좌표 ({x0:.1f}, {y0:.1f}) cm · pan = {a:+d}×방향 + {b:.1f}° · 잔차 중앙 {np.median(np.abs(res)):.1f}° 최대 {np.abs(res).max():.1f}°')
for d in D:
    d['bear']=math.degrees(math.atan2(d['y']-y0,d['x']-x0))
    d['yaw_use']=d['yaw'] if d['yaw'] is not None else tgt(d['plan'])
    d['rel']=w90(d['yaw_use']-d['bear'])   # 반지름(법선) 기준 큐브 각도 (−45, 45]
# 2) 손목: s*(roll − r0) ≡ rel (90° 주기). s, r0 를 맞춘다
best=None
for s in (1,-1):
    for r0 in np.arange(-90,90.01,0.5):
        e=[abs(w90(s*(d['roll']-r0)-d['rel'])) for d in D]
        k=np.median(e)
        if best is None or k<best[0]: best=(k,s,r0)
_,s,r0=best
print(f'손목 회전 부호 s={s:+d} · 반지름 방향과 그리퍼가 나란한 손목 값 r0 = {r0:.1f}° (판 시작 손목 값 중앙 {np.median([d["roll0"] for d in D]):.1f}°)')
rows=[]
for d in D:
    turn=s*(d['roll']-r0)              # 실제로 돌린 양 (반지름 기준, + = 반시계)
    err=w90(turn-d['rel'])              # 90° 주기 차이 (정렬 오차)
    k=round((turn-d['rel']-err)/90)     # 몇 바퀴(90°) 더 돌렸나: 0 = 예각, ±1 = 반대쪽(둔각)으로
    d.update(turn=turn,err=err,k=k)
print('\nep  K   계획  잰각도  로봇방향  필요(반지름기준)  실제돌림  정렬오차  방향')
for d in sorted(D,key=lambda d:d['ep']):
    tag='예각 ✓' if d['k']==0 else ('반대쪽(90° 더)' if abs(d['k'])==1 else f'{d["k"]}×90')
    yaw=f"{d['yaw']:+6.1f}" if d['yaw'] is not None else '  (계획)'
    print(f"{d['ep']:02d} {d['K']} {d['plan']:>4} {yaw} {d['bear']:+7.1f} {d['rel']:+8.1f} {d['turn']:+9.1f} {d['err']:+7.1f}  {tag}")
E=np.array([d['err'] for d in D]); Kk=np.array([d['k'] for d in D])
print(f"\n예각으로 돌린 판 {int((Kk==0).sum())}/{len(D)} · 정렬 오차 |중앙| {np.median(np.abs(E)):.1f}° · 15° 넘음 {int((np.abs(E)>15).sum())}판")
json.dump({'x0':x0,'y0':y0,'pan_a':a,'pan_b':b,'s':s,'r0':r0,'eps':D},open(f'{S}/analysis.json','w'),indent=0)
