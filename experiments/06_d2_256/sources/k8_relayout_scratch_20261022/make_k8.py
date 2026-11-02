import cv2,numpy as np,json
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
plt.rcParams['font.family']='NanumSquare'; plt.rcParams['axes.unicode_minus']=False
S='/tmp/claude-2001/-home-user/401de9d0-444f-477e-991b-156d7183fd3b/scratchpad/k8'
d=json.load(open(f'{S}/cam_fit.json')); G=d['G']; px=d['px']
C=np.array([8.5,-11.5])   # box robot-side wall outer face, robot-right end, grid frame (origin K2). x: user K2->wall 8.5; y: fit5 box centre +0.2..0.3
Kphoto={k:(np.array(v)-C).round(2) for k,v in G.items()}          # cubes as photographed (K4-K7 9 cm)
Gnew=dict(G); Gnew['K7']=(-17.0,15); Gnew['K8']=(-17.0,-15)       # user 10-22: K4-K7 -> 8.5 cm
K={k:(np.array(v)-C).round(2) for k,v in Gnew.items()}
P1280=np.array([px[k] for k in G]); P640=(P1280-[160,0])/1.5
Hc,_=cv2.findHomography(np.array([Kphoto[k] for k in G]),P640)
Hc/=Hc[2,2]
r=cv2.perspectiveTransform(np.array([list(Kphoto.values())],float),Hc)[0]-P640
Kpx=cv2.perspectiveTransform(np.array([list(K.values())],float),Hc)[0]
print('H_cm_to_px (640x480, C frame):',json.dumps(Hc.round(6).tolist()))
print('reproj px (640):',np.hypot(*r.T).round(2),'rms',np.sqrt((r**2).sum(1).mean()).round(2))
px_per_cm=[np.linalg.norm(cv2.perspectiveTransform(np.array([[K[k]+[0,0.5],K[k]-[0,0.5]]],float),Hc)[0].ptp(0)) for k in G]
print('px/cm along y at K (640):',np.round(px_per_cm,1))
for k in G: print(k,'xy_cm',K[k].tolist(),'front_px',Kpx[list(G).index(k)].round().astype(int).tolist())
json.dump({'C_grid':C.tolist(),'K':{k:v.tolist() for k,v in K.items()},'H640':Hc.tolist(),'front_px':{k:Kpx[i].round().astype(int).tolist() for i,k in enumerate(G)}},open(f'{S}/k8_result.json','w'),indent=1)
# ---- plan view (x forward = toward box -> up; y left -> left), robot side at bottom
fig,ax=plt.subplots(figsize=(8,8))
box=np.array([[0,0],[13,0],[13,23.5],[0,23.5],[0,0]])  # outer: x 0..13 (inner 12 + walls), y 0..23.5
ax.fill(box[:,1],box[:,0],color='#c8a070',alpha=.35); ax.plot(box[:,1],box[:,0],color='#8a5a2b')
ax.plot([0,23.5],[0,0],color='#c0392b',lw=3,label='상자 앞 벽 (로봇 쪽) 바깥면')
ax.plot(0,0,'ko'); ax.annotate('C (0,0)',(0,0),(-1.2,1),fontsize=11,ha='right')
for k,v in K.items():
    x,y=v; ax.add_patch(plt.Rectangle((y-1.25,x-1.25),2.5,2.5,fc='#e74c3c',alpha=.85))
    ax.annotate(f'{k}\n({x:.1f}, {y:.1f})',(y,x),(y,x-3.6),ha='center',fontsize=10)
ax.set_xlim(32,-8); ax.set_ylim(-31,16); ax.set_aspect('equal'); ax.grid(alpha=.3)
ax.set_xlabel('y (cm, + = 로봇 왼쪽)'); ax.set_ylabel('x (cm, + = 상자 쪽)')
ax.text(12,-29.5,'[로봇 쪽]',ha='center',fontsize=12)
ax.set_title('K1–K8 평면도 (2026-10-22) · 원점 C = 상자 앞 벽 바깥면 로봇 기준 오른쪽 끝\n격자 = 사용자 실측 (가로 15, 세로 8.5·8.5), K2–상자 앞 벽 8.5 실측, 좌우 원점은 화면 추정 (±0.5 cm)',fontsize=10)
ax.legend(loc='upper right',fontsize=9)
fig.tight_layout(); fig.savefig('/home/user/Desktop/redbox_K8_위치_평면도.png',dpi=110)
# ---- camera check (1280x720): project K + 5 cm grid via H (scaled to 1280)
S2=np.array([[1.5,0,160],[0,1.5,0],[0,0,1]]); H12=S2@Hc
img=cv2.imread(f'{S}/front_1280.png')
def P(pts): return cv2.perspectiveTransform(np.array([pts],float),H12)[0]
for gx in np.arange(-30,-4.9,5):
    a,b=P([[gx,-8],[gx,32]]); cv2.line(img,tuple(a.astype(int)),tuple(b.astype(int)),(225,225,225),1)
for gy in np.arange(-5,30.1,5):
    a,b=P([[-30,gy],[-5,gy]]); cv2.line(img,tuple(a.astype(int)),tuple(b.astype(int)),(225,225,225),1)
for k,v in K.items():
    q=P([v])[0].astype(int); o=P1280[list(G).index(k)].astype(int)
    cv2.drawMarker(img,tuple(q),(255,90,0),cv2.MARKER_CROSS,22,2); cv2.circle(img,tuple(o),4,(0,255,0),-1)
    cv2.putText(img,k,(q[0]-25,q[1]-38),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),5); cv2.putText(img,k,(q[0]-25,q[1]-38),cv2.FONT_HERSHEY_SIMPLEX,1,(200,60,0),2)
cv2.rectangle(img,(0,0),(1000,60),(255,255,255),-1)
cv2.putText(img,'blue + = K (K7/K8 at new 8.5 cm row), green dot = cube centre in this photo',(8,24),cv2.FONT_HERSHEY_SIMPLEX,0.65,(0,0,0),2)
cv2.putText(img,'gray grid = 5 cm (C frame), drawn only up to x=-5 (box area not valid for this H)',(8,50),cv2.FONT_HERSHEY_SIMPLEX,0.65,(0,0,0),2)
cv2.imwrite('/home/user/Desktop/redbox_K8_위치_카메라확인.png',img)
