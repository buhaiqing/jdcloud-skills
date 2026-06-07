---
name: jdcloud-topo-discovery
description: >-
  Use this skill to automatically discover and generate JD Cloud network topology
  and resource inventory reports, and export cloud resources as a snapshot for
  baseline & drift detection. Triggers when the user asks to "scan network
  resources", "generate topology map", "inventory VPC resources", "check cloud
  resources", or "audit network structure", as well as "create baseline
  snapshots", "export HCL sketch", or "audit infrastructure drift" for a
  specific JD Cloud account. Supports both summary (brief) and detailed
  inventory modes, plus on-demand export and periodic baseline management.
  Keywords: 网络拓扑, 资源清单, VPC 探测, 云资源扫描, 网络审计, 基础设施基线,
  配置漂移检测, network topology, resource inventory, VPC scan, infra baseline,
  drift detection, topology render, JD Cloud, 京东云.
  Do NOT use for resource creation, modification, deletion, or troubleshooting.
  Read-only discovery only.
license: MIT
compatibility: >-
  Official JD Cloud CLI (`jdc`, Python 3.10+ package), valid API credentials
  configured in `~/.jdc/config` (CLI mode) or env vars `JDC_ACCESS_KEY` /
  `JDC_SECRET_KEY` (SDK fallback), network access to JD Cloud endpoints.
  Read-only operations (Describe/List/Get) strictly enforced.
metadata:
  author: jdcloud
  version: "1.0.0"
  last_updated: "2026-06-08"
  runtime: Harness AI Agent, Claude Code, Cursor, or compatible Agent runtimes
  type: cross-product-discovery
  cli_applicability: jdc-first-with-fallback
  cli_version_locked: "1.2.12"
  sdk_version_locked: ">=1.6.26"
  cli_support_evidence: >-
    Confirmed via `jdc --help` output showing the `vpc`, `vm`, `rds`, `redis`,
    `lb`, `iam`, `kms`, `ag`, `mongodb` products required for cross-product
    discovery. Official CLI documentation:
    https://docs.jdcloud.com/cn/cli/introduction
  environment:
    - JDC_ACCESS_KEY        # SDK mode; CLI reads from ~/.jdc/config INI
    - JDC_SECRET_KEY        # SDK mode; CLI reads from ~/.jdc/config INI
    - JDC_REGION            # Default region (e.g. cn-north-1)
---

> This skill follows the [Agent Skill OpenSpec](https://agentskills.io/specification).

# JD Cloud Network Topology Discovery Skill

## 🔒 READ-ONLY PRINCIPLE (不可打破)

本 Skill 的核心设计原则是 **Absolute Read-Only**。在执行任何操作前,Agent 必须遵守以下红线:

| 规则 | 说明 |
|------|------|
| **NO Write Operations** | 绝不执行任何 `create*`, `delete*`, `modify*`, `update*`, `associate*`, `disassociate*`, `attach*`, `detach*`, `enable*`, `disable*`, `reset*`, `start*`, `stop*`, `reboot*`, `restore*`, `failover*`, `attach*`, `detach*`, `schedule*` 操作 |
| **NO State Changes** | 绝不改变任何云资源的状态,包括但不限于实例开关机、安全组规则增删、EIP 绑定、备份执行等 |
| **NO Credential Exposure** | 绝不输出完整的 AK/Secret,输出中必须掩码为 `JDC_******` 或 `***` |
| **Read-Only API Only** | 仅允许调用 `describe*`, `list*`, `get*` 类 API(详见 [安全门规范](references/safety-gate.md)) |

**违反此原则 = 严重安全违规,立即 HALT 并向用户报告。**

## Overview

`jdcloud-topo-discovery` 是一个 **跨产品网络发现工具**,用于自动化扫描京东云账户下的 VPC 网络结构、关联资源(VM/RDS/Redis/CLB/EIP/SG/IAM/KMS),并生成结构化的网络拓扑图和资源清单报告。

> **本 skill 镜像 `alicloud-topo-discovery` 的方法论,适配京东云 `jdc` CLI 生态。**

### 核心特性

| 特性 | 说明 |
|------|------|
| **交互式模式选择** | 用户可选择"简报"(VPC/Subnet/CLB/EIP 摘要)或"详细报告"(全资源清单) |
| **树形拓扑视图** | 按参考模板格式输出 VPC → Subnet → 资源树形结构 |
| **多格式输出** | 支持 ASCII 树形图 + Mermaid 图 + Markdown 报告 |
| **多文档生成** | 可选生成单文件或拆分多文件(topology / inventory / summary) |
| **独立模板引擎** | 基于 `templates/` 下 `.md` 模板文件,支持变量替换和自定义 |
| **声明式安全门** | 执行前强制命令预检,确保无破坏性操作 |
| **基线管理** | 支持按日期归档拓扑快照,提供 `--diff` 漂移检测能力 |
| **HCL Sketch 导出** | 导出 `terraform show`-friendly 的 HCL 草图(注:京东云**无官方 Terraform provider**,此 HCL 仅作文档用途,不可 `terraform apply`) |

### 与现有 Skill 的关系

| 关系类型 | 说明 |
|---------|------|
| **不替代** | 本 Skill 不替代任何产品级 Skill(如 `jdcloud-vm-ops`, `jdcloud-mysql-ops`, `jdcloud-vpc-ops`) |
| **组合调用** | 本 Skill 通过调用各产品 API 的只读接口,实现跨产品拓扑聚合 |
| **发现 vs 操作** | 本 Skill 负责"发现",产品 Skill 负责"操作";若用户发现后需要修改资源,应引导至对应产品 Skill |
| **AIOps 集成** | 配合 `jdcloud-cloudmonitor-ops` + `jdcloud-alert-intelligence`,叠加健康状态覆盖层到拓扑中 |

## Trigger & Scope

### SHOULD Use This Skill When

- User 需要查看/扫描/探测/审计京东云网络拓扑
- User 需要获取 VPC 下的资源清单/资产列表
- User 需要了解账号下有哪些 VPC/EIP/CLB/VM/RDS
- User 需要生成网络架构图/资源报告
- User 需要创建基础设施基线快照 (`baseline`)
- User 需要比较两次基线间的配置变更 (`baseline-diff`)
- User 需要跨账号扫描资源 (使用 `--assume-role`)
- Keywords: 网络拓扑, VPC 结构, 资源清单, 云资源扫描, 基础设施基线, 拓扑图, 京东云资源盘点
- User 说"扫描一下网络", "看看有哪些资源", "生成拓扑图", "创建 baseline"

### SHOULD NOT Use This Skill When

- User 需要创建/修改/删除资源 → 引导至对应产品 Skill
- User 需要排查资源故障/性能问题 → 引导至监控/诊断 Skill
- User 需要查询账单/费用 → 引导至计费 Skill
- User 需要配置安全策略 → 引导至安全相关 Skill
- User 需要通过 `terraform apply` 创建云资源 → **本 skill 不支持**(京东云无官方 Terraform Provider)

## Delegation Rules

| 能力 | 委托目标 | 说明 |
|------|----------|------|
| 资源清单(VM) | `jdcloud-vm-ops` | 详见 `references/field-mappings/vm.md` |
| 资源清单(MySQL/PostgreSQL/MongoDB) | `jdcloud-mysql-ops` / `jdcloud-postgresql-ops` / `jdcloud-mongodb-ops` | 详见 `references/field-mappings/mysql.md` 等 |
| 资源清单(Redis) | `jdcloud-redis-ops` | 详见 `references/field-mappings/redis.md` |
| 资源清单(CLB) | `jdcloud-clb-ops` | 详见 `references/field-mappings/clb.md` |
| 资源清单(EIP) | `jdcloud-eip-ops` | 详见 `references/field-mappings/eip.md` |
| VPC/Subnet/ACL/Route/ENI | (无对应 skill,本 skill 自管) | `jdc vpc` 子命令直接调用 |
| 安全组 | (无对应 skill,本 skill 自管) | `jdc vpc describe-network-security-groups` |
| IAM 用户/策略 | `jdcloud-iam-ops` | 详见 `references/field-mappings/iam.md` |
| KMS 密钥 | `jdcloud-kms-ops` | 详见 `references/field-mappings/kms.md` |
| 高可用组 | (无对应 skill) | `jdc ag describe-ags` |
| 操作审计事件 | `jdcloud-audit-ops` | (本 skill 不直接采集审计事件,但 manifest 中可关联) |
| 健康状态叠加 | `jdcloud-cloudmonitor-ops` | (可选)叠加 CPU/内存/告警到拓扑中 |
| GCL 质量门禁 | N/A | 只读操作,不触发 GCL 质量门禁 |

## Quality Gate (GCL)

本 Skill 遵循 AGENTS.md §12 Generator-Critic-Loop 质量门。

### Rubric Dimensions

见 [references/gcl-rubric.md](references/gcl-rubric.md)。

| 维度 | 权重 | 说明 |
|---|---|---|
| **Correctness** | 25% | 拓扑关系和资源清单与实际情况一致 |
| **Safety** | 30% | 纯读操作,任何写操作为 0 |
| **Idempotency** | 15% | 同一输入多次扫描结果一致 |
| **Traceability** | 20% | 报告含完整执行上下文(命令、参数、输出路径) |
| **Spec Compliance** | 10% | 遵循 manifest-schema 和字段映射规范 |

### Sub-Mode Rubric

| Sub-Mode | Correctness 侧重点 | Safety 检查点 |
|----------|-------------------|---------------|
| scan-topo | 输出格式完整、拓扑关系准确 | 只读门禁 |
| export-hcl | 字段映射精度 | 无敏感泄露 |
| baseline | 目录结构完整 | 无数据删除 |
| baseline-diff | Diff 准确度 | 只读 Diff |

## Pre-flight Interaction (用户决策)

在执行扫描前,**必须** 向用户确认以下选项:

```
📋 拓扑扫描配置:

1. 报告模式 (必需):
   [1] 简报版 —— VPC + Subnet + CLB/EIP + 资源数量统计 (默认)
   [2] 详细版 —— 简报 + 所有 VM/RDS/Redis/SG/IAM/KMS 的完整属性和清单

2. 拓扑格式:
   [1] ASCII 树形图 —— 终端友好,直接可读 (默认)
   [2] Mermaid 图 —— 支持流程/渲染,适合文档嵌入
   [3] 两者都要

3. 输出结构:
   [1] 单文件 —— 所有内容写入 report.md (默认)
   [2] 多文件 —— topology.md + inventory.md + summary.md 拆分

4. 项目名称/标识 (可选):
   [输入]: 自定义报告标题前缀 (默认自动从 VPC 名称提取)

5. 凭证来源 (默认自动检测):
   - CLI 模式(默认): 读取 `~/.jdc/config` INI
   - SDK 模式(CLI 失败 3 次后降级): 读取 env vars `JDC_ACCESS_KEY` / `JDC_SECRET_KEY`

6. 健康状态叠加 (可选,与 `jdcloud-cloudmonitor-ops` 联动):
   [输入]: 监控 JSON 报告路径 (自动叠加健康状态到拓扑中)

请回复选项编号或描述,确认后开始扫描。
```

## Variable Convention

| Placeholder | Meaning | Source |
|-------------|---------|--------|
| `{{env.JDC_ACCESS_KEY}}` | AK ID | From runtime env (SDK mode), NEVER ask user |
| `{{env.JDC_SECRET_KEY}}` | AK Secret | From runtime env (SDK mode), NEVER exposed |
| `{{env.JDC_REGION}}` | Region | From runtime env, default `cn-north-1` |
| `{{user.report_mode}}` | 简报/详细 | User decision (step 1) |
| `{{user.topology_format}}` | ASCII/Mermaid | User decision (step 2) |
| `{{user.output_structure}}` | 单文件/多文件 | User decision (step 3) |
| `{{user.project_name}}` | 项目名 | User input or extracted from VPC name |
| `{{output.topology_data}}` | 扫描结果 | From CLI execution |
| `{{output.vpc_name}}` | VPC 名称 | From `jdc vpc describe-vpcs` response |

## Execution Flows

### Phase 1: Pre-flight Safety Check

**MANDATORY before any CLI execution:**

1. Verify credentials exist (SDK mode only — CLI uses `~/.jdc/config`):
   ```bash
   test -n "$JDC_ACCESS_KEY" && test -n "$JDC_SECRET_KEY" || echo "WARN: SDK env vars not set; CLI mode uses ~/.jdc/config"
   ```

2. Check CLI available and configured:
   ```bash
   command -v jdc >/dev/null || { echo "ERROR: jdc CLI not found"; exit 1; }
   test -f ~/.jdc/config || { echo "ERROR: ~/.jdc/config not found; run jdc configure add"; exit 1; }
   ```

3. Verify read-only mode (this is the **key safety gate**):
   - Scan the planned command list
   - Reject any command matching: `(create|delete|modify|update|associate|disassociate|attach|detach|enable|disable|reset|start|stop|reboot|restore|failover|schedule)`
   - If found → HALT and report to user

4. Test API connectivity (read-only):
   ```bash
   jdc --output json vpc describe-vpcs --region-id "$JDC_REGION" --page-size 1 >/dev/null 2>&1 || { echo "ERROR: API check failed"; exit 1; }
   ```

#### 📊 输出格式 (Token 效率优化)

所有 CLI 命令的 JSON 输出必须用 `jq` 过滤到最小必要字段,避免全量 JSON 输出造成 Token 浪费:

```bash
# 优化前: 输出全量 JSON(可能 100+ 行)
jdc --output json vpc describe-vpcs --region-id $REGION --page-size 100

# 优化后: 仅输出 ID + Name + CIDR
jdc --output json vpc describe-vpcs --region-id $REGION --page-size 100 \
  | jq '.result.vpcs[] | {vpcId, vpcName, addressPrefix, azType}'
```

各 API 的字段过滤规则见 `references/execution-commands.md` 的 JSON 输出路径映射。

### Phase 2: Parallel Data Collection

Execute CLI commands in parallel (background) for speed. 注意:**`jdc --output json` 必须放在子命令前**(在所有 jdc 京东云 CLI 中)。

> **注意**:`topo-scan.sh` 中实现了多 VPC 扫描 + 健康状态叠加 + Mermaid 图生成。
> 下面为示意流程,完整实现见 `scripts/topo-scan.sh`。

```bash
# VPC & Subnet (Foundation) — 先等 VPC 返回再查 Subnet
jdc --output json vpc describe-vpcs --region-id "$JDC_REGION" --page-size 100 > /tmp/topo_vpcs.json &
PID_VPC=$!

# 并行查 CLB/EIP/AG/SG/IAM/KMS
jdc --output json lb describe-load-balancers --region-id "$JDC_REGION" --page-size 100 > /tmp/topo_clbs.json &
jdc --output json eip describe-elastic-ips --region-id "$JDC_REGION" --page-size 100 > /tmp/topo_eips.json &
jdc --output json vpc describe-network-security-groups --region-id "$JDC_REGION" --page-size 100 > /tmp/topo_sgs.json &
jdc --output json ag describe-ags --region-id "$JDC_REGION" --page-size 50 > /tmp/topo_ags.json &
jdc --output json iam describe-sub-users --page-size 100 > /tmp/topo_iam.json &
jdc --output json kms describe-key-list --page-size 100 > /tmp/topo_kms.json &

# 等 VPC 返回后查 Subnet
wait $PID_VPC
FIRST_VPC_ID=$(jq -r '.result.vpcs[0].vpcId // empty' /tmp/topo_vpcs.json 2>/dev/null)
if [ -n "$FIRST_VPC_ID" ]; then
  jdc --output json vpc describe-subnets --region-id "$JDC_REGION" \
    --filters "vpcId=$FIRST_VPC_ID" --page-size 100 > /tmp/topo_subnets.json &
fi

# VM/RDS/Redis Instances (Optional for detailed mode)
if [ "$REPORT_MODE" = "detailed" ]; then
  jdc --output json vm describe-instances --region-id "$JDC_REGION" --page-size 100 > /tmp/topo_vms.json &
  jdc --output json rds describe-instances --region-id "$JDC_REGION" --page-size 100 > /tmp/topo_rds.json &
  jdc --output json redis describe-cache-instances --region-id "$JDC_REGION" --page-size 100 > /tmp/topo_redis.json &
fi

# Wait for remaining background jobs
wait
```

### Phase 3: Topology Generation (Template Rendering)

`topo-render.py` 自动完成:

1. 加载 `/tmp/topo_*.json` 数据
2. 构建 Subnet → 资源映射(VM/CLB/RDS 按归属子网分组)
3. 加载健康状态覆盖层(如果 `--health-json` 传入)
4. 生成输出:
   - **ASCII 树形图**:终端友好,`report.md`
   - **Mermaid 图**:可视化拓扑,支持渲染,`topology.mermaid.md`
5. 写文件到输出目录

> 旧有模板文件 `templates/vpc-topology.md` 保留作参考。完整渲染逻辑由 `topo-render.py` 实现。

### Phase 4: Report Compilation

**Single File Mode:**

支持 **ASCII 树形图 + Mermaid 图** 两种格式,可通过 Pre-flight 选项选择。

- ASCII 树形图:终端友好,直接可读
- Mermaid 图:支持渲染成可视化图表,适合文档嵌入

**Single File Mode:**
```markdown
# {{user.project_name}} - 网络拓扑与资源清单

> 生成时间: {{timestamp}}
> 区域: {{env.JDC_REGION}}
> 模式: {{user.report_mode}}

{{topology_output}}

---

{{inventory_output}}

---

{{statistics_output}}
```

**Multi-File Mode:**
- `topology.md`: VPC 树形图 + Mermaid 图
- `inventory.md`: 完整资源清单表
- `summary.md`: 摘要 + 架构分析 + 风险提示

### Phase 5: Post-Execution Verification

1. Verify output file exists and size > 0:
   ```bash
   test -s report.md && echo "Report generated successfully"
   ```

2. Check no credentials leaked:
   ```bash
   grep -E 'JDC_[A-Z0-9]{16,}|access_key\s*=|secret_key\s*=' report.md && { echo "WARNING: Possible credential leak"; exit 1; }
   ```

3. Verify read-only compliance (meta-check, no commands executed):
   - Confirm no write commands were in the execution log

## Failure Recovery

| Error Pattern | Max Retries | Backoff | Agent Action |
|--------------|-------------|---------|--------------|
| `InvalidAccessKeyId` / `secret key is null` | 0 | - | HALT. Credentials invalid. User must provide valid AK. |
| `SignatureDoesNotMatch` | 0 | - | HALT. AK/Secret mismatch or time skew. Check credentials. |
| `Forbidden.RAM` | 0 | - | HALT. Insufficient permissions. User needs `JDReadOnlyAccess` or custom read-only policy. |
| `Throttling` / 429 | 3 | Exponential | Back off 2s, 4s, 8s. Retry. |
| `InternalError` / 5xx | 3 | 2s fixed | Retry; continue with partial data if persistent. |
| `RegionId.NotExist` | 0 | - | HALT. Check `{{env.JDC_REGION}}`. |
| `InvalidVpcId.NotFound` | 0 | - | Skip VPC, continue scanning. |
| Command Timeout (>30s) | 1 | - | Kill process; log timeout; continue with other resources. |

---

## Well-Architected Assessment (卓越架构)

This skill's operations are evaluated against the JD Cloud Well-Architected Framework (参考 AWS WAF + 阿里云 WAF 适配京东云产品,详见 `references/waf-pillars.md` 的元认知层)。

### 安全 (Security)

| Area | Guidance |
|------|----------|
| **IAM** | Require: `JDReadOnlyAccess` only. Principle: least privilege, read-only access |
| **Credentials** | `{{env.*}}` only (SDK mode). All AK/Secret values in output must be masked (e.g., `JDC_***`) |
| **Data Sensitivity** | VPC IDs, instance IDs, and IP ranges are sensitive infrastructure data. Restrict report distribution |

### 稳定 (Stability)

| Area | Guidance |
|------|----------|
| **面向失败的架构设计** | Skip individual VPCs on error but continue scanning. Partial results are still valuable |
| **面向精细的运维管控** | Regular topology discovery enables change tracking and drift detection |
| **面向风险的应急快恢** | N/A (read-only skill). Use reports as baseline for post-incident infrastructure comparison |

### 成本 (Cost)

This skill uses read-only Describe APIs which are free. Minimal API call volume:
- **Optimization:** Use batch APIs where possible. Set `page-size` to 100 to minimize calls
- **Waste:** N/A for read-only discovery

### 效率 (Efficiency)

- **Parallel Collection:** VM/RDS/Redis/CLB/VPC APIs can be queried simultaneously
- **CI/CD Integration:** Run in CI pipeline for regular topology drift detection
- **JSON Output:** Compatible with `jq` for automated analysis

### 性能 (Performance)

| Operation | Expected API Calls | Time Estimate |
|-----------|-------------------|---------------|
| Full scan (all VPCs, multi-region) | ~15-20 Describe calls | < 30s |
| Brief mode | ~6-8 Describe calls | < 10s |
| + Health overlay | +0 (复用已有数据) | +0s |
| + HCL sketch export | ~10-15 API calls | < 60s |


## See Also — Meta-Skill Rules

This skill is subject to cross-cutting rules defined by the
[jdcloud-skill-generator](../jdcloud-skill-generator/SKILL.md) meta-skill.

- **[Code Snippets Rule](../jdcloud-skill-generator/templates/code-snippets.md)** —
  When `cli_applicability: sdk-only` (CLI 不足以覆盖完整功能,必须依赖 SDK/API 方式),
  the skill MUST provide `assets/code-snippets/` with runnable Python SDK code.
  **DOES NOT APPLY** — 本 skill 为 `jdc-first-with-fallback`,CLI 优先,SDK 作为 3 次失败后的降级,无需独立 code snippets。
