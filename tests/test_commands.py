import unittest
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase


class TestCommandMetadata(unittest.TestCase):
    def test_draw_command_pattern_matches(self):
        from plugins.maibot_comfyui_plugin.commands import DrawCommand

        self.assertEqual(DrawCommand.command_pattern, r"^/画图\s+(?P<prompt>.+)$")

    def test_help_command_has_expected_name(self):
        from plugins.maibot_comfyui_plugin.commands import ComfyHelpCommand

        self.assertEqual(ComfyHelpCommand.command_name, "comfy_help")


class TestCommandExecution(IsolatedAsyncioTestCase):
    async def test_draw_command_executes_service_and_sends_image(self):
        from plugins.maibot_comfyui_plugin.commands import DrawCommand

        class FakeService:
            async def generate(self, **kwargs):
                self.kwargs = kwargs
                return SimpleNamespace(
                    success=True,
                    message="ok",
                    image_base64="ZmFrZQ==",
                    normalized_prompt="cat girl",
                    workflow_name="workflow_api.json",
                )

        message = SimpleNamespace(raw_message="/画图 cat girl", chat_stream=SimpleNamespace(stream_id="stream-1"))
        service = FakeService()
        command = DrawCommand(message=message, plugin_config={}, service=service)
        command.set_matched_groups({"prompt": "cat girl"})

        sent = {}

        async def fake_send_image(image_base64, **kwargs):
            sent["image_base64"] = image_base64
            return True

        command.send_image = fake_send_image

        success, _, intercept = await command.execute()
        self.assertTrue(success)
        self.assertEqual(intercept, 2)
        self.assertEqual(sent["image_base64"], "ZmFrZQ==")

