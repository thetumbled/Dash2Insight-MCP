English | [中文](README_zh.md)

# Dash2Insight-MCP

An MCP (Model Context Protocol) server that extracts professional monitoring metrics from existing Grafana Dashboards and queries real-time data via Prometheus to assist AI in monitoring analysis and troubleshooting.

Key Features:
- Extracts key metrics from large JSON files (20000+ lines), saving AI context and focusing on important indicators
- Supports both instant and range queries for Prometheus, meeting different monitoring needs
- Supports Dashboard variable parsing for dynamic metric and option retrieval

## Requirements

- **Python**: 3.10+ (MCP SDK minimum requirement)
> ⚠️ **Note**: MCP Python SDK requires Python 3.10 or higher

### Option 1: Automated Setup (Recommended)

```bash
./setup.sh
```

This script will automatically:
- Detect available Python 3.10+ version
- Create virtual environment
- Install all dependencies
- Run basic tests

### Option 2: Manual Installation

#### 1. Check Python Version

```bash
python3 --version
# Ensure version >= 3.10
```

If version is too low, install Python 3.10+:
- macOS: `brew install python@3.10` or `brew install python@3.11`
- Linux: Use system package manager
- Windows: Download from [python.org](https://www.python.org/downloads/)

#### 2. Create Virtual Environment

```bash
# Create virtual environment with Python 3.10+
python -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate
```

#### 3. Install Dependencies

```bash
# Upgrade pip (recommended)
pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt
```


## Running the Service

### 1. Add Dashboard Files
Export dashboard JSON files from Grafana and place them in the `dashboard/` directory. Multiple dashboard files are supported.
> ⚠️ **Note**: A professional Grafana dashboard metadata is crucial for AI analysis.

How to export:
1. Open your Grafana dashboard
2. Click the gear icon (Settings) in the top right
3. Select "JSON Model"
4. Copy the content and save as `your-service-dashboard.json`

### 2. Configure Prometheus

Copy the example config file and edit:

```bash
cp config.yaml.example config.yaml
```

Then edit `config.yaml` with your Prometheus server info and dashboard list:

```yaml
prometheus:
  url: "http://your-prometheus-url:9090"
  username: "your_username"  # Optional, if authentication required
  password: "your_password"  # Optional, if authentication required
  timeout: 30

dashboards:
  - name: "pulsar-dashboard"
    path: "./dashboard/pulsar-dashboard.json"
```

> ⚠️ **Note**: `config.yaml` contains sensitive information and is ignored by `.gitignore`.

**Specify a custom config file**: You can use a config file outside the project root by:
- **Command line**: `python -m src.server -c /path/to/config.yaml` or `./scripts/run_server.sh --config /path/to/config.yaml`
- **Environment variable**: Set `DASH2INSIGHT_CONFIG=/path/to/config.yaml` (useful when the MCP client does not pass args)

### 3. Configure MCP Server

Configure the MCP Server in AI clients like Cursor or Claude Desktop, pointing to the `server.py` script.
Using Cursor as an example:
1. Open Cursor Settings
2. Find "MCP Servers" configuration
3. Add server configuration

**Option 1: Using Virtual Environment Python**

```json
{
  "mcpServers": {
    "Dash2Insight-MCP": {
      "command": "/path/to/Dash2Insight-MCP/venv/bin/python",
      "args": ["/path/to/Dash2Insight-MCP/src/server.py"],
      "cwd": "/path/to/Dash2Insight-MCP"
    }
  }
}
```
> Use absolute paths to avoid environment variable issues. \
> To use a config file outside the project root, add `"-c", "/path/to/your/config.yaml"` to `args`. \
> ⚠️ **Option 1 requires setting `cwd`** to the project root, otherwise you'll get: `ModuleNotFoundError: No module named 'src'`.


**Option 2: Using Startup Script**

The script automatically switches to the project root, no need to set `cwd` in MCP config:

```json
{
  "mcpServers": {
    "Dash2Insight-MCP": {
      "command": "/path/to/Dash2Insight-MCP/scripts/run_server.sh"
    }
  }
}
```

4. Restart Cursor

After configuration, **restart Cursor** to activate the MCP server. AI can then use prometheus_query, prometheus_range_query tools, and access dashboard variables and metrics resources.
Success screenshot:
![img.png](docs/img.png)
![img.png](docs/img2.png)

## Usage Examples

1. Generate a traffic report for the Pulsar cluster and save it as a markdown document.
2. Cluster XXX experienced a failure at XXX time, help me analyze the cause and provide troubleshooting steps.
3. Analyze the load of cluster XXX and provide optimization suggestions.

## License

Apache-2.0
