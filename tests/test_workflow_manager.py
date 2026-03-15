import json
import tempfile
import unittest
from pathlib import Path


class TestWorkflowManager(unittest.TestCase):
    def test_list_workflows_ignores_steps_sidecar(self):
        from plugins.maibot_comfyui_plugin.workflow_manager import WorkflowManager

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.json").write_text("{}", encoding="utf-8")
            (root / "a.steps.json").write_text(json.dumps({"1": {"steps": 20}}), encoding="utf-8")

            manager = WorkflowManager(root)
            self.assertEqual(manager.list_workflows(), ["a.json"])

    def test_read_step_overrides_returns_empty_dict_when_missing(self):
        from plugins.maibot_comfyui_plugin.workflow_manager import WorkflowManager

        with tempfile.TemporaryDirectory() as tmp:
            manager = WorkflowManager(Path(tmp))
            self.assertEqual(manager.read_step_overrides("missing.json"), {})

    def test_write_step_overrides_persists_sidecar(self):
        from plugins.maibot_comfyui_plugin.workflow_manager import WorkflowManager

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manager = WorkflowManager(root)

            manager.write_step_overrides("demo.json", {"3839": {"steps": 20}})
            content = json.loads((root / "demo.steps.json").read_text(encoding="utf-8"))
            self.assertEqual(content, {"3839": {"steps": 20}})

    def test_clear_sidecar_when_overrides_empty(self):
        from plugins.maibot_comfyui_plugin.workflow_manager import WorkflowManager

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sidecar = root / "demo.steps.json"
            sidecar.write_text(json.dumps({"1": {"steps": 10}}), encoding="utf-8")

            manager = WorkflowManager(root)
            manager.write_step_overrides("demo.json", {})

            self.assertFalse(sidecar.exists())
