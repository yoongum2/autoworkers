"""RTX 3080 Ti(12GB)용 로컬 image-to-video 파이프라인.

ComfyUI + Wan 2.2 I2V-A14B(GGUF)로 짧은 클립을 반복 생성하고,
끝프레임 체이닝으로 이어붙여 긴 영상(기본 300초)을 만든다.
"""

__version__ = "0.1.0"
