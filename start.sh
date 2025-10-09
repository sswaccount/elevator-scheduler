#!/usr/bin/env bash
set -e  # 一旦出错立即退出

VENV_DIR=".venv"
REQUIREMENTS_FILE="requirements.txt"
ENTRANCE_FILE="main.py"

echo "=== Python 环境检查 ==="

# 检查 Python3 是否存在
if ! command -v python3 &> /dev/null; then
    echo "❌ 未检测到 Python3，请先安装 Python 3.11 或更高版本。"
    exit 1
fi

# 检查 Python 版本
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -le 11 ]); then
    echo "❌ Python 版本必须 > 3.11，当前版本为 $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python 版本符合要求：$PYTHON_VERSION"

echo
echo "=== 虚拟环境检查 ==="

# 创建虚拟环境（如果不存在）
if [ ! -d "$VENV_DIR" ]; then
    echo "🔧 创建虚拟环境：$VENV_DIR"
    python3 -m venv --copies "$VENV_DIR"
else
    echo "✅ 虚拟环境已存在：$VENV_DIR"
fi

# 激活虚拟环境
ACTIVATE_SCRIPT="$VENV_DIR/bin/activate"
if [ ! -f "$ACTIVATE_SCRIPT" ]; then
    echo "❌ 无法找到虚拟环境激活脚本：$ACTIVATE_SCRIPT"
    exit 1
fi

source "$ACTIVATE_SCRIPT"
echo "✅ 虚拟环境已激活"

echo
echo "=== 安装依赖 ==="

if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "🔧 正在安装依赖，请稍候..."
    pip install -r "$REQUIREMENTS_FILE" --quiet > /dev/null 2>&1
    echo "✅ 依赖安装完成"
else
    echo "❌ 未找到 $REQUIREMENTS_FILE，跳过依赖安装"
fi

echo
echo "=== 运行程序 ==="

if [ -f "$ENTRANCE_FILE" ]; then
    echo "🚀 正在运行 $ENTRANCE_FILE ..."
    python "$ENTRANCE_FILE"
else
    echo "❌ 未找到入口文件：$ENTRANCE_FILE"
    exit 1
fi
