---
name: "jdcloud-aiops-cruise"
version: "1.5.0"
metadata:
 description: "JD Cloud 全链路巡检 Skill —覆盖 EIP审计/CLB升级评估/VM/K8s/Redis/NAT/安全组的自动拓扑发现与深度诊断"
 cli_applicability: "partial"
 cli_version_locked: false
 sdk_version_locked: false
---

# JD Cloud 全链路巡检

## Trigger & Scope

### SHOULD Use

- 需要对指定客户（按标签）的 JD Cloud资源做全链路健康检查时
- 需要排查故障根因时（从 CLB入口到后端数据库的整条链路）
- 需要做容量规划或大促前预检时
- 需要评估 CLB 是否存在连接数/新建连接/健康后端风险，并生成升级建议时
- 需要审计 EIP绑定状态、公网入口与带宽利用风险时
- 需要了解某个客户的 JD Cloud资源拓扑结构时

### SHOULD NOT Use

- 只查单一资源（如单台 VM）→ 使用 `jdcloud-vm-ops`
- 需要修改/变更资源 → 使用对应产品的 ops skill
- 不涉及 JD Cloud资源的巡检 → 不使用

### Cross-Skill Delegation

|需求 |委托 |
|---|---|
| VM 创建/停止/删除 | `jdcloud-vm-ops` |
| Redis 实例 CRUD | `jdcloud-redis-ops` |
| MySQL慢查询分析/索引优化 | `jdcloud-mysql-ops` |
|监控告警规则变更 | `jdcloud-cloudmonitor-ops` |
| CLB升级/升配/监听器或后端变更 | `jdcloud-clb-ops` |
| EIP绑定/解绑/释放/带宽调整 | `jdcloud-eip-ops` |
| IAM/权限管理 | `jdcloud-iam-ops` |

## Variable Convention

| 类型 | 说明 | 示例 |
|---|---|---|
| `{{env.*}}` |运行时环境变量，不提示用户 | `{{env.JDC_ACCESS_KEY}}` |
| `{{user.*}}` |每次巡检时询问用户 | `{{user.customer_name}}` |
| `{{output.*}}` |脚本解析输出 | `{{output.topology}}` |

## Execution Flow

### Phase1:嗅探（`scripts/01-perceive/cruise_sniff.py`）

1. **Pre-flight**:读取 runbook 配置，解析阈值
2. **Discover**:扫描客户标签下的 EIP/CLB/VM/Redis/RDS MySQL/NAT/K8s/安全组（EIP 通过只读 `list_eips`纳入发现）
3. **Classify**: 按标签置信度分类部署模式（K8s /传统 /未知）
4. **Build Topology**: 构建 VPC→子网→资源拓扑
5. **Human Confirm**: 低置信度资源输出待确认清单
6. **Output**:拓扑初判报告（Markdown / JSON）

### Phase2:深度巡检（`scripts/02-reason/cruise_analyze.py`）

1. **Collect**:采集6h监控 +昨日/上周环比 +告警历史
2. **Check Spec Limits**: 对比实例规格上限，计算资源水位
3. **Analyze**: Analyzer逐资源分析，包含 CLB升级评估/建议与 EIP审计
4. **Correlate**:链路关联推理，定位根因
5. **Predict**:容量预测（30 天）
6. **Report**: 双格式输出（Markdown + JSON）

## Safety Gates（安全铁律）

> **本 Skill 是纯读（Read-Only）巡检，不执行任何写操作。**
>任何要求变更资源的结论，只输出"建议"，具体操作必须由人工确认后通过对应 ops skill 执行。

| 操作 | 要求 |
|---|---|
|巡检触发 | 必须有 `客户`标签筛选；允许通过只读 list/describe 做发现，但返回/持久化的原始资源数据必须按客户范围最小化，严禁落盘全账号清单 |
|报告输出 | 运行报告 JSON写入 `jdcloud-aiops-cruise/reports/output/`；GCL审计追踪单独写入仓库级 `audit-results/` |
|敏感信息 |隐藏 AK/SK/密码等敏感字段（显示 `<masked>`） |
| 删除/停止/规格变更 | ❌ 不允许自动执行，报告只出建议 |
| CLB升级/升配 | ❌ 不允许自动执行，只输出容量/健康证据与 `jdcloud-clb-ops`委托建议 |
| EIP绑定/解绑/释放/调带宽 | ❌ 不允许自动执行，只输出审计结论与 `jdcloud-eip-ops`委托建议 |

## 新增 AIOps能力

### CLB升级评估/建议（只读）

- 输入：客户标签下 CLB清单、`lb.active_connection_count`、`lb.new_connection_count`、`lb.backend.healthy.host_count`。
- 分析：按标准型/高性能型规格上限计算连接水位；当并发连接或新建连接达到60% 输出 Info，达到80% 输出 Warning；健康后端数 `<2` 输出 Critical。
- 输出：仅生成"评估升配/升级"的证据链和建议，实际升级、升配、监听器/后端变更必须委托 `jdcloud-clb-ops` 并人工确认。
- Runbook：`runbooks/07-clb-upgrade-assessment.md`。

### EIP审计（只读）

- 输入：客户标签下 EIP清单、`eip.bandwidth.in`、`eip.bandwidth.out`、绑定资源字段（如 API 返回）。
- 分析：审计入/出带宽利用率、未绑定 EIP、缺失监控数据和公网入口治理提示。
- 输出：只报告风险与建议；EIP释放、绑定/解绑、带宽调整必须委托 `jdcloud-eip-ops` 并人工确认。
- Runbook：`runbooks/08-eip-audit.md`。

## Quality Gate (GCL)

> 本 Skill 是 **optional GCL（read-only）**巡检，不是 required GCL写操作 Skill。
>巡检产出物（报告、建议）面向人工审查，不需要 CI强制门控；但建议在生产客户巡检中启用 GCL，
>验证 Safety / Traceability / Spec Compliance三大维度。

### GCL 设置

| 参数 | 值 | 说明 |
|---|---|---|
|启用模式 | **optional (read-only)** | CI 不强制；可在本地 / staging启用 |
| `max_iterations` | **3** | 默认3轮迭代；超过返回 best-so-far |
| Trace落盘路径 | `<repo-root>/audit-results/gcl-trace-<YYYYMMDD-HHMMSS>.json` |统一审计追踪 |
| Prompt模板 | `references/prompt-templates.md` | Generator / Critic / Orchestrator 三套 |
| Rubric 实例 | `references/rubric.md` |5维框架 + 本 skill专属 Safety规则 |

### Rubric（5维）

|维度 |阈值 |含义 |
|---|---|---|
| **Correctness** | ≥0.5 | finding 与人工复核一致 |
| **Safety** | **=1（强制）** | 未执行资源变更、未泄露 `SECRET_KEY`、未返回/持久化跨客户或全账号原始资源清单 |
| **Idempotency** | ≥0.8 |相同输入不同时间执行产出一致结论 |
| **Traceability** | ≥0.8 |报告含完整执行上下文（命令 / 参数 /原始响应） |
| **Spec Compliance** | ≥0.8 |严格遵循 runbook 与 AGENTS.md路径约定 |

> **Safety =0 必须无条件 ABORT**。即使巡检为只读，只要出现变更调用、敏感信息泄露、或跨客户/全账号原始资源数据被返回或持久化，Safety 即为0；不允许"best-effort"返回部分结果。

### Safety 红线（本 skill专属）

|严禁动作 |后果 |替代 |
|---|---|---|
|任何资源的删除 /释放 /停止 / 重启 | Safety =0 → ABORT | `jdcloud-vm-ops` / `jdcloud-clb-ops` / `jdcloud-eip-ops` 等 |
|任何资源的升配 /降配 /规格变更 | Safety =0 → ABORT | 同上 |
| EIP / CLB 后端的绑定 / 解绑 /摘除 | Safety =0 → ABORT | `jdcloud-eip-ops` / `jdcloud-clb-ops` |
|任何 DDL（CREATE INDEX / VACUUM FULL / DROP） | Safety =0 → ABORT | `jdcloud-mysql-ops` / `jdcloud-postgresql-ops` |
| 修改 / 删除 /禁用告警规则 | Safety =0 → ABORT | `jdcloud-cloudmonitor-ops` |
|打印完整 `SECRET_KEY` / 返回跨客户原始清单 | Safety =0 → ABORT | 仅 `<masked>` + 按客户范围最小化输出 |

###终止条件（按优先级）

|条件 |触发 |行为 |
|---|---|---|
| **SAFETY_FAIL** | Safety =0 |立即 ABORT，不返回任何结果 |
| **PASS** | 所有维度 ≥阈值 | 返回 Generator 结果 |
| **MAX_ITER** | iter ≥3 | 返回 best-so-far + 未解决 rubric 项 |
| **RETRY** | 任一维度 <阈值 且 iter <3 | 将 Critic反馈注入 Generator 重试 |

### GCL Prompt

- Generator Prompt：`references/prompt-templates.md`（执行器）
- Critic Prompt：`references/prompt-templates.md`（独立审计员，**不可见用户原始请求**）
- Orchestrator Prompt：`references/prompt-templates.md`（循环控制 + Safety FAIL优先决策）
- Rubric详细定义：`references/rubric.md`

###跨 Skill GCL兼容性

| Skill | GCL 设置 | 与本 skill 的差异 |
|---|---|---|
| `jdcloud-vm-ops` / `jdcloud-redis-ops` / `jdcloud-mysql-ops` | required / max_iter=2 |写操作，需要 Safety 双门 |
| `jdcloud-clb-ops` / `jdcloud-cloudmonitor-ops` | recommended / max_iter=3 |写操作但风险中等 |
| `jdcloud-alert-intelligence` / `jdcloud-audit-ops` | optional / max_iter=5 | 只读，但本 skill 是全链路跨产品，更严格 |
| **`jdcloud-aiops-cruise`** | **optional / max_iter=3** | 只读 +跨产品 + 数据最小化强制 |

### 本 skill 不强制 GCL 的原因

1. **只读边界明确** —任何变更调用都需走对应 ops skill，违反即 Safety FAIL。
2. **人工终审** —报告由人工审阅后再委托执行，GCL主要是审计追踪而非阻塞门。
3. **跨产品数据量大** — 单次巡检可达上百资源，强制 GCL 会显著拖慢 CI。
4. **历史溯源靠 runbook Changelog** —阈值/场景变更通过 SemVer + runbook 版本控制保证。

> 生产客户巡检建议**手动启用 GCL**（`--gcl`标志），并将 trace落盘供事后审计。

## Changelog

| 版本 | 日期 |变更 |
|---|---|---|
|1.5.0 |2026-06-10 |补齐8/8 refs（新增 core-concepts.md / cli-usage.md / api-sdk-usage.md / monitoring.md / rubric.md）；强化 ## Quality Gate (GCL)章节：optional模式 + max_iter=3 + Safety 红线 +终止条件表 +跨 Skill兼容性；与 AGENTS.md GCL §3框架完全对齐 |
|1.4.0 |2026-06-09 | 新增 CLB升级评估/建议（runbook07）与 EIP审计（runbook08）；EIP纳入发现；Monitor serviceCode显式化；修复 CLB 健康后端 datetime路径 |
|1.3.0 |2026-06-08 | 新增 PostgreSQL巡检场景（runbook06），新增 rds_postgresql_analyzer，支持 PostgreSQL 实例健康检查、慢查询分析、VACUUM状态检查 |
|1.2.0 |2026-06-08 |脚本目录按 AIOps 三阶段模型重组：`scripts/01-perceive/`（感知）、`scripts/02-reason/`（推理）、`scripts/03-execute/`（执行建议），更新 AGENTS.md规范 |
|1.1.0 |2026-06-08 | 新增 MySQL慢查询巡检场景（runbook05），新增 rds_mysql_analyzer，支持三阶段慢查询分析（严重度分级、根因分析、优化建议） |
|1.0.0 |2026-06-06 |初始版本 |
