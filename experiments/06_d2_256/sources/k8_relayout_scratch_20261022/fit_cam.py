import cv2,numpy as np,json,sys
from scipy.optimize import least_squares
S='/tmp/claude-2001/-home-user/401de9d0-444f-477e-991b-156d7183fd3b/scratchpad/k8'
f=cv2.imread(f'{S}/front_1280.png'); H_,W_=f.shape[:2]
hsv=cv2.cvtColor(f,cv2.COLOR_BGR2HSV)
m=((hsv[...,1]>120)&(hsv[...,2]>100)&((hsv[...,0]<20)|(hsv[...,0]>160))).astype(np.uint8)
n,l,st,c=cv2.connectedComponentsWithStats(m)
cents=[c[i] for i in range(1,n) if st[i,4]>800]
G={'K1':(0,15),'K2':(0,0),'K3':(0,-15),'K4':(-8.5,15),'K5':(-8.5,0),'K6':(-8.5,-15),'K7':(-17.5,15),'K8':(-17.5,-15)}
approx={'K1':(904,416),'K2':(638,422),'K3':(380,420),'K4':(885,288),'K5':(637,284),'K6':(398,281),'K7':(867,156),'K8':(416,165)}
px={k:min(cents,key=lambda p:np.hypot(*(p-np.array(v)))) for k,v in approx.items()}
names=list(G); X=np.array([G[k] for k in names],float); U=np.array([px[k] for k in names])
cx,cy=W_/2,H_/2
def proj(p,P3):
    fo,r,t,zc,k1=p[0],p[1:4],p[4:7],p[7],p[8]
    Pc=(cv2.Rodrigues(r)[0]@P3.T).T+t
    xn=Pc[:,:2]/Pc[:,2:3]; r2=(xn**2).sum(1,keepdims=True); xn=xn*(1+k1*r2)
    return xn*fo+[cx,cy]
def res(p,use_k1):
    if not use_k1: p=p.copy(); p[8]=0
    P3=np.c_[X,np.full(len(X),p[7])]
    return (proj(p,P3)-U).ravel()
# init from homography decomposition
Hm,_=cv2.findHomography(X,U)
best=None
for fo in np.linspace(500,2500,41):
    K=np.array([[fo,0,cx],[0,fo,cy],[0,0,1]]); B=np.linalg.inv(K)@Hm; s=1/np.linalg.norm(B[:,0])
    if B[2,2]*s<0: s=-s
    r1,r2,t=B[:,0]*s,B[:,1]*s/np.linalg.norm(B[:,1]*s),B[:,2]*s
    R=np.c_[r1,r2,np.cross(r1,r2)]; Uu,_,Vt=np.linalg.svd(R); R=Uu@Vt
    p0=np.r_[fo,cv2.Rodrigues(R)[0].ravel(),t,1.5,0]
    sol=least_squares(res,p0,args=(False,))
    if best is None or sol.cost<best.cost: best=sol
out={}
for use_k1 in (False,True):
    sol=least_squares(res,best.x,args=(use_k1,))
    p=sol.x.copy()
    if not use_k1: p[8]=0
    r=res(p,use_k1).reshape(-1,2)
    print('k1' if use_k1 else 'nok1','f=%.0f zc=%.2f k1=%.3f'%(p[0],p[7],p[8]),'rms px %.2f max %.2f'%(np.sqrt((r**2).sum(1).mean()),np.hypot(*r.T).max()))
    R=cv2.Rodrigues(p[1:4])[0]; cam=-R.T@p[4:7]; print('  camera pos (grid cm)',cam.round(1))
    for k,e in zip(names,r): print('  ',k,G[k],U[names.index(k)].round(1),'res px',e.round(2))
    out['k1' if use_k1 else 'nok1']=p.tolist()
json.dump({'params':out,'cx':cx,'cy':cy,'px':{k:list(map(float,v)) for k,v in px.items()},'G':G},open(f'{S}/cam_fit.json','w'),indent=1)
