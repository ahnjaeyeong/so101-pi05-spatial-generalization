# so101_runs — SO-101 데이터 수집 세션

연습(practice)과 본 수집(main)을 같은 구조로 관리한다. 녹화는
`~/so101_boxpick/scripts/record_ui.py --session <카테고리>/<세션이름>` 으로 한다.

- 카메라 설정(자동 노출·자동 화이트밸런스 결정, 수동 후보값, 측정 기록): [camera_settings.md](camera_settings.md)
- 학습·평가 정리 문서: [docs/](docs/) — [practice_10 π0.5 연습 학습·실물 평가](docs/practice_10_pi05_2k.md)

```
so101_runs/
├── README.md            이 파일 (폴더·이름 규칙)
├── docs/                학습·평가 결과 정리 문서
├── practice/
│   ├── README.md        세션 목록 (세션당 한 줄)
│   └── <세션이름>/
└── main/
    ├── README.md
    └── <세션이름>/
```

## 이름 규칙
- 카테고리: `practice` 또는 `main`.
- 세션 이름·학습 실행 이름·평가 이름: **영어 소문자·숫자·밑줄만** (`practice_10`, `endbox_v1`, `act_bs8_20k`).
- 옵션 값 안에서는 `~` 대신 **`$HOME`** 을 쓴다 (`--opt=~/x` 는 셸이 펼치지 않는다).

## 세션 폴더
```
<세션>/
├── notes.md          설정·명령·판별 메모·결과 (record_ui.py 가 실행마다 기록을 추가)
├── setup_photos/     세팅 사진 + 카메라 첫 프레임 (ep000_<카메라>_first.png)
├── dataset/          lerobot 원본 데이터 — lerobot 이 만들고, 녹화 후 절대 수정 금지
├── review_videos/    에피소드별 확인용 영상 (episode_000.mp4 …, front|wrist 나란히)
├── train/            학습 결과 (학습마다 하위 폴더)
└── eval/             실물 테스트 기록
```
- `dataset/` 은 record_ui.py 가 만들지 않는다. 새 녹화면 lerobot 이 만들고, 이미 있으면 녹화를 거부한다
  (이어 찍으려면 `--resume=true`).
- 후처리(`--postprocess`)는 `dataset/` 을 읽기만 하고 `review_videos/`, `setup_photos/`, `notes.md`,
  카테고리 `README.md` 에만 쓴다. 이미 있는 영상·사진은 건너뛴다.

## 학습 규칙
```bash
~/so101-env/bin/lerobot-train ... \
  --dataset.repo_id=<notes.md 의 repo_id> \
  --dataset.root=$HOME/so101_runs/<세션>/dataset \
  --output_dir=$HOME/so101_runs/<세션>/train/<실행이름>
```
- 학습마다 `train/<실행이름>/` 하나. 실행이름 예: `act_bs8_20k`, `pi05_lora_v1`.
- `output_dir` 은 lerobot 이 만든다(이미 있으면 다른 이름을 쓴다).
- 어떤 설정으로 돌렸는지 notes.md 에 한 줄 남긴다.

## 평가 규칙
- `<세션>/eval/<평가이름>/` 에 실물 테스트 영상과 성공·실패 표(`results.md`)를 둔다.
- 표 예:

  | 시도 | 체크포인트 | 결과 | 메모 |
  |---|---|---|---|
  | 1 | train/act_bs8_20k/checkpoints/last | 성공 | |
