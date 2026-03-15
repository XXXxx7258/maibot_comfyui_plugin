import unittest
from unittest import IsolatedAsyncioTestCase


class TestPromptBuilder(unittest.TestCase):
    def test_normalize_prompt_trims_whitespace(self):
        from plugins.maibot_comfyui_plugin.prompt_builder import normalize_prompt

        self.assertEqual(normalize_prompt("  cat   girl  "), "cat girl")


class TestGenerationService(IsolatedAsyncioTestCase):
    async def test_generate_stops_when_access_denied(self):
        from plugins.maibot_comfyui_plugin.generation_service import GenerationService

        class Guard:
            def check_access(self, **kwargs):
                from plugins.maibot_comfyui_plugin.generation_guard import GuardResult

                return GuardResult(False, "denied")

        class WorkflowManager:
            def read_step_overrides(self, workflow_name):
                return {}

        class Client:
            async def generate_image(self, **kwargs):
                raise AssertionError("client should not be called")

        service = GenerationService(
            guard=Guard(),
            workflow_manager=WorkflowManager(),
            comfyui_client=Client(),
            workflow_config={"default_json_file": "workflow_api.json"},
        )

        result = await service.generate(user_id="42", group_id="10001", is_group=True, prompt=" cat ")
        self.assertFalse(result.success)
        self.assertEqual(result.message, "denied")

    async def test_generate_returns_image_base64_on_success(self):
        from plugins.maibot_comfyui_plugin.generation_service import GenerationService
        from plugins.maibot_comfyui_plugin.generation_guard import GuardResult

        class Guard:
            def check_access(self, **kwargs):
                return GuardResult(True)

            def check_cooldown(self, **kwargs):
                return GuardResult(True)

            def resolve_policy(self, **kwargs):
                return "lite"

            def check_sensitive(self, **kwargs):
                return GuardResult(True)

            def is_admin(self, user_id):
                return False

        class WorkflowManager:
            def read_step_overrides(self, workflow_name):
                return {"3839": {"steps": 20}}

        class Client:
            async def generate_image(self, **kwargs):
                return {"image_base64": "ZmFrZQ==", "workflow_name": kwargs["workflow_name"]}

        service = GenerationService(
            guard=Guard(),
            workflow_manager=WorkflowManager(),
            comfyui_client=Client(),
            workflow_config={"default_json_file": "workflow_api.json"},
        )

        result = await service.generate(user_id="42", group_id="10001", is_group=True, prompt="  cat   girl ")
        self.assertTrue(result.success)
        self.assertEqual(result.image_base64, "ZmFrZQ==")
        self.assertEqual(result.normalized_prompt, "cat girl")
        self.assertEqual(result.workflow_name, "workflow_api.json")
