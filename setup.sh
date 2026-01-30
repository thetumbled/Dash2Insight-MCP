#!/bin/bash
# 项目环境设置脚本

set -e

# 切换到脚本所在目录（支持从任意位置运行）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Dash2Insight-MCP - 环境设置"
echo "=========================================="
echo "项目目录: $SCRIPT_DIR"
echo

# 检查 Python 版本是否 >= 3.10
check_python_version() {
    local python_cmd=$1
    if command -v "$python_cmd" &> /dev/null; then
        local version=$($python_cmd -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null)
        local major=$(echo "$version" | cut -d. -f1)
        local minor=$(echo "$version" | cut -d. -f2)
        if [ "$major" -ge 3 ] && [ "$minor" -ge 10 ]; then
            echo "$python_cmd"
            return 0
        fi
    fi
    return 1
}

echo "1. 检查 Python 版本..."
PYTHON_CMD=""
USE_UV=false

# 依次检查 python3、python 命令
for cmd in python3 python; do
    if result=$(check_python_version "$cmd"); then
        PYTHON_CMD="$result"
        break
    fi
done

if [ -n "$PYTHON_CMD" ]; then
    PYTHON_VERSION=$($PYTHON_CMD --version)
    echo "   找到符合要求的 Python: $PYTHON_VERSION"
else
    echo "   未找到 Python 3.10+ 版本，将使用 uv 创建虚拟环境"
    USE_UV=true
    # 检查是否安装了 uv
    if ! command -v uv &> /dev/null; then
        echo "   正在安装 uv..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.local/bin:$PATH"
        echo "   ✓ uv 安装完成"
    fi
fi
echo

# 删除旧的虚拟环境
if [ -d "venv" ]; then
    echo "2. 删除旧的虚拟环境..."
    rm -rf venv
    echo "   ✓ 已删除"
    echo
fi

# 创建新的虚拟环境
echo "3. 创建虚拟环境..."
if [ "$USE_UV" = true ]; then
    uv venv venv --python 3.10
    echo "   ✓ 虚拟环境已创建 (Python 3.10 via uv)"
else
    $PYTHON_CMD -m venv venv
    echo "   ✓ 虚拟环境已创建 (使用系统 Python)"
fi
echo

# 激活虚拟环境并安装依赖
echo "4. 安装依赖..."
source venv/bin/activate
if [ "$USE_UV" = true ]; then
    uv pip install --upgrade pip -q
    uv pip install -r requirements.txt
else
    pip install --upgrade pip -q
    pip install -r requirements.txt
fi
echo "   ✓ 依赖安装完成"
echo

# 运行测试
echo "5. 运行基础测试..."
venv/bin/python tests/test_basic.py

echo
echo "=========================================="
echo "✓ 环境设置完成！"
echo "=========================================="
echo
