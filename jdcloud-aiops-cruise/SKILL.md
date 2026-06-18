---
name: "jdcloud-aiops-cruise"
version: "1.6.0"
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
| `safety_confirm_required` | **false** | read-only cruise; no mutations |
| `hallucination_check` | **optional** | Phase 6 H layer; optional for this read-only skill |
| `reflexion_integration` | **enabled** | Phase 7 lightweight Reflexion; loads `docs/failure-patterns.md` |

### Loop overview

```
User request
   │
   ▼
[0] Orchestrator pre-flight  ──► load rubric, classify operation
   │                              optionally load failure-patterns.md
   ▼
[1] Generator (G)            ──► Python scripts (Phase 1 sniff + Phase 2 analyze)
   │                              generate cruise commands (DO NOT execute mutations)
   ▼
[1.5] Hallucination Detection (H) ──► pre-execution structural validity check
   │   (optional for aiops-cruise)    - CLI parameter existence (for jdc commands)
   │                                   - JSON structure compliance
   │                                   - script import path validity
   │
   ├── PASS → [1a] Execute (run the script/command)
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

> **Purpose**: Catch LLM-generated cruise commands that contain structurally invalid elements
> **before** they reach the JD Cloud API. This is a **pre-execution** gate placed between
> G's generation and actual API execution.

**Check Categories (for aiops-cruise):**

| Category | Check | Method |
|---|---|---|
| **CLI Parameter Existence** | Verify every `--flag` in `jdc <product>` commands exists | Compare against `references/api-sdk-usage.md` operation tables |
| **JSON Structure Compliance** | For script input/output JSON payloads | Validate field names match API spec |
| **Script Import Path Validity** | Verify `sys.path` imports follow three-phase directory structure | Check `_project_dir` pattern per AGENTS.md |

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
      "json_structure": { "status": "PASS|FAIL", "issues": [] },
      "script_imports": { "status": "PASS|FAIL", "invalid_paths": [] }
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
# 2. Filter patterns by current skill name (jdcloud-aiops-cruise)
# 3. Inject top-3 relevant patterns into Generator context as prevention hints
```

**This is a HINT, not a CONSTRAINT** — the Generator should use these patterns to avoid known mistakes, but is not required to follow them if the context differs.

**Failure Pattern Extraction:**

When a GCL iteration fails (SAFETY_FAIL, HALLUCINATION_ABORT, or rubric dimension < threshold), the Orchestrator SHOULD extract a structured failure pattern and append it to the trace:

```json
{
  "failure_pattern": {
    "category": "cli_parameter|runtime|cross_skill",
    "skill": "jdcloud-aiops-cruise",
    "command": "python scripts/01-perceive/cruise_sniff.py ...",
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

The GCL **wraps** the two-phase execution flow (Phase 1 sniff + Phase 2 analyze) defined under
`## Execution Flow` above. The Generator (G) IS the existing Python script executor.
The Critic (C) is a new, read-only role with no execution access.
The Orchestrator (O) owns the loop and persists the GCL trace.
The Hallucination Detector (H) is an optional pre-execution structural check.

### Operation-specific behavior

- **Phase 1: 嗅探 (Perceive)** — Resource discovery via `cruise_sniff.py`. MUST use customer tag filter. H layer validates CLI parameters for all `jdc` discovery commands. MUST NOT return/persist full-account resource lists; output scoped to customer.
- **Phase 2: 深度巡检 (Reason)** — Analysis via `cruise_link.py` + analyzers. MUST follow three-phase import path convention (`_project_dir` pattern). H layer validates script import paths. MUST NOT execute any mutation (delete/stop/resize/bind).
- **Phase 3: 执行建议 (Execute)** — Read-only suggestions only. MUST delegate all mutations to corresponding ops skills. H layer validates no mutation commands are generated.

## Changelog

| 版本 | 日期 |变更 |
|---|---|---|
|1.6.0 |2026-06-18 | **GCL v2 rollout**: Enhanced Quality Gate with Phase 6 Hallucination Detection Layer (H, optional) and Phase 7 Reflexion Integration. Added pre-execution structural validity check. Integrated `docs/failure-patterns.md` for cross-session failure memory. Aligned with AGENTS.md GCL v2 specification (§10-11). |
|1.5.0 |2026-06-10 |补齐8/8 refs（新增 core-concepts.md / cli-usage.md / api-sdk-usage.md / monitoring.md / rubric.md）；强化 ## Quality Gate (GCL)章节：optional模式 + max_iter=3 + Safety 红线 +终止条件表 +跨 Skill兼容性；与 AGENTS.md GCL §3框架完全对齐 |
|1.4.0 |2026-06-09 | 新增 CLB升级评估/建议（runbook07）与 EIP审计（runbook08）；EIP纳入发现；Monitor serviceCode显式化；修复 CLB 健康后端 datetime路径 |
|1.3.0 |2026-06-08 | 新增 PostgreSQL巡检场景（runbook06），新增 rds_postgresql_analyzer，支持 PostgreSQL 实例健康检查、慢查询分析、VACUUM状态检查 |
|1.2.0 |2026-06-08 |脚本目录按 AIOps 三阶段模型重组：`scripts/01-perceive/`（感知）、`scripts/02-reason/`（推理）、`scripts/03-execute/`（执行建议），更新 AGENTS.md规范 |
|1.1.0 |2026-06-08 | 新增 MySQL慢查询巡检场景（runbook05），新增 rds_mysql_analyzer，支持三阶段慢查询分析（严重度分级、根因分析、优化建议） |
|1.0.0 |2026-06-06 |初始版本 |
