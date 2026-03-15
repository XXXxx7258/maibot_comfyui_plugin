import time
import unittest


class TestGenerationGuard(unittest.TestCase):
    def _build_guard(self):
        from plugins.maibot_comfyui_plugin.generation_guard import GenerationGuard

        return GenerationGuard(
            control_config={
                "admin_ids": ["1"],
                "whitelist_group_ids": ["10001"],
                "group_policies": {"10001": "full"},
                "default_group_policy": "lite",
                "default_private_policy": "none",
                "cooldown_seconds": 10,
                "lockdown": False,
                "admin_bypass_whitelist": True,
                "admin_bypass_cooldown": True,
                "admin_bypass_sensitive_words": True,
            },
            lexicon={
                "legacy_lite": ["bad"],
                "full": ["worse"],
            },
            time_func=lambda: 1000.0,
        )

    def test_non_admin_group_whitelist_is_blocked(self):
        guard = self._build_guard()
        result = guard.check_access(user_id="42", group_id="99999", is_group=True)
        self.assertFalse(result.allowed)
        self.assertIn("白名单", result.message)

    def test_admin_can_bypass_group_whitelist(self):
        guard = self._build_guard()
        result = guard.check_access(user_id="1", group_id="99999", is_group=True)
        self.assertTrue(result.allowed)

    def test_group_policy_prefers_group_specific_setting(self):
        guard = self._build_guard()
        policy = guard.resolve_policy(group_id="10001", is_group=True)
        self.assertEqual(policy, "full")

    def test_sensitive_words_block_under_lite_policy(self):
        guard = self._build_guard()
        result = guard.check_sensitive(prompt="this is bad", policy="lite", is_admin=False)
        self.assertFalse(result.allowed)
        self.assertEqual(result.matched_words, ["bad"])

    def test_first_cooldown_passes_second_blocks(self):
        current = {"value": 1000.0}

        def fake_time():
            return current["value"]

        from plugins.maibot_comfyui_plugin.generation_guard import GenerationGuard

        guard = GenerationGuard(
            control_config={
                "admin_ids": [],
                "whitelist_group_ids": [],
                "group_policies": {},
                "default_group_policy": "lite",
                "default_private_policy": "none",
                "cooldown_seconds": 10,
                "lockdown": False,
                "admin_bypass_whitelist": True,
                "admin_bypass_cooldown": True,
                "admin_bypass_sensitive_words": True,
            },
            lexicon={"legacy_lite": [], "full": []},
            time_func=fake_time,
        )

        first = guard.check_cooldown(user_id="42", is_admin=False)
        current["value"] = 1005.0
        second = guard.check_cooldown(user_id="42", is_admin=False)

        self.assertTrue(first.allowed)
        self.assertFalse(second.allowed)
        self.assertEqual(second.remain_seconds, 5)
