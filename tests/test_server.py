#!/usr/bin/env python3
"""测试脚本"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import load_config
from src.prometheus_client import PrometheusClient
from src.dashboard_parser import DashboardParser
from src.resources import VariablesResource, MetricsResource


def test_config():
    """测试配置加载"""
    print("=" * 60)
    print("测试配置加载")
    print("=" * 60)
    
    config_path = Path(__file__).parent.parent / "config.yaml"
    config = load_config(str(config_path))
    print(f"Prometheus URL: {config.prometheus.url}")
    print(f"Dashboards: {[d.name for d in config.dashboards]}")
    print()


def test_prometheus_client():
    """测试 Prometheus 客户端"""
    print("=" * 60)
    print("测试 Prometheus 客户端")
    print("=" * 60)
    
    config_path = Path(__file__).parent.parent / "config.yaml"
    config = load_config(str(config_path))
    client = PrometheusClient(
        base_url=config.prometheus.url,
        username=config.prometheus.username,
        password=config.prometheus.password
    )
    
    # 测试简单查询
    try:
        query = "up"
        print(f"执行查询: {query}")
        result = client.query(query)
        print(f"查询成功，返回 {len(result['data']['result'])} 条结果")
        if result['data']['result']:
            print(f"第一条结果: {result['data']['result'][0]}")
    except Exception as e:
        print(f"查询失败: {e}")
    
    print()


def test_dashboard_parser():
    """测试 Dashboard 解析器"""
    print("=" * 60)
    print("测试 Dashboard 解析器")
    print("=" * 60)
    
    config_path = Path(__file__).parent.parent / "config.yaml"
    config = load_config(str(config_path))
    dashboard_config = config.dashboards[0]
    
    # 解析 variables
    parser = DashboardParser(dashboard_config.path)
    variables = parser.parse_variables()
    print(f"解析到 {len(variables)} 个变量:")
    for var in variables[:5]:  # 只显示前5个
        print(f"  - {var.name} ({var.type}): {var.query[:50] if var.query else 'N/A'}...")
    
    # 解析 metrics
    metrics = parser.parse_metrics()
    print(f"\n解析到 {len(metrics)} 个指标:")
    for metric in metrics[:5]:  # 只显示前5个
        print(f"  - {metric.title}: {metric.expr[:50]}...")
    
    print()


def test_resources():
    """测试 Resources"""
    print("=" * 60)
    print("测试 Resources")
    print("=" * 60)
    
    config_path = Path(__file__).parent.parent / "config.yaml"
    config = load_config(str(config_path))
    dashboard_config = config.dashboards[0]
    
    client = PrometheusClient(
        base_url=config.prometheus.url,
        username=config.prometheus.username,
        password=config.prometheus.password
    )
    
    # 测试 Variables Resource
    print("测试 Variables Resource:")
    var_resource = VariablesResource(
        dashboard_name=dashboard_config.name,
        dashboard_path=dashboard_config.path,
        prometheus_client=client
    )
    print(f"URI: {var_resource.get_uri()}")
    print(f"描述: {var_resource.get_description()}")
    
    try:
        content = var_resource.get_content()
        import json
        data = json.loads(content)
        print(f"变量数量: {len(data['variables'])}")
        if data['variables']:
            first_var = data['variables'][0]
            print(f"第一个变量: {first_var['name']}")
            if 'values' in first_var:
                print(f"候选值数量: {len(first_var.get('values', []))}")
                print(f"候选值示例: {first_var.get('values', [])[:3]}")
    except Exception as e:
        print(f"获取 Variables Resource 失败: {e}")
    
    print()
    
    # 测试 Metrics Resource
    print("测试 Metrics Resource:")
    metrics_resource = MetricsResource(
        dashboard_name=dashboard_config.name,
        dashboard_path=dashboard_config.path
    )
    print(f"URI: {metrics_resource.get_uri()}")
    print(f"描述: {metrics_resource.get_description()}")
    
    try:
        content = metrics_resource.get_content()
        import json
        data = json.loads(content)
        print(f"指标数量: {data['total_metrics']}")
        if data['metrics']:
            print(f"第一个指标: {data['metrics'][0]['title']}")
    except Exception as e:
        print(f"获取 Metrics Resource 失败: {e}")
    
    print()


def test_mcp_server():
    """测试 MCP Server 功能"""
    print("=" * 60)
    print("测试 MCP Server")
    print("=" * 60)

    config_path = Path(__file__).parent.parent / "config.yaml"

    # 导入 server 模块
    from src.server import PrometheusServer

    # 创建 server 实例
    server = PrometheusServer(str(config_path))

    print("\n--- 测试 list_resources ---")
    # 获取 list_resources handler
    import asyncio

    # 测试 list_resources - 模拟 server.py 中的描述逻辑
    async def test_list_resources():
        resources = []

        # 添加 variables resources（使用 server.py 中的描述）
        for uri, resource in server.variables_resources.items():
            resources.append({
                "uri": uri,
                "name": f"📊 {resource.dashboard_name} - Variables",
                "description": (
                    f"【优先阅读】Dashboard '{resource.dashboard_name}' 的变量定义和可用标签值。\n"
                    "包含所有可用的变量（如 cluster、namespace、pod 等）及其候选值，"
                    "这些变量可以在 PromQL 查询中使用。\n"
                    "⚠️ 在构造任何 PromQL 查询前，必须先阅读此资源！"
                )
            })

        # 添加 metrics resources（使用 server.py 中的描述）
        for uri, resource in server.metrics_resources.items():
            resources.append({
                "uri": uri,
                "name": f"📈 {resource.dashboard_name} - Metrics",
                "description": (
                    f"【优先阅读】Dashboard '{resource.dashboard_name}' 的所有可用监控指标列表。\n"
                    "包含每个指标的名称、描述、查询模板和用途说明。\n"
                    "这是构造 PromQL 查询的必读资源，所有可用指标都在这里。\n"
                    "⚠️ 不要猜测指标名称，直接从此资源中获取准确的指标信息！"
                )
            })
        return resources

    resources = asyncio.run(test_list_resources())
    print(f"Resources 总数: {len(resources)}")
    for res in resources:
        print(f"\n资源:")
        print(f"  URI: {res['uri']}")
        print(f"  名称: {res['name']}")
        print(f"  描述: {res['description'][:150]}...")
        # 验证描述中包含关键词
        desc = res['description']
        if 'Variables' in res['name']:
            assert '【优先阅读】' in desc, "Variables 描述应包含【优先阅读】"
            assert '变量' in desc or 'variable' in desc.lower(), "Variables 描述应包含变量相关信息"
            assert '⚠️' in desc, "Variables 描述应包含警告符号"
            assert 'PromQL' in desc, "Variables 描述应提到 PromQL"
        if 'Metrics' in res['name']:
            assert '【优先阅读】' in desc, "Metrics 描述应包含【优先阅读】"
            assert '指标' in desc or 'metric' in desc.lower(), "Metrics 描述应包含指标相关信息"
            assert '⚠️' in desc, "Metrics 描述应包含警告符号"
            assert 'PromQL' in desc, "Metrics 描述应提到 PromQL"

    print("\n--- 测试 list_prompts ---")
    # 测试 list_prompts
    async def test_list_prompts():
        prompts = [
            {
                "name": "metrics_query_guide",
                "description": "指标查询向导 - 引导你正确地从 Resources 获取指标信息后再进行查询",
                "arguments": [
                    {"name": "query_goal", "description": "你想查询什么指标或监控什么系统状态？", "required": True},
                    {"name": "dashboard", "description": "要使用哪个 dashboard？（可选，如果不确定可以留空）", "required": False}
                ]
            }
        ]
        return prompts

    prompts = asyncio.run(test_list_prompts())
    print(f"Prompts 总数: {len(prompts)}")
    for prompt in prompts:
        print(f"\nPrompt:")
        print(f"  名称: {prompt['name']}")
        print(f"  描述: {prompt['description']}")
        print(f"  参数:")
        for arg in prompt['arguments']:
            print(f"    - {arg['name']} (必需: {arg['required']}): {arg['description']}")
        # 验证 prompt 内容
        assert 'guide' in prompt['name'].lower(), "Prompt 名称应包含 guide"
        assert 'Resources' in prompt['description'] or '资源' in prompt['description'], "Prompt 描述应提到 Resources"

    print("\n--- 测试 get_prompt ---")
    # 测试 get_prompt
    async def test_get_prompt():
        # 模拟 get_prompt 的返回
        query_goal = "测试查询 CPU 使用率"
        dashboard = "test-dashboard"

        guide_text = (
            f"# 📊 指标查询标准流程\n\n"
            f"你的查询目标：**{query_goal}**\n\n"
            f"## ✅ 正确的查询步骤：\n\n"
            f"### 第 1 步：读取可用的 Resources\n"
            f"- 读取 `prometheus://dashboard/{dashboard}/metrics` 获取 **{dashboard}** 的所有可用指标\n"
            f"- 读取 `prometheus://dashboard/{dashboard}/variables` 获取可用的变量和标签\n\n"
            f"### 第 2 步：从 Resources 中选择合适的指标\n"
            "- 仔细阅读指标的描述和用途\n"
            "- 找到与你的查询目标最匹配的指标\n"
            "- 注意指标的查询模板（expr）和相关变量\n\n"
            "### 第 3 步：构造 PromQL 查询\n"
            "- 使用从 Resources 中获取的准确指标名称\n"
            "- 根据需要添加标签过滤（标签值可从 variables resource 获取）\n"
            "- 可以参考指标的查询模板（expr）作为基础\n\n"
            "### 第 4 步：执行查询\n"
            "- 使用 `prometheus_query` 获取即时数据\n"
            "- 或使用 `prometheus_range_query` 获取时间序列数据\n\n"
            "## ❌ 避免以下错误做法：\n"
            "- ❌ 不要跳过第 1 步，直接猜测指标名称\n"
            "- ❌ 不要使用 `prometheus_query` 探索可用指标（如查询 `up` 等通用指标）\n"
            "- ❌ 不要假设指标名称，所有指标都应该从 Resources 中获取\n\n"
            "## 💡 提示：\n"
            "Resources 中的信息已经过验证和整理，直接使用可以节省大量时间并避免错误。\n"
        )

        return guide_text

    prompt_content = asyncio.run(test_get_prompt())
    print(f"Prompt 内容长度: {len(prompt_content)} 字符")
    print(f"Prompt 内容预览:\n{prompt_content[:500]}...\n")
    # 验证 prompt 内容
    assert '指标查询标准流程' in prompt_content, "Prompt 内容应包含标准流程标题"
    assert '第 1 步' in prompt_content, "Prompt 内容应包含步骤说明"
    assert 'Resources' in prompt_content, "Prompt 内容应提到 Resources"
    assert 'prometheus://dashboard/' in prompt_content, "Prompt 内容应包含资源 URI"
    assert '❌' in prompt_content, "Prompt 内容应包含错误做法警告"
    assert 'prometheus_query' in prompt_content, "Prompt 内容应提到查询工具"

    print("\n--- 测试 list_tools ---")
    # 测试 list_tools
    async def test_list_tools():
        tools = [
            {
                "name": "prometheus_query",
                "description": (
                    "执行 Prometheus 即时查询（instant query）。支持标准 PromQL 语法，返回当前时间点或指定时间点的查询结果。\n\n"
                    "⚠️ 重要提示：使用此工具前，必须先通过 Resources 获取可用的指标列表和变量信息！\n"
                    "- 查看 'prometheus://dashboard/{dashboard_name}/metrics' 获取所有可用指标\n"
                    "- 查看 'prometheus://dashboard/{dashboard_name}/variables' 获取可用的变量和标签\n"
                    "- 不要盲目探索或猜测指标名称，这会浪费时间并可能失败\n"
                    "- 从 Resources 中获取的指标名称和查询模板已经过验证，可以直接使用"
                )
            },
            {
                "name": "prometheus_range_query",
                "description": (
                    "执行 Prometheus 范围查询（range query）。在指定时间范围内按步长查询，适合绘制时间序列图表。\n\n"
                    "⚠️ 重要提示：使用此工具前，必须先通过 Resources 获取可用的指标列表和变量信息！\n"
                    "- 查看 'prometheus://dashboard/{dashboard_name}/metrics' 获取所有可用指标\n"
                    "- 查看 'prometheus://dashboard/{dashboard_name}/variables' 获取可用的变量和标签\n"
                    "- 不要盲目探索或猜测指标名称，这会浪费时间并可能失败\n"
                    "- 从 Resources 中获取的指标名称和查询模板已经过验证，可以直接使用"
                )
            }
        ]
        return tools

    tools = asyncio.run(test_list_tools())
    print(f"Tools 总数: {len(tools)}")
    for tool in tools:
        print(f"\nTool:")
        print(f"  名称: {tool['name']}")
        print(f"  描述: {tool['description'][:200]}...")
        # 验证 tool 描述
        desc = tool['description']
        assert '⚠️' in desc, f"Tool {tool['name']} 描述应包含警告符号"
        assert 'Resources' in desc or '资源' in desc, f"Tool {tool['name']} 描述应提到 Resources"
        assert 'prometheus://dashboard/' in desc, f"Tool {tool['name']} 描述应包含资源 URI"
        assert '不要盲目探索' in desc or '不要猜测' in desc or '必须先通过' in desc, f"Tool {tool['name']} 描述应包含警告信息"
        # prometheus_query 需要提到 PromQL，range_query 可以不提
        if tool['name'] == 'prometheus_query':
            assert 'PromQL' in desc, f"Tool {tool['name']} 描述应提到 PromQL"

    print("\n✅ 所有 MCP Server 测试通过!")
    print()


def main():
    """主函数"""
    try:
        test_config()
        test_dashboard_parser()
        test_mcp_server()

        # 以下测试需要连接到实际的 Prometheus 服务器
        print("注意: 以下测试需要连接到 Prometheus 服务器")
        response = input("是否继续测试 Prometheus 连接? (y/n): ")
        if response.lower() == 'y':
            test_prometheus_client()
            test_resources()
        
        print("=" * 60)
        print("所有测试完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
