import json,os,sys,math,cv2,numpy as np
sys.path.insert(0,'scripts'); import layout_plan as lp, cube_angle as ca, servo_plot as sp
S=sys.argv[1]; sess=sys.argv[2]
cfg=lp.load_config('config/redbox8_layouts.yaml'); H=np.array(cfg['camera']['front_640x480']['H_cm_to_px']); cxy=cfg['camera']['front_640x480']['camera_xy_cm']
sd=lp.session_dir(sess); rows=lp.read_layout(sd+'/layout.csv'); D=json.load(open(sd+'/qa/servo_data.json'))
out=[]
for e in D['episodes']:
    i=e['ep']; r=rows[i]; o=[x for x in lp.parse_objects(r['objects']) if x['type']=='red_cube'][0]
    img=cv2.imread(f'{S}/ff/ep{i:03d}.png'); hsv=cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
    m=cv2.inRange(hsv,(160,90,60),(180,255,255))|cv2.inRange(hsv,(0,90,60),(1,255,255))
    m=cv2.morphologyEx(cv2.morphologyEx(m,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5))),cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(9,9)))
    yaw,why=ca.measure_at(m,H,cxy,(o['x'],o['y']))
    s=np.array(e['s']); gi=sp.grasp_index(s)
    out.append({'ep':i,'K':o['pos'],'x':o['x'],'y':o['y'],'plan':lp.parse_angles(r['angles'])[o['pos']],'yaw':yaw,'why':why if yaw is None else '',
                'gi':gi,'pan':float(s[gi,0]) if gi is not None else None,'roll':float(s[gi,4]) if gi is not None else None,'roll0':float(s[0,4]),
                'excluded':e['excluded']})
json.dump(out,open(f'{S}/collect.json','w'),indent=0); print(len(out),'eps; no grasp',sum(o['gi'] is None for o in out),'; no yaw',[(o['ep'],o['why']) for o in out if o['yaw'] is None])
