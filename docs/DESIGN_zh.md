[English](DESIGN.md) | 中文

# Dash2Insight-MCP 设计方案

## 1. 整体架构

```
dash2insight-mcp/
├── src/
│   ├── server.py              # MCP server 主入口
│   ├── config.py              # 配置加载模块
│   ├── prometheus_client.py   # Prometheus 客户端封装
│   ├── dashboard_parser.py    # Dashboard 解析器
│   └── resources/
│       ├── variables.py       # Variables resource 实现
│       └── metrics.py         # Metrics resource 实现
├── config.yaml                # 配置文件
├── requirements.txt           # Python 依赖
└── CHANGELOG.md              # 变更记录
```

## 2. MCP Server 提供的能力

### 2.1 Tools

#### prometheus_query
- **功能**：执行 Prometheus 查询
- **入参**：
  - `query`: PromQL 查询语句（必填）
  - `time`: 查询时间点（可选，ISO 8601 格式）
  - `timeout`: 超时时间（可选，默认 30s）
- **返回**：查询结果的 JSON 数据

### 2.2 Resources

#### dashboard_variables
- **URI 格式**：`prometheus://dashboard/{dashboard_name}/variables`
- **功能**：提供 dashboard 的变量定义和候选值
- **返回数据**：
  ```json
  {
    "dashboard": "pulsar-dashboard",
    "variables": [
      {
        "name": "cluster",
        "label": "cluster",
        "type": "query",
        "query": "label_values(...)",
        "values": ["CN_PULSAR_TEST", "US_PULSAR_TEST", ...]
      }
    ]
  }
  ```

#### dashboard_metrics
- **URI 格式**：`prometheus://dashboard/{dashboard_name}/metrics`
- **功能**：提供 dashboard 包含的所有指标信息
- **返回数据**：
  ```json
  {
    "dashboard": "pulsar-dashboard",
    "metrics": [
      {
        "title": "Message In",
        "description": "Pulsar 消息流入速率",
        "expr": "sum(pulsar_rate_in{cluster=~\"$cluster\"}) by (instance)",
        "panel_id": 4,
        "type": "graph"
      }
    ]
  }
  ```

## 3. 核心模块设计

### 3.1 配置模块 (config.py)
```yaml
# config.yaml 格式
prometheus:
  url: "http://localhost:9090"
  timeout: 30

dashboards:
  - name: "pulsar-dashboard"
    path: "./dashboard/pulsar-dashboard.json"
```

**职责**：
- 加载和验证配置文件
- 提供配置访问接口

### 3.2 Prometheus 客户端 (prometheus_client.py)
**职责**：
- 封装 Prometheus HTTP API 调用
- 执行 PromQL 查询
- 执行 label_values 查询（用于获取变量候选值）
- 处理错误和超时

**主要方法**：
- `query(promql: str, time: Optional[str]) -> dict`
- `query_label_values(metric: str, label: str, match: Optional[str]) -> List[str]`

### 3.3 Dashboard 解析器 (dashboard_parser.py)
**职责**：
- 解析 Grafana dashboard JSON 文件
- 提取 variables 定义（从 `templating.list`）
- 提取 panels 中的指标信息（title、expr、description）

**主要方法**：
- `parse_variables(dashboard_json: dict) -> List[Variable]`
- `parse_metrics(dashboard_json: dict) -> List[Metric]`
- `extract_panels_recursive(panels: list) -> List[Panel]` # 处理嵌套的 collapsed panels

### 3.4 Resources 实现

#### variables.py
**职责**：
- 提供 dashboard variables resource
- 实时查询 Prometheus 获取 variable 的候选值
- 缓存查询结果（可选）

**工作流程**：
1. 从 dashboard JSON 解析 variables 定义
2. 对于 type="query" 的 variable，执行其 query 语句获取候选值
3. 格式化返回给 AI 的数据

#### metrics.py
**职责**：
- 提供 dashboard metrics resource
- 递归遍历所有 panels（包括 collapsed panels）
- 提取关键信息：title、description、expr、type

**数据清洗**：
- 过滤掉没有 targets 的 panel
- 提取所有 targets 中的 expr
- 合并 panel 的 title 和 description

## 4. 数据流

### 4.1 Tool 调用流程
```
AI Client -> MCP Server -> prometheus_query tool
                          -> PrometheusClient.query()
                          -> Prometheus API
                          -> 返回结果给 AI
```

### 4.2 Resource 访问流程
```
AI Client -> MCP Server -> list_resources()
                          -> 返回所有 dashboard resources

AI Client -> MCP Server -> read_resource(uri)
                          -> DashboardParser.parse_variables()
                          -> PrometheusClient.query_label_values()
                          -> 返回变量及候选值

AI Client -> MCP Server -> read_resource(uri)
                          -> DashboardParser.parse_metrics()
                          -> 返回指标列表
```

## 5. 关键设计决策

### 5.1 为什么分离 variables 和 metrics 为两个 resource？
- **降低 context 消耗**：AI 可以按需获取，不需要时不加载
- **提高查询效率**：variables 需要实时查询 Prometheus，metrics 只需解析 JSON

### 5.2 如何处理大型 dashboard？
- **懒加载**：只在 resource 被访问时才解析
- **关键信息提取**：只返回 title、description、expr，忽略样式配置
- **递归遍历**：正确处理 collapsed panels

### 5.3 变量候选值的获取策略
- **实时查询**：调用 Prometheus API 获取最新的 label values
- **错误处理**：如果查询失败，返回空数组但不阻断整个 resource
- **变量依赖**：不处理变量间的依赖关系（如 $cluster 依赖 $datasource），简化实现

## 6. 依赖项

- `mcp`: MCP Python SDK
- `httpx`: HTTP 客户端（异步支持）
- `pyyaml`: YAML 配置文件解析
- `pydantic`: 数据验证

## 7. 使用场景示例

### 场景 1：AI 查询指定集群的指标
1. AI 读取 `dashboard_variables` resource，获知 cluster 有 ["CN_PULSAR_TEST", "US_PULSAR_TEST"]
2. 用户问："查询中国区pulsar test集群的消息流入速率"
3. AI 匹配到 "CN_PULSAR_TEST"
4. AI 读取 `dashboard_metrics` resource，找到 "Message In" 指标的 expr
5. AI 调用 `prometheus_query` tool，替换 $cluster 为 "CN_PULSAR_TEST"

### 场景 2：AI 列举可用的监控指标
1. AI 读取 `dashboard_metrics` resource
2. 向用户展示所有可用的指标 title 和 description
3. 用户选择感兴趣的指标
4. AI 使用对应的 expr 查询 Prometheus
