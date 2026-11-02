import cv2,numpy as np,sys
sys.path.insert(0,'/home/user/so101_boxpick/scripts'); import layout_plan as lp
cfg=lp.load_config('/home/user/so101_boxpick/config/redbox8_layouts.yaml'); H=np.array(cfg['camera']['front_640x480']['H_cm_to_px']); Hi=np.linalg.inv(H)
f=cv2.imread(sys.argv[1]); hsv=cv2.cvtColor(f,cv2.COLOR_BGR2HSV)
def mask(rngs):
    m=np.zeros(f.shape[:2],np.uint8)
    for r in rngs: m|=cv2.inRange(hsv,(r['h'][0],r['s'][0],r['v'][0]),(r['h'][1],r['s'][1],r['v'][1]))
    return m
cols=cfg['detection']['colors']; m=mask(cols['red'])|mask(cols['orange'])|mask(cols['yellow'])|mask(cols['blue'])|mask(cols['green'])
m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
n,l,st,cc=cv2.connectedComponentsWithStats(m)
def yaw(pts):
    cm=cv2.perspectiveTransform(pts.reshape(-1,1,2).astype(float),Hi).reshape(-1,2)
    q=np.c_[-cm[:,1],cm[:,0]].astype(np.float32)   # 로봇 시점 화면: 오른쪽 = -y, 위 = +x (상자 쪽)
    (_, _),(w,h),a=cv2.minAreaRect(q)
    return ((a+45)%90)-45,(w,h)
for i in range(1,n):
    if st[i,4]<300 or st[i,1]>350: continue
    blob=(l==i).astype(np.uint8)
    cs,_=cv2.findContours(blob,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
    a_all,wh=yaw(cs[0])
    v=hsv[...,2][blob>0]; thr,_=cv2.threshold(v.reshape(-1,1),0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    top=((hsv[...,2]>thr)&(blob>0)).astype(np.uint8); top=cv2.morphologyEx(top,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
    n2,l2,st2,_=cv2.connectedComponentsWithStats(top); j=1+np.argmax(st2[1:,4])
    ct,_=cv2.findContours((l2==j).astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
    a_top,wh2=yaw(ct[0])
    print('blob',cc[i].round(0),'area',st[i,4],'all %5.1f'%a_all,np.round(wh,2),'| top %5.1f'%a_top,np.round(wh2,2),'top area',st2[j,4])
