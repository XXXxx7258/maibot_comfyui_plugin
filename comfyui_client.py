from __future__ import annotations

import asyncio
import base64
import json
from copy import deepcopy
from pathlib import Path

import aiohttp


class ComfyUIClient:
    def __init__(self, server_config: dict, workflow_config: dict, workflow_dir: Path | str | None = None) -> None:
        self.server_config = server_config or {}
        self.workflow_config = workflow_config or {}
        self.workflow_dir = Path(workflow_dir) if workflow_dir else None

    def prepare_workflow(
        self,
        workflow: dict,
        prompt: str,
        negative_prompt: str = "",
        step_overrides: dict | None = None,
    ) -> dict:
        updated = deepcopy(workflow)

        input_node_id = str(self.workflow_config.get("input_node_id", ""))
        neg_node_id = str(self.workflow_config.get("neg_node_id", ""))

        if input_node_id and input_node_id in updated:
            updated.setdefault(input_node_id, {}).setdefault("inputs", {})["text"] = prompt

        if negative_prompt and neg_node_id and neg_node_id in updated:
            updated.setdefault(neg_node_id, {}).setdefault("inputs", {})["text"] = negative_prompt

        for node_id, override in (step_overrides or {}).items():
            if node_id in updated and isinstance(override, dict):
                for key, value in override.items():
                    updated.setdefault(node_id, {}).setdefault("inputs", {})[key] = value

        return updated

    def load_workflow(self, workflow_name: str) -> dict:
        if self.workflow_dir is None:
            raise FileNotFoundError("未配置 workflow 目录")

        workflow_path = self.workflow_dir / workflow_name
        with open(workflow_path, "r", encoding="utf-8") as file:
            return json.load(file)

    async def generate_image(
        self,
        *,
        workflow_name: str,
        prompt: str,
        negative_prompt: str = "",
        step_overrides: dict | None = None,
    ) -> dict:
        workflow = self.load_workflow(workflow_name)
        prepared_workflow = self.prepare_workflow(
            workflow=workflow,
            prompt=prompt,
            negative_prompt=negative_prompt,
            step_overrides=step_overrides,
        )

        address = self.server_config.get("address", "127.0.0.1:8188")
        timeout_seconds = int(self.server_config.get("timeout_seconds", 120) or 120)
        base_url = f"http://{address}"
        timeout = aiohttp.ClientTimeout(total=timeout_seconds)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(f"{base_url}/prompt", json={"prompt": prepared_workflow}) as response:
                response.raise_for_status()
                payload = await response.json()

            prompt_id = payload.get("prompt_id")
            if not prompt_id:
                raise RuntimeError("ComfyUI 未返回 prompt_id")

            image_info = None
            for _ in range(timeout_seconds):
                await asyncio.sleep(1)
                async with session.get(f"{base_url}/history/{prompt_id}") as response:
                    if response.status != 200:
                        continue
                    history = await response.json()

                if prompt_id not in history:
                    continue

                outputs = history[prompt_id].get("outputs", {})
                output_node_id = str(self.workflow_config.get("output_node_id", "") or "")
                if output_node_id and output_node_id in outputs and outputs[output_node_id].get("images"):
                    image_info = outputs[output_node_id]["images"][0]
                else:
                    for node_output in outputs.values():
                        images = node_output.get("images", [])
                        if images:
                            image_info = images[0]
                            break
                if image_info:
                    break

            if not image_info:
                raise TimeoutError("ComfyUI 生成超时或未找到输出图片")

            image_url = (
                f"{base_url}/view?filename={image_info['filename']}"
                f"&subfolder={image_info['subfolder']}&type={image_info['type']}"
            )
            async with session.get(image_url) as response:
                response.raise_for_status()
                image_bytes = await response.read()

        return {
            "workflow_name": workflow_name,
            "image_base64": base64.b64encode(image_bytes).decode("utf-8"),
            "prompt_id": prompt_id,
        }
