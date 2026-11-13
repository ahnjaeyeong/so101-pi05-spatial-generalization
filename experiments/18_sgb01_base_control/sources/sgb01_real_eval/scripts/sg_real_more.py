import sys, os, json, math, glob, numpy as np, pandas as pd, av
sys.path.insert(0, os.path.expanduser("~/so101_runs/main_k8/r1_r2_collection/tools"))
import r12_common as rc, sg_phase, sg_fk, sg_viewer as sv
from PIL import Image, ImageDraw
R=os.path.expanduser("~/so101_runs/main_k8/sgb01_real_eval/eval/rollouts/20261109_100345_10k_t01_02_03_04_05_06_07_08_ft_series")
cfg=rc.load_config(os.path.expanduser("~/so101_runs/main_k8/r1_r2_collection/config/sg50.yaml"))
# 사람 잡는 높이 (예비3 닫기 순간 TCP z)
p3=rc.session_dir("practice/sg50_pilot3"); d3=pd.concat([pd.read_parquet(p) for p in sorted(glob.glob(f"{p3}/dataset/data/*/*.parquet"))]); Z=[]
for ep in range(3,43):
    e=d3[d3.episode_index==ep].sort_values("frame_index"); st=np.stack(e["observation.state"].values); ac=np.stack(e["action"].values)
    ci=sg_phase.analyze(st,ac,30)["_idx"]["close"]; Z.append(sg_fk.fk([st[ci,:5]])[0][0][2]*100)
print(f"사람 닫기 높이 z: 중앙 {np.median(Z):.1f} cm (범위 {min(Z):.1f}…{max(Z):.1f})")
info=json.load(open(f"{R}/dataset/meta/info.json")); em=pd.concat([pd.read_parquet(p) for p in sorted(glob.glob(f"{R}/dataset/meta/episodes/*/*.parquet"))])
df=pd.concat([pd.read_parquet(p) for p in sorted(glob.glob(f"{R}/dataset/data/*/*.parquet"))])
lab=["K5","U7","K2","K8(HU3자리)","K8","HU7","K4","U1"]; ver="P F F F F F P F".split()
out={}
for ep in range(8):
    e=df[df.episode_index==ep].sort_values("frame_index"); st=np.stack(e["observation.state"].values).astype(float); ac=np.stack(e["action"].values).astype(float); n=len(st); t=np.arange(n)/30
    p,_=sg_fk.fk(st[:,:5]); z=p[:,2]*100
    g=ac[:,5]; dg=np.diff(g); sgn=np.sign(dg[np.abs(dg)>0.5]); rev=int(np.sum(sgn[1:]!=sgn[:-1]))
    # 그리퍼 명령 큰 떨림: 0.5 s 창에서 ptp > 10 인 비율
    dither=float(np.mean([np.ptp(g[k:k+15])>10 for k in range(0,n-15,5)]))
    er=em[em.episode_index==ep].iloc[0]; k="observation.images.front"
    pth=f"{R}/dataset/"+info["video_path"].format(video_key=k,chunk_index=int(er[f"videos/{k}/chunk_index"]),file_index=int(er[f"videos/{k}/file_index"]))
    t0=float(er[f"videos/{k}/from_timestamp"]); want=[0,n//4,n//2,3*n//4,n-1]; fr={}
    c=av.open(pth)
    for f in c.decode(video=0):
        fi=int(round((float(f.pts*f.time_base)-t0)*30))
        for w in want:
            if fi>=w and w not in fr: fr[w]=f.to_ndarray(format="rgb24")
        if len(fr)==len(want): break
    c.close()
    cube=[(rc.vision(fr[w],None,cfg).get("front") or {}).get("xy_cm") for w in want]
    moved=None
    if cube[0] and cube[2] and cube[0]!=None: moved=round(math.hypot(cube[2][0]-cube[0][0],cube[2][1]-cube[0][1]),1)
    out[ep]=dict(pos=lab[ep],v=ver[ep],zmin=round(float(z.min()),1),z_t=round(float(t[z.argmin()]),1),rev=rev,dither=round(dither,2),cube_track=cube,moved_mid=moved)
    print(f"ep{ep} {lab[ep]:12s} {ver[ep]} | 그리퍼 끝 최저 z {z.min():5.1f} cm @ {t[z.argmin()]:.1f}s | 그리퍼 명령 방향 바뀜 {rev} · 큰 떨림 시간 비율 {dither:.0%} | front 큐브 0·¼·½·¾·끝: {cube}")
json.dump(out,open(sys.argv[1],"w"),ensure_ascii=False,indent=1,default=float)
