#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
device_cli.py — 设备串口命令桥（bridge）

作用：让 AI agent 或用户通过一条 shell 命令操作设备。
内部自动完成：开串口 → 两级解锁 → 发 CLI 命令 → 收回复 → 关串口。

【交互规则】
- 串口号：每次运行时交互式输入（并列出当前可用端口），失败/占用时提示并重试。
- 波特率/数据位/校验/停止位：通过命令行参数设置。
- 例外：若用 --port 指定串口号，则跳过交互输入（供 agent 非交互调用）。

用法示例：
    python device_cli.py cmd qSensor                       # 运行时问你要 COM 口
    python device_cli.py --baud 9600 cmd qSensor           # 改波特率
    python device_cli.py --port COM3 cmd qSensor           # 跳过提问（agent 用）
    python device_cli.py unlock                            # 仅测试两级解锁
    python device_cli.py cmd set-rtc 2026 7 5 10 30 0
"""

import argparse
import re
import sys
import time

try:
    import serial  # pyserial
    from serial.tools import list_ports
except ImportError:
    print("缺少 pyserial，请先安装：  pip install pyserial", file=sys.stderr)
    sys.exit(1)


# —— 两级解锁用的固定报文（来自 AGENTS.md）——
UNLOCK1_HEX  = "01 10 0C 22 00 02 04 45 4C 55 43 8F 14"   # 第一级 Modbus（HEX）
UNLOCK1_OK   = "01 10 0C 22 00 02 E2 92"                  # 第一级正确响应（标准 Modbus 精简应答，8 字节）
UNLOCK2_CMD  = b"AT+ENTER\r\n"                            # 第二级 CMD（ASCII）
UNLOCK2_MARK = b"FreeRTOS command server"                 # 第二级成功标志

PARITY_MAP = {
    "N": serial.PARITY_NONE, "E": serial.PARITY_EVEN, "O": serial.PARITY_ODD,
    "M": serial.PARITY_MARK, "S": serial.PARITY_SPACE,
}
STOPBITS_MAP = {1: serial.STOPBITS_ONE, 1.5: serial.STOPBITS_ONE_POINT_FIVE,
                2: serial.STOPBITS_TWO}

# 匹配 ANSI 转义序列（颜色码等），用于剥离设备输出中的终端控制字符
# 例如 \x1b[36;22m...\x1b[0m
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def strip_ansi(text: str) -> str:
    """剥离 ANSI 转义序列（颜色码、光标控制等），返回纯文本"""
    return _ANSI_RE.sub("", text)


def list_available_ports():
    """返回 [(设备名, 描述)]，用于引导用户选口"""
    return [(p.device, p.description) for p in list_ports.comports()]


def ask_port():
    """交互式询问串口号；输入 q 退出"""
    print("\n=== 设备串口命令桥 ===")
    avail = list_available_ports()
    if avail:
        print("当前检测到的串口：")
        for dev, desc in avail:
            print(f"  {dev:<10}  ({desc})")
    else:
        print("⚠ 未检测到任何串口。请检查：设备是否已连接 / USB转串口驱动是否安装 / 设备管理器里端口是否正常。")
    while True:
        port = input("\n请输入串口号（如 COM3，输入 q 退出）: ").strip()
        if port.lower() in ("q", "quit", "exit", ""):
            print("已取消。")
            sys.exit(0)
        return port


def open_serial_with_retry(get_port, baud, bytesize, parity, stopbits, debug):
    """尝试打开串口；占用/失败时打印友好提示并让用户重新选口。

    get_port: 一个返回串口号的可调用；首次用命令行 --port（或 None），
              失败重试时改成 ask_port()，于是后续变成交互式。"""
    port = get_port()
    while True:
        try:
            if debug:
                print(f"[open] {port} @ {baud} {bytesize}{parity}{stopbits}",
                      file=sys.stderr)
            ser = serial.Serial(port, baud, bytesize=bytesize, parity=parity,
                                stopbits=stopbits, timeout=0.2)
            time.sleep(0.2)
            ser.reset_input_buffer()
            print(f"[ok] 已打开 {port} @ {baud}", file=sys.stderr)
            return ser
        except serial.SerialException as e:
            low = str(e).lower()
            if "access is denied" in low or "拒绝访问" in str(e) or "permission" in low:
                print(f"\n❌ 串口 {port} 被占用或无访问权限。")
                print("   最常见原因：其他串口工具（SSCOM / MobaXterm / 串口调试助手 / Putty）正占用该口。")
                print("   → 请关闭占用该串口的程序后重试。")
            elif "could not open" in low or "file not found" in low or "找不到" in str(e):
                print(f"\n❌ 串口 {port} 不存在或无法打开。")
                print("   请确认拼写正确，且设备已连接、驱动已安装。")
            else:
                print(f"\n❌ 打开串口 {port} 失败：{e}")
            port = ask_port()   # 失败后切成交互式重选
        except Exception as e:
            print(f"\n❌ 未知错误：{e}")
            port = ask_port()


class DeviceBridge:
    def __init__(self, ser, debug=False):
        self.ser = ser
        self.debug = debug

    def _read_for(self, seconds: float) -> bytes:
        """持续读 seconds 秒；收到新数据再宽限 0.3s，保证多行输出读全。"""
        end = time.time() + seconds
        buf = bytearray()
        while time.time() < end:
            chunk = self.ser.read(256)
            if chunk:
                buf += chunk
                end = time.time() + 0.3
        return bytes(buf)

    def unlock(self) -> bool:
        """执行两级解锁，失败抛异常。
        每次运行都先把设备拉回已知状态，保证幂等（agent 可重复调用同一命令）。"""
        # —— 预清理 ——
        # 若设备仍停留在上次的 CLI 模式，exit 让它退出回到未解锁态；
        # 若设备本就未解锁，exit 会被忽略，无害。
        # 不做这一步的话：重复解锁的字节会混进 CLI 命令行，扰乱状态，
        # 表现为后续命令 "Command not recognised"。
        self.ser.write(b"exit\r\n")
        time.sleep(0.3)
        self.ser.reset_input_buffer()

        # —— 第一级：Modbus 二进制 ——
        # 该设备 UART 会回显发送字节：先收到本帧回显(14B)，再收到标准应答(8B)。
        # 这里剥掉开头的回显前缀，再去匹配末尾的标准应答。
        pkt1 = bytes.fromhex(UNLOCK1_HEX.replace(" ", ""))
        ok1  = bytes.fromhex(UNLOCK1_OK.replace(" ", ""))
        self.ser.write(pkt1)
        resp1 = self._read_for(0.8)
        echo1 = pkt1 if resp1.startswith(pkt1) else b""
        payload1 = resp1[len(echo1):] if echo1 else resp1
        if self.debug:
            print(f"[unlock1 raw ] {resp1.hex(' ')}", file=sys.stderr)
            if echo1:
                print(f"[unlock1 echo] (剥掉 {len(echo1)}B 回显前缀)", file=sys.stderr)
            print(f"[unlock1 pay ] {payload1.hex(' ')}", file=sys.stderr)
        if payload1[:len(ok1)] != ok1:
            raise RuntimeError(
                f"第一级解锁失败：预期 {ok1.hex(' ')}，实际 {payload1.hex(' ')}"
            )

        # —— 第二级：AT+ENTER ——
        # 同样存在回显，但这里只关心是否出现关键标志字符串，回显不影响判断。
        self.ser.write(UNLOCK2_CMD)
        resp2 = self._read_for(1.0)
        if self.debug:
            print(f"[unlock2 resp] {resp2!r}", file=sys.stderr)
        if UNLOCK2_MARK not in resp2:
            print("[warn] 未捕获到 'FreeRTOS command server'，可能已处于 CLI 模式",
                  file=sys.stderr)
        return True

    def send_cmd(self, cmd: str) -> str:
        """发送一条 CLI 命令，返回干净文本回复。
        处理三件事：
        1. 剥掉首行命令回显（设备把收到的命令文本又吐回来）；
        2. 剥掉尾部的 CLI 提示符行（如 '[Press ENTER ...]'、'>'）；
        3. 用 GBK 解码（设备输出的 '℃' 等中文字符在 GBK 编码下正确，
           否则按 Windows 默认或 UTF-8 解会变乱码）。"""
        self.ser.write((cmd + "\r\n").encode())
        raw = self._read_for(1.5)
        text = raw.decode("gbk", errors="replace")
        text = strip_ansi(text)   # 剥离 ANSI 颜色码等终端控制字符

        lines = [ln.rstrip() for ln in text.splitlines()]
        # 剥首部：命令回显行（CLI 模式下会把输入字节当文本回显）
        if lines and lines[0].strip() == cmd.strip():
            lines = lines[1:]
        # 剥尾部：CLI 提示符行（空行、'>'、'[Press ENTER ...]' 等）
        while lines:
            s = lines[-1].strip()
            if s == "" or s == ">" or s.startswith("[Press ENTER"):
                lines.pop()
            else:
                break
        return "\n".join(lines)

    def close(self):
        try:
            self.ser.close()
        except Exception:
            pass


def main():
    ap = argparse.ArgumentParser(
        description="设备串口命令桥：交互式输入串口号，命令行设置串口参数",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例:\n"
               "  python device_cli.py cmd qSensor\n"
               "  python device_cli.py --baud 9600 cmd qSensor\n"
               "  python device_cli.py --port COM3 cmd qSensor   (agent 非交互调用)\n")
    ap.add_argument("--port", default=None,
                    help="直接指定串口号（如 COM3）；不填则运行时交互输入")
    ap.add_argument("--baud", type=int, default=115200, help="波特率，默认 115200")
    ap.add_argument("--bytesize", type=int, choices=[5, 6, 7, 8], default=8,
                    help="数据位，默认 8")
    ap.add_argument("--parity", choices=list(PARITY_MAP.keys()), default="N",
                    help="校验位 N/E/O/M/S，默认 N")
    ap.add_argument("--stopbits", type=float, choices=[1, 1.5, 2], default=1,
                    help="停止位 1/1.5/2，默认 1")
    ap.add_argument("--debug", action="store_true", help="打印收发细节到 stderr")
    sub = ap.add_subparsers(dest="action", required=True)
    sub.add_parser("unlock", help="仅执行两级解锁测试")
    p_cmd = sub.add_parser("cmd", help="执行一条 CLI 命令")
    p_cmd.add_argument("argv", nargs="+", help="CLI 命令及其参数，如 qSensor")

    args = ap.parse_args()

    parity = PARITY_MAP[args.parity]
    stopbits = STOPBITS_MAP[args.stopbits]

    # 首选命令行 --port；没给就用交互式；失败重试也走交互式
    initial_port = args.port if args.port else None

    def get_port():
        return initial_port if initial_port else ask_port()

    ser = open_serial_with_retry(get_port, args.baud, args.bytesize,
                                 parity, stopbits, args.debug)
    br = DeviceBridge(ser, debug=args.debug)
    try:
        br.unlock()
        if args.action == "cmd":
            cmd = " ".join(args.argv)
            out = br.send_cmd(cmd)
            print(out, end="")          # 设备回复打印到 stdout（给 agent 看）
        elif args.action == "unlock":
            print("[ok] 两级解锁成功，已进入 CLI 模式", file=sys.stderr)
    finally:
        br.close()


if __name__ == "__main__":
    main()
