# Monitoring — jdcloud-vpc-ops

> **版本**: 1.0.0 | 与 `jdcloud-cloudmonitor-ops` 配合

## 1. VPC Flow Logs (VPC 流日志)

京东云 VPC 支持流日志功能，记录 VPC 内弹性网卡的出入流量信息。

### 开启流日志

```bash
# 1. 创建流日志 (委托给 jdcloud-cloudmonitor-ops)
# 或直接 CLI:
jdc --output json cloudmonitor create-vpc-flow-log \
  --vpc-id "vpc-xxx" \
  --log-store-name "flow-log-store" \
  --traffic-type "ALL"  # ALL | ACCEPT | REJECT
```

### 流日志字段

| 字段 | 说明 | 示例 |
|------|------|------|
| `vpc_id` | VPC ID | vpc-3p9mkq2v3a |
| `interface_id` | 弹性网卡 ID | eni-xxxx |
| `src_addr` | 源 IP | 10.0.1.11 |
| `dst_addr` | 目的 IP | 10.0.2.22 |
| `src_port` | 源端口 | 443 |
| `dst_port` | 目的端口 | 8080 |
| `protocol` | 协议号 | 6 (TCP) |
| `packets` | 包数量 | 1024 |
| `bytes` | 字节数 | 1048576 |
| `action` | 动作 | ACCEPT / REJECT |
| `log_status` | 日志状态 | OK / NODATA / SKIPDATA |

## 2. Cloud Monitor 指标

通过 `jdcloud-cloudmonitor-ops` (或直接 `jdc cloudmonitor`)查询 VPC 相关监控指标:

### VPC 级指标

| 指标 | 单位 | 说明 |
|------|:---:|------|
| `vpc.bandwidth_in` | bps | VPC 入方向带宽 |
| `vpc.bandwidth_out` | bps | VPC 出方向带宽 |
| `vpc.packets_in` | 个/秒 | 入方向包速率 |
| `vpc.packets_out` | 个/秒 | 出方向包速率 |

### 子网级指标

| 指标 | 单位 | 说明 |
|------|:---:|------|
| `subnet.bandwidth_in` | bps | 子网入方向带宽 |
| `subnet.bandwidth_out` | bps | 子网出方向带宽 |

### 安全组级指标

| 指标 | 单位 | 说明 |
|------|:---:|------|
| `sg.active_rule_count` | 个 | 安全组生效规则数 |
| `sg.referenced_count` | 个 | 安全组被引用次数 |

### 查询示例

```bash
# jdc 方式 (委托 cloudmonitor)
jdc --output json cloudmonitor describe-metric-data \
  --metric "vpc.bandwidth_in" \
  --resource-id "vpc-xxx" \
  --start-time "2026-06-07T00:00:00Z" \
  --end-time "2026-06-08T00:00:00Z" \
  --time-interval "1h"

# SDK 方式
from jdcloud_sdk.services.monitor.client.MonitorClient import MonitorClient
# 委托给 jdcloud-cloudmonitor-ops
```

## 3. 告警规则建议

### 需要设置告警的 VPC 场景

| 场景 | 指标 | 阈值 | 严重级别 | 委托 skill |
|------|------|:---:|:-------:|-----------|
| VPC 带宽接近上限 | `vpc.bandwidth_out` | > 80% 规格 | Warning | `jdcloud-cloudmonitor-ops` |
| 安全组规则数超限预警 | `sg.active_rule_count` | > 80 | Warning | `jdcloud-cloudmonitor-ops` |
| 子网 IP 耗尽（无直接指标,需结合 describe） | subnet CIDR 使用率 | > 80% | Warning | manual check |
| VPC Peering 带宽 | peering 流量 | 按需 | — | manual check |

### 创建告警规则

```bash
# 创建带宽告警
jdc --output json cloudmonitor create-alarm-rule \
  --rule-name "VPC-Bandwidth-High" \
  --metric "vpc.bandwidth_out" \
  --resource-id "vpc-xxx" \
  --statistics "avg" \
  --comparison-operator ">" \
  --threshold 8000000000 \  # 8 Gbps
  --evaluation-count 3 \
  --period 300               # 5分钟周期
```

## 4. 与其它 skill 的监控集成

| Skill | 交互方式 |
|-------|---------|
| `jdcloud-cloudmonitor-ops` | 主监控 provider,查询所有 VPC 指标 |
| `jdcloud-arch-advisor` | Mode B 采集 VPC 带宽利用率做 Performance 评估 |
| `jdcloud-aiops-cruise` | 全链路巡检时采集 VPC/子网指标 |
| `jdcloud-topo-discovery` | 不采集指标,只采集资源拓扑 |

## 5. 注意事项

- VPC Flow Logs **不免费**,按日志量计费
- Cloud Monitor 指标默认保留 30 天,可延长
- 安全组规则数指标 `sg.active_rule_count` 并非所有地域都支持
- 子网 IP 使用率需通过 `describe-subnet` + `describe-vm` 自行计算