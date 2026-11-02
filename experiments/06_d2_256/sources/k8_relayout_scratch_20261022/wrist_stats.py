import glob,os,sys,numpy as np,pandas as pd
sessions=sys.argv[1:]
rows=[]
for s in sessions:
    d=os.path.expanduser(f'~/so101_runs/{s}/dataset')
    for p in sorted(glob.glob(f'{d}/data/*/*.parquet')):
        df=pd.read_parquet(p,columns=['episode_index','frame_index','observation.state','action'])
        for e,g in df.groupby('episode_index'):
            g=g.sort_values('frame_index'); st=np.stack(g['observation.state'].values)[:,4]; ac=np.stack(g['action'].values)[:,4]
            r={'session':s.split('/')[-1],'ep':e}
            for name,x in (('st',st),):
                v=np.abs(np.diff(x))*30
                r['p99spd']=np.percentile(v,99); r['maxspd']=v.max()
                for w in (0.5,1.0):
                    n=int(w*30); m=max(np.ptp(x[i:i+n+1]) for i in range(0,len(x)-n))
                    r[f'win{w}']=m
                r['range']=np.ptp(x); r['net']=abs(x[-1]-x[0])
            rows.append(r)
D=pd.DataFrame(rows)
pd.set_option('display.width',200)
print(D.groupby('session')[['p99spd','maxspd','win0.5','win1.0','range']].describe(percentiles=[.5,.9,.95]).T.round(0).to_string())
D.to_csv('/tmp/claude-2001/-home-user/401de9d0-444f-477e-991b-156d7183fd3b/scratchpad/k8/wrist_stats.csv',index=False)
