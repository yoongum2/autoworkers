"""테스트용 가짜 ComfyUI 서버.

/prompt로 받은 그래프를 읽어 WanImageToVideo의 length만큼 단색 PNG를 만들어 돌려준다.
실제 GPU 없이 파이프라인 전체 흐름(업로드→큐→폴링→다운로드→인코딩→합치기)을 검증한다.
"""

from __future__ import annotations

import json
import threading
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from io import BytesIO
from urllib.parse import parse_qs, urlparse

from PIL import Image

OBJECT_INFO = {
    "UnetLoaderGGUF": {"input": {"required": {"unet_name": [["high.gguf", "low.gguf"]]}}},
    "CLIPLoader": {"input": {"required": {"clip_name": [["umt5.safetensors"]]}}},
    "VAELoader": {"input": {"required": {"vae_name": [["wan_vae.safetensors"]]}}},
    "ModelSamplingSD3": {"input": {"required": {}}},
    "CLIPTextEncode": {"input": {"required": {}}},
    "LoadImage": {"input": {"required": {}}},
    "WanImageToVideo": {"input": {"required": {}}},
    "KSamplerAdvanced": {"input": {"required": {}}},
    "VAEDecode": {"input": {"required": {}}},
    "SaveImage": {"input": {"required": {}}},
}


class FakeComfy:
    def __init__(self) -> None:
        self.jobs: dict[str, dict] = {}
        self.uploads: list[str] = []
        self.graphs: list[dict] = []
        self.server = HTTPServer(("127.0.0.1", 0), _make_handler(self))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.server.server_address[1]}"

    def __enter__(self) -> "FakeComfy":
        self.thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self.server.shutdown()
        self.server.server_close()


def _make_handler(state: FakeComfy):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args: object) -> None:  # 조용히
            pass

        def _send(self, code: int, body: bytes, content_type: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _json(self, payload: object, code: int = 200) -> None:
            self._send(code, json.dumps(payload).encode(), "application/json")

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path == "/system_stats":
                self._json({"devices": [{"name": "FakeGPU", "vram_total": 2**33, "vram_free": 2**32}]})
            elif parsed.path == "/object_info":
                self._json(OBJECT_INFO)
            elif parsed.path.startswith("/history/"):
                job = state.jobs.get(parsed.path.rsplit("/", 1)[1])
                self._json({} if job is None else {job["id"]: job["entry"]})
            elif parsed.path == "/view":
                query = parse_qs(parsed.query)
                index = int(query["filename"][0].split("_")[-1].split(".")[0])
                buf = BytesIO()
                # 프레임마다 조금씩 다른 색 → 색 보정 로직이 실제로 동작하는지 확인 가능
                Image.new("RGB", (64, 112), (index * 3 % 256, 90, 140)).save(buf, "PNG")
                self._send(200, buf.getvalue(), "image/png")
            else:
                self._json({"error": "not found"}, 404)

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)

            if parsed.path == "/upload/image":
                state.uploads.append(str(len(raw)))
                self._json({"name": f"up_{len(state.uploads)}.png", "subfolder": "i2v"})
            elif parsed.path == "/prompt":
                graph = json.loads(raw)["prompt"]
                state.graphs.append(graph)
                job_id = str(uuid.uuid4())
                save = next(n for n, v in graph.items() if v["class_type"] == "SaveImage")
                wan = next(n for n, v in graph.items() if v["class_type"] == "WanImageToVideo")
                count = graph[wan]["inputs"]["length"]
                prefix = graph[save]["inputs"]["filename_prefix"]
                images = [
                    {"filename": f"{prefix.split('/')[-1]}_{i:05d}.png", "subfolder": "i2v", "type": "output"}
                    for i in range(count)
                ]
                state.jobs[job_id] = {
                    "id": job_id,
                    "entry": {"outputs": {save: {"images": images}}, "status": {"completed": True}},
                }
                self._json({"prompt_id": job_id})
            elif parsed.path == "/interrupt":
                self._json({})
            else:
                self._json({"error": "not found"}, 404)

    return Handler
