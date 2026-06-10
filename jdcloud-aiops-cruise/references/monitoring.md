# Monitoring — jdcloud-aiops-cruise

> 本文定义 `jdcloud-aiops-cruise` Skill 在监控指标采集、阈值判定、告警关联和容量预测方面的规范。
> 所有 `analyzer` 必须遵循本文定义的指标名、聚合方式和判定逻辑。

##1.监控指标采集规范

###1.1指标名约定

> **指标名严格按 JD Cloud 云监控官方定义**。任何自定义命名会导致 `404 Not Found`。

| 服务 |指标名 |单位 | 默认聚合 |用途 |
|---|---|---|---|---|
| vm | `cpu_util` |% | avg | CPU 水位 |
| vm | `memory.usage` |% | avg |内存水位 |
| vm | `vm.disk.dev.io.read` | IOPS | max |读 IOPS瓶颈 |
| vm | `vm.disk.dev.io.write` | IOPS | max |写 IOPS瓶颈 |
| vm | `vm.disk.dev.used` |% | max |磁盘使用率 |
| vm | `vm.avg.load5` | — | avg | 系统负载（5min） |
| vm | `vm.network.dev.bytes.in` | bps | max | 入带宽峰值 |
| vm | `vm.network.dev.bytes.out` | bps | max | 出带宽峰值 |
| vm | `vm.netstat.tcp.established` |个 | avg | TCP活跃连接数 |
| lb | `lb.active_connection_count` |个 | max | CLB 并发连接 |
| lb | `lb.new_connection_count` | 个/秒 | max | CLB 新建连接速率 |
| lb | `lb.backend.healthy.host_count` |个 | min | 健康后端数 |
| redis | `redis.memory.usage` |% | max | Redis内存 |
| redis | `redis.hit_rate` |% | avg | Redis命中率 |
| redis | `redis.connections` |个 | avg | Redis 连接数 |
| redis | `redis.cpu.util` |% | avg | Redis CPU |
| eip | `eip.bandwidth.in` | bps | max | EIP 入带宽 |
| eip | `eip.bandwidth.out` | bps | max | EIP 出带宽 |
| nat | `nat.connections` |个 | max | SNAT 连接数 |
| nat | `nat.bandwidth.in` | bps | max | NAT 入带宽 |
| nat | `nat.bandwidth.out` | bps | max | NAT 出带宽 |
| monitor | `alarmHistory` | — | — |告警历史 |

###1.2 `serviceCode`映射

`monitor.getMetricData` 必须显式传入 `serviceCode`，否则 API 会默认成 `vm` 导致非 VM资源查询失败：

|资源类型 | `serviceCode` |
|---|---|
| VM | `vm` |
| CLB | `lb` |
| Redis | `redis` |
| EIP | `eip` |
| NAT | `nat` |
| ES | `es` |
| RDS（MySQL/PG） | `rds` |
| K8s | `kubernetes` |

> ⚠️ **永远不允许** `serviceCode="vm"`（默认）查询非 VM资源。

###1.3时间窗口与粒度

|场景 | `hours` | `timeInterval` | 点数（估算） |
|---|---|---|---|
|实时告警（runbook02） |1 |1m |60 |
|日常巡检（runbook01） |6 |1h |6 |
|容量规划（runbook03） |168 (7天) |1h |168 |
| 大促预检（runbook04） |720 (30天) |1h |720 |
| MySQL慢查询（runbook05） |24 |1h |24 |
| PostgreSQL巡检（runbook06） |24 |1h |24 |

###1.4请求模板

```bash
# jdc CLI形式（首选）
jdc --output json monitor metric-data \
 --service-code vm \
 --resource-id i-abc123 \
 --metric cpu_util \
 --start-time "2026-06-10T00:00:00Z" \
 --end-time "2026-06-10T06:00:00Z" \
 --time-interval1h \
 --aggr-type avg
```

```python
# jdc_client.py形式（fallback）
from lib.jdc_client import JdcClient
client = JdcClient()
points = client.get_metric(
 resource_id="i-abc123",
 metric="cpu_util",
 hours=6,
 aggr="avg",
 service_code="vm"
) # [(ts_ms, value), ...]
```

---

##2.阈值定义

###2.1通用阈值（来自 `threshold-definitions.md`）

|指标 | Warning | Critical |判定逻辑 |
|---|---:|---:|---|
| CPU 使用率 | >70% | >85% | 取6h 平均 +峰值 |
|内存使用率 | >80% | >90% | 取6h 平均 +峰值 |
|磁盘使用率 | >75% | >90% | 取最近一点 |
| 系统负载 / vCPU | >4.0 | >6.0 | 取6h 平均 |
|环比增长率 | >30% | >50% | 与昨日同期对比 |

###2.2实例规格上限（与水位对比）

|规格 | vCPU |内存(GB) |内网带宽(Gbps) | 最大PPS(万) | 最大连接数 |
|---|---:|---:|---:|---:|---:|
| c.n3.large |2 |4 |1.5 |30 |20万 |
| c.n3.xlarge |4 |8 |3 |50 |40万 |
| c.n3.2xlarge |8 |16 |4 |80 |50万 |
| g.n3.large |2 |8 |1.5 |30 |20万 |
| g.n3.2xlarge |8 |32 |4 |80 |50万 |
| g.n3.4xlarge |16 |64 |8 |120 |80万 |
| m.n2.xlarge |4 |32 |3 |50 |40万 |

###2.3云盘上限

|类型 | IOPS/GB |单盘最大IOPS |吞吐量(MB/s) |
|---|---:|---:|---:|
| ssd.gp1 |20 |10,000 |150 |
| ssd.io1 |50 |50,200 |350 |
| premium |10 |5,000 |100 |

###2.4 CLB规格上限

|规格 |最大并发连接 |最大新建连接/秒 |带宽(Gbps) | Info | Warning |
|---|---:|---:|---:|---:|---:|
| 标准型 |500,000 |50,000 |5 | ≥60% | ≥80% |
| 高性能型 |2,000,000 |100,000 |10 | ≥60% | ≥80% |

###2.5 EIP阈值

|指标 | Info | Warning |行动 |
|---|---:|---:|---|
| 入带宽峰值 / EIP带宽 | ≥50% | ≥80% |关注入口流量 |
| 出带宽峰值 / EIP带宽 | ≥50% | ≥80% |关注出口流量 |
|绑定状态 | 已绑定 | 未绑定 | 未绑定只提示可能闲置 |

###2.6安全规则阈值

|规则 |级别 |判定 |
|---|---|---|
| CIDR = `0.0.0.0/0` AND端口 =22/3389/5432/3306/6379 | Critical | 管理/数据库端口对公网开放 |
| CIDR = `0.0.0.0/0` AND端口 >1024 | Warning | 大范围端口对公网开放 |
| 安全组规则数 >50 | Warning |规则过多 |

---

##3.告警关联

###3.1告警历史查询

```bash
jdc --output json monitor alarm-history \
 --resource-id i-abc123 \
 --start-time "2026-06-10T00:00:00Z" \
 --end-time "2026-06-10T06:00:00Z"
```

返回字段：

```json
{
 "result": {
 "alarmHistoryList": [
 {
 "alarmId": "...",
 "ruleName": "...",
 "metricName": "...",
 "triggerValue":95.0,
 "triggerTime": "2026-06-10T05:30:00Z",
 "resourceId": "i-abc123"
 }
 ]
 }
}
```

###3.2告警 vs监控指标交叉验证

`analyzer.analyze()` 应同时检查：

1. 当前监控指标是否超阈值（实时）
2. 同窗口告警历史是否触发过（历史）

**目的**：避免假阳性 — 例如某时刻峰值 `>85%` 但告警未触发，说明该资源有可能是**已知的临时抖动**；反之亦然（指标正常但告警触发 =阈值设置问题）。

###3.3关联推理（runbook02决策树）

|现象 |推断方向 |
|---|---|
| CLB 健康检查失败 >10% AND VM状态正常 |查 CLB→VM 网络连通性（SG /子网 ACL） |
| VM CPU >70% AND内存 >80% |查进程资源占用，考虑升配或拆分服务 |
| Redis命中率 <90% AND VM CPU正常 |查热 key /大 key /缓存穿透 |
| VM IOPS接近上限 AND磁盘延迟高 |查慢查询，考虑升配云盘或优化查询 |
| 网络带宽 >80% AND 用户报慢 |查流量来源，考虑升配实例或限流 |
| NAT SNAT >80% |查端口耗尽，考虑增加 NAT规格 |
| K8s节点 Pod分配率 >80% |扩容节点组或优化 Pod request |
| 安全规则允许 `0.0.0.0/0`访问 DB端口 | 高危配置，建议限制来源 IP |

---

##4.容量预测

###4.1预测算法

> 默认使用**线性回归（Linear Regression）**，对最近7天或30天的数据点拟合斜率。

```python
import numpy as np
def predict_exhaust(pts, threshold, horizon_days):
 """
 pts: [(ts_ms, value), ...] 时间序列
 threshold:警戒阈值（如磁盘90%）
 horizon_days:预测窗口
 返回:预计到达 threshold 的天数（int）或 None
 """
 if len(pts) <3:
 return None
 xs = np.array([p[0] for p in pts]) /86400_000 # →天
 ys = np.array([p[1] for p in pts])
 slope, intercept = np.polyfit(xs, ys,1)
 if slope <=0:
 return None #下降趋势，永不耗尽
 days_left = (threshold - intercept) / slope
 if days_left > horizon_days:
 return None #超出预测窗口
 return int(days_left)
```

###4.2预测对象

|资源 |指标 |警戒阈值 |预测窗口 |
|---|---|---:|---|
| VM | `vm.disk.dev.used` |90% |30天 |
| VM | `memory.usage` |90% |30天 |
| Redis | `redis.memory.usage` |85% |30天 |
| VM | `vm.disk.dev.io.read` / `write` |80%规格上限 |30天 |
| VM | `vm.network.dev.bytes.in` / `out` |80%规格上限 |30天 |

###4.3容量预测输出

```json
{
 "resource_id": "i-abc123",
 "resource_name": "web-01",
 "metric": "vm.disk.dev.used",
 "current":65.0,
 "trend_per_day":0.5, //每天增长0.5%
 "predicted_exhaustion_days":50,
 "predicted_exhaustion_date": "2026-07-30",
 "warning": "50天后磁盘满，建议30天内扩容"
}
```

###4.4降配建议（成本优化）

> 仅在 `runbooks/03-capacity-planning.md` 中触发，**不在日常巡检中触发**。

|条件 |建议 |
|---|---|
| CPU7天平均 <20% AND内存7天平均 <40% |降配（如 c.n3.2xlarge →c.n3.xlarge） |
|磁盘使用率7天平均 <20% |缩小云盘容量 |
| Redis内存使用率7天平均 <40% |降配 Redis规格 |

---

##5.大促前压力评估（runbook04）

###5.1基线取数

- 取最近30天业务高峰期（10:00-11:00 /14:00-16:00）的指标作为流量基线
- 计算各指标在基线期的**峰值**

###5.23x流量评估

对每个资源检查 `baseline_peak ×3` 是否仍有余量：

| 检查项 |合格阈值 |
|---|---|
| 当前峰值 CPU ×3 | <80% |
| 当前峰值内存 ×3 | <85% |
| 当前峰值 IOPS ×3 | <规格上限80% |
| 当前峰值带宽 ×3 | <规格上限80% |
| 当前峰值 Redis内存 ×3 | <85% |
| 当前峰值 CLB 并发 ×3 | <规格上限80% |
| 当前峰值 NAT SNAT ×3 | <规格上限80% |

###5.3输出

```text
✅ 余量充足
 VM CPU:峰值25% ×3 =75% <80% →合格
磁盘 IOPS:峰值3115 ×3 =9345 <50200 →合格

⚠️建议升配
 CLB 并发:峰值3500 ×3 =10500 >规格上限8000 →建议升配CLB规格
 NAT SNAT:峰值6000 ×3 =18000 >规格上限15000 →建议升配NAT规格
```

> **绝不直接执行升配** — 输出建议，必须由人工通过 `jdcloud-clb-ops` / `jdcloud-nat-ops` 执行。

---

##6.数据存储与最小化

###6.1落盘路径

|文件 |路径 | 内容 |
|---|---|---|
| Phase1 sniff 输出 | `reports/output/sniff-<customer>-<YYYYMMDD-HHMMSS>.json` |拓扑初判 |
| Phase2 cruise 输出 | `reports/output/cruise-<customer>-<YYYYMMDD-HHMMSS>.json` |深度巡检 |
| MySQL慢查询 | `reports/output/mysql-cruise-<customer>-<YYYYMMDD-HHMMSS>.{json,md}` | MySQL巡检 |
| PostgreSQL巡检 | `reports/output/postgresql-cruise-<customer>-<YYYYMMDD-HHMMSS>.{json,md}` | PostgreSQL巡检 |
| GCL audit追踪 | `<repo-root>/audit-results/gcl-trace-<YYYYMMDD-HHMMSS>.json` |跨 skill GCL审计 |

###6.2数据最小化（强制）

`resource_discovery.discover_customer_resources()` 输出必须：

- ✅ 仅含 `客户=<customer>`标签的资源
- ✅ 仅含客户资源关联的 VPC /子网 /安全组
- ❌ **绝不**包含跨客户 /全账号的原始资源清单
- ❌ **绝不**包含未带客户标签的资源（即使临时扫描到）

###6.3敏感信息处理

- `access_key` / `secret_key` /密码 → 显示 `<masked>`
-内部 IP（如 `192.168.x.x`）→允许显示（运维必需）
- 公网 IP（如 EIP）→允许显示（审计必需）

---

##7.监控告警规则协作

###7.1依赖 jdcloud-cloudmonitor-ops

`jdcloud-aiops-cruise` 不创建 / 修改 / 删除告警规则。所有告警规则相关操作委托给 `jdcloud-cloudmonitor-ops`。

###7.2告警规则的"反向"用途

`jdcloud-aiops-cruise` 利用告警规则作为**指标质量的反向校验**：

-触发告警的指标未达阈值 →告警规则阈值设置过低
-指标超阈值但告警未触发 →告警规则阈值设置过高

这些发现应作为 Info级别 finding 输出，提示人工审查告警规则。

---

##8.与 jdcloud-cloudmonitor-ops 的边界

|边界类型 | jdcloud-aiops-cruise | jdcloud-cloudmonitor-ops |
|---|---|---|
|查询指标 | ✅ | ✅ |
| 查询告警历史 | ✅ | ✅ |
| 创建告警规则 | ❌ | ✅ |
| 修改告警规则 | ❌ | ✅ |
|删除告警规则 | ❌ | ✅ |
|启用 /禁用告警 | ❌ | ✅ |
|告警通知渠道 | ❌ | ✅ |

> **硬规则**：本 skill严禁调用告警规则的任何写接口。所有调整必须委托给 `jdcloud-cloudmonitor-ops` 并人工确认。

---

##9.性能与限制

###9.1 API限流

- 默认每资源指标查询间隔 ≥200ms
- 单 analyzer内部串行处理
-失败重试最多3 次（指数退避0s→2s→4s）

###9.2超时

- 单次 API 调用 timeout=30s
- Phase2 总耗时通常5-10 分钟（100 个资源）
-资源数 ≥500 时建议拆分为多次执行

###9.3并发

> **本 skill 默认串行执行**。若未来支持并发，必须遵守：
- 全局并发 ≤5
-同一服务 / API 的并发 ≤2
- 必须有完整的错误隔离（一个资源失败不影响其他）

---

##10. 版本演进

|版本 | 日期 |变更 |
|---|---|---|
|1.5.0 |2026-06-10 | 新增 `monitoring.md` 系统化指标采集 /阈值 /告警关联 /容量预测规范 |
|1.4.0 |2026-06-09 | CLB / EIP指标扩展 |
|1.0.0 |2026-06-06 |初始监控定义 |
