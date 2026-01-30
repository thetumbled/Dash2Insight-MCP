"""Prometheus 客户端封装"""
import json
import time
import requests
from requests.auth import HTTPBasicAuth
from typing import List, Optional, Dict, Any
from datetime import datetime

from .logger import get_logger

logger = get_logger("prometheus_client")


class PrometheusClient:
    """Prometheus 客户端"""
    
    def __init__(self, base_url: str, username: Optional[str] = None, 
                 password: Optional[str] = None, timeout: int = 30):
        """
        初始化 Prometheus 客户端
        
        Args:
            base_url: Prometheus 服务地址
            username: 认证用户名（可选）
            password: 认证密码（可选）
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.auth = HTTPBasicAuth(username, password) if username and password else None
    
    def query(self, query: str, query_time: Optional[str] = None, retry: int = 3) -> Dict[str, Any]:
        """
        执行 Prometheus 即时查询
        
        Args:
            query: PromQL 查询语句
            query_time: 查询时间点（可选，RFC3339 或 Unix 时间戳）
            retry: 重试次数
            
        Returns:
            查询结果字典，包含 status 和 data 字段
            
        Example:
            {
                "status": "success",
                "data": {
                    "resultType": "vector",
                    "result": [
                        {
                            "metric": {"instance": "localhost:9090"},
                            "value": [1234567890, "1.0"]
                        }
                    ]
                }
            }
        """
        url = f"{self.base_url}/api/v1/query"
        payload = {"query": query}
        if query_time:
            payload["time"] = query_time
        
        for i in range(retry):
            try:
                response = requests.post(
                    url, 
                    data=payload, 
                    auth=self.auth, 
                    timeout=self.timeout
                )
                response.raise_for_status()
                result = response.json()
                
                if result.get("status") != "success":
                    error_msg = result.get("error", "Unknown error")
                    raise Exception(f"Prometheus 查询失败: {error_msg}")
                
                return result
                
            except Exception as e:
                logger.warning(f"查询失败 (尝试 {i+1}/{retry}): {e}", exc_info=i == retry - 1)
                if i == retry - 1:
                    logger.error(f"查询最终失败，query={query[:100]}")
                    raise
                time.sleep(1)
    
    def range_query(self, query: str, start: str, end: str, 
                    step: str = "1m", retry: int = 3) -> Dict[str, Any]:
        """
        执行 Prometheus 范围查询
        
        Args:
            query: PromQL 查询语句
            start: 起始时间（RFC3339 或 Unix 时间戳）
            end: 结束时间（RFC3339 或 Unix 时间戳）
            step: 查询步长，例如 "1m"、"5m"
            retry: 重试次数
            
        Returns:
            查询结果字典
            
        Example:
            {
                "status": "success",
                "data": {
                    "resultType": "matrix",
                    "result": [
                        {
                            "metric": {"instance": "localhost:9090"},
                            "values": [
                                [1234567890, "1.0"],
                                [1234567950, "1.5"]
                            ]
                        }
                    ]
                }
            }
        """
        url = f"{self.base_url}/api/v1/query_range"
        payload = {
            "query": query,
            "start": start,
            "end": end,
            "step": step
        }
        
        for i in range(retry):
            try:
                response = requests.post(
                    url,
                    data=payload,
                    auth=self.auth,
                    timeout=self.timeout
                )
                response.raise_for_status()
                result = response.json()
                
                if result.get("status") != "success":
                    error_msg = result.get("error", "Unknown error")
                    raise Exception(f"Prometheus 范围查询失败: {error_msg}")
                
                return result
                
            except Exception as e:
                logger.warning(f"范围查询失败 (尝试 {i+1}/{retry}): {e}", exc_info=i == retry - 1)
                if i == retry - 1:
                    logger.error(f"范围查询最终失败，query={query[:100]}, start={start}, end={end}")
                    raise
                time.sleep(1)
    
    def query_label_values(self, label: str, match: Optional[str] = None, 
                          retry: int = 3) -> List[str]:
        """
        查询指定 label 的所有可能值
        
        Args:
            label: label 名称
            match: 可选的匹配条件，例如 'pulsar_lb_cpu_usage{service="Pulsar"}'
            retry: 重试次数
            
        Returns:
            label 值列表
            
        Example:
            ["cluster1", "cluster2", "cluster3"]
        """
        url = f"{self.base_url}/api/v1/label/{label}/values"
        params = {}
        if match:
            params["match[]"] = match
        
        for i in range(retry):
            try:
                response = requests.get(
                    url,
                    params=params,
                    auth=self.auth,
                    timeout=self.timeout
                )
                response.raise_for_status()
                result = response.json()
                
                if result.get("status") != "success":
                    error_msg = result.get("error", "Unknown error")
                    raise Exception(f"查询 label 值失败: {error_msg}")
                
                return result.get("data", [])
                
            except Exception as e:
                logger.warning(f"查询 label 值失败 (尝试 {i+1}/{retry}), label={label}: {e}")
                if i == retry - 1:
                    # 查询失败时返回空列表，不阻断整个流程
                    logger.error(f"查询 label 值最终失败，返回空列表: label={label}, match={match}")
                    return []
                time.sleep(1)
    
    def series(self, match: str, start: Optional[str] = None, 
               end: Optional[str] = None, retry: int = 3) -> List[Dict[str, str]]:
        """
        查询时间序列
        
        Args:
            match: 匹配条件，例如 'up' 或 'up{job="prometheus"}'
            start: 起始时间（可选）
            end: 结束时间（可选）
            retry: 重试次数
            
        Returns:
            时间序列列表，每个元素是一个 metric 字典
        """
        url = f"{self.base_url}/api/v1/series"
        params = {"match[]": match}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        
        for i in range(retry):
            try:
                response = requests.get(
                    url,
                    params=params,
                    auth=self.auth,
                    timeout=self.timeout
                )
                response.raise_for_status()
                result = response.json()
                
                if result.get("status") != "success":
                    error_msg = result.get("error", "Unknown error")
                    raise Exception(f"查询时间序列失败: {error_msg}")
                
                return result.get("data", [])
                
            except Exception as e:
                logger.warning(f"查询时间序列失败 (尝试 {i+1}/{retry}), match={match}: {e}")
                if i == retry - 1:
                    logger.error(f"查询时间序列最终失败，返回空列表: match={match}")
                    return []
                time.sleep(1)
