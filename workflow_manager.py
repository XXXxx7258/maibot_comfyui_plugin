from __future__ import annotations

import json
from pathlib import Path


class WorkflowManager:
    def __init__(self, workflow_dir: Path | str) -> None:
        self.workflow_dir = Path(workflow_dir)
        self.workflow_dir.mkdir(parents=True, exist_ok=True)

    def list_workflows(self) -> list[str]:
        return sorted(
            file.name
            for file in self.workflow_dir.glob("*.json")
            if not file.name.endswith(".steps.json")
        )

    def get_workflow_path(self, workflow_name: str) -> Path:
        return self.workflow_dir / workflow_name

    def get_sidecar_path(self, workflow_name: str) -> Path:
        return self.workflow_dir / f"{Path(workflow_name).stem}.steps.json"

    def save_workflow(self, workflow_name: str, data: dict) -> Path:
        workflow_path = self.get_workflow_path(workflow_name)
        with open(workflow_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        return workflow_path

    def read_step_overrides(self, workflow_name: str) -> dict:
        sidecar_path = self.get_sidecar_path(workflow_name)
        if not sidecar_path.exists():
            return {}

        with open(sidecar_path, "r", encoding="utf-8") as file:
            return json.load(file) or {}

    def write_step_overrides(self, workflow_name: str, data: dict) -> None:
        sidecar_path = self.get_sidecar_path(workflow_name)
        if not data:
            if sidecar_path.exists():
                sidecar_path.unlink()
            return

        with open(sidecar_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
