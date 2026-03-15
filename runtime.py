from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import toml

from .comfyui_client import ComfyUIClient
from .generation_guard import GenerationGuard
from .generation_service import GenerationService
from .workflow_manager import WorkflowManager


PLUGIN_DIR = Path(__file__).resolve().parent


@dataclass
class PluginRuntime:
    plugin_dir: Path
    config_path: Path
    plugin_config: dict
    workflow_manager: WorkflowManager
    guard: GenerationGuard
    comfyui_client: ComfyUIClient
    generation_service: GenerationService

    def save_config(self) -> None:
        with open(self.config_path, "w", encoding="utf-8") as file:
            toml.dump(self.plugin_config, file)

    def set_workflow(
        self,
        workflow_name: str,
        *,
        input_node_id: str | None = None,
        neg_node_id: str | None = None,
        output_node_id: str | None = None,
    ) -> None:
        workflow_config = self.plugin_config.setdefault("workflow", {})
        workflow_config["default_json_file"] = workflow_name
        if input_node_id is not None:
            workflow_config["input_node_id"] = input_node_id
        if neg_node_id is not None:
            workflow_config["neg_node_id"] = neg_node_id
        if output_node_id is not None:
            workflow_config["output_node_id"] = output_node_id
        self.comfyui_client.workflow_config = workflow_config
        self.generation_service.workflow_config = workflow_config
        self.save_config()

    def set_group_policy(self, group_id: str, level: str) -> None:
        control_config = self.plugin_config.setdefault("control", {})
        group_policies = control_config.setdefault("group_policies", {})
        group_policies[str(group_id)] = level
        self.guard.group_policies[str(group_id)] = level
        self.save_config()


def _load_lexicon(plugin_dir: Path) -> dict:
    sensitive_path = plugin_dir / "sensitive_words.json"
    if not sensitive_path.exists():
        return {"legacy_lite": [], "full": []}

    with open(sensitive_path, "r", encoding="utf-8") as file:
        return json.load(file) or {"legacy_lite": [], "full": []}


def build_runtime(plugin_config: dict | None) -> PluginRuntime:
    plugin_dir = PLUGIN_DIR
    config_path = plugin_dir / "config.toml"
    plugin_config = plugin_config or {}
    workflow_manager = WorkflowManager(plugin_dir / "workflow")
    guard = GenerationGuard(plugin_config.get("control", {}), _load_lexicon(plugin_dir))
    comfyui_client = ComfyUIClient(
        server_config=plugin_config.get("server", {}),
        workflow_config=plugin_config.get("workflow", {}),
        workflow_dir=plugin_dir / "workflow",
    )
    generation_service = GenerationService(
        guard=guard,
        workflow_manager=workflow_manager,
        comfyui_client=comfyui_client,
        workflow_config=plugin_config.get("workflow", {}),
    )
    return PluginRuntime(
        plugin_dir=plugin_dir,
        config_path=config_path,
        plugin_config=plugin_config,
        workflow_manager=workflow_manager,
        guard=guard,
        comfyui_client=comfyui_client,
        generation_service=generation_service,
    )
