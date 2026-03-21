# Argus

**README 语言：** [English](README.md) · [日本語](README.ja.md) · 中文

> *以希腊神话中百眼巨人 Argus Panoptes 命名——他从不入睡，时刻注视着一切。*

一个 Python 工具，每 5 秒静默记录当前活跃的应用和窗口。在后台运行，随时调出实时仪表盘或终端报告，清楚了解你的时间都去了哪里。

---

## 技术栈

| 功能 | 工具 |
|---|---|
| 活跃窗口检测 | `pywin32`（Windows）· `osascript`（macOS）· `xdotool`（Linux）|
| 空闲检测 | `GetLastInputInfo` via ctypes（Windows）· `ioreg`（macOS）· `xprintidle`（Linux）|
| 进程信息 | `psutil` |
| 存储 | SQLite（标准库 `sqlite3`）|
| CLI | `Typer` |
| 终端报告 | `Rich` |
| 交互式仪表盘 | `Textual` |
| 开机自启 | 注册表键（Windows）· LaunchAgent plist（macOS）· XDG autostart（Linux）|

---

## 开发环境安装

```bash
pip install -r requirements.txt
```

**仅 Linux** — 额外安装两个系统包：
```bash
sudo apt install xdotool xprintidle   # Ubuntu / Debian
sudo dnf install xdotool xprintidle   # Fedora
```

---

## 构建独立可执行文件

将 Argus 打包为单个文件，终端用户无需安装 Python 或 pip。

```bash
# 安装构建工具（仅需一次）
pip install -r requirements-dev.txt

# 构建
python build.py
```

输出到 `dist/` 目录：

| 平台 | 文件 |
|---|---|
| Windows | `dist/argus.exe` |
| Linux | `dist/argus` |
| macOS | `dist/argus` |

可执行文件完全自包含——Python、Textual、Rich 及所有依赖均已打包。**终端用户无需安装任何额外内容。**

> **Linux 注意：** `xdotool` 和 `xprintidle` 是系统包，无法打包进可执行文件。分发 Linux 版本时请提示用户：
> ```bash
> sudo apt install xdotool xprintidle
> ```

---

## 使用方法（源码运行）

```bash
# 交互式仪表盘（推荐——同时在后台运行追踪器）
python src/main.py tui

# 仅在前台运行追踪器（Ctrl+C 停止）
python src/main.py start

# 今日活动报告
python src/main.py report

# 指定日期的报告
python src/main.py report --date 2026-03-15

# 本周报告
python src/main.py week

# 查看当前正在做什么
python src/main.py status

# 注册开机自启
python src/main.py install

# 取消开机自启
python src/main.py uninstall
```

### 使用构建后的可执行文件

```bash
argus tui
argus report
argus install
# 等等——与源码命令相同，无需 "python src/main.py" 前缀
```

---

## TUI 仪表盘

运行 `argus tui` 打开由 [Textual](https://textual.textualize.io/) 驱动的全终端实时仪表盘，同时在后台运行追踪器，无需单独执行 `start`。

**显示内容**

- **状态面板** — 当前应用、分类、窗口标题、空闲时间、快照总数
- **今日** — 前 10 个应用及分类占比（含进度条）
- **本周** — 逐日汇总、每周分类分布、每周热门应用

每 5 秒自动刷新。

**键盘快捷键**

| 按键 | 功能 |
|---|---|
| `?` | 帮助界面 |
| `R` | 立即刷新所有数据 |
| `T` | 切换颜色主题 |
| `L` | 切换界面语言 |
| `A` | 切换开机自启（启用 / 禁用）|
| `O` | 在文件管理器中打开数据目录 |
| `Q` | 退出 |

**工具栏按钮**

| 按钮 | 功能 |
|---|---|
| `开机自启  开/关` | 切换登录自启 |
| `ZH  中文` | 切换语言 |
| `打开数据目录` | 打开数据文件夹 |

---

## 语言支持

TUI 支持 6 种语言，按 `L` 循环切换：

| 代码 | 语言 |
|---|---|
| `en` | English |
| `ja` | 日本語 |
| `zh` | 中文 |
| `fr` | Français |
| `de` | Deutsch |
| `es` | Español |

语言选择保存至 `~/.argus/settings.json`，下次启动时自动恢复。

---

## 主题

在 TUI 中按 `T` 循环切换 12 个内置 Textual 主题（无需额外安装）：

`textual-dark` · `textual-light` · `nord` · `gruvbox` · `catppuccin-mocha` · `catppuccin-latte` · `dracula` · `tokyo-night` · `monokai` · `solarized-dark` · `solarized-light` · `flexoki`

主题选择同样自动保存并恢复。

---

## 数据

所有数据存储于 `~/.argus/argus.db`（SQLite），每个 5 秒快照对应一行：

| 字段 | 类型 | 说明 |
|---|---|---|
| `ts` | REAL | Unix 时间戳 |
| `app_name` | TEXT | 进程名（如 `chrome`、`code`）|
| `window_title` | TEXT | 当时的窗口标题 |
| `exe_path` | TEXT | 可执行文件完整路径 |
| `idle` | INTEGER | 超过空闲阈值时为 1 |

空闲快照在报告和 TUI 中默认排除。

用户偏好（语言、主题）单独存储于 `~/.argus/settings.json`。

---

## 分类

应用自动归入以下分类：

`浏览器` · `IDE / 编辑器` · `终端` · `通讯` · `设计` · `游戏` · `生产力` · `媒体` · `文件管理器` · `系统` · `其他`

如需修改映射，编辑 `src/argus/config.py` 中的 `CATEGORIES` 字典。

---

## 配置调整

编辑 `src/argus/config.py` 顶部的两个常量：

```python
POLL_INTERVAL  = 5    # 快照间隔（秒）
IDLE_THRESHOLD = 60   # 标记为空闲的无操作时长（秒）
```

---

## 项目结构

```
src/
├── main.py               # Typer CLI 入口，委托给 argus/
└── argus/
    ├── __init__.py       # 包版本
    ├── config.py         # 常量、分类映射、设置持久化
    ├── i18n.py           # 界面字符串（6 种语言）
    ├── tracker.py        # 活跃窗口 + 空闲检测（Win / macOS / Linux）
    ├── storage.py        # SQLite 读写
    ├── daemon.py         # 前台轮询循环（start 命令）
    ├── report.py         # Rich 日报 / 周报 / 状态报告
    ├── tui.py            # Textual 实时仪表盘
    └── autostart.py      # 开机自启（Win / macOS / Linux）
build.py                  # PyInstaller 构建脚本 → dist/argus[.exe]
requirements.txt          # 运行时依赖
requirements-dev.txt      # 运行时 + 构建工具（pyinstaller）
dist/                     # 编译产物（已加入 .gitignore）
```
