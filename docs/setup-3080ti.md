# RTX 3080 Ti (12GB) 셋업 가이드

## 0. 하드웨어 전제

| 항목 | 필요 | 이유 |
|---|---|---|
| VRAM | 12GB | Wan 2.2 14B GGUF Q4/Q5가 여기에 들어갑니다 |
| 시스템 RAM | **32GB 권장** (최소 16GB + 넉넉한 페이지파일) | high/low 두 전문가 모델을 번갈아 쓰면서 안 쓰는 쪽을 RAM으로 내립니다 |
| 저장공간 | 60GB+ | 모델 약 25GB + 60클립 중간 프레임 |

> **3080 Ti는 Ampere입니다.** fp8 연산 가속은 Ada(RTX 40xx) 이상 기능이라
> `fp8_e4m3fn` UNet 체크포인트를 써도 빨라지지 않고 오히려 느려질 수 있습니다.
> UNet은 **GGUF Q4_K_M / Q5_K_M**을 쓰세요. (텍스트 인코더의 fp8은 무관합니다 — 그건 저장 포맷일 뿐입니다.)

## 1. ComfyUI 설치

```bash
git clone https://github.com/comfyanonymous/ComfyUI
cd ComfyUI
python -m venv venv && . venv/bin/activate      # Windows: venv\Scripts\activate
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements.txt
```

## 2. 커스텀 노드

`ComfyUI/custom_nodes/`에서:

```bash
git clone https://github.com/city96/ComfyUI-GGUF          # UnetLoaderGGUF (필수)
```

설치 후 ComfyUI를 재시작하세요. `UnetLoaderGGUF` 노드가 없으면
`i2v check`가 잡아냅니다.

## 3. 모델 받기

```bash
pip install huggingface_hub
python scripts/download_models.py --comfy /path/to/ComfyUI --quant Q4_K_M
```

배치되는 위치:

```
ComfyUI/models/unet/           wan2.2_i2v_high_noise_14B_Q4_K_M.gguf
                               wan2.2_i2v_low_noise_14B_Q4_K_M.gguf
ComfyUI/models/text_encoders/  umt5_xxl_fp8_e4m3fn_scaled.safetensors
ComfyUI/models/vae/            wan_2.1_vae.safetensors
```

스크립트가 출력하는 실제 파일명을 `config.toml`의 `[models]`에 그대로 넣으세요.
양자화 선택:

| 양자화 | 크기(전문가 1개) | 12GB에서 |
|---|---|---|
| Q4_K_M | ~9GB | 여유 있음. 기본값 |
| Q5_K_M | ~11GB | 가능. 조금 느림, 디테일 약간 개선 |
| Q8_0 | ~16GB | 계속 스왑이 일어나 매우 느림. 비권장 |

## 4. ComfyUI 실행

```bash
python main.py --listen 127.0.0.1 --port 8188
```

12GB에서 OOM이 나면 순서대로 시도하세요:

1. `--lowvram` 추가
2. `config.toml`의 `video.width/height`를 낮춤 (480x832 → 416x736)
3. `video.clip_frames`를 81 → 65 또는 49로 (그만큼 클립 수는 늘어납니다)
4. `--reserve-vram 1.0` 으로 다른 프로그램 몫을 남김

## 5. 속도 올리기 (선택)

### SageAttention

Ampere(sm86)에서 동작하며 30~40% 빨라집니다.

```bash
pip install triton-windows   # Windows. Linux는 pip install triton
pip install sageattention
python main.py --use-sage-attention
```

### distill LoRA (효과가 가장 큼)

Lightning / LightX2V 계열 4-step LoRA를 `ComfyUI/models/loras/`에 넣고
`config.toml`에서:

```toml
[speed]
enabled = true
high_lora = "받은_high_lora_파일명.safetensors"
low_lora  = "받은_low_lora_파일명.safetensors"
steps = 6
cfg = 1.0
```

20스텝 → 6스텝이면 클립당 시간이 **3배 이상** 줄어, 60클립 배치가
하룻밤(6~10시간)이 아니라 2~3시간에 끝납니다. 대신 모션의 다이내믹이 다소 얌전해집니다.

## 6. 실측 참고치

3080 Ti · Q4_K_M · 480x832 · 81프레임 기준 (환경에 따라 크게 다릅니다):

| 설정 | 클립당 | 60클립(300초) |
|---|---|---|
| 20스텝, SageAttention 없음 | 약 9~12분 | 9~12시간 |
| 20스텝, SageAttention | 약 6~8분 | 6~8시간 |
| 6스텝 distill LoRA + SageAttention | 약 2~3분 | 2~3시간 |

첫 클립은 모델 로딩 때문에 2~3분 더 걸립니다. `i2v run --limit 2`로
2클립만 돌려 실제 시간을 먼저 재보세요 — `run`은 진행하면서 남은 시간을 계속 갱신해 보여줍니다.

## 7. 밤새 돌리기

- 작업은 클립 단위로 `work/state.json`에 기록됩니다. Ctrl+C로 끊거나 정전이 나도
  같은 명령을 다시 실행하면 **완료된 클립은 건너뛰고 이어서** 진행합니다.
- Windows에서는 전원 옵션의 절전/최대 절전을 꺼두세요.
- 다 만든 뒤 합치기만 다시 하려면 `i2v assemble`.
