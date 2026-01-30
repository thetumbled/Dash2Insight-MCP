"""Dashboard 解析器"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class Variable:
    """Dashboard 变量"""
    name: str
    label: Optional[str]
    type: str  # query, custom, interval, datasource, etc.
    query: Optional[str] = None  # PromQL 查询语句
    current_value: Optional[str] = None
    options: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "label": self.label or self.name,
            "type": self.type,
            "query": self.query,
            "current_value": self.current_value,
        }


@dataclass
class Metric:
    """Dashboard 指标"""
    title: str
    description: Optional[str]
    expr: str  # PromQL 表达式
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典（精简版，节省 AI token 消耗）
        
        只保留对 AI 分析有用的字段：
        - title: 指标名称
        - description: 指标描述
        - expr: PromQL 表达式
        """
        result = {
            "title": self.title,
            "expr": self.expr,
        }
        # 只在有 description 时才添加，避免空字符串占用 token
        if self.description:
            result["description"] = self.description
        return result


class DashboardParser:
    """Dashboard 解析器"""
    
    def __init__(self, dashboard_path: str):
        """
        初始化解析器
        
        Args:
            dashboard_path: dashboard JSON 文件路径
        """
        self.dashboard_path = Path(dashboard_path)
        if not self.dashboard_path.exists():
            raise FileNotFoundError(f"Dashboard 文件不存在: {dashboard_path}")
        
        with open(self.dashboard_path, 'r', encoding='utf-8') as f:
            self.dashboard_json = json.load(f)
    
    def parse_variables(self) -> List[Variable]:
        """
        解析 dashboard 中的变量定义
        
        Returns:
            变量列表
        """
        variables = []
        templating = self.dashboard_json.get("templating", {})
        variable_list = templating.get("list", [])
        
        for var in variable_list:
            name = var.get("name")
            if not name:
                continue
            
            var_type = var.get("type", "")
            label = var.get("label")
            query = var.get("query")
            
            # 获取当前值
            current = var.get("current", {})
            current_value = None
            if isinstance(current, dict):
                current_value = current.get("value") or current.get("text")
            
            variable = Variable(
                name=name,
                label=label,
                type=var_type,
                query=query,
                current_value=current_value,
            )
            variables.append(variable)
        
        return variables
    
    def parse_metrics(self) -> List[Metric]:
        """
        解析 dashboard 中的指标信息
        
        Returns:
            指标列表
        """
        metrics = []
        panels = self.dashboard_json.get("panels", [])
        
        # 递归提取所有 panels（包括 collapsed 的）
        all_panels = self._extract_panels_recursive(panels)
        
        for panel in all_panels:
            panel_metrics = self._extract_metrics_from_panel(panel)
            metrics.extend(panel_metrics)
        
        return metrics
    
    def _extract_panels_recursive(self, panels: List[Dict]) -> List[Dict]:
        """
        递归提取所有 panels，包括 collapsed panels 中的嵌套 panels
        
        Args:
            panels: panels 列表
            
        Returns:
            扁平化的 panels 列表
        """
        result = []
        
        for panel in panels:
            # 如果是 row 类型且 collapsed，需要提取其中的 panels
            if panel.get("type") == "row" and panel.get("collapsed"):
                nested_panels = panel.get("panels", [])
                # 递归处理嵌套的 panels
                result.extend(self._extract_panels_recursive(nested_panels))
            else:
                result.append(panel)
        
        return result
    
    def _extract_metrics_from_panel(self, panel: Dict) -> List[Metric]:
        """
        从单个 panel 中提取指标信息
        
        Args:
            panel: panel 字典
            
        Returns:
            指标列表
        """
        metrics = []
        
        # 跳过没有 targets 的 panel
        targets = panel.get("targets", [])
        if not targets:
            return metrics
        
        title = panel.get("title", "Untitled")
        description = panel.get("description")
        
        # 提取所有 targets 中的 expr
        for idx, target in enumerate(targets):
            expr = target.get("expr")
            if not expr:
                continue
            
            # 如果有多个 target，在 title 后面加上编号
            metric_title = title
            if len(targets) > 1:
                ref_id = target.get("refId", str(idx))
                metric_title = f"{title} [{ref_id}]"
            
            metric = Metric(
                title=metric_title,
                description=description,
                expr=expr,
            )
            metrics.append(metric)
        
        return metrics
    
    def get_dashboard_title(self) -> str:
        """获取 dashboard 标题"""
        return self.dashboard_json.get("title", "Unknown Dashboard")
    
    def get_dashboard_description(self) -> Optional[str]:
        """获取 dashboard 描述"""
        return self.dashboard_json.get("description")
