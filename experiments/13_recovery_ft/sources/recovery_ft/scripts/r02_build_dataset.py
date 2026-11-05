"""r02 학습용 병합 사본 만들기 (CPU). 로봇 연결 없음. 원본 3 개 dataset 은 읽기만 (전후 sha256 비교).

처음에는 lerobot `aggregate_datasets(concatenate_videos=False, concatenate_data=False)` 를 썼으나 실패했다:
d2 의 meta/episodes 는 file-000.parquet 하나 (256 줄) 인데 그 안의 'meta/episodes/file_index' 열이 0–3 이다
(d2 를 병합할 때 4 개 원본 값이 그대로 남은 기존 특성). aggregate_metadata 가 이 열을 믿고 file-001 을 찾다가 FileNotFoundError.
그래서 aggregate 의 파일 단위 처리 (update_data_df 와 같은 번호 이동 + `to_parquet_one_row_group_per_episode`) 를 그대로 따라
아래처럼 단순하게 병합한다 (모든 원본은 chunk-000 만 씀 — 확인 후 진행):
  - 영상: 원본 mp4 를 바이트 그대로 복사, 카메라별 file 번호만 이어 붙임 (재인코딩 · 이어붙이기 없음).
           episode meta 의 videos/*/from_timestamp · to_timestamp 는 원본 값 그대로, file_index 만 이동.
  - 데이터: 원본 data parquet 하나 → 사본 parquet 하나. episode_index += 앞 dataset 편수, index += 앞 dataset 프레임 수.
           task 는 세 dataset 모두 같은 문장 1 개 (task_index 0) — 확인 후 그대로.
  - meta/episodes: 모든 원본 줄을 이어 하나의 file-000.parquet. episode_index · dataset_from/to_index · data/file_index ·
           videos/*/file_index 갱신, meta/episodes/chunk_index · file_index = 0 (실제 위치). 원본 per-episode stats 열은 그대로.
  - info.json: d2 것 + total_episodes / total_frames / splits 갱신. tasks.parquet: d2 것 그대로.
  - stats.json: **d2 meta/stats.json 바이트 그대로** (d2 020000 normalizer 와 같은 값 — 새 fine-tune 때 lerobot-train 이
           dataset.meta.stats 로 normalizer 를 덮어쓰므로, 병합 통계를 새로 계산하지 않는다).
제외 편 (병합 256–259, 275) 은 영상 파일을 자르지 않으려고 (lerobot delete_episodes 는 재인코딩) 사본에 남기고,
학습은 manifest 의 272 편 목록 (`--dataset.episodes`) 만 쓴다.
출력: recovery_ft/dataset (repo_id oxr/so101_k8_d2_rc16), manifest/merge_map.json, logs/r02_build.log
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

import pandas as pd

HOME = Path.home()
RF = HOME / "so101_runs/main_k8/d2/recovery_ft"
DST = RF / "dataset"
REPO = "oxr/so101_k8_d2_rc16"
CAMS = ["observation.images.front", "observation.images.wrist"]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def tree_sha(root):
    return {str(p.relative_to(root)): sha(p) for p in sorted(Path(root).rglob("*")) if p.is_file()}


def main():
    from lerobot.datasets.aggregate import to_parquet_one_row_group_per_episode
    man = json.loads((RF / "manifest/training_manifest.json").read_text())
    if DST.exists():
        sys.exit(f"{DST} 이미 있음 — 덮어쓰지 않음")
    groups = man["merge_order"]
    roots = {g: Path(man["sources"][g]["root"]) for g in groups}
    before = {g: tree_sha(roots[g]) for g in groups}
    infos = {g: json.load(open(roots[g] / "meta/info.json")) for g in groups}
    feats0 = infos[groups[0]]["features"]
    for g in groups:
        assert infos[g]["features"] == feats0, f"{g} features ≠ d2"
        assert infos[g]["fps"] == 30 and infos[g]["codebase_version"] == "v3.0" and infos[g]["robot_type"] == infos[groups[0]]["robot_type"]
        t = pd.read_parquet(roots[g] / "meta/tasks.parquet")
        assert list(t.index) == [man["task"]] and list(t.task_index) == [0], f"{g} tasks"
    (DST / "meta/episodes/chunk-000").mkdir(parents=True)
    (DST / "data/chunk-000").mkdir(parents=True)
    for c in CAMS:
        (DST / f"videos/{c}/chunk-000").mkdir(parents=True)
    ep_off = idx_off = 0
    data_next = 0
    vid_next = {c: 0 for c in CAMS}
    metas, mapping = [], {}
    for g in groups:
        root = roots[g]
        E = pd.concat([pd.read_parquet(p) for p in sorted((root / "meta/episodes").rglob("*.parquet"))], ignore_index=True)
        E = E.sort_values("episode_index").reset_index(drop=True)
        assert list(E.episode_index) == list(range(infos[g]["total_episodes"]))
        assert (E["data/chunk_index"] == 0).all() and all((E[f"videos/{c}/chunk_index"] == 0).all() for c in CAMS), f"{g} chunk ≠ 0"
        # 데이터 파일
        dmap = {}
        for p in sorted((root / "data/chunk-000").glob("file-*.parquet")):
            src_fi = int(p.stem.split("-")[1])
            df = pd.read_parquet(p)
            assert (df.task_index == 0).all()
            df["episode_index"] = df["episode_index"] + ep_off
            df["index"] = df["index"] + idx_off
            out = DST / f"data/chunk-000/file-{data_next:03d}.parquet"
            to_parquet_one_row_group_per_episode(df, out)
            dmap[src_fi] = data_next
            mapping[str(out.relative_to(DST))] = str(p)
            data_next += 1
        assert set(E["data/file_index"]) <= set(dmap), f"{g} data file index 불일치"
        # 영상 파일 (바이트 복사)
        vmap = {}
        for c in CAMS:
            vmap[c] = {}
            for p in sorted((root / f"videos/{c}/chunk-000").glob("file-*.mp4")):
                src_fi = int(p.stem.split("-")[1])
                out = DST / f"videos/{c}/chunk-000/file-{vid_next[c]:03d}.mp4"
                shutil.copyfile(p, out)
                vmap[c][src_fi] = vid_next[c]
                mapping[str(out.relative_to(DST))] = str(p)
                vid_next[c] += 1
            assert set(E[f"videos/{c}/file_index"]) <= set(vmap[c]), f"{g} {c} video file index 불일치"
        # 에피소드 meta
        E = E.copy()
        E["episode_index"] += ep_off
        E["dataset_from_index"] += idx_off
        E["dataset_to_index"] += idx_off
        E["data/file_index"] = E["data/file_index"].map(dmap)
        for c in CAMS:
            E[f"videos/{c}/file_index"] = E[f"videos/{c}/file_index"].map(vmap[c])
        E["meta/episodes/chunk_index"] = 0
        E["meta/episodes/file_index"] = 0
        metas.append(E)
        ep_off += infos[g]["total_episodes"]
        idx_off += infos[g]["total_frames"]
    M = pd.concat(metas, ignore_index=True)
    M.to_parquet(DST / "meta/episodes/chunk-000/file-000.parquet")
    info = json.loads(json.dumps(infos[groups[0]]))
    info.update(total_episodes=ep_off, total_frames=idx_off, splits={"train": f"0:{ep_off}"})
    (DST / "meta/info.json").write_text(json.dumps(info, indent=4))
    shutil.copyfile(roots[groups[0]] / "meta/tasks.parquet", DST / "meta/tasks.parquet")
    shutil.copyfile(roots[groups[0]] / "meta/stats.json", DST / "meta/stats.json")
    (RF / "manifest/merge_map.json").write_text(json.dumps(dict(repo_id=REPO, files=mapping), indent=1))
    after = {g: tree_sha(roots[g]) for g in groups}
    assert before == after, "원본 파일이 바뀜"
    print("source files unchanged (sha256):", {g: len(v) for g, v in after.items()})
    print("merged episodes", ep_off, "frames", idx_off, "data files", data_next, "video files", vid_next)
    print("stats.json = d2 stats.json:", sha(DST / "meta/stats.json") == sha(roots[groups[0]] / "meta/stats.json"))
    print("BUILD_OK", DST)


if __name__ == "__main__":
    main()
