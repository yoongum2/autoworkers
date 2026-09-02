"""프레임/영상 후처리: 키프레임 정규화, 색 드리프트 보정, ffmpeg 인코딩."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image


class FFmpegError(RuntimeError):
    """ffmpeg 실행 실패."""


def ensure_ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        raise FFmpegError(
            "ffmpeg를 찾을 수 없습니다. "
            "Windows: winget install Gyan.FFmpeg / Linux: apt install ffmpeg"
        )
    return exe


def _run(args: list[str]) -> None:
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        tail = "\n".join(proc.stderr.strip().splitlines()[-15:])
        raise FFmpegError(f"ffmpeg 실패 ({' '.join(args[:3])} ...):\n{tail}")


def prepare_keyframe(src: str | Path, width: int, height: int, dest: Path) -> Path:
    """시작 이미지를 목표 해상도에 맞춰 중앙 크롭 + 리사이즈한다."""
    with Image.open(src) as img:
        img = img.convert("RGB")
        scale = max(width / img.width, height / img.height)
        resized = img.resize(
            (max(width, round(img.width * scale)), max(height, round(img.height * scale))),
            Image.LANCZOS,
        )
        left = (resized.width - width) // 2
        top = (resized.height - height) // 2
        cropped = resized.crop((left, top, left + width, top + height))
    dest.parent.mkdir(parents=True, exist_ok=True)
    cropped.save(dest)
    return dest


def color_anchor(src: Path, reference: Path, strength: float, dest: Path) -> Path:
    """체이닝 프레임의 채널별 평균/표준편차를 기준 이미지 쪽으로 되돌린다.

    클립을 계속 이어 붙이면 색이 서서히 밀리는데(drift), 다음 클립의 시작 프레임을
    원본 키프레임 통계로 부분 보정해서 누적을 늦춘다. strength=0이면 원본 그대로.
    """
    if strength <= 0:
        if src != dest:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dest)
        return dest

    with Image.open(src) as s, Image.open(reference) as r:
        cur = np.asarray(s.convert("RGB"), dtype=np.float32)
        ref = np.asarray(r.convert("RGB"), dtype=np.float32)

    cur_mean, cur_std = cur.mean((0, 1)), cur.std((0, 1))
    ref_mean, ref_std = ref.mean((0, 1)), ref.std((0, 1))
    # 평평한 채널에서 노이즈가 증폭되지 않도록 하한을 둔다.
    ratio = np.clip(ref_std / np.maximum(cur_std, 1e-3), 0.5, 2.0)

    matched = (cur - cur_mean) * ratio + ref_mean
    blended = cur + (matched - cur) * float(strength)

    dest.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.clip(blended, 0, 255).astype(np.uint8)).save(dest)
    return dest


def encode_clip(frame_dir: Path, fps: int, dest: Path, *, pattern: str = "%05d.png") -> Path:
    """번호순 PNG 시퀀스를 mp4로 인코딩한다."""
    ensure_ffmpeg()
    dest.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-framerate", str(fps),
            "-start_number", "0",
            "-i", str(frame_dir / pattern),
            "-c:v", "libx264", "-preset", "medium", "-crf", "17",
            "-pix_fmt", "yuv420p",
            str(dest),
        ]
    )
    return dest


def concat(clips: list[Path], dest: Path, *, list_path: Path | None = None) -> Path:
    """같은 설정으로 인코딩된 클립들을 재인코딩 없이 이어 붙인다."""
    ensure_ffmpeg()
    if not clips:
        raise FFmpegError("이어 붙일 클립이 없습니다.")
    dest.parent.mkdir(parents=True, exist_ok=True)
    list_path = list_path or dest.with_suffix(".txt")
    list_path.write_text(
        "".join(f"file '{p.resolve().as_posix()}'\n" for p in clips), encoding="utf-8"
    )
    _run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "concat", "-safe", "0", "-i", str(list_path),
            "-c", "copy", str(dest),
        ]
    )
    return dest


def interpolate(src: Path, dest: Path, target_fps: int) -> Path:
    """ffmpeg minterpolate로 프레임을 보간한다.

    ComfyUI의 RIFE 노드보다 품질은 떨어지지만 추가 의존성이 없다.
    """
    ensure_ffmpeg()
    dest.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
            "-vf", f"minterpolate=fps={target_fps}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-pix_fmt", "yuv420p", str(dest),
        ]
    )
    return dest


def trim_to(src: Path, dest: Path, seconds: float) -> Path:
    """최종 영상을 목표 길이에 맞춰 자른다."""
    ensure_ffmpeg()
    dest.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
            "-t", f"{seconds:.3f}", "-c", "copy", str(dest),
        ]
    )
    return dest
