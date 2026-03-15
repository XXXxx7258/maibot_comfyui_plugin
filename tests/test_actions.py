import unittest

from src.plugin_system import ActionActivationType


class TestActions(unittest.TestCase):
    def test_action_is_always_visible_to_llm(self):
        from plugins.maibot_comfyui_plugin.actions import ComfyUIDrawAction

        self.assertEqual(ComfyUIDrawAction.activation_type, ActionActivationType.ALWAYS)

    def test_action_declares_prompt_parameter(self):
        from plugins.maibot_comfyui_plugin.actions import ComfyUIDrawAction

        self.assertIn("prompt", ComfyUIDrawAction.action_parameters)
