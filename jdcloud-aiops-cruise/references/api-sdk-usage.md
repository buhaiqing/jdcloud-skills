# API / SDK Usage — jdcloud-aiops-cruise

> 本文描述 `jdcloud-aiops-cruise` Skill 在不同场景下的 API 与 SDK 调用模式。
> 服务端点、签名机制、错误处理、限流策略与 `cli-usage.md`互补。

##1. 调用策略概览

本 skill严格遵守仓库级 `jdc-first with SDK fallback`策略：

```text
┌──────────────────────────────────────────────────────────┐
│优先级1: jdc CLI (jdc --output json <command>) │
│ ↓3 次重试（指数退避0s→2s→4s） │
│优先级2: jdcloud_sdk Python SDK │
│ ↓ 不支持 /失败 │
│优先级3: jdc_client.py 内置 urllib 自签客户端 │
└──────────────────────────────────────────────────────────┘
```

> **jdc CLI 必须放在第一位**：所有巡检脚本能直接用 `jdc --output json`完成的，绝不绕到 SDK 或自签客户端。

---

##2.服务端点矩阵

###2.1资源列表类 API（只读）

|资源 | HTTP |路径 | 结果 JSON字段 |
|---|---|---|---|
| VM | GET | `/v1/regions/{r}/instances` | `result.instances[]` |
| LB（CLB） | GET | `/v1/regions/{r}/loadBalancers` | `result.loadBalancers[]` |
| Redis | GET | `/v1/regions/{r}/cacheInstance` | `result.cacheInstances[]` |
| RDS（MySQL+PG） | GET | `/v1/regions/{r}/instances` | `result.dbInstances[]` |
| VPC | GET | `/v1/regions/{r}/vpcs` | `result.vpcs[]` |
| Subnet | GET | `/v1/regions/{r}/subnets` | `result.subnets[]` |
| Security Group | GET | `/v1/regions/{r}/securityGroups` | `result.securityGroups[]` |
| EIP | GET | `/v1/regions/{r}/elasticIps` | `result.elasticIps[]` |
| K8s Cluster | GET | `/v1/regions/{r}/clusters` | `result.clusters[]` |
| Disk | GET | `/v1/regions/{r}/disks` | `result.disks[]` |
| ES | GET | `/v1/regions/{r}/instances` | `result.instances[]` |
| NAT | GET | `/v1/regions/{r}/natGateways` | `result.natGateways[]` |

###2.2监控指标查询 API

|指标 |服务 |路径 |请求参数 |
|---|---|---|---|
| VM CPU | `vm` | `/v2/regions/{r}/metrics/{metric}/metricData` | `serviceCode=vm&resourceId=i-xxx&startTime=...&endTime=...&timeInterval=1h` |
| CLB 连接 | `lb` | `/v2/regions/{r}/metrics/lb.active_connection_count/metricData` | `serviceCode=lb&resourceId=lb-xxx` |
| Redis内存 | `redis` | `/v2/regions/{r}/metrics/redis.memory.usage/metricData` | `serviceCode=redis&resourceId=redis-xxx` |
| EIP带宽 | `eip` | `/v2/regions/{r}/metrics/eip.bandwidth.in/metricData` | `serviceCode=eip` |
| NAT 连接 | `nat` | `/v2/regions/{r}/metrics/nat.connections/metricData` | `serviceCode=nat` |
|告警历史 | `monitor` | `/v1/regions/{r}/alarmHistory` | `resourceId=...` |

>监控 API 的 `serviceCode` 必须显式传入（`vm` / `lb` / `redis` / `eip` / `nat`），绝不允许默认成 `vm`。

###2.3 已实现的客户端方法

`scripts/lib/jdc_client.py` 的 `JdcClient` 类已封装：

| 方法 |用途 |
|---|---|
| `list_vms(region, tag_key, tag_value)` | 列 VM并按标签过滤 |
| `list_lbs(region)` | 列 CLB |
| `list_redis(region)` | 列 Redis |
| `list_rds(region)` | 列 RDS（MySQL+PG 不分） |
| `list_vpcs(region)` | 列 VPC |
| `list_subnets(region)` | 列子网 |
| `list_security_groups(region)` | 列安全组 |
| `list_clusters(region)` | 列 K8s集群 |
| `list_disks(region)` | 列云盘 |
| `list_es(region)` | 列 ES |
| `list_eips(region)` | 列 EIP |
| `get_metric(resource_id, metric, hours, aggr, region, service_code)` | 单指标查询 |
| `get_metrics_batch(resource_id, [metrics], ...)` |批量指标查询 |
| `get_alarm_history(resource_id, hours, region)` |告警历史 |

---

##3.签名机制（自签客户端）

`jdc_client.py` 已实现完整的 `JDCLOUD3-HMAC-SHA256`签名（与 `jdcloud_sdk` 完全兼容）：

```text
kDate = HMAC("JDCLOUD3" + sk, date_stamp)
kRegion = HMAC(kDate, region)
kService = HMAC(kRegion, service)
kSigning = HMAC(kService, "jdcloud3_request")
```

**签名头字段**：

```text
Authorization: JDCLOUD3-HMAC-SHA256 Credential={ak}/{cred_scope},
 SignedHeaders=content-type;host,
 Signature={signature}
x-jdcloud-date:20260610T063000Z
x-jdcloud-content-sha256: <sha256_hex>
x-jdcloud-nonce: <16字节随机 hex>
```

> **Credential Scope规则**：当 URI 含 `/regions/{id}/` 时用真实 region；否则用通用占位 `jdcloud-api`。

---

##4.错误处理策略

###4.1 HTTP错误

|错误码 |动作 |
|---|---|
| `400` |立即抛出（业务错误，重试无意义） |
| `401` / `403` |立即抛出（凭证问题） |
| `404` |立即抛出（资源不存在） |
| `429` |退避后重试 |
| `5xx` |退避后重试 |
| 网络错误 / `URLError` |退避后重试 |

###4.2业务错误响应

```json
{
 "error": {
 "code":400,
 "message": "InvalidParameter"
 }
}
```

- `4xx`业务错误（除 `429` 外） →抛出 `RuntimeError`
- `5xx`业务错误 →退避后重试

###4.3限流保护

- 默认 `MAX_RETRIES=3`，`RETRY_BACKOFF=[0,2,4]` 秒
-监控 API 调用建议 **每资源间隔 ≥200ms**（避免触发 `429`）
- Phase2 analyzer内部串行处理，无需额外限流
- 如发现持续 `429`，应减少 `--hours`窗口或拆分多次执行

---

##5. 分页与游标

###5.1 默认分页参数

|参数 |值 |
|---|---|
| `pageNumber` |1（递增） |
| `pageSize` |100（默认） |

###5.2终止条件（任一满足即停）

- 返回 `items` 为空
-累计返回数 ≥ `totalCount`
- 单页返回数 < `pageSize`

###5.3资源量估算

>经验值：单个客户标签下通常50-200 个资源。扫描所有区域所有产品最多需要 ~30次 list 调用 + ~10分钟 timeout。

---

##6.标签过滤

###6.1客户端过滤（推荐）

`JdcClient.list_vms(tag_key="客户", tag_value="烟台振华")`内部在拿到全量 VM 后做客户端过滤。

**优势**：对 API 不一致（不同产品的 `tags`字段格式略有差异）更鲁棒。

###6.2 服务端过滤

部分 API 支持 `filters` 参数（如 RDS 支持）。但因各产品支持度不一致，本 skill统一采用客户端过滤。

###6.3工具函数

```python
from lib.jdc_client import filter_by_tag, get_tag, tag_dict

#列表过滤
vms = filter_by_tag(all_vms, "客户", "烟台振华")

# 单个标签读取
env = get_tag(vm, "环境") # "production" / None

#完整标签字典
tags = tag_dict(vm) # {"客户": "烟台振华", "环境": "production"}
```

---

##7.监控指标聚合模式

###7.1 时间窗口

|场景 |`--hours` |`timeInterval` |点数（估算） |
|---|---|---|---|
|实时告警排查 |1 |1m |60 |
|日常巡检（默认） |6 |1h |6 |
|容量规划（runbook03） |168 (7天) |1h |168 |
| 大促预检（runbook04） |720 (30天) |1h |720 |

###7.2聚合函数

| `aggr` |用途 |
|---|---|
| `avg` | 平均值（默认，用于容量评估） |
| `max` |峰值（用于规格上限对比） |
| `min` |谷值（用于低利用率识别） |

###7.3指标名（按服务）

| 服务 |指标名 |
|---|---|
| VM | `cpu_util` / `memory.usage` / `vm.disk.dev.io.read` / `vm.disk.dev.io.write` / `vm.disk.dev.used` / `vm.avg.load5` / `vm.network.dev.bytes.in` / `vm.network.dev.bytes.out` / `vm.netstat.tcp.established` |
| CLB | `lb.active_connection_count` / `lb.new_connection_count` / `lb.backend.healthy.host_count` |
| Redis | `redis.memory.usage` / `redis.hit_rate` / `redis.connections` / `redis.cpu.util` |
| EIP | `eip.bandwidth.in` / `eip.bandwidth.out` |
| NAT | `nat.connections` / `nat.bandwidth.in` / `nat.bandwidth.out` |
| ES | `cpu_util` / `memory.usage` / `vm.disk.dev.used` |

>指标名严格按 `references/threshold-definitions.md` 的定义。

---

##8. SDK 调用示例（fallback路径）

###8.1 jdcloud_sdk VM列表

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.vm.apis.DescribeInstancesRequest import DescribeInstancesRequest
from jdcloud_sdk.services.vm.models.DescribeInstancesFilter import DescribeInstancesFilter
from jdcloud_sdk.core.const import REGION_CN_NORTH_1

cred = Credential(os.environ["JDC_ACCESS_KEY"], os.environ["JDC_SECRET_KEY"])
req = DescribeInstancesRequest(cred)
req.set_region(REGION_CN_NORTH_1)
req.set_pageNumber(1)
req.set_pageSize(50)

resp = req.send()
instances = resp.result.instances
```

###8.2 jdcloud_sdk监控指标

```python
from jdcloud_sdk.services.monitor.apis.DescribeMetricDataRequest import DescribeMetricDataRequest

req = DescribeMetricDataRequest(cred)
req.set_region(REGION_CN_NORTH_1)
req.set_serviceCode("vm")
req.set_resourceId("i-abc123")
req.set_metric("cpu_util")
req.set_startTime("2026-06-10T00:00:00Z")
req.set_endTime("2026-06-10T06:00:00Z")
req.set_timeInterval("1h")
req.set_aggrType("avg")

resp = req.send()
md_list = resp.result.metricDatas
```

> ⚠️ `jdcloud_sdk==1.2.12` 要求 Python3.10。Python3.12+会 `ImportError`。

---

##9. 自签 urllib调用示例

当 jdc / SDK 均不可用时，回退到 `JdcClient`：

```python
from lib.jdc_client import JdcClient

client = JdcClient() #自动从 env / .env读取凭证
vms = client.list_vms(region="cn-north-1")

#批量指标
metrics = client.get_metrics_batch(
 resource_id="i-abc123",
 metrics=["cpu_util", "memory.usage"],
 hours=6,
 service_code="vm"
)

#告警历史
alarms = client.get_alarm_history(resource_id="i-abc123", hours=24)
```

---

##10. 调用安全约束

###10.1凭证最小化

- 仅使用 **只读权限** 的 `JDC_ACCESS_KEY`
- 不要使用主账号凭证，建议使用 `jdcloud-iam-ops` 创建的子账号 `AccessKey`
- 子账号至少需要以下权限：
 - `vm:DescribeInstances`
 - `lb:DescribeLoadBalancers`
 - `redis:DescribeCacheInstances`
 - `rds:DescribeDBInstances`
 - `vpc:DescribeVpcs` / `DescribeSubnets` / `DescribeSecurityGroups` / `DescribeElasticIps`
 - `kubernetes:DescribeClusters`
 - `monitor:GetMetricData` / `DescribeAlarmHistory`

###10.2区域范围

- Phase1 必须扫描所有支持区域（`cn-north-1` / `cn-east-2` / `cn-south-1` / `cn-east-1`）
- 不要假设资源在某特定区域；通过 `--region`显式传入

###10.3限流控制

- 每个 analyzer串行处理（避免并发触发 `429`）
- 单个资源指标查询间隔 ≥200ms
-失败重试最多3 次（指数退避）

###10.4错误日志规范

- ✅错误信息中允许出现 resource_id / metric name / region
- ❌错误信息中禁止出现完整 `SECRET_KEY`
- ❌错误信息中禁止出现跨客户 / 全账号的原始资源清单（即使是 debug 日志）

---

##11.性能基准

> 在 cn-north-1、100 个资源、6 小时窗口的典型场景下：

|阶段 | 调用次数 |耗时 |
|---|---|---|
| Phase1 sniff | ~10 (跨产品 list) |30-60s |
| Phase2 analyze (10个 analyzer) | ~100 (指标批量查询) |5-10分钟 |
| 总计 | ~110 |6-12分钟 |

> 当资源数 ≥500 时，建议拆分为多次执行（按 VPC 或子网拆分），避免单次 timeout。
