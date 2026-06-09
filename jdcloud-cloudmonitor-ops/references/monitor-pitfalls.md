# 云监控数据采集常见陷阱 (Monitor Pitfalls)

> 本文档记录使用 `jdc monitor` CLI 和 `jdcloud_sdk` SDK 采集监控数据时
> 遇到的真实错误模式，作为后续开发和代码审查的参考。
>
> 每新增一个错误模式，请按下方模板追加。

---

## 陷阱索引

| # | 症状关键词 | 根因类别 | 首次发现 |
|:-:|-----------|----------|----------|
| 1 | `jdc monitor --help` 崩溃 | CLI 参数解析 bug | 2026-06-09 |
| 2 | `--down-sample-type` 不识别 | CLI 参数名不一致 | 2026-06-09 |
| 3 | `MonitorClient` not callable | SDK 模块/类混淆 | 2026-06-09 |
| 4 | `Config` no attribute 'log' | SDK 构造函数签名 | 2026-06-09 |
| 5 | `serviceCode and metric not match` | 指标名前缀规则 | 2026-06-09 |
| 6 | 所有指标返回 `data: null` | 监控 agent 未安装 | 2026-06-09 |
| 7 | 重试 3 次仍失败 | CLI bug 是确定性的 | 2026-06-09 |

---

## 陷阱 1: `jdc monitor` CLI 参数解析崩溃

### 症状

```bash
$ jdc monitor --help
ValueError: unsupported format character 'B' (0x42) at index 87
```

### 根因

`jdc_cli==1.2.12` 的 `monitor` 子命令帮助文本中包含 `%B` 格式字符串，
Python `argparse` 的 `%` 替换逻辑将其误解析为格式化占位符。

### 影响范围

所有 `jdc monitor` 子命令的 `--help` 均受影响。但 `--input-json` 方式
执行实际命令不受影响（不触发帮助文本渲染）。

### 修复

**绕过方式**: 使用 `--input-json` 传参，避免触发 CLI 参数解析：

```bash
# ❌ 直接传参（可能触发 bug）
jdc --output json monitor describe-metric-data \
  --service-code vm --resource-id i-xxx --metric cpu_util ...

# ✅ 使用 --input-json 绕过
jdc --output json monitor describe-metric-data --input-json '{
  "serviceCode": "vm",
  "resourceId": "i-xxx",
  "metric": "vm.cpu_util",
  "startTime": "2026-06-09T00:00:00Z",
  "endTime": "2026-06-09T12:00:00Z",
  "timeInterval": "1h"
}'
```

### 相关

- 本 bug 在 `jdc_cli==1.2.12` 中确认存在
- 升级到更高版本可能修复（待验证）

---

## 陷阱 2: `last-downsample` 参数名不一致

### 症状

```bash
$ jdc monitor last-downsample --down-sample-type last ...
jdc: error: unrecognized arguments: --down-sample-type last
```

### 根因

`jdc monitor last-downsample` 的实际参数名与 SKILL.md 文档中的名称不一致。
CLI 的 `--help` 又因为陷阱 1 无法查看，导致只能试错。

### 修复

**方案 A**: 使用 `describe-metric-data` 替代（推荐）
```bash
jdc --output json monitor describe-metric-data --input-json '{...}'
```

**方案 B**: 降级到 SDK
```python
from jdcloud_sdk.services.monitor.client import MonitorClient
client = MonitorClient.MonitorClient(cred, region, config)
# 使用 DescribeMetricDataRequest
```

### 相关

- `jdcloud-cloudmonitor-ops/SKILL.md` → 操作：查询监控数据

---

## 陷阱 3: SDK `MonitorClient` 是模块不是类

### 症状

```python
from jdcloud_sdk.services.monitor.client import MonitorClient
client = MonitorClient(cred, region)
# TypeError: 'module' object is not callable
```

### 根因

`jdcloud_sdk` 的 `monitor/client.py` 导出了一个 **module**，其中包含
`MonitorClient` 类。正确的引用路径是 `MonitorClient.MonitorClient`。

### 修复

```python
# ❌ 错误
from jdcloud_sdk.services.monitor.client import MonitorClient
client = MonitorClient(cred, region)

# ✅ 正确
from jdcloud_sdk.services.monitor.client import MonitorClient
client = MonitorClient.MonitorClient(cred, region, config)
```

### 通用 SDK 引用模式

| SDK 模块 | 正确引用 |
|----------|----------|
| `monitor.client` | `MonitorClient.MonitorClient(cred, region, config)` |
| `vm.client` | `VmClient.VmClient(cred, region, config)` |
| `vpc.client` | `VpcClient.VpcClient(cred, region, config)` |

---

## 陷阱 4: SDK `Config` 构造函数签名

### 症状

```python
from jdcloud_sdk.core.config import Config
cfg = Config(scheme='https', endpoint='monitor.jdcloud-api.com', timeout=30)
# AttributeError: 'Config' object has no attribute 'log'
```

### 根因

`Config.__init__` 的实际签名是 `(self, endpoint, scheme, timeout)`，
参数顺序与直觉相反（endpoint 在前）。

### 修复

```python
# ❌ 错误顺序
cfg = Config(scheme='https', endpoint='monitor.jdcloud-api.com', timeout=30)

# ✅ 正确顺序
cfg = Config(endpoint='monitor.jdcloud-api.com', scheme='https', timeout=30)
```

### 各产品 endpoint

| 产品 | endpoint |
|------|----------|
| monitor | `monitor.jdcloud-api.com` |
| vm | `vm.jdcloud-api.com` |
| vpc | `vpc.jdcloud-api.com` |
| lb | `lb.jdcloud-api.com` |
| redis | `redis.jdcloud-api.com` |
| rds | `rds.jdcloud-api.com` |

---

## 陷阱 5: 指标名前缀规则

### 症状

```bash
$ jdc monitor describe-metric-data --input-json '{"metric":"cpu_util",...}'
# error: "serviceCode and metric not match"
```

### 根因

不同产品的指标名有不同的前缀规则：

| 产品 | serviceCode | 指标前缀 | 示例 |
|------|:----------:|:--------:|------|
| VM | `vm` | `vm.` | `vm.cpu_util`, `vm.disk.bytes.read` |
| VM (旧) | `vm` | 无前缀 | `cpu_util`, `memory.usage` |
| CLB | `lb` | `network.services.lb.` | `network.services.lb.active.connections` |
| Redis | `redis` | `jmiss.redis.cluster.` 或 `redis_` | `jmiss.redis.cluster.memory_usage` |

### 修复

**始终先用 `describe-metrics` 查询可用指标列表**，确认正确的 metric 名称：

```bash
jdc --output json monitor describe-metrics --service-code vm 2>&1 | \
  python3 -c "import sys,json; [print(m['metric']) for m in json.load(sys.stdin)['result']['metrics']]"
```

### 相关

- `jdcloud-cloudmonitor-ops/SKILL.md` → 操作：查询监控数据

---

## 陷阱 6: 监控数据静默返回 null

### 症状

```json
{
  "result": {
    "metricDatas": [{
      "data": null,
      "metric": {"metric": "vm.cpu_util", "metricName": "CPU使用率"}
    }]
  }
}
```

### 根因

API 调用成功（`error: null`），但 `data` 字段为 `null`。原因：
- VM 未安装云监控 agent
- 时间范围内确实无数据
- 资源刚创建，数据尚未上报

**API 不报错 ≠ 有数据**。这是最常见的静默失败模式。

### 修复

**每次查询后必须检查 `data` 是否非空**：

```python
items = resp.result.get('metricDatas', [])
for item in items:
    data = item.get('data')
    if data is None:
        print(f"[WARN] {item['metric']['metric']}: 无监控数据（可能未安装 agent）")
        continue
    # 处理数据...
```

### 相关

- 建议在查询前先检查告警规则列表，有告警规则 = 大概率有监控数据

---

## 陷阱 7: 确定性 CLI bug 不应重试

### 症状

```
jdc monitor --help → ValueError (重试 3 次，仍然失败)
jdc monitor last-downsample --down-sample-type last → unrecognized arguments (重试 3 次，仍然失败)
```

### 根因

SKILL.md 中的 jdc-first-with-fallback 策略规定"重试 3 次后降级到 SDK"。
但 CLI 参数解析 bug 是**确定性的**（同样的输入永远产生同样的错误），
重试不会修复问题，只会浪费时间。

### 修复

**区分可重试错误和不可重试错误**：

| 错误类型 | 可重试？ | 示例 |
|----------|:------:|------|
| 网络超时 | ✅ 是 | `ConnectionError`, `Timeout` |
| API 限流 | ✅ 是 | `Throttling`, `429` |
| 服务端错误 | ✅ 是 | `InternalError`, `5xx` |
| 参数解析错误 | ❌ 否 | `unrecognized arguments`, `ValueError` |
| 认证失败 | ❌ 否 | `InvalidAccessKeyId`, `SignatureDoesNotMatch` |
| 权限不足 | ❌ 否 | `Forbidden.RAM` |

**建议的快速降级策略**：

```python
def call_jdc_or_sdk(command, sdk_fn):
    """jdc-first with smart fallback."""
    result = run_jdc(command)
    if result.success:
        return result
    
    # 确定性错误 → 立即降级，不重试
    if is_deterministic_error(result.stderr):
        print(f"[INFO] CLI deterministic error, falling back to SDK")
        return sdk_fn()
    
    # 可重试错误 → 重试 3 次
    for i in range(3):
        time.sleep(2 ** i)
        result = run_jdc(command)
        if result.success:
            return result
    
    # 最终降级
    print(f"[INFO] CLI failed after 3 retries, falling back to SDK")
    return sdk_fn()
```

---

## 通用修复模式

### 监控数据采集安全流程

```
1. describe-metrics → 确认指标名
        │
2. describe-alarms → 确认是否有告警规则（间接判断 agent 是否安装）
        │
        ▼
3. describe-metric-data → 拉取数据
        │
        ▼
4. 检查 data != null → 是 → 处理数据
                      → 否 → WARNING + 标记为"无监控"
```

### 代码审查检查点

- [ ] 是否先用 `describe-metrics` 确认了指标名？
- [ ] 是否检查了 `data` 字段非 null？
- [ ] 是否区分了可重试和不可重试的 CLI 错误？
- [ ] SDK 引用是否使用了正确的 `Module.Class` 模式？
- [ ] `Config` 参数顺序是否正确（`endpoint, scheme, timeout`）？
- [ ] 是否处理了"无监控数据"的静默失败？

---

## 变更记录

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-06-09 | 1.0.0 | 初始版本，收录 7 个已知陷阱 |
