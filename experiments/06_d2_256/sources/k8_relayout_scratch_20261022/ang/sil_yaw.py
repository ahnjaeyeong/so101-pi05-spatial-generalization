import cv2,numpy as np,sys,json,math
sys.path.insert(0,'/home/user/so101_boxpick/scripts'); import layout_plan as lp
S='/tmp/claude-2001/-home-user/401de9d0-444f-477e-991b-156d7183fd3b/scratchpad/k8'
cfg=lp.load_config('/home/user/so101_boxpick/config/redbox8_layouts.yaml'); H=np.array(cfg['camera']['front_640x480']['H_cm_to_px']); Hi=np.linalg.inv(H)
M=json.load(open(f'{S}/cam_model_C640.json')); R=cv2.Rodrigues(np.array(M['rvec']))[0]; T=np.array(M['tvec'])
def proj(P):
    Pc=P@R.T+T; xn=Pc[:,:2]/Pc[:,2:3]; xn=xn*(1+M['k1']*(xn**2).sum(1,keepdims=True)); return xn*M['f']+[M['cx'],M['cy']]
SZ=2.5
def sil(x,y,th):
    a=SZ/2; c,s=math.cos(th),math.sin(th)
    pts=[(x+u*c-v*s,y+u*s+v*c,z) for u in (-a,a) for v in (-a,a) for z in (0,SZ)]
    return cv2.convexHull(proj(np.array(pts)).astype(np.float32))
def fit(blob):
    ys,xs=np.nonzero(blob); x0,x1,y0,y1=xs.min()-8,xs.max()+9,ys.min()-8,ys.max()+9
    obs=blob[y0:y1,x0:x1]>0
    c=cv2.perspectiveTransform(np.array([[[xs.mean(),ys.mean()]]],float),Hi)[0,0]
    def iou(x,y,th):
        m=np.zeros_like(obs,np.uint8); h=(sil(x,y,th)-[x0,y0])
        cv2.fillConvexPoly(m,np.round(h*4).astype(np.int32),1,shift=2)
        m=m>0; return (m&obs).sum()/max(1,(m|obs).sum())
    best=(-1,)
    for th in np.radians(np.arange(-45,45,3)):
        for dx in np.arange(-1.2,1.21,0.4):
            for dy in np.arange(-1.2,1.21,0.4):
                v=iou(c[0]+dx,c[1]+dy,th)
                if v>best[0]: best=(v,c[0]+dx,c[1]+dy,th)
    _,bx,by,bt=best
    for th in bt+np.radians(np.arange(-3,3.1,0.5)):
        for dx in np.arange(-0.3,0.31,0.1):
            for dy in np.arange(-0.3,0.31,0.1):
                v=iou(bx+dx,by+dy,th)
                if v>best[0]: best=(v,bx+dx,by+dy,th)
    v,x,y,th=best; d=((math.degrees(th)+45)%90)-45
    return d,x,y,v
if __name__=='__main__':
    f=cv2.imread(sys.argv[1]); hsv=cv2.cvtColor(f,cv2.COLOR_BGR2HSV)
    m=np.zeros(f.shape[:2],np.uint8)
    for col in ('red','orange','yellow','blue','green'):
        for r in cfg['detection']['colors'][col]: m|=cv2.inRange(hsv,(r['h'][0],r['s'][0],r['v'][0]),(r['h'][1],r['s'][1],r['v'][1]))
    m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
    n,l,st,cc=cv2.connectedComponentsWithStats(m)
    K={k:v['xy_cm'] for k,v in cfg['known_positions'].items()}
    for i in range(1,n):
        if st[i,4]<300 or st[i,1]>350: continue
        d,x,y,v=fit((l==i).astype(np.uint8))
        k=min(K,key=lambda k:math.dist(K[k],(x,y)))
        print(f'{k}: yaw {d:6.1f}°  pos ({x:6.2f},{y:6.2f}) vs K {K[k]}  IoU {v:.3f}')
