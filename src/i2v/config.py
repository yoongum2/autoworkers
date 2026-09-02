"""config.toml 파싱과 검증."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - 3.10 이하
    import tomli as tomllib  # type: ignore[no-redef]


class ConfigError(ValueError):
    """설정 값이 잘못됐을 때."""


@dataclass
class ComfyConfig:
    url: str = "http://127.0.0.1:8188"
    workflow: Path = Path("workflows/wan22_i2v_gguf_api.json")
    timeout: float = 3600.0
    poll_interval: float = 2.0


@dataclass
class ModelConfig:
    high_noise: str = "wan2.2_i2v_high_noise_14B_Q4_K_M.gguf"
    low_noise: str = "wan2.2_i2v_low_noise_14B_Q4_K_M.gguf"
    clip: str = "umt5_xxl_fp8_e4m3fn_scaled.safetensors"
    vae: str = "wan_2.1_vae.safetensors"


@dataclass
class VideoConfig:
    width: int = 480
    height: int = 832
    fps: int = 16
    clip_frames: int = 81
    target_seconds: float = 300.0

    #: 체이닝 시 다음 클립의 첫 프레임이 이전 클립의 마지막 프레임과 겹치므로,
    #: 이어붙일 때 클립마다 마지막 프레임 1장을 버린다.
    trim_overlap: bool = True

    @property
    def clip_seconds(self) -> float:
        return self.clip_frames / self.fps

    @property
    def usable_frames(self) -> int:
        return self.clip_frames - 1 if self.trim_overlap else self.clip_frames

    @property
    def usable_seconds(self) -> float:
        return self.usable_frames / self.fps

    @property
    def clips_needed(self) -> int:
        return math.ceil(self.target_seconds / self.usable_seconds)

    def validate(self) -> None:
        # Wan 계열은 시간축을 4프레임 단위로 압축하므로 length는 4n+1 이어야 한다.
        if self.clip_frames < 5 or self.clip_frames % 4 != 1:
            raise ConfigError(
                f"video.clip_frames는 4n+1 이어야 합니다 (예: 49, 65, 81). 현재: {self.clip_frames}"
            )
        for name, value in (("width", self.width), ("height", self.height)):
            if value % 16 != 0:
                raise ConfigError(f"video.{name}는 16의 배수여야 합니다. 현재: {value}")
        if self.fps <= 0:
            raise ConfigError("video.fps는 1 이상이어야 합니다.")
        if self.target_seconds <= 0:
            raise ConfigError("video.target_seconds는 0보다 커야 합니다.")


@dataclass
class SamplingConfig:
    steps: int = 20
    cfg: float = 3.5
    sampler: str = "euler"
    scheduler: str = "simple"
    shift: float = 8.0
    boundary: float = 0.5
    seed: int = 12345
    seed_mode: str = "increment"  # increment | fixed | random

    def validate(self) -> None:
        if self.steps < 1:
            raise ConfigError("sampling.steps는 1 이상이어야 합니다.")
        if not 0.0 < self.boundary < 1.0:
            raise ConfigError("sampling.boundary는 0과 1 사이여야 합니다.")
        if self.seed_mode not in ("increment", "fixed", "random"):
            raise ConfigError("sampling.seed_mode는 increment/fixed/random 중 하나여야 합니다.")

    @property
    def switch_step(self) -> int:
        """high-noise 전문가에서 low-noise 전문가로 넘어가는 스텝."""
        return max(1, min(self.steps - 1, round(self.steps * self.boundary)))


@dataclass
class SpeedConfig:
    """Lightning / LightX2V 계열 distill LoRA (선택)."""

    enabled: bool = False
    high_lora: str = ""
    low_lora: str = ""
    strength: float = 1.0
    steps: int = 6
    cfg: float = 1.0

    def validate(self) -> None:
        if self.enabled and not (self.high_lora and self.low_lora):
            raise ConfigError("speed.enabled=true면 speed.high_lora와 speed.low_lora가 필요합니다.")
        if self.enabled and self.steps < 2:
            raise ConfigError("speed.steps는 2 이상이어야 합니다.")


@dataclass
class ChainConfig:
    reset_every: int = 0
    color_anchor: float = 0.6
    negative: str = (
        "색조 왜곡, 정지 화면, 흐릿함, 디테일 뭉개짐, 자막, 워터마크, 로고, 손가락 기형, "
        "저화질, JPEG 아티팩트, 밝기 깜빡임, 급격한 장면 전환"
    )

    def validate(self) -> None:
        if self.reset_every < 0:
            raise ConfigError("chain.reset_every는 0 이상이어야 합니다 (0 = 하드 리셋 없음).")
        if not 0.0 <= self.color_anchor <= 1.0:
            raise ConfigError("chain.color_anchor는 0.0~1.0 이어야 합니다.")


@dataclass
class PathConfig:
    work: Path = Path("work")
    out: Path = Path("out")


@dataclass
class Shot:
    """하나의 '샷' = 같은 프롬프트로 연속 생성할 클립 묶음."""

    prompt: str
    clips: int = 1
    keyframe: Path | None = None
    negative: str | None = None
    seed: int | None = None

    def validate(self, index: int) -> None:
        if not self.prompt.strip():
            raise ConfigError(f"shots[{index}].prompt가 비어 있습니다.")
        if self.clips < 1:
            raise ConfigError(f"shots[{index}].clips는 1 이상이어야 합니다.")


@dataclass
class Config:
    comfy: ComfyConfig = field(default_factory=ComfyConfig)
    models: ModelConfig = field(default_factory=ModelConfig)
    video: VideoConfig = field(default_factory=VideoConfig)
    sampling: SamplingConfig = field(default_factory=SamplingConfig)
    speed: SpeedConfig = field(default_factory=SpeedConfig)
    chain: ChainConfig = field(default_factory=ChainConfig)
    paths: PathConfig = field(default_factory=PathConfig)
    shots: list[Shot] = field(default_factory=list)
    source: Path | None = None

    @property
    def effective_steps(self) -> int:
        return self.speed.steps if self.speed.enabled else self.sampling.steps

    @property
    def effective_cfg(self) -> float:
        return self.speed.cfg if self.speed.enabled else self.sampling.cfg

    @property
    def switch_step(self) -> int:
        steps = self.effective_steps
        return max(1, min(steps - 1, round(steps * self.sampling.boundary)))

    @property
    def total_clips(self) -> int:
        """샷 리스트가 있으면 그 합계, 없으면 target_seconds에서 역산."""
        if self.shots:
            return sum(shot.clips for shot in self.shots)
        return self.video.clips_needed

    def validate(self) -> None:
        self.video.validate()
        self.sampling.validate()
        self.speed.validate()
        self.chain.validate()
        for i, shot in enumerate(self.shots):
            shot.validate(i)
        if not self.shots:
            raise ConfigError("최소 한 개의 [[shots]] 항목이 필요합니다.")
        if self.shots[0].keyframe is None:
            raise ConfigError("shots[0]에는 시작 이미지(keyframe)가 반드시 있어야 합니다.")


def _subset(raw: dict[str, Any], cls: type, *, path_fields: tuple[str, ...] = ()) -> Any:
    """알 수 없는 키는 에러로 잡고, 지정된 필드는 Path로 변환한다."""
    known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
    unknown = set(raw) - known
    if unknown:
        raise ConfigError(f"[{cls.__name__}] 알 수 없는 설정 키: {', '.join(sorted(unknown))}")
    kwargs = dict(raw)
    for name in path_fields:
        if name in kwargs:
            kwargs[name] = Path(kwargs[name])
    return cls(**kwargs)


def load(path: str | Path) -> Config:
    """config.toml을 읽어 검증된 Config를 돌려준다."""
    path = Path(path)
    if not path.is_file():
        raise ConfigError(f"설정 파일을 찾을 수 없습니다: {path}")
    with path.open("rb") as fh:
        raw = tomllib.load(fh)

    base = path.parent
    shots: list[Shot] = []
    for entry in raw.pop("shots", []):
        keyframe = entry.get("keyframe")
        shots.append(
            Shot(
                prompt=entry.get("prompt", ""),
                clips=int(entry.get("clips", 1)),
                keyframe=(base / keyframe) if keyframe else None,
                negative=entry.get("negative"),
                seed=entry.get("seed"),
            )
        )

    paths_raw = raw.pop("paths", {})
    paths = _subset(paths_raw, PathConfig, path_fields=("work", "out"))
    paths.work = base / paths.work
    paths.out = base / paths.out

    comfy = _subset(raw.pop("comfy", {}), ComfyConfig, path_fields=("workflow",))
    comfy.workflow = base / comfy.workflow

    cfg = Config(
        comfy=comfy,
        models=_subset(raw.pop("models", {}), ModelConfig),
        video=_subset(raw.pop("video", {}), VideoConfig),
        sampling=_subset(raw.pop("sampling", {}), SamplingConfig),
        speed=_subset(raw.pop("speed", {}), SpeedConfig),
        chain=_subset(raw.pop("chain", {}), ChainConfig),
        paths=paths,
        shots=shots,
        source=path,
    )
    if raw:
        raise ConfigError(f"알 수 없는 최상위 섹션: {', '.join(sorted(raw))}")
    cfg.validate()
    return cfg
