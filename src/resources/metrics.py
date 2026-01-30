"""Metrics Resource 实现"""
import json
from typing import Dict, Any
from ..dashboard_parser import DashboardParser


class MetricsResource:
    """Dashboard Metrics Resource"""
    
    def __init__(self, dashboard_name: str, dashboard_path: str):
        """
        初始化 Metrics Resource
        
        Args:
            dashboard_name: dashboard 名称
            dashboard_path: dashboard JSON 文件路径
        """
        self.dashboard_name = dashboard_name
        self.parser = DashboardParser(dashboard_path)
    
    def get_uri(self) -> str:
        """获取 resource URI"""
        return f"prometheus://dashboard/{self.dashboard_name}/metrics"
    
    def get_content(self) -> str:
        """
        获取 resource 内容
        
        Returns:
            格式化的指标信息（JSON 字符串）
        """
        metrics = self.parser.parse_metrics()
        metrics_data = [metric.to_dict() for metric in metrics]
        
        result = {
            "dashboard": self.dashboard_name,
            "dashboard_title": self.parser.get_dashboard_title(),
            "dashboard_description": self.parser.get_dashboard_description(),
            "total_metrics": len(metrics_data),
            "metrics": metrics_data
        }
        
        return json.dumps(result, indent=2, ensure_ascii=False)
    
    def get_description(self) -> str:
        """获取 resource 描述"""
        return f"Dashboard '{self.dashboard_name}' 的所有监控指标信息"
    
    def get_mime_type(self) -> str:
        """获取 MIME 类型"""
        return "application/json"
