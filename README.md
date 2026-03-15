# maibot_comfyui_plugin

一个面向 **MaiBot** 的 **ComfyUI** 插件，提供：

- 命令绘图
- LLM 主动调用绘图 Action
- 多工作流切换
- 群白名单 / 冷却 / 敏感词控制

> 当前仓库就是插件根目录，放进 `MaiBot/plugins/maibot_comfyui_plugin/` 即可被加载。

---

## 功能概览

### 已实现

- `/画图 <提示词>`：使用当前工作流生成图片
- `/画图no <提示词>`：兼容保留命令入口，当前版本行为与 `/画图` 基本一致
- `/comfy帮助`：显示帮助
- `/comfy_ls`：列出工作流
- `/comfy_use <序号> [正面ID] [负面ID] [输出ID]`：切换工作流
- `/comfy_save <文件名> <JSON内容>`：保存新的工作流 JSON
- `/comfy_add list|clear|<节点ID> <步数>`：管理步数覆盖
- `/违禁级别 <none|lite|full>`：设置当前群聊违禁级别
- `ComfyUIDrawAction`：让麦麦在普通对话中可自主决定是否绘图

### 当前版本说明

- 插件仅对接 **ComfyUI**
- 工作流文件位于 `workflow/`
- 步数覆盖 sidecar 文件格式为 `*.steps.json`
- 敏感词文件位于 `sensitive_words.json`

### 当前未覆盖 / 预留项

以下配置项已经出现在 `config.toml` schema 中，但当前实现里主要属于**预留字段**，不要把它们当成完全可用的高级特性：

- `llm.enable_action`
- `llm.direct_send_by_default`
- `llm.action_cooldown_share_command`
- `server.save_output`
- `workflow.auto_scan_workflows`

---

## 安装方式

### 方式 1：直接克隆到 MaiBot 的 `plugins/` 目录

在 MaiBot 根目录执行：

```bash
git clone https://github.com/XXXxx7258/maibot_comfyui_plugin.git plugins/maibot_comfyui_plugin
```

要求：

- 目录名必须是 `maibot_comfyui_plugin`
- 插件根目录内应直接包含 `_manifest.json`、`plugin.py` 等文件

### 方式 2：手动复制

把整个仓库目录复制到：

```text
MaiBot/plugins/maibot_comfyui_plugin/
```

---

## 前置条件

使用前请确保：

1. **MaiBot 已正常运行**
2. **ComfyUI 已启动并开启 API**
3. ComfyUI 工作流可以通过 API 正常执行
4. 你知道工作流中这些节点 ID：
   - 正向提示词节点
   - 负向提示词节点（可选）
   - 输出节点（可选）

---

## 目录结构

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
│  └─ workflow_api.json
└─ tests/
```

---

## 首次使用

### 1. 启动 MaiBot

插件会在首次加载时根据 `config_schema` 自动生成：

```text
plugins/maibot_comfyui_plugin/config.toml
```

### 2. 编辑 `config.toml`

默认生成的关键配置如下：

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

## 配置说明

### `[server]`

```toml
[server]
address = "127.0.0.1:8188"
timeout_seconds = 120
```

- `address`：ComfyUI 地址
- `timeout_seconds`：生成轮询超时

示例：

```toml
[server]
address = "192.168.2.1:8188"
timeout_seconds = 180
```

### `[workflow]`

```toml
[workflow]
default_json_file = "workflow_api.json"
input_node_id = "6"
neg_node_id = "7"
output_node_id = ""
```

- `default_json_file`：默认工作流
- `input_node_id`：正向提示词节点 ID
- `neg_node_id`：负向提示词节点 ID
- `output_node_id`：输出节点 ID；留空时会回退到第一个有图片输出的节点

### `[control]`

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

- `admin_ids`：管理员账号列表
- `whitelist_group_ids`：允许启用插件的群
- `group_policies`：按群覆盖策略
- `default_group_policy`：群聊默认敏感词级别
- `default_private_policy`：私聊默认敏感词级别
- `lockdown`：全局锁定，仅管理员可用

支持的敏感词策略：

- `none`
- `lite`
- `full`

---

## 工作流说明

### 默认工作流目录

```text
workflow/
```

### 步数覆盖文件

比如当前工作流是：

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

## 敏感词文件说明

文件：

```text
sensitive_words.json
```

默认结构：

```json
{
  "legacy_lite": [],
  "full": []
}
```

说明：

- `lite` 策略会检查 `legacy_lite`
- `full` 策略会检查 `legacy_lite + full`

---

## 命令说明

### 1. 基础绘图

```text
/画图 可爱的猫娘
/画图no 赛博朋克城市夜景
```

> 当前版本中 `/画图no` 主要用于兼容原插件命令风格，发送链路与 `/画图` 基本一致。

### 2. 查看帮助

```text
/comfy帮助
```

### 3. 列出工作流

```text
/comfy_ls
```

### 4. 切换工作流

```text
/comfy_use 1
/comfy_use 2 6 7 9
```

含义：

- 第一个参数：工作流序号
- 后面三个参数可选：
  - 正面提示词节点 ID
  - 负面提示词节点 ID
  - 输出节点 ID

### 5. 保存工作流

```text
/comfy_save my_workflow {"1":{"inputs":{...}}}
```

### 6. 管理步数覆盖

```text
/comfy_add list
/comfy_add clear
/comfy_add 3839 20
/comfy_add 3839 20 4521 40
/comfy_add 3839 off
```

### 7. 设置违禁级别

```text
/违禁级别 none
/违禁级别 lite
/违禁级别 full
```

---

## LLM 主动调用说明

插件提供了 `ComfyUIDrawAction`。

设计目标是让麦麦在普通对话中，当“生成图片比纯文本更合适”时，主动选择该 Action。

当前 Action 参数：

```python
{
  "prompt": "用于生成图片的提示词",
  "direct_send": "是否直接发送图片，true/false",
  "reason_brief": "为什么此时适合调用绘图"
}
```

---

## 测试与开发

在 MaiBot 根目录执行：

### 运行插件测试

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s plugins\maibot_comfyui_plugin\tests -p "test_*.py"
```

### 运行 Ruff

```powershell
.\.venv\Scripts\python.exe -m ruff check plugins\maibot_comfyui_plugin
```

---

## 当前限制

当前版本暂未覆盖：

- 多图连续生成
- 文本占位标记解析式出图
- 自动扫描后动态刷新 UI schema
- 更细粒度的 per-chat 工作流路由
- 真正区分 `/画图` 与 `/画图no` 的发送策略

---

## 发布建议

如果你要把它作为公开仓库继续维护，建议后续补充：

- `LICENSE`
- 更完整的 `README` 截图示例
- `CHANGELOG`
- GitHub Actions 基础 CI
- 一次真实 ComfyUI 联机 smoke test 文档

