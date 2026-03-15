import importlib
import json
import unittest
from pathlib import Path


class TestPluginScaffold(unittest.TestCase):
    def test_plugin_module_can_be_imported(self):
        module = importlib.import_module("plugins.maibot_comfyui_plugin.plugin")
        self.assertTrue(hasattr(module, "MaiBotComfyUIPlugin"))

    def test_manifest_has_required_fields(self):
        manifest_path = Path("plugins/maibot_comfyui_plugin/_manifest.json")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["manifest_version"], 1)
        self.assertIn("name", manifest)
        self.assertIn("description", manifest)
