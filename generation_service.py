from __future__ import annotations

from dataclasses import dataclass, field

from .prompt_builder import normalize_prompt


@dataclass
class GenerationResult:
    success: bool
    message: str = ""
    image_base64: str = ""
    normalized_prompt: str = ""
    workflow_name: str = ""
    metadata: dict = field(default_factory=dict)


class GenerationService:
    def __init__(
        self,
        guard,
        workflow_manager,
        comfyui_client,
        workflow_config: dict,
    ) -> None:
        self.guard = guard
        self.workflow_manager = workflow_manager
        self.comfyui_client = comfyui_client
        self.workflow_config = workflow_config or {}

    async def generate(
        self,
        *,
        user_id: str,
        group_id: str | None,
        is_group: bool,
        prompt: str,
        negative_prompt: str = "",
        direct_send: bool = False,
    ) -> GenerationResult:
        normalized_prompt = normalize_prompt(prompt)
        access_result = self.guard.check_access(user_id=user_id, group_id=group_id, is_group=is_group)
        if not access_result.allowed:
            return GenerationResult(False, message=access_result.message, normalized_prompt=normalized_prompt)

        is_admin = self.guard.is_admin(user_id)
        cooldown_result = self.guard.check_cooldown(user_id=user_id, is_admin=is_admin)
        if not cooldown_result.allowed:
            return GenerationResult(False, message=cooldown_result.message, normalized_prompt=normalized_prompt)

        policy = self.guard.resolve_policy(group_id=group_id, is_group=is_group)
        sensitive_result = self.guard.check_sensitive(
            prompt=normalized_prompt,
            policy=policy,
            is_admin=is_admin,
        )
        if not sensitive_result.allowed:
            return GenerationResult(False, message=sensitive_result.message, normalized_prompt=normalized_prompt)

        workflow_name = str(self.workflow_config.get("default_json_file", "workflow_api.json"))
        step_overrides = self.workflow_manager.read_step_overrides(workflow_name)
        payload = await self.comfyui_client.generate_image(
            workflow_name=workflow_name,
            prompt=normalized_prompt,
            negative_prompt=negative_prompt,
            step_overrides=step_overrides,
        )
        return GenerationResult(
            success=True,
            image_base64=payload.get("image_base64", ""),
            normalized_prompt=normalized_prompt,
            workflow_name=payload.get("workflow_name", workflow_name),
            metadata={**payload, "direct_send": direct_send},
        )
