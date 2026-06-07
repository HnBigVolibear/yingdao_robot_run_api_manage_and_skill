"""
影刀机器人管理 Skill 核心脚本
支持：自动配置、列出机器人、搜索机器人、查询机器人详情、启动机器人、停止机器人、查询运行状态、日志分析运行机器人、查看配置
"""

import json
import os
import sys
import subprocess
import tempfile
import time
import threading
import ctypes
import ctypes.wintypes
from datetime import datetime

# 确保 stdout/stderr 使用 UTF-8 编码，避免在 GBK 终端下因 emoji 等字符导致 UnicodeEncodeError
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace') # type: ignore
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace') # type: ignore
    except Exception:
        pass


# ============ 配置读取 ============

# 环境变量：
#   YINGDAO_USER_PATH — 影刀用户目录，如 C:\Users\xxx\AppData\Local\ShadowBot\users\640969793025564674


def load_config():
    """
    从环境变量加载配置
    返回 dict: { user_path }
    """
    user_path = os.environ.get('YINGDAO_USER_PATH', '')
    return {"user_path": user_path}


def check_config():
    """检查配置是否完整，返回 (is_ok, missing_items)"""
    config = load_config()
    missing = []
    if not config.get("user_path") or not os.path.exists(config["user_path"]):
        missing.append("YINGDAO_USER_PATH")
    return len(missing) == 0, missing


def auto_detect_user_path():
    """
    自动检测影刀用户目录
    扫描 C:\\Users\\<用户名>\\AppData\\Local\\ShadowBot\\users\\ 下的数字ID目录
    返回检测到的路径（字符串），未找到返回 None
    """
    local_app_data = os.environ.get('LOCALAPPDATA', '')
    if not local_app_data:
        # 回退构造路径
        userprofile = os.environ.get('USERPROFILE', '')
        if userprofile:
            local_app_data = os.path.join(userprofile, 'AppData', 'Local')
        else:
            return None

    shadowbot_users_dir = os.path.join(local_app_data, 'ShadowBot', 'users')
    if not os.path.exists(shadowbot_users_dir):
        return None

    # 扫描 users 目录下的数字ID子目录（含 apps 子目录的才是有效用户目录）
    candidates = []
    for item in os.listdir(shadowbot_users_dir):
        item_path = os.path.join(shadowbot_users_dir, item)
        if os.path.isdir(item_path):
            apps_path = os.path.join(item_path, 'apps')
            if os.path.exists(apps_path):
                candidates.append(item_path)

    if len(candidates) == 1:
        return candidates[0]
    elif len(candidates) > 1:
        # 多个用户目录，返回第一个（按修改时间排序，最新的优先）
        candidates.sort(key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0, reverse=True)
        return candidates[0]

    return None


def setup_env():
    """
    自动检测影刀用户路径并设置环境变量（用户级别，永久生效）
    同时输出 PowerShell 命令供 Agent 在当前终端会话中执行，使当前会话也立即生效
    """
    print("🔍 正在自动检测影刀用户路径...")
    detected_path = auto_detect_user_path()

    if not detected_path:
        print("❌ 未能自动检测到影刀用户路径")
        print()
        print("可能原因：")
        print("  1. 影刀尚未安装")
        print("  2. 影刀用户目录不在默认位置")
        print()
        print("请手动配置：")
        print('  setx YINGDAO_USER_PATH "C:\\Users\\你的用户名\\AppData\\Local\\ShadowBot\\users\\你的用户ID"')
        print()
        print("如何找到路径：")
        print("  打开影刀 → 右键任意机器人 → 打开所在文件夹 → 向上两级到 users\\数字ID 目录")
        return False

    print(f"✅ 检测到影刀用户路径: {detected_path}")

    # 验证路径下有机器人
    apps_path = os.path.join(detected_path, 'apps')
    if os.path.exists(apps_path):
        robot_count = len([d for d in os.listdir(apps_path)
                          if os.path.isdir(os.path.join(apps_path, d)) and not d.endswith("_temp")])
        print(f"   机器人数量: {robot_count}")

    # 使用 setx 设置用户级别环境变量（永久生效，新终端自动生效）
    try:
        result = subprocess.run(
            ['setx', 'YINGDAO_USER_PATH', detected_path],
            capture_output=True, timeout=10
        )
        if result.returncode == 0:
            print()
            print("✅ 环境变量已永久设置：")
            print(f"   YINGDAO_USER_PATH = {detected_path}")
            print()
            print("   新打开的终端会自动生效。")
        else:
            print(f"⚠️ setx 设置失败（返回码: {result.returncode}）")
            print(f"   错误信息: {result.stderr.decode('gbk', errors='ignore')}")
    except Exception as e:
        print(f"⚠️ setx 执行失败: {str(e)}")

    # 输出 PowerShell 命令供 Agent 在当前终端执行，使当前会话立即生效
    # 注意：Python 的 os.environ 只影响当前 Python 进程，不会影响父 Shell
    # 所以必须由 Agent 在 PowerShell 中执行以下命令
    print()
    print("⚠️ 当前终端会话需要手动刷新环境变量，请在当前终端执行以下命令：")
    print()
    print(f'   $env:YINGDAO_USER_PATH = "{detected_path}"')
    print()
    print("   执行后当前会话即可使用所有命令，无需重启终端。")

    return True


def print_config_guide():
    """打印配置引导信息"""
    print("=" * 60)
    print("⚠️  影刀机器人 Skill 首次使用需要配置环境变量：")
    print("=" * 60)
    print()
    print("方式一（推荐）：自动检测并配置")
    print("  python robot_skill.py setup")
    print()
    print("方式二：手动配置")
    print('  setx YINGDAO_USER_PATH "C:\\Users\\你的用户名\\AppData\\Local\\ShadowBot\\users\\你的用户ID"')
    print()
    print("如何找到路径：")
    print("  打开影刀 → 右键任意机器人 → 打开所在文件夹 → 向上两级到 users\\数字ID 目录")
    print()
    print("配置完成后请重新打开终端（环境变量需要新终端生效）。")
    print("=" * 60)


def get_apps_path(config):
    """获取 apps 目录路径"""
    user_path = config.get("user_path", "")
    if user_path and os.path.exists(user_path):
        apps_path = os.path.join(user_path, "apps")
        if os.path.exists(apps_path):
            return apps_path
    return None


# ============ 机器人扫描 ============

def scan_robots(apps_path):
    """扫描所有机器人，返回列表"""
    robots = []
    if not apps_path or not os.path.exists(apps_path):
        return robots

    for item in os.listdir(apps_path):
        if item.endswith("_temp"):
            continue
        item_path = os.path.join(apps_path, item)
        if os.path.isdir(item_path):
            info = read_robot_info(item, item_path)
            if info:
                robots.append(info)

    robots.sort(key=lambda r: r.get('modified_time', '') or '', reverse=True)
    return robots


def read_robot_info(uuid, robot_dir):
    """读取单个机器人信息"""
    xbot_robot_path = os.path.join(robot_dir, "xbot_robot")
    modified_time = ""
    if os.path.exists(xbot_robot_path):
        try:
            mtime = os.path.getmtime(xbot_robot_path)
            modified_time = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
        except Exception:
            pass

    package_paths = [
        os.path.join(robot_dir, "xbot_robot", "package.json"),
        os.path.join(robot_dir, "package.json"),
        os.path.join(robot_dir, "robot.json"),
        os.path.join(robot_dir, "config.json"),
    ]

    for package_path in package_paths:
        if os.path.exists(package_path):
            try:
                with open(package_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {
                        "uuid": uuid,
                        "name": data.get("name") or uuid,
                        "version": data.get("version") or "未知",
                        "description": data.get("description") or "暂无描述",
                        "author": data.get("author") or "未知",
                        "modified_time": modified_time,
                    }
            except Exception:
                continue

    return {
        "uuid": uuid,
        "name": uuid,
        "version": "未知",
        "description": "无法读取详细信息",
        "author": "未知",
        "modified_time": modified_time,
    }


# ============ 功能实现 ============

def list_robots(limit=20):
    """列出机器人，默认显示最近修改的20个，可通过 limit 参数指定数量"""
    is_ok, missing = check_config()
    if not is_ok:
        print("❌ 配置未完成，无法获取机器人列表")
        print_config_guide()
        return

    config = load_config()
    apps_path = get_apps_path(config)

    robots = scan_robots(apps_path)

    if not robots:
        print("⚠️ 未找到任何机器人")
        print(f"   apps 目录: {apps_path}")
        return

    total = len(robots)
    displayed = robots[:limit] if limit > 0 else robots
    show_count = len(displayed)

    if limit > 0 and total > limit:
        print(f"✅ 共找到 {total} 个机器人，显示最近修改的 {show_count} 个（使用 list <数量> 查看更多）：")
    else:
        print(f"✅ 共找到 {total} 个机器人：")
    print()
    print(f"{'序号':<4} {'机器人名称':<30} {'UUID':<40} {'版本':<8} {'修改时间':<16}")
    print("-" * 100)
    for i, robot in enumerate(displayed, 1):
        name = robot['name'][:28] if len(robot['name']) > 28 else robot['name']
        print(f"{i:<4} {name:<30} {robot['uuid']:<40} {robot['version']:<8} {robot['modified_time']:<16}")


def search_robots(keyword):
    """按名字关键词或 UUID 搜索机器人"""
    is_ok, missing = check_config()
    if not is_ok:
        print("❌ 配置未完成，无法搜索机器人")
        print_config_guide()
        return

    config = load_config()
    apps_path = get_apps_path(config)

    robots = scan_robots(apps_path)
    keyword_lower = keyword.lower()

    matched = [r for r in robots if keyword_lower in r['name'].lower() or keyword_lower in r['uuid'].lower()]

    if not matched:
        print(f"⚠️ 未找到包含关键词 '{keyword}' 的机器人")
        print("   所有机器人名称列表：")
        for r in robots:
            print(f"   - {r['name']}")
        return

    print(f"✅ 找到 {len(matched)} 个匹配 '{keyword}' 的机器人：")
    print()
    print(f"{'序号':<4} {'机器人名称':<30} {'UUID':<40} {'版本':<8}")
    print("-" * 85)
    for i, robot in enumerate(matched, 1):
        name = robot['name'][:28] if len(robot['name']) > 28 else robot['name']
        print(f"{i:<4} {name:<30} {robot['uuid']:<40} {robot['version']:<8}")


def run_robot(robot_uuid):
    """通过 UUID 启动机器人"""
    is_ok, missing = check_config()
    if not is_ok:
        print("❌ 配置未完成，无法启动机器人")
        print_config_guide()
        return

    config = load_config()

    # 验证 UUID 是否存在
    apps_path = get_apps_path(config)
    if apps_path:
        robots = scan_robots(apps_path)
        found = [r for r in robots if r['uuid'] == robot_uuid]
        robot_name = found[0]['name'] if found else robot_uuid
    else:
        robot_name = robot_uuid

    # 使用命令行方式启动：start shadowbot:Run?robot-uuid={uuid}
    command = f'@echo off\nstart shadowbot:Run?robot-uuid={robot_uuid}'

    # 创建临时批处理文件执行（使用 NamedTemporaryFile 替代已弃用的 mktemp）
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bat', delete=False, encoding='utf-8') as f:
            bat_path = f.name
            f.write(command)

        # 执行批处理文件
        subprocess.Popen(
            ['cmd', '/c', bat_path],
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
            close_fds=True
        )

        # 延迟删除临时文件（等待足够时间确保 cmd 已读取文件）
        def cleanup():
            time.sleep(3)
            try:
                os.unlink(bat_path)
            except Exception:
                pass

        threading.Timer(10.0, cleanup).start()

        print(f"✅ 已启动机器人：{robot_name}")
        print(f"   UUID: {robot_uuid}")
        print(f"   命令: start shadowbot:Run?robot-uuid={robot_uuid}")
        print()
        print("⏳ 等待 5 秒后检测运行状态...")
        time.sleep(5)
        print()
        check_status(skip_activation=True)
    except Exception as e:
        print(f"❌ 启动失败: {str(e)}")


def _get_shadowbot_processes():
    """
    查询 ShadowBot 相关进程
    返回 list of dict: [{ name, pid }]
    使用 PowerShell（wmic 在新版 Windows 已弃用）
    """
    processes = []
    try:
        result = subprocess.run(
            ['powershell', '-Command',
             '[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; '
             'Get-Process -Name "*ShadowBot*" -ErrorAction SilentlyContinue | '
             'ForEach-Object { "$($_.ProcessName)|$($_.Id)" }'],
            capture_output=True, timeout=10
        )
        output = result.stdout.decode('utf-8', errors='ignore').strip()
        for line in output.split('\n'):
            line = line.strip()
            if '|' in line:
                parts = line.split('|', 1)
                name = parts[0].strip()
                pid_str = parts[1].strip() if len(parts) > 1 else ""
                if name and pid_str.isdigit():
                    processes.append({"name": name, "pid": int(pid_str)})
    except Exception:
        pass
    return processes


def _get_shell_window_info():
    """
    获取 ShadowBot.Shell 主窗口信息
    返回 dict: { pid, handle, title, is_minimized, is_visible }
    核心逻辑：
      - 有进程 + 无窗口句柄 = 影刀正在运行机器人（主窗口被隐藏/最小化）
      - 有进程 + 窗口可见 = 影刀主界面空闲
      - 无进程 = 影刀未启动
    """
    info = {"pid": None, "handle": 0, "title": "", "is_minimized": False, "is_visible": False}

    # 获取 ShadowBot.Shell 进程的 PID 和 MainWindowHandle
    try:
        result = subprocess.run(
            ['powershell', '-Command',
             '[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; '
             'Get-Process -Name "ShadowBot.Shell" -ErrorAction SilentlyContinue | '
             'ForEach-Object { "$($_.Id)|$($_.MainWindowHandle)" }'],
            capture_output=True, timeout=10
        )
        output = result.stdout.decode('utf-8', errors='ignore').strip()
        for line in output.split('\n'):
            line = line.strip()
            if '|' in line:
                parts = line.split('|', 1)
                pid_str = parts[0].strip()
                handle_str = parts[1].strip() if len(parts) > 1 else "0"
                if pid_str.isdigit():
                    info["pid"] = int(pid_str)
                    info["handle"] = int(handle_str) if handle_str.isdigit() else 0
                    break  # 只取第一个
    except Exception:
        pass

    if not info["pid"]:
        return info

    handle = info["handle"]
    if handle > 0:
        user32 = ctypes.windll.user32
        # 获取窗口标题
        try:
            length = user32.GetWindowTextLengthW(handle)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(handle, buf, length + 1)
                info["title"] = buf.value.strip()
        except Exception:
            pass

        # 检测窗口是否最小化（IsIconic 返回非零表示最小化）
        try:
            info["is_minimized"] = bool(user32.IsIconic(handle))
        except Exception:
            pass

        # 检测窗口是否可见
        try:
            info["is_visible"] = bool(user32.IsWindowVisible(handle))
        except Exception:
            pass

    return info


def check_status(skip_activation=False):
    """
    查询影刀机器人运行状态

    参数:
      skip_activation — 为 True 时跳过 `start shadowbot` 激活步骤
                        （从 run_robot 调用时应传 True，避免干扰刚启动的机器人）

    核心检测逻辑：
      先执行 `start shadowbot` 尝试激活影刀主窗口：
        - 如果影刀空闲（即使最小化），该命令会把主窗口调起到前台
        - 如果影刀正在运行机器人，该命令不会让主窗口出现
      然后检测窗口状态来判断当前是否在运行机器人。

    判断结果：
      1. 无 ShadowBot 进程 → 影刀未启动
      2. 有进程 + start shadowbot 后主窗口出现 → 空闲
      3. 有进程 + start shadowbot 后主窗口仍不出现 → 正在运行机器人
      4. 有进程 + 窗口标题含"设计"/"编辑" → 正在设计器中编辑
    """
    # 1. 检查 ShadowBot 进程是否在运行
    processes = _get_shadowbot_processes()

    if not processes:
        print("❌ ShadowBot 未在运行")
        print("   电脑上没有任何影刀进程，请先启动影刀客户端")
        return

    # 统计进程数
    proc_count = len(processes)
    proc_names = set(p["name"] for p in processes)

    # 2. 执行 `start shadowbot` 尝试激活影刀主窗口
    #    - 空闲时：会把最小化的主窗口调起到前台
    #    - 运行机器人时：主窗口不会出现
    #    - skip_activation=True 时跳过此步骤（从 run_robot 调用时避免干扰）
    if not skip_activation:
        try:
            subprocess.run(
                ['cmd', '/c', 'start', 'shadowbot:'],
                capture_output=True, timeout=5
            )
        except Exception:
            pass

    # 3. 轮询检测窗口状态（最多等待5秒）
    #    空闲时窗口会从最小化变为可见，需要等待窗口响应
    #    关键判断：窗口是否成为前台窗口（GetForegroundWindow）
    window_appeared = False
    win_info = {"pid": None, "handle": 0, "title": "", "is_minimized": False, "is_visible": False}
    user32 = ctypes.windll.user32
    for i in range(5):
        time.sleep(1)
        win_info = _get_shell_window_info()
        handle = win_info["handle"]
        if handle > 0:
            # 获取窗口矩形区域
            rect = ctypes.wintypes.RECT()
            user32.GetWindowRect(handle, ctypes.byref(rect))
            win_width = rect.right - rect.left
            win_height = rect.bottom - rect.top

            if skip_activation:
                # skip_activation 模式：不依赖激活判断，直接通过窗口可见性+尺寸判断
                if win_info["is_visible"] and not win_info["is_minimized"] and win_width > 300 and win_height > 200:
                    window_appeared = True
                    break
            else:
                # 常规模式：检查窗口是否成为前台窗口（最可靠）
                foreground = user32.GetForegroundWindow()
                if foreground == handle and win_width > 300 and win_height > 200:
                    window_appeared = True
                    break
                if win_info["is_visible"] and not win_info["is_minimized"] and win_width > 300 and win_height > 200:
                    window_appeared = True
                    break

    # 4. 综合判断状态
    is_minimized = win_info["is_minimized"]
    is_visible = win_info["is_visible"]
    window_title = win_info["title"]
    is_in_designer = "设计" in window_title or "Designer" in window_title or "编辑" in window_title

    # 核心判断：使用轮询中已经判断的 window_appeared 结果
    #   - 空闲：start shadowbot 会调起主窗口到前台
    #   - 运行中：start shadowbot 无法调起主窗口
    is_running_robot = not window_appeared and not is_in_designer

    # 5. 输出状态报告
    # 获取窗口尺寸信息
    win_rect = ctypes.wintypes.RECT()
    if win_info["handle"] > 0:
        user32.GetWindowRect(win_info["handle"], ctypes.byref(win_rect))
        win_w = win_rect.right - win_rect.left
        win_h = win_rect.bottom - win_rect.top
    else:
        win_w = 0
        win_h = 0

    print("📊 影刀机器人运行状态：")
    print()
    print(f"  ShadowBot 进程数: {proc_count}")
    print(f"  进程类型: {', '.join(sorted(proc_names))}")
    print(f"  主窗口句柄: {win_info['handle'] or '无'}")
    print(f"  主窗口标题: {window_title or '(空)'}")
    print(f"  窗口尺寸: {win_w}x{win_h}")
    print(f"  窗口是否可见: {'是' if is_visible else '否'}")
    print(f"  窗口是否最小化: {'是' if is_minimized else '否'}")
    print(f"  start shadowbot 激活: {'成功' if window_appeared else '失败（窗口未出现）'}")

    # 综合判断
    print()
    if is_in_designer:
        print(f"  ⚡ 当前正在设计器中编辑: {window_title}")
    elif is_running_robot:
        print(f"  ⚡ 当前正在运行机器人！")
        print(f"   （start shadowbot 未能调起主窗口，说明影刀正处于运行状态）")
    elif window_appeared:
        print(f"  🔹 ShadowBot 已启动，主界面空闲中")
        print(f"   （start shadowbot 成功调起主窗口，没有机器人在运行）")
    else:
        print(f"  🔹 ShadowBot 已启动")


def _is_small_window(handle):
    """判断窗口是否为小窗口（如右下角通知弹窗），主窗口通常 > 300x200"""
    if not handle:
        return False
    try:
        user32 = ctypes.windll.user32
        rect = ctypes.wintypes.RECT()
        user32.GetWindowRect(handle, ctypes.byref(rect))
        width = rect.right - rect.left
        height = rect.bottom - rect.top
        return width < 300 or height < 200
    except Exception:
        return False


def _verify_stop_via_log():
    """
    通过日志分析二次验证机器人是否已停止
    当窗口检测不可靠时（如停止后主窗口未恢复、右下角通知弹窗干扰），使用此方法确认
    """
    log_dir = _get_shadowbot_log_dir()
    if not log_dir:
        print("   ⚠️ 无法访问日志目录，无法二次验证")
        return

    today_str = datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(log_dir, f"{today_str}.log")

    if not os.path.exists(log_file):
        print("   ⚠️ 未找到今天的日志文件，无法二次验证")
        return

    try:
        with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
    except Exception:
        print("   ⚠️ 读取日志文件失败，无法二次验证")
        return

    # 查找所有 engine PID，检查是否仍有存活的
    running_pids = {}
    stopped_pids = set()
    _active_engine_pids = []

    for line in lines:
        line = line.strip()
        if 'xbot engine running' in line and 'pid:' in line:
            pid_part = line.split('pid:')[-1].split(',')[0].strip()
            if pid_part.isdigit():
                pid = int(pid_part)
                running_pids[pid] = line[:23].strip() if len(line) > 23 else ""
                _active_engine_pids.append(pid)
        if 'xbot engine exited' in line:
            if _active_engine_pids:
                stopped_pids.add(_active_engine_pids.pop())

    # 检查进程存活
    active_count = 0
    for pid in running_pids:
        if pid in stopped_pids:
            continue
        try:
            kernel32 = ctypes.windll.kernel32
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if handle:
                exit_code = ctypes.wintypes.DWORD()
                kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
                kernel32.CloseHandle(handle)
                if exit_code.value == 259:  # STILL_ACTIVE
                    active_count += 1
        except Exception:
            pass

    if active_count == 0:
        print("   ✅ 日志二次验证：所有 engine 进程已退出，机器人已成功停止")
        print("   （影刀主窗口可能需要手动点击恢复，或等待通知弹窗消失后自动恢复）")
    else:
        print(f"   ⚠️ 日志二次验证：仍有 {active_count} 个 engine 进程在运行")
        print("   可能需要再次执行 stop 命令")


def stop_robot():
    """
    停止当前正在运行的影刀机器人
    通过发送 Ctrl+Alt+Q 快捷键实现（影刀默认停止快捷键）
    使用 keybd_event 发送，能触发影刀的全局键盘钩子
    """
    # 先检查是否有影刀进程
    processes = _get_shadowbot_processes()

    if not processes:
        print("❌ ShadowBot 未在运行，无需停止")
        return

    user32 = ctypes.windll.user32
    VK_CONTROL = 0x11
    VK_MENU = 0x12  # Alt
    VK_Q = 0x51
    KEYEVENTF_KEYUP = 0x0002

    # 使用 keybd_event 发送 Ctrl+Alt+Q
    # keybd_event 虽然已标记为弃用，但它能触发全局键盘钩子
    # 影刀通过全局钩子监听 Ctrl+Alt+Q，SendInput 无法触发全局钩子
    print("🔑 正在发送停止快捷键 Ctrl+Alt+Q...")
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    user32.keybd_event(VK_MENU, 0, 0, 0)
    user32.keybd_event(VK_Q, 0, 0, 0)
    time.sleep(0.1)
    user32.keybd_event(VK_Q, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)

    print("✅ 已发送停止快捷键 Ctrl+Alt+Q")
    print("   影刀机器人应该已停止运行")
    print()
    print("⏳ 等待 5 秒后检测运行状态...")
    time.sleep(5)
    print()
    check_status(skip_activation=False)

    # 二次验证：如果窗口检测仍显示运行中，通过日志分析确认是否真正停止
    # 原因：影刀停止机器人后主窗口可能不会立即恢复，右下角通知弹窗会干扰窗口检测
    win_info = _get_shell_window_info()
    if win_info["handle"] == 0 or (win_info["is_visible"] and not win_info["is_minimized"]
                                    and _is_small_window(win_info["handle"])):
        print()
        print("💡 窗口检测仍显示运行中，正在通过日志二次验证...")
        _verify_stop_via_log()


def robot_info(robot_uuid):
    """查询单个机器人的详细信息"""
    is_ok, missing = check_config()
    if not is_ok:
        print("❌ 配置未完成，无法查询机器人信息")
        print_config_guide()
        return

    config = load_config()
    apps_path = get_apps_path(config)

    if not apps_path:
        print("❌ 无法访问机器人目录")
        return

    robots = scan_robots(apps_path)
    found = [r for r in robots if r['uuid'] == robot_uuid]

    if not found:
        print(f"❌ 未找到 UUID 为 {robot_uuid} 的机器人")
        print("   提示: 使用 search 命令搜索机器人")
        return

    robot = found[0]
    print(f"📋 机器人详细信息：")
    print()
    print(f"  名称: {robot['name']}")
    print(f"  UUID: {robot['uuid']}")
    print(f"  版本: {robot['version']}")
    print(f"  作者: {robot['author']}")
    print(f"  描述: {robot['description']}")
    print(f"  修改时间: {robot['modified_time']}")
    print(f"  本地路径: {os.path.join(apps_path, robot['uuid'])}")


def show_config():
    """显示当前环境变量配置信息"""
    config = load_config()
    user_path = config.get("user_path", "")

    print("⚙️ 当前配置信息：")
    print()
    print(f"  YINGDAO_USER_PATH: {user_path or '(未设置)'}")
    if user_path:
        print(f"    路径存在: {'✅ 是' if os.path.exists(user_path) else '❌ 否'}")
        apps_path = os.path.join(user_path, "apps")
        if os.path.exists(apps_path):
            robot_count = len([d for d in os.listdir(apps_path)
                              if os.path.isdir(os.path.join(apps_path, d)) and not d.endswith("_temp")])
            print(f"    机器人数量: {robot_count}")

    is_ok, missing = check_config()
    print()
    if is_ok:
        print("  配置状态: ✅ 完整")
    else:
        print(f"  配置状态: ❌ 缺少 {', '.join(missing)}")
        # 尝试自动检测
        detected = auto_detect_user_path()
        if detected:
            print(f"  💡 已自动检测到影刀用户路径: {detected}")
            print("     执行以下命令可一键配置：")
            print("     python robot_skill.py setup")
        else:
            print_config_guide()


def _is_valid_uuid(value):
    """简单校验 UUID 格式（影刀 UUID 为纯数字或数字+字母的长字符串）"""
    return len(value) >= 10 and value.replace('-', '').replace('_', '').isalnum()


def _get_shadowbot_log_dir():
    """
    动态获取影刀日志目录
    路径: %LOCALAPPDATA%\\ShadowBot\\log
    """
    local_app_data = os.environ.get('LOCALAPPDATA', '')
    if not local_app_data:
        userprofile = os.environ.get('USERPROFILE', '')
        if userprofile:
            local_app_data = os.path.join(userprofile, 'AppData', 'Local')
        else:
            return None
    log_dir = os.path.join(local_app_data, 'ShadowBot', 'log')
    if os.path.exists(log_dir):
        return log_dir
    return None


def check_running_robot_log():
    """
    通过分析影刀主日志，定位当前正在运行的机器人
    解析今天的主日志文件，查找 robot task started 且没有对应 engine exited 的记录
    """
    log_dir = _get_shadowbot_log_dir()
    if not log_dir:
        print("❌ 未找到影刀日志目录")
        print("   请确认影刀已安装在本机")
        return

    # 构造今天的日志文件名（格式：YYYYMMDD.log）
    today_str = datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(log_dir, f"{today_str}.log")

    if not os.path.exists(log_file):
        print(f"❌ 未找到今天的日志文件: {log_file}")
        return

    print(f"📋 正在分析影刀日志: {log_file}")
    print()

    # 读取日志文件
    try:
        with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"❌ 读取日志文件失败: {str(e)}")
        return

    # 解析日志，提取机器人启动和停止记录
    # 关键日志行格式：
    #   [TaskManager]  task continue: True. <name> <uuid> <trigger_type>
    #   xbot engine running, pid:<pid>,engineid:<id>
    #   xbot engine exited, ending
    #   task end <name>,taskName:..., s25, window prepare to close
    running_robots = {}  # {engine_pid: {name, uuid, start_time, trigger, engine_id}}
    stopped_pids = set()
    _pending_task = None
    _active_engine_pids = []  # 按顺序记录正在运行的 engine PID，用于匹配 engine exited

    for line in lines:
        line = line.strip()

        # 匹配 TaskManager 任务启动记录（含机器人名称和UUID）
        # 格式: [TaskManager]  task continue: True. 测试skill远程调度系统 c6073f48-0629-4eaa-9414-69de74c28757 Manual
        if '[TaskManager]' in line and 'task continue' in line:
            parts = line.split('task continue:')
            if len(parts) >= 2:
                info_part = parts[1].strip()
                # 提取时间（日志行开头格式：2026-06-07 10:58:03,xxx）
                time_match = line[:23].strip() if len(line) > 23 else ""
                # 解析: True. <name> <uuid> <trigger>
                tokens = info_part.split()
                if len(tokens) >= 4:
                    robot_uuid = tokens[-2] if _is_valid_uuid(tokens[-2]) else ""
                    trigger = tokens[-1]
                    robot_name = ' '.join(tokens[1:-2]) if robot_uuid else ' '.join(tokens[1:-1])
                    # 暂存，等待 engine running 行来关联 PID
                    _pending_task = {
                        'name': robot_name,
                        'uuid': robot_uuid,
                        'trigger': trigger,
                        'time': time_match,
                    }

        # 匹配 engine running 记录（含 PID）
        # 格式: xbot engine running, pid:28920,engineid:3
        if 'xbot engine running' in line:
            time_match = line[:23].strip() if len(line) > 23 else ""
            pid = None
            engine_id = None
            if 'pid:' in line:
                pid_part = line.split('pid:')[-1].split(',')[0].strip()
                if pid_part.isdigit():
                    pid = int(pid_part)
            if 'engineid:' in line:
                eid_part = line.split('engineid:')[-1].strip()
                if eid_part.isdigit():
                    engine_id = int(eid_part)
            if pid:
                info = {
                    'name': _pending_task.get('name', '未知') if _pending_task else '未知',
                    'uuid': _pending_task.get('uuid', '') if _pending_task else '',
                    'trigger': _pending_task.get('trigger', '') if _pending_task else '',
                    'start_time': time_match,
                    'engine_id': engine_id,
                }
                running_robots[pid] = info
                _active_engine_pids.append(pid)
                _pending_task = None  # 已关联 PID，清空暂存

        # 匹配 engine exited 记录（影刀实际的结束标记）
        # 格式: xbot engine exited, ending
        # exited 行不含 PID，按 LIFO 顺序匹配最近启动的 engine
        if 'xbot engine exited' in line:
            if _active_engine_pids:
                last_pid = _active_engine_pids.pop()
                stopped_pids.add(last_pid)

        # 匹配 task end 记录（包含机器人名称，作为 engine exited 的补充验证）
        # 格式: task end 测试python远程调度系统,taskName:管理后台唤起后执行, s25, window prepare to close
        if 'task end' in line and 'window' in line:
            task_end_match = line.split('task end ')
            if len(task_end_match) >= 2:
                name_part = task_end_match[1].split(',')[0].strip()
                # 将所有匹配名称且尚未标记停止的 PID 标记为已停止
                for pid in list(running_robots.keys()):
                    if pid not in stopped_pids and running_robots[pid].get('name') == name_part:
                        stopped_pids.add(pid)
                        if pid in _active_engine_pids:
                            _active_engine_pids.remove(pid)

    # 检查进程是否仍然存活，找到最近一个正在运行的机器人
    # 优先排除日志中已标记停止的 PID，再用 GetExitCodeProcess 二次确认
    active_robots = {}
    for pid, info in running_robots.items():
        if pid in stopped_pids:
            continue
        try:
            kernel32 = ctypes.windll.kernel32
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if handle:
                exit_code = ctypes.wintypes.DWORD()
                kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
                kernel32.CloseHandle(handle)
                # STILL_ACTIVE = 259
                if exit_code.value == 259:
                    active_robots[pid] = info
        except Exception:
            pass

    if not active_robots:
        print("📭 日志中未发现当前正在运行的机器人")
        print()
        # 显示最近一次运行记录
        if running_robots:
            latest = sorted(running_robots.items(), key=lambda x: x[1].get('start_time', ''), reverse=True)[0]
            pid, info = latest
            print(f"最近一次运行（已停止）：")
            print(f"  {info.get('start_time', '')} {info['name']} (PID:{pid})")
        return

    # 取最近启动的那个正在运行的机器人
    latest_pid, latest_info = sorted(active_robots.items(), key=lambda x: x[1].get('start_time', ''), reverse=True)[0]

    print("✅ 当前正在运行的机器人：")
    print()
    print(f"  🤖 机器人名称: {latest_info['name']}")
    if latest_info.get('uuid'):
        print(f"     UUID: {latest_info['uuid']}")
    print(f"     启动时间: {latest_info.get('start_time', '未知')}")
    print(f"     Engine PID: {latest_pid}")
    if latest_info.get('engine_id'):
        print(f"     Engine ID: {latest_info['engine_id']}")
    if latest_info.get('trigger'):
        trigger_map = {'Manual': '手动触发', 'Schedule': '定时触发', 'API': 'API触发',
                      'Console': '控制台触发', '手动触发': '手动触发'}
        print(f"     触发方式: {trigger_map.get(latest_info['trigger'], latest_info['trigger'])}")
    print()

    # 如果有多个活跃的（罕见情况），简要提示
    if len(active_robots) > 1:
        print(f"💡 另有 {len(active_robots) - 1} 个历史进程仍在运行（可能是异常残留）")
        print()


# ============ 主入口 ============

def main():
    if len(sys.argv) < 2:
        print("用法: python robot_skill.py <命令> [参数]")
        print("命令:")
        print("  setup             - 自动检测并配置环境变量（推荐首次使用）")
        print("  list [数量]        - 列出机器人（默认20个，0=全部）")
        print("  search <关键词>   - 搜索机器人")
        print("  info <UUID>       - 查询机器人详细信息")
        print("  run <UUID>        - 启动机器人")
        print("  stop              - 停止当前运行的机器人")
        print("  status            - 查询影刀运行状态")
        print("  log               - 通过日志分析当前运行的机器人")
        print("  config            - 显示当前配置信息")
        return

    command = sys.argv[1].lower()

    if command == "setup":
        setup_env()
    elif command == "list":
        limit = 20  # 默认显示20个
        if len(sys.argv) >= 3:
            try:
                limit = int(sys.argv[2])
                if limit <= 0:
                    limit = 0  # 0 表示显示全部
            except ValueError:
                print(f"⚠️ 无效的数量参数: {sys.argv[2]}，将使用默认值 20")
        list_robots(limit)
    elif command == "search":
        if len(sys.argv) < 3:
            print("❌ 请提供搜索关键词")
            print("用法: python robot_skill.py search <关键词>")
            return
        keyword = sys.argv[2]
        search_robots(keyword)
    elif command == "info":
        if len(sys.argv) < 3:
            print("❌ 请提供机器人 UUID")
            print("用法: python robot_skill.py info <UUID>")
            return
        robot_uuid = sys.argv[2]
        if not _is_valid_uuid(robot_uuid):
            print(f"❌ 无效的 UUID 格式: {robot_uuid}")
            print("   UUID 应为影刀分配的长字符串（通常为纯数字），而非机器人名称")
            print("   提示: 请先使用 search 命令搜索机器人获取其 UUID")
            return
        robot_info(robot_uuid)
    elif command == "run":
        if len(sys.argv) < 3:
            print("❌ 请提供机器人 UUID")
            print("用法: python robot_skill.py run <UUID>")
            return
        robot_uuid = sys.argv[2]
        if not _is_valid_uuid(robot_uuid):
            print(f"❌ 无效的 UUID 格式: {robot_uuid}")
            print("   UUID 应为影刀分配的长字符串（通常为纯数字），而非机器人名称")
            print("   提示: 请先使用 search 命令搜索机器人获取其 UUID")
            return
        run_robot(robot_uuid)
    elif command == "stop":
        stop_robot()
    elif command == "status":
        check_status()
    elif command == "log":
        check_running_robot_log()
    elif command == "config":
        show_config()
    else:
        print(f"❌ 未知命令: {command}")
        print("支持的命令: setup, list, search, info, run, stop, status, log, config")


if __name__ == "__main__":
    main()