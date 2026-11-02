# CLAUDE.md — 이 저장소를 갱신할 때의 규칙

이 저장소는 SO-101 π₀.₅ 공간 일반화 연구의 **기록** 저장소다. 실험을 실행하는 곳이 아니다.

## 절대 하지 않는 것
- GPU 학습 시작·재개, 학습 프로세스 신호 보내기 (sampling ablation 큐 재개 포함) — 사용자가 명시적으로 지시할 때만, 그리고 이 저장소 밖에서.
- 로봇 연결·토크·rollout·teleop·record 실행. 로봇 명령은 사용자가 직접 실행한다.
- 원본 연구 폴더 (`/home/user/so101_runs`, `/home/user/so101_boxpick`) 의 파일 수정·이동·삭제. 이 저장소로 **복사만** 한다.
- 체크포인트 (`*.safetensors`), 데이터셋 (`*.parquet`, 영상), `.npz/.npy`, 대용량 로그를 커밋. 경로·SHA-256 만 기록한다.
- `git push --force`, 이력 재작성, 원격 브랜치 삭제.
- 존재하지 않는 결과를 채워 넣기. 확인 안 된 값은 `미확인`.

## 기록 규칙
1. 모든 진술에 표기: [사실] (파일 측정값) · [관찰] (연구자 실물 관찰, 메모 원문) · [가설] (분석 해석) · [계획] (설계만).
2. 실물 결과와 오프라인 결과를 섞지 않는다. 오프라인 probe·재추론·합성 격자 결과를 성공률로 쓰지 않는다.
3. 데이터 종류 표기: [in-sample] · [held-out fold] · [합성] · [반사실] · [재구성]. 진짜 held-out 사람 시연 (H) 이 생기기 전까지 "held-out 평가" 라고 쓰지 않는다.
4. 성공률에는 n 과 판정 방식 (사람 UI / 자동 / 분석) 을 붙인다.
5. 조건이 다른 실험 비교는 `evaluations/comparisons/README.md` 형식으로 통제 안 된 차이를 같이 적는다. 단순 비교로 "개선" 이라 쓰지 않는다.
6. 상태 코드: `PLANNED` · `IN_PROGRESS` · `COMPLETED` · `NOT_EVALUATED` · `PAUSED` · `PARTIAL` · `STOPPED`. 학습 완료와 평가 완료는 따로 적는다.
7. 구분 유지:
   - redbox_all (384편, K1–K4) 과 d2 (256편, K1–K8) 는 별개 데이터·별개 학습.
   - redbox 20k→30k resume (EXP-05) 와 d2 신규 20k (EXP-06) 는 다른 실험.
   - R1/R2 수동 복구 시연 (EXP-11) 과 HIL = 정책 실행 중 인간 교정 (EXP-12) 은 다른 방식. HIL 은 구현·검증 전까지 `PLANNED`.
   - 파일럿 "U1–U8" (임의 자리) ≠ Held-out H "U1–U8" (지정 좌표).

## 새 실험 기록 절차
1. `templates/experiment_template.md` 를 `experiments/NN_<이름>/README.md` 로 복사, 다음 번호로 ID `EXP-NN` 부여.
2. 실험 전에 목적·가설·판정 기준을 적고 상태 `PLANNED` 로 커밋.
3. 데이터셋·모델 설정: `tools/collect_run_metadata.py` 의 `TRAIN_RUNS` / `DATASETS` 에 추가 후 실행 (읽기 전용). 체크포인트 해시는
   `find <run>/checkpoints -name model.safetensors | grep -v /last/ | xargs sha256sum >> configs/checkpoints/model_sha256.txt` (사용자 승인 후, 학습이 끝난 뒤).
4. 결과 파일 연결: `tools/sync_sources.py` 의 `MAPPINGS` 에 원본 폴더 추가 → `python3 tools/sync_sources.py --dry-run` 로 크기 확인 → 실행.
5. 정량·정성 결과, 실패 사례 (메모 원문), 분석·후속 가설을 README 에 적고 상태 갱신.
6. `EXPERIMENT_INDEX.md`, `CHANGELOG.md`, 필요하면 `evaluations/*/README.md` 와 `README.md` 9절 (현재 상태) 갱신.
7. `python3 tools/check_repo.py` — 필수 항목, 상대 링크, 파일 크기, 비밀정보 패턴 검사. 실패하면 커밋하지 않는다.
8. `git status` 로 추적 파일 확인 후 의미 있는 메시지로 커밋.
9. Push (ahnjaeyeong 계정, gh 활성 계정은 바꾸지 않음):
   ```bash
   GH_TOKEN=$(gh auth token --user ahnjaeyeong) git -c credential.helper= \
     -c 'credential.helper=!f(){ echo username=ahnjaeyeong; echo "password=$GH_TOKEN"; }; f' push origin main
   ```

## 원본 위치
- 연구 폴더: `/home/user/so101_runs` (practice, main, main_k8, redbox_all, reference, e0_j0, research_survey_20261102)
- 코드·배치 설정: `/home/user/so101_boxpick` (별도 git 저장소 `ahnjaeyeong/so101_boxpick` — 이 저장소에서 건드리지 않음)
- 가상환경: `/home/user/so101-env` (LeRobot 0.6.2)
