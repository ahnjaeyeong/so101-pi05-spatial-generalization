"""record_ui 녹화 시작(빨강) 배너 미리보기 — config/redbox8_layouts.yaml K1–K8. 화면 출력만 (로봇·카메라·파일 안 건드림)."""
import os, sys, copy
sys.dont_write_bytecode = True
BOX = os.path.expanduser("~/so101_boxpick")
sys.path.insert(0, os.path.join(BOX, "scripts"))
import yaml, layout_plan as lp, record_ui as ru

cfg = lp.load_config(os.path.join(BOX, "config/redbox8_layouts.yaml"))
cfg = copy.deepcopy(cfg)
# 미리보기용 그룹 (설정 파일에는 안 씀)
cfg["groups"] = {
    "t1_known": {"task": "t1", "mode": "known", "episodes": 16, "seed": 1, "session": "practice/preview_t1k", "repo_id": "x/p1"},
    "t2_known": {"task": "t2", "mode": "known", "episodes": 28, "seed": 2, "session": "practice/preview_t2k", "repo_id": "x/p2"},
    "t3_known": {"task": "t3", "mode": "known", "episodes": 64, "seed": 3, "session": "practice/preview_t3k", "repo_id": "x/p3"},
    "t3_random": {"task": "t3", "mode": "random", "episodes": 64, "seed": 4, "session": "practice/preview_t3r", "repo_id": "x/p4"},
}
cfg["tasks"]["t2"]["red_counts"] = {2: 28}  # 미리보기용 (현재 설정 값은 K 8개와 안 맞음)
tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_preview_cfg.yaml")
with open(tmp, "w") as f:
    yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)

def show(group, ttime, kinds=("REC",)):
    meta, rows = lp.build(tmp, group, None, True, None)
    layout = {"path": "", "rows": rows, "meta": meta, "lp": lp, "describe": lambda r, m=meta: lp.describe_row(r, m["resolved"])}
    ui = ru.UI([f"--dataset.num_episodes={len(rows)}", f"--dataset.episode_time_s={ttime}", "--dataset.reset_time_s=30"], layout)
    ui.episode = ep = 0
    for kind in kinds:
        print(f"\n── {group} · {kind} (미리보기) ──", flush=True)
        if kind == "REC":
            ui.banner(ru.REC, f"▶ 녹화 시작 ({ep + 1}번째 / {len(rows)})",
                      f"episode {ep} · {ttime}초 · 끝나면 →  다시 ←  종료 Esc", ui.layout_rows(ep))
        elif kind == "RESET":
            ui.banner(ru.RESET, "↺ 환경 초기화 — 준비되면 →", f"{ui.reset_time:.0f}초 안에 준비 · 다시 녹화 ←  종료 Esc",
                      ui.layout_rows(ep + 1, f"다음 판 (episode {ep + 1}) — "))
        elif kind == "DONE":
            ui.banner(ru.DONE, "✅ 녹화 종료 — 이번 실행 16개 저장")

which = sys.argv[1:] or ["t1_known", "t3_known", "reset", "done"]
for w in which:
    if w == "reset":
        show("t3_known", 45, ("RESET",))
    elif w == "done":
        show("t1_known", 45, ("DONE",))
    else:
        show(w, 75 if w.startswith("t2") else 45)
print()
