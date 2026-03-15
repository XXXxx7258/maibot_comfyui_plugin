from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class GuardResult:
    allowed: bool
    message: str = ""
    remain_seconds: int = 0
    matched_words: list[str] = field(default_factory=list)


class GenerationGuard:
    def __init__(
        self,
        control_config: dict,
        lexicon: dict,
        time_func: Callable[[], float] | None = None,
    ) -> None:
        self.control_config = control_config or {}
        self.lexicon = lexicon or {}
        self.time_func = time_func or __import__("time").time
        self._cooldowns: dict[str, float] = {}

        self.admin_ids = {str(item) for item in self.control_config.get("admin_ids", [])}
        self.whitelist_group_ids = {str(item) for item in self.control_config.get("whitelist_group_ids", [])}
        self.group_policies = {
            str(key): str(value).lower()
            for key, value in self.control_config.get("group_policies", {}).items()
        }

    def is_admin(self, user_id: str) -> bool:
        return str(user_id) in self.admin_ids

    def resolve_policy(self, group_id: str | None, is_group: bool) -> str:
        if is_group:
            if group_id is not None and str(group_id) in self.group_policies:
                return self.group_policies[str(group_id)]
            return str(self.control_config.get("default_group_policy", "lite")).lower()
        return str(self.control_config.get("default_private_policy", "none")).lower()

    def check_access(self, user_id: str, group_id: str | None, is_group: bool) -> GuardResult:
        is_admin = self.is_admin(user_id)

        if self.control_config.get("lockdown", False) and not is_admin:
            return GuardResult(False, "🔒 绘图功能锁定中，仅管理员可用")

        if is_group and group_id is not None and self.whitelist_group_ids:
            if str(group_id) not in self.whitelist_group_ids:
                can_bypass = bool(self.control_config.get("admin_bypass_whitelist", True))
                if not (is_admin and can_bypass):
                    return GuardResult(False, f"🚫 当前群不在白名单中: {group_id}")

        return GuardResult(True)

    def check_cooldown(self, user_id: str, is_admin: bool) -> GuardResult:
        if is_admin and bool(self.control_config.get("admin_bypass_cooldown", True)):
            return GuardResult(True)

        cooldown_seconds = int(self.control_config.get("cooldown_seconds", 0) or 0)
        if cooldown_seconds <= 0:
            return GuardResult(True)

        now = float(self.time_func())
        last_time = self._cooldowns.get(str(user_id))
        if last_time is not None:
            elapsed = now - last_time
            if elapsed < cooldown_seconds:
                remain = int(cooldown_seconds - elapsed)
                return GuardResult(False, f"⏱️ 请等待 {remain} 秒后再试", remain_seconds=remain)

        self._cooldowns[str(user_id)] = now
        return GuardResult(True)

    def check_sensitive(self, prompt: str, policy: str, is_admin: bool) -> GuardResult:
        if is_admin and bool(self.control_config.get("admin_bypass_sensitive_words", True)):
            return GuardResult(True)

        policy = str(policy or "none").lower()
        if policy == "none":
            return GuardResult(True)

        words: list[str] = []
        words.extend(self.lexicon.get("legacy_lite", []))
        if policy == "full":
            words.extend(self.lexicon.get("full", []))

        matched = [word for word in words if word and word in prompt]
        if matched:
            return GuardResult(False, "🚫 检测到敏感内容，无法生成图片", matched_words=matched)

        return GuardResult(True)
