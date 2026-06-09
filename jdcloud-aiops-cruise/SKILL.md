---
name: "jdcloud-aiops-cruise"
version: "1.4.0"
metadata:
  description: "JD Cloud 全链路巡检 Skill — 覆盖 EIP审计/CLB升级评估/VM/K8s/Redis/NAT/安全组的自动拓扑发现与深度诊断"
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
- 需要评估 CLB 是否存在连接数/新建连接/健康后端风险，并生成升级建议时
- 需要审计 EIP 绑定状态、公网入口与带宽利用风险时
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
| MySQL 慢查询分析/索引优化 | `jdcloud-mysql-ops` |
| 监控告警规则变更 | `jdcloud-cloudmonitor-ops` |
| CLB 升级/升配/监听器或后端变更 | `jdcloud-clb-ops` |
| EIP 绑定/解绑/释放/带宽调整 | `jdcloud-eip-ops` |
| IAM/权限管理 | `jdcloud-iam-ops` |

## Variable Convention

| 类型 | 说明 | 示例 |
|---|---|---|
| `{{env.*}}` | 运行时环境变量，不提示用户 | `{{env.JDC_ACCESS_KEY}}` |
| `{{user.*}}` | 每次巡检时询问用户 | `{{user.customer_name}}` |
| `{{output.*}}` | 脚本解析输出 | `{{output.topology}}` |

## Execution Flow

### Phase 1: 嗅探（`scripts/01-perceive/cruise_sniff.py`）

1. **Pre-flight**: 读取 runbook 配置，解析阈值
2. **Discover**: 扫描客户标签下的 EIP/CLB/VM/Redis/RDS MySQL/NAT/K8s/安全组（EIP 通过只读 `list_eips` 纳入发现）
3. **Classify**: 按标签置信度分类部署模式（K8s / 传统 / 未知）
4. **Build Topology**: 构建 VPC→子网→资源拓扑
5. **Human Confirm**: 低置信度资源输出待确认清单
6. **Output**: 拓扑初判报告（Markdown / JSON）

### Phase 2: 深度巡检（`scripts/02-reason/cruise_analyze.py`）

1. **Collect**: 采集 6h 监控 + 昨日/上周环比 + 告警历史
2. **Check Spec Limits**: 对比实例规格上限，计算资源水位
3. **Analyze**: Analyzer 逐资源分析，包含 CLB 升级评估/建议与 EIP 审计
4. **Correlate**: 链路关联推理，定位根因
5. **Predict**: 容量预测（30 天）
6. **Report**: 双格式输出（Markdown + JSON）

## Safety Gates（安全铁律）

> **本 Skill 是纯读（Read-Only）巡检，不执行任何写操作。**
> 任何要求变更资源的结论，只输出"建议"，具体操作必须由人工确认后通过对应 ops skill 执行。

| 操作 | 要求 |
|---|---|
| 巡检触发 | 必须有 `客户` 标签筛选；允许通过只读 list/describe 做发现，但返回/持久化的原始资源数据必须按客户范围最小化，严禁落盘全账号清单 |
| 报告输出 | 运行报告 JSON 写入 `jdcloud-aiops-cruise/reports/output/`；GCL 审计追踪单独写入仓库级 `audit-results/` |
| 敏感信息 | 隐藏 AK/SK/密码等敏感字段（显示 `<masked>`） |
| 删除/停止/规格变更 | ❌ 不允许自动执行，报告只出建议 |
| CLB 升级/升配 | ❌ 不允许自动执行，只输出容量/健康证据与 `jdcloud-clb-ops` 委托建议 |
| EIP 绑定/解绑/释放/调带宽 | ❌ 不允许自动执行，只输出审计结论与 `jdcloud-eip-ops` 委托建议 |

## 新增 AIOps 能力

### CLB 升级评估/建议（只读）

- 输入：客户标签下 CLB 清单、`lb.active_connection_count`、`lb.new_connection_count`、`lb.backend.healthy.host_count`。
- 分析：按标准型/高性能型规格上限计算连接水位；当并发连接或新建连接达到 60% 输出 Info，达到 80% 输出 Warning；健康后端数 `< 2` 输出 Critical。
- 输出：仅生成“评估升配/升级”的证据链和建议，实际升级、升配、监听器/后端变更必须委托 `jdcloud-clb-ops` 并人工确认。
- Runbook：`runbooks/07-clb-upgrade-assessment.md`。

### EIP 审计（只读）

- 输入：客户标签下 EIP 清单、`eip.bandwidth.in`、`eip.bandwidth.out`、绑定资源字段（如 API 返回）。
- 分析：审计入/出带宽利用率、未绑定 EIP、缺失监控数据和公网入口治理提示。
- 输出：只报告风险与建议；EIP 释放、绑定/解绑、带宽调整必须委托 `jdcloud-eip-ops` 并人工确认。
- Runbook：`runbooks/08-eip-audit.md`。

## Quality Gate (GCL)

### GCL 要求

| 维度 | 阈值 | 说明 |
|---|---|---|
| **Correctness** | ≥ 0.5 | 巡检结论与人工复核一致 |
| **Safety** | = 1 | 未执行资源变更、未泄露敏感信息、未返回/持久化跨客户或全账号原始清单 |
| **Idempotency** | ≥ 0.8 | 相同输入在不同时间执行应产出一致结论 |
| **Traceability** | ≥ 0.8 | 报告包含完整的执行上下文（命令、参数、原始响应） |
| **Spec Compliance** | ≥ 0.8 | 严格遵循 runbook 定义 |

> Safety = 0 必须无条件 ABORT。即使巡检为只读，只要出现变更调用、敏感信息泄露、或跨客户/全账号原始资源数据被返回或持久化，Safety 即为 0。

### GCL Prompt

见 `references/prompt-templates.md`。

## Changelog

| 版本 | 日期 | 变更 |
|---|---|---|
| 1.4.0 | 2026-06-09 | 新增 CLB 升级评估/建议（runbook 07）与 EIP 审计（runbook 08）；EIP 纳入发现；Monitor serviceCode 显式化；修复 CLB 健康后端 datetime 路径 |
| 1.3.0 | 2026-06-08 | 新增 PostgreSQL 巡检场景（runbook 06），新增 rds_postgresql_analyzer，支持 PostgreSQL 实例健康检查、慢查询分析、VACUUM 状态检查 |
| 1.2.0 | 2026-06-08 | 脚本目录按 AIOps 三阶段模型重组：`scripts/01-perceive/`（感知）、`scripts/02-reason/`（推理）、`scripts/03-execute/`（执行建议），更新 AGENTS.md 规范 |
| 1.1.0 | 2026-06-08 | 新增 MySQL 慢查询巡检场景（runbook 05），新增 rds_mysql_analyzer，支持三阶段慢查询分析（严重度分级、根因分析、优化建议） |
| 1.0.0 | 2026-06-06 | 初始版本 |