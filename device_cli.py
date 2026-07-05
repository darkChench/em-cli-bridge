#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
device_cli.py — 设备串口命令桥（bridge）v0.2.0

作用：让 AI agent 或用户通过一条 shell 命令操作设备。
内部自动完成：开串口 → 两级解锁 → 发 CLI 命令 → 收回复 → 关串口。

【v0.2.0 特性】
- 配置文件化：解锁帧/编码/超时放 device.json，换设备零改代码（无配置时用内置默认）
- 命令超时参数化：--timeout / --long，防止大输出（日志）读不全
- 规范化退出码：成功=0，参数/配置错=1，解锁失败=2，串口错误=3，超时=4
- --version 查看版本

用法示例：
    python device_cli.py cmd qSensor                       # 运行时问串口号
    python device_cli.py --baud 9600 cmd qSensor           # 改波特率
    python device_cli.py --port COM59 cmd qSensor          # agent 非交互调用
    python device_cli.py --port COM59 cmd lfs-read-log xxx.txt --long  # 大输出长超时
    python device_cli.py --config mydevice.json cmd qSensor
    python device_cli.py --version
    python device_cli.py unlock                            # 仅测试两级解锁

配置加载优先级（高→低）：--config 指定 > 工作目录 device.json > 用户目录
~/.em-cli-bridge/device.json > 内置默认值。
"""

import argparse
import json
import os
import re
import sys
import time

__version__ = "0.2.0"

try:
    import serial  # pyserial
    from serial.tools import list_ports
except ImportError:
    print("缺少 pyserial，请先安装：  pip install pyserial", file=sys.stderr)
    sys.exit(1)


# —— 标准化退出码 ——
EXIT_OK          = 0   # 成功
EXIT_ERROR       = 1   # 通用错误（参数错误、配置错误）
EXIT_UNLOCK_FAIL = 2   # 解锁失败
EXIT_SERIAL      = 3   # 串口错误（打不开、被占用）
EXIT_TIMEOUT     = 4   # 超时（读取无数据）


# —— 内置默认配置（向后兼容：无配置文件时用这套，即当前 RDM 设备参数）——
DEFAULT_CONFIG = {
    "unlock": {
        "stage1_hex":  "01 10 0C 22 00 02 04 45 4C 55 43 8F 14",
        "stage1_ok":   "01 10 0C 22 00 02 E2 92",
        "stage2_cmd":  "AT+ENTER\\r\\n",
        "stage2_mark": "FreeRTOS command server",
    },
    "serial": {
        "encoding":       "gbk",
        "default_timeout": 1.5,
    },
}


def deep_merge(base: dict, override: dict) -> dict:
    """用 override 递归覆盖 base，返回新 dict。保证嵌套结构也能合并。"""
    out = dict(base)
    for k, v in override.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config(explicit_path=None):
    """按优先级加载配置文件并合并到默认值上。返回最终配置 dict。"""
    candidates = []
    if explicit_path:
        candidates.append(explicit_path)
    else:
        candidates.append(os.path.join(os.getcwd(), "device.json"))
        home = os.path.expanduser("~")
        candidates.append(os.path.join(home, ".em-cli-bridge", "device.json"))

    cfg = dict(DEFAULT_CONFIG)
    loaded_from = None
    for path in candidates:
        if path and os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    user_cfg = json.load(f)
                cfg = deep_merge(DEFAULT_CONFIG, user_cfg)
                loaded_from = path
                break
            except (json.JSONDecodeError, OSError) as e:
                print(f"[warn] 配置文件 {path} 解析失败：{e}，回退到内置默认",
                      file=sys.stderr)
    return cfg, loaded_from


# —— 解锁报文预处理：把配置里的字符串转成运行时用的 bytes ——
def build_unlock_packets(cfg):
    u = cfg["unlock"]
    stage1_cmd = bytes.fromhex(u["stage1_hex"].replace(" ", ""))
    stage1_ok  = bytes.fromhex(u["stage1_ok"].replace(" ", ""))
    # stage2_cmd 在 JSON 里写成形如 "AT+ENTER\\r\\n"，需把字面 \r\n 转成真实换行
    stage2_cmd = u["stage2_cmd"].encode("latin-1").decode("unicode_escape").encode("latin-1")
    stage2_mark = u["stage2_mark"].encode("latin-1")
    return stage1_cmd, stage1_ok, stage2_cmd, stage2_mark


PARITY_MAP = {
    "N": serial.PARITY_NONE, "E": serial.PARITY_EVEN, "O": serial.PARITY_ODD,
    "M": serial.PARITY_MARK, "S": serial.PARITY_SPACE,
}
STOPBITS_MAP = {1: serial.STOPBITS_ONE, 1.5: serial.STOPBITS_ONE_POINT_FIVE,
                2: serial.STOPBITS_TWO}

# 匹配 ANSI 转义序列（颜色码等），用于剥离设备输出中的终端控制字符
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


def list_available_ports():
    return [(p.device, p.description) for p in list_ports.comports()]


def ask_port():
    print("\n=== 设备串口命令桥 v%s ===" % __version__)
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
            sys.exit(EXIT_OK)
        return port


class SerialError(Exception):
    """串口打开/IO 错误（退出码 3）"""


class UnlockError(Exception):
    """解锁失败（退出码 2）"""


class TimeoutError_(Exception):
    """读取超时且无数据（退出码 4）"""


def open_serial_with_retry(get_port, baud, bytesize, parity, stopbits, debug):
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
                print(f"\n❌ 串口 {port} 被占用或无访问权限。", file=sys.stderr)
                print("   最常见原因：其他串口工具（SSCOM / MobaXterm / 串口调试助手 / Putty）正占用该口。",
                      file=sys.stderr)
                print("   → 请关闭占用该串口的程序后重试。", file=sys.stderr)
            elif "could not open" in low or "file not found" in low or "找不到" in str(e):
                print(f"\n❌ 串口 {port} 不存在或无法打开。", file=sys.stderr)
                print("   请确认拼写正确，且设备已连接、驱动已安装。", file=sys.stderr)
            else:
                print(f"\n❌ 打开串口 {port} 失败：{e}", file=sys.stderr)
            port = ask_port()   # 失败后切成交互式重选
        except Exception as e:
            print(f"\n❌ 未知错误：{e}", file=sys.stderr)
            port = ask_port()


class DeviceBridge:
    def __init__(self, ser, cfg, debug=False):
        self.ser = ser
        self.cfg = cfg
        self.debug = debug
        self.encoding = cfg["serial"]["encoding"]
        # 预处理解锁报文
        (self.s1_cmd, self.s1_ok, self.s2_cmd, self.s2_mark) = build_unlock_packets(cfg)

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
        """执行两级解锁，失败抛 UnlockError。每次先 exit 预清理，保证幂等。"""
        # —— 预清理 ——
        self.ser.write(b"exit\r\n")
        time.sleep(0.3)
        self.ser.reset_input_buffer()

        # —— 第一级：Modbus 二进制 ——
        # 设备 UART 会回显发送字节：先收到本帧回显(14B)，再收到标准应答(8B)。
        # 这里剥掉开头的回显前缀，再去匹配末尾的标准应答。
        self.ser.write(self.s1_cmd)
        resp1 = self._read_for(0.8)
        echo1 = self.s1_cmd if resp1.startswith(self.s1_cmd) else b""
        payload1 = resp1[len(echo1):] if echo1 else resp1
        if self.debug:
            print(f"[unlock1 raw ] {resp1.hex(' ')}", file=sys.stderr)
            if echo1:
                print(f"[unlock1 echo] (剥掉 {len(echo1)}B 回显前缀)", file=sys.stderr)
            print(f"[unlock1 pay ] {payload1.hex(' ')}", file=sys.stderr)
        if payload1[:len(self.s1_ok)] != self.s1_ok:
            raise UnlockError(
                f"第一级解锁失败：预期 {self.s1_ok.hex(' ')}，实际 {payload1.hex(' ')}"
            )

        # —— 第二级：AT+ENTER ——
        self.ser.write(self.s2_cmd)
        resp2 = self._read_for(1.0)
        if self.debug:
            print(f"[unlock2 resp] {resp2!r}", file=sys.stderr)
        if self.s2_mark not in resp2:
            print("[warn] 未捕获到第二级解锁成功标志，可能已处于 CLI 模式",
                  file=sys.stderr)
        return True

    def send_cmd(self, cmd: str, timeout: float) -> str:
        """发送一条 CLI 命令，返回干净文本回复。
        处理：剥首部命令回显、剥尾部 CLI 提示符、剥 ANSI 颜色码、按配置编码解码。"""
        self.ser.write((cmd + "\r\n").encode())
        raw = self._read_for(timeout)
        if not raw.strip():
            raise TimeoutError_(f"命令 '{cmd}' 在 {timeout}s 内无数据返回")
        text = raw.decode(self.encoding, errors="replace")
        text = strip_ansi(text)

        lines = [ln.rstrip() for ln in text.splitlines()]
        if lines and lines[0].strip() == cmd.strip():
            lines = lines[1:]
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
        description="设备串口命令桥 v%s：交互式输入串口号，命令行设置串口参数" % __version__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例:\n"
               "  python device_cli.py cmd qSensor\n"
               "  python device_cli.py --baud 9600 cmd qSensor\n"
               "  python device_cli.py --port COM59 cmd qSensor\n"
               "  python device_cli.py --port COM59 cmd lfs-read-log xxx.txt --long\n"
               "  python device_cli.py --config mydevice.json cmd qSensor\n"
               "  python device_cli.py --version\n")
    ap.add_argument("--version", action="version", version=f"em-cli-bridge {__version__}")
    ap.add_argument("--port", default=None,
                    help="直接指定串口号（如 COM3）；不填则运行时交互输入")
    ap.add_argument("--baud", type=int, default=115200, help="波特率，默认 115200")
    ap.add_argument("--bytesize", type=int, choices=[5, 6, 7, 8], default=8,
                    help="数据位，默认 8")
    ap.add_argument("--parity", choices=list(PARITY_MAP.keys()), default="N",
                    help="校验位 N/E/O/M/S，默认 N")
    ap.add_argument("--stopbits", type=float, choices=[1, 1.5, 2], default=1,
                    help="停止位 1/1.5/2，默认 1")
    ap.add_argument("--config", default=None,
                    help="指定配置文件路径（默认按优先级查找 device.json）")
    ap.add_argument("--timeout", type=float, default=None,
                    help="命令读取超时（秒），默认读配置，再默认 1.5")
    ap.add_argument("--debug", action="store_true", help="打印收发细节到 stderr")
    sub = ap.add_subparsers(dest="action", required=True)
    sub.add_parser("unlock", help="仅执行两级解锁测试")
    p_cmd = sub.add_parser("cmd", help="执行一条 CLI 命令")
    p_cmd.add_argument("--long", action="store_true",
                       help="使用长超时（5s），适合 lfs-read-log/lfs-read 等大输出命令")
    p_cmd.add_argument("argv", nargs="+", help="CLI 命令及其参数，如 qSensor")

    args = ap.parse_args()

    # —— 加载配置 ——
    cfg, loaded_from = load_config(args.config)
    if args.debug and loaded_from:
        print(f"[config] 已加载 {loaded_from}", file=sys.stderr)
    elif args.debug:
        print("[config] 未找到配置文件，使用内置默认", file=sys.stderr)

    parity = PARITY_MAP[args.parity]
    stopbits = STOPBITS_MAP[args.stopbits]

    # 决定读取超时：命令行 --timeout > 配置 default_timeout > 1.5
    default_timeout = cfg["serial"].get("default_timeout", 1.5)
    if args.action == "cmd" and args.long:
        read_timeout = 5.0
    elif args.timeout is not None:
        read_timeout = args.timeout
    else:
        read_timeout = default_timeout

    initial_port = args.port

    def get_port():
        return initial_port if initial_port else ask_port()

    # —— 主流程 ——
    try:
        ser = open_serial_with_retry(get_port, args.baud, args.bytesize,
                                     parity, stopbits, args.debug)
    except Exception as e:
        print(f"❌ 串口错误：{e}", file=sys.stderr)
        sys.exit(EXIT_SERIAL)

    br = DeviceBridge(ser, cfg, debug=args.debug)
    try:
        br.unlock()
        if args.action == "cmd":
            cmd = " ".join(args.argv)
            out = br.send_cmd(cmd, read_timeout)
            print(out, end="")
        elif args.action == "unlock":
            print("[ok] 两级解锁成功，已进入 CLI 模式", file=sys.stderr)
    except UnlockError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(EXIT_UNLOCK_FAIL)
    except TimeoutError_ as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(EXIT_TIMEOUT)
    except serial.SerialException as e:
        print(f"❌ 串口 IO 错误：{e}", file=sys.stderr)
        sys.exit(EXIT_SERIAL)
    finally:
        br.close()


if __name__ == "__main__":
    main()
