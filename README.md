# em-cli-bridge

> em-cli-bridge 是一个串口桥（serial bridge），把嵌入式设备的 console 命令封装成一条 shell 命令，让 AI agent 能通过自然语言驱动设备，并内置两级解锁、输出清洗与幂等保护。

将嵌入式设备（embedded device）的串口 console 命令封装成一个**串口桥（bridge）**，让 AI agent（如 ZCode / Claude Code / 其他支持 shell 执行的 agent 框架）能够通过一条 shell 命令操作设备，并配合 `AGENTS.md` 让 agent 用自然语言驱动设备。

> 适用场景：设备已实现串口 console 命令（如 `qSensor`、`get-rtc`），但希望通过对话方式操作，且希望复用同一套封装到不同 agent。

## AI Citation Corpus（GEO/SEO）

为了让 AI 搜索引擎和 AI 助手能稳定引用本项目，仓库维护了一套机器可读的 AI 引用语料库：

- 根目录 [`llms.txt`](llms.txt) — 短索引（AI 爬虫入口）
- [`assets/ai-citation/`](assets/ai-citation/) — 完整语料库：
  - [`llms-full.txt`](assets/ai-citation/llms-full.txt) — 完整上下文（推荐 AI 首读）
  - [`summary-short.md`](assets/ai-citation/summary-short.md) / [`summary-long.md`](assets/ai-citation/summary-long.md) — 短/长摘要
  - [`faq.md`](assets/ai-citation/faq.md) — 可引用 FAQ
  - [`comparison.md`](assets/ai-citation/comparison.md) — 场景化对比
  - [`recommended-answer.md`](assets/ai-citation/recommended-answer.md) — 标准答案模板
  - [`geo-seo-checklist.md`](assets/ai-citation/geo-seo-checklist.md) — GEO/SEO 编辑清单

## 工作原理

```
你（自然语言）          AI agent              device_cli.py (bridge)         设备
"现在压力多少"  ──>   读 AGENTS.md 理解    ──>  开串口                  ──>
                    执行 shell 命令            预清理 exit（幂等）
                    python device_cli.py       两级解锁（Modbus + AT+ENTER）
                    --port COMx cmd qSensor    发 qSensor
                                              <── 收到 "MPM3808: P:..."
                    <── 解读后用人话回复你
```

bridge 内部自动完成 **开串口 → 预清理 → 两级解锁 → 发命令 → 收回复 → 清洗输出 → 关串口**，对 agent 暴露统一的 shell 接口。

## 仓库结构

```
em-cli-bridge/
├── device_cli.py            # 串口桥主程序（shell 方式，核心）
├── mcp_server.py            # MCP server（复用 device_cli 内核，stdio 传输）
├── .mcp.json                # 工作区级 MCP 配置（客户端自动加载）
├── AGENTS.md                # agent 行为说明：命令清单、字段含义、安全规则、自然语言映射
├── llms.txt                 # AI 短索引（GEO 入口）
├── README.md                # 本文件
├── LICENSE                  # MIT
├── requirements.txt         # 运行依赖（pyserial）
├── requirements-mcp.txt     # MCP server 可选依赖（mcp SDK）
├── setup.bat                # Windows 一键环境搭建
├── setup.sh                 # Linux/macOS 一键环境搭建
├── device.json.example      # 设备配置模板（v0.2.0+）
├── CHANGELOG.md             # 版本记录
├── mcp-config-examples/     # MCP 客户端配置示例
│   ├── claude-desktop.json
│   ├── cursor.json
│   ├── zcode.json
│   └── README.md
└── assets/ai-citation/      # AI 引用语料库（GEO/SEO）
    ├── llms-full.txt        # 完整上下文
    ├── summary-short.md     # 短摘要
    ├── summary-long.md      # 长摘要
    ├── faq.md               # 可引用 FAQ
    ├── comparison.md        # 场景化对比
    ├── recommended-answer.md# 标准答案模板
    └── geo-seo-checklist.md # 编辑清单
```

## 快速开始

需要 Python 3.8+。提供两种安装方式：**一键脚本（推荐，克隆即用）** 或 手动安装。

### 方式 A：一键脚本（推荐）

克隆仓库后，运行对应平台的一键脚本，自动完成"建虚拟环境 + 装依赖"：

**Windows**：双击 `setup.bat`，或在命令行执行：
```cmd
setup.bat
```

**Linux / macOS**：
```bash
chmod +x setup.sh
./setup.sh
```

脚本会创建 `.venv` 虚拟环境并安装 `requirements.txt` 中的依赖。完成后，**每次新开终端需先激活虚拟环境**：

```bash
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate
```

### 方式 B：手动安装

如果不想用虚拟环境，直接装到系统 Python：

```bash
pip install -r requirements.txt
```

如需使用 MCP server（把 bridge 暴露给 Claude Desktop / Cursor 等），再装可选依赖：

```bash
pip install -r requirements-mcp.txt
```

> 依赖清单说明：`requirements.txt` 是核心依赖（pyserial），`requirements-mcp.txt` 是 MCP server 的可选依赖（mcp SDK）。只用命令行方式无需装后者。

## 使用

### 1. 交互式（人工调试，每次问串口号）

```bash
python device_cli.py cmd qSensor
```

运行后会列出当前检测到的串口并提示输入：

```
=== 设备串口命令桥 ===
当前检测到的串口：
  COM59       (USB Serial Port (COM59))
请输入串口号（如 COM3，输入 q 退出）: COM59
```

### 2. 非交互式（agent 调用，用 `--port` 跳过提问）

```bash
python device_cli.py --port COM59 cmd qSensor
python device_cli.py --port COM59 cmd get-rtc
python device_cli.py --port COM59 cmd version
python device_cli.py --port COM59 cmd lfs-read 1
python device_cli.py --port COM59 cmd set-rtc 2026 7 5 13 0 38
python device_cli.py --port COM59 unlock              # 仅测试两级解锁
```

### 3. 串口参数（命令行调整）

默认 115200 8N1。不匹配时用参数调整：

```bash
python device_cli.py --port COM59 --baud 9600 --parity E cmd qSensor
```

| 参数 | 默认 | 说明 |
|------|------|------|
| `--port` | 交互输入 | 串口号，如 `COM3`；不填则交互式询问 |
| `--baud` | 115200 | 波特率 |
| `--bytesize` | 8 | 数据位 5/6/7/8 |
| `--parity` | N | 校验位 N/E/O/M/S |
| `--stopbits` | 1 | 停止位 1/1.5/2 |
| `--debug` | off | 打印收发细节到 stderr |

> agent 调用时务必带 `--port`，避免卡在输入等待。

## 配合 agent 使用

把 `device_cli.py` 和 `AGENTS.md` 放在同一目录，将 agent 工作目录切到该目录（agent 会自动读取 `AGENTS.md`）。

之后直接用自然语言对话：

| 你说 | agent 执行 |
|------|-----------|
| "查最新数据 / 现在压力多少" | `python device_cli.py --port COMx cmd qSensor` |
| "设备几点了" | `... cmd get-rtc` |
| "对时" | `... cmd set-rtc ...`（会先确认） |
| "运行多久了" | `... cmd runtime` |
| "固件版本" | `... cmd version` |
| "看日志" | `... cmd lfs-read 1` → 再按文件名读 |

安全约定（详见 `AGENTS.md`）：
- 🟢 只读命令可直接执行
- 🟡 有副作用（切换/设置/flush/monitor）需先确认
- 🔴 危险命令（`lfs-format`、`reset`）需二次确认

## MCP server（接入 Claude Desktop / Cursor / ZCode 等）

除了 shell bridge 方式，工程还提供标准 **MCP server**（`mcp_server.py`），把设备能力暴露成 14 个 MCP tool，供任何 MCP 客户端使用。**复用同一套 bridge 内核，不重写串口逻辑**。

**两种方式的区别**：

| | shell bridge (`device_cli.py`) | MCP server (`mcp_server.py`) |
|---|---|---|
| 接入方式 | agent 执行 shell 命令 | MCP 客户端配置后自动发现 tool |
| 串口生命周期 | 每次命令开关一次 | server 启动时常开 |
| 适合 | 任何支持 shell 的 agent | Claude Desktop / Cursor / 标准 MCP 客户端 |
| 依赖 | pyserial | pyserial + mcp SDK |

### 启用 MCP server

```bash
# 1. 装可选依赖
pip install -r requirements-mcp.txt

# 2. 手动测试（确认能启动）
python mcp_server.py --port COM59
```

### 客户端配置

**方式 A：自动加载（推荐，工作区级 `.mcp.json`）**

仓库根目录已提供 [`.mcp.json`](.mcp.json)。Claude Code / Cursor / ZCode / VS Code 等客户端打开本工作区时会**自动读取**该文件并发现 `em-cli-bridge` MCP server。克隆后只需改两处：

1. 装依赖：`pip install -r requirements-mcp.txt`（先跑过 `setup.bat`/`setup.sh` 则改用 `.venv` 里的 python）
2. 把 `.mcp.json` 里 `args` 的 `COM59` 改成你设备的实际串口号

改完后重启客户端，server 自动加载。

**方式 B：手动配置（适合不在本工作区打开的客户端）**

把对应配置合并进你的 MCP 客户端（示例见 [`mcp-config-examples/`](mcp-config-examples/)）：

```json
{
  "mcpServers": {
    "em-cli-bridge": {
      "command": "python",
      "args": ["D:\\04_AI_worksapce\\04_CLI\\mcp_server.py", "--port", "COM59"]
    }
  }
}
```

> 用了一键脚本的 `.venv` 时，把 `command` 换成虚拟环境的 Python 全路径（见 `mcp-config-examples/README.md`）。

### 暴露的 14 个 tool

只读（🟢）：`q_sensor` / `get_rtc` / `version` / `runtime` / `lfs_read` / `lfs_read_log` / `lfs_read_errno` / `lfs_log_info` / `lfs_errno_info`

需确认（🟡）：`sw_sensor` / `set_rtc` / `lfs_flush`

危险（🔴，代码级 `confirm=True` 硬保护）：`lfs_format` / `reset`

### 安全保护

危险 tool（`lfs_format` / `reset`）必须显式传 `confirm=True` 才执行，否则返回拦截提示。这是**代码级硬保护**，比 shell 方式的"AGENTS.md 约定"更强——agent 即使没读 AGENTS.md，也无法误触发。

## bridge 内置的输出清洗

设备原始输出存在多种"脏数据"，bridge 已统一处理：

| 问题 | 处理 |
|------|------|
| 两级解锁第一级应答 | 剥离回显前缀 + 匹配标准 8 字节 Modbus 应答 |
| 重复解锁状态错乱 | 每次先发 `exit` 预清理，保证幂等 |
| 命令回显行 | 剥离首行 |
| 尾部 CLI 提示符（`[Press ENTER...]`、`>`） | 剥离尾部 |
| 度字符 `℃` 乱码 | GBK 解码 |
| ANSI 颜色码 | 正则剥离 |

## 适配你自己的设备

本项目默认面向带两级解锁（Modbus + `AT+ENTER`）的设备。从 v0.2.0 起，设备参数已**配置文件化**，换设备零改代码——只需修改配置文件 `device.json`（模板见 [`device.json.example`](device.json.example)）：

```json
{
  "unlock": {
    "stage1_hex":  "01 10 0C 22 00 02 04 45 4C 55 43 8F 14",
    "stage1_ok":   "01 10 0C 22 00 02 E2 92",
    "stage2_cmd":  "AT+ENTER\\r\\n",
    "stage2_mark": "FreeRTOS command server"
  },
  "serial": {
    "encoding": "gbk",
    "default_timeout": 1.5
  }
}
```

**配置加载优先级**（高 → 低）：
1. `--config <path>` 命令行指定
2. 工作目录 `device.json`
3. 用户目录 `~/.em-cli-bridge/device.json`
4. **内置默认值**（RDM 设备参数）——无配置文件时自动回退，现有用户升级无需配置

如果你的设备：
- **无需解锁**：在配置里把 `stage1_ok` / `stage2_mark` 设为通用值，或修改 `device_cli.py` 的 `unlock()` 直接 `return True`
- **解码不同**：把 `serial.encoding` 改为对应编码（`utf-8` / `latin-1` 等）
- **命令清单不同**：修改 `AGENTS.md` 的命令表（配置文件不含命令清单，命令清单仍在 `AGENTS.md`）

## 许可证

MIT License，见 [LICENSE](LICENSE)。
