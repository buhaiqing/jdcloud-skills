# 智能降级策略 (Smart Fallback Strategy)

> 本文档从 `SKILL.md` 提取。
> 适用范围: 所有 `jdc-first-with-fallback` 执行路径。
> 详见 [monitor-pitfalls.md](monitor-pitfalls.md) 陷阱 7。

## 核心原则

**不是所有 CLI 错误都值得重试。** 确定性错误（参数解析 bug、认证失败）
重试 3 次只是浪费时间，应立即降级到 SDK。

## 错误分类

| 错误类型 | 可重试？ | 退避策略 | 示例 |
|----------|:------:|----------|------|
| 网络超时 | ✅ 是 | 指数退避 0s/2s/4s | `ConnectionError`, `Timeout` |
| API 限流 | ✅ 是 | 指数退避 2s/4s/8s | `Throttling`, `429` |
| 服务端错误 | ✅ 是 | 固定 2s | `InternalError`, `5xx` |
| **参数解析错误** | **❌ 否** | **立即降级** | `unrecognized arguments`, `ValueError` |
| **认证失败** | **❌ 否** | **HALT** | `InvalidAccessKeyId`, `SignatureDoesNotMatch` |
| **权限不足** | **❌ 否** | **HALT** | `Forbidden.RAM` |

## 执行伪代码

```python
def call_jdc_or_sdk(command, sdk_fn):
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

## CLI Bug 绕过技巧

`jdc_cli==1.2.12` 的 `monitor` 子命令存在已知的参数解析 bug。
使用 `--input-json` 传参可绕过：

```bash
# ❌ 直接传参（可能触发 CLI bug）
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

## SDK 引用陷阱

`jdcloud_sdk` 的 client 模块导出的是 module 而非 class：

```python
# ❌ 错误
from jdcloud_sdk.services.monitor.client import MonitorClient
client = MonitorClient(cred, region)  # TypeError: not callable

# ✅ 正确
from jdcloud_sdk.services.monitor.client import MonitorClient
from jdcloud_sdk.core.config import Config
cfg = Config(endpoint='monitor.jdcloud-api.com', scheme='https', timeout=30)
client = MonitorClient.MonitorClient(cred, region, cfg)
```

## 监控数据静默失败

API 返回 `error: null` + `data: null` 是**静默失败**——表示资源无监控数据
（通常因为未安装云监控 agent），而非 API 调用失败。

**每次查询后必须检查 `data` 字段**：

```python
items = resp.result.get('metricDatas', [])
for item in items:
    if item.get('data') is None:
        print(f"[WARN] {item['metric']['metric']}: 无监控数据（可能未安装 agent）")
        continue
```

## 相关文档

| 文档 | 路径 | 说明 |
|------|------|------|
| 监控陷阱库 | `monitor-pitfalls.md` | 7 个已知陷阱 + 修复模式 |
| 模板安全契约 | `../../jdcloud-topo-discovery/SKILL.md` → Template Safety Contract | 跨 skill 通用约束 |
