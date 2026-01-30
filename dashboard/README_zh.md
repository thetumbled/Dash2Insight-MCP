[English](README.md) | 中文

# Dashboard 目录

此目录用于存放从 Grafana 导出的 Dashboard JSON 文件。

## 如何获取 Dashboard 文件

1. 打开 Grafana 仪表盘
2. 点击右上角的齿轮图标（设置）
3. 选择 "JSON Model"
4. 复制内容并保存为 `.json` 文件到此目录

你可以参考位于 https://github.com/apache/pulsar/tree/master/grafana/dashboards 的dashboard文件。

## 文件结构

Dashboard JSON 文件应按组件或功能进行组织。参考 [Apache Pulsar](https://github.com/apache/pulsar/tree/master/grafana/dashboards) 等项目的最佳实践，你可以按如下方式组织 dashboard 文件：

```
dashboard/
├── overview.json          # 系统概览仪表盘
├── jvm.json               # JVM 指标仪表盘
├── database.json          # 数据库指标仪表盘
├── api-gateway.json       # API 网关指标仪表盘
└── ...
```

### 命名规范

- 使用小写字母，以连字符（`-`）作为分隔符
- 根据被监控的组件或服务命名文件
- 保持名称简洁且具有描述性
- 示例：`kafka-consumer.json`、`redis-cluster.json`、`nginx-ingress.json`

## 配置说明

在 `config.yaml` 中配置 dashboard 列表：

```yaml
dashboards:
  - name: "your-dashboard"
    path: "./dashboard/your-dashboard.json"
```

> ⚠️ **注意**: Dashboard JSON 文件可能包含敏感信息（如内部 URL、集群名称等），因此不包含在 Git 仓库中。
