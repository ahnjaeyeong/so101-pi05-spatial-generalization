#!/home/user/so101-env/bin/python
"""접근 중 좌우 · 앞뒤 반응 재추론 (GPU, 로봇 · 카메라 연결 없음, 원본 읽기만). 2026-11-12.
질문: 정책이 접근하는 동안 손목 화면의 큐브 위치를 보고 경로를 고치는가.
장면: (실물) sgb01 010000 run 20261112_093536 diag chunk 중 그리퍼 열림 · 큐브 크기 0.55–0.95 (판마다 최대 12) / (사람) 예비3 ep3–42 닫기 150 · 240 프레임 전.
조건: 손목 영상에서 큐브만 화면 좌우 (u) 또는 세로 (v) 로 ±32 · ±64 px 옮김 (집게 · 배경 그대로, 원래 자리는 inpaint). prefix 없음, noise 8 평균.
측정: 예측 끝 이동 (바깥 · 옆 · 높이 cm) 시점 20 · 49, 숄더팬 명령 변화 (°). 기울기 = 옮긴 양 (화면 비) 에 대한 직선 맞춤.
  OD_CK=<pretrained_model> PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 nice -n 10 ~/so101-env/bin/python p2_approach_probe.py → ../data/approach_probe.json
"""
import json, os, pathlib, sys, time
import cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
OD = os.path.expanduser("~/so101_runs/main_k8/sgft01_real_eval/overshoot_diag")
os.environ.setdefault("OD_TAG", "unused_approach_probe")
sys.path.insert(0, f"{OD}/sgb01/scripts"); sys.path.insert(1, f"{OD}/scripts")
import b10_height as B10  # noqa: E402
R2, BB, O = B10.R2, B10.BB, B10.O
R = os.path.expanduser("~/so101_runs/main_k8/sgb01_real_eval/eval/rollouts/20261112_093536_10k_t01_02_03_04_05_06_07_08_ft_series")
LAB = "K5 U7 K2 HU3 K8 HU7 K4 U1".split(); VER = "F F F P F F P P".split()
D2DS = {1: 0, 2: 1, 3: 2, 4: 3, 6: 4, 7: 5, 8: 6, 9: 7}
# 2026-11-13 다른 실물 run 에도 쓰게: PROBE_RUN (run 폴더) · PROBE_VERS ("P P F …") · PROBE_SIZE ("0.55,1.12") · PROBE_MAXN · PROBE_NO_HUMAN=1 · PROBE_EDGE=1 (끝에 걸린 장면도)
if os.environ.get("PROBE_RUN"):
    R = os.path.expanduser(os.environ["PROBE_RUN"]); VER = os.environ["PROBE_VERS"].split(); D2DS = None
SZ = tuple(float(x) for x in os.environ.get("PROBE_SIZE", "0.55,0.95").split(","))
MAXN = int(os.environ.get("PROBE_MAXN", 12))
SH = [("u", -64), ("u", -32), ("0", 0), ("u", 32), ("u", 64), ("v", -48), ("v", -24), ("v", 24), ("v", 48)]
OUTF = os.path.join(HERE, "..", "data", "approach_probe" + ("_" + os.environ["OUT_TAG"] if os.environ.get("OUT_TAG") else "") + ".json")   # OUT_TAG: 다른 체크포인트 결과를 따로 저장


def shift_cube(w, det, dx, dy):
    if dx == 0 and dy == 0: return w
    cx, cy = det["cube"]["u"] * w.shape[1], det["cube"]["v"] * w.shape[0]
    hull = np.array(det["cube"]["hull"], float).reshape(-1, 2)
    m0 = np.zeros(w.shape[:2], np.uint8); cv2.fillConvexPoly(m0, ((hull - [cx, cy]) * 1.25 + [cx, cy]).astype(np.int32), 255)
    bg = cv2.inpaint(w, cv2.dilate(m0, np.ones((5, 5), np.uint8)), 7, cv2.INPAINT_TELEA)
    mf = cv2.GaussianBlur(m0.astype(np.float32) / 255.0, (0, 0), 2)
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    P = cv2.warpAffine(w, M, (w.shape[1], w.shape[0]), borderMode=cv2.BORDER_REPLICATE); mk = cv2.warpAffine(mf, M, (w.shape[1], w.shape[0]))[..., None]
    return (bg * (1 - mk) + P * mk).astype(np.uint8)


def main():
    sys.path.insert(0, R2.VD)
    import v_common as V
    import v02_engine as E
    V.CKPT = pathlib.Path(R2.CK); print("CKPT", V.CKPT, flush=True); t0 = time.time()
    S = []
    C = [json.loads(x) for x in open(f"{R}/diag/chunks.jsonl") if x.strip()]
    if D2DS is None:   # diag 판 번호 → dataset 판 (첫 chunk 관절값 = 그 판 첫 프레임, p1 과 같은 방법)
        info_, em_, df_ = O.load_ds(f"{R}/dataset")
        S0 = {ep: np.stack(df_[df_.episode_index == ep].sort_values("frame_index")["observation.state"].values)[0] for ep in sorted(set(df_.episode_index))}
        first = {}
        for m in C: first.setdefault(m["episode"], m)
        m2 = {}
        for de, m in first.items():
            err = {ep: float(np.abs(np.array(m["obs_state"]) - S0[ep]).max()) for ep in S0 if ep not in m2.values()}
            if err and min(err.values()) < 1.0: m2[de] = min(err, key=err.get)
        print("diag→dataset", m2, flush=True)
    else:
        m2 = D2DS
    for de, ep in m2.items():
        cand = []
        for m in [m for m in C if m["episode"] == de]:
            if m["obs_state"][5] < 35: continue
            w = R2.rgb(f"{R}/diag/obs/c{m['chunk_id']:05d}_wrist.png"); det = O.ss.detect(w, O.PRM); c = O.ss.target_compare(det, O.ref)
            if c is None or not (SZ[0] <= c["size"] <= SZ[1]) or (c["edge"] and not os.environ.get("PROBE_EDGE")): continue
            cand.append(dict(kind="robot", ep=ep, lab=LAB[ep], verdict=VER[ep], chunk=m["chunk_id"], q=np.array(m["obs_state"], float), w=w,
                             f=R2.rgb(f"{R}/diag/obs/c{m['chunk_id']:05d}_front.png"), det=det, c=c))
        if len(cand) > MAXN: cand = [cand[i] for i in np.linspace(0, len(cand) - 1, MAXN).astype(int)]
        S += cand; print(LAB[ep], len(cand), flush=True)
    info, em, d3 = O.load_ds(f"{O.P3}/dataset")
    for ep in ([] if os.environ.get("PROBE_NO_HUMAN") else range(3, 43)):
        e = d3[d3.episode_index == ep].sort_values("frame_index"); st = np.stack(e["observation.state"].values).astype(float); ac = np.stack(e["action"].values).astype(float)
        ci = O.sg_phase.analyze(st, ac, 30)["_idx"]["close"]; want = [ci - b for b in (150, 240) if ci - b >= 0]
        fw = O.frames(f"{O.P3}/dataset", info, em, ep, want); ff = O.frames(f"{O.P3}/dataset", info, em, ep, want, cam="front")
        for k in want:
            det = O.ss.detect(fw[k], O.PRM); c = O.ss.target_compare(det, O.ref)
            if c is None or c["edge"] or st[k, 5] < 35: continue
            S.append(dict(kind="human", ep=ep, lab="H", verdict="H", chunk=None, q=st[k], w=fw[k], f=ff[k], det=det, c=c, back=ci - k))
    eng = E.Engine(n_noise=8); print(f"엔진 {time.time() - t0:.0f}s · 장면 {len(S)}", flush=True)
    out = []
    for n, s in enumerate(S):
        imgs = [(s["f"], shift_cube(s["w"], s["det"], dx if ax == "u" else 0, dx if ax == "v" else 0)) for ax, dx in SH]
        A = eng.run(s["q"], imgs)                                   # (9, 8, 50, 6)
        r = dict(kind=s["kind"], ep=s["ep"], lab=s["lab"], verdict=s["verdict"], chunk=s["chunk"], du=s["c"]["du"], dv=s["c"]["dv"], size=s["c"]["size"], grip=float(s["q"][5]))
        r["disp20"] = [B10.disp(A[i], s["q"], (20,))[0].tolist() for i in range(len(SH))]
        r["disp49"] = [B10.disp(A[i], s["q"], (49,))[0].tolist() for i in range(len(SH))]
        r["pan20"] = [float(A[i][:, 20, 0].mean() - s["q"][0]) for i in range(len(SH))]
        r["pan49"] = [float(A[i][:, 49, 0].mean() - s["q"][0]) for i in range(len(SH))]
        out.append(r)
        if n % 20 == 0: print(f"  {n}/{len(S)} · {time.time() - t0:.0f}s", flush=True)
    json.dump(dict(ckpt=R2.CK, shifts=SH, scenes=out, sec=round(time.time() - t0, 1)), open(OUTF, "w"), default=float)
    print("P2_DONE", f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
