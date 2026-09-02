#!/usr/bin/env python3
"""Wan 2.2 I2V(GGUF) 모델을 ComfyUI 폴더로 내려받는다.

    pip install huggingface_hub
    python scripts/download_models.py --comfy /path/to/ComfyUI --quant Q4_K_M

리포지토리 안의 파일명은 업로더가 바꿀 수 있으므로, 받기 전에 실제 파일 목록에서
패턴으로 찾아낸다. 원하는 파일이 안 잡히면 --list로 목록을 먼저 확인하세요.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from huggingface_hub import hf_hub_download, list_repo_files
except ImportError:  # pragma: no cover
    sys.exit("huggingface_hub가 필요합니다: pip install huggingface_hub")

UNET_REPO = "QuantStack/Wan2.2-I2V-A14B-GGUF"
COMFY_REPO = "Comfy-Org/Wan_2.1_ComfyUI_repackaged"

# (설명, 리포, 파일명에 반드시 포함돼야 할 조각들, ComfyUI 하위 폴더)
TARGETS = [
    ("high-noise 전문가", UNET_REPO, ("highnoise", "{quant}.gguf"), "models/unet"),
    ("low-noise 전문가", UNET_REPO, ("lownoise", "{quant}.gguf"), "models/unet"),
    ("텍스트 인코더", COMFY_REPO, ("umt5_xxl_fp8_e4m3fn_scaled", ".safetensors"), "models/text_encoders"),
    ("VAE", COMFY_REPO, ("wan_2.1_vae", ".safetensors"), "models/vae"),
]


def pick(files: list[str], needles: tuple[str, ...]) -> str | None:
    """파일 목록에서 모든 조각을 (대소문자/구분자 무시하고) 포함하는 첫 파일."""
    def norm(text: str) -> str:
        return text.lower().replace("_", "").replace("-", "").replace(" ", "")

    wanted = [norm(n) for n in needles]
    matches = [f for f in files if all(n in norm(f) for n in wanted)]
    return min(matches, key=len) if matches else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--comfy", type=Path, required=True, help="ComfyUI 설치 폴더")
    parser.add_argument(
        "--quant",
        default="Q4_K_M",
        help="GGUF 양자화. 12GB면 Q4_K_M(기본) 또는 Q5_K_M 권장 (기본: %(default)s)",
    )
    parser.add_argument("--list", action="store_true", help="받지 않고 리포 파일 목록만 출력")
    args = parser.parse_args()

    if args.list:
        for repo in (UNET_REPO, COMFY_REPO):
            print(f"\n=== {repo} ===")
            for name in sorted(list_repo_files(repo)):
                print(" ", name)
        return 0

    if not args.comfy.is_dir():
        return _fail(f"ComfyUI 폴더를 찾을 수 없습니다: {args.comfy}")

    cache: dict[str, list[str]] = {}
    resolved: list[tuple[str, str]] = []
    missing = False

    for label, repo, needles, subdir in TARGETS:
        files = cache.setdefault(repo, list_repo_files(repo))
        wanted = tuple(n.format(quant=args.quant) for n in needles)
        remote = pick(files, wanted)
        if remote is None:
            print(f"[건너뜀] {label}: {' + '.join(wanted)} 에 맞는 파일이 없습니다.")
            missing = True
            continue

        dest_dir = args.comfy / subdir
        dest_dir.mkdir(parents=True, exist_ok=True)
        print(f"[받는 중] {label}: {remote}")
        path = hf_hub_download(repo, remote, local_dir=str(dest_dir))
        # 리포의 하위 폴더 구조가 그대로 생기면 ComfyUI가 못 찾으므로 평탄화한다.
        final = dest_dir / Path(remote).name
        if Path(path) != final:
            Path(path).replace(final)
            print(f"           → {final}")
        resolved.append((label, final.name))

    if resolved:
        print("\nconfig.toml [models] 에 아래 이름을 넣으세요:")
        keys = {"high-noise 전문가": "high_noise", "low-noise 전문가": "low_noise",
                "텍스트 인코더": "clip", "VAE": "vae"}
        for label, name in resolved:
            print(f'  {keys[label]:<10} = "{name}"')

    if missing:
        print("\n일부 파일을 찾지 못했습니다. `--list`로 실제 파일명을 확인하고 직접 받으세요.")
        return 1
    return 0


def _fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
