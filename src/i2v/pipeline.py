"""클립 생성 → 끝프레임 체이닝 → 이어붙이기 전체 흐름.

수십 분~수 시간 걸리는 작업이라 클립 단위로 상태를 저장하고, 중단 후 재실행하면
이미 만든 클립은 건너뛴다.
"""

from __future__ import annotations

import json
import random
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Iterator

from . import frames as fx
from . import workflow as wf
from .comfy import ComfyClient
from .config import Config

Reporter = Callable[[str], None]


@dataclass
class ClipPlan:
    """클립 하나를 만들기 위한 확정된 지시."""

    index: int
    shot: int
    prompt: str
    negative: str
    seed: int
    #: 이 클립부터 새 키프레임으로 시작한다면 그 경로, 체이닝이면 None
    keyframe: Path | None


@dataclass
class ClipResult:
    index: int
    video: str
    last_frame: str
    seed: int
    seconds: float
    elapsed: float


@dataclass
class State:
    """work/state.json 내용."""

    clips: dict[int, ClipResult] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> "State":
        if not path.is_file():
            return cls()
        raw = json.loads(path.read_text(encoding="utf-8"))
        return cls(clips={int(k): ClipResult(**v) for k, v in raw.get("clips", {}).items()})

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"clips": {str(k): asdict(v) for k, v in sorted(self.clips.items())}}
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)


def plan_clips(cfg: Config) -> list[ClipPlan]:
    """샷 리스트를 클립 단위 작업 목록으로 펼친다."""
    plans: list[ClipPlan] = []
    rng = random.Random(cfg.sampling.seed)
    since_reset = 0

    for shot_index, shot in enumerate(cfg.shots):
        for offset in range(shot.clips):
            index = len(plans)

            if cfg.sampling.seed_mode == "random":
                seed = rng.randrange(2**31)
            elif cfg.sampling.seed_mode == "fixed":
                seed = shot.seed if shot.seed is not None else cfg.sampling.seed
            else:  # increment
                base = shot.seed if shot.seed is not None else cfg.sampling.seed
                seed = base + index

            keyframe: Path | None = None
            if offset == 0 and shot.keyframe is not None:
                keyframe = shot.keyframe
                since_reset = 0
            elif cfg.chain.reset_every and since_reset >= cfg.chain.reset_every:
                # 하드 리셋: 이 샷의 앵커 키프레임으로 되돌아간다 (루프성 콘텐츠용).
                anchor = _anchor_for(cfg, shot_index)
                if anchor is not None:
                    keyframe = anchor
                    since_reset = 0

            since_reset += 1
            plans.append(
                ClipPlan(
                    index=index,
                    shot=shot_index,
                    prompt=shot.prompt,
                    negative=shot.negative or cfg.chain.negative,
                    seed=seed,
                    keyframe=keyframe,
                )
            )
    return plans


def _anchor_for(cfg: Config, shot_index: int) -> Path | None:
    """해당 샷 기준으로 가장 가까운 상위 키프레임."""
    for i in range(shot_index, -1, -1):
        if cfg.shots[i].keyframe is not None:
            return cfg.shots[i].keyframe
    return None


class Pipeline:
    def __init__(self, cfg: Config, *, report: Reporter = print) -> None:
        self.cfg = cfg
        self.report = report
        self.client = ComfyClient(
            cfg.comfy.url,
            timeout=cfg.comfy.timeout,
            poll_interval=cfg.comfy.poll_interval,
        )
        self.work = cfg.paths.work
        self.state_path = self.work / "state.json"
        self.state = State.load(self.state_path)
        self.base_graph = wf.load_graph(cfg.comfy.workflow)
        wf.resolve(self.base_graph)  # 시작 전에 그래프 모양을 검증한다

    # ------------------------------------------------------------------ 실행

    def run(self, plans: list[ClipPlan], *, force: bool = False) -> list[ClipResult]:
        fx.ensure_ffmpeg()
        stats = self.client.ping()
        self.report(f"ComfyUI 연결됨: {self.cfg.comfy.url} ({vram_line(stats)})")

        results: list[ClipResult] = []
        durations: list[float] = []
        anchor_cache: dict[int, Path] = {}
        previous_last: Path | None = None

        for plan in plans:
            cached = self.state.clips.get(plan.index)
            if cached and not force and Path(cached.video).is_file():
                self.report(f"[{plan.index + 1}/{len(plans)}] 이미 생성됨 — 건너뜀")
                results.append(cached)
                previous_last = Path(cached.last_frame)
                continue

            anchor = self._anchor_image(plan, anchor_cache)
            start = self._start_image(plan, previous_last, anchor)

            eta = _eta(durations, len(plans) - plan.index)
            self.report(
                f"[{plan.index + 1}/{len(plans)}] 샷{plan.shot + 1} seed={plan.seed} "
                f"start={start.name}{eta}"
            )

            began = time.monotonic()
            result = self._render(plan, start)
            durations.append(time.monotonic() - began)

            self.state.clips[plan.index] = result
            self.state.save(self.state_path)
            results.append(result)
            previous_last = Path(result.last_frame)
            self.report(f"    → {Path(result.video).name} ({result.elapsed:.0f}초)")

        return results

    def _anchor_image(self, plan: ClipPlan, cache: dict[int, Path]) -> Path:
        """색 보정 기준이 될, 해당 샷의 정규화된 키프레임."""
        if plan.shot not in cache:
            source = _anchor_for(self.cfg, plan.shot)
            if source is None:
                raise FileNotFoundError(f"샷 {plan.shot + 1}의 기준 키프레임을 찾을 수 없습니다.")
            cache[plan.shot] = fx.prepare_keyframe(
                source,
                self.cfg.video.width,
                self.cfg.video.height,
                self.work / "keyframes" / f"shot_{plan.shot:03d}.png",
            )
        return cache[plan.shot]

    def _start_image(self, plan: ClipPlan, previous: Path | None, anchor: Path) -> Path:
        """이 클립의 시작 프레임을 만든다 (새 키프레임이거나, 보정된 이전 끝프레임)."""
        if plan.keyframe is not None or previous is None:
            source = plan.keyframe if plan.keyframe is not None else anchor
            return fx.prepare_keyframe(
                source,
                self.cfg.video.width,
                self.cfg.video.height,
                self.work / "starts" / f"clip_{plan.index:04d}.png",
            )
        return fx.color_anchor(
            previous,
            anchor,
            self.cfg.chain.color_anchor,
            self.work / "starts" / f"clip_{plan.index:04d}.png",
        )

    def _render(self, plan: ClipPlan, start: Path) -> ClipResult:
        cfg = self.cfg
        clip_dir = self.work / "clips" / f"clip_{plan.index:04d}"
        frame_dir = clip_dir / "frames"
        if frame_dir.exists():
            for stale in frame_dir.glob("*.png"):
                stale.unlink()

        image_name = self.client.upload_image(start)
        graph, nodes = wf.build(
            cfg,
            self.base_graph,
            prompt=plan.prompt,
            negative=plan.negative,
            image_name=image_name,
            seed=plan.seed,
            filename_prefix=f"i2v/clip_{plan.index:04d}",
        )

        began = time.monotonic()
        prompt_id = self.client.queue(graph)
        outputs = self.client.wait(prompt_id)
        elapsed = time.monotonic() - began

        refs = self.client.images_from(outputs, nodes.save)
        if len(refs) != cfg.video.clip_frames:
            raise RuntimeError(
                f"프레임 {cfg.video.clip_frames}장을 기대했는데 {len(refs)}장을 받았습니다. "
                "워크플로의 SaveImage가 디코딩된 전체 배치를 받고 있는지 확인하세요."
            )

        for i, ref in enumerate(refs):
            self.client.download(ref, frame_dir / f"{i:05d}.png")

        # 다음 클립의 시작점은 항상 '버리기 전' 마지막 프레임이어야 이어짐이 자연스럽다.
        last_frame = clip_dir / "last.png"
        last_frame.write_bytes((frame_dir / f"{len(refs) - 1:05d}.png").read_bytes())

        if cfg.video.trim_overlap:
            (frame_dir / f"{len(refs) - 1:05d}.png").unlink()

        video = fx.encode_clip(frame_dir, cfg.video.fps, clip_dir.with_suffix(".mp4"))
        return ClipResult(
            index=plan.index,
            video=str(video),
            last_frame=str(last_frame),
            seed=plan.seed,
            seconds=cfg.video.usable_seconds,
            elapsed=elapsed,
        )

    # ------------------------------------------------------------------ 마무리

    def assemble(
        self,
        results: list[ClipResult],
        name: str,
        *,
        interpolate_fps: int | None = None,
        trim: bool = True,
    ) -> Path:
        clips = [Path(r.video) for r in sorted(results, key=lambda r: r.index)]
        missing = [str(p) for p in clips if not p.is_file()]
        if missing:
            raise FileNotFoundError("클립 파일이 없습니다: " + ", ".join(missing[:5]))

        out = self.cfg.paths.out
        merged = fx.concat(clips, out / f"{name}_raw.mp4", list_path=self.work / "concat.txt")
        self.report(f"이어붙임: {merged} ({len(clips)}클립)")

        final = merged
        if trim and self.cfg.video.target_seconds > 0:
            final = fx.trim_to(final, out / f"{name}_trimmed.mp4", self.cfg.video.target_seconds)
            self.report(f"길이 정리: {self.cfg.video.target_seconds:.1f}초")
        if interpolate_fps:
            final = fx.interpolate(final, out / f"{name}_{interpolate_fps}fps.mp4", interpolate_fps)
            self.report(f"프레임 보간: {self.cfg.video.fps} → {interpolate_fps}fps")

        target = out / f"{name}.mp4"
        if final != target:
            target.write_bytes(final.read_bytes())
        return target


def _eta(durations: list[float], remaining: int) -> str:
    if len(durations) < 2:
        return ""
    avg = sum(durations[-5:]) / len(durations[-5:])
    total = avg * remaining
    return f" | 남은 예상 {total / 60:.0f}분 (클립당 {avg:.0f}초)"


def vram_line(stats: dict) -> str:
    devices = stats.get("devices") or []
    if not devices:
        return "GPU 정보 없음"
    dev = devices[0]
    total = dev.get("vram_total", 0) / 2**30
    free = dev.get("vram_free", 0) / 2**30
    return f"{dev.get('name', 'GPU')} · VRAM {free:.1f}/{total:.1f}GB 여유"


def iter_progress(plans: list[ClipPlan]) -> Iterator[str]:
    """계획을 사람이 읽을 수 있게 요약."""
    for plan in plans:
        kind = "키프레임" if plan.keyframe else "체이닝"
        yield f"{plan.index + 1:>3}. 샷{plan.shot + 1} [{kind}] seed={plan.seed} :: {plan.prompt[:60]}"
