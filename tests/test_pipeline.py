"""가짜 ComfyUI를 상대로 파이프라인 전체를 돌려본다.

실행: python tests/test_pipeline.py
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from PIL import Image  # noqa: E402

from fake_comfy import FakeComfy  # noqa: E402
from i2v import config as cfgmod  # noqa: E402
from i2v import frames as fx  # noqa: E402
from i2v import pipeline as pipemod  # noqa: E402
from i2v import workflow as wf  # noqa: E402

PASS, FAIL = 0, 0


def check(label: str, condition: bool, detail: str = "") -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ok   {label}")
    else:
        FAIL += 1
        print(f"  FAIL {label} {detail}")


CONFIG = """
[comfy]
url = "{url}"
workflow = "{workflow}"
poll_interval = 0.01

[models]
high_noise = "high.gguf"
low_noise = "low.gguf"
clip = "umt5.safetensors"
vae = "wan_vae.safetensors"

[video]
width = 64
height = 112
fps = 16
clip_frames = 9
target_seconds = 1.5

[sampling]
steps = 8
boundary = 0.5
seed = 100

[chain]
color_anchor = 0.5

[paths]
work = "work"
out = "out"

[[shots]]
keyframe = "images/a.png"
clips = 2
prompt = "첫 번째 샷"

[[shots]]
clips = 2
prompt = "이어지는 샷"
"""


def build_workspace(tmp: Path, url: str) -> Path:
    (tmp / "images").mkdir(parents=True)
    Image.new("RGB", (200, 400), (200, 60, 60)).save(tmp / "images" / "a.png")
    shutil.copytree(ROOT / "workflows", tmp / "workflows")
    path = tmp / "config.toml"
    path.write_text(
        CONFIG.format(url=url, workflow="workflows/wan22_i2v_gguf_api.json"), encoding="utf-8"
    )
    return path


def test_config_validation() -> None:
    print("config 검증")
    cases = [
        ("clip_frames = 9", "clip_frames = 80", "clip_frames가 4n+1이 아님"),
        ("width = 64", "width = 100", "width가 16의 배수가 아님"),
        ("boundary = 0.5", "boundary = 1.5", "boundary가 범위 밖"),
        ('seed_mode = "increment"', 'seed_mode = "nope"', "알 수 없는 seed_mode"),
        ("[chain]", "[chain]\ncolour_anchor = 1", "오타 난 설정 키"),
    ]
    base = CONFIG.replace('seed = 100', 'seed = 100\nseed_mode = "increment"')
    for token, replacement, why in cases:
        body = base.replace(token, replacement)
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            (tmp / "images").mkdir()
            Image.new("RGB", (10, 10)).save(tmp / "images" / "a.png")
            (tmp / "config.toml").write_text(
                body.format(url="http://x", workflow="w.json"), encoding="utf-8"
            )
            try:
                cfgmod.load(tmp / "config.toml")
                check(why, False, "ConfigError가 나야 함")
            except cfgmod.ConfigError:
                check(why, True)


def test_workflow_build(cfg: cfgmod.Config) -> None:
    print("workflow 패치")
    base = wf.load_graph(cfg.comfy.workflow)
    graph, nodes = wf.build(
        cfg, base, prompt="P", negative="N", image_name="x.png", seed=7, filename_prefix="pre"
    )
    check("원본 그래프 불변", base[nodes.positive]["inputs"]["text"] == "")
    check("프롬프트 주입", graph[nodes.positive]["inputs"]["text"] == "P")
    check("네거티브 주입", graph[nodes.negative]["inputs"]["text"] == "N")
    check("해상도 주입", graph[nodes.wan_i2v]["inputs"]["width"] == 64)
    check("length 주입", graph[nodes.wan_i2v]["inputs"]["length"] == 9)
    high, low = graph[nodes.high_sampler]["inputs"], graph[nodes.low_sampler]["inputs"]
    check("high는 노이즈 추가", high["add_noise"] == "enable")
    check("low는 노이즈 미추가", low["add_noise"] == "disable")
    check("스텝 경계 연속", high["end_at_step"] == low["start_at_step"] == 4,
          f'{high["end_at_step"]} vs {low["start_at_step"]}')
    check("high가 leftover noise 유지", high["return_with_leftover_noise"] == "enable")
    check("시드 일치", high["noise_seed"] == low["noise_seed"] == 7)
    check("GGUF 이름 주입", graph[nodes.high_unet]["inputs"]["unet_name"] == "high.gguf")

    # 그래프의 역할 탐색이 노드 ID에 의존하지 않는지: ID를 전부 바꿔도 동작해야 한다.
    remapped = _remap_ids(base)
    nodes2 = wf.resolve(remapped)
    check("노드 ID를 바꿔도 해석 성공", remapped[nodes2.high_sampler]["class_type"] == "KSamplerAdvanced")

    speed_cfg = cfgmod.load(cfg.source)
    speed_cfg.speed.enabled = True
    speed_cfg.speed.high_lora, speed_cfg.speed.low_lora = "h.safetensors", "l.safetensors"
    g2, n2 = wf.build(
        speed_cfg, base, prompt="P", negative="N", image_name="x.png", seed=1, filename_prefix="p"
    )
    loras = [k for k, v in g2.items() if v["class_type"] == "LoraLoaderModelOnly"]
    check("LoRA 2개 삽입", len(loras) == 2, str(loras))
    check("LoRA 삽입 후 스텝 수 변경", g2[n2.high_sampler]["inputs"]["steps"] == 6)
    high_chain, _ = wf._walk_to_unet(g2, g2[n2.high_sampler]["inputs"]["model"][0])
    check("LoRA 경유해도 UNet 추적 성공", high_chain == n2.high_unet)


def _remap_ids(graph: dict) -> dict:
    mapping = {nid: f"n{i * 7 + 3}" for i, nid in enumerate(graph)}
    out = {}
    for nid, node in graph.items():
        new = {"class_type": node["class_type"], "inputs": {}}
        for key, value in node["inputs"].items():
            if isinstance(value, list) and len(value) == 2 and str(value[0]) in mapping:
                new["inputs"][key] = [mapping[str(value[0])], value[1]]
            else:
                new["inputs"][key] = value
        out[mapping[nid]] = new
    return out


def test_plan(cfg: cfgmod.Config) -> None:
    print("클립 계획")
    plans = pipemod.plan_clips(cfg)
    check("클립 수", len(plans) == 4, str(len(plans)))
    check("0번은 키프레임 시작", plans[0].keyframe is not None)
    check("1번은 체이닝", plans[1].keyframe is None)
    check("2번(키프레임 없는 샷)도 체이닝", plans[2].keyframe is None)
    check("시드 증가", [p.seed for p in plans] == [100, 101, 102, 103], str([p.seed for p in plans]))
    check("샷 번호 매핑", [p.shot for p in plans] == [0, 0, 1, 1])


def test_color_anchor(tmp: Path) -> None:
    print("색 드리프트 보정")
    ref = tmp / "ref.png"
    drifted = tmp / "drift.png"
    Image.new("RGB", (32, 32), (120, 120, 120)).save(ref)
    Image.new("RGB", (32, 32), (30, 200, 90)).save(drifted)

    full = fx.color_anchor(drifted, ref, 1.0, tmp / "full.png")
    with Image.open(full) as img:
        px = img.getpixel((5, 5))
    check("strength=1이면 기준 색으로 수렴", all(abs(c - 120) <= 2 for c in px), str(px))

    off = fx.color_anchor(drifted, ref, 0.0, tmp / "off.png")
    with Image.open(off) as img:
        check("strength=0이면 원본 유지", img.getpixel((5, 5)) == (30, 200, 90))

    half = fx.color_anchor(drifted, ref, 0.5, tmp / "half.png")
    with Image.open(half) as img:
        r = img.getpixel((5, 5))[0]
    check("strength=0.5는 중간값", 70 <= r <= 80, str(r))


def test_full_run(cfg: cfgmod.Config, server: FakeComfy) -> None:
    print("전체 실행 (가짜 ComfyUI)")
    pipe = pipemod.Pipeline(cfg, report=lambda _: None)
    plans = pipemod.plan_clips(cfg)
    results = pipe.run(plans)

    check("클립 4개 생성", len(results) == 4)
    check("업로드 4회", len(server.uploads) == 4, str(len(server.uploads)))
    check("mp4 파일 존재", all(Path(r.video).is_file() for r in results))
    check("last.png 존재", all(Path(r.last_frame).is_file() for r in results))

    frame_dir = Path(results[0].video).with_suffix("") / "frames"
    check("겹침 프레임 제거", len(list(frame_dir.glob("*.png"))) == 8,
          str(len(list(frame_dir.glob("*.png")))))

    # 두 번째 클립은 첫 클립의 끝프레임에서 이어져야 한다.
    graph = server.graphs[1]
    load = next(v for v in graph.values() if v["class_type"] == "LoadImage")
    check("체이닝 클립도 업로드 이미지 사용", load["inputs"]["image"].endswith(".png"))
    check("클립마다 다른 시드", len({g and _seed(g) for g in server.graphs}) == 4)

    out = pipe.assemble(results, "test")
    check("최종 mp4 생성", out.is_file())
    check("최종 길이 = target", abs(_duration(out) - cfg.video.target_seconds) < 0.2,
          f"{_duration(out):.2f}s")

    # 재개: 다시 돌리면 새 작업을 큐에 넣지 않아야 한다.
    before = len(server.graphs)
    pipemod.Pipeline(cfg, report=lambda _: None).run(plans)
    check("재실행 시 전부 건너뜀", len(server.graphs) == before, f"+{len(server.graphs) - before}")


def _seed(graph: dict) -> int:
    return next(v["inputs"]["noise_seed"] for v in graph.values() if v["class_type"] == "KSamplerAdvanced")


def _duration(path: Path) -> float:
    import subprocess

    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True,
    )
    return float(out.stdout.strip())


def main() -> int:
    test_config_validation()
    with tempfile.TemporaryDirectory() as d, FakeComfy() as server:
        tmp = Path(d)
        cfg_path = build_workspace(tmp, server.url)
        cfg = cfgmod.load(cfg_path)
        test_workflow_build(cfg)
        test_plan(cfg)
        test_color_anchor(tmp)
        if shutil.which("ffmpeg") and shutil.which("ffprobe"):
            test_full_run(cfg, server)
        else:
            print("전체 실행 (가짜 ComfyUI)\n  skip ffmpeg/ffprobe 없음")
    print(f"\n{PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
