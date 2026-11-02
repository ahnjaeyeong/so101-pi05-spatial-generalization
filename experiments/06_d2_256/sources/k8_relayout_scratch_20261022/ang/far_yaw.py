import cv2,numpy as np,sys,json,math
sys.path.insert(0,'/home/user/so101_boxpick/scripts'); import layout_plan as lp
S='/tmp/claude-2001/-home-user/401de9d0-444f-477e-991b-156d7183fd3b/scratchpad/k8'
cfg=lp.load_config('/home/user/so101_boxpick/config/redbox8_layouts.yaml'); H=np.array(cfg['camera']['front_640x480']['H_cm_to_px']); Hi=np.linalg.inv(H)
M=json.load(open(f'{S}/cam_model_C640.json')); R=cv2.Rodrigues(np.array(M['rvec']))[0]; CAM=(-R.T@np.array(M['tvec']))[:2]
def far_yaw(blob, step=0.4):
    cs,_=cv2.findContours(blob,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
    c=max(cs,key=cv2.contourArea).reshape(-1,2).astype(float)
    P=cv2.perspectiveTransform(c.reshape(-1,1,2),Hi).reshape(-1,2)
    # 0.1 cm 간격으로 다시 찍기
    seg=np.r_[P,P[:1]]; L=np.hypot(*np.diff(seg,axis=0).T); s=np.r_[0,np.cumsum(L)]
    q=np.c_[np.interp(np.arange(0,s[-1],0.1),s,seg[:,0]),np.interp(np.arange(0,s[-1],0.1),s,seg[:,1])]
    cen=q.mean(0); d=cen-CAM; d/=np.linalg.norm(d)
    k=max(1,int(step/0.1)); a=q; b=np.roll(q,-k,axis=0); v=b-a; mid=(a+b)/2
    nrm=np.c_[v[:,1],-v[:,0]]; nrm/=np.linalg.norm(nrm,axis=1,keepdims=True)+1e-9
    nrm*=np.sign(((mid-cen)*nrm).sum(1,keepdims=True)+1e-9)          # 바깥쪽
    far=(nrm@d>0.25)
    # 로봇 시점 화면 (오른쪽 = -y, 위 = +x) 에서 방향각, 90° 주기
    ang=np.arctan2(v[:,0],-v[:,1])
    w=np.linalg.norm(v,axis=1)*far
    z=(w*np.exp(4j*ang)).sum()
    yaw=math.degrees(np.angle(z))/4
    conf=abs(z)/max(w.sum(),1e-9)
    return ((yaw+45)%90)-45, conf, cen
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
        y,cf,cen=far_yaw((l==i).astype(np.uint8))
        k=min(K,key=lambda k:math.dist(K[k],cen))
        print(f'{k}: yaw {y:6.1f}°  conf {cf:.2f}')
