# CLI Usage — jdcloud-aiops-cruise

> 本文档描述 `jdcloud-aiops-cruise` Skill 的 CLI 调用规范与脚本调用模式。
> 所有调用必须遵守 `AGENTS.md` 中的 `jdc-first with SDK fallback`策略与CLI禁忌（如 `--no-interactive`）。

##1. 设计原则

`jdcloud-aiops-cruise` 的脚本 **优先使用 `jdc` CLI** 调用 JD Cloud OpenAPI，当 CLI 不支持或连续3 次失败时回退到 Python SDK /自实现 urllib客户端。

```text
┌─────────────────────────────────────────────────────┐
│ jdc --output json <command> (首选) │
│ ↓失败（3 次重试，指数退避0s →2s →4s） │
│ Python SDK (jdcloud_sdk) │
│ ↓ 不支持 /失败 │
│ 自实现 urllib + JDCLOUD3-HMAC-SHA256签名 │
│ (jdc_client.py 内置) │
└─────────────────────────────────────────────────────┘
```

> ⚠️ **本 skill的 `jdc_client.py`已内置 urllib 自签**，是因为 `jdcloud_sdk==1.2.12` 与 Python3.10之外的版本有兼容问题。CLI / SDK / 自签 三条路径同时可用，由调用方按 `jdc-first with SDK fallback`优先级选择。

---

##2.脚本调用入口

###2.1 Phase1:嗅探（Perceive）

```bash
python scripts/01-perceive/cruise_sniff.py \
 --customer烟台振华 \
 [--region cn-north-1 cn-east-2] \
 [--output-dir reports/output]
```

|参数 |必填 |说明 |
|---|---|---|
| `--customer` | ✅ |客户标签值（如 `烟台振华`） |
| `--region` | ❌ |区域列表（空格分隔）；默认扫描所有支持区域 |
| `--output-dir` | ❌ | 输出目录；默认 `reports/output` |

**退出码语义**：

|退出码 |含义 |
|---|---|
|0 | 所有资源自动分类成功（置信度 >0.8），可继续 Phase2 |
|1 |存在需要人工确认的资源（置信度 ≤0.8），等待人工复核 |

###2.2 Phase2:深度分析（Reason）

```bash
python scripts/02-reason/cruise_analyze.py \
 --customer烟台振华 \
 [--sniff-file reports/output/sniff-烟台振华-20260610-063000.json] \
 [--hours6] \
 [--json] \
 [--output-dir reports/output]
```

|参数 |必填 |说明 |
|---|---|---|
| `--customer` | ✅ |客户标签值 |
| `--sniff-file` | ❌ |复用 Phase1 输出；不传则重新执行 sniff |
| `--hours` | ❌ |监控回溯小时数（默认6） |
| `--json` | ❌ | 同时输出 JSON报告 |
| `--output-dir` | ❌ | 输出目录 |

> **历史兼容**：`scripts/02-reason/cruise_link.py` 是 `cruise_analyze.py` 的 thin wrapper，保留旧命令路径兼容。

---

##3. jdc CLI规范（强制）

###3.1 必须遵守的规则

|规则 |错误示例 |正确示例 |
|---|---|---|
|`--output json`放在 `jdc` 后第一个位置 | `jdc vm list --output json` | `jdc --output json vm list` |
| **不要** 使用 `--no-interactive`标志 | `jdc --no-interactive vm delete` | （省略此标志） |
|凭证配置 INI 文件（不是环境变量） | `export JDC_ACCESS_KEY=...` |写入 `~/.jdc/config` INI |
|`~/.jdc/current`末尾无换行 | `echo "default" > file` | `printf "%s" "default" > file` |
|区域参数放末尾 | `jdc --region cn-north-1 vm list` | `jdc vm list --region cn-north-1` |

###3.2凭证处理

**优先级**（高 →低）：

1. `os.environ["JDC_ACCESS_KEY"]` / `["JDC_SECRET_KEY"]`（运行时显式注入）
2. 项目根 `.env` 文件（`jdcloud-skills/.env`）
3. `~/.jdc/config` INI 文件（jdc CLI 要求）

**安全要求**：

- ✅ 仅打印 `<masked>` 表示密钥状态
- ✅ `test -n "$JDC_SECRET_KEY"`（存在性检查）
- ❌严禁 `print` / `echo` / `json.dump` 中出现完整 `SECRET_KEY`

###3.3 本 skill 的 jdc 命令清单

| 服务 |资源 |用途 |典型命令 |
|---|---|---|---|
| vm |主机 |列出客户 VM | `jdc --output json vm list --region cn-north-1` |
| lb |负载均衡 |列出客户 CLB | `jdc --output json lb list --region cn-north-1` |
| redis |缓存 |列出 Redis 实例 | `jdc --output json redis list --region cn-north-1` |
| rds | 数据库 |列出 RDS 实例 | `jdc --output json rds list --region cn-north-1` |
| vpc | 网络 |列出 VPC /子网 /SG | `jdc --output json vpc list --region cn-north-1` |
| eip |弹性 IP |列出 EIP | `jdc --output json vpc list-eip --region cn-north-1` |
| kubernetes |容器 |列出 K8s集群 | `jdc --output json kubernetes list-clusters --region cn-north-1` |
| monitor |监控 | 查询指标 | `jdc --output json monitor metric-data --service-code vm ...` |

---

##4. SDK fallback路径

当 `jdc`不可用 /失败时，回退顺序：

###4.1优先：Python SDK（`jdcloud_sdk`）

```python
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.vm.apis.DescribeInstancesRequest import DescribeInstancesRequest
from jdcloud_sdk.core.const import REGION_CN_NORTH_1

cred = Credential(access_key, secret_key)
client = DescribeInstancesRequest(cred)
client.set_region(REGION_CN_NORTH_1)
resp = client.send()
```

> ⚠️ `jdcloud_sdk==1.2.12`依赖 `SafeConfigParser`（Python3.12 已移除）。建议在 Python3.10 环境运行。

###4.2 最后：自实现 urllib客户端（已内置）

`scripts/lib/jdc_client.py` 已用 `urllib.request` +手动 `JDCLOUD3-HMAC-SHA256`签名实现完整 JD Cloud OpenAPI客户端。它作为 **最终 fallback**，对 SDK 不支持的场景（如自定义监控指标）尤其重要。

**已实现的服务端点**：

```python
SERVICE_ENDPOINTS = {
 "vm": "vm.jdcloud-api.com",
 "lb": "lb.jdcloud-api.com",
 "redis": "redis.jdcloud-api.com",
 "rds": "rds.jdcloud-api.com",
 "vpc": "vpc.jdcloud-api.com",
 "monitor": "monitor.jdcloud-api.com",
 "kubernetes": "kubernetes.jdcloud-api.com",
 "disk": "disk.jdcloud-api.com",
 "es": "es.jdcloud-api.com",
 "nc": "nc.jdcloud-api.com",
}
```

---

##5. 执行策略与重试

###5.1 三次重试（指数退避）

`JdcClient._get()` 内置：

```python
MAX_RETRIES =3
RETRY_BACKOFF = [0,2,4] #秒
```

仅在以下情况重试：

- `5xx` HTTP错误
- `429`限流
- 网络超时 / `URLError`
- `OSError` / DNS失败

**不重试**：

- `4xx`业务错误（400/401/403/404 等） — 直接抛出异常
-签名错误 —视为凭证问题，抛出

###5.2 分页

`JdcClient._paginate()` 自动处理：

- `pageNumber` / `pageSize` 参数
-累计 `totalCount`决定是否继续
- 单页返回结果数 < `pageSize` 时停止
- 默认 `pageSize=100`

---

##6. 输出格式

###6.1 Phase1（sniff）输出

**stdout**：Markdown拓扑预览

**JSON 文件路径**：`reports/output/sniff-<customer>-<YYYYMMDD-HHMMSS>.json`

**关键字段**：

```json
{
 "customer": "烟台振华",
 "regions": ["cn-north-1", "cn-east-2"],
 "raw": {
 "vms": [...], #仅客户标签范围
 "lbs": [...],
 "redis": [...],
 "rds": [...],
 "vpcs": [...], #仅客户资源引用的 VPC
 "subnets": [...],
 "security_groups": [...], #仅客户 VM 引用的 SG
 "eips": [...]
 },
 "topology": {
 "vpcs": {
 "<vpc_id>": {
 "name": "...", "cidr": "...",
 "subnets": [...], "vms": [...],
 "lbs": [...], "redis": [...],
 "rds": [...], "eips": [...]
 }
 }
 },
 "classification": {
 "resources": [{"id":..., "type":..., "mode":..., "confidence":..., "reason":...}],
 "needs_confirmation": [...]
 }
}
```

###6.2 Phase2（analyze）输出

**stdout**：分级 findings（Critical / Warning / Info）

**JSON 文件路径**：`reports/output/cruise-<customer>-<YYYYMMDD-HHMMSS>.json`

**关键字段**：

```json
{
 "customer": "烟台振华",
 "timestamp": "2026-06-10T06:30:00",
 "hours":6,
 "summary": {
 "total_findings":25,
 "critical":3, "warning":12, "info":10
 },
 "service_reports": [...], # 每个 analyzer 的 report
 "all_findings": [...] #全部 finding（带 service字段）
}
```

---

##7.常见问题

###7.1 `ModuleNotFoundError: lib.jdc_client`

**原因**：脚本不在 `scripts/` 下，或 `sys.path.insert` 未正确指向项目根。

**修复**：确认 `cruise_sniff.py` / `cruise_analyze.py` 中有：

```python
_scripts_dir = os.path.dirname(os.path.abspath(__file__))
_project_dir = os.path.join(_scripts_dir, "..") #对于01-perceive/、02-reason/
# analyzers/ 子目录则要..两次
sys.path.insert(0, _project_dir)
```

###7.2 `jdc: command not found`

**修复**：通过 `pip install jdcloud_cli` 或 `uv pip install jdcloud_cli` 安装 jdc CLI。

###7.3 `ImportError: SafeConfigParser`

**原因**：Python ≥3.12移除了 `configparser.SafeConfigParser`，但 `jdcloud_cli==1.2.12`仍在引用。

**修复**：使用 Python3.10 环境（`uv venv --python3.10`）。

###7.4凭证缺失

```text
RuntimeError: No JD Cloud credentials. Set JDC_ACCESS_KEY / JDC_SECRET_KEY
```

**修复**：

1. 在 `jdcloud-skills/.env` 中写入 `JDC_ACCESS_KEY=xxx` / `JDC_SECRET_KEY=yyy`
2. 或通过 `jdc config init`写入 `~/.jdc/config`

###7.5跨账号 /全账号资源泄露

**修复**：检查 `resource_discovery.discover_customer_resources()` 中是否将 `raw`字典的 `vms / lbs / redis / rds / eips / vpcs / subnets / security_groups` 都覆盖为 `customer_*`列表（数据最小化）。

---

##8. 安全门（Safety Gates）速查

|风险动作 |严禁通过本 skill执行 | 必须委托 |
|---|---|---|
| 删除 VM / CLB / EIP / RDS / Redis | ❌ | `jdcloud-vm-ops` 等 |
|停止 / 重启 VM | ❌ | `jdcloud-vm-ops` |
|升配 /降配实例规格 | ❌ | `jdcloud-vm-ops` |
|释放 /绑定 EIP | ❌ | `jdcloud-eip-ops` |
|调整 NAT 网关规格 | ❌ | `jdcloud-nat-ops` |
|调整 CLB监听器 | ❌ | `jdcloud-clb-ops` |
| 注册 /摘除 CLB 后端 | ❌ | `jdcloud-clb-ops` |
| 创建 / 删除索引（DDL） | ❌ | `jdcloud-mysql-ops` |
| VACUUM FULL / ANALYZE | ❌ | `jdcloud-postgresql-ops` |
| 修改 / 删除告警规则 | ❌ | `jdcloud-cloudmonitor-ops` |

> **任何上述动作通过本 skill执行 → Safety =0 → GCL ABORT**。
