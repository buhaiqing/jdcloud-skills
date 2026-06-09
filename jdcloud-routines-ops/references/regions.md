# 京东云区域列表

## 支持巡检的区域

| Region ID | 中文名 | 可用区 | 说明 |
|-----------|--------|--------|------|
| `cn-north-1` | 华北 (北京) | cn-north-1a, cn-north-1b, cn-north-1c | 主数据中心 |
| `cn-south-1` | 华南 (广州) | cn-south-1a, cn-south-1b | 华南节点 |
| `cn-east-1` | 华东 (上海) | cn-east-1a, cn-east-1b | 华东节点 |
| `cn-east-2` | 华东 (宿迁) | cn-east-2a, cn-east-2b | 华东节点2 |
| `ap-southeast-1` | 东南亚 (新加坡) | ap-southeast-1a, ap-southeast-1b | 海外节点 |

## 未覆盖的API

以下服务暂未通过 jdc CLI 暴露到期信息：

- RDS MySQL / PostgreSQL
- Kubernetes Cluster
- WAF
- OSS

如需巡检这些资源，需使用 SDK 方式查询。