# maibot_comfyui_plugin

MaiBot 的 ComfyUI 绘图插件。

支持：

- 命令绘图
- 普通对话中由麦麦主动调用绘图 Action
- 多工作流切换
- 群白名单 / 冷却 / 敏感词控制

---

## 安装

把仓库放到 MaiBot 的插件目录：

```text
MaiBot/plugins/maibot_comfyui_plugin/
```

也可以直接在 MaiBot 根目录执行：

```bash
git clone https://github.com/XXXxx7258/maibot_comfyui_plugin.git plugins/maibot_comfyui_plugin
```

---

## 使用前准备

请先确认：

1. MaiBot 已正常运行
2. ComfyUI 已启动并开启 API
3. 你要使用的工作流支持 API 调用
4. 你知道工作流里的这些节点 ID：
   - 正向提示词节点
   - 负向提示词节点（可选）
   - 输出节点（可选）

---

## 首次使用

首次加载插件后，会自动生成：

```text
plugins/maibot_comfyui_plugin/config.toml
```

你需要检查并修改其中的 ComfyUI 地址和工作流节点配置。

---

## 配置示例

```toml
[plugin]
enabled = true
config_version = "1.0.0"

[server]
address = "127.0.0.1:8188"
timeout_seconds = 120
save_output = true

[workflow]
default_json_file = "workflow_api.json"
input_node_id = "6"
neg_node_id = "7"
output_node_id = ""
auto_scan_workflows = true

[llm]
enable_action = true
direct_send_by_default = false
action_cooldown_share_command = true

[control]
cooldown_seconds = 35
admin_ids = []
whitelist_group_ids = []
group_policies = {}
default_group_policy = "lite"
default_private_policy = "lite"
lockdown = false
admin_bypass_whitelist = true
admin_bypass_cooldown = true
admin_bypass_sensitive_words = true
```

---

## 主要配置项

### ComfyUI 服务

```toml
[server]
address = "127.0.0.1:8188"
timeout_seconds = 120
```

- `address`：ComfyUI 服务地址
- `timeout_seconds`：请求超时时间

示例：

```toml
[server]
address = "192.168.2.1:8188"
timeout_seconds = 180
```

### 工作流

```toml
[workflow]
default_json_file = "workflow_api.json"
input_node_id = "6"
neg_node_id = "7"
output_node_id = ""
```

- `default_json_file`：默认使用的工作流文件
- `input_node_id`：正向提示词节点 ID
- `neg_node_id`：负向提示词节点 ID
- `output_node_id`：输出节点 ID；留空时自动查找第一个有图片输出的节点

### 权限与风控

```toml
[control]
cooldown_seconds = 35
admin_ids = ["123456"]
whitelist_group_ids = ["10001", "10002"]
group_policies = { "10001" = "full" }
default_group_policy = "lite"
default_private_policy = "lite"
lockdown = false
admin_bypass_whitelist = true
admin_bypass_cooldown = true
admin_bypass_sensitive_words = true
```

- `admin_ids`：管理员 ID 列表
- `whitelist_group_ids`：允许使用插件的群
- `group_policies`：按群单独设置违禁级别
- `default_group_policy`：群聊默认违禁级别
- `default_private_policy`：私聊默认违禁级别
- `lockdown`：全局锁定，仅管理员可用

支持的违禁级别：

- `none`
- `lite`
- `full`

---

## 工作流文件

工作流目录：

```text
workflow/
```

例如：

```text
workflow/workflow_api.json
workflow/portrait.json
```

### 步数覆盖文件

如果当前工作流是：

```text
workflow/portrait.json
```

那么对应的步数覆盖文件是：

```text
workflow/portrait.steps.json
```

内容示例：

```json
{
  "3839": {
    "steps": 20
  },
  "4521": {
    "steps": 40
  }
}
```

---

## 敏感词文件

文件：

```text
sensitive_words.json
```

默认格式：

```json
{
  "legacy_lite": [],
  "full": []
}
```

规则：

- `lite`：检查 `legacy_lite`
- `full`：检查 `legacy_lite + full`

---

## 命令

### 绘图

```text
/画图 可爱的猫娘
/画图no 赛博朋克城市夜景
```

### 帮助

```text
/comfy帮助
```

### 列出工作流

```text
/comfy_ls
```

### 切换工作流

```text
/comfy_use 1
/comfy_use 2 6 7 9
```

参数说明：

- 第一个参数：工作流序号
- 后面三个参数可选：
  - 正向提示词节点 ID
  - 负向提示词节点 ID
  - 输出节点 ID

### 保存工作流

```text
/comfy_save my_workflow {"1":{"inputs":{...}}}
```

### 步数覆盖

```text
/comfy_add list
/comfy_add clear
/comfy_add 3839 20
/comfy_add 3839 20 4521 40
/comfy_add 3839 off
```

### 设置当前群违禁级别

```text
/违禁级别 none
/违禁级别 lite
/违禁级别 full
```

---

## 普通对话中的主动绘图

插件提供了 `ComfyUIDrawAction`。

开启后，麦麦在普通对话中可以根据上下文主动决定是否调用绘图。

---

## 仓库结构

```text
maibot_comfyui_plugin/
├─ _manifest.json
├─ plugin.py
├─ actions.py
├─ commands.py
├─ comfyui_client.py
├─ generation_guard.py
├─ generation_service.py
├─ prompt_builder.py
├─ runtime.py
├─ workflow_manager.py
├─ sensitive_words.json
├─ workflow/
└─ _locales/
```
