English | [中文](README_zh.md)

# Dashboard Directory

This directory is for storing Dashboard JSON files exported from Grafana.

## How to Get Dashboard Files

1. Open your Grafana dashboard
2. Click the gear icon (Settings) in the top right
3. Select "JSON Model"
4. Copy the content and save as a `.json` file in this directory

## Configuration

Configure the dashboard list in `config.yaml`:

```yaml
dashboards:
  - name: "your-dashboard"
    path: "./dashboard/your-dashboard.json"
```

> ⚠️ **Note**: Dashboard JSON files may contain sensitive information (such as internal URLs, cluster names, etc.) and are not included in the Git repository.
