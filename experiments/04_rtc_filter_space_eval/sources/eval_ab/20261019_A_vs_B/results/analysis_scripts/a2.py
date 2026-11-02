import pandas as pd, numpy as np, json, cv2, glob
ST='/home/user/so101_runs/main/redbox_all/eval/eval_ab/20261019_A_vs_B'
cfg=json.load(open(f'{ST}/study.json')); pos=cfg['positions']
T=pd.read_csv(f'{ST}/results/trials.csv', encoding='utf-8-sig')
rows=[]
for _,r in T.iterrows():
    img=cv2.imread(f"{ST}/trials/{r.dir}/start_front.png")  # BGR
    rgb=img[...,::-1].astype(int)
    m=((rgb[...,0]>140)&(rgb[...,1]<90)&(rgb[...,2]<90)&(rgb[...,0]-rgb[...,1]>70)).astype(np.uint8)
    n,lab,st,cen=cv2.connectedComponentsWithStats(m)
    if n>1:
        i=1+int(np.argmax(st[1:,cv2.CC_STAT_AREA])); c=cen[i]; area=st[i,cv2.CC_STAT_AREA]
    else: c=(np.nan,np.nan); area=0
    k=np.array(pos[r.position]['front_px'])
    rows.append(dict(trial=r.trial,cond=r.condition,pos=r.position,rep=r.rep,cx=c[0],cy=c[1],area=area,dx=c[0]-k[0],dy=c[1]-k[1],off=float(np.hypot(c[0]-k[0],c[1]-k[1])),
                     fs=int(r.first_grasp=='success'),ok=int(r.final=='success'),note=str(r.note) if isinstance(r.note,str) else ''))
D=pd.DataFrame(rows); pd.set_option('display.width',250)
print(D.drop(columns='note').round(1).to_string())
D.to_csv('/tmp/claude-2001/-home-user/a503e28d-bef9-4614-b1f4-e109c6c55501/scratchpad/ana/cube_offsets.csv',index=False)
for lo,hi in [(0,15),(15,30),(30,60),(60,999)]:
    s=D[(D.off>=lo)&(D.off<hi)]
    print(f"offset {lo}-{hi}px: n={len(s)} first {s.fs.sum()} final {s.ok.sum()}  (A first {s[s.cond=='A'].fs.sum()}/{(s.cond=='A').sum()}, B first {s[s.cond=='B'].fs.sum()}/{(s.cond=='B').sum()})")
