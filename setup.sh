#!/usr/bin/env bash
# ============================================================
#  em-cli-bridge 一键环境搭建（Linux / macOS）
#  干三件事：① 检查 Python ② 建虚拟环境 ③ 装依赖
#  用法：chmod +x setup.sh && ./setup.sh
# ============================================================
set -e

echo ""
echo "============================================================"
echo "  em-cli-bridge 环境搭建"
echo "============================================================"
echo ""

# —— 1. 检查 Python ——
echo "[1/4] 检查 Python..."
if command -v python3 >/dev/null 2>&1; then
    PY=python3
elif command -v python >/dev/null 2>&1; then
    PY=python
else
    echo ""
    echo "❌ 未检测到 Python。请先安装 Python 3.8+。"
    exit 1
fi
PYVER=$($PY --version)
echo "   ✓ $PYVER"

# —— 2. 建虚拟环境 ——
echo ""
echo "[2/4] 创建虚拟环境 .venv ..."
if [ -d .venv ]; then
    echo "   .venv 已存在，跳过创建。如需重建请先删除：rm -rf .venv"
else
    $PY -m venv .venv
    echo "   ✓ 虚拟环境已创建"
fi

# —— 3. 激活并升级 pip ——
echo ""
echo "[3/4] 激活虚拟环境并升级 pip ..."
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip >/dev/null 2>&1
echo "   ✓ 已激活"

# —— 4. 装依赖 ——
echo ""
echo "[4/4] 安装依赖（requirements.txt）..."
pip install -r requirements.txt

# —— 完成 ——
echo ""
echo "============================================================"
echo "  ✓ 环境搭建完成！"
echo "============================================================"
echo ""
echo " 接下来："
echo "  1. 测试 bridge（每次新开终端需先激活虚拟环境）："
echo "       source .venv/bin/activate"
echo "       python device_cli.py cmd qSensor"
echo ""
echo "  2. 如需 MCP server，再装可选依赖："
echo "       pip install -r requirements-mcp.txt"
echo ""
echo "  3. 查看设备串口号：ls /dev/tty* (Linux) 或 ls /dev/cu.* (macOS)"
echo ""
