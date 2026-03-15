from typing import List, Tuple, Type

from src.plugin_system import BasePlugin, ComponentInfo, ConfigField, register_plugin


@register_plugin
class MaiBotComfyUIPlugin(BasePlugin):
    """MaiBot ComfyUI 插件。"""

    plugin_name = "maibot_comfyui_plugin"
    enable_plugin = True
    dependencies: List[str] = []
    python_dependencies: List[str] = []
    config_file_name = "config.toml"
    config_section_descriptions = {
        "plugin": "插件基础配置",
        "server": "ComfyUI 服务配置",
        "workflow": "工作流配置",
        "llm": "LLM 主动绘图配置",
        "control": "权限、冷却与敏感词配置",
    }
    config_schema = {
        "plugin": {
            "enabled": ConfigField(type=bool, default=True, description="是否启用插件"),
            "config_version": ConfigField(type=str, default="1.0.0", description="配置版本"),
        },
        "server": {
            "address": ConfigField(type=str, default="127.0.0.1:8188", description="ComfyUI 服务地址"),
            "timeout_seconds": ConfigField(type=int, default=120, description="请求超时秒数"),
            "save_output": ConfigField(type=bool, default=True, description="是否保留输出文件"),
        },
        "workflow": {
            "default_json_file": ConfigField(type=str, default="workflow_api.json", description="默认工作流文件"),
            "input_node_id": ConfigField(type=str, default="6", description="正向提示词节点 ID"),
            "neg_node_id": ConfigField(type=str, default="7", description="负向提示词节点 ID"),
            "output_node_id": ConfigField(type=str, default="", description="输出节点 ID"),
            "auto_scan_workflows": ConfigField(type=bool, default=True, description="是否自动扫描工作流目录"),
        },
        "llm": {
            "enable_action": ConfigField(type=bool, default=True, description="是否启用 LLM 主动绘图"),
            "direct_send_by_default": ConfigField(type=bool, default=False, description="LLM 默认是否直接发图"),
            "action_cooldown_share_command": ConfigField(
                type=bool,
                default=True,
                description="Action 与命令是否共享冷却",
            ),
        },
        "control": {
            "cooldown_seconds": ConfigField(type=int, default=35, description="冷却时间（秒）"),
            "admin_ids": ConfigField(type=list, default=[], description="管理员 ID 列表"),
            "whitelist_group_ids": ConfigField(type=list, default=[], description="群白名单"),
            "group_policies": ConfigField(type=dict, default={}, description="按群配置的违禁级别"),
            "default_group_policy": ConfigField(type=str, default="lite", description="群默认敏感词策略"),
            "default_private_policy": ConfigField(type=str, default="lite", description="私聊默认敏感词策略"),
            "lockdown": ConfigField(type=bool, default=False, description="是否全局锁定"),
            "admin_bypass_whitelist": ConfigField(type=bool, default=True, description="管理员可绕过群白名单"),
            "admin_bypass_cooldown": ConfigField(type=bool, default=True, description="管理员可绕过冷却"),
            "admin_bypass_sensitive_words": ConfigField(
                type=bool,
                default=True,
                description="管理员可绕过敏感词过滤",
            ),
        },
    }

    def get_plugin_components(self) -> List[Tuple[ComponentInfo, Type]]:
        from .actions import ComfyUIDrawAction
        from .commands import (
            ComfyAddCommand,
            ComfyHelpCommand,
            ComfyListCommand,
            ComfyPolicyCommand,
            ComfySaveCommand,
            ComfyUseCommand,
            DrawCommand,
            DrawDirectCommand,
        )

        return [
            (DrawCommand.get_command_info(), DrawCommand),
            (DrawDirectCommand.get_command_info(), DrawDirectCommand),
            (ComfyHelpCommand.get_command_info(), ComfyHelpCommand),
            (ComfyListCommand.get_command_info(), ComfyListCommand),
            (ComfyUseCommand.get_command_info(), ComfyUseCommand),
            (ComfySaveCommand.get_command_info(), ComfySaveCommand),
            (ComfyAddCommand.get_command_info(), ComfyAddCommand),
            (ComfyPolicyCommand.get_command_info(), ComfyPolicyCommand),
            (ComfyUIDrawAction.get_action_info(), ComfyUIDrawAction),
        ]
