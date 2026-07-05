# 设备 CLI 说明

本机通过串口 console 操作嵌入式设备。**agent 不直接操作串口，统一通过 bridge 脚本 `device_cli.py` 执行命令**，bridge 内部会自动完成"开串口→两级解锁→发命令→收回复→关串口"。

## 零、如何执行命令（agent 必看）

所有设备操作都走 bridge 脚本。**串口参数用命令行参数设置；串口号默认交互式输入（运行后会列出可用端口并提问），用 `--port COM3` 可跳过提问用于非交互调用。**

```
python device_cli.py [串口参数] cmd <CLI命令及参数>
```

串口参数（可选）：
- `--port COM3`    指定串口号（不填则运行时交互输入）
- `--baud 115200`  波特率（默认 115200）
- `--bytesize 8`   数据位 5/6/7/8（默认 8）
- `--parity N`     校验位 N/E/O/M/S（默认 N）
- `--stopbits 1`   停止位 1/1.5/2（默认 1）
- `--debug`        打印收发细节到 stderr

示例：

```
python device_cli.py cmd qSensor                       # 运行时问串口号
python device_cli.py --baud 9600 cmd qSensor           # 改波特率
python device_cli.py --port COM3 cmd qSensor           # agent 非交互调用
python device_cli.py cmd get-rtc
python device_cli.py cmd lfs-read 1
python device_cli.py cmd lfs-read-log 00000000_2000-03-11_0.txt
python device_cli.py cmd set-rtc 2026 7 5 10 30 0
python device_cli.py unlock                            # 仅测试两级解锁
python device_cli.py cmd exit                          # 退出 CLI
```

- bridge 的 **stdout 是设备的文本回复**（agent 直接解读）；其余提示都在 stderr。
- 串口被占用/失败时，脚本会**打印原因（如"被占用请关闭其他串口工具"）并让用户重新选口**，不会直接崩溃。

## 一、进入 / 退出 CLI（两级解锁机制）

agent 无需关心解锁细节，bridge 已自动处理。仅作背景说明：

1. **解锁指令 1**（Modbus, HEX）：`01 10 0C 22 00 02 04 45 4C 55 43 8F 14`，正确响应 `01 10 0C 22 00 02 E2 92`（标准 Modbus 精简应答）。注意该设备 UART 会**回显发送的字节**，所以实际收到的字节流是"回显帧(14B) + 应答帧(8B)"，bridge 已自动剥掉回显前缀再校验。
2. **解锁指令 2**（CMD, ASCII）：`AT+ENTER\r\n`，响应含 `FreeRTOS command server.`
3. **退出**：`exit` —— 响应 `User exit console.`

## 二、命令清单（按功能分类）

> **副作用等级**：🟢 只读（安全） / 🟡 有副作用（需确认） / 🔴 危险或不可逆（务必先确认）

### 1. 传感器
| 命令 | 说明 | 等级 |
|------|------|------|
| `qSensor` | 查询所有传感器最新采样值 | 🟢 |
| `sw-sensor <n>` | 切换压力传感器（**立即生效**）。n: 1=MPM3808 2=SNPM602 3=CPS121 4=SCCE | 🟡 |

**`qSensor` 输出字段含义**（每行 `设备名 : 键值...`）：
- `MPM3808 : P:0.1008Mpa, T:25.49℃` —— 压力传感器，P=压力(MPa)，T=温度(℃)
- `PT1000  : T:25.93` —— 温度传感器，T=温度(℃)
- `Remote: P:.. T:.. P20:..` —— 远端/折算：P=压力，T=温度，P20=20℃折算压力(MPa)
- `Debug sf6 info: P:.. T:.. P20:.. sensorT:.. tempCabtCu:.. tempCabtTag:..` —— SF6 综合调试信息

### 2. 文件系统（littleFS）
| 命令 | 说明 | 等级 |
|------|------|------|
| `lfs-log-info` | 查询 log 目录占用（dir/file） | 🟢 |
| `lfs-errno-info` | 查询 errno 目录占用 | 🟢 |
| `lfs-read <n>` | 读全部文件：1=Logs 2=Errno 3=Sensor 4=Cmbacktrace | 🟢 |
| `lfs-read-log <file>` | 读指定 log 文件内容，`<file>` 为文件名，来自 `lfs-read 1` 列出的文件名，例如 `lfs-read-log 00000000_2000-03-11_0.txt` | 🟢 |
| `lfs-read-errno <file>` | 读指定 errno 文件内容，`<file>` 为文件名，来自 `lfs-read 2` 列出的文件名 | 🟢 |
| `lfs-flush` | flush 文件系统 | 🟡 |
| `lfs-format` | **格式化 littleFS（数据全失）** | 🔴 |
| `lfs-test1` / `lfs-test2` / `lfs-test3` | 测试命令（研发用） | 🟡 |

> **读日志标准流程**：先 `lfs-read 1`（Logs）或 `lfs-read 2`（Errno）拿到文件名列表 → 再用文件名执行 `lfs-read-log <file>` / `lfs-read-errno <file>` 读具体内容。

### 3. RTC 时间
| 命令 | 说明 | 等级 |
|------|------|------|
| `get-rtc` | 读取 RTC 时间 | 🟢 |
| `set-rtc <yyyy> <mm> <dd> <hh> <mm> <ss>` | 设置 RTC 时间，6 个参数：年 月 日 时 分 秒 | 🟡 |

### 4. 系统
| 命令 | 说明 | 等级 |
|------|------|------|
| `version` | 查询系统版本信息 | 🟢 |
| `runtime` | 查询系统运行时长 | 🟢 |
| `monitor` | 开启系统 monitor 实时输出 | 🟡 |
| `nomonitor` | 停止 monitor 输出 | 🟢 |
| `reset` | **系统复位（重启）** | 🔴 |

## 三、典型用法（自然语言 → 命令）

下列命令均通过 bridge 执行：`python device_cli.py cmd <命令>`

- "查询最新数据 / 最新采样 / 现在压力温度多少" → `qSensor`，按上面字段含义解读
- "看日志 / 看错误码" → 先 `lfs-read 1`（Logs）或 `lfs-read 2`（Errno）列出文件名，再用文件名执行 `lfs-read-log <file>` / `lfs-read-errno <file>`
- "看传感器历史" → `lfs-read 3`（Sensor）
- "现在几点 / 设备时间" → `get-rtc`
- "对时 / 设置时间为 xxx" → `set-rtc yyyy mm dd hh mm ss`（**执行前向用户确认时间值**）
- "设备跑了多久 / 运行时间" → `runtime`
- "固件版本" → `version`
- "切换压力传感器到 xxx" → `sw-sensor <n>`（立即生效，**先确认**）

## 四、安全约定（agent 必须遵守）

1. 🟢 只读命令可直接通过 bridge 执行。
2. 🟡 命令（切换、设置、flush、monitor、test）执行前**必须先向用户确认**。
3. 🔴 命令（`lfs-format`、`reset`）**必须明确二次确认**后才能执行，并提示后果。
4. 原始输出若非结构化，按"二、`qSensor` 输出字段含义"解读，不要臆测字段。
5. 解锁由 bridge 自动完成，agent 不要自己拼解锁报文。bridge 每次运行会先发 `exit` 预清理、再做两级解锁，**保证幂等**——同一条命令反复调用结果一致，agent 无需关心设备当前处于什么状态。

## 五、初次部署（人工，仅一次）

1. 安装 Python 依赖：`pip install pyserial`
2. 测试解锁：`python device_cli.py --debug unlock`
   - 脚本会列出当前检测到的串口并问你要选哪个，输入对应 COM 口（如 `COM3`）。
   - 看到 stderr 输出 `[ok] 已打开 COMx @ 115200` 和 `[ok] 两级解锁成功` 即通。
   - 若提示"串口被占用"：先关闭其他串口工具（SSCOM / MobaXterm / 调试助手等），再按提示重选。
   - 若提示"串口不存在"：检查设备连接、USB 转串口驱动是否安装（设备管理器里端口有无黄色感叹号）。
3. 测试一条命令：`python device_cli.py cmd qSensor`，能看到传感器数据即全通。
4. 波特率等参数不匹配时用命令行参数调整，例如 `python device_cli.py --baud 9600 cmd qSensor`。
5. agent 非交互调用时需用 `--port` 指定串口号，避免卡在输入等待。
