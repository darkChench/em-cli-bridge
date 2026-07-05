#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mcp_server.py — 把 em-cli-bridge 暴露为 MCP server（stdio 传输）

复用 device_cli.py 的内核（DeviceBridge / load_config / open_serial_with_retry），
不重写串口逻辑。启动时开一次串口 + 解锁一次，后续所有 tool 调用复用这个长连接
（MCP server 是长驻进程，串口常开效率最高）。

【使用】
  1. 安装依赖：  pip install -r requirements-mcp.txt
  2. 手动测试：  python mcp_server.py --port COM59
  3. 客户端配置：见 mcp-config-examples/

【安全】
  危险命令（lfs-format / reset）必须传 confirm=True 才执行，代码级硬保护。
"""

import argparse
import sys

from mcp.server.fastmcp import FastMCP

# 复用 device_cli.py 的内核（同目录 import）
from device_cli import (
    DeviceBridge, load_config, open_serial_with_retry,
    PARITY_MAP, STOPBITS_MAP,
    UnlockError, SerialError,
)


def main():
    ap = argparse.ArgumentParser(description="em-cli-bridge MCP server (stdio)")
    ap.add_argument("--port", required=True,
                    help="串口号，如 COM3（MCP 模式必须指定，不交互提问）")
    ap.add_argument("--baud", type=int, default=115200, help="波特率，默认 115200")
    ap.add_argument("--bytesize", type=int, choices=[5, 6, 7, 8], default=8)
    ap.add_argument("--parity", choices=list(PARITY_MAP.keys()), default="N")
    ap.add_argument("--stopbits", type=float, choices=[1, 1.5, 2], default=1)
    ap.add_argument("--config", default=None, help="配置文件路径（默认按优先级查找 device.json）")
    ap.add_argument("--timeout", type=float, default=None,
                    help="命令读取超时（秒），默认读配置再默认 1.5；大输出建议设 5")
    args = ap.parse_args()

    # —— 1. 加载配置 ——
    cfg, loaded_from = load_config(args.config)
    print(f"[mcp] config: {loaded_from or 'built-in default'}", file=sys.stderr)

    default_timeout = cfg["serial"].get("default_timeout", 1.5)
    read_timeout = args.timeout if args.timeout is not None else default_timeout

    # —— 2. 开串口（MCP 模式 --port 必填，不交互） ——
    parity = PARITY_MAP[args.parity]
    stopbits = STOPBITS_MAP[args.stopbits]
    try:
        # open_serial_with_retry 失败会进交互重选，但 MCP 模式无 stdin 可用，
        # 所以用固定 port 直接开，失败即退出
        import serial as _serial
        print(f"[mcp] opening {args.port} @ {args.baud}", file=sys.stderr)
        ser = _serial.Serial(args.port, args.baud, bytesize=args.bytesize,
                             parity=parity, stopbits=stopbits, timeout=0.2)
        import time
        time.sleep(0.2)
        ser.reset_input_buffer()
    except Exception as e:
        print(f"[mcp] 串口打开失败：{e}", file=sys.stderr)
        sys.exit(3)

    # —— 3. 解锁（一次性） ——
    bridge = DeviceBridge(ser, cfg, debug=False)
    try:
        bridge.unlock()
        print("[mcp] 两级解锁成功，进入 CLI 模式", file=sys.stderr)
    except UnlockError as e:
        print(f"[mcp] 解锁失败：{e}", file=sys.stderr)
        sys.exit(2)

    # —— 4. 注册 MCP tools ——
    mcp = FastMCP("em-cli-bridge")

    def _send(cmd: str, long: bool = False) -> str:
        """统一发送 + 清洗，自动选超时。"""
        return bridge.send_cmd(cmd, 5.0 if long else read_timeout)

    @mcp.tool()
    def q_sensor() -> str:
        """🟢【只读】查询所有传感器最新采样值。
        返回字段：MPM3808(P=压力MPa,T=温度℃)、PT1000(T)、Remote(P/T/P20)、SF6综合信息。
        安全等级：只读，可直接调用。"""
        return _send("qSensor")

    @mcp.tool()
    def sw_sensor(sensor_id: int) -> str:
        """🟡【需确认】切换压力传感器（立即生效）。
        参数：sensor_id 1=MPM3808 2=SNPM602 3=CPS121 4=SCCE。
        调用前应向用户确认，因为会改变设备测量通道。"""
        if sensor_id not in (1, 2, 3, 4):
            return f"参数错误：sensor_id 必须是 1/2/3/4，收到 {sensor_id}"
        return _send(f"sw-sensor {sensor_id}")

    @mcp.tool()
    def get_rtc() -> str:
        """🟢【只读】读取设备 RTC 当前时间。"""
        return _send("get-rtc")

    @mcp.tool()
    def set_rtc(year: int, month: int, day: int, hour: int, minute: int, second: int) -> str:
        """🟡【需确认】设置设备 RTC 时间（6 个参数：年 月 日 时 分 秒）。
        调用前应向用户确认时间值。"""
        return _send(f"set-rtc {year} {month} {day} {hour} {minute} {second}")

    @mcp.tool()
    def version() -> str:
        """🟢【只读】查询设备系统版本信息（软件/硬件版本、Git 提交、组件清单）。"""
        return _send("version")

    @mcp.tool()
    def runtime() -> str:
        """🟢【只读】查询设备系统运行时长。"""
        return _send("runtime")

    @mcp.tool()
    def lfs_read(category: int) -> str:
        """🟢【只读】列出 littleFS 某类全部文件名。
        参数：category 1=Logs 2=Errno 3=Sensor 4=Cmbacktrace(崩溃回溯)。
        读日志标准流程：先用本工具列文件名，再用 lfs_read_log/lfs_read_errno 读内容。"""
        if category not in (1, 2, 3, 4):
            return f"参数错误：category 必须是 1/2/3/4，收到 {category}"
        return _send(f"lfs-read {category}")

    @mcp.tool()
    def lfs_read_log(filename: str) -> str:
        """🟢【只读】读取指定 log 文件内容。
        参数：filename 来自 lfs_read(1) 列出的文件名，如 '00000000_2000-03-11_0.txt'。
        大输出，内部用长超时。"""
        return _send(f"lfs-read-log {filename}", long=True)

    @mcp.tool()
    def lfs_read_errno(filename: str) -> str:
        """🟢【只读】读取指定 errno 文件内容。
        参数：filename 来自 lfs_read(2) 列出的文件名。大输出，内部用长超时。"""
        return _send(f"lfs-read-errno {filename}", long=True)

    @mcp.tool()
    def lfs_log_info() -> str:
        """🟢【只读】查询 log 目录占用情况（文件名及大小）。"""
        return _send("lfs-log-info")

    @mcp.tool()
    def lfs_errno_info() -> str:
        """🟢【只读】查询 errno 目录占用情况。"""
        return _send("lfs-errno-info")

    @mcp.tool()
    def lfs_flush() -> str:
        """🟡【需确认】flush 文件系统（强制缓冲区落盘）。调用前应向用户确认。"""
        return _send("lfs-flush")

    @mcp.tool()
    def lfs_format(confirm: bool = False) -> str:
        """🔴【危险】格式化 littleFS（数据全部丢失，不可恢复）！
        必须传 confirm=True 才执行；这是代码级硬保护。
        调用前务必向用户明确二次确认并提示后果。"""
        if not confirm:
            return ("⚠ 已拦截：格式化是危险操作。"
                    "确认要格式化（将丢失全部日志/错误码/传感器数据）请重新调用并传 confirm=true。")
        return _send("lfs-format")

    @mcp.tool()
    def reset(confirm: bool = False) -> str:
        """🔴【危险】系统复位（设备重启）！
        必须传 confirm=True 才执行；这是代码级硬保护。
        调用前务必向用户明确二次确认。"""
        if not confirm:
            return "⚠ 已拦截：复位是危险操作。确认要重启设备请重新调用并传 confirm=true。"
        return _send("reset")

    print(f"[mcp] 已注册 14 个 tool，进入 MCP 主循环（stdio）", file=sys.stderr)

    # —— 5. 进入 MCP 主循环（阻塞，stdio 传输） ——
    mcp.run()


if __name__ == "__main__":
    main()
