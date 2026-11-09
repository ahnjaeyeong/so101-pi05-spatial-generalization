import sys, os, json, math, glob, numpy as np, pandas as pd, av
sys.path.insert(0, os.path.expanduser("~/so101_runs/main_k8/r1_r2_collection/tools")); os.environ["R12_CONFIG"]=os.path.expanduser("~/so101_runs/main_k8/r1_r2_collection/config/sg50.yaml")
import r12_common as rc, sg_phase, sg_fk, sg_sticker as ss, sg_viewer as sv
R=os.path.expanduser("~/so101_runs/main_k8/sgft01_real_eval/eval/rollouts/20261109_100345_10k_t01_02_03_04_05_06_07_08_ft_series")
cfg=rc.load_config(os.environ["R12_CONFIG"]); s50=cfg["sg50"]; bx,by=rc.base_xy(cfg)
ref=next(r for r in ss.read_refs()["refs"].values() if r.get("name")=="닫기자리"); P=ss.load_params()
# 사람 기준 pan (예비3 닫기 순간 pan ↔ 큐브 방위) 직선
p3=rc.session_dir("practice/sg50_pilot3"); plan3={int(r["episode_index"]):r for r in rc.read_plan(p3)}
d3=pd.concat([pd.read_parquet(p) for p in sorted(glob.glob(f"{p3}/dataset/data/*/*.parquet"))])
X=[];Y=[]
for ep in range(3,43):
    e=d3[d3.episode_index==ep].sort_values("frame_index"); st=np.stack(e["observation.state"].values); ac=np.stack(e["action"].values)
    ci=sg_phase.analyze(st,ac,30)["_idx"]["close"]; x,y=rc.known_xy(cfg,plan3[ep]["position"]); X.append(-math.degrees(math.atan2(y-by,x-bx))); Y.append(st[ci,0])
a,b=np.polyfit(X,Y,1); res=np.array(Y)-(a*np.array(X)+b); print(f"사람 pan@닫기 = {a:.3f}·pe + {b:.1f} (잔차 sd {res.std():.1f}°)")
info=json.load(open(f"{R}/dataset/meta/info.json")); em=pd.concat([pd.read_parquet(p) for p in sorted(glob.glob(f"{R}/dataset/meta/episodes/*/*.parquet"))])
df=pd.concat([pd.read_parquet(p) for p in sorted(glob.glob(f"{R}/dataset/data/*/*.parquet"))])
lab=["K5","U7","K2","K8(HU3 자리)","K8","HU7","K4","U1"]; verdict="P F F F F F P F".split()
def frames(ep,cam,idxs):
    er=em[em.episode_index==ep].iloc[0]; k=f"observation.images.{cam}"
    p=f"{R}/dataset/"+info["video_path"].format(video_key=k,chunk_index=int(er[f"videos/{k}/chunk_index"]),file_index=int(er[f"videos/{k}/file_index"]))
    t0=float(er[f"videos/{k}/from_timestamp"]); want=sorted(set(idxs)); out={}; c=av.open(p)
    for f in c.decode(video=0):
        fi=int(round((float(f.pts*f.time_base)-t0)*30))
        if fi in want and fi not in out: out[fi]=f.to_ndarray(format="rgb24")
        if fi>want[-1]: break
    c.close(); return out
rows=[]
for ep in range(8):
    e=df[df.episode_index==ep].sort_values("frame_index"); st=np.stack(e["observation.state"].values).astype(float); ac=np.stack(e["action"].values).astype(float); n=len(st); t=np.arange(n)/30
    f0=np.array(__import__("PIL.Image",fromlist=["Image"]).open(f"{R}/start_images/ep{ep:03d}_front.png").convert("RGB")); xy=rc.vision(f0,None,cfg)["front"]["xy_cm"]
    pe=-math.degrees(math.atan2(xy[1]-by,xy[0]-bx)); pan_exp=a*pe+b
    r=sg_phase.analyze(st,ac,30); idx=r.get("_idx") or {}
    g=ac[:,5]; g0=np.median(g[:10])
    # 닫기 시도: 명령이 그때까지 최고값의 70% 아래로 떨어진 순간들 (다시 벌어졌다 또 닫는 것 포함)
    closes=[]; hi=g[0]; armed=False
    for k in range(n):
        if g[k]>g0+8: armed=True; hi=max(hi,g[k])
        if armed and g[k]<0.7*hi and hi>g0+8: closes.append(k); armed=False; hi=g[k]
    # 잡힘 = 닫은 뒤 1 s 동안 그리퍼 상태가 6 넘게 머묾 (큐브 폭)
    held=[k for k in closes if k+30<n and np.median(st[k+20:k+30,5])>6]
    empty=[k for k in closes if k not in held]
    # 닫기 시도마다 손목 큐브 ↔ 주황 프레임, 기울기
    fr=frames(ep,"wrist",[max(0,k-3) for k in closes]) if closes else {}
    tg=[]
    for k in closes:
        w=fr.get(max(0,k-3)); c=ss.target_compare(ss.detect(w,P),ref) if w is not None else None
        tilt=sg_fk.tool_tilt(st[k,:5])[0]-sv.tilt_zero(s50,st[k,0])
        tg.append({"t":round(t[k],1),"pan":round(st[k,0],1),"tilt":round(tilt,1),"ok":(sum(c["ok"].values()) if c else None),"du":(c["du"] if c else None),"dv":(c["dv"] if c else None),"size":(round(c["size"],2) if c else None),"held":k in held})
    # 숄더팬: 처음 정렬 끝 pan vs 사람 기준
    pe_end=idx.get("pan_end"); pan_al=st[pe_end,0] if pe_end is not None else st[int(min(n-1,90)),0]
    lifted = any(st[k+40:k+60,1].mean() < st[k,1]-10 for k in held if k+60<n)
    rows.append(dict(ep=ep,pos=lab[ep],verdict=verdict[ep],len=round(t[-1],1),cube=xy,pe=round(pe,1),pan_expected=round(pan_exp,1),pan_after_align=round(pan_al,1),
                     pan_err=round(pan_al-pan_exp,1),open_s=r.get("open_s"),open_stage=r.get("open_stage"),n_close=len(closes),n_empty=len(empty),n_held=len(held),closes=tg))
    print(f"ep{ep} {lab[ep]:12s} {verdict[ep]} {t[-1]:4.1f}s | 큐브 {xy} pe {pe:+.1f} → 사람 기준 pan {pan_exp:+.1f}, 정렬 뒤 pan {pan_al:+.1f} (차 {pan_al-pan_exp:+.1f}) | 그리퍼 열림 {r.get('open_s')}s [{r.get('open_stage')}] | 닫기 {len(closes)}회 (빈 {len(empty)} · 잡음 {len(held)})")
    for c in tg: print(f"     닫기 {c['t']}s pan {c['pan']} 기울기 {c['tilt']:+} 프레임 {c['ok']}/4 du {c['du']} dv {c['dv']} 크기 {c['size']} {'잡음' if c['held'] else '빈 닫기'}")
json.dump(rows,open(sys.argv[1],"w"),ensure_ascii=False,indent=1,default=float)
