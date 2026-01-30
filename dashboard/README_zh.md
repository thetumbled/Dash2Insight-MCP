[English](README.md) | 中文

# Dashboard 目录

此目录用于存放从 Grafana 导出的 Dashboard JSON 文件。

## 如何获取 Dashboard 文件

1. 打开 Grafana 仪表盘
2. 点击右上角的齿轮图标（设置）
3. 选择 "JSON Model"
4. 复制内容并保存为 `.json` 文件到此目录

## 配置说明

在 `config.yaml` 中配置 dashboard 列表：

```yaml
dashboards:
  - name: "your-dashboard"
    path: "./dashboard/your-dashboard.json"
```

> ⚠️ **注意**: Dashboard JSON 文件可能包含敏感信息（如内部 URL、集群名称等），因此不包含在 Git 仓库中。
