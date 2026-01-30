#!/bin/bash
# 启动 Dash2Insight-MCP
# 供 Cursor 等 MCP 客户端使用：脚本会切换到项目根目录，客户端无需配置 cwd。

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.." || exit 1

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "错误: 虚拟环境不存在" >&2
    echo "请先运行: ./setup.sh" >&2
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 检查依赖
if ! python -c "import mcp" 2>/dev/null; then
    echo "错误: 未安装 mcp 包" >&2
    echo "请运行: pip install -r requirements.txt" >&2
    exit 1
fi

# 启动 server
echo "启动 Dash2Insight-MCP..." >&2
python -m src.server "$@"
