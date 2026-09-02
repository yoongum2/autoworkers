# autoworkers — 로컬 image-to-video 300초 파이프라인

RTX 3080 Ti(12GB) 한 장으로 **5초짜리 클립 60개를 이어붙여 300초 영상**을 만드는
배치 파이프라인입니다. ComfyUI를 백엔드로 쓰고, Wan 2.2 I2V-A14B(GGUF)로 생성합니다.

> **왜 이런 구조인가:** 로컬에서 돌릴 수 있는 I2V 모델은 한 번에 5초 안팎까지만
> 생성합니다. 300초를 만들려면 클립을 나눠 만들고, **각 클립의 마지막 프레임을 다음
> 클립의 시작 이미지로 넘겨(체이닝)** 이어 붙여야 합니다. 이 저장소가 그 반복을 자동화합니다.
>
> MiniMax(Hailuo)는 가중치 비공개 클라우드 서비스라 이 GPU에서 돌지 않습니다.
> 여기서는 전부 로컬로만 돌아갑니다.

## 빠른 시작

```bash
pip install -e .          # i2v 명령이 등록됩니다
                          # (설치 없이 쓰려면: pip install -r requirements.txt 후 PYTHONPATH=src python -m i2v ...)

# 1) ComfyUI + 모델 준비  →  docs/setup-3080ti.md
python scripts/download_models.py --comfy /path/to/ComfyUI --quant Q4_K_M

# 2) 설정 만들고 시작 이미지 넣기
cp config.example.toml config.toml
mkdir -p images   # 샷별 키프레임 PNG/JPG를 여기에

# 3) 연결·노드·모델·샷 구성 점검 (실제 생성 전에 반드시)
i2v check

# 4) 2클립만 시험 생성해서 소요 시간 재기
i2v run --limit 2 --name test

# 5) 전체 실행 (중단해도 다시 실행하면 이어서 진행)
i2v run --name final
```

결과는 `out/final.mp4`.

## 길이 계산

| | |
|---|---|
| 클립 길이 | 81프레임 @ 16fps |
| 겹침 제거 | 클립 경계에서 중복 프레임 1장 삭제 → **정확히 5.000초/클립** |
| 목표 300초 | **60클립** |

`clip_frames`는 Wan의 시간축 압축(4배) 때문에 반드시 **4n+1**이어야 합니다 (49 / 65 / 81).
`check` 명령이 이걸 포함해 설정을 전부 검증합니다.

## 이어붙임 품질을 지키는 두 가지

체이닝을 오래 반복하면 색이 서서히 밀리고(drift) 디테일이 뭉개집니다. 이 파이프라인은
두 가지로 대응합니다.

1. **색 앵커 (`chain.color_anchor`)** — 다음 클립의 시작 프레임을 그 샷의 원본
   키프레임 통계(채널별 평균/표준편차) 쪽으로 부분 보정합니다. `0.6`이 기본값이고,
   `0.0`이면 끕니다.
2. **샷 분할** — 한 샷을 **6클립(30초) 이하**로 유지하고 새 키프레임으로 다시 시작하세요.
   `config.example.toml`이 10샷 × 6클립 = 60클립 구조입니다.

`chain.reset_every`는 N클립마다 같은 키프레임으로 되돌아가는 하드 리셋입니다. 화면이
원점으로 튀므로 **루프성/앰비언트 영상에만** 쓰고, 서사가 있는 영상에서는 0(기본)으로 두세요.

## 명령

| 명령 | 하는 일 |
|---|---|
| `check` | ComfyUI 연결, 노드 설치 여부, 모델 파일명 일치, 샷 길이 합계까지 점검 |
| `plan` | 생성될 클립 목록(샷·시드·체이닝 여부)을 출력 |
| `estimate` | 양자화별 예상 소요 시간 |
| `run` | 클립 생성 + 이어붙이기. `--limit N`, `--force`, `--no-assemble`, `--interpolate 32` |
| `assemble` | 이미 만든 클립만 다시 합치기 |

`run`은 진행 중 클립당 실제 소요 시간으로 남은 시간을 계속 갱신합니다.

## 설정

전체 항목과 주석은 [`config.example.toml`](config.example.toml)에 있습니다. 핵심만:

```toml
[video]
width = 480; height = 832    # 16의 배수. 12GB에서 720x1280은 빠듯합니다
clip_frames = 81             # 4n+1
target_seconds = 300.0

[sampling]
steps = 20                   # boundary=0.5 → 앞 10스텝 high-noise, 뒤 10스텝 low-noise
cfg = 3.5
shift = 8.0

[speed]                      # distill LoRA. 켜면 6스텝으로 3배 이상 빨라짐
enabled = false

[[shots]]
keyframe = "images/01.png"   # 없으면 앞 샷 끝프레임에서 이어짐
clips = 6
prompt = "..."
```

## 중단과 재개

클립 하나가 끝날 때마다 `work/state.json`에 기록됩니다. Ctrl+C로 끊거나 PC가 꺼져도
같은 `run` 명령을 다시 실행하면 완료된 클립은 건너뛰고 이어서 진행합니다.
다시 만들고 싶으면 `--force`.

## 구조

```
src/i2v/
  config.py     config.toml 파싱·검증 (4n+1, 16의 배수, 오타 난 키까지 잡음)
  comfy.py      ComfyUI HTTP 클라이언트 (업로드 / 큐 / 폴링 / 결과 다운로드)
  workflow.py   API 그래프 패치. 노드 ID가 아니라 연결 관계로 역할을 찾음
  frames.py     키프레임 정규화, 색 앵커, ffmpeg 인코딩·concat·보간
  pipeline.py   클립 계획 → 생성 → 체이닝 → 합치기, 재개 상태 관리
  cli.py        python -m i2v
workflows/wan22_i2v_gguf_api.json   Wan 2.2 MoE(high/low 전문가) I2V 그래프
tests/          가짜 ComfyUI 서버로 전체 흐름 검증 (GPU 불필요)
```

`workflows/*.json`은 ComfyUI에서 **Export (API)** 로 저장한 형식입니다. 직접 워크플로를
고쳐 쓰고 싶으면 노드를 추가/재배치해도 됩니다 — `workflow.py`는 `class_type`과 연결
관계로 역할을 찾으므로 노드 번호가 바뀌어도 동작합니다. 다만 `WanImageToVideo` 1개,
`KSamplerAdvanced` 2개(high/low), `SaveImage` 1개 구조는 유지해야 합니다.

## 테스트

GPU도 ComfyUI도 없이 파이프라인 전체를 검증합니다 (가짜 ComfyUI 서버 사용):

```bash
python tests/test_pipeline.py
```

ffmpeg가 설치돼 있으면 실제 mp4 인코딩·합치기·길이까지 확인합니다.

## 요구사항

- Python 3.10+
- ffmpeg (PATH에 있어야 함)
- ComfyUI + [ComfyUI-GGUF](https://github.com/city96/ComfyUI-GGUF)
- 자세한 셋업: **[docs/setup-3080ti.md](docs/setup-3080ti.md)**
