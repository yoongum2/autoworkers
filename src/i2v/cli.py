"""명령줄 진입점: python -m i2v <명령>"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import config as cfgmod
from . import pipeline as pipemod
from . import workflow as wf
from .comfy import ComfyClient, ComfyError


def _load(args: argparse.Namespace) -> cfgmod.Config:
    return cfgmod.load(args.config)


# ---------------------------------------------------------------- 하위 명령


def cmd_check(args: argparse.Namespace) -> int:
    cfg = _load(args)
    print(f"설정: {cfg.source}")

    graph = wf.load_graph(cfg.comfy.workflow)
    nodes = wf.resolve(graph)
    print(f"워크플로: {cfg.comfy.workflow.name} — 노드 {len(graph)}개, 구조 정상")

    client = ComfyClient(cfg.comfy.url, timeout=cfg.comfy.timeout)
    stats = client.ping()
    print(f"ComfyUI: {cfg.comfy.url} — {pipemod.vram_line(stats)}")

    info = client.object_info()
    problems: list[str] = []

    required_classes = {graph[nid]["class_type"] for nid in graph}
    if cfg.speed.enabled:
        required_classes.add("LoraLoaderModelOnly")
    for cls in sorted(required_classes):
        if cls not in info:
            problems.append(f"노드 '{cls}'가 설치돼 있지 않습니다 (커스텀 노드 확인 필요)")

    checks = [
        (graph[nodes.high_unet]["class_type"], "unet_name", cfg.models.high_noise),
        (graph[nodes.low_unet]["class_type"], "unet_name", cfg.models.low_noise),
        ("CLIPLoader", "clip_name", cfg.models.clip),
        ("VAELoader", "vae_name", cfg.models.vae),
    ]
    if cfg.speed.enabled:
        checks += [
            ("LoraLoaderModelOnly", "lora_name", cfg.speed.high_lora),
            ("LoraLoaderModelOnly", "lora_name", cfg.speed.low_lora),
        ]

    for cls, field, wanted in checks:
        options = _options(info, cls, field)
        if options is None:
            continue  # 노드 미설치는 위에서 이미 보고됨
        if wanted not in options:
            hint = ", ".join(options[:4]) or "(없음)"
            problems.append(f"{cls}.{field}에 '{wanted}'가 없습니다. 설치된 것: {hint} ...")
        else:
            print(f"모델 OK: {wanted}")

    plans = pipemod.plan_clips(cfg)
    total = len(plans) * cfg.video.usable_seconds
    print(
        f"계획: {len(plans)}클립 × {cfg.video.usable_seconds:.2f}초 = {total:.1f}초 "
        f"(목표 {cfg.video.target_seconds:.0f}초)"
    )
    if total < cfg.video.target_seconds:
        short = cfg.video.target_seconds - total
        problems.append(
            f"샷 합계가 목표보다 {short:.1f}초 짧습니다 "
            f"(클립 {int(short / cfg.video.usable_seconds) + 1}개 추가 필요)"
        )

    for missing in (s.keyframe for s in cfg.shots if s.keyframe and not s.keyframe.is_file()):
        problems.append(f"키프레임 파일이 없습니다: {missing}")

    if problems:
        print("\n문제 발견:")
        for item in problems:
            print(f"  - {item}")
        return 1
    print("\n전부 정상. `i2v run` 으로 시작하세요.")
    return 0


def _options(info: dict, cls: str, field: str) -> list[str] | None:
    node = info.get(cls)
    if not node:
        return None
    required = node.get("input", {}).get("required", {})
    spec = required.get(field)
    if isinstance(spec, list) and spec and isinstance(spec[0], list):
        return [str(v) for v in spec[0]]
    return []


def cmd_plan(args: argparse.Namespace) -> int:
    cfg = _load(args)
    plans = pipemod.plan_clips(cfg)
    for line in pipemod.iter_progress(plans):
        print(line)
    print(
        f"\n합계 {len(plans)}클립 → {len(plans) * cfg.video.usable_seconds:.1f}초 "
        f"({cfg.video.width}x{cfg.video.height} @ {cfg.video.fps}fps)"
    )
    return 0


def cmd_estimate(args: argparse.Namespace) -> int:
    cfg = _load(args)
    plans = pipemod.plan_clips(cfg)
    steps = cfg.effective_steps
    pixels = cfg.video.width * cfg.video.height * cfg.video.clip_frames
    scale = pixels / (480 * 832 * 81)  # 기준: 480x832x81프레임

    print(
        f"클립 {len(plans)}개 · 스텝 {steps} · {cfg.video.width}x{cfg.video.height}"
        f" · {cfg.video.clip_frames}프레임"
    )
    print("\nRTX 3080 Ti 12GB 대략치 (스텝당 초, 실측으로 대체하세요):")
    # docs/setup-3080ti.md의 실측 표에서 역산한 값
    for label, per_step in (("Q4_K_M", 28.0), ("Q5_K_M", 33.0), ("Q8_0", 50.0)):
        per_clip = per_step * scale * steps
        total = per_clip * len(plans)
        sage = total * 0.68  # SageAttention 적용 시
        print(
            f"  {label:>7}: 클립당 {per_clip / 60:4.1f}분 → 전체 {total / 3600:5.1f}시간"
            f"  (SageAttention 시 {sage / 3600:.1f}시간)"
        )

    if not cfg.speed.enabled:
        print(
            "\n[speed] distill LoRA를 켜면 스텝이 20 → 6으로 줄어 위 시간의 약 1/3이 됩니다."
        )
    print("먼저 `i2v run --limit 2`로 2클립만 돌려 실제 속도를 재보세요.")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    cfg = _load(args)
    plans = pipemod.plan_clips(cfg)
    if args.limit:
        plans = plans[: args.limit]
    pipe = pipemod.Pipeline(cfg)
    results = pipe.run(plans, force=args.force)
    if args.no_assemble:
        print(f"\n{len(results)}클립 완료. 합치기: i2v assemble")
        return 0
    out = pipe.assemble(results, args.name, interpolate_fps=args.interpolate)
    print(f"\n완료: {out}")
    return 0


def cmd_assemble(args: argparse.Namespace) -> int:
    cfg = _load(args)
    pipe = pipemod.Pipeline(cfg)
    if not pipe.state.clips:
        print("생성된 클립이 없습니다. 먼저 `i2v run`을 실행하세요.", file=sys.stderr)
        return 1
    results = [pipe.state.clips[i] for i in sorted(pipe.state.clips)]
    out = pipe.assemble(results, args.name, interpolate_fps=args.interpolate)
    print(f"완료: {out}")
    return 0


# ---------------------------------------------------------------- 파서


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="i2v",
        description="ComfyUI + Wan 2.2 I2V로 짧은 클립을 이어붙여 긴 영상 만들기",
    )
    parser.add_argument("-c", "--config", default="config.toml", help="설정 파일 (기본: config.toml)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("check", help="ComfyUI 연결·노드·모델·샷 구성 점검").set_defaults(func=cmd_check)
    sub.add_parser("plan", help="생성될 클립 목록 출력").set_defaults(func=cmd_plan)
    sub.add_parser("estimate", help="소요 시간 대략 계산").set_defaults(func=cmd_estimate)

    run = sub.add_parser("run", help="클립 생성 후 이어붙이기")
    run.add_argument("--name", default="final", help="출력 파일 이름 (기본: final)")
    run.add_argument("--limit", type=int, default=0, help="앞에서 N개 클립만 (테스트용)")
    run.add_argument("--force", action="store_true", help="이미 만든 클립도 다시 생성")
    run.add_argument("--no-assemble", action="store_true", help="합치기 없이 생성만")
    run.add_argument("--interpolate", type=int, default=0, metavar="FPS", help="보간 목표 fps")
    run.set_defaults(func=cmd_run)

    asm = sub.add_parser("assemble", help="이미 만든 클립만 이어붙이기")
    asm.add_argument("--name", default="final")
    asm.add_argument("--interpolate", type=int, default=0, metavar="FPS")
    asm.set_defaults(func=cmd_assemble)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (cfgmod.ConfigError, wf.WorkflowError) as exc:
        print(f"설정 오류: {exc}", file=sys.stderr)
        return 2
    except ComfyError as exc:
        print(f"ComfyUI 오류: {exc}", file=sys.stderr)
        return 3
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n중단했습니다. 같은 명령을 다시 실행하면 이어서 진행합니다.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
