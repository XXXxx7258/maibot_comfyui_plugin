from __future__ import annotations

from src.plugin_system import ActionActivationType, BaseAction

from .runtime import build_runtime


class ComfyUIDrawAction(BaseAction):
    action_name = "comfyui_draw"
    action_description = "在普通对话中，当生成图片比纯文本更合适时主动绘图"
    activation_type = ActionActivationType.ALWAYS
    associated_types = ["image", "text"]
    action_parameters = {
        "prompt": "用于生成图片的提示词",
        "direct_send": "是否直接发送图片，true/false",
        "reason_brief": "为什么此时适合调用绘图",
    }
    action_require = [
        "当用户描述了明显画面内容且生成图片比纯文字更合适时使用",
        "普通问答、信息检索和不需要图像的聊天不要使用",
        "风控失败时不要强行发送图片",
    ]

    def __init__(self, *args, service=None, runtime=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.runtime = runtime or build_runtime(self.plugin_config)
        self._service = service or self.runtime.generation_service

    async def execute(self):
        prompt = str(self.action_data.get("prompt", "")).strip()
        result = await self._service.generate(
            user_id=str(self.user_id),
            group_id=str(self.group_id) if self.group_id else None,
            is_group=bool(self.is_group),
            prompt=prompt,
        )
        if not result.success:
            return False, result.message or "绘图失败"

        await self.send_image(result.image_base64)
        return True, f"已主动生成图片: {result.normalized_prompt}"
