#!/home/user/so101-env/bin/python
"""b10 형식 height*.json → 비교 표 값 (CPU). 시점 = 적용 구간 끝 (res[k][0]), 성분 0 = 바깥, 2 = 높이 (cm).
실물 그리퍼 열림 = 장면 grip ≥ 35 (11_bias_results.md P8 과 같은 기준), 사람 = kind human 전체.
bootstrap 은 ../../scripts/b11_height_summary.py 의 cb (판 단위, seed 0, 2000회) 를 그대로 가져다 씀.
  PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python s1_open_summary.py NAME=height.json [NAME=...] [--out ../data/compare.json]"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
from b11_height_summary import cb  # noqa: E402


def summ(path):
    J = json.load(open(path))
    M, R = J["scenes"], J["res"]
    v = lambda i, k, c: R[i][k][0][c]
    rob = [i for i, m in enumerate(M) if m["kind"] == "robot" and m["grip"] >= 35]
    hum = [i for i, m in enumerate(M) if m["kind"] == "human"]
    g = [M[i]["ep"] for i in rob]
    gh = [M[i]["ep"] for i in hum]
    return dict(
        ckpt=J["ckpt"], n_robot_open=len(rob), n_robot_open_eps=len(set(g)), n_human=len(hum),
        O_out=cb([v(i, "O", 0) for i in rob], g),
        Cc_out=cb([v(i, "Cc", 0) for i in rob], g),
        Cc_up=cb([v(i, "Cc", 2) for i in rob], g),
        ZcCc_out=cb([v(i, "Zc", 0) - v(i, "Cc", 0) for i in rob], g),
        human_Cc_out=cb([v(i, "Cc", 0) for i in hum], gh),
        human_Cc_up=cb([v(i, "Cc", 2) for i in hum], gh),
        scenes_key=[(M[i]["kind"], M[i]["ep"], M[i].get("chunk"), M[i]["frame"]) for i in rob + hum],
    )


def main():
    a = [x for x in sys.argv[1:] if "=" in x and not x.startswith("--")]
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
    S = {}
    f = lambda t: f"{t[0]:+.2f} [{t[1]:+.2f}, {t[2]:+.2f}] 중앙 {t[3]:+.2f} n{t[4]}"
    for x in a:
        n, p = x.split("=", 1)
        S[n] = summ(p)
        s = S[n]
        print(f"{n}: 열림 n{s['n_robot_open']} ({s['n_robot_open_eps']}판) · 사람 n{s['n_human']} · ckpt {s['ckpt']}")
        for k in ("O_out", "Cc_out", "Cc_up", "ZcCc_out", "human_Cc_out", "human_Cc_up"):
            print(f"   {k:13s} {f(s[k])}")
    if out:
        json.dump({k: {kk: vv for kk, vv in v.items() if kk != "scenes_key"} for k, v in S.items()}, open(out, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
