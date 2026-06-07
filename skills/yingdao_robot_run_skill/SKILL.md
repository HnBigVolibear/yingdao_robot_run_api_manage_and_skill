---
name: "yingdao-robot-run-skill"
description: "Manage and launch 影刀Yingdao(ShadowBot) RPA robots. Invoke when user wants to setup/list/search/info/run/stop robots, check running status, show configuration, analyze logs to identify running robot, or pass parameters when launching a robot."
version: "1.0.4"
---

# 影刀 Yingdao Robot Run Skill

This skill enables the agent to manage and control Yingdao (影刀/ShadowBot) RPA robots on the local machine through natural language commands. This skill is designed for the **free community edition** of Yingdao RPA — no enterprise management console API required, completely free to use.

本技能通过自然语言指令管理本地影刀（ShadowBot）RPA 机器人，适用于**免费社区版**，无需企业管理控制台 API。

## Capabilities / 功能列表

1. **Auto setup / 自动配置** — Auto-detect ShadowBot user path and set environment variable / 自动检测影刀用户路径并设置环境变量
2. **List all robots / 列出所有机器人** — Query robots under the current Yingdao account, default shows the 20 most recently modified; supports specifying count / 查询当前影刀账号下的机器人，默认显示最近修改的20个，支持指定数量
3. **Search robots by name or UUID / 按名称或 UUID 搜索机器人** — Fuzzy search robots by name keyword or UUID / 按名称关键词或 UUID 模糊搜索
4. **Get robot details / 查询机器人详情** — Get detailed info of a specific robot by UUID / 通过 UUID 获取机器人详细信息
5. **Launch a robot by UUID / 通过 UUID 启动机器人** — Start a specific robot using the `shadowbot:Run` protocol, supports passing parameters via `&key=value` / 使用 `shadowbot:Run` 协议启动指定机器人，支持通过 `&key=value` 传入参数
6. **Stop running robot / 停止运行中的机器人** — Stop the currently running robot by sending Ctrl+Alt+Q hotkey / 发送 Ctrl+Alt+Q 快捷键停止当前运行的机器人
7. **Check robot running status / 检查运行状态** — Detect whether ShadowBot is currently running a robot / 检测影刀当前是否正在运行机器人
8. **Analyze running robot via log / 通过日志分析运行中的机器人** — Parse ShadowBot log to identify which robot is currently running, including name, UUID, start time, Engine PID, Engine ID, and trigger method / 解析影刀日志定位当前运行的机器人，包括名称、UUID、启动时间、Engine PID、Engine ID 和触发方式
9. **Show configuration / 查看配置** — Display current environment variable configuration / 显示当前环境变量配置信息

## Prerequisites / 前置条件

### 1. Python Dependencies / Python 依赖

No extra dependencies required. The script uses only Python standard library + Win32 API (built-in on Windows).

无需额外依赖，仅使用 Python 标准库 + Win32 API（Windows 内置）。

### 2. Environment Variables / 环境变量

This skill needs one environment variable configured. **Recommended: use the** **`setup`** **command to auto-detect and configure.**

本技能需要配置一个环境变量。**推荐：使用** **`setup`** **命令自动检测并配置。**

#### Method 1: Auto Setup (Recommended) / 方式一：自动配置（推荐）

```bash
python robot_skill.py setup
```

This automatically scans the ShadowBot installation directory, detects the user path, and sets the `YINGDAO_USER_PATH` environment variable permanently (via `setx`). New terminal sessions will pick it up automatically. For the current session, the `setup` command outputs a PowerShell command that the Agent must execute to make it effective immediately.

自动扫描影刀安装目录，检测用户路径，并通过 `setx` 永久设置 `YINGDAO_USER_PATH` 环境变量（新终端自动生效）。对于当前会话，`setup` 命令会输出一条 PowerShell 命令，Agent 必须执行该命令才能使当前会话立即生效。

#### Method 2: Manual Setup / 方式二：手动配置

If auto-detection fails, you can manually set the environment variable:

如果自动检测失败，可以手动设置环境变量：

```powershell
setx YINGDAO_USER_PATH "C:\Users\你的用户名\AppData\Local\ShadowBot\users\你的用户ID"
```

#### How to Find the Path / 如何找到路径

- **YINGDAO\_USER\_PATH**: Open ShadowBot → Right-click any robot → Open folder location → Navigate up to `users\数字ID` directory
- **查找方法**：打开影刀 → 右键任意机器人 → 打开文件夹位置 → 向上导航到 `users\数字ID` 目录

## How to Execute / 执行方式

All operations are performed by running the Python script `robot_skill.py` (located in the same directory as this SKILL.md) via the `RunCommand` tool. All command paths below are relative to this skill's directory.

所有操作通过 `RunCommand` 工具运行 `robot_skill.py` 脚本执行。以下命令路径均相对于本技能目录。

**IMPORTANT / 重要**：使用 `RunCommand` 执行时，必须将 `cwd` 设置为本 SKILL.md 所在目录，例如：

```
cwd: <skill_dir>
command: python robot_skill.py list
```

其中 `<skill_dir>` 为本 SKILL.md 文件所在的目录路径。

### 0. Auto Setup / 自动配置

```bash
python robot_skill.py setup
```

Automatically detects the ShadowBot user path by scanning `%LOCALAPPDATA%\ShadowBot\users\` for directories containing an `apps` subfolder. Once detected, it:

1. Runs `setx YINGDAO_USER_PATH <path>` to persist the variable (permanent, user-level, new terminals will pick it up)
2. Outputs a PowerShell command for the Agent to execute in the current terminal session, making it effective immediately without restarting

**IMPORTANT / 重要**：`setx` only affects new terminal sessions. After running `setup`, the Agent MUST also execute the printed PowerShell command (`$env:YINGDAO_USER_PATH = "..."`) in the current terminal to make the current session effective immediately.

自动检测影刀用户路径，扫描 `%LOCALAPPDATA%\ShadowBot\users\` 下含 `apps` 子目录的文件夹。检测到后：

1. 执行 `setx YINGDAO_USER_PATH <路径>` 永久设置环境变量（用户级别，新终端自动生效）
2. 输出 PowerShell 命令供 Agent 在当前终端执行，使当前会话立即生效

**重要**：`setx` 只对新终端生效。运行 `setup` 后，Agent 必须在当前终端执行输出的 PowerShell 命令（`$env:YINGDAO_USER_PATH = "..."`），才能让当前会话立即生效。

### 1. List All Robots / 列出所有机器人

```bash
python robot_skill.py list [数量]
```

Lists robots under the current account. By default shows the 20 most recently modified robots. Pass a number to specify how many to show (e.g., `list 50` for 50, `list 0` for all).

返回当前账号下的机器人列表，默认显示最近修改的20个。可传入数字指定显示数量（如 `list 50` 显示50个，`list 0` 显示全部）。

### 2. Search Robots by Name or UUID / 按名称或 UUID 搜索机器人

```bash
python robot_skill.py search "关键词"
```

Replace `关键词` with the search term. Returns matching robots with their names, UUIDs, and versions.

将 `关键词` 替换为搜索词。返回匹配机器人的名称、UUID 和版本。

### 3. Get Robot Details by UUID / 通过 UUID 查询机器人详情

```bash
python robot_skill.py info "robot-uuid-here"
```

Returns detailed info of a specific robot: name, UUID, version, author, description, modification time, and local path.

返回机器人详细信息：名称、UUID、版本、作者、描述、修改时间和本地路径。

### 4. Launch a Robot by UUID / 通过 UUID 启动机器人

```bash
# 不带参数启动
python robot_skill.py run "robot-uuid-here"

# 带参数启动（key=value 格式，多个参数用空格分隔）
python robot_skill.py run "robot-uuid-here" key1=value1 key2=value2
```

This executes `start shadowbot:Run?robot-uuid={uuid}&key1=value1&key2=value2` to launch the robot. After launching, it automatically waits 5 seconds and then runs a status check (with `skip_activation=True` to avoid re-activating the ShadowBot window and interfering with the just-launched robot) to verify whether the robot is actually running.

**Parameter Passing / 传参说明**：The `shadowbot:Run` protocol supports passing parameters via URL query string. Parameters are appended as `&key=value` pairs after `robot-uuid`. For example, `run "uuid" name=张三 age=25` generates URL: `shadowbot:Run?robot-uuid=uuid&name=张三&age=25`.

**💡 Suggestion / 建议**：When the user explicitly wants to pass parameters to a robot, the Agent should first run the `info` command to query the robot's details (description, etc.) to see if the expected parameter format is documented, and then execute `run` with the correct parameters. This helps avoid passing incorrect parameter names or formats.

通过 `shadowbot:Run` 协议启动机器人，启动后自动等待 5 秒并执行状态检测（跳过窗口激活以避免干扰刚启动的机器人），验证机器人是否成功运行。

**传参说明**：`shadowbot:Run` 协议支持通过 URL query 传参，参数以 `&key=value` 格式追加在 `robot-uuid` 之后。例如 `run "uuid" name=张三 age=25` 会生成 URL：`shadowbot:Run?robot-uuid=uuid&name=张三&age=25`。

**💡 建议**：当用户明确表示要传参启动机器人时，Agent 应先执行 `info` 命令查询该机器人的详情（描述等信息），看看能否获取到具体的入参格式，然后再用正确的参数执行 `run` 命令，避免传入错误的参数名或格式。

### 5. Stop Running Robot / 停止运行中的机器人

```bash
python robot_skill.py stop
```

Sends the Ctrl+Alt+Q hotkey to stop the currently running ShadowBot robot. Uses Win32 `keybd_event` API (no extra dependencies needed), which can trigger ShadowBot's global keyboard hook. After sending the hotkey, it automatically waits 5 seconds and then runs a status check to verify whether the robot has stopped. If the window detection is unreliable (e.g., notification popup interfering), it automatically performs a log-based secondary verification to confirm the stop result.

**⚠️ CRITICAL / 严禁**：NEVER directly kill/terminate ShadowBot processes (e.g., `taskkill`, `Process.Kill()`, or closing PID). Directly killing processes will corrupt ShadowBot's internal state, cause data loss, and may leave the robot in an unrecoverable state. Always use the `stop` command (Ctrl+Alt+Q hotkey) to gracefully stop the robot.

发送 Ctrl+Alt+Q 快捷键停止当前运行的影刀机器人（使用 Win32 `keybd_event` API，能触发影刀的全局键盘钩子，无需额外依赖）。发送后自动等待 5 秒并检测状态，验证机器人是否已停止。若窗口检测不可靠（如通知弹窗干扰），会自动通过日志二次验证确认停止结果。

**⚠️ 严禁**：绝对不要直接杀掉/终止 ShadowBot 进程（如 `taskkill`、`Process.Kill()` 或关闭 PID）。直接杀进程会导致影刀内部状态损坏、数据丢失，并可能使机器人进入不可恢复的状态。必须始终使用 `stop` 命令（Ctrl+Alt+Q 快捷键）来优雅地停止机器人。

### 6. Check Robot Running Status / 检查运行状态

```bash
python robot_skill.py status
```

Detects whether ShadowBot is currently running a robot by:

1. Checking if ShadowBot processes exist — if not, ShadowBot is not launched
2. Executing `start shadowbot:` to attempt activating the main window
3. If the main window appears (size > 300x200), ShadowBot is idle
4. If the main window does not appear, a robot is currently running
5. Also checks window title for designer/edit mode

**Tip / 提示**：`status` only tells you whether a robot is running or not. To find out **which** robot is running, use the `log` command for detailed analysis.

检测影刀机器人运行状态的逻辑：

1. 检查 ShadowBot 进程是否存在 — 不存在则影刀未启动
2. 执行 `start shadowbot:` 尝试激活主窗口
3. 主窗口出现（尺寸 > 300x200）→ 影刀空闲
4. 主窗口未出现 → 正在运行机器人
5. 同时检查窗口标题判断是否在设计器中编辑

**提示**：`status` 只能判断是否有机器人在运行。要了解**哪个**机器人在运行，请使用 `log` 命令进行详细分析。

### 7. Analyze Running Robot via Log / 通过日志分析运行中的机器人

```bash
python robot_skill.py log
```

Parses the ShadowBot main log file (`%LOCALAPPDATA%\ShadowBot\log\YYYYMMDD.log`) to identify which robot is currently running. It:

1. Locates today's log file dynamically (no hardcoded paths)
2. Parses `[TaskManager]` entries to extract robot name, UUID, and trigger type
3. Matches `xbot engine running` entries to associate PIDs
4. Uses `GetExitCodeProcess` (Win32 API) to verify whether each engine process is still alive (STILL\_ACTIVE=259)
5. Reports the most recently started active robot: name, UUID, start time, Engine PID, Engine ID, trigger method (Manual/Schedule/API/Console)
6. If no robot is running, shows the most recent stopped record

**When to use / 使用场景**：

- User asks "哪个机器人在运行", "当前运行的机器人是什么", "查看正在运行的机器人"
- After `status` reports a robot is running, use `log` to identify which one
- To troubleshoot or verify robot execution details

解析影刀主日志文件（`%LOCALAPPDATA%\ShadowBot\log\YYYYMMDD.log`）定位当前运行的机器人：

1. 动态定位今天的日志文件（无硬编码路径）
2. 解析 `[TaskManager]` 记录提取机器人名称、UUID 和触发方式
3. 匹配 `xbot engine running` 记录关联 PID
4. 通过 `GetExitCodeProcess`（Win32 API）验证每个 engine 进程是否仍存活（STILL\_ACTIVE=259）
5. 报告最近启动的活跃机器人：名称、UUID、启动时间、Engine PID、Engine ID、触发方式（手动/定时/API/控制台）
6. 若无机器人运行，显示最近一次已停止的运行记录

### 8. Show Configuration / 查看配置

```bash
python robot_skill.py config
```

Displays current environment variable values, whether paths exist, and robot count. If configuration is incomplete, prints setup guide.

显示当前环境变量值、路径是否存在及机器人数量。配置不完整时打印配置引导。

## Usage Guidelines / 使用指引

- When user asks to "配置影刀", "初始化", "设置环境变量", "首次使用", use the `setup` command to auto-detect and configure. **After setup completes, the Agent MUST also execute the printed PowerShell command (`$env:YINGDAO_USER_PATH = "..."`) in the current terminal via RunCommand to make the current session effective immediately.**
- When user asks to "列出机器人", "查看所有机器人", "有哪些机器人", use the `list` command (default 20). If user specifies a count like "列出50个机器人" or "显示全部机器人", pass the number as argument (e.g., `list 50` or `list 0`).
- When user asks to "搜索机器人", "查找XXX机器人", "有没有叫XXX的机器人", use the `search` command with the keyword.
- When user asks to "机器人详情", "XXX机器人信息", "查看XXX机器人", use the `info` command with the UUID.
- When user asks to "启动机器人", "运行XXX机器人", "跑一下XXX", first search to find the UUID, then use the `run` command.
- When user asks to "带参启动机器人", "运行XXX机器人并传入参数", "跑一下XXX传入YYY", first use `info` to check robot details for parameter format hints, then use the `run` command with `key=value` params (e.g., `run "uuid" name=张三 age=25`).
- 用户要求传参启动机器人时，Agent 应先执行 `info` 命令查询该机器人详情，看看描述等信息中是否标注了入参格式，再使用正确的参数执行 `run` 命令。
- When user asks to "停止机器人", "停掉机器人", "中止运行", use the `stop` command.
- When user asks to "机器人状态", "是否在运行", "运行情况", use the `status` command.
- When user asks to "哪个机器人在运行", "当前运行的机器人", "查看正在运行的机器人", "正在跑什么机器人", use the `log` command to analyze ShadowBot logs and identify the running robot. The `log` command can also be used as a supplement after `status` reports a robot is running, to get detailed info about which robot it is.
- When user asks to "查看配置", "当前配置", "配置信息", use the `config` command.
- Always confirm with the user before launching a robot, showing the robot name and UUID.
- If the environment variables are not set, the script will print a configuration guide. Recommend using the `setup` command for auto-detection. If auto-detection fails, help the user manually set up `YINGDAO_USER_PATH`. / 如果环境变量未设置，脚本会打印配置引导。推荐使用 `setup` 命令自动检测配置。自动检测失败时，帮助用户手动设置 `YINGDAO_USER_PATH`。

## Important Notes / 重要说明

- This skill only works on Windows with ShadowBot installed. / 本技能仅在安装了影刀的 Windows 系统上可用。
- **⚠️ NEVER directly kill/terminate ShadowBot processes (taskkill, Process.Kill(), closing PID). This corrupts ShadowBot's internal state, causes data loss, and may leave the robot unrecoverable. Always use the** **`stop`** **command. / ⚠️ 严禁直接杀掉 ShadowBot 进程，这会导致状态损坏和数据丢失，必须使用** **`stop`** **命令。**
- The `shadowbot:Run` protocol requires ShadowBot to be installed and the URL scheme registered. / `shadowbot:Run` 协议需要影刀已安装并注册 URL Scheme。
- Robot launch includes an automatic status check 5 seconds after launching to verify the robot started successfully. Similarly, stop includes a 5-second delayed status check to verify the robot has stopped, with automatic log-based secondary verification if window detection is unreliable. / 启动机器人后自动等待 5 秒检测状态验证是否成功运行；停止机器人后同样等待 5 秒验证是否已停止，窗口检测不可靠时自动通过日志二次验证。
- The running status detection uses `start shadowbot:` activation + window size analysis, which has been tested and verified to work reliably. / 运行状态检测使用 `start shadowbot:` 激活 + 窗口尺寸分析，已测试验证可靠。
- The `log` command parses ShadowBot's main log file at `%LOCALAPPDATA%\ShadowBot\log\YYYYMMDD.log` (path is dynamically resolved, no hardcoded paths). It identifies the most recently started active robot by matching log entries with `GetExitCodeProcess` process liveness checks, reporting name, UUID, start time, Engine PID, Engine ID, and trigger method. / `log` 命令解析影刀主日志文件 `%LOCALAPPDATA%\ShadowBot\log\YYYYMMDD.log`（路径动态解析，无硬编码路径），通过匹配日志记录并使用 `GetExitCodeProcess` 进程存活检测，定位最近启动的活跃机器人，报告名称、UUID、启动时间、Engine PID、Engine ID 和触发方式。
- The `run` command supports passing parameters via `&key=value` in the URL. Parameter values containing `&`, `=`, `#`, `%`, or spaces are automatically URL-encoded (e.g., `&` → `%26`). Chinese characters are kept as-is (verified to work with ShadowBot). When the user explicitly wants to pass parameters, the Agent should first use the `info` command to check the robot's description for expected parameter format. / `run` 命令支持通过 URL `&key=value` 传参。参数值中的 `&`、`=`、`#`、`%`、空格会自动做 URL 编码（如 `&` → `%26`），中文字符保持原样（已验证影刀支持）。当用户明确要传参时，Agent 应先执行 `info` 查看机器人描述中的入参格式。
