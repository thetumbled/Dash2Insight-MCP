"""Variables Resource 实现"""
import re
from typing import Dict, Any, List
from ..prometheus_client import PrometheusClient
from ..dashboard_parser import DashboardParser, Variable
from ..logger import get_logger

logger = get_logger("resources.variables")


class VariablesResource:
    """Dashboard Variables Resource"""
    
    def __init__(self, dashboard_name: str, dashboard_path: str, 
                 prometheus_client: PrometheusClient):
        """
        初始化 Variables Resource
        
        Args:
            dashboard_name: dashboard 名称
            dashboard_path: dashboard JSON 文件路径
            prometheus_client: Prometheus 客户端
        """
        self.dashboard_name = dashboard_name
        self.parser = DashboardParser(dashboard_path)
        self.prometheus_client = prometheus_client
    
    def get_uri(self) -> str:
        """获取 resource URI"""
        return f"prometheus://dashboard/{self.dashboard_name}/variables"
    
    def get_content(self) -> str:
        """
        获取 resource 内容
        
        Returns:
            格式化的变量信息（JSON 字符串）
        """
        variables = self.parser.parse_variables()
        variables_data = []
        
        for var in variables:
            var_dict = var.to_dict()
            
            # 对于 query 类型的变量，查询 Prometheus 获取候选值
            if var.type == "query" and var.query:
                values = self._query_variable_values(var)
                var_dict["values"] = values
            
            variables_data.append(var_dict)
        
        result = {
            "dashboard": self.dashboard_name,
            "dashboard_title": self.parser.get_dashboard_title(),
            "variables": variables_data
        }
        
        import json
        return json.dumps(result, indent=2, ensure_ascii=False)

    def _unwrap_query_result(self, query: str) -> str:
        """
        去掉 VictoriaMetrics/Grafana 的 query_result(...) 包装，返回内层 PromQL。
        标准 Prometheus 不支持 query_result()，但支持内层的 sort_desc/topk 等。
        """
        q = query.strip()
        if not re.match(r'query_result\s*\(', q, re.IGNORECASE):
            return query
        start = q.index('(') + 1
        depth = 1
        i = start
        while i < len(q) and depth > 0:
            if q[i] == '(':
                depth += 1
            elif q[i] == ')':
                depth -= 1
            i += 1
        inner = q[start : i - 1].strip()
        logger.debug("query_result 已剥离，内层 PromQL: %s", inner[:80])
        return inner

    def _query_variable_values(self, variable: Variable) -> List[str]:
        """
        查询变量的候选值
        
        Args:
            variable: 变量对象
            
        Returns:
            候选值列表
        """
        query = variable.query
        if not query:
            return []
        
        try:
            # 检测是否是 label_values() 查询
            # 格式1: label_values(label_name)
            # 格式2: label_values(metric{...}, label_name)，metric 内可含逗号，用贪婪匹配取最后一个逗号分隔
            label_values_pattern = r'label_values\s*\(\s*(?:(.+),\s*)?([^,\)]+)\s*\)'
            match = re.search(label_values_pattern, query)
            
            if match:
                metric_part = match.group(1)
                label_name = match.group(2).strip()
                
                if metric_part:
                    # 格式2: label_values(metric{...}, label_name)
                    # 提取 metric 部分作为 match 参数
                    metric_part = metric_part.strip()
                    values = self.prometheus_client.query_label_values(
                        label=label_name,
                        match=metric_part
                    )
                else:
                    # 格式1: label_values(label_name)
                    values = self.prometheus_client.query_label_values(label=label_name)
                
                return values

            # 处理 VictoriaMetrics/Grafana 的 query_result(...) 包装（标准 Prometheus 不支持）
            # 去掉 query_result(...) 只保留内层 PromQL，再请求
            promql = self._unwrap_query_result(query)

            # 尝试直接执行查询
            result = self.prometheus_client.query(promql)
            data = result.get("data", {})
            result_list = data.get("result", [])

            # 提取所有不重复的值
            values = []
            for item in result_list:
                metric = item.get("metric", {})
                value_data = item.get("value", [])

                # 尝试从 metric 中提取值（先按变量名，再按常见映射如 maxmount->mountpoint）
                label_to_try = variable.name
                if label_to_try not in metric and variable.name == "maxmount":
                    label_to_try = "mountpoint"
                if label_to_try in metric:
                    val = metric[label_to_try]
                    if val and val not in values:
                        values.append(val)
                # 或取任意非 __ 开头的 label 值（单结果时常用）
                if not values and metric:
                    for k, v in metric.items():
                        if not k.startswith("__") and v and v not in values:
                            values.append(v)
                            break
                # 或者从 value 中提取
                if not values and len(value_data) >= 2:
                    val = str(value_data[1])
                    if val and val not in values:
                        values.append(val)

            return values
            
        except Exception as e:
            logger.error(f"查询变量 {variable.name} 的候选值失败: {e}", exc_info=True)
            return []
    
    def get_description(self) -> str:
        """获取 resource 描述"""
        return f"Dashboard '{self.dashboard_name}' 的变量定义和候选值"
    
    def get_mime_type(self) -> str:
        """获取 MIME 类型"""
        return "application/json"
