"""ComfyUI HTTP API 클라이언트.

ComfyUI가 같은 PC에 있든 LAN 너머에 있든 동일하게 동작하도록,
결과 프레임은 파일시스템이 아니라 /view 엔드포인트로 받아온다.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import requests


class ComfyError(RuntimeError):
    """ComfyUI 호출 실패."""


@dataclass(frozen=True)
class ImageRef:
    """ComfyUI가 돌려주는 이미지 핸들."""

    filename: str
    subfolder: str
    type: str

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "ImageRef":
        return cls(
            filename=raw["filename"],
            subfolder=raw.get("subfolder", ""),
            type=raw.get("type", "output"),
        )


class ComfyClient:
    def __init__(
        self,
        url: str = "http://127.0.0.1:8188",
        *,
        timeout: float = 3600.0,
        poll_interval: float = 2.0,
        session: requests.Session | None = None,
    ) -> None:
        self.url = url.rstrip("/")
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.client_id = str(uuid.uuid4())
        self._session = session or requests.Session()

    # ------------------------------------------------------------------ 저수준

    def _get(self, path: str, **kwargs: Any) -> requests.Response:
        try:
            resp = self._session.get(f"{self.url}{path}", timeout=60, **kwargs)
        except requests.RequestException as exc:
            raise ComfyError(f"GET {path} 실패: {exc}") from exc
        if resp.status_code >= 400:
            raise ComfyError(f"GET {path} → HTTP {resp.status_code}: {resp.text[:400]}")
        return resp

    def ping(self) -> dict[str, Any]:
        """서버가 살아있는지 확인하고 시스템 정보를 돌려준다."""
        return self._get("/system_stats").json()

    def object_info(self) -> dict[str, Any]:
        return self._get("/object_info").json()

    # ------------------------------------------------------------------ 입력

    def upload_image(self, path: str | Path, *, subfolder: str = "i2v") -> str:
        """이미지를 ComfyUI input 폴더에 올리고 LoadImage용 이름을 돌려준다."""
        path = Path(path)
        if not path.is_file():
            raise ComfyError(f"업로드할 이미지가 없습니다: {path}")
        with path.open("rb") as fh:
            files = {"image": (path.name, fh, "image/png")}
            data = {"overwrite": "true", "type": "input", "subfolder": subfolder}
            try:
                resp = self._session.post(
                    f"{self.url}/upload/image", files=files, data=data, timeout=120
                )
            except requests.RequestException as exc:
                raise ComfyError(f"이미지 업로드 실패: {exc}") from exc
        if resp.status_code >= 400:
            raise ComfyError(f"이미지 업로드 → HTTP {resp.status_code}: {resp.text[:400]}")
        body = resp.json()
        name = body["name"]
        folder = body.get("subfolder") or ""
        return f"{folder}/{name}" if folder else name

    # ------------------------------------------------------------------ 실행

    def queue(self, prompt: dict[str, Any]) -> str:
        payload = {"prompt": prompt, "client_id": self.client_id}
        try:
            resp = self._session.post(f"{self.url}/prompt", json=payload, timeout=120)
        except requests.RequestException as exc:
            raise ComfyError(f"작업 제출 실패: {exc}") from exc
        if resp.status_code >= 400:
            # ComfyUI는 그래프 검증 오류를 JSON으로 자세히 돌려준다.
            raise ComfyError(f"그래프 검증 실패 (HTTP {resp.status_code}):\n{resp.text[:2000]}")
        return resp.json()["prompt_id"]

    def wait(
        self,
        prompt_id: str,
        *,
        on_tick: Callable[[float], None] | None = None,
    ) -> dict[str, Any]:
        """작업이 끝날 때까지 /history를 폴링하고 outputs를 돌려준다."""
        started = time.monotonic()
        while True:
            history = self._get(f"/history/{prompt_id}").json()
            entry = history.get(prompt_id)
            if entry:
                status = entry.get("status", {})
                if status.get("completed") or status.get("status_str") == "success":
                    return entry.get("outputs", {})
                if status.get("status_str") == "error":
                    raise ComfyError(f"실행 오류: {_describe_error(status)}")

            elapsed = time.monotonic() - started
            if elapsed > self.timeout:
                self.interrupt()
                raise ComfyError(f"{self.timeout:.0f}초 안에 끝나지 않아 중단했습니다 ({prompt_id}).")
            if on_tick:
                on_tick(elapsed)
            time.sleep(self.poll_interval)

    def interrupt(self) -> None:
        try:
            self._session.post(f"{self.url}/interrupt", timeout=30)
        except requests.RequestException:
            pass  # 정리용 호출이라 실패해도 진행

    # ------------------------------------------------------------------ 출력

    @staticmethod
    def images_from(outputs: dict[str, Any], node_id: str) -> list[ImageRef]:
        node_out = outputs.get(node_id)
        if not node_out or "images" not in node_out:
            raise ComfyError(
                f"노드 {node_id}의 이미지 출력이 없습니다. "
                f"받은 출력 노드: {', '.join(outputs) or '(없음)'}"
            )
        return [ImageRef.from_dict(item) for item in node_out["images"]]

    def download(self, ref: ImageRef, dest: Path) -> Path:
        params = {"filename": ref.filename, "subfolder": ref.subfolder, "type": ref.type}
        resp = self._get("/view", params=params)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(resp.content)
        return dest


def _describe_error(status: dict[str, Any]) -> str:
    """history의 messages 배열에서 사람이 읽을 만한 오류 설명을 뽑아낸다."""
    details: list[str] = []
    for message in status.get("messages", []):
        if not (isinstance(message, list) and len(message) == 2):
            continue
        kind, body = message
        if kind not in ("execution_error", "execution_interrupted"):
            continue
        if isinstance(body, dict):
            node = body.get("node_type", body.get("node_id", "?"))
            details.append(f"[{node}] {body.get('exception_message', kind)}")
    return " / ".join(details) or "알 수 없는 오류 (ComfyUI 콘솔 로그를 확인하세요)"
