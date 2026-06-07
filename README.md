# 湖南大白熊的影刀RPA接口管理平台 与 Skill技能
- V0.0.2 
- Flet应用软件：win端，支持影刀社区版！！！暴露API供远程调用一键启动影刀机器人！！！
- Skill技能，提供通过自然语言让Agent智能体自动操控影刀机器人功能。
- 均适用于影刀社区免费版！！！

---

## 🆕 全新 Skill 技能 — 用自然语言操控影刀机器人！20260607上架！

现在你可以在 你的各类OpenClaw龙虾智能体 中通过自然语言对话来管理和控制影刀 RPA 机器人，无需手动操作界面！

**核心功能：**

- 🛠️ 一键自动配置 — `setup` 自动检测影刀路径
- 🔵 列出 / 🔍 搜索机器人 — 快速定位目标
- 🚀 启动机器人 — 自然语言说"跑一下XXX"即可
- 🛑 停止机器人 — 安全优雅停止（严禁杀进程）
- 📊 状态检测 / 📝 日志分析 — 精准了解运行情况

> 💡 社区免费版适用，无需企业管理控制台 API，零额外依赖，开箱即用！

👉 **完整介绍、安装配置和使用方式，可以直接查看Skill本身的Readme文档：[./skills/README.md](./skills/README.md)**

![image](./skill_image/skill_1.png)
![image](./skill_image/skill_2.png)
![image](./skill_image/skill_3.png)

---

---

接下来是之前的Flet应用软件的介绍：

## 功能特性

基于 Python Flet 框架开发的 Windows 桌面应用，用于管理影刀RPA机器人并提供 REST API 接口服务。

- 🤖 **机器人列表展示** - 自动扫描并显示本地所有影刀机器人
- ▶️ **一键启动** - 点击按钮即可启动对应机器人
- 🔌 **REST API 接口** - 提供 HTTP 接口，支持远程调用启动机器人
- 📚 **接口文档** - 内置 API 接口文档，一键查看所有接口
- 🔍 **模糊搜索** - 支持按机器人名称模糊查询
- ⚙️ **灵活配置** - 支持配置用户路径和影刀程序路径
- 💾 **配置持久化** - 配置自动保存到用户目录，永久保留
- 🎨 **现代化UI** - 基于 Flet 框架的 Material Design 界面
- 👤 **作者信息** - 左上角展示作者信息

## 界面展示

![img](./demo1.png)
![img](./demo2.png)

# 安装运行：

## (一) 【推荐】直接安装发行版exe软件，运行桌面端即可！

前往Release页面下载最新版本的exe安装包，解压后直接运行exe即可！

## (二) 使用源码运行

### 1. 【极其强烈建议】创建venv虚拟环境！

```bash
# 创建虚拟环境（或在你所用的IDE里，找到相关创建虚拟环境的按钮一键创建！）
# 注意：一定要在项目根目录里创建！！！
cd yingdao_robot_run_api_manage
python -m venv .venv

# 激活虚拟环境
.venv\Scripts\activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 运行应用（默认启动是Win桌面端应用形式）

```bash
# 推荐直接python启动：
python main.py

# 或者也可以采用flet官方的启动方式：（需要下载依赖，确保你的网络能连通。。。额。。。）
# flet run main.py
```

## 使用说明

### 首次使用

1. 首次打开应用会自动弹出配置对话框
2. 配置两个路径：
   - **影刀用户ID文件夹路径**：如 `C:\Users\Administrator\AppData\Local\ShadowBot\users\64*************74`
     - 支持直接选择用户ID目录，也可以选择其下的 `apps` 文件夹
   - **ShadowBot.exe 路径**：如 `D:\Program Files (x86)\ShadowBot\ShadowBot.exe`
3. 点击"保存配置"完成设置
4. 系统会自动加载该用户下的所有机器人

### 日常使用

- **启动机器人**：点击机器人卡片右侧的"▶ 启动"按钮
- **刷新列表**：点击右上角的"刷新"按钮
- **修改配置**：点击右上角的"⚙️ 配置"按钮
- **查看接口文档**：点击"接口文档"按钮查看所有 API 接口

### API 接口

应用启动后会自动开启 API 服务（端口 16666），支持以下接口：

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/status` | GET | 获取 API 服务状态 |
| `/api/config` | GET | 获取当前配置 |
| `/api/robots` | GET | 获取所有机器人列表 |
| `/api/robot/{uuid}` | GET | 获取指定机器人信息 |
| `/api/robots/search?name={keyword}` | GET | 根据名称模糊查询机器人 |
| `/api/robot/{uuid}/launch` | POST | 启动指定机器人 |

**调用示例：**

```python
import requests

# 获取机器人列表
response = requests.get('http://localhost:16666/api/robots')
robots = response.json()

# 根据名称模糊查询
response = requests.get('http://localhost:16666/api/robots/search?name=测试')
robots = response.json()

# 启动机器人
uuid = robots['data'][0]['uuid']
response = requests.post(f'http://localhost:16666/api/robot/{uuid}/launch')
result = response.json()
```

#### 或直接在cmd里发起调用来测试：

```bash
# 注：切记是cmd，不是powershell！！！
## 这里假设你已经确认了你所需运行的机器人的uuid是：a123456-b123-c123-d123-e12345678901
curl -X POST http://localhost:16666/api/robot/a123456-b123-c123-d123-e12345678901/launch
```

## 数据目录

配置文件保存在用户 AppData 目录，打包后也不会丢失：

- **Windows**: `%APPDATA%\yingdao_robot_manager\config.json`
  - 通常路径：`C:\Users\用户名\AppData\Roaming\yingdao_robot_manager\config.json`

## 技术栈

- **Python 3.8+**
- **Flet >= 0.25.0** - 跨平台UI框架（基于Flutter）
- **Flask >= 2.3.0** - REST API 框架
- **requests >= 2.31.0** - HTTP 请求库

# 打包 exe
#### 强烈建议使用venv虚拟环境打包！否则可能打出来的exe会很大！甚至超过1GB！！！

这里强烈推荐使用 PyInstaller 打包（需激活虚拟环境）：

```bash
# 务必先激活虚拟环境： .\.venv\Scripts\activate

# 打包命令
pyinstaller --windowed --onefile --name "湖南大白熊的影刀RPA接口管理平台" --add-data "bear.ico;." --add-data "sponsor.png;." main.py --icon bear.ico --add-data "./.venv/Lib/site-packages/flet*;./" --noconfirm --clean

# 你也可以使用Flet官方的打包命令：
# flet build Windows
# 但是这个命令，需要下载安装Flutter一大堆依赖。。。很慢的。。。而且需要科学上网。。。国内用户很不推荐。。。上手难度较大，可能需要你有一定的基础，所以完全不如直接使用傻瓜式的PyInstaller打包。。。
```

打包后的可执行文件在 `dist/` 目录下。

## 注意事项

1. 确保影刀客户端已正确安装
2. 配置的用户路径必须包含 `apps` 文件夹
3. 需要 Windows 系统才能启动机器人
4. API 服务端口为 16666，请确保端口未被占用

## 作者

**湖南大白熊** - 影刀RPA高级开发者^_^

- GitHub主页: [https://github.com/HnBigVolibear](https://github.com/HnBigVolibear)
- 本项目仓库开源地址：[https://github.com/HnBigVolibear/yingdao_robot_run_api_manage](https://github.com/HnBigVolibear/yingdao_robot_run_api_manage)

### Buy me a Coffee:

![img](./sponsor.png)

## ⚖️ 免责声明

- 本项目仅供学习交流使用，请勿用于任何商业或非法用途！
- 如果本项目涉及任何侵权情况，请联系作者（[GitHub](https://github.com/HnBigVolibear)）立即下架处理。

## License

MIT License
