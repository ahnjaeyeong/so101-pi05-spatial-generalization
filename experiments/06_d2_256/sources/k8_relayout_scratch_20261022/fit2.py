import cv2,numpy as np,json
from scipy.optimize import least_squares
S='/tmp/claude-2001/-home-user/401de9d0-444f-477e-991b-156d7183fd3b/scratchpad/k8'
d=json.load(open(f'{S}/cam_fit.json')); G=d['G']; px=d['px']; cx,cy=d['cx'],d['cy']
names=list(G); X=np.array([G[k] for k in names],float); U=np.array([px[k] for k in names])
img=cv2.imread(f'{S}/front_1280.png'); g=img.astype(float).mean(2)
def proj(p,P3):
    fo,r,t=p[0],p[1:4],p[4:7]
    Pc=(cv2.Rodrigues(r)[0]@P3.T).T+t; return Pc[:,:2]/Pc[:,2:3]*fo+[cx,cy]
def ray_plane(p,uv,plane_n,plane_d):
    fo,R,t=p[0],cv2.Rodrigues(p[1:4])[0],p[4:7]; C=-R.T@t
    dirc=np.array([(uv[0]-cx)/fo,(uv[1]-cy)/fo,1.0]); dw=R.T@dirc
    s=(plane_d-plane_n@C)/(plane_n@dw); return C+s*dw
# box lines: floor line (inner far wall meets floor) and rim top edge, per column
cols=np.arange(450,840,10); floor=[];rim=[]
for u in cols:
    col=g[530:615,u-2:u+3].mean(1); dcol=np.diff(col)
    rim.append(530+np.argmin(dcol[:35])+0.5)          # bright table -> dark wall
    floor.append(530+40+np.argmax(dcol[40:])+0.5)      # darker wall face -> lighter floor
rim=np.array(rim); floor=np.array(floor)
print('rim v',rim.min(),rim.max(),' floor v',floor.min(),floor.max())
for zc in (1.0,1.4,1.8):
    def res(p):
        return (proj(p,np.c_[X,np.full(len(X),zc)])-U).ravel()
    p0=np.r_[d['params']['nok1'][:7]]
    best=None
    for fo in (450,550,650,800,1000):
        q=p0.copy(); q[0]=fo
        s=least_squares(res,q)
        if best is None or s.cost<best.cost: best=s
    p=best.x
    r=res(p).reshape(-1,2)
    # far-wall inner face: floor points (z=0) -> x of wall
    fl=np.array([ray_plane(p,(u,v),np.array([0,0,1.]),0.0) for u,v in zip(cols,floor)])
    Xw=np.median(fl[:,0])
    # rim (outer top edge) on plane x = Xw-0.5 (outer face top), solve z
    rm=np.array([ray_plane(p,(u,v),np.array([1.,0,0]),Xw-0.5) for u,v in zip(cols,rim)])
    h=np.median(rm[:,2])
    # outer corners of far wall rim (image left = robot right = -y)
    cl=ray_plane(p,(384.2,551.7),np.array([0,0,1.]),h); cr=ray_plane(p,(894.0,545.0),np.array([0,0,1.]),h)
    R=cv2.Rodrigues(p[1:4])[0]; C=-R.T@p[4:7]
    print(f'zc={zc} f={p[0]:.0f} rms={np.sqrt((r**2).sum(1).mean()):.2f}px cam={C.round(1)} | wall inner x={Xw:.2f} (spread {fl[:,0].std():.2f}) h={h:.2f} (spread {rm[:,2].std():.2f}) | rim corners y {cl[1]:.2f} {cr[1]:.2f} outer len {cr[1]-cl[1]:.2f} x {cl[0]:.2f} {cr[0]:.2f}')
