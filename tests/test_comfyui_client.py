import unittest


class TestComfyUIClient(unittest.TestCase):
    def test_prepare_workflow_sets_prompt_negative_and_steps(self):
        from plugins.maibot_comfyui_plugin.comfyui_client import ComfyUIClient

        client = ComfyUIClient(
            server_config={"address": "127.0.0.1:8188", "timeout_seconds": 120},
            workflow_config={
                "input_node_id": "6",
                "neg_node_id": "7",
                "output_node_id": "",
            },
        )

        workflow = {
            "6": {"inputs": {"text": "old positive"}},
            "7": {"inputs": {"text": "old negative"}},
            "31": {"inputs": {"steps": 24}},
        }

        updated = client.prepare_workflow(
            workflow=workflow,
            prompt="new positive",
            negative_prompt="new negative",
            step_overrides={"31": {"steps": 12}},
        )

        self.assertEqual(updated["6"]["inputs"]["text"], "new positive")
        self.assertEqual(updated["7"]["inputs"]["text"], "new negative")
        self.assertEqual(updated["31"]["inputs"]["steps"], 12)
