# CLI — 告警智能助手 (`jdc`)

> 本文件是 `jdcloud-alert-intelligence` 的 CLI 命令参考手册。
> **本 Skill 全程只读**：仅使用查询类命令（describe-* / last-downsample），不调用 create/update/delete/enable。

## 通用约定

### jdc CLI 凭证加载

- `jdc` CLI 仅从 `~/.jdc/config` INI 文件读取凭证，**不支持** `JDC_ACCESS_KEY` / `JDC_SECRET_KEY` 环境变量
- 沙箱环境：将 `HOME` 重定向到可写目录并预创建配置文件
- 详细配置参考 [京东云 CLI 官方仓库](https://github.com/jdcloud-api/jdcloud-cli)

### 参数位置硬性规则

- **`--output json` 必须放在子命令之前**（顶层参数）：
  ```bash
  jdc --output json monitor describe-alarm-history ...
  ```
- **`--no-interactive` 不存在**：`jdc` 默认非交互式，删除此标志
- 时间戳：ISO 8601 格式带时区（推荐 `+08:00`，兼容 `Z`）
- 布尔值：小写 `true` / `false`

### 失败重试策略

- 单条命令最多重试 **3 次**，指数退避 `0s → 2s → 4s`
- 3 次失败后**不静默吞错**，返回原始错误响应给上层 Agent
- 推荐用 bash 包装函数（见末尾"批量/自动化样例"）

### 时间窗约束

| 数据类型 | 保留期 | 本 skill 推荐窗口 |
|---|---|---|
| 告警历史原始 | 15d | ≤ 15d |
| 1h 聚合 | 30d | 15d - 30d |
| 1d 聚合 | 180d | 30d+（仅做趋势） |

> 超过 15d 的告警历史查询可能返回空数据或采样后数据，分析时需在报告中标注"采样后"。

---

## 告警规则查询（只读）

### 1. describe-alarms — 查询告警规则列表

列出当前区域下所有告警规则，含规则状态、阈值、关联资源等元信息。本 skill 在 Step 3 分级时会用到"规则元信息"做关联。

```bash
jdc --output json monitor describe-alarms \
  --region-id cn-north-1 \
  --page-number 1 \
  --page-size 100
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--region-id` | string | 是 | 区域 ID |
| `--service-code` | string | 否 | 服务代码过滤（vm / rds / lb / redis / ...） |
| `--resource-id` | string | 否 | 资源 ID 过滤 |
| `--alarm-name` | string | 否 | 告警名称模糊过滤 |
| `--alarm-status` | string | 否 | 告警状态过滤：`enabled` / `disabled` |
| `--page-number` | integer | 否 | 页码，默认 1 |
| `--page-size` | integer | 否 | 每页数量，默认 20，上限 100 |

**返回示例**

```json
{
  "result": {
    "alarms": [
      {
        "alarmId": "alarm-abc123",
        "alarmName": "VM-HighCPU-Critical",
        "serviceCode": "vm",
        "resourceId": "i-xxx",
        "metricName": "vm.cpu.util",
        "comparisonOperator": "gt",
        "threshold": 90,
        "period": 300,
        "evaluationPeriods": 2,
        "enabled": true,
        "status": "OK"
      }
    ],
    "totalCount": 42,
    "pageNumber": 1,
    "pageSize": 100
  }
}
```

**关键 JSON 路径**

| 用途 | 路径 |
|------|------|
| 全部告警 ID | `$.result.alarms[*].alarmId` |
| 告警名称 | `$.result.alarms[*].alarmName` |
| 关联服务 | `$.result.alarms[*].serviceCode` |
| 关联资源 | `$.result.alarms[*].resourceId` |
| 监控指标 | `$.result.alarms[*].metricName` |
| 当前状态 | `$.result.alarms[*].status` |
| 启用状态 | `$.result.alarms[*].enabled` |
| 阈值 | `$.result.alarms[*].threshold` |
| 总数 | `$.result.totalCount` |

---

### 2. describe-alarm — 查询告警规则详情

查询单个告警规则的完整配置。

```bash
jdc --output json monitor describe-alarm \
  --region-id cn-north-1 \
  --alarm-id alarm-abc123
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--region-id` | string | 是 | 区域 ID |
| `--alarm-id` | string | 是 | 告警规则 ID |

**返回示例**

```json
{
  "result": {
    "alarm": {
      "alarmId": "alarm-abc123",
      "alarmName": "VM-HighCPU-Critical",
      "serviceCode": "vm",
      "resourceId": "i-xxx",
      "metricName": "vm.cpu.util",
      "comparisonOperator": "gt",
      "threshold": 90,
      "period": 300,
      "evaluationPeriods": 2,
      "contactGroupId": 1,
      "noticeType": "sms,email",
      "noticePeriod": 30,
      "enabled": true,
      "status": "OK",
      "createTime": "2026-01-15T10:00:00+08:00"
    }
  }
}
```

**关键 JSON 路径**

| 用途 | 路径 |
|------|------|
| 告警状态 | `$.result.alarm.status`（值：`ALARM` / `OK` / `INSUFFICIENT_DATA`） |
| 阈值 | `$.result.alarm.threshold` |
| 启用 | `$.result.alarm.enabled` |
| 通知配置 | `$.result.alarm.noticeType` |

---

## 告警历史查询（核心入口）

### 3. describe-alarm-history — 查询告警触发历史

**本 skill 的 Step 1 主入口**：拉取时间窗内所有告警事件，用于聚合与分级。

```bash
jdc --output json monitor describe-alarm-history \
  --region-id cn-north-1 \
  --start-time "2026-06-02T00:00:00+08:00" \
  --end-time   "2026-06-03T00:00:00+08:00" \
  --page-size 100
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--region-id` | string | 是 | 区域 ID |
| `--start-time` | string | 否 | 开始时间（ISO 8601） |
| `--end-time` | string | 否 | 结束时间（ISO 8601） |
| `--alarm-id` | string | 否 | 按告警规则 ID 过滤 |
| `--service-code` | string | 否 | 按服务代码过滤（vm/rds/lb/...） |
| `--resource-id` | string | 否 | 按资源 ID 过滤 |
| `--page-number` | integer | 否 | 页码，默认 1 |
| `--page-size` | integer | 否 | 每页数量，默认 20，上限 100 |

**返回示例**

```json
{
  "result": {
    "alarmHistoryList": [
      {
        "alarmId": "alarm-abc123",
        "alarmName": "VM-HighCPU-Critical",
        "serviceCode": "vm",
        "resourceId": "i-xxx",
        "metricName": "vm.cpu.util",
        "status": "ALARM",
        "triggerTime": "2026-06-02T14:35:12+08:00",
        "value": 95.2,
        "regionId": "cn-north-1"
      }
    ],
    "totalCount": 187,
    "pageNumber": 1,
    "pageSize": 100
  }
}
```

**关键 JSON 路径**

| 用途 | 路径 |
|------|------|
| 告警历史条目 | `$.result.alarmHistoryList[*]` |
| 告警规则 ID | `$.result.alarmHistoryList[*].alarmId` |
| 服务代码 | `$.result.alarmHistoryList[*].serviceCode` |
| 资源 ID | `$.result.alarmHistoryList[*].resourceId` |
| 监控指标 | `$.result.alarmHistoryList[*].metricName` |
| 触发状态 | `$.result.alarmHistoryList[*].status`（`ALARM` / `OK`） |
| 触发时间 | `$.result.alarmHistoryList[*].triggerTime` |
| 触发时指标值 | `$.result.alarmHistoryList[*].value` |
| 区域 | `$.result.alarmHistoryList[*].regionId` |
| 总条数 | `$.result.totalCount` |

> **注意**：JSON 字段名是 `alarmHistoryList`（SKILL.md 已锁定），不是 cloudmonitor-ops cli-usage.md 中的 `alarmHistories`。两者是不同 skill 下的不同响应结构。

**分页处理示例**

```bash
fetch_all_history() {
  local region="$1" start="$2" end="$3"
  local page=1
  local all="[]"

  while : ; do
    local resp
    resp=$(jdc --output json monitor describe-alarm-history \
      --region-id "$region" \
      --start-time "$start" \
      --end-time "$end" \
      --page-number "$page" \
      --page-size 100)

    local batch total
    batch=$(echo "$resp" | jq '.result.alarmHistoryList // []')
    total=$(echo "$resp" | jq '.result.totalCount // 0')

    all=$(jq -s 'add' <(echo "$all") <(echo "$batch"))

    # 本页条数 < pageSize 说明已到末页
    local batch_count
    batch_count=$(echo "$batch" | jq 'length')
    if [ "$batch_count" -lt 100 ]; then
      break
    fi
    page=$((page + 1))

    # 安全护栏：单次查询不超过 50 页
    if [ "$page" -gt 50 ]; then
      echo "WARN: 分页超过 50 页，提前终止" >&2
      break
    fi
  done

  echo "$all"
}
```

---

## v0.1 限制: alarm-id 单数

`jdc monitor describe-alarm-history` 的 `--alarm-id` 参数在 jdc CLI 中为**单数** (string)，**不**支持数组传入。

**影响场景：**

- 周期性检测（[suppression-rules.md §3](./suppression-rules.md)）需拉多个 alarm-rule 的历史时
- 多告警规则聚类后追溯来源时

**v0.1 应对策略：** 必须在 bash 脚本中**循环调用**，每次传 1 个 alarm-id：

```bash
for aid in "${alarm_ids[@]}"; do
  jdc --output json monitor describe-alarm-history \
    --region-id "${JDC_REGION:-cn-north-1}" \
    --alarm-id "$aid" \
    --start-time "<now-7d>" \
    --end-time   "<now>" \
    --page-size 200
done
```

**v0.2 计划：** 切换到 SDK 调用 `alarmIds` 数组参数（一次拉取），同时保留 jdc CLI 路径以对齐其余调用风格。

---

## 监控项查询

### 4. describe-metrics — 查询服务的监控项

聚合后如需补充"该指标的语义描述、单位、合理范围"，可调用此命令。

```bash
jdc --output json monitor describe-metrics \
  --region-id cn-north-1 \
  --service-code vm \
  --resource-id i-xxx
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--region-id` | string | 是 | 区域 ID |
| `--service-code` | string | 是 | 服务代码（vm / rds / lb / ...） |
| `--resource-id` | string | 否 | 资源 ID |
| `--metric` | string | 否 | 监控项名称模糊过滤 |
| `--page-number` | integer | 否 | 页码 |
| `--page-size` | integer | 否 | 每页数量 |

**关键 JSON 路径**

| 用途 | 路径 |
|------|------|
| 监控项列表 | `$.result.metrics[*].metric` |
| 显示名称 | `$.result.metrics[*].metricName` |
| 单位 | `$.result.metrics[*].unit` |
| 采集周期 | `$.result.metrics[*].period` |

---

## 监控数据查询

### 5. describe-metric-data — 查询时间序列数据

聚合后如需对某个告警簇的"指标走势"做佐证（例如取告警触发前后 1h 的 CPU 曲线），调用此命令。

```bash
jdc --output json monitor describe-metric-data \
  --region-id cn-north-1 \
  --metric vm.cpu.util \
  --service-code vm \
  --resource-id i-xxx \
  --start-time "2026-06-02T13:00:00+08:00" \
  --end-time   "2026-06-02T15:00:00+08:00" \
  --aggr-type max \
  --period 60
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--region-id` | string | 是 | 区域 ID |
| `--metric` | string | 是 | 监控项名称（如 `vm.cpu.util`） |
| `--service-code` | string | 是 | 服务代码 |
| `--resource-id` | string | 是 | 资源 ID |
| `--start-time` | string | 是 | 开始时间（ISO 8601） |
| `--end-time` | string | 是 | 结束时间（ISO 8601） |
| `--aggr-type` | string | 否 | 聚合类型：`avg` / `max` / `min` / `sum`，默认 `avg` |
| `--period` | integer | 否 | 时间粒度（秒），与告警规则的 `period` 对齐 |
| `--dimensions` | string | 否 | 维度过滤（JSON 字符串） |

**关键 JSON 路径**

| 用途 | 路径 |
|------|------|
| 数据点 | `$.result.metricDatas[*].dataPoints` |
| 时间戳 | `$.result.metricDatas[*].dataPoints[*].timestamp` |
| 值 | `$.result.metricDatas[*].dataPoints[*].value` |
| 单位 | `$.result.metricDatas[*].dataPoints[*].unit` |

---

### 6. last-downsample — 查询最新降采样数据

快速拉取资源最新一个数据点，用于"告警是否还在触发"的状态确认。

```bash
jdc --output json monitor last-downsample \
  --region-id cn-north-1 \
  --service-code vm \
  --resource-id i-xxx \
  --metrics '["vm.cpu.util","vm.memory.util","vm.disk.util"]'
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--region-id` | string | 是 | 区域 ID |
| `--service-code` | string | 是 | 服务代码 |
| `--resource-id` | string | 是 | 资源 ID |
| `--metrics` | string | 是 | 监控项列表（JSON 数组字符串） |
| `--start-time` | string | 否 | 起始时间（默认最新） |
| `--end-time` | string | 否 | 结束时间 |

**返回示例**

```json
{
  "result": {
    "items": [
      {
        "metric": "vm.cpu.util",
        "timestamp": "2026-06-03T10:00:00+08:00",
        "value": 45.2,
        "unit": "%"
      }
    ]
  }
}
```

---

## 告警联系人查询

### 7. describe-alarm-contacts — 查询告警联系人

分析报告中需要展示"告警通知给了谁"时调用（值班疲劳分析）。

```bash
jdc --output json monitor describe-alarm-contacts \
  --region-id cn-north-1 \
  --page-number 1 \
  --page-size 50
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--region-id` | string | 是 | 区域 ID |
| `--contact-group-id` | integer | 否 | 联系组 ID 过滤 |
| `--page-number` | integer | 否 | 页码 |
| `--page-size` | integer | 否 | 每页数量 |

**关键 JSON 路径**

| 用途 | 路径 |
|------|------|
| 联系组 | `$.result.contactGroups[*].contactGroupId` |
| 组名 | `$.result.contactGroups[*].contactGroupName` |
| 联系人 | `$.result.contactGroups[*].contacts` |

---

## 关键 JSON 路径汇总表

| 操作 | 主路径 | 类型 |
|------|--------|------|
| 告警规则列表 | `$.result.alarms[*].alarmId` | array |
| 告警规则详情状态 | `$.result.alarm.status` | string |
| **告警历史条目** | `$.result.alarmHistoryList[*]` | array |
| 告警历史状态 | `$.result.alarmHistoryList[*].status` | string |
| 监控项列表 | `$.result.metrics[*].metric` | array |
| 监控数据点 | `$.result.metricDatas[*].dataPoints` | array |
| 最新数据点 | `$.result.items[*].value` | array |

---

## 错误码与异常 case

> 详细故障排查见 [`../jdcloud-cloudmonitor-ops/references/troubleshooting.md`](../../jdcloud-cloudmonitor-ops/references/troubleshooting.md)。本节仅列本 skill 高频遇到的 case。

| 错误码 / 现象 | 含义 | 本 skill 处理 |
|---|---|---|
| `InvalidParameter` | 时间格式错误 | 检查 ISO 8601 格式 |
| `InvalidParameterValue` | `page-size` 超过 100 | 改为 100，分页处理 |
| `ResourceNotFound` | 区域 ID 错误 | 修正 `--region-id` |
| `MetricNotFound` | 监控项名称错误 | 调 `describe-metrics` 查正确名 |
| `AlarmNotFound` | alarm-id 错误 | 调 `describe-alarms` 列出 |
| `QuotaExceeded` | 调用频率超限 | 加重试退避，必要时 fallback 到 1d 聚合查询 |
| `RateLimitExceeded` | 限流 | 立即重试一次；持续则报告"采样不全" |
| `Unauthorized` | 凭证无权限 | 提示用户检查 `~/.jdc/config` |
| **空响应**（`alarmHistoryList: []`） | 时间窗内无告警 | 报告"该时段无告警"，不报错 |
| **数据延迟** | 最新数据延迟 3-5min | 用 `last-downsample` 而非 `describe-metric-data` |

### 数据完整性自检

每次拉取后做 3 项自检：

```bash
# 1. 响应是否为空
if [ "$(echo "$resp" | jq '.result.alarmHistoryList | length // 0')" -eq 0 ]; then
  echo "INFO: 时间窗内无告警事件"
fi

# 2. 总数与本批是否一致（潜在分页残留）
local_count=$(echo "$resp" | jq '.result.alarmHistoryList | length')
total_count=$(echo "$resp" | jq '.result.totalCount // 0')
if [ "$total_count" -gt "$local_count" ]; then
  echo "WARN: 存在分页，总数 $total_count > 本批 $local_count，需翻页"
fi

# 3. 必填字段是否完整
missing=$(echo "$resp" | jq '[.result.alarmHistoryList[] | select(.alarmId == null or .serviceCode == null or .resourceId == null)] | length')
if [ "$missing" -gt 0 ]; then
  echo "WARN: $missing 条告警缺关键字段，需在报告中标注"
fi
```

---

## 批量 / 自动化样例脚本

### 样例 1：单区域 24h 告警全量拉取（带重试）

```bash
#!/bin/bash
# fetch_alerts_24h.sh — 拉取某区域最近 24h 全部告警，自动重试
set -euo pipefail

REGION="${1:-cn-north-1}"
OUTPUT="${2:-/tmp/alerts_${REGION}_24h.json}"

START=$(date -u -v-24H +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null \
  || date -u -d '24 hours ago' +"%Y-%m-%dT%H:%M:%SZ")
END=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

fetch_with_retry() {
  local attempt=0
  local delay=0
  while [ $attempt -lt 3 ]; do
    if jdc --output json monitor describe-alarm-history \
        --region-id "$REGION" \
        --start-time "$START" \
        --end-time "$END" \
        --page-size 100; then
      return 0
    fi
    attempt=$((attempt + 1))
    delay=$((delay == 0 ? 2 : delay * 2))
    echo "RETRY: attempt=$attempt delay=${delay}s" >&2
    sleep "$delay"
  done
  return 1
}

fetch_with_retry > "$OUTPUT"
echo "Saved to $OUTPUT"
```

### 样例 2：按服务代码分批拉取

```bash
#!/bin/bash
# fetch_by_service.sh — 拉取指定服务列表的告警
set -euo pipefail

REGION="$1"
shift
SERVICES=("$@")
START="$3"
END="$4"

for svc in "${SERVICES[@]}"; do
  jdc --output json monitor describe-alarm-history \
    --region-id "$REGION" \
    --service-code "$svc" \
    --start-time "$START" \
    --end-time "$END" \
    --page-size 100 \
    > "/tmp/alerts_${REGION}_${svc}.json"
  echo "Service=$svc saved"
done
```

### 样例 3：拉取 + 解析 + 聚合键提取（jq pipeline）

```bash
REGION="cn-north-1"
START="2026-06-02T00:00:00+08:00"
END="2026-06-03T00:00:00+08:00"

jdc --output json monitor describe-alarm-history \
  --region-id "$REGION" \
  --start-time "$START" \
  --end-time "$END" \
  --page-size 100 \
| jq '[.result.alarmHistoryList[]? | {
    cluster_key: "\(.serviceCode)|\(.resourceId)|\(.metricName)",
    alarm_id: .alarmId,
    status: .status,
    trigger_time: .triggerTime,
    value: .value
  }]' \
> /tmp/alerts_normalized.json

# 统计簇数
echo "Distinct clusters: $(jq -r '.[].cluster_key' /tmp/alerts_normalized.json | sort -u | wc -l)"
echo "Total events: $(jq 'length' /tmp/alerts_normalized.json)"
```

### 样例 4：拉取后做最简分级（P0/P1/P2/P3 启发式）

```bash
# 简易分级脚本（v0.1 规则：持续 > 30min 视为 P0，> 5min 视为 P1，否则 P2）
jq -r '
  group_by(.cluster_key) | .[] |
  {
    cluster: .[0].cluster_key,
    count: length,
    first: min_by(.trigger_time).trigger_time,
    last:  max_by(.trigger_time).trigger_time,
    severity: (
      if length > 0 then
        ((max_by(.trigger_time).trigger_time | fromdateiso8601) -
         (min_by(.trigger_time).trigger_time | fromdateiso8601)) as $dur |
        (if $dur > 1800 then "P0"
         elif $dur > 300 then "P1"
         else "P2" end)
      else "P3" end
    )
  } | "\(.severity)\t\(.count)x\t\(.cluster)\t\(.first)~\(.last)"
' /tmp/alerts_normalized.json | sort -k1,1 -k2,2nr
```

> 真实分级规则参考 [severity-matrix.md](./severity-matrix.md)。此样例仅供"应急用"快速出数。

---

## 输出格式

`--output` 顶层参数指定输出格式：

| 格式 | 用途 |
|------|------|
| `json` | 自动化（**本 skill 唯一推荐格式**） |
| `table` | 人眼查看（调试用） |
| `text` | 纯文本（极少用） |

```bash
jdc --output table monitor describe-alarms --region-id cn-north-1
```

---

## 全局参数

| 参数 | 说明 |
|------|------|
| `--debug` | 显示调试信息 |
| `--output` | 输出格式（json/table/text），**必须放在子命令之前** |
| `--profile` | 使用指定的 INI profile |
| `--region-id` | 区域 ID |

---

## 跨 skill 命令速查

| 任务 | 命令 | 委派给 |
|------|------|--------|
| 创建告警规则 | `jdc monitor create-alarm ...` | `jdcloud-cloudmonitor-ops` |
| 修改告警阈值 | `jdc monitor update-alarm ...` | `jdcloud-cloudmonitor-ops` |
| 删除告警 | `jdc monitor delete-alarms ...` | `jdcloud-cloudmonitor-ops` |
| 启用/禁用告警 | `jdc monitor enable-alarm ...` | `jdcloud-cloudmonitor-ops` |
| 上报自定义指标 | `jdc monitor put-metric-data ...` | `jdcloud-cloudmonitor-ops` |
| **查询告警历史** | `jdc monitor describe-alarm-history ...` | **本 skill** |
| **查询告警规则** | `jdc monitor describe-alarms ...` | **本 skill** |
| **查询监控数据** | `jdc monitor describe-metric-data ...` | **本 skill** |
| **查询最新数据** | `jdc monitor last-downsample ...` | **本 skill** |

> 本 skill **不调用**写命令（create/update/delete/enable/put）。若分析结果需要变更告警规则，输出建议交给 `jdcloud-cloudmonitor-ops`。
