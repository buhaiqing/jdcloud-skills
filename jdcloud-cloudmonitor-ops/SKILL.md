---
name: jdcloud-cloudmonitor-ops
description: >-
  Use when you need to query monitoring metrics, create or manage alarm rules,
  view alarm history, or configure custom monitoring on JD Cloud resources.
  User mentions CloudMonitor, 云监控, monitoring, 告警, or metric-related tasks.
license: MIT
compatibility: >-
  Official JD Cloud SDK (Python 3.10+), valid API credentials, network access
  to JD Cloud endpoints, and official JD Cloud CLI (jdc) for this product.
metadata:
  author: jdcloud
  version: "1.1.0"
  last_updated: "2026-05-03"
  runtime: Harness AI Agent
  api_profile: "monitor v1 - https://docs.jdcloud.com/cn/monitoring/api/overview"
  cli_applicability: dual-path
  cli_support_evidence: >-
    Official jdc supports monitor product. Verified via `jdc monitor --help`
    and official CLI documentation at https://github.com/jdcloud-api/jdcloud-cli
  environment:
    - JDC_ACCESS_KEY
    - JDC_SECRET_KEY
    - JDC_REGION
---

> This skill follows the [Agent Skill OpenSpec](https://agentskills.io/specification).

# 京东云云监控(CloudMonitor)运维 Skill

## Overview

京东云云监控(CloudMonitor)是对用户名下云资源进行监控和报警的服务，支持40余种云产品的监控。本 Skill 是 **运维 Runbook**：明确的触发范围、凭证规则、前置检查、**双路径执行**（官方 SDK/API 和官方 `jdc` CLI）、响应验证和失败恢复。

### CLI applicability (repository policy)

- **`cli_applicability: dual-path`:** 官方 `jdc` 支持云监控产品。本 Skill **必须** 提供 `references/cli-usage.md` 和 `references/api-sdk-usage.md`，并在 **每个** 执行流程中记录 SDK/API 和 `jdc` 两种路径。

**路径偏好提示**: 无 Python 运行时 → 使用 `jdc` CLI；批量操作/集成测试 → 使用 SDK。

## Changelog

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| 1.1.0 | 2026-05-03 | 添加 SDK/API 双路径执行流程、完善 frontmatter、新增 api-sdk-usage.md |
| 1.0.0 | 2026-04-28 | 初始版本，包含云监控核心功能、告警配置和运维最佳实践 |

## 触发范围（Agent 可读）

### 应使用本 Skill 的场景
- 用户提及"云监控"、"CloudMonitor"、"监控"、"告警"等关键词
- 任务涉及监控数据查询、告警规则 CRUD、告警历史查看、自定义监控上报
- 任务关键词：describe-metric-data、create-alarm、alarm、metric、dashboard、put-metric-data
- 用户要求对云资源监控指标进行查询、配置告警、或分析告警历史

### 不应使用本 Skill 的场景
- 任务纯粹是云主机(VM)的创建/删除/启停 → 委派给 `jdcloud-vm-ops`
- 任务纯粹是云数据库(RDS)的管理 → 委派给 `jdcloud-rds-ops`
- 任务纯粹是负载均衡(LB)的配置 → 委派给 `jdcloud-lb-ops`
- 任务涉及账单/账户管理 → 委派给 `jdcloud-billing-ops`

### 委派规则
- 若用户需要先确认某资源（如 VM）的监控数据，先用本 Skill 查询，再根据结果建议使用对应的资源管理 Skill
- 若请求涉及多个独立云产品的监控，分别用本 Skill 对每个产品独立查询

## 变量约定（Agent 可读）

本 Skill 使用结构化占位符，防止 prompt 注入和解析歧义：

| 占位符 | 含义 | Agent 行为 |
|--------|------|-----------|
| `{{env.JDC_ACCESS_KEY}}` | Agent 运行时环境变量 | 绝不向用户索取；未设置则失败 |
| `{{env.JDC_SECRET_KEY}}` | Agent 运行时环境变量 | 绝不向用户索取；未设置则失败 |
| `{{env.JDC_REGION}}` | Agent 运行时环境变量 | 默认 `cn-north-1`，可被用户覆盖 |
| `{{user.region}}` | 须向用户收集 | 询问一次，缓存复用 |
| `{{user.resource_id}}` | 须向用户收集 | 询问一次，缓存复用 |
| `{{user.alarm_id}}` | 须向用户收集 | 询问一次，缓存复用 |
| `{{output.alarm_id}}` | 从 CLI JSON 输出捕获 | 从 `$.result.alarmId` 解析 |

> 规则：`{{env.*}}` 占位符不得向用户暴露或索取。`{{user.*}}` 占位符须通过交互收集。

## 输出解析规则（Agent 可读）

### CLI 强制约定
- 所有 CLI 命令必须追加 `--output json` 以保证机器可解析
- 所有 CLI 命令应追加 `--no-interactive`（或等价参数）防止阻塞等待用户输入
- 时间戳采用 ISO 8601 格式带时区：`2026-04-28T10:00:00+08:00`
- 布尔值：`true` / `false`（小写）

### SDK 响应约定
- SDK 返回对象属性遵循 OpenAPI 定义
- 错误通过 `ClientException` / `ServerException` 抛出
- 时间戳格式同 CLI

### 关键 JSON 路径
| 操作 | JSON 路径 | 类型 | 说明 |
|------|-----------|------|------|
| 创建告警 | `$.result.alarmId` / `response.result.alarmId` | string | 告警规则 ID |
| 查询告警列表 | `$.result.alarms[*].alarmId` | array | 所有告警 ID |
| 查询告警详情 | `$.result.alarm.status` | string | ALARM / OK / INSUFFICIENT_DATA |
| 查询监控数据 | `$.result.metricDatas[*].value` | array | 监控数值 |
| 查询服务列表 | `$.result.services[*].serviceCode` | array | 服务代码列表 |

### 操作超时约定
| 操作 | 最长等待 | 轮询间隔 |
|------|---------|---------|
| 创建告警规则 | 10s（同步操作） | - |
| 查询监控数据 | 30s（API 限流重试） | 2s |
| 删除告警规则 | 10s（同步操作） | - |

## 核心功能

- **监控数据查询**: 查询云资源的实时和历史监控指标数据
- **告警规则管理**: 创建、修改、启用/禁用、删除告警规则
- **告警历史查看**: 查询告警触发历史和通知记录
- **自定义监控**: 上报和查询自定义业务指标
- **Dashboard管理**: 监控面板和图表管理

## 执行流程（Agent 可读）

每个操作遵循：前置检查 → 执行（SDK/API 和 CLI 双路径） → 后置验证 → 失败恢复。Agent 不得跳过任何阶段。

### 操作：创建告警规则

#### 前置检查
| 检查项 | 方法 | 期望 | 失败处理 |
|--------|------|------|---------|
| SDK/CLI 已安装 | SDK: `import jdcloud_sdk`; CLI: `jdc --version` | 无错误 / exit code 0 | 引导用户安装 jdcloud-sdk 或 jdcloud-cli |
| 凭证有效 | SDK: 构造 Credential; CLI: `jdc monitor describe-services --region-id cn-north-1 --output json` | 非空凭证 / `$.error == null` | 提示配置环境变量或 `jdc config init` |
| 区域可用 | SDK/CLI 调用 describeServices | 返回服务列表非空 | 建议最近可用区域 |

#### 执行 — SDK (Python)

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.monitor.client import MonitorClient
from jdcloud_sdk.services.monitor.apis.CreateAlarmRequest import CreateAlarmRequest

credential = Credential(os.environ['JDC_ACCESS_KEY'], os.environ['JDC_SECRET_KEY'])
client = MonitorClient(credential, os.environ.get('JDC_REGION', 'cn-north-1'))

request = CreateAlarmRequest({
    "regionId": "{{user.region}}",
    "alarmName": "{{user.alarm_name}}",
    "serviceCode": "{{user.service_code}}",
    "resourceId": "{{user.resource_id}}",
    "metricName": "{{user.metric_name}}",
    "comparisonOperator": "{{user.comparison}}",
    "threshold": {{user.threshold}},
    "period": {{user.period}},
    "evaluationPeriods": {{user.eval_periods}},
    "contactGroupId": {{user.contact_group_id}},
    "noticeType": "{{user.notice_type}}"
})

response = client.createAlarm(request)
# JSON 路径: $.result.alarmId
alarm_id = response.result.alarmId
```

#### 执行 — CLI (`jdc`)

```bash
jdc monitor create-alarm \
  --region-id {{user.region}} \
  --alarm-name "{{user.alarm_name}}" \
  --service-code {{user.service_code}} \
  --resource-id {{user.resource_id}} \
  --metric-name {{user.metric_name}} \
  --comparison-operator {{user.comparison}} \
  --threshold {{user.threshold}} \
  --period {{user.period}} \
  --evaluation-periods {{user.eval_periods}} \
  --contact-group-id {{user.contact_group_id}} \
  --notice-type "{{user.notice_type}}" \
  --output json \
  --no-interactive
```

#### 后置验证
1. 从 SDK `response.result.alarmId` 或 CLI JSON `$.result.alarmId` 捕获 `{{output.alarm_id}}`
2. 验证告警已创建（SDK 和 CLI 双路径）：
   ```python
   # SDK 验证
   from jdcloud_sdk.services.monitor.apis.DescribeAlarmRequest import DescribeAlarmRequest
   req = DescribeAlarmRequest({"regionId": "{{user.region}}", "alarmId": "{{output.alarm_id}}"})
   resp = client.describeAlarm(req)
   status = resp.result.alarm.status  # ALARM/OK/INSUFFICIENT_DATA
   ```
   ```bash
   # CLI 验证
   jdc monitor describe-alarm \
     --region-id {{user.region}} \
     --alarm-id {{output.alarm_id}} \
     --output json | jq -r '.result.alarm.status'
   ```
3. 若返回有效状态 → 操作成功，向用户报告 `{{output.alarm_id}}`
4. 若返回错误 → 捕获错误信息，进入失败恢复

#### 失败恢复
| 错误模式 (regex) | 最大重试 | 退避策略 | Agent 动作 |
|-----------------|---------|---------|-----------|
| `InvalidParameter` | 1 | - | 检查参数格式，修正后重试 |
| `QuotaExceeded` | 0 | - | 停止。告知用户告警规则配额已满（每区域最多 500 条） |
| `MetricNotFound` | 1 | - | 确认监控项名称，用 `describe-metrics` 查询可用项后重试 |
| `ResourceAlreadyExists` | 0 | - | 告警名称已存在，询问用户是否复用或换名 |
| `InternalError` | 3 | 2s, 4s, 8s | 指数退避重试。第 3 次失败后报告用户 |

### 操作：查询监控数据

#### 执行 — SDK (Python)

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.monitor.client import MonitorClient
from jdcloud_sdk.services.monitor.apis.DescribeMetricDataRequest import DescribeMetricDataRequest

credential = Credential(os.environ['JDC_ACCESS_KEY'], os.environ['JDC_SECRET_KEY'])
client = MonitorClient(credential, os.environ.get('JDC_REGION', 'cn-north-1'))

request = DescribeMetricDataRequest({
    "regionId": "{{user.region}}",
    "metric": "{{user.metric}}",
    "serviceCode": "{{user.service_code}}",
    "resourceId": "{{user.resource_id}}",
    "startTime": "{{user.start_time}}",
    "endTime": "{{user.end_time}}",
    "aggrType": "avg"
})

response = client.describeMetricData(request)
# JSON 路径: $.result.metricDatas[*].value
for data in response.result.metricDatas:
    print(f"Time: {data.timestamp}, Value: {data.value}, Unit: {data.unit}")
```

#### 执行 — CLI (`jdc`)

```bash
jdc monitor describe-metric-data \
  --region-id {{user.region}} \
  --metric {{user.metric}} \
  --service-code {{user.service_code}} \
  --resource-id {{user.resource_id}} \
  --start-time "{{user.start_time}}" \
  --end-time "{{user.end_time}}" \
  --aggr-type avg \
  --output json
```

#### 后置验证
1. 检查 SDK `response.result.metricDatas` 或 CLI JSON `$.result.metricDatas` 是否非空
2. 若为空 → 可能原因：资源刚创建无数据、时间范围错误、监控项名错误
3. 以表格形式展示：时间戳 | 数值 | 单位

#### 失败恢复
| 错误模式 (regex) | 最大重试 | 退避策略 | Agent 动作 |
|-----------------|---------|---------|-----------|
| `RateLimitExceeded` | 3 | 2s, 4s, 8s | 降低频率重试 |
| `ResourceNotFound` | 0 | - | 停止。告知用户资源 ID 不存在 |
| `MetricNotFound` | 1 | - | 用 `describe-metrics` 确认名称后重试 |

### 操作：删除告警规则

#### 前置检查（安全门）
- **必须**询问用户："确认删除告警规则 `{{user.alarm_name}}` ({{user.alarm_id}})？此操作不可撤销。"
- **必须**等待用户明确回复"确认"或"yes"后才继续（SDK 和 CLI 路径均需此安全门）

#### 执行 — SDK (Python)

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.monitor.client import MonitorClient
from jdcloud_sdk.services.monitor.apis.DeleteAlarmsRequest import DeleteAlarmsRequest

credential = Credential(os.environ['JDC_ACCESS_KEY'], os.environ['JDC_SECRET_KEY'])
client = MonitorClient(credential, os.environ.get('JDC_REGION', 'cn-north-1'))

request = DeleteAlarmsRequest({
    "regionId": "{{env.JDC_REGION}}",
    "alarmIds": ["{{user.alarm_id}}"]
})

response = client.deleteAlarms(request)
# 返回 requestId 表示成功
print(f"Delete request accepted: {response.requestId}")
```

#### 执行 — CLI (`jdc`)

```bash
jdc monitor delete-alarms \
  --region-id {{env.JDC_REGION}} \
  --alarm-ids '["{{user.alarm_id}}"]' \
  --output json \
  --no-interactive
```

#### 后置验证
1. 再次查询确认不存在（SDK 和 CLI 双路径）：
   ```python
   # SDK 验证
   from jdcloud_sdk.services.monitor.apis.DescribeAlarmRequest import DescribeAlarmRequest
   req = DescribeAlarmRequest({"regionId": "{{env.JDC_REGION}}", "alarmId": "{{user.alarm_id}}"})
   try:
       client.describeAlarm(req)
   except Exception as e:
       if "AlarmNotFound" in str(e) or "ResourceNotFound" in str(e):
           print("Alarm deleted successfully")
   ```
   ```bash
   # CLI 验证
   jdc monitor describe-alarm \
     --region-id {{env.JDC_REGION}} \
     --alarm-id {{user.alarm_id}} \
     --output json 2>&1
   ```
2. 期望返回 `AlarmNotFound` 错误 → 删除成功

## 前提条件

### 1. 安装京东云 CLI 和 SDK

**方式一：通过 pip 安装 SDK**

```bash
# 安装京东云 SDK
pip install jdcloud_sdk

# 验证安装
python -c "import jdcloud_sdk; print('SDK installed')"
```

**方式二：安装 CLI**

```bash
# 安装京东云 CLI
pip install jdcloud_cli

# 验证安装
jdc --version
```

### 2. 配置凭证

三种方式（按优先级排序）:

**方式 1：`.env` 文件（本地开发推荐）**
```ini
JDC_ACCESS_KEY=your_access_key_here
JDC_SECRET_KEY=your_secret_key_here
JDC_REGION=cn-north-1
```
> Agent Runtime 自动加载 `.env`，Shell 环境变量优先级更高。

**方式 2：Shell 环境变量（生产环境推荐）**
Agent 运行时必须设置以下环境变量，对应本 Skill 中的 `{{env.*}}` 占位符：
```bash
export JDC_ACCESS_KEY="{{env.JDC_ACCESS_KEY}}"
export JDC_SECRET_KEY="{{env.JDC_SECRET_KEY}}"
export JDC_REGION="cn-north-1"
```

**方式 3：CLI 交互式配置**
```bash
jdc config init
```

> Agent 必须在任何操作前验证这些变量已设置。`.env` 文件禁止提交到版本控制。

## 支持的云产品监控

| 类别 | 产品 |
|------|------|
| 计算 | 云主机 CVM、轻量云主机、原生容器、Kubernetes 集群、函数计算 |
| 网络 | 负载均衡、NAT 网关、弹性公网 IP、共享带宽包、专线服务 |
| 存储 | 云硬盘、对象存储、云文件服务 |
| 数据库 | RDS、MongoDB、Redis、Memcached、TiDB、ClickHouse |
| 中间件 | 消息队列 JCQ/RabbitMQ/Kafka/RocketMQ、Zookeeper |
| 其他 | CDN、Elasticsearch、DTS、堡垒机等 |

## 常用 CLI 命令

### 查询监控服务列表
```bash
jdc monitor describe-services --region-id cn-north-1 --output json
```

### 查询指定产品的监控项
```bash
jdc monitor describe-metrics \
  --region-id cn-north-1 \
  --service-code vm \
  --resource-id i-xxx \
  --output json
```

### 查询监控数据
```bash
jdc monitor describe-metric-data \
  --region-id cn-north-1 \
  --metric vm.cpu.util \
  --service-code vm \
  --resource-id i-xxx \
  --start-time "2024-01-01T00:00:00Z" \
  --end-time "2024-01-01T23:59:59Z" \
  --output json
```

### 查询最新监控数据（降采样）
```bash
jdc monitor last-downsample \
  --region-id cn-north-1 \
  --service-code vm \
  --resource-id i-xxx \
  --metrics '["vm.cpu.util","vm.memory.util"]' \
  --output json
```

### 创建告警规则
```bash
jdc monitor create-alarm \
  --region-id cn-north-1 \
  --alarm-name "HighCPUAlarm" \
  --service-code vm \
  --resource-id i-xxx \
  --metric-name "vm.cpu.util" \
  --comparison-operator "gt" \
  --threshold 80 \
  --period 300 \
  --evaluation-periods 2 \
  --contact-group-id 1 \
  --notice-type "sms,email" \
  --output json \
  --no-interactive
```

### 查询告警规则列表
```bash
jdc monitor describe-alarms \
  --region-id cn-north-1 \
  --page-number 1 \
  --page-size 20 \
  --output json
```

### 启用/禁用告警规则
```bash
# 启用告警
jdc monitor enable-alarm \
  --region-id cn-north-1 \
  --alarm-id alarm-xxx \
  --enabled true \
  --output json

# 禁用告警
jdc monitor enable-alarm \
  --region-id cn-north-1 \
  --alarm-id alarm-xxx \
  --enabled false \
  --output json
```

### 查询告警历史
```bash
jdc monitor describe-alarm-history \
  --region-id cn-north-1 \
  --alarm-id alarm-xxx \
  --start-time "2024-01-01T00:00:00Z" \
  --end-time "2024-01-31T23:59:59Z" \
  --output json
```

### 上报自定义监控数据
```bash
jdc monitor put-metric-data \
  --region-id cn-north-1 \
  --namespace custom-namespace \
  --metric-name custom-metric \
  --value 100 \
  --dimensions '{"instance":"app-server-01"}' \
  --output json
```

### 查询自定义监控数据
```bash
jdc monitor describe-custom-metric-data \
  --region-id cn-north-1 \
  --namespace custom-namespace \
  --metric-name custom-metric \
  --start-time "2024-01-01T00:00:00Z" \
  --end-time "2024-01-01T23:59:59Z" \
  --output json
```

## Reference 目录

- [核心概念](references/core-concepts.md) - 云监控核心概念和术语
- [API & SDK 使用](references/api-sdk-usage.md) - SDK 操作映射、请求/响应字段、错误处理
- [CLI 使用指南](references/cli-usage.md) - 详细的 CLI 命令说明、CLI vs API 覆盖对比
- [故障排查指南](references/troubleshooting.md) - 常见问题及解决方案
- [监控与告警](references/monitoring.md) - 监控指标和告警配置
- [集成指南](references/integration.md) - SDK 和 MCP 集成

## 运维最佳实践

### 1. 监控覆盖策略
- **核心资源**: 对生产环境所有云资源启用基础监控
- **关键指标**: CPU、内存、磁盘、网络四大黄金指标必配告警
- **业务指标**: 通过自定义监控上报业务关键指标

### 2. 告警规则配置
- **阈值设置**: 根据业务特点设置合理的告警阈值，避免告警风暴
- **通知策略**: 配置多渠道通知（短信+邮件+回调），设置通知周期避免重复打扰
- **分级告警**: 区分 P0/P1/P2 级别，配置不同的通知策略和响应时间

### 3. Dashboard 管理
- **业务视角**: 按业务系统组织监控面板
- **关键指标置顶**: 将最重要的指标放在面板顶部
- **模板变量**: 使用模板变量实现资源的快速切换

### 4. 成本优化
- **存储周期**: 根据数据重要性设置不同的数据存储周期
- **采集频率**: 非关键资源可适当降低监控数据采集频率

## 常用监控指标

### 云主机(VM)常用指标
| 指标名称 | 说明 | 单位 |
|---------|------|------|
| vm.cpu.util | CPU 使用率 | % |
| vm.memory.util | 内存使用率 | % |
| vm.disk.read | 磁盘读速率 | Bps |
| vm.disk.write | 磁盘写速率 | Bps |
| vm.network.in | 内网入速率 | bps |
| vm.network.out | 内网出速率 | bps |

### 云数据库 RDS 常用指标
| 指标名称 | 说明 | 单位 |
|---------|------|------|
| rds.cpu.util | CPU 使用率 | % |
| rds.memory.util | 内存使用率 | % |
| rds.connection.util | 连接数使用率 | % |
| rds.qps | 每秒查询数 | 次/秒 |
| rds.tps | 每秒事务数 | 次/秒 |

### 负载均衡常用指标
| 指标名称 | 说明 | 单位 |
|---------|------|------|
| lb.newconnection | 新建连接数 | 个/秒 |
| lb.activeconnection | 活跃连接数 | 个 |
| lb.traffic.in | 入流量 | bps |
| lb.traffic.out | 出流量 | bps |

## API 限制说明

| 限制项 | 说明 |
|--------|------|
| 查询频率 | 监控数据查询接口默认 QPS 限制为 100 |
| 数据保留 | 原始监控数据保留 15 天，聚合数据保留 30 天 |
| 告警规则 | 每个区域最多可创建 500 条告警规则 |
| 自定义指标 | 每个命名空间最多支持 1000 个自定义指标 |

## 相关链接

- [京东云云监控产品页](https://www.jdcloud.com/cn/products/monitoring)
- [云监控文档中心](https://docs.jdcloud.com/cn/monitoring/learning)
- [云监控 API 文档](https://docs.jdcloud.com/cn/monitoring/api/overview)
- [京东云 CLI](https://github.com/jdcloud-api/jdcloud-cli)