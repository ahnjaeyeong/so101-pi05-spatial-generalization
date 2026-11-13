#!/home/user/so101-env/bin/python
"""멈춘 장면 재추론 (GPU, 로봇 · 카메라 연결 없음, 원본 읽기만). 2026-11-12.
대상: sgb01 010000 실물 run 20261112_093536 의 diag chunk 중 '그리퍼 열림 (obs grip >= 35) · 손목에 큐브 보임 (size >= 0.75) · 첫 held 닫기 전'.
조건: pf = 실물 그대로 (저장 prefix · applied_delay, noise bank 8) / O · Cc · Zc = prefix 없음, 손목 영상 원래 · 큐브만 닫기자리 중심 · 중심+크기 1 (b10 variants 그대로).
측정: 예측 끝 이동 (바깥 · 옆 · 높이 cm, 넣은 관절값 기준) 시점 h = applied_delay+20 · 49, 그리퍼 명령 (chunk 안 최소 − 지금 값, 8 넘게 내려간 noise 비율 = 닫기 비율).
  OD_CK=<pretrained_model> PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 nice -n 10 ~/so101-env/bin/python p1_stuck_probe.py → ../data/stuck_probe.json
"""
import json, os, pathlib, sys, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
OD = os.path.expanduser("~/so101_runs/main_k8/sgft01_real_eval/overshoot_diag")
os.environ.setdefault("OD_TAG", "unused_stuck_probe")
sys.path.insert(0, f"{OD}/sgb01/scripts")
sys.path.insert(1, f"{OD}/scripts")
import b10_height as B10  # noqa: E402  (variants · disp 재사용; main 은 부르지 않음)
R2, BB, O = B10.R2, B10.BB, B10.O
R = os.path.expanduser("~/so101_runs/main_k8/sgb01_real_eval/eval/rollouts/20261112_093536_10k_t01_02_03_04_05_06_07_08_ft_series")
LAB = "K5 U7 K2 HU3 K8 HU7 K4 U1".split(); VER = "F F F P F F P P".split()
T_HELD = [None, 21.2, 55.9, 17.8, None, 49.9, 27.8, 34.5]   # 첫 held 닫기 (s), 2026-11-12 trace 분석
MAXN = 30
OUTF = os.path.join(HERE, "..", "data", "stuck_probe" + ("_" + os.environ["OUT_TAG"] if os.environ.get("OUT_TAG") else "") + ".json")   # OUT_TAG: 다른 체크포인트 결과를 따로 저장


def main():
    sys.path.insert(0, R2.VD)
    import sg_vis_eval as VE
    import v_common as V
    import v02_engine as E
    V.CKPT = pathlib.Path(R2.CK)
    print("CKPT", V.CKPT, flush=True)
    C = [json.loads(x) for x in open(f"{R}/diag/chunks.jsonl") if x.strip()]
    info, em, df = O.load_ds(f"{R}/dataset")
    S0 = {ep: np.stack(df[df.episode_index == ep].sort_values("frame_index")["observation.state"].values)[0] for ep in range(8)}
    first = {}
    for m in C: first.setdefault(m["episode"], m)
    d2ds = {}
    for de, m in first.items():
        err = {ep: float(np.abs(np.array(m["obs_state"]) - S0[ep]).max()) for ep in range(8) if ep not in d2ds.values()}
        ep = min(err, key=err.get)
        n_ch = sum(1 for c in C if c["episode"] == de); n_ds = int((df.episode_index == ep).sum())
        if err[ep] < 1.0 and abs(n_ch * 20 - n_ds) < 120: d2ds[de] = ep
        print("diag ep", de, "chunks", n_ch, "→ ds ep", d2ds.get(de), "start err", round(err[ep], 2), "frames", n_ds, flush=True)
    t0 = time.time(); scenes = []
    for de, ep in d2ds.items():
        cs = [m for m in C if m["episode"] == de]
        tick0 = cs[0]["obs_tick"]
        cand = []
        for m in cs:
            t = (m["obs_tick"] - tick0) / 30.0
            if m["obs_state"][5] < 35 or (T_HELD[ep] is not None and t >= T_HELD[ep]): continue
            w = R2.rgb(f"{R}/diag/obs/c{m['chunk_id']:05d}_wrist.png")
            e = O.err_of(w)
            if np.isnan(e["du"]) or e["size"] < 0.75: continue
            cand.append((m, t, e))
        if len(cand) > MAXN: cand = [cand[i] for i in np.linspace(0, len(cand) - 1, MAXN).astype(int)]
        scenes += [(ep, m, t, e) for m, t, e in cand]
        print(LAB[ep], VER[ep], "scenes", len(cand), flush=True)
    eng = E.Engine(n_noise=8)
    print(f"엔진 {time.time() - t0:.0f}s · 장면 {len(scenes)}", flush=True)
    rep = []
    for ep, m, t, e in scenes[:4]:
        z = np.load(f"{R}/diag/chunks/c{m['chunk_id']:05d}.npz")
        f = R2.rgb(f"{R}/diag/obs/c{m['chunk_id']:05d}_front.png"); w = R2.rgb(f"{R}/diag/obs/c{m['chunk_id']:05d}_wrist.png")
        kw = dict(prefix=z["prefix"], delay=m.get("applied_delay")) if m.get("has_prefix") else {}
        A = eng.run(m["obs_state"], [(f, w)], noise=z["noise"], **kw)[0, 0]
        rep.append(float(np.abs(A - z["processed"]).max()))
    print("재현 (저장 chunk 와 최대 차 °)", [round(x, 3) for x in rep], flush=True)
    out = []
    def meas(A, q, h):
        d = B10.disp(A, q, (h, 49))                        # (2, 3)
        g = A[:, :, 5]; drop = g.min(1) - q[5]
        return dict(disp_h=d[0].tolist(), disp_49=d[1].tolist(), grip_min_minus_now=float(drop.mean()), close_frac=float((drop < -8).mean()),
                    grip_h_minus_now=float(g[:, h].mean() - q[5]))
    for n, (ep, m, t, e) in enumerate(scenes):
        cid = m["chunk_id"]; z = np.load(f"{R}/diag/chunks/c{cid:05d}.npz")
        f = R2.rgb(f"{R}/diag/obs/c{cid:05d}_front.png"); w = R2.rgb(f"{R}/diag/obs/c{cid:05d}_wrist.png")
        q = np.array(m["obs_state"], float); h = min(49, int(m.get("applied_delay") or 0) + 20)
        kw = dict(prefix=z["prefix"], delay=m.get("applied_delay")) if m.get("has_prefix") else {}
        r = dict(ep=ep, lab=LAB[ep], verdict=VER[ep], chunk=cid, t=round(t, 2), h=h, grip=float(q[5]), z=float(BB.tip(q)[0][2]),
                 du=e["du"], dv=e["dv"], size=e["size"], edge=e["edge"])
        r["pf"] = meas(eng.run(q, [(f, w)], **kw)[0], q, h)
        imgs, inf = B10.variants(w, VE)
        if imgs is not None:
            A = eng.run(q, [(f, imgs[k]) for k in ("O", "Cc", "Zc")])
            for i, k in enumerate(("O", "Cc", "Zc")): r[k] = meas(A[i], q, h)
            r["scale"] = inf["scale"]
        out.append(r)
        if n % 20 == 0: print(f"  {n}/{len(scenes)} · {time.time() - t0:.0f}s", flush=True)
    json.dump(dict(ckpt=R2.CK, run=R, diag2ds=d2ds, replay=rep, scenes=out, sec=round(time.time() - t0, 1)), open(OUTF, "w"), ensure_ascii=False, default=float)
    print("P1_DONE", f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
