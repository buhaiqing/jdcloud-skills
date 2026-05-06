# JD Cloud 云监控(CloudMonitor) Quick Start

## 目录

1. [概述](#概述)
2. [环境准备](#环境准备)
3. [核心概念速览](#核心概念速览)
4. [提示词教程](#提示词教程)
5. [附录：CLI 命令参考](#附录：cli 命令参考)
6. [故障排查](#故障排查)

---

## 概述

本教程将从零开始指导你如何使用 **JD Cloud 云监控(CloudMonitor)运维 Skill**。通过本教程，你将学会：

- 使用 `.env` 文件配置云监控环境
- 通过**自然语言提示词**查询监控指标、创建告警规则
- 查看告警历史、上报自定义监控数据
- （进阶）使用 CLI 命令和 Python SDK 进行高级操作

> 💡 **使用方式**: 将下方**提示词教程**中的任意提示词发给 AI Agent 即可执行。无需记忆 CLI 命令。

**预计学习时间**：10-15 分钟

---

## 环境准备

### 1. 安装 JD Cloud CLI

**推荐：使用 uv（幂等且可重现）**

```bash
# 安装 uv（一次性系统设置）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建隔离环境并安装（幂等，可重复执行）
uv venv --python 3.10
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install jdcloud_cli

# 验证安装
jdc --version
```

**备选：使用 pip**

```bash
pip install jdcloud_cli
jdc --version
```

### 2. 配置凭证

凭证配置支持三种方式，按优先级排序：**Shell 环境变量 > `.env` 文件 > 交互式配置**

**方式一：`.env` 文件（本地开发推荐）**

Agent Runtime 会自动加载项目根目录下的 `.env` 文件，无需手动加载。

```bash
# 1. 创建 .env 文件（项目根目录）
cat > .env << 'EOF'
JDC_ACCESS_KEY=your_access_key_here
JDC_SECRET_KEY=your_secret_key_here
JDC_REGION=cn-north-1
EOF

# 2. 确保 .gitignore 包含 .env（防止提交到版本控制）
echo ".env" >> .gitignore

# 3. 验证文件权限（仅所有者可读写）
chmod 600 .env
```

> ⚠️ **安全警告**: 切勿将 `.env` 文件提交到代码仓库！`.env` 包含敏感凭证信息，必须在 `.gitignore` 中排除。

**方式二：Shell 环境变量（优先级更高，可覆盖 `.env`）**

当 `.env` 文件和 Shell 环境变量同时存在时，Shell 环境变量优先生效：

```bash
export JDC_ACCESS_KEY="your_access_key_here"
export JDC_SECRET_KEY="your_secret_key_here"
export JDC_REGION="cn-north-1"
```

> 💡 **使用场景**: 生产环境建议使用 Shell 环境变量或密钥管理服务，避免凭证文件泄露。

**方式三：交互式配置**

```bash
jdc config init
# 按提示输入 Access Key、Secret Key 和默认区域
```

**凭证优先级说明**：

| 优先级 | 配置方式 | 说明 |
|--------|----------|------|
| 1 | Shell 环境变量 | 最高优先级，会覆盖其他配置 |
| 2 | `.env` 文件 | Agent Runtime 自动加载 |
| 3 | `jdc config` | CLI 本地配置 |

### 3. 验证配置

```bash
# 验证 CLI 配置是否正确
jdc monitor describe-services --region-id cn-north-1 --output json

# 预期输出：返回服务列表 JSON
```

### 4. 安装 Python SDK（可选，用于复杂自动化）

**使用 uv（推荐）**

```bash
# 确保已激活 uv 环境
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install jdcloud_sdk
```

**使用 pip**

```bash
pip install jdcloud_sdk
```

---

### 5. 快速验证 .env 配置（可选）

创建 `verify_config.py` 脚本验证凭证：

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.core.config import Config
from jdcloud_sdk.services.monitor.client import MonitorClient
from jdcloud_sdk.core.exception import ClientException, ServerException

access_key = os.environ.get('JDC_ACCESS_KEY')
secret_key = os.environ.get('JDC_SECRET_KEY')
region = os.environ.get('JDC_REGION', 'cn-north-1')

if not access_key or not secret_key:
    print("错误：请配置 JDC_ACCESS_KEY 和 JDC_SECRET_KEY")
    print("方式 1: 创建 .env 文件 → Agent Runtime 自动加载")
    print("方式 2: source .env && python verify_config.py")
    exit(1)

credential = Credential(access_key, secret_key)
config = Config(timeout=30)
client = MonitorClient(config, credential, region)

try:
    result = client.describe_services()
    print(f"✅ 配置成功！区域 {region}，服务数：{len(result.result)}")
except ClientException as e:
    print(f"❌ 客户端错误 ({e.status}): {e.message}")
except ServerException as e:
    print(f"❌ 服务端错误 ({e.status}): {e.message}")
except Exception as e:
    print(f"❌ 未知错误: {e}")
```

运行验证：

```bash
# 1. 确保 .env 文件存在
cat .env

# 2. 方式 A：加载 .env 后运行（手动场景）
source .env && python verify_config.py

# 3. 方式 B：Agent Runtime 自动加载 .env，直接运行即可
python verify_config.py
```

> 💡 **提示**: 对于大部分 CLI 命令，使用 `jdc <command> --help` 可查看所有可用参数。

---

## 核心概念速览

在开始操作之前，你需要了解以下核心概念：

| 概念 | 说明 | 示例 |
|------|------|------|
| **Service（服务）** | 可监控的云产品 | vm（云主机）、rds（云数据库）、disk（云硬盘） |
| **Metric（监控项）** | 具体监控指标 | vm.cpu.util（CPU使用率）、vm.memory.util（内存使用率） |
| **ResourceId（资源ID）** | 被监控的资源标识 | i-xxxxxxxx、disk-xxxxxxxx |
| **Alarm（告警规则）** | 监控条件 + 通知规则 | CPU > 90% 时发送短信 |
| **Period（统计周期）** | 数据聚合时间窗口 | 60秒、300秒 |

### 常用服务代码

| 服务代码 | 云产品 |
|---------|--------|
| vm | 云主机 |
| rds | 云数据库 MySQL |
| disk | 云硬盘 |
| lb / nlb / alb | 负载均衡 |
| redis | 分布式缓存 |
| elasticsearch | 云搜索 |

### 常用监控项

| 监控项 | 说明 | 单位 |
|--------|------|------|
| vm.cpu.util | CPU 使用率 | % |
| vm.memory.util | 内存使用率 | % |
| vm.disk.util | 磁盘使用率 | % |
| vm.network.in | 网络入流量 | bps |
| vm.network.out | 网络出流量 | bps |
| rds.cpu.util | RDS CPU 使用率 | % |
| rds.connection.util | RDS 连接数使用率 | % |

---

## 提示词教程

以下提示词可直接发给 AI Agent 执行。**无需记忆 CLI 命令，说人话即可**。

### 基础操作

#### 查询监控数据

```
查询京东云 cn-north-1 区域云主机实例 i-xxxxxxxx 的 CPU 和内存使用率最近 24 小时的数据
```

> 支持多实例批量查询、指定时间范围、指定聚合方式（avg / max / min）。

#### 查询可用监控项

```
查询京东云 cn-north-1 区域云主机 i-xxxxxxxx 支持的所有监控项，并以表格形式输出
```

#### 查询最新监控快照

```
查询京东云 cn-north-1 区域云主机 i-xxxxxxxx 的最新 CPU、内存、磁盘和网络监控数据
```

#### 创建告警规则

```
为京东云 cn-north-1 区域的云主机 i-xxxxxxxx 创建告警规则：
- 告警名称：生产环境-CPU告警
- 监控项：CPU 使用率
- 阈值：80%
- 统计周期：5分钟
- 连续 2 个周期超阈值触发
- 通知方式：短信+邮件
```

> 支持磁盘告警、内存告警等，只需替换监控项名称和阈值。

#### 查看告警详情

```
查看京东云告警规则 alarm-xxxxxxxx 的详细信息，包括当前状态、触发条件和通知设置
```

#### 查看告警历史

```
查询京东云 cn-north-1 区域过去 7 天内所有触发的告警，统计告警最多的资源
```

#### 删除告警规则

```
删除京东云告警规则 alarm-xxxxxxxx，确认操作后立即执行
```

#### 上报自定义监控数据

```
为订单服务配置自定义监控：
1. 上报订单数量指标到京东云监控（命名空间 custom.business，指标名 order.count）
2. 创建告警：订单数 < 100/分钟 持续 5 分钟触发通知
3. 查询最近 1 小时的订单量数据
```

---

### 综合场景

#### 场景 A：云主机日常巡检

```
对京东云 cn-north-1 区域的所有云主机进行监控巡检，查询每个实例的 CPU、内存、磁盘使用率，
找出资源使用率超过 80% 的实例，并给出优化建议
```

**预期输出**：各资源使用率表格、异常资源列表、优化建议

#### 场景 B：数据库性能分析

```
分析京东云 cn-north-1 区域 RDS 实例 rds-xxxxxxxx 的性能：
1. 查询最近 24 小时的 CPU、内存、连接数、磁盘使用率
2. 找出性能瓶颈
3. 给出优化建议
```

**预期输出**：性能指标趋势、瓶颈分析、优化建议

#### 场景 C：告警规则批量配置

```
为京东云 cn-north-1 区域所有带 tag env=prod 的云主机创建 CPU 告警：
- CPU 使用率 > 80% 持续 5 分钟触发
- 通知方式：短信
- 告警名称格式：生产环境-CPU-{instance_id}
```

---

## 附录：CLI 命令参考

> 以下为底层 CLI 命令，供需要手动执行或调试时参考。日常使用建议直接使用上方的**提示词教程**。

### 查询监控服务列表

```bash
jdc monitor describe-services --region-id cn-north-1 --output json
```

### 查询可用监控项

```bash
jdc monitor describe-metrics \
  --region-id cn-north-1 \
  --service-code vm \
  --resource-id i-xxxxxxxx \
  --output json
```

### 查询监控数据

```bash
jdc monitor describe-metric-data \
  --region-id cn-north-1 \
  --metric vm.cpu.util \
  --service-code vm \
  --resource-id i-xxxxxxxx \
  --start-time "2025-07-01T00:00:00+08:00" \
  --end-time "2025-07-01T12:00:00+08:00" \
  --aggr-type avg \
  --output json
```

### 创建告警规则

```bash
jdc monitor create-alarm \
  --region-id cn-north-1 \
  --alarm-name "VM-CPU-High-Alarm" \
  --service-code vm \
  --resource-id i-xxxxxxxx \
  --metric-name vm.cpu.util \
  --comparison-operator gt \
  --threshold 80 \
  --period 300 \
  --evaluation-periods 2 \
  --contact-group-id 1 \
  --notice-type "sms,email" \
  --output json \
  --no-interactive
```

### 查看告警

```bash
# 查询告警列表
jdc monitor describe-alarms \
  --region-id cn-north-1 \
  --service-code vm \
  --output json

# 查看告警详情
jdc monitor describe-alarm \
  --region-id cn-north-1 \
  --alarm-id alarm-xxxxxxxx \
  --output json
```

### 查看告警历史

```bash
jdc monitor describe-alarm-history \
  --region-id cn-north-1 \
  --alarm-id alarm-xxxxxxxx \
  --start-time "2025-06-25T00:00:00+08:00" \
  --end-time "2025-07-01T23:59:59+08:00" \
  --output json
```

### 上报自定义监控数据

```bash
jdc monitor put-metric-data \
  --region-id cn-north-1 \
  --namespace "custom.business" \
  --metric-name "order.count" \
  --value 100 \
  --dimensions '{"service":"order-api"}' \
  --unit Count \
  --output json
```

---

## 故障排查

### 问题 1：CLI 命令返回空结果

**可能原因**：
- 资源 ID 不存在
- 时间范围内无数据
- 查询参数错误

**排查步骤**：
```bash
# 1. 验证资源是否存在
jdc vm describe-instances --region-id cn-north-1 --instance-ids '["i-xxxxxxxx"]' --output json

# 2. 验证监控项名称是否正确
jdc monitor describe-metrics --region-id cn-north-1 --service-code vm --resource-id i-xxxxxxxx --output json
```

---

### 问题 2：告警未触发

**可能原因**：
- 监控数据未上报
- 阈值设置不合理
- 告警被禁用

**排查步骤**：
```bash
# 1. 检查告警状态
jdc monitor describe-alarm --region-id cn-north-1 --alarm-id alarm-xxxxxxxx --output json

# 2. 检查告警是否启用
# 3. 验证监控数据是否存在
```

---

### 问题 3：凭证验证失败

**可能原因**：
- `.env` 文件未创建或路径不正确
- Shell 环境变量未设置
- Access Key / Secret Key 错误
- 凭证权限不足

**排查步骤**：
```bash
# 1. 检查 .env 文件是否存在
cat .env

# 2. 检查环境变量（Shell 变量会覆盖 .env）
echo $JDC_ACCESS_KEY
echo $JDC_SECRET_KEY

# 3. 验证 .env 文件格式是否正确（不能有引号）
# 正确格式：JDC_ACCESS_KEY=your_key_here
# 错误格式：JDC_ACCESS_KEY="your_key_here"  ❌

# 4. 如果使用交互式配置，重新配置
jdc config init
```

**常见 `.env` 文件错误**：

| 错误 | 说明 | 正确写法 |
|------|------|----------|
| 带引号 | 值被引号包裹 | `JDC_ACCESS_KEY=xxx` |
| 空格 | 等号两边有空格 | `JDC_ACCESS_KEY=xxx` |
| 注释 | 注释在行尾 | `JDC_ACCESS_KEY=xxx  # 注释` |

---

### 问题 4：权限不足错误 (403)

**可能原因**：
- 当前凭证没有访问指定资源的权限
- IAM 策略未正确配置

**排查步骤**：
```bash
# 1. 检查错误信息
jdc monitor describe-alarms --region-id cn-north-1 --service-code vm --output json

# 2. 验证凭证权限
# 登录京东云控制台 → IAM → 检查密钥权限策略
```

---

### 问题 5：请求频率超限 (429)

**可能原因**：
- API 调用频率超过配额限制
- 短时间内请求过于频繁

**排查步骤**：
```bash
# 1. 降低请求频率，避免短时间内大量调用
# 2. 使用缓存减少重复查询
# 3. 联系客服申请提高配额限制
```

---

### 问题 6：网络连接超时

**可能原因**：
- 网络不稳定或防火墙阻断
- 京东云服务不可用

**排查步骤**：
```bash
# 1. 检查网络连接
ping jdcloud.com

# 2. 检查代理设置（如果使用代理）
echo $HTTP_PROXY
echo $HTTPS_PROXY

# 3. 重试操作
jdc monitor describe-services --region-id cn-north-1 --output json
```

---

## 进阶学习

- [核心概念详解](jdcloud-cloudmonitor-ops/references/core-concepts.md) - 深入理解云监控各项功能
- [CLI 使用指南](jdcloud-cloudmonitor-ops/references/cli-usage.md) - 完整的 CLI 命令参考
- [API & SDK 参考](jdcloud-cloudmonitor-ops/references/api-sdk-usage.md) - SDK 方法与 API 字段说明
- [监控最佳实践](jdcloud-cloudmonitor-ops/references/monitoring.md) - 监控配置最佳实践
- [故障排查指南](jdcloud-cloudmonitor-ops/references/troubleshooting.md) - 常见问题解决方案

---

## 相关资源

- [京东云监控官方文档](https://docs.jdcloud.com/cn/monitoring/)
- [京东云 CLI 文档](https://docs.jdcloud.com/cn/cli/)
- [京东云 SDK GitHub](https://github.com/jdcloud-api)
