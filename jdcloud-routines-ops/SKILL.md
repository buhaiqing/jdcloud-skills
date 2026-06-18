---
name: jdcloud-routines-ops
version: "1.4.0"
metadata:
  displayName: 京东云日常运维
  description: 京东云日常运维场景集：资源到期巡检、资源盘点（账单分析已委托给 jdcloud-billing-ops）
  icon: 🔧
  tags: [jdcloud, operations, routines, cruise, expiry]
  cli_applicability: jdc + SDK
  cli_version_locked: "1.2.12"
  sdk_version_locked: ""
---

## Overview

`jdcloud-routines-ops` 是京东云日常运维场景的集 Skill，提供**静态 / 周期类**
巡检能力：资源到期巡检、资源盘点。**账单分析已委托给 `jdcloud-billing-ops`**。
所有场景遵循"读-only / 排程驱动 / 快照输出"的设计原则。

### 支持场景

| 场景 | 说明 | 状态 |
|------|------|------|
| [资源到期巡检](#资源到期巡检) | 巡检VM/云盘/EIP/Redis/RDS/CLB/MongoDB/Elasticsearch/SSL证书等资源到期情况 | ✅ 可用 |
| 资源账单分析 | **已委托** — 账户余额、消费记录、账单明细、代金券查询 | ↪️ `jdcloud-billing-ops` |
| [资源盘点报告](#资源盘点报告) | 生成客户资源使用汇总报告 | 🔜 规划中 |

---

## Trigger & Scope

### SHOULD Use

- 需要按周期（cron / 周报 / 月报）巡检资源到期情况时
- 需要按客户维度汇总账单 / 资源使用情况时
- 需要在大促 / 续费窗口前一次性扫描即将到期资源时
- 需要把"即将到期"信号传递给 `jdcloud-cloudmonitor-ops` 触发告警时

### SHOULD NOT Use

| 需求 | 委托 |
|---|---|
| 排查线上故障 / 实时性能 / 根因分析 | `jdcloud-aiops-cruise` |
| 修改变更 / 续费 / 删除具体资源 | 对应产品的 ops skill（如 `jdcloud-vm-ops`） |
| 告警聚合 / 抑制 / 降档 | `jdcloud-alert-intelligence` |
| 标签审计 / 标签合规 | `jdcloud-tag-audit-ops` |
| **账单查询 / 消费分析 / 余额查询 / 代金券** | **`jdcloud-billing-ops`** |

### Cross-Skill Delegation

| 本 skill 的需求 | 委托 |
|---|---|
| Cloud Monitor 指标查询 | `jdcloud-cloudmonitor-ops` |
| 续费前健康检查（针对 routines-ops 发现的即将到期 prod 资源） | `jdcloud-aiops-cruise` |
| 周期性告警压制规则 | `jdcloud-alert-intelligence` |
| 资源标签合规审计 | `jdcloud-tag-audit-ops` |
| VM / Redis / RDS 等资源续费 / 删除 | 对应产品的 ops skill（`jdcloud-vm-ops` 等） |
| **账单查询 / 消费记录 / 账户余额 / 代金券** | **`jdcloud-billing-ops`** |

---

## 职责边界（Responsibility Boundary）

> ⚠️ **本节是本 skill 与 `jdcloud-aiops-cruise` 的关键区分**。两者都属于
> "巡检类" skill，但服务完全不同的运维场景。

### 一句话总结

- **`jdcloud-routines-ops` = 静态 / 周期类巡检**（到期、账单、盘点）
- **`jdcloud-aiops-cruise` = 动态 / 事件类巡检**（健康、根因、容量）

### 对照表

| 维度 | `jdcloud-routines-ops`（本 skill） | `jdcloud-aiops-cruise` |
|---|---|---|
| **触发方式** | 排程（cron / 周 / 月 / 续费窗口） | 事件驱动 / 按需（告警、工单、人工） |
| **时间视角** | 面向未来 — "未来 N 天 / 下个月 / 本季度" | 面向当下 — "现在正在发生什么" |
| **时间窗** | 天 → 月（ahead-of-time） | 实时 → 分钟级（back / now） |
| **输出形态** | 静态快照报告（JSON + 控制台汇总） | 流式诊断 + 根因候选 + 监控指标 |
| **典型问题** | "哪些资源 14 天内到期？" "5 月账单多少？" "本周资源用量如何？" | "CLB 5xx 飙升" "VM CPU 100% 自 14:02 起" "MySQL 慢查询突发" |
| **数据来源** | `describe-*` 列表 + `charge` 元数据 | Cloud Monitor 指标 + 告警历史 + 链路拓扑 |
| **是否触发执行** | ❌ 绝不执行变更 | ❌ 不执行变更（只出建议） |
| **下一步交接** | "建议在某日前续费 / 处置" → 交给对应 ops skill | "建议升配 / 重启 / 切流" → 交给对应 ops skill |

### 决策启发式

> - "**这件事**正在发生 / 已经发生了吗？" → `jdcloud-aiops-cruise`
> - "**这件事**将要发生 / 何时到期？" → `jdcloud-routines-ops`

### 互补场景（同一资源可能同时被两者覆盖）

- **到期 + 健康**：routines-ops 发现 prod-VM 7 天后到期 → aiops-cruise 做一次
  续费前健康检查，决定续费还是替换。
- **账单 + 告警**：routines-ops 输出月度账单异常 → alert-intelligence 把
  "账单突增"作为非业务告警的输入信号。

### 不重叠的红线

- 本 skill **绝不**发起任何 `delete-*` / `stop-*` / `reboot-*` / `modify-*` 调用。
- 本 skill **绝不**写 Cloud Monitor 告警规则（委托 `jdcloud-cloudmonitor-ops`）。
- 本 skill **绝不**调用实时监控指标（委托 `jdcloud-aiops-cruise` 或
  `jdcloud-cloudmonitor-ops`）。

---

## Variable Convention

| 类型 | 语法 | 示例 | 说明 |
|------|------|------|------|
| 运行时 | `{{env.*}}` | `{{env.JDC_ACCESS_KEY}}` | agent 运行时变量 |
| 用户输入 | `{{user.*}}` | `{{user.customer}}` | 需用户确认的参数 |
| 输出引用 | `{{output.*}}` | `{{output.report_path}}` | 脚本输出路径 |

---

## 资源到期巡检

### Description

巡检当前账号下所有区域的资源（VM、云盘、EIP、Redis、RDS、CLB、MongoDB、
Elasticsearch、SSL证书等）的到期情况，按客户分组展示。

### Parameters

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--warning-days` | int | `14` | 预警天数阈值（默认14天内到期） |
| `--regions` | string | `all` | 巡检区域，逗号分隔或 `all` |
| `--types` | string | `vm,redis,eip,disk,rds,clb,mongodb,elasticsearch,ssl` | 资源类型，逗号分隔 |
| `--customer` | string | `` | 按客户名称过滤（可选） |
| `--output-dir` | string | `~/.jdcloud-routines-ops/outputs` | 输出目录 |

### Execution Flow

```
1. Pre-flight
   ├── 激活 .venv (Python 3.10)
   ├── 解析参数（warning-days, regions, types）
   └── 确认 jdc CLI凭证可用（~/.jdc/config）

2. Execute (jdc primary, SDK fallback)
   ├── 遍历指定区域
   │   ├── vm describe-instances
   │   ├── redis describe-cache-instances
   │   ├── disk describe-disks
   │   ├── vpc describe-eips
   │   ├── rds describe-instances
   │   ├── lb describe-load-balancers
   │   ├── mongodb describe-instances
   │   └── elasticsearch (SDK OpenAPI)
   ├── SSL 证书全局巡检（不分区域）
   │   └── ssl describe-certs
   └── 解析 chargeExpiredTime，计算剩余天数

3. Output
   ├── 控制台彩色输出汇总
   ├── JSON 详细报告 → outputs/expiry/expiry-report-YYYYMMDD-HHMMSS.json
   └── 返回0 (有到期资源) 或 1 (无到期资源)
```

### Output Parsing

| 资源类型 | jdc 命令 | 到期字段 |
|----------|----------|----------|
| VM | `vm describe-instances` | `$.result.instances[].charge.chargeExpiredTime` |
| Redis | `redis describe-cache-instances` | `$.result.cacheInstances[].charge.chargeExpiredTime` |
| 云盘 | `disk describe-disks` | `$.result.disks[].charge.chargeExpiredTime` |
| EIP | `vpc describe-eips` | `$.result.eips[].charge.chargeExpiredTime` |
| RDS | `rds describe-instances` | `$.result.dbInstances[].charge.chargeExpiredTime` |
| CLB | `lb describe-load-balancers` | `$.result.loadBalancers[].charge.chargeExpiredTime` |
| MongoDB | `mongodb describe-instances` | `$.result.mongodbInstances[].charge.chargeExpiredTime` |
| Elasticsearch | SDK OpenAPI | `$.result.instances[].charge.chargeExpiredTime` |
| SSL证书 | `ssl describe-certs` | `$.result.certListDetails[].endTime` |

### Example

```bash
# 基本巡检（14天阈值，所有区域）
python jdcloud-routines-ops/scripts/expiry_cruise.py

# 7天紧急预警
python jdcloud-routines-ops/scripts/expiry_cruise.py --warning-days 7

# 询价模式：额外调用 billing API 获取续费价格（较慢但提供成本预估）
python jdcloud-routines-ops/scripts/expiry_cruise.py --with-price

# 只巡检华北区域和VM类型
python jdcloud-routines-ops/scripts/expiry_cruise.py --regions cn-north-1 --types vm

# 只巡检华北区域和RDS类型
python jdcloud-routines-ops/scripts/expiry_cruise.py --regions cn-north-1 --types rds

# 只巡检SSL证书（全局资源）
python jdcloud-routines-ops/scripts/expiry_cruise.py --types ssl

# 按客户过滤
python jdcloud-routines-ops/scripts/expiry_cruise.py --customer 烟台振华
```

### Output Artifacts

| 文件 | 路径 | 说明 |
|------|------|------|
| 控制台摘要 | stdout | 按客户分组的到期资源列表 |
| JSON 报告 | `outputs/expiry/expiry-report-YYYYMMDD-HHMMSS.json` | 完整数据，可供后续处理 |

---

## 资源账单分析

> ⚠️ **已委托给 `jdcloud-billing-ops`**
>
> 账单相关功能（账户余额查询、消费记录、账单明细、代金券管理、成本预估）
> 已迁移至专门的 `jdcloud-billing-ops` Skill。
>
> **routines-ops 保留的能力**：到期资源**续费询价**（`--with-price` 模式）
> 仍可在 [资源到期巡检](#资源到期巡检) 中使用，作为续费决策的辅助数据。
>
> **委托路径**：
> - 账户余额、消费记录、账单明细查询 → `jdcloud-billing-ops`
> - 代金券查询和管理 → `jdcloud-billing-ops`
> - 成本预估（新购资源）→ `jdcloud-billing-ops`

---

## Code Patterns 参考

所有脚本开发应遵循 [references/code-patterns.md](references/code-patterns.md)
提供的 5 个模式模板：

| 模式 | 场景 | 关键收益 |
|------|------|----------|
| 模式 1 | 资源迭代通用 | 用配置表替代 8 个重复函数 |
| 模式 2 | `--input-json` 复杂参数 | 避免 billing/renewal API 反复试错 |
| 模式 3 | 多步骤依赖流程 | `query-instance` → `calculate-total-price` 询价核心 |
| 模式 4 | jdc-first with SDK fallback | 统一重试和 fallback 逻辑 |
| 模式 5 | 报告输出模板 | 统一控制台 + JSON 双输出 |

**Agent 开发新脚本时**：
1. 先阅读 `code-patterns.md` 找到匹配的模式
2. 复制对应模板作为起点
3. 修改 `RESOURCE_CONFIG` 或调整 `order_payload` 即可

---

## 资源盘点报告

> ✅ **Available** (v1.3 规范定型)

生成客户资源使用汇总报告，包括VM规格、存储容量、网络配置等。

### 报告格式规范（强制执行）

基于 `jdcloud-routines-ops/outputs/customers/丹东鹏飞/部署结构分析报告-20260610.md` 从 v1.0 → v1.3 的三轮强化经验，制定以下 **P0/P1 规范**。所有资源盘点报告必须自检通过后方可提交。

| 规则 | 级别 | 规范内容 | 正例 | 反例 |
|---|---|---|---|---|
| **R1 双标识规则** | P0 | 凡涉及**子网/VPC/安全组/路由表**等可引用资源，必须同时显示 **Name + ID**，缺一不可 | `鹏飞-ERP-DB / subnet-ue3wimfa0j` | `鹏飞-ERP-DB` ❌ 或 `subnet-ue3wimfa0j` ❌ |
| **R2 操作性清单规则** | P0 | **续费/变更/删除**等可操作清单，每行必须含**具体实例 ID**（如 `i-9i22fdurlq`），不得仅以"12 台 VM"聚合 | `鹏飞-erp-prd-oracle / i-9i22fdurlq` | `12 台 VM 即将到期` ❌ |
| **R3 归因责任矩阵** | P1 | 风险项描述必须区分**"云上资源客观状态"** vs **"Skill 自身问题"**。`jdcloud-aiops-cruise` 是 read-only，**不打标签、不改字段**，发现云上数据矛盾时应描述为"三方字段不一致"而非"Skill 标签错误" | `subnet-ru6zazmhqu 的 name/vpc/tag 三方矛盾（云上资源状态）` | `Skill 标签错误` ❌ |
| **R4 执行者视角** | P1 | 每节必须自问：**"读者拿到这节要做什么？"** 如需操作资源，必须提供可直接使用的 ID/API 参数；如仅需了解，需提供可追溯的标识 | 续费清单含 YAML + 实例 ID，可直接粘贴执行 | 纯文字描述，需二次查询 ID ❌ |
| **R5 章节自检清单** | P1 | 提交前必须对照《资源盘点报告自检清单》（见 `references/report-format.md` §3）逐项勾选 | 附录含"自检清单签名" | 无自检记录 ❌ |

### 典型章节格式模板

```markdown
## 3. 业务系统划分(Business Workload Mapping)

### 3.X [系统名](N 台 VM)

| 主机名 | **实例 ID** | IP | 规格 | OS | 用途 | **子网名 + ID** | 计费到期 |
|---|---|---|---|---|---|---|---|
| 鹏飞-erp-prd-oracle | **i-9i22fdurlq** | 172.21.14.19 | c.n3.2xlarge | CentOS 7.9 | Oracle DB | **鹏飞-ERP-DB** / subnet-ue3wimfa0j | 2026-06-15 |

## 5. 计费与生命周期(Billing & Lifecycle)

### 5.2 到期资源完整清单(含实例 ID + 子网名 + 子网 ID)

| # | 资源名 | **实例 ID** | IP | 规格 | **子网名 + ID** | 续费 Skill | 到期日 |
|---|---|---|---|---|---|---|---|
| 1 | 鹏飞-erp-prd-oracle | **i-9i22fdurlq** | 172.21.14.19 | c.n3.2xlarge | **鹏飞-ERP-DB** / subnet-ue3wimfa0j | jdcloud-vm-ops | 2026-06-15 |
```

### 违规处理

- **P0 违规**（R1/R2）：GCL Critic 直接判定 `Correctness = 0`，必须修复后方可进入下一阶段
- **P1 违规**（R3/R4/R5）：GCL Critic 判定 `Spec Compliance = 0.5`，建议修复，可讨论豁免

### 参考文档

- 详细规范与自检清单：`references/report-format.md`
- 评分维度更新：`references/rubric.md` §Dimensions
- 代码模式模板：`references/code-patterns.md` §模式 6

---

## Output Management

### 目录结构

```
~/.jdcloud-routines-ops/
└── outputs/
    └── expiry/
        └── expiry-report-20260609-143000.json
```

### 清理策略

```bash
# 清理7天前的报告
find ~/.jdcloud-routines-ops/outputs -type f -mtime +7 -delete

# 清理30天前的报告
find ~/.jdcloud-routines-ops/outputs -type f -mtime +30 -delete
```

### .gitignore

项目内 `outputs/` 目录已加入 `.gitignore`，不会提交到 git repo。

---

## Quality Gate (GCL)

> This skill participates in the repository-wide **Generator-Critic-Loop**
> (GCL) defined in [`AGENTS.md` §Quality Gate](../AGENTS.md#generator-critic-loop-gcl--adversarial-quality-gate).
> The quality gate is **optional** for this read-only skill (per
> `AGENTS.md` §8).

### Parameters (override `AGENTS.md` §8 defaults)

| Parameter | Value | Reason |
|---|---|---|
| `max_iterations` | **5** | `AGENTS.md` §8 default for optional skills |
| `rubric_version` | `v2` | see [references/rubric.md](references/rubric.md) |
| `trace_path` | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | unified trace path |
| `safety_confirm_required` | **false** | read-only by default; renewal flows must confirm via delegated ops skills |
| `hallucination_check` | **optional** | Phase 6 H layer; optional for this read-only skill |
| `reflexion_integration` | **enabled** | Phase 7 lightweight Reflexion; loads `docs/failure-patterns.md` |

### GCL 触发条件

| 触发场景 | GCL 要求 |
|---|---|
| 排程（cron / 周报） | **跳过**（输出直接落盘） |
| 操作员 on-demand 调用 | **推荐** |
| 续费 / 替换决策前置巡检 | **必须** |

### Loop overview

```
User request
   │
   ▼
[0] Orchestrator pre-flight  ──► load rubric, classify operation
   │                              optionally load failure-patterns.md
   ▼
[1] Generator (G)            ──► jdc CLI (primary) → SDK (after 3 fails)
   │                              generate cruise commands (DO NOT execute mutations)
   ▼
[1.5] Hallucination Detection (H) ──► pre-execution structural validity check
   │   (optional for routines-ops)    - CLI parameter existence
   │                                   - JSON structure compliance
   │
   ├── PASS → [1a] Execute (run the jdc/SDK call)
   ├── FAIL → [1b] Regenerate (H retriggers G with hallucination report; max 1 retry)
   │         still FAIL → HALT with "HALLUCINATION_ABORT"
   ▼
[2] Critic (C)               ──► isolated context, blind to user request
   │                              score every rubric dimension
   │                              assess test accuracy + regression gate
   ▼
[3] Orchestrator decider
   ├─ HALLUCINATION_ABORT     → ABORT (no partial)
   ├─ Safety=0 / blocking     → ABORT
   ├─ all pass                → RETURN
   ├─ iter<5 & not all pass   → RETRY (inject suggestions)
   └─ iter=5 & not all pass   → RETURN_BEST
```

### Hallucination Detection Layer (H) — Optional

> **Purpose**: Catch LLM-generated jdc/SDK calls that contain structurally invalid elements
> **before** they reach the JD Cloud API. This is a **pre-execution** gate placed between
> G's generation and actual API execution.

**Check Categories (for routines-ops):**

| Category | Check | Method |
|---|---|---|
| **CLI Parameter Existence** | Verify every `--flag` in `jdc <product>` commands exists | Compare against `references/api-sdk-usage.md` operation tables |
| **JSON Structure Compliance** | For cruise script input/output JSON | Validate field names match API spec |

**Termination:**

| Condition | Exit Code | Action |
|---|---|---|
| **H_PASS** | — | Continue to [1a] Execute |
| **H_FAIL → Regenerate** | — | Inject hallucination report into G; max 1 regeneration attempt |
| **HALLUCINATION_ABORT** | 5 | HALT — structural hallucinations persist after regeneration |

**Trace Integration:**

The H result is embedded in the GCL trace JSON under `iterations[].hallucination_detector`:

```json
{
  "iter": 1,
  "hallucination_detector": {
    "status": "PASS|FAIL",
    "checks": {
      "cli_parameters": { "status": "PASS|FAIL", "unrecognized_params": [] },
      "json_structure": { "status": "PASS|FAIL", "issues": [] }
    },
    "report": "..."
  },
  "regenerated": false,
  "generator": { ... },
  "critic": { ... }
}
```

### Reflexion Integration (Lightweight Reflexion)

> **Purpose**: Enable cross-session learning from failure patterns, complementing the within-session
> GCL loop with persistent failure memory.

**Architecture:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    GCL Execution (per-session)                   │
│   [0] Pre-flight → [1] Generate → [1.5] H → [2] C → [3] Decide │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                    failure_pattern (in trace)
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              Reflexion Memory (cross-session)                    │
│   docs/failure-patterns.md (structured text, ≤200 lines)        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                    Pre-flight retrieval (optional)
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              Prevention (next session)                           │
│   Inject known patterns into Generator context                  │
└─────────────────────────────────────────────────────────────────┘
```

**Pre-flight Retrieval (Optional):**

During GCL Pre-flight (step [0]), the Orchestrator MAY:

```bash
# 1. Load docs/failure-patterns.md (lazy-load, ~150 lines)
# 2. Filter patterns by current skill name (jdcloud-routines-ops)
# 3. Inject top-3 relevant patterns into Generator context as prevention hints
```

**This is a HINT, not a CONSTRAINT** — the Generator should use these patterns to avoid known mistakes, but is not required to follow them if the context differs.

**Failure Pattern Extraction:**

When a GCL iteration fails (SAFETY_FAIL, HALLUCINATION_ABORT, or rubric dimension < threshold), the Orchestrator SHOULD extract a structured failure pattern and append it to the trace:

```json
{
  "failure_pattern": {
    "category": "cli_parameter|runtime|cross_skill",
    "skill": "jdcloud-routines-ops",
    "command": "python scripts/expiry_cruise.py ...",
    "error": "...",
    "fix": "...",
    "reusable": true
  }
}
```

### Artifacts

- Rubric (concrete scoring rules): [references/rubric.md](references/rubric.md)
- Prompt templates (G / C / O / H): [references/prompt-templates.md](references/prompt-templates.md)
- Failure patterns (cross-session memory): [docs/failure-patterns.md](../docs/failure-patterns.md)

### Integration with existing flows

The GCL **wraps** the jdc-first / SDK-fallback flow defined under
`## Execution Flows` above. The Generator (G) IS the existing jdc-or-SDK
executor. The Critic (C) is a new, read-only role with no `jdc` / SDK
access. The Orchestrator (O) owns the loop and persists the GCL trace.
The Hallucination Detector (H) is an optional pre-execution structural check.

### Operation-specific behavior

- **资源到期巡检 (Expiry Cruise)** — Read-only. H layer validates CLI parameters for all `jdc` discovery commands. MUST use `--customer` filter. MUST NOT execute any mutation. Report MUST include `report_time` / `warning_days` / `regions_checked` / `types_checked` / `summary` / `details[]`.
- **资源盘点 (Resource Inventory)** — Read-only. Same constraints as expiry cruise.
- **续费决策前置巡检** — GCL **必须** enabled. H layer validates all parameters before execution. Renewal recommendations MUST be delegated to corresponding ops skills with human confirmation.

---

## Safety Gates（安全铁律）

> **本 Skill 是纯读（Read-Only）巡检，不执行任何写操作。**
> 任何要求变更资源的结论，只输出"建议"，具体操作必须由人工确认后通过
> 对应 ops skill 执行。

| 操作 | 要求 |
|---|---|
| 资源到期巡检触发 | jdc CLI 默认 + SDK fallback；不发起任何 mutation |
| 报告输出 | 报告 JSON 写入 `~/.jdcloud-routines-ops/outputs/`；GCL 审计追踪写入仓库级 `audit-results/` |
| 敏感信息 | 隐藏 AK/SK/密码等敏感字段（显示 `<masked>`） |
| 删除 / 停止 / 规格变更 / 续费 | ❌ 不允许自动执行，报告只出建议 |
| 跨客户数据 | `--customer` 过滤后的报告**严禁**混入其他客户数据 |

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.4.0 | 2026-06-18 | **GCL v2 rollout**: Enhanced Quality Gate with Phase 6 Hallucination Detection Layer (H, optional) and Phase 7 Reflexion Integration. Added pre-execution structural validity check. Integrated `docs/failure-patterns.md` for cross-session failure memory. Aligned with AGENTS.md GCL v2 specification (§10-11). |
| 1.3.0 | 2026-06-10 | **重构**：账单分析功能委托给 `jdcloud-billing-ops`；更新 description 和 Cross-Skill Delegation 表；本 skill 专注于资源到期巡检和资源盘点 |
| 1.2.0 | 2026-06-10 | 新增 [references/code-patterns.md](references/code-patterns.md) 提供 5 个脚本开发模式模板；重构 `expiry_cruise.py` 为配置驱动模式；更新 `lib/jdc_client.py` 增加 `--input-json` 和多步骤询价支持 |
| 1.1.0 | 2026-06-09 | 添加 MongoDB 和 Elasticsearch 到期巡检；默认 types 增加 mongodb,elasticsearch |
| 1.0.3 | 2026-06-09 | 添加 CLB 负载均衡到期巡检；默认 types 增加 clb |
| 1.0.2 | 2026-06-09 | 添加 SSL 证书到期巡检；汇总报告增加区域统计 |
| 1.0.1 | 2026-06-09 | 添加 RDS 到期巡检（支持 MySQL/PostgreSQL/SQL Server） |
| 1.0.0 | 2026-06-09 | Initial release with expiry cruise scenario |