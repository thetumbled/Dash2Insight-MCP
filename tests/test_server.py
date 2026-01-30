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


def main():
    """主函数"""
    try:
        test_config()
        test_dashboard_parser()
        
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
