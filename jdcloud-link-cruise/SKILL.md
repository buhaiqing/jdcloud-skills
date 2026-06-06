---
name: "jdcloud-link-cruise"
version: "1.0.0"
metadata:
  description: "JD Cloud 全链路巡检 Skill — 覆盖 EIP/CLB/VM/K8s/Redis/NAT/安全组的自动拓扑发现与深度诊断"
  cli_applicability: "partial"
  cli_version_locked: false
  sdk_version_locked: false
---

# JD Cloud 全链路巡检

## Trigger & Scope

### SHOULD Use

- 需要对指定客户（按标签）的 JD Cloud 资源做全链路健康检查时
- 需要排查故障根因时（从 CLB 入口到后端数据库的整条链路）
- 需要做容量规划或大促前预检时
- 需要了解某个客户的 JD Cloud 资源拓扑结构时

### SHOULD NOT Use

- 只查单一资源（如单台 VM）→ 使用 `jdcloud-vm-ops`
- 需要修改/变更资源 → 使用对应产品的 ops skill
- 不涉及 JD Cloud 资源的巡检 → 不使用

### Cross-Skill Delegation

| 需求 | 委托 |
|---|---|
| VM 创建/停止/删除 | `jdcloud-vm-ops` |
| Redis 实例 CRUD | `jdcloud-redis-ops` |
| 监控告警规则变更 | `jdcloud-cloudmonitor-ops` |
| IAM/权限管理 | `jdcloud-iam-ops` |

## Variable Convention

| 类型 | 说明 | 示例 |
|---|---|---|
| `{{env.*}}` | 运行时环境变量，不提示用户 | `{{env.JDC_ACCESS_KEY}}` |
| `{{user.*}}` | 每次巡检时询问用户 | `{{user.customer_name}}` |
| `{{output.*}}` | 脚本解析输出 | `{{output.topology}}` |

## Execution Flow

### Phase 1: 嗅探（cruise_sniff.py）

1. **Pre-flight**: 读取 runbook 配置，解析阈值
2. **Discover**: 扫描客户标签下的 EIP/CLB/VM/Redis/NAT/K8s/安全组
3. **Classify**: 按标签置信度分类部署模式（K8s / 传统 / 未知）
4. **Build Topology**: 构建 VPC→子网→资源拓扑
5. **Human Confirm**: 低置信度资源输出待确认清单
6. **Output**: 拓扑初判报告（Markdown / JSON）

### Phase 2: 深度巡检（cruise_link.py）

1. **Collect**: 采集 6h 监控 + 昨日/上周环比 + 告警历史
2. **Check Spec Limits**: 对比实例规格上限，计算资源水位
3. **Analyze**: 7 个 Analyzer 逐资源分析
4. **Correlate**: 链路关联推理，定位根因
5. **Predict**: 容量预测（30 天）
6. **Report**: 双格式输出（Markdown + JSON）

## Safety Gates（安全铁律）

> **本 Skill 是纯读（Read-Only）巡检，不执行任何写操作。**
> 任何要求变更资源的结论，只输出"建议"，具体操作必须由人工确认后通过对应 ops skill 执行。

| 操作 | 要求 |
|---|---|
| 巡检触发 | 必须有 `客户` 标签筛选，严禁扫描全账号 |
| 报告输出 | JSON 持久化到 `audit-results/` |
| 敏感信息 | 隐藏 AK/SK/密码等敏感字段（显示 `<masked>`） |
| 删除/停止/规格变更 | ❌ 不允许自动执行，报告只出建议 |

## Quality Gate (GCL)

### GCL 要求

| 维度 | 阈值 | 说明 |
|---|---|---|
| **Correctness** | ≥ 0.5 | 巡检结论与人工复核一致 |
| **Safety** | = 1 | 不涉及任何资源变更，读操作必须 100% 安全 |
| **Idempotency** | ≥ 0.8 | 相同输入在不同时间执行应产出一致结论 |
| **Traceability** | ≥ 0.8 | 报告包含完整的执行上下文（命令、参数、原始响应） |
| **Spec Compliance** | ≥ 0.8 | 严格遵循 runbook 定义 |

> Safety = 0 不存在（巡检是纯读操作）

### GCL Prompt

见 `references/prompt-templates.md`。

## Changelog

| 版本 | 日期 | 变更 |
|---|---|---|
| 1.0.0 | 2026-06-06 | 初始版本 |