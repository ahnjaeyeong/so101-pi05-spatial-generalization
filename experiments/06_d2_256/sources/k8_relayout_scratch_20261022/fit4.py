import cv2,numpy as np,json
from scipy.optimize import least_squares
S='/tmp/claude-2001/-home-user/401de9d0-444f-477e-991b-156d7183fd3b/scratchpad/k8'
d=json.load(open(f'{S}/cam_fit.json')); G=d['G']; px=d['px']; cx,cy=d['cx'],d['cy']
names=list(G); X=np.array([G[k] for k in names],float); U=np.array([px[k] for k in names])
g=cv2.GaussianBlur(cv2.imread(f'{S}/front_1280.png').astype(float).mean(2),(3,3),0)
obs={}
cols=np.arange(450,841,10)
obs['far_rim']=[(u,530+np.argmin(np.diff(g[530:565,u]))+0.5) for u in cols]
obs['far_floor']=[(u,570+np.argmax(np.diff(g[570:605,u]))+0.5) for u in cols]
rows=np.arange(600,716,8)
obs['L_rim']=[(365+np.argmin(np.diff(g[v,365:395]))+0.5,v) for v in rows]
obs['L_floor']=[(420+np.argmax(np.diff(g[v,420:445]))+0.5,v) for v in rows]
obs['R_rim']=[(890+np.argmax(np.diff(g[v,890:910]))+0.5,v) for v in rows]
obs['R_floor']=[(850+np.argmin(np.diff(g[v,850:870]))+0.5,v) for v in rows]
for k,v in obs.items(): a=np.array(v); print(k,'u',a[:,0].min(),a[:,0].max(),'v',a[:,1].min(),a[:,1].max())
def proj(p,P3):
    fo,r,t,k1=p[0],p[1:4],p[4:7],p[7]
    Pc=(cv2.Rodrigues(r)[0]@np.atleast_2d(P3).T).T+t; xn=Pc[:,:2]/Pc[:,2:3]; xn=xn*(1+k1*(xn**2).sum(1,keepdims=True)); return xn*fo+[cx,cy]
def linedist(p,A,B,pts):
    a,b=proj(p,np.array([A,B])); dvec=(b-a)/np.linalg.norm(b-a); q=np.array(pts)-a
    return q[:,0]*dvec[1]-q[:,1]*dvec[0]
def lines(q):
    Xi,h,Ya,Yb=q
    return {'far_rim':((Xi-0.5,-30,h),(Xi-0.5,30,h)),'far_floor':((Xi,-30,0),(Xi,30,0)),
            'L_rim':((Xi,Ya-0.5,h),(Xi+20,Ya-0.5,h)),'L_floor':((Xi,Ya,0),(Xi+20,Ya,0)),
            'R_rim':((Xi,Yb+0.5,h),(Xi+20,Yb+0.5,h)),'R_floor':((Xi,Yb,0),(Xi+20,Yb,0))}
def res(p,zc,wbox=1.0):
    r=[(proj(p[:8],np.c_[X,np.full(len(X),zc)])-U).ravel()]
    for k,(A,B) in lines(p[8:]).items(): r.append(wbox*linedist(p[:8],A,B,obs[k])/np.sqrt(len(obs[k])/4))
    return np.concatenate(r)
p0=np.array(json.load(open(f'{S}/cam_fit.json'))['params']['nok1'][:7])
results={}
for zc in (1.1,1.4,1.7):
    best=None
    for fo in (500,600,700,850,1000,1200):
        for h in (5,8,12):
            q=np.r_[p0,0.0,9.5,h,-11,11]; q[0]=fo
            # rescale t so camera stays consistent: keep init simple
            s=least_squares(res,q,args=(zc,),loss='soft_l1',f_scale=2)
            if best is None or s.cost<best.cost: best=s
    p=best.x; R=cv2.Rodrigues(p[1:4])[0]; C=-R.T@p[4:7]
    rc=(proj(p[:8],np.c_[X,np.full(len(X),zc)])-U)
    rb={k:np.abs(linedist(p[:8],*lines(p[8:])[k],obs[k])).mean() for k in obs}
    Xi,h,Ya,Yb=p[8:]
    print(f'zc={zc}: f={p[0]:.0f} cam={C.round(1)} cube rms {np.sqrt((rc**2).sum(1).mean()):.2f}px | Xi={Xi:.2f} h={h:.2f} Ya={Ya:.2f} Yb={Yb:.2f} inner width={Yb-Ya:.2f}')
    print('   line mean |res| px', {k:round(v,2) for k,v in rb.items()})
    results[zc]=p.tolist()
json.dump({'results':results,'obs':{k:[list(map(float,x)) for x in v] for k,v in obs.items()}},open(f'{S}/fit4.json','w'))
