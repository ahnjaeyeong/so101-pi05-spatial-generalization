# constrained fit: box wall outer face at x=8.5 (grid frame, origin K2), h=6, inner width 22.5 (outer 23.5), wall 0.5
import cv2,numpy as np,json
from scipy.optimize import least_squares
S='/tmp/claude-2001/-home-user/401de9d0-444f-477e-991b-156d7183fd3b/scratchpad/k8'
d=json.load(open(f'{S}/cam_fit.json')); px=d['px']; cx,cy=d['cx'],d['cy']
obs={k:np.array(v) for k,v in json.load(open(f'{S}/fit3.json'))['obs'].items()}
# photo positions (as placed at capture time: K4-K7 9 cm)
Gphoto=d['G']; names=list(Gphoto); X=np.array([Gphoto[k] for k in names],float); U=np.array([px[k] for k in names])
XO,H,WALL,INW=8.5,6.0,0.5,22.5
def proj(p,P3):
    fo,r,t,k1=p[0],p[1:4],p[4:7],p[7]
    Pc=(cv2.Rodrigues(r)[0]@np.atleast_2d(P3).T).T+t; xn=Pc[:,:2]/Pc[:,2:3]; xn=xn*(1+k1*(xn**2).sum(1,keepdims=True)); return xn*fo+[cx,cy]
def linedist(p,A,B,pts):
    a,b=proj(p,np.array([A,B])); dv=(b-a)/np.linalg.norm(b-a); q=pts-a; return q[:,0]*dv[1]-q[:,1]*dv[0]
def lines(Yc):
    Xi=XO+WALL; Ya,Yb=Yc-INW/2,Yc+INW/2
    return {'far_rim':((XO,-30,H),(XO,30,H)),'far_floor':((Xi,-30,0),(Xi,30,0)),
            'L_rim':((Xi,Ya-WALL,H),(Xi+20,Ya-WALL,H)),'L_floor':((Xi,Ya,0),(Xi+20,Ya,0)),
            'R_rim':((Xi,Yb+WALL,H),(Xi+20,Yb+WALL,H)),'R_floor':((Xi,Yb,0),(Xi+20,Yb,0))}
def res(p,zc,use=('far_rim','far_floor','L_rim','R_rim','R_floor','L_floor')):
    r=[(proj(p[:8],np.c_[X,np.full(len(X),zc)])-U).ravel()]
    for k,(A,B) in lines(p[8]).items():
        if k in use: r.append(linedist(p[:8],A,B,obs[k])/np.sqrt(len(obs[k])/4))
    return np.concatenate(r)
p0=np.array(json.load(open(f'{S}/fit4.json'))['results']['1.4'])
best=None
for fo in (600,750,900,1050,1200):
    for zc in (1.4,):
        q=np.r_[p0[:8],0.3]; q[0]=fo
        s=least_squares(res,q,args=(zc,),loss='soft_l1',f_scale=2)
        if best is None or s.cost<best.cost: best=s
for use in [('far_rim','far_floor','L_rim','R_rim','R_floor','L_floor'),('far_rim','far_floor','L_rim','R_rim','R_floor')]:
    s=least_squares(res,best.x,args=(1.4,use),loss='soft_l1',f_scale=2); p=s.x
    rc=proj(p[:8],np.c_[X,np.full(len(X),1.4)])-U
    rb={k:round(float(np.abs(linedist(p[:8],*lines(p[8])[k],obs[k])).mean()),2) for k in obs}
    C=-cv2.Rodrigues(p[1:4])[0].T@p[4:7]
    print('lines used',len(use),f'f={p[0]:.0f} k1={p[7]:.3f} cam={C.round(1)} cube rms {np.sqrt((rc**2).sum(1).mean()):.2f}px  box centre y Yc={p[8]:.2f}  -> C y={p[8]-INW/2-WALL:.2f}')
    print('   line |res| px',rb)

# ---- 저장: C 좌표계(원점 C, x 상자 쪽, y 로봇 왼쪽) · 640x480 화면용 카메라 모델 (6줄 맞춤 결과)
p = least_squares(res, best.x, args=(1.4,), loss='soft_l1', f_scale=2).x
Cg = np.array([8.5, -11.5, 0.0])                  # C 의 격자 좌표
R = cv2.Rodrigues(p[1:4])[0]; t = p[4:7] + R @ Cg  # P_cam = R (P_C + Cg) + t
model = {"f": p[0] / 1.5, "cx": (cx - 160) / 1.5, "cy": cy / 1.5, "k1": p[7],
         "rvec": p[1:4].tolist(), "tvec": t.tolist()}
json.dump(model, open(f'{S}/cam_model_C640.json', 'w'), indent=1)
print('saved', {k: (round(v, 4) if isinstance(v, float) else [round(x, 4) for x in v]) for k, v in model.items()})
