from __future__ import annotations

import json
from typing import Optional

from src.plugin_system import BaseCommand

from .runtime import build_runtime


class _BaseComfyCommand(BaseCommand):
    def __init__(self, message, plugin_config: Optional[dict] = None, service=None, runtime=None):
        super().__init__(message, plugin_config)
        self.runtime = runtime or build_runtime(self.plugin_config)
        self._service = service or self.runtime.generation_service

    def _get_user_id(self) -> str:
        message_info = getattr(self.message, "message_info", None)
        user_info = getattr(message_info, "user_info", None)
        user_id = getattr(user_info, "user_id", None)
        if user_id is None:
            user_id = getattr(self.message, "user_id", "0")
        return str(user_id)

    def _get_group_id(self) -> str | None:
        message_info = getattr(self.message, "message_info", None)
        group_info = getattr(message_info, "group_info", None)
        group_id = getattr(group_info, "group_id", None)
        if group_id is None:
            return getattr(self.message, "group_id", None)
        return str(group_id)

    def _is_group(self) -> bool:
        return self._get_group_id() is not None

    def _is_admin(self) -> bool:
        return self.runtime.guard.is_admin(self._get_user_id())


class DrawCommand(_BaseComfyCommand):
    command_name = "comfy_draw"
    command_description = "使用当前工作流生成图片"
    command_pattern = r"^/画图\s+(?P<prompt>.+)$"

    async def execute(self):
        prompt = self.matched_groups.get("prompt", "").strip()
        result = await self._service.generate(
            user_id=self._get_user_id(),
            group_id=self._get_group_id(),
            is_group=self._is_group(),
            prompt=prompt,
        )
        if not result.success:
            await self.send_text(result.message or "❌ 绘图失败")
            return False, result.message, 2

        await self.send_image(result.image_base64)
        return True, f"已生成图片: {result.normalized_prompt}", 2


class DrawDirectCommand(DrawCommand):
    command_name = "comfy_draw_direct"
    command_description = "直接发送 ComfyUI 生成图片"
    command_pattern = r"^/画图no\s+(?P<prompt>.+)$"


class ComfyHelpCommand(_BaseComfyCommand):
    command_name = "comfy_help"
    command_description = "显示 ComfyUI 插件帮助"
    command_pattern = r"^/comfy帮助$"

    async def execute(self):
        lines = [
            "🎨 ComfyUI 插件帮助",
            "━━━━━━━━━━━━━━━━━━",
            "  /画图 <提示词>     生成图片",
            "  /画图no <提示词>   直接发送图片",
            "  /comfy帮助         显示帮助",
            "  /comfy_ls          列出工作流",
            "  /comfy_use <序号>  切换工作流",
            "  /comfy_save <文件名> <JSON内容>",
            "  /comfy_add list|clear|<节点ID> <步数>",
            "  /违禁级别 <none|lite|full>",
        ]
        await self.send_text("\n".join(lines))
        return True, "显示帮助成功", 2


class ComfyListCommand(_BaseComfyCommand):
    command_name = "comfy_list"
    command_description = "列出所有工作流"
    command_pattern = r"^/comfy_ls$"

    async def execute(self):
        if not self._is_admin():
            await self.send_text("🚫 权限不足，仅管理员可查看工作流列表")
            return False, "权限不足", 2

        workflows = self.runtime.workflow_manager.list_workflows()
        if not workflows:
            await self.send_text("📂 目录中没有工作流文件")
            return False, "没有工作流", 2

        current = self.plugin_config.get("workflow", {}).get("default_json_file", "")
        lines = ["📂 可用工作流列表", "━━━━━━━━━━━━━━━━━━"]
        for index, workflow in enumerate(workflows, start=1):
            prefix = "✅" if workflow == current else "  "
            suffix = " (当前)" if workflow == current else ""
            lines.append(f"{prefix} {index}. {workflow}{suffix}")
        await self.send_text("\n".join(lines))
        return True, "列出工作流成功", 2


class ComfyUseCommand(_BaseComfyCommand):
    command_name = "comfy_use"
    command_description = "切换当前工作流"
    command_pattern = r"^/comfy_use(?:\s+.+)?$"

    async def execute(self):
        if not self._is_admin():
            await self.send_text("🚫 权限不足，仅管理员可切换工作流")
            return False, "权限不足", 2

        args = str(getattr(self.message, "raw_message", "")).split()
        if len(args) < 2:
            await self.send_text("❌ 参数不足\n用法：/comfy_use <序号> [正面ID] [负面ID] [输出ID]")
            return False, "参数不足", 2

        workflows = self.runtime.workflow_manager.list_workflows()
        try:
            index = int(args[1])
        except ValueError:
            await self.send_text("❌ 请输入有效的数字序号")
            return False, "序号无效", 2

        if index < 1 or index > len(workflows):
            await self.send_text(f"❌ 序号错误，请输入 1 到 {len(workflows)} 之间的数字")
            return False, "序号越界", 2

        workflow_name = workflows[index - 1]
        input_node_id = args[2] if len(args) > 2 else None
        neg_node_id = args[3] if len(args) > 3 else None
        output_node_id = args[4] if len(args) > 4 else None
        self.runtime.set_workflow(
            workflow_name,
            input_node_id=input_node_id,
            neg_node_id=neg_node_id,
            output_node_id=output_node_id,
        )
        await self.send_text(f"✅ 已切换至 {workflow_name}")
        return True, f"切换到 {workflow_name}", 2


class ComfySaveCommand(_BaseComfyCommand):
    command_name = "comfy_save"
    command_description = "保存新的工作流 JSON"
    command_pattern = r"^/comfy_save(?:\s+.+)?$"

    async def execute(self):
        if not self._is_admin():
            await self.send_text("🚫 权限不足，仅管理员可导入工作流")
            return False, "权限不足", 2

        full_text = str(getattr(self.message, "raw_message", ""))
        content = full_text.split(maxsplit=2)
        if len(content) < 3:
            await self.send_text("❌ 参数不足\n用法：/comfy_save <文件名> <JSON内容>")
            return False, "参数不足", 2

        filename = content[1]
        if not filename.endswith(".json"):
            filename += ".json"
        try:
            parsed = json.loads(content[2])
        except json.JSONDecodeError:
            await self.send_text("❌ JSON 内容无效")
            return False, "json 无效", 2

        self.runtime.workflow_manager.save_workflow(filename, parsed)
        await self.send_text(f"✅ 已保存工作流：{filename}")
        return True, f"保存工作流 {filename}", 2


class ComfyAddCommand(_BaseComfyCommand):
    command_name = "comfy_add"
    command_description = "管理当前工作流的步数覆盖"
    command_pattern = r"^/comfy_add(?:\s+.+)?$"

    async def execute(self):
        if not self._is_admin():
            await self.send_text("🚫 权限不足，仅管理员可设置步数覆盖")
            return False, "权限不足", 2

        current = self.plugin_config.get("workflow", {}).get("default_json_file", "workflow_api.json")
        args = str(getattr(self.message, "raw_message", "")).split()
        if len(args) < 2:
            await self.send_text("📝 用法：/comfy_add list|clear|<节点ID> <步数>")
            return False, "参数不足", 2

        sub_command = args[1].lower()
        if sub_command == "list":
            overrides = self.runtime.workflow_manager.read_step_overrides(current)
            if not overrides:
                await self.send_text(f"ℹ️ {current} 暂无步数覆盖")
                return True, "无覆盖", 2
            lines = ["📊 当前工作流步数覆盖", f"📍 工作流: {current}"]
            for node_id, data in overrides.items():
                steps = data["steps"] if isinstance(data, dict) and "steps" in data else data
                lines.append(f"  • 节点 {node_id}: {steps} 步")
            await self.send_text("\n".join(lines))
            return True, "列出步数覆盖成功", 2

        if sub_command == "clear":
            self.runtime.workflow_manager.write_step_overrides(current, {})
            await self.send_text(f"🗑️ 已清空 {current} 的所有步数覆盖")
            return True, "已清空步数覆盖", 2

        params = args[1:]
        if len(params) % 2 != 0:
            await self.send_text("❌ 参数格式错误，需要成对输入：<节点ID> <步数>")
            return False, "参数格式错误", 2

        existing = self.runtime.workflow_manager.read_step_overrides(current)
        for index in range(0, len(params), 2):
            node_id = params[index]
            value = params[index + 1].lower()
            if value in {"off", "0", "del", "delete", "rm", "remove"}:
                existing.pop(node_id, None)
                continue

            try:
                steps = int(value)
            except ValueError:
                await self.send_text(f"❌ 无效的步数值：{value}")
                return False, "步数无效", 2
            existing[node_id] = {"steps": steps}

        self.runtime.workflow_manager.write_step_overrides(current, existing)
        await self.send_text(f"✅ 已更新 {current} 的步数覆盖")
        return True, "更新步数覆盖成功", 2


class ComfyPolicyCommand(_BaseComfyCommand):
    command_name = "comfy_policy"
    command_description = "设置当前群聊的违禁级别"
    command_pattern = r"^/违禁级别(?:\s+.+)?$"

    async def execute(self):
        if not self._is_admin():
            await self.send_text("🚫 权限不足，仅管理员可设置违禁级别")
            return False, "权限不足", 2

        group_id = self._get_group_id()
        if not group_id:
            await self.send_text("⚠️ 当前不是群聊，无法设置群违禁级别")
            return False, "不是群聊", 2

        args = str(getattr(self.message, "raw_message", "")).split()
        if len(args) < 2 or args[1] not in {"none", "lite", "full"}:
            await self.send_text("❌ 用法：/违禁级别 <none|lite|full>")
            return False, "参数不足", 2

        level = args[1]
        self.runtime.set_group_policy(group_id, level)
        await self.send_text(f"✅ 已将本群违禁级别设置为：{level}")
        return True, f"设置违禁级别为 {level}", 2
