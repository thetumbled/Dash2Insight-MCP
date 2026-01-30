English | [中文](DESIGN_zh.md)

# Dash2Insight-MCP Design Document

## 1. Overall Architecture

```
dash2insight-mcp/
├── src/
│   ├── server.py              # MCP server main entry
│   ├── config.py              # Configuration loading module
│   ├── prometheus_client.py   # Prometheus client wrapper
│   ├── dashboard_parser.py    # Dashboard parser
│   └── resources/
│       ├── variables.py       # Variables resource implementation
│       └── metrics.py         # Metrics resource implementation
├── config.yaml                # Configuration file
├── requirements.txt           # Python dependencies
└── CHANGELOG.md              # Change log
```

## 2. MCP Server Capabilities

### 2.1 Tools

#### prometheus_query
- **Function**: Execute Prometheus queries
- **Parameters**:
  - `query`: PromQL query statement (required)
  - `time`: Query time point (optional, ISO 8601 format)
  - `timeout`: Timeout duration (optional, default 30s)
- **Returns**: Query results in JSON format

### 2.2 Resources

#### dashboard_variables
- **URI Format**: `prometheus://dashboard/{dashboard_name}/variables`
- **Function**: Provides dashboard variable definitions and candidate values
- **Response Data**:
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
- **URI Format**: `prometheus://dashboard/{dashboard_name}/metrics`
- **Function**: Provides all metric information contained in the dashboard
- **Response Data**:
  ```json
  {
    "dashboard": "pulsar-dashboard",
    "metrics": [
      {
        "title": "Message In",
        "description": "Pulsar message inflow rate",
        "expr": "sum(pulsar_rate_in{cluster=~\"$cluster\"}) by (instance)",
        "panel_id": 4,
        "type": "graph"
      }
    ]
  }
  ```

## 3. Core Module Design

### 3.1 Configuration Module (config.py)
```yaml
# config.yaml format
prometheus:
  url: "http://localhost:9090"
  timeout: 30

dashboards:
  - name: "pulsar-dashboard"
    path: "./dashboard/pulsar-dashboard.json"
```

**Responsibilities**:
- Load and validate configuration files
- Provide configuration access interface

### 3.2 Prometheus Client (prometheus_client.py)
**Responsibilities**:
- Wrap Prometheus HTTP API calls
- Execute PromQL queries
- Execute label_values queries (for getting variable candidates)
- Handle errors and timeouts

**Main Methods**:
- `query(promql: str, time: Optional[str]) -> dict`
- `query_label_values(metric: str, label: str, match: Optional[str]) -> List[str]`

### 3.3 Dashboard Parser (dashboard_parser.py)
**Responsibilities**:
- Parse Grafana dashboard JSON files
- Extract variable definitions (from `templating.list`)
- Extract metric information from panels (title, expr, description)

**Main Methods**:
- `parse_variables(dashboard_json: dict) -> List[Variable]`
- `parse_metrics(dashboard_json: dict) -> List[Metric]`
- `extract_panels_recursive(panels: list) -> List[Panel]` # Handle nested collapsed panels

### 3.4 Resources Implementation

#### variables.py
**Responsibilities**:
- Provide dashboard variables resource
- Query Prometheus in real-time to get variable candidates
- Cache query results (optional)

**Workflow**:
1. Parse variable definitions from dashboard JSON
2. For type="query" variables, execute their query statements to get candidates
3. Format and return data to AI

#### metrics.py
**Responsibilities**:
- Provide dashboard metrics resource
- Recursively traverse all panels (including collapsed panels)
- Extract key information: title, description, expr, type

**Data Cleaning**:
- Filter out panels without targets
- Extract all expr from targets
- Merge panel title and description

## 4. Data Flow

### 4.1 Tool Call Flow
```
AI Client -> MCP Server -> prometheus_query tool
                          -> PrometheusClient.query()
                          -> Prometheus API
                          -> Return results to AI
```

### 4.2 Resource Access Flow
```
AI Client -> MCP Server -> list_resources()
                          -> Return all dashboard resources

AI Client -> MCP Server -> read_resource(uri)
                          -> DashboardParser.parse_variables()
                          -> PrometheusClient.query_label_values()
                          -> Return variables and candidates

AI Client -> MCP Server -> read_resource(uri)
                          -> DashboardParser.parse_metrics()
                          -> Return metrics list
```

## 5. Key Design Decisions

### 5.1 Why separate variables and metrics into two resources?
- **Reduce context consumption**: AI can fetch on-demand, no loading when not needed
- **Improve query efficiency**: variables require real-time Prometheus queries, metrics only need JSON parsing

### 5.2 How to handle large dashboards?
- **Lazy loading**: Only parse when resource is accessed
- **Key information extraction**: Only return title, description, expr, ignore style configurations
- **Recursive traversal**: Correctly handle collapsed panels

### 5.3 Variable Candidate Retrieval Strategy
- **Real-time queries**: Call Prometheus API to get latest label values
- **Error handling**: If query fails, return empty array without blocking the entire resource
- **Variable dependencies**: Do not handle dependencies between variables (e.g., $cluster depends on $datasource), simplifying implementation

## 6. Dependencies

- `mcp`: MCP Python SDK
- `httpx`: HTTP client (async support)
- `pyyaml`: YAML configuration file parsing
- `pydantic`: Data validation

## 7. Usage Scenario Examples

### Scenario 1: AI Queries Metrics for Specified Cluster
1. AI reads `dashboard_variables` resource, learns cluster has ["CN_PULSAR_TEST", "US_PULSAR_TEST"]
2. User asks: "Query the message inflow rate for the China Pulsar test cluster"
3. AI matches "CN_PULSAR_TEST"
4. AI reads `dashboard_metrics` resource, finds the expr for "Message In" metric
5. AI calls `prometheus_query` tool, replaces $cluster with "CN_PULSAR_TEST"

### Scenario 2: AI Lists Available Monitoring Metrics
1. AI reads `dashboard_metrics` resource
2. Displays all available metric titles and descriptions to user
3. User selects metrics of interest
4. AI uses corresponding expr to query Prometheus
