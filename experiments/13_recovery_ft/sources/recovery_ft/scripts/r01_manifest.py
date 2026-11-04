"""r01 학습 manifest 고정 (CPU, 읽기만). 로봇 연결 없음.

승인 목록은 아래 상수로 **명시**한다 (파일이 있다는 이유로 자동 포함하지 않음):
  d2           : main_k8/d2/dataset 의 256 편 전부 (0..255)
  R1           : main_k8/r12_pilot12_r1  ep 4,5,6,7   (ep 0–3 은 녹화 안 지나침 → 사용자 제외 · 재촬영)
  R2 (회복 RC) : main_k8/r12_pilot12_rc  ep 0–10, 12   (ep 11 은 사용자 요청 재촬영 → 제외, ep 12 가 그 재촬영)
r12_pilot12_r2p / r2o 세션 (R2-P 의 첫 빈 파지 뒤 재파지 2 편, 연습 시연) 은 이 manifest 에 넣지 않는다.

교차 확인 (하나라도 어긋나면 종료 코드 2):
  - 각 세션 r12_attempts.jsonl 의 'excluded' 이벤트 집합 = 위 제외 목록
  - qa/r12_pilot_qa.csv 의 excluded 열 = 위 제외 목록
  - 승인 편이 dataset 에 존재, 과제 문장 = d2
태그:
  arm_before_gripper_open : RC 닫힌 그리퍼 시작 편 중 QA Q4 '열기 전 Lift/Elbow 이동' > 5° (동작 순서는 그대로 보존, 기록만)
출력: manifest/training_manifest.csv, manifest/training_manifest.json (+ sha256), stdout 요약
사용: PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python scripts/r01_manifest.py
"""
import hashlib
import json
import re
import sys
from pathlib import Path

import pandas as pd

HOME = Path.home()
K8 = HOME / "so101_runs/main_k8"
RF = K8 / "d2/recovery_ft"
SRC = {
    "d2": dict(root=K8 / "d2/dataset", repo_id="oxr/so101_k8_d2", session=None, approved=list(range(256)), excluded=[]),
    "R1": dict(root=K8 / "r12_pilot12_r1/dataset", repo_id="oxr/so101_k8_r12_pilot12_r1", session=K8 / "r12_pilot12_r1",
               approved=[4, 5, 6, 7], excluded=[0, 1, 2, 3]),
    "R2": dict(root=K8 / "r12_pilot12_rc/dataset", repo_id="oxr/so101_k8_r12_pilot12_rc", session=K8 / "r12_pilot12_rc",
               approved=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12], excluded=[11]),
}
ORDER = ["d2", "R1", "R2"]  # 병합 순서 = 병합 episode 번호 순서
TASK = "pick up the red cube and put it in the brown box"
# RC 시나리오 → 시작 그리퍼 · 오차 종류 (config/r12_recovery.yaml, 12_recovery_usage.md)
RC_KIND = {"RC-F1": ("open", "F1 사선 하강 · 큐브 앞 (손가락 끝이 큐브 윗면 앞)"),
           "RC-F2": ("closed", "F2 이른 닫힘 · 큐브 위 1.5–2.5 cm"),
           "RC-F3-L": ("closed", "F3 좌우 정렬 오차 · 로봇 왼쪽"),
           "RC-F3-R": ("closed", "F3 좌우 정렬 오차 · 로봇 오른쪽")}


def fail(msg):
    print("MANIFEST_FAIL:", msg)
    sys.exit(2)


def main():
    rows = []
    offset = 0
    for g in ORDER:
        s = SRC[g]
        info = json.load(open(s["root"] / "meta/info.json"))
        tasks = pd.read_parquet(s["root"] / "meta/tasks.parquet")
        if list(tasks.index) != [TASK]:
            fail(f"{g} tasks {list(tasks.index)}")
        eps = pd.concat([pd.read_parquet(p) for p in sorted((s["root"] / "meta/episodes").rglob("*.parquet"))]).sort_values("episode_index")
        n = info["total_episodes"]
        if list(eps.episode_index) != list(range(n)):
            fail(f"{g} episode_index not 0..{n - 1}")
        if set(s["approved"]) | set(s["excluded"]) != set(range(n)) or set(s["approved"]) & set(s["excluded"]):
            fail(f"{g} approved ∪ excluded ≠ dataset episodes 0..{n - 1}")
        qa = epcsv = None
        if s["session"] is not None:
            ex_ev = sorted({json.loads(l)["ep"] for l in (s["session"] / "r12_attempts.jsonl").read_text().splitlines()
                            if l.strip() and json.loads(l).get("ev") == "excluded"})
            if ex_ev != s["excluded"]:
                fail(f"{g} attempts 제외 {ex_ev} ≠ 상수 {s['excluded']}")
            qa = pd.read_csv(s["session"] / "qa/r12_pilot_qa.csv").set_index("episode")
            if sorted(qa.index[qa.excluded.astype(bool)]) != s["excluded"]:
                fail(f"{g} QA excluded 열 ≠ 상수")
            epcsv = pd.read_csv(s["session"] / "r12_episodes.csv").set_index("episode_index")
        for _, e in eps.iterrows():
            ei = int(e.episode_index)
            r = dict(group=g, source_repo_id=s["repo_id"], source_root=str(s["root"]), source_episode=ei,
                     merged_episode=offset + ei, length=int(e.length), approved=ei in s["approved"],
                     scenario="", start_gripper="", cube_position="", cube_rotation="", tags="", qa_q4_detail="")
            if g != "d2":
                r["scenario"] = epcsv.loc[ei, "scenario_id"]
                r["cube_position"] = epcsv.loc[ei, "cube_position"]
                r["cube_rotation"] = epcsv.loc[ei, "cube_rotation"]
                tags = []
                if g == "R1":
                    r["start_gripper"] = "closed" if float(epcsv.loc[ei, "start_gripper_state"]) < 15 else "open"
                    tags.append(f"wrist_start={epcsv.loc[ei, 'wrist_cube_visibility']}")
                else:
                    r["start_gripper"] = RC_KIND[r["scenario"]][0]
                    q4 = str(qa.loc[ei, "q4_detail"]) if ei in qa.index else ""
                    r["qa_q4_detail"] = q4 if q4 != "nan" else ""
                    m = re.search(r"열기 전 Lift/Elbow 이동 ([0-9.]+)°", q4)
                    if m and float(m.group(1)) > 5:
                        tags.append(f"arm_before_gripper_open({m.group(1)}deg)")
                if not r["approved"]:
                    tags.append("EXCLUDED_by_user")
                r["tags"] = ";".join(tags)
            rows.append(r)
        offset += n
    M = pd.DataFrame(rows)
    use = M[M.approved]
    cnt = use.group.value_counts().to_dict()
    if cnt != {"d2": 256, "R1": 4, "R2": 12}:
        fail(f"승인 편수 {cnt}")
    M.to_csv(RF / "manifest/training_manifest.csv", index=False)
    body = dict(created_note="frozen training manifest — d2 256 + R1 4 + R2(RC) 12 = 272", task=TASK, merge_order=ORDER,
                sources={g: dict(repo_id=SRC[g]["repo_id"], root=str(SRC[g]["root"]), approved=SRC[g]["approved"], excluded=SRC[g]["excluded"]) for g in ORDER},
                train_episodes_merged=[int(x) for x in use.merged_episode],
                excluded_merged=[int(x) for x in M[~M.approved].merged_episode],
                frames=dict(use.groupby("group").length.sum().astype(int)), total_merged_episodes=len(M))
    js = json.dumps(body, ensure_ascii=False, indent=1, default=int)
    (RF / "manifest/training_manifest.json").write_text(js)
    h = hashlib.sha256(js.encode()).hexdigest()
    hc = hashlib.sha256((RF / "manifest/training_manifest.csv").read_bytes()).hexdigest()
    (RF / "manifest/training_manifest.sha256").write_text(f"{h}  training_manifest.json\n{hc}  training_manifest.csv\n")
    print(use.groupby("group").agg(eps=("length", "size"), frames=("length", "sum")))
    print(M[M.group != "d2"][["group", "source_episode", "merged_episode", "length", "approved", "scenario", "start_gripper", "cube_position", "tags"]].to_string())
    print("train episodes", len(body["train_episodes_merged"]), "excluded merged", body["excluded_merged"])
    print("manifest json sha256", h)
    print("MANIFEST_OK")


if __name__ == "__main__":
    main()
