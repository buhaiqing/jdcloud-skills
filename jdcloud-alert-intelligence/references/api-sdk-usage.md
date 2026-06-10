# API & SDK — 告警智能助手

> **本 Skill 全程只读**：仅使用 `describe*` 类查询接口，**不**调用 `createAlarm` /
> `updateAlarm` / `enableAlarm` / `disableAlarm` / `deleteAlarms` 等变更接口。
> 任何告警规则的变更请委派 [`jdcloud-cloudmonitor-ops`](../jdcloud-cloudmonitor-ops/SKILL.md)。

## OpenAPI 规格

- **API 文档**: https://docs.jdcloud.com/cn/monitoring/api/overview
- **服务标识**: `monitor`
- **基础路径**: `monitor.jdcloud-api.com`
- **API 版本**: v1
- **本 Skill 用到的 operationId**: `describeAlarmHistory`, `describeAlarms`, `describeAlarm`,
  `describeMetrics`, `describeMetricData`, `lastDownsample`, `describeAlarmContacts`

> **明确不调用**：`createAlarm` / `updateAlarm` / `enableAlarm` / `disableAlarm` /
> `deleteAlarms` / `createAlarmContact` / `updateAlarmContact` —— 这些都委派给
> [`jdcloud-cloudmonitor-ops`](../jdcloud-cloudmonitor-ops/SKILL.md)。

## SDK 操作映射（本 Skill 用到的子集）

| 目标 | API operationId | SDK 方法 (Python) | 本 Skill 用途 |
|---|---|---|---|
| 查询告警历史 | `describeAlarmHistory` | `client.describeAlarmHistory(request)` | Step 1 拉取（主调用）|
| 查询告警规则列表 | `describeAlarms` | `client.describeAlarms(request)` | Step 3 关联规则元信息 |
| 查询告警规则详情 | `describeAlarm` | `client.describeAlarm(request)` | Step 3 单条规则详情 |
| 查询监控项 | `describeMetrics` | `client.describeMetrics(request)` | 校验 metricName 是否合法 |
| 查询监控数据 | `describeMetricData` | `client.describeMetricData(request)` | Step 2 取 peak_value |
| 查询最新数据 | `lastDownsample` | `client.lastDownsample(request)` | 实时面板辅助查询 |
| 查询告警联系人 | `describeAlarmContacts` | `client.describeAlarmContacts(request)` | 报告中"联系谁"段（只读）|

## Python SDK 使用

### 安装

```bash
uv pip install jdcloud_sdk>=1.6.26
# 或
pip install jdcloud_sdk>=1.6.26
```

> **版本锁定**：与 [`jdcloud-cloudmonitor-ops`](../jdcloud-cloudmonitor-ops/SKILL.md)
> 一致，固定 `jdcloud_cli==1.2.12` + `jdcloud_sdk>=1.6.26`。本 Skill 仅使用 SDK 作为
> **fallback** 路径，主路径是 `jdc --output json monitor ...` CLI。

### 初始化客户端

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.core.config import Config
from jdcloud_sdk.services.monitor.client import MonitorClient

# 使用环境变量配置凭证（推荐）
credential = Credential(
    os.environ['JDC_ACCESS_KEY'],
    os.environ['JDC_SECRET_KEY']
)

config = Config(timeout=30)
client = MonitorClient(config, credential, os.environ.get('JDC_REGION', 'cn-north-1'))
```

### 查询告警历史（主调用）

```python
from jdcloud_sdk.services.monitor.apis.DescribeAlarmHistoryRequest import DescribeAlarmHistoryRequest

request = DescribeAlarmHistoryRequest({
    "regionId": "cn-north-1",
    "startTime": "2026-06-02T00:00:00+08:00",
    "endTime":   "2026-06-03T00:00:00+08:00",
    "pageSize":  100,
    # 可选过滤:
    # "serviceCode": "vm",
    # "resourceId": "i-xxx",
    # "alarmId": "alarm-xxx",     # v0.1 单数 string，多规则需循环
})

response = client.describeAlarmHistory(request)
# JSON 路径: $.result.alarmHistoryList[*]
for ev in response.result.alarmHistoryList:
    print(f"{ev.triggerTime} {ev.serviceCode}/{ev.resourceId}/{ev.metricName} status={ev.status}")
```

### 查询告警规则

```python
from jdcloud_sdk.services.monitor.apis.DescribeAlarmsRequest import DescribeAlarmsRequest

request = DescribeAlarmsRequest({
    "regionId": "cn-north-1",
    "pageSize": 100,
    # 可选:
    # "serviceCode": "vm",
    # "alarmStatus": "enabled",
})

response = client.describeAlarms(request)
# JSON 路径: $.result.alarms[*].alarmId
for rule in response.result.alarms:
    print(f"alarmId={rule.alarmId} {rule.serviceCode}/{rule.metricName} threshold={rule.threshold}")
```

### 查询监控数据（peak_value 关联）

```python
from jdcloud_sdk.services.monitor.apis.DescribeMetricDataRequest import DescribeMetricDataRequest

request = DescribeMetricDataRequest({
    "regionId":    "cn-north-1",
    "metric":      "vm.cpu.util",
    "serviceCode": "vm",
    "resourceId":  "i-xxx",
    "startTime":   "2026-06-02T00:00:00+08:00",
    "endTime":     "2026-06-03T00:00:00+08:00",
    "aggrType":    "max",   # 取 peak 用 max
    "period":      300,
})

response = client.describeMetricData(request)
# JSON 路径: $.result.metricDatas[*].dataPoints
peak = max((dp.value for dp in response.result.metricDatas[0].dataPoints), default=None)
```

## CLI 主路径（推荐）

**优先使用 `jdc` CLI**，避免 Python SDK 依赖。CLI 主路径示例：

```bash
jdc --output json monitor describe-alarm-history \
  --region-id "${JDC_REGION:-cn-north-1}" \
  --start-time "2026-06-02T00:00:00+08:00" \
  --end-time   "2026-06-03T00:00:00+08:00" \
  --page-size 100
```

完整 CLI 用法见 [cli-usage.md](./cli-usage.md)。

## 失败 fallback 路径

| 场景 | 主路径 | Fallback |
|---|---|---|
| jdc CLI 不可用 | jdc CLI | jdcloud_sdk Python SDK |
| 单 alarm-id 周期性历史 | jdc CLI `--alarm-id` (单数) | SDK `describeAlarmHistory`（单数）循环 |
| 分页 100 条以上 | jdc CLI `--page-size 100` + `--page-number N` | SDK `pageSize`/`pageNumber` 循环 |

> **术语约定**：本 Skill 中 "fallback" **专指**主路径失败后的回退动作（如 jdc → SDK）。
> 抑制层的"降一档"使用 "demote"，**不**使用 "fallback"（见 [core-concepts.md §3.1](./core-concepts.md)）。
> 中文"降级"一词在本 Skill 内**只**用于"抑制降档 (demote)"语义。

## 错误码映射（只读类）

| 错误码 | 含义 | 本 Skill 处理 |
|---|---|---|
| `InvalidParameter` | 参数无效 | 修正参数，重试 3 次后仍失败 → 返回错误给上层 |
| `InvalidParameterValue` | 参数值无效 | 同上 |
| `ResourceNotFound` | 资源不存在 | 跳过该资源，不阻断 |
| `AlarmNotFound` | 告警规则不存在 | 跳过该 alarmId，不阻断 |
| `MetricNotFound` | 监控项不存在 | 跳过，不阻断 |
| `Unauthorized` | 未授权 | **ABORT** — IAM 配置错误，需用户介入 |
| `RateLimitExceeded` | 限流 | 重试 3 次（指数退避 0s/2s/4s）|
| `InternalError` | 内部错误 | 重试 3 次（指数退避），仍失败则返回错误 |

完整错误码见 [`jdcloud-cloudmonitor-ops` integration.md](../jdcloud-cloudmonitor-ops/references/integration.md) § 错误处理。

## 调用频率约束

- **jdc CLI 单次调用**：拉告警历史 + 7d 周期性回看 = 至少 2 次 `describe-alarm-history`
- **推荐上限**：单次分析（24h 窗口）总调用次数 ≤ 10 次（避免触发限流）
- **多页场景**：使用 `--page-number` 循环，而非并行调用

## 跨 Skill 引用

- 告警规则变更（创建/修改/删除）→ [`jdcloud-cloudmonitor-ops`](../jdcloud-cloudmonitor-ops/SKILL.md)
- 资源问题排查（VM/RDS/LB/Redis）→ 各 `jdcloud-*-ops`
- 告警联系人配置 → [`jdcloud-cloudmonitor-ops`](../jdcloud-cloudmonitor-ops/SKILL.md) `alarmContacts` 子命令