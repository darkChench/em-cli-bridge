# em-cli-bridge

将嵌入式设备（embedded device）的串口 console 命令封装成一个**串口桥（bridge）**，让 AI agent（如 ZCode / Claude Code / 其他支持 shell 执行的 agent 框架）能够通过一条 shell 命令操作设备，并配合 `AGENTS.md` 让 agent 用自然语言驱动设备。

> 适用场景：设备已实现串口 console 命令（如 `qSensor`、`get-rtc`），但希望通过对话方式操作，且希望复用同一套封装到不同 agent。

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
├── device_cli.py   # 串口桥主程序（核心）
├── AGENTS.md       # agent 行为说明：命令清单、字段含义、安全规则、自然语言映射
├── README.md       # 本文件
└── LICENSE         # MIT
```

## 安装

需要 Python 3.8+ 和串口库 `pyserial`：

```bash
pip install pyserial
```

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

本项目默认面向带两级解锁（Modbus + `AT+ENTER`）的设备。要适配到其他设备，修改 `device_cli.py` 顶部常量：

```python
UNLOCK1_HEX  = "01 10 0C 22 00 02 04 45 4C 55 43 8F 14"   # 第一级解锁帧（HEX）
UNLOCK1_OK   = "01 10 0C 22 00 02 E2 92"                  # 第一级正确响应（HEX）
UNLOCK2_CMD  = b"AT+ENTER\r\n"                            # 第二级解锁（ASCII）
UNLOCK2_MARK = b"FreeRTOS command server"                 # 第二级成功标志
```

如果你的设备：
- **无需解锁**：把 `unlock()` 改为直接 `return True`
- **解码不同**：把 `send_cmd` 里的 `decode("gbk")` 改为对应编码（`utf-8` / `latin-1` 等）
- **命令清单不同**：修改 `AGENTS.md` 的命令表

## 许可证

MIT License，见 [LICENSE](LICENSE)。
