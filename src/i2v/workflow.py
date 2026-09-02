"""ComfyUI API 그래프를 클립마다 패치한다.

노드 ID를 하드코딩하지 않고 class_type과 연결 관계로 역할을 찾아내므로,
workflows/*.json을 사용자가 조금 고쳐도 계속 동작한다.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import Config

Graph = dict[str, dict[str, Any]]

# model 입력을 그대로 통과시키는 래퍼 노드들 (UNet 로더를 찾을 때 건너뛴다)
_MODEL_PASSTHROUGH = {
    "ModelSamplingSD3",
    "ModelSamplingAuraFlow",
    "LoraLoaderModelOnly",
    "CFGNorm",
    "PathchSageAttentionKJ",
}
_UNET_LOADERS = {"UnetLoaderGGUF", "UnetLoaderGGUFAdvanced", "UNETLoader"}


class WorkflowError(ValueError):
    """워크플로 그래프가 기대한 모양이 아닐 때."""


@dataclass(frozen=True)
class NodeMap:
    """그래프에서 찾아낸 역할별 노드 ID."""

    wan_i2v: str
    positive: str
    negative: str
    clip: str
    vae: str
    load_image: str
    save: str
    high_sampler: str
    low_sampler: str
    high_unet: str
    low_unet: str
    shift_nodes: tuple[str, ...]


def load_graph(path: str | Path) -> Graph:
    path = Path(path)
    if not path.is_file():
        raise WorkflowError(f"워크플로 파일이 없습니다: {path}")
    graph = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(graph, dict) or not graph:
        raise WorkflowError(f"{path}는 ComfyUI API 형식(JSON 객체)이 아닙니다.")
    for node_id, node in graph.items():
        if "class_type" not in node:
            raise WorkflowError(
                f"노드 {node_id}에 class_type이 없습니다. "
                "ComfyUI에서 'Export (API)'로 저장한 파일인지 확인하세요."
            )
    return graph


def _find_all(graph: Graph, class_type: str) -> list[str]:
    return [nid for nid, node in graph.items() if node.get("class_type") == class_type]


def _find_one(graph: Graph, class_type: str) -> str:
    found = _find_all(graph, class_type)
    if len(found) != 1:
        raise WorkflowError(
            f"{class_type} 노드가 정확히 1개여야 하는데 {len(found)}개 있습니다."
        )
    return found[0]


def _link_source(node: dict[str, Any], input_name: str) -> str:
    """노드 입력이 가리키는 상위 노드 ID."""
    value = node.get("inputs", {}).get(input_name)
    if not (isinstance(value, list) and len(value) == 2):
        raise WorkflowError(f"입력 '{input_name}'이 다른 노드에 연결돼 있지 않습니다.")
    return str(value[0])


def _walk_to_unet(graph: Graph, start: str) -> tuple[str, tuple[str, ...]]:
    """model 체인을 거슬러 올라가 UNet 로더를 찾고, 지나온 통과 노드들을 함께 돌려준다."""
    seen: list[str] = []
    node_id = start
    for _ in range(len(graph) + 1):
        node = graph[node_id]
        cls = node.get("class_type")
        if cls in _UNET_LOADERS:
            return node_id, tuple(seen)
        if cls not in _MODEL_PASSTHROUGH:
            raise WorkflowError(f"model 체인에서 예상 밖의 노드를 만났습니다: {cls}")
        seen.append(node_id)
        node_id = _link_source(node, "model")
    raise WorkflowError("model 체인에 순환이 있습니다.")


def resolve(graph: Graph) -> NodeMap:
    """그래프를 훑어 각 노드의 역할을 알아낸다."""
    wan = _find_one(graph, "WanImageToVideo")
    samplers = _find_all(graph, "KSamplerAdvanced")
    if len(samplers) != 2:
        raise WorkflowError(
            f"Wan 2.2 MoE는 KSamplerAdvanced 2개(high/low)가 필요합니다. 현재 {len(samplers)}개."
        )

    # latent를 WanImageToVideo에서 직접 받는 쪽이 high-noise 단계.
    high = next((s for s in samplers if _link_source(graph[s], "latent_image") == wan), None)
    if high is None:
        raise WorkflowError("latent_image를 WanImageToVideo에서 받는 샘플러를 찾지 못했습니다.")
    low = next(s for s in samplers if s != high)
    if _link_source(graph[low], "latent_image") != high:
        raise WorkflowError("두 번째 샘플러가 첫 번째 샘플러의 latent를 받고 있지 않습니다.")

    high_unet, high_pass = _walk_to_unet(graph, _link_source(graph[high], "model"))
    low_unet, low_pass = _walk_to_unet(graph, _link_source(graph[low], "model"))
    if high_unet == low_unet:
        raise WorkflowError(
            "high/low 샘플러가 같은 UNet을 쓰고 있습니다. "
            "Wan 2.2는 high-noise/low-noise 두 전문가 모델이 각각 필요합니다."
        )

    return NodeMap(
        wan_i2v=wan,
        positive=_link_source(graph[wan], "positive"),
        negative=_link_source(graph[wan], "negative"),
        clip=_find_one(graph, "CLIPLoader"),
        vae=_find_one(graph, "VAELoader"),
        load_image=_link_source(graph[wan], "start_image"),
        save=_find_one(graph, "SaveImage"),
        high_sampler=high,
        low_sampler=low,
        high_unet=high_unet,
        low_unet=low_unet,
        shift_nodes=high_pass + low_pass,
    )


def _insert_lora(graph: Graph, unet_id: str, consumer_id: str, lora: str, strength: float) -> None:
    """UNet 로더와 그 소비자 사이에 LoraLoaderModelOnly를 끼워 넣는다."""
    new_id = f"lora_{unet_id}"
    graph[new_id] = {
        "class_type": "LoraLoaderModelOnly",
        "_meta": {"title": f"speed LoRA ({unet_id})"},
        "inputs": {"model": [unet_id, 0], "lora_name": lora, "strength_model": strength},
    }
    graph[consumer_id]["inputs"]["model"] = [new_id, 0]


def _consumer_of(graph: Graph, unet_id: str) -> str:
    for nid, node in graph.items():
        value = node.get("inputs", {}).get("model")
        if isinstance(value, list) and len(value) == 2 and str(value[0]) == unet_id:
            return nid
    raise WorkflowError(f"UNet 노드 {unet_id}의 출력을 쓰는 노드가 없습니다.")


def build(
    cfg: Config,
    base: Graph,
    *,
    prompt: str,
    negative: str,
    image_name: str,
    seed: int,
    filename_prefix: str,
) -> tuple[Graph, NodeMap]:
    """클립 하나를 생성할 완성된 그래프와 노드 맵을 돌려준다."""
    graph = copy.deepcopy(base)
    nodes = resolve(graph)

    graph[nodes.high_unet]["inputs"]["unet_name"] = cfg.models.high_noise
    graph[nodes.low_unet]["inputs"]["unet_name"] = cfg.models.low_noise
    graph[nodes.clip]["inputs"]["clip_name"] = cfg.models.clip
    graph[nodes.vae]["inputs"]["vae_name"] = cfg.models.vae

    graph[nodes.positive]["inputs"]["text"] = prompt
    graph[nodes.negative]["inputs"]["text"] = negative
    graph[nodes.load_image]["inputs"]["image"] = image_name
    graph[nodes.save]["inputs"]["filename_prefix"] = filename_prefix

    graph[nodes.wan_i2v]["inputs"].update(
        width=cfg.video.width,
        height=cfg.video.height,
        length=cfg.video.clip_frames,
        batch_size=1,
    )

    for node_id in nodes.shift_nodes:
        if graph[node_id]["class_type"] == "ModelSamplingSD3":
            graph[node_id]["inputs"]["shift"] = cfg.sampling.shift

    if cfg.speed.enabled:
        # 소비자를 먼저 찾아둬야 삽입 후 링크가 꼬이지 않는다.
        high_consumer = _consumer_of(graph, nodes.high_unet)
        low_consumer = _consumer_of(graph, nodes.low_unet)
        _insert_lora(graph, nodes.high_unet, high_consumer, cfg.speed.high_lora, cfg.speed.strength)
        _insert_lora(graph, nodes.low_unet, low_consumer, cfg.speed.low_lora, cfg.speed.strength)

    steps = cfg.effective_steps
    switch = cfg.switch_step
    graph[nodes.high_sampler]["inputs"].update(
        add_noise="enable",
        noise_seed=seed,
        steps=steps,
        cfg=cfg.effective_cfg,
        sampler_name=cfg.sampling.sampler,
        scheduler=cfg.sampling.scheduler,
        start_at_step=0,
        end_at_step=switch,
        return_with_leftover_noise="enable",
    )
    graph[nodes.low_sampler]["inputs"].update(
        add_noise="disable",
        noise_seed=seed,
        steps=steps,
        cfg=cfg.effective_cfg,
        sampler_name=cfg.sampling.sampler,
        scheduler=cfg.sampling.scheduler,
        start_at_step=switch,
        end_at_step=10_000,
        return_with_leftover_noise="disable",
    )
    return graph, nodes
