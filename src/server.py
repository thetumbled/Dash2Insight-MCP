#!/usr/bin/env python3
"""Dash2Insight-MCP 主入口"""
import sys
import asyncio
from pathlib import Path
from typing import Any, Sequence

# 添加项目根目录到 Python 路径，支持直接运行
if __name__ == "__main__":
    # 获取 src 目录的父目录（项目根目录）
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, TextContent

# 根据运行方式选择导入方式
if __name__ == "__main__":
    # 直接运行时使用绝对导入
    from src.config import load_config
    from src.prometheus_client import PrometheusClient
    from src.resources import VariablesResource, MetricsResource
    from src.logger import setup_logger, get_logger
else:
    # 作为模块导入时使用相对导入
    from .config import load_config
    from .prometheus_client import PrometheusClient
    from .resources import VariablesResource, MetricsResource
    from .logger import setup_logger, get_logger


class PrometheusServer:
    """Prometheus MCP Server"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        初始化 MCP Server
        
        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        self.config = load_config(config_path)
        
        # 初始化日志
        setup_logger(
            level=self.config.logging.level,
            log_file=self.config.logging.file,
            max_bytes=self.config.logging.max_bytes,
            backup_count=self.config.logging.backup_count
        )
        self.logger = get_logger("server")
        self.logger.info("=" * 60)
        self.logger.info("Dash2Insight-MCP 启动")
        self.logger.info(f"配置文件: {config_path}")
        self.logger.info(f"Prometheus URL: {self.config.prometheus.url}")
        self.logger.info(f"日志级别: {self.config.logging.level}")
        self.logger.info("=" * 60)
        
        # 初始化 Prometheus 客户端
        self.prometheus_client = PrometheusClient(
            base_url=self.config.prometheus.url,
            username=self.config.prometheus.username,
            password=self.config.prometheus.password,
            timeout=self.config.prometheus.timeout
        )
        
        # 初始化 resources
        self.variables_resources = {}
        self.metrics_resources = {}
        
        self.logger.info(f"加载 {len(self.config.dashboards)} 个 dashboard...")
        for dashboard in self.config.dashboards:
            # 确保 dashboard 路径是绝对路径
            dashboard_path = Path(dashboard.path)
            if not dashboard_path.is_absolute():
                # 相对于配置文件所在目录
                config_dir = Path(config_path).parent
                dashboard_path = (config_dir / dashboard_path).resolve()
            
            # Variables resource
            var_resource = VariablesResource(
                dashboard_name=dashboard.name,
                dashboard_path=str(dashboard_path),
                prometheus_client=self.prometheus_client
            )
            var_uri = var_resource.get_uri()
            self.variables_resources[var_uri] = var_resource

            # Metrics resource
            metrics_resource = MetricsResource(
                dashboard_name=dashboard.name,
                dashboard_path=str(dashboard_path)
            )
            metrics_uri = metrics_resource.get_uri()
            self.metrics_resources[metrics_uri] = metrics_resource

            self.logger.info(f"  - {dashboard.name}: {dashboard_path}")
            self.logger.debug(f"    Variables URI: {var_uri}")
            self.logger.debug(f"    Metrics URI: {metrics_uri}")

        self.logger.info(f"总共加载 {len(self.variables_resources)} 个 variables resources")
        self.logger.info(f"总共加载 {len(self.metrics_resources)} 个 metrics resources")
        
        # 创建 MCP server
        self.server = Server("dash2insight-mcp")
        self._setup_handlers()
        self.logger.info("MCP Server 初始化完成")
    
    def _setup_handlers(self):
        """设置 MCP 处理器"""
        
        @self.server.list_resources()
        async def list_resources() -> list[Resource]:
            """列出所有可用的 resources"""
            self.logger.debug("收到 list_resources 请求")
            resources = []
            
            # 添加 variables resources
            for uri, resource in self.variables_resources.items():
                resources.append(Resource(
                    uri=uri,
                    name=f"{resource.dashboard_name} - Variables",
                    description=resource.get_description(),
                    mimeType=resource.get_mime_type()
                ))
            
            # 添加 metrics resources
            for uri, resource in self.metrics_resources.items():
                resources.append(Resource(
                    uri=uri,
                    name=f"{resource.dashboard_name} - Metrics",
                    description=resource.get_description(),
                    mimeType=resource.get_mime_type()
                ))
            
            self.logger.info(f"返回 {len(resources)} 个 resources")
            return resources
        
        @self.server.read_resource()
        async def read_resource(uri) -> str:
            """读取指定 resource 的内容"""
            # MCP 传入的 uri 是 AnyUrl 对象，需要转换为字符串
            uri_str = str(uri)
            self.logger.info(f"读取 resource: {uri_str}")
            self.logger.debug(f"已注册的 variables resources: {list(self.variables_resources.keys())}")
            self.logger.debug(f"已注册的 metrics resources: {list(self.metrics_resources.keys())}")

            # 查找 variables resource
            if uri_str in self.variables_resources:
                content = self.variables_resources[uri_str].get_content()
                self.logger.debug(f"返回 variables resource，大小: {len(content)} bytes")
                return content
            
            # 查找 metrics resource
            if uri_str in self.metrics_resources:
                content = self.metrics_resources[uri_str].get_content()
                self.logger.debug(f"返回 metrics resource，大小: {len(content)} bytes")
                return content
            
            self.logger.error(f"未找到 resource: {uri_str}")
            self.logger.error(f"可用的 URIs: {list(self.variables_resources.keys()) + list(self.metrics_resources.keys())}")
            raise ValueError(f"未找到 resource: {uri_str}")
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """列出所有可用的 tools"""
            return [
                Tool(
                    name="prometheus_query",
                    description="执行 Prometheus 即时查询（instant query）。支持标准 PromQL 语法，返回当前时间点或指定时间点的查询结果。",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "PromQL 查询语句，例如: up{job=\"prometheus\"} 或 rate(http_requests_total[5m])"
                            },
                            "time": {
                                "type": "string",
                                "description": "可选的查询时间点，支持 RFC3339 格式（2023-01-01T00:00:00Z）或 Unix 时间戳（1234567890）。不指定则查询当前时间。"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="prometheus_range_query",
                    description="执行 Prometheus 范围查询（range query）。在指定时间范围内按步长查询，适合绘制时间序列图表。",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "PromQL 查询语句"
                            },
                            "start": {
                                "type": "string",
                                "description": "起始时间，支持 RFC3339 格式或 Unix 时间戳"
                            },
                            "end": {
                                "type": "string",
                                "description": "结束时间，支持 RFC3339 格式或 Unix 时间戳"
                            },
                            "step": {
                                "type": "string",
                                "description": "查询步长，例如 '1m'（1分钟）、'5m'（5分钟）、'1h'（1小时），默认为 '1m'",
                                "default": "1m"
                            }
                        },
                        "required": ["query", "start", "end"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
            """执行 tool 调用"""
            self.logger.info(f"调用 tool: {name}")
            self.logger.debug(f"参数: {arguments}")
            
            if name == "prometheus_query":
                return await self._handle_prometheus_query(arguments)
            elif name == "prometheus_range_query":
                return await self._handle_prometheus_range_query(arguments)
            else:
                self.logger.error(f"未知的 tool: {name}")
                raise ValueError(f"未知的 tool: {name}")
    
    async def _handle_prometheus_query(self, arguments: dict) -> Sequence[TextContent]:
        """处理 prometheus_query tool 调用"""
        query = arguments.get("query")
        time = arguments.get("time")
        
        if not query:
            self.logger.error("query 参数缺失")
            raise ValueError("query 参数是必需的")
        
        self.logger.info(f"执行 Prometheus 查询: {query[:100]}...")
        
        try:
            # 在线程池中执行同步的 Prometheus 查询
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                lambda: self.prometheus_client.query(query, time)
            )
            
            result_count = len(result.get("data", {}).get("result", []))
            self.logger.info(f"查询成功，返回 {result_count} 条结果")
            
            import json
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False)
            )]
        except Exception as e:
            self.logger.error(f"查询失败: {e}", exc_info=True)
            return [TextContent(
                type="text",
                text=f"查询失败: {str(e)}"
            )]
    
    async def _handle_prometheus_range_query(self, arguments: dict) -> Sequence[TextContent]:
        """处理 prometheus_range_query tool 调用"""
        query = arguments.get("query")
        start = arguments.get("start")
        end = arguments.get("end")
        step = arguments.get("step", "1m")
        
        if not query or not start or not end:
            self.logger.error("query/start/end 参数缺失")
            raise ValueError("query, start, end 参数是必需的")
        
        self.logger.info(f"执行 Prometheus 范围查询: {query[:100]}... (start={start}, end={end}, step={step})")
        
        try:
            # 在线程池中执行同步的 Prometheus 查询
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.prometheus_client.range_query(query, start, end, step)
            )
            
            result_count = len(result.get("data", {}).get("result", []))
            self.logger.info(f"范围查询成功，返回 {result_count} 条时间序列")
            
            import json
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False)
            )]
        except Exception as e:
            self.logger.error(f"范围查询失败: {e}", exc_info=True)
            return [TextContent(
                type="text",
                text=f"范围查询失败: {str(e)}"
            )]
    
    async def run(self):
        """运行 MCP server"""
        self.logger.info("启动 MCP Server，等待客户端连接...")
        try:
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    self.server.create_initialization_options()
                )
        except Exception as e:
            self.logger.error(f"Server 运行错误: {e}", exc_info=True)
            raise
        finally:
            self.logger.info("MCP Server 已停止")


def main():
    """主入口函数"""
    # 获取项目根目录（src 目录的父目录）
    project_root = Path(__file__).parent.parent

    # 默认配置文件路径（相对于项目根目录）
    config_path = project_root / "config.yaml"

    # 如果提供了命令行参数，使用指定的配置文件
    if len(sys.argv) > 1:
        user_config_path = Path(sys.argv[1])
        # 如果是相对路径，相对于项目根目录解析
        if not user_config_path.is_absolute():
            config_path = project_root / user_config_path
        else:
            config_path = user_config_path

    # 转换为字符串
    config_path = str(config_path)

    try:
        # 创建并运行 server
        server = PrometheusServer(config_path)
        asyncio.run(server.run())
    except KeyboardInterrupt:
        print("\n收到中断信号，正在关闭...", file=sys.stderr)
    except Exception as e:
        print(f"启动失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
