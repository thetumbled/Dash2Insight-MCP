#!/usr/bin/env python3
"""基础测试脚本（不需要 Prometheus 连接）"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import load_config
from src.dashboard_parser import DashboardParser
from src.resources import MetricsResource


def main():
    """主函数"""
    print("=" * 60)
    print("Dash2Insight-MCP - 基础功能测试")
    print("=" * 60)
    print()
    
    # 测试配置加载
    print("1. 测试配置加载...")
    try:
        # 配置文件在项目根目录
        config_path = Path(__file__).parent.parent / "config.yaml"
        config = load_config(str(config_path))
        print(f"   ✓ Prometheus URL: {config.prometheus.url}")
        print(f"   ✓ Dashboards: {[d.name for d in config.dashboards]}")
    except Exception as e:
        print(f"   ✗ 配置加载失败: {e}")
        return
    
    print()
    
    # 测试 Dashboard 解析
    print("2. 测试 Dashboard 解析...")
    try:
        dashboard_config = config.dashboards[0]
        parser = DashboardParser(dashboard_config.path)
        
        variables = parser.parse_variables()
        print(f"   ✓ 解析到 {len(variables)} 个变量")
        
        metrics = parser.parse_metrics()
        print(f"   ✓ 解析到 {len(metrics)} 个指标")
        
        # 显示前3个变量
        print(f"\n   变量示例:")
        for var in variables[:3]:
            print(f"     - {var.name} ({var.type})")
        
        # 显示前3个指标
        print(f"\n   指标示例:")
        for metric in metrics[:3]:
            print(f"     - {metric.title}")
            print(f"       expr: {metric.expr[:60]}...")
        
    except Exception as e:
        print(f"   ✗ Dashboard 解析失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print()
    
    # 测试 Metrics Resource
    print("3. 测试 Metrics Resource...")
    try:
        metrics_resource = MetricsResource(
            dashboard_name=dashboard_config.name,
            dashboard_path=dashboard_config.path
        )
        print(f"   ✓ URI: {metrics_resource.get_uri()}")
        
        content = metrics_resource.get_content()
        import json
        data = json.loads(content)
        print(f"   ✓ 成功生成 resource 内容")
        print(f"   ✓ 指标总数: {data['total_metrics']}")
        
    except Exception as e:
        print(f"   ✗ Metrics Resource 失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print()
    print("=" * 60)
    print("✓ 所有基础功能测试通过!")
    print("=" * 60)
    print()
    print("提示: 要测试 Prometheus 连接和 Variables Resource，")
    print("      请确保 config.yaml 中的 Prometheus URL 可访问，")
    print("      然后运行: python3 tests/test_server.py")


if __name__ == "__main__":
    main()
