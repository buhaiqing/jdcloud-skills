---
name: jdcloud-vpc-ops
version: "1.1.0"
description: >-
  JD Cloud VPC (Virtual Private Cloud) operations — manage VPCs, Subnets,
  Security Groups (with rules), Route Tables, Network ACLs, and VPC Peering.
  Core infrastructure layer for all JD Cloud networking.
license: MIT
compatibility: >-
  JD Cloud CLI (`jdc`) 1.2.12+, Python 3.10 runtime (NOT 3.12+),
  valid API credentials (`~/.jdc/config` for CLI, `JDC_ACCESS_KEY`/`JDC_SECRET_KEY` env vars for SDK),
  network access to `vpc.jdcloud-api.com`.

metadata:
  api_profile: "JD Cloud VPC API v1 - https://docs.jdcloud.com/cn/virtual-private-cloud/api/overview"
  cli_version_locked: "1.2.12"
  sdk_version_locked: ">=1.6.26"
  python_version_minimum: "3.10"
  author: "jdcloud-skills"
  last_updated: "2026-06-18"
  type: product-operations
  cli_applicability: "jdc-first-with-fallback"
  gcl_classification: "recommended"
  gcl_max_iter: 3
  token_budget_estimate: "~6000 tokens (full VPC scan)"
  references_index:
    - path: "references/core-concepts.md"
      load_condition: "always"
    - path: "references/cli-usage.md"
      load_condition: "always"
    - path: "references/api-sdk-usage.md"
      load_condition: "当 SDK fallback 时"
    - path: "references/monitoring.md"
      load_condition: "当需要监控或告警时"
    - path: "references/integration.md"
      load_condition: "当跨 skill 协作时"
    - path: "references/troubleshooting.md"
      load_condition: "当执行出错时"
    - path: "references/rubric.md"
      load_condition: "当 GCL 执行时"
    - path: "references/prompt-templates.md"
      load_condition: "当 GCL 执行时"
---

# JD Cloud VPC Operations — jdcloud-vpc-ops

> **一句话定位**: 京东云 VPC 网络的"操作手"——创建、查询、更新、删除 VPC、子网、安全组(及规则)、路由表、网络 ACL 和 VPC 对等连接。所有京东云资源都依赖 VPC 网络层。

---

## 能力范围

本 Skill 管理以下京东云 VPC 核心资源:

| 资源 | CLI 子命令数 | 关键操作 | GCL 级别 |
|------|:----------:|---------|:--------:|
| **VPC** (私有网络) | 4 | create / describe / modify / delete | Safety check(delete) |
| **Subnet** (子网) | 4 | create / describe / modify / delete | Safety check(delete) |
| **Security Group** (安全组) | 4 | create / describe / modify / delete | Safety check(delete) |
| **Security Group Rules** (安全组规则) | 3 | add / modify / remove | Safety check(remove) |
| **Route Table** (路由表) | 4 | create / describe / modify / delete | 常规 |
| **Route Table Rules** (路由表规则) | 3 | add / modify / remove | 常规 |
| **Network ACL** (网络访问控制) | 4 | create / describe / modify / delete (绑定/解绑子网) | Safety check(delete) |
| **VPC Peering** (对等连接) | 4 | create / describe / modify / delete | Safety check(delete) |

**不在此 Skill 范围内**: 弹性公网IP (→ `jdcloud-eip-ops`)、NAT 网关 (→ `jdcloud-nat-ops`,待建)、带宽包 (→ `jdcloud-eip-ops`)、弹性网卡 (辅助,→ `jdcloud-topo-discovery`)。

---

## Trigger & Scope

### SHOULD Use

| 场景 | 用户表述示例 |
|------|-------------|
| 创建 VPC | "创建 VPC"、"创建 10.0.0.0/16 的私有网络" |
| 列出 VPC/子网/安全组 | "看看我有几个 VPC"、"列出安全组" |
| 创建子网 | "在 VPC xxx 下面创建一个 10.0.1.0/24 的子网" |
| 安全组规则管理 | "开放 80 端口"、"允许 10.0.0.0/8 访问 3306" |
| 路由表配置 | "添加一条指向 NAT 的路由" |
| ACL 管理 | "给子网绑定网络 ACL" |
| **读取操作** (describe-*) | "查询 VPC 详情"、"看看安全组规则" |

### SHOULD NOT Use

| 场景 | 委托给 |
|------|--------|
| 弹性公网 IP (EIP) | `jdcloud-eip-ops` |
| CLB 负载均衡 | `jdcloud-clb-ops` |
| VM 实例管理(含弹性网卡) | `jdcloud-vm-ops` |
| NAT 网关管理 | `jdcloud-nat-ops`(待建) |
| VPC 拓扑发现(批量) | `jdcloud-topo-discovery` |
| 架构评审(含 VPC) | `jdcloud-arch-advisor` |
| 全链路巡检(VPC 相关) | `jdcloud-aiops-cruise` |
| 标签相关操作 | `jdcloud-tag-audit-ops` |

---

## Variable Convention

### 环境变量 — `{{env.*}}`

| 变量 | 说明 | 来源 |
|------|------|------|
| `{{env.JDC_ACCESS_KEY}}` | 京东云 AccessKey ID | 运行时环境 (NEVER ask) |
| `{{env.JDC_SECRET_KEY}}` | 京东云 AccessKey Secret | 运行时环境 (NEVER ask, NEVER log) |
| `{{env.JDC_REGION}}` | 默认地域（如 `cn-north-1`） | 运行时环境 |

### 用户输入 — `{{user.*}}`

| 变量 | 说明 | 示例 |
|------|------|------|
| `{{user.vpc_name}}` | VPC 名称 | `"prod-beijing-vpc"` |
| `{{user.vpc_cidr}}` | VPC CIDR | `"10.0.0.0/16"` |
| `{{user.subnet_name}}` | 子网名称 | `"app-subnet-a"` |
| `{{user.subnet_cidr}}` | 子网 CIDR | `"10.0.1.0/24"` |
| `{{user.az}}` | 可用区 | `"cn-north-1a"` |
| `{{user.sg_name}}` | 安全组名称 | `"web-sg"` |
| `{{user.sg_rule_protocol}}` | 协议 | `tcp`, `udp`, `icmp`, `all` |
| `{{user.sg_rule_port}}` | 端口 | `80`, `3306`, `1-65535` |
| `{{user.sg_rule_cidr}}` | 源/目的 CIDR | `"0.0.0.0/0"`, `"10.0.0.0/8"` |
| `{{user.sg_rule_direction}}` | 方向 | `inbound` (0), `outbound` (1) |
| `{{user.safety_confirmed}}` | 删除操作确认 | `"I confirm deletion"` |

### 输出变量 — `{{output.*}}`

| 变量 | 说明 | 来源 |
|------|------|------|
| `{{output.vpc_id}}` | VPC ID | jdc vpc describe-vpcs → `$.result.vpcs[0].vpcId` |
| `{{output.vpc_name}}` | VPC 名称 | `$.result.vpcs[0].vpcName` |
| `{{output.subnet_id}}` | 子网 ID | `$.result.subnets[0].subnetId` |
| `{{output.sg_id}}` | 安全组 ID | `$.result.networkSecurityGroups[0].networkSecurityGroupId` |
| `{{output.rule_id}}` | 规则 ID | `$.result.networkSecurityGroupRuleIds[0]` |
| `{{output.route_table_id}}` | 路由表 ID | `$.result.routeTables[0].routeTableId` |
| `{{output.acl_id}}` | ACL ID | `$.result.networkAcls[0].networkAclId` |
| `{{output.peering_id}}` | 对等连接 ID | `$.result.vpcPeering.vpcPeeringId` |

---

## API and Response Conventions

### 通用 jdc 调用规范

```
jdc --output json vpc <sub-command> [--region-id REGION] [--param value ...]
```

**关键规则**:
1. `--output json` **必须**在 `vpc` 之前(不是之后)
2. `--region-id` 默认值来自 `~/.jdc/config` 中的 `region_id` 字段
3. 分页参数: `--page-number N --page-size N` (最大值 100)
4. 过滤器: `--filters "key=value"` (多个 filter 用空格分隔)
5. 列表查询 JSON path: `$.result.<resources>[]`
6. 安全组规则 specs 使用 JSON 数组字符串

### 统一 jdc 响应格式

```json
{
  "request_id": "xxx-xxx-xxx",
  "result": {
    "vpcs": [
      {
        "vpcId": "vpc-3p9mkq2v3a",
        "vpcName": "prod-beijing-vpc",
        "addressPrefix": "10.0.0.0/16",
        "description": "Production VPC",
        "createdTime": "2026-01-15T10:00:00+08:00",
        "azType": "standard"
      }
    ],
    "totalCount": 1
  },
  "error": null
}
```

### 统一 SDK 响应格式 (Python)

```python
{
  "request_id": "xxx-xxx-xxx",
  "result": Vpc describe-vpcs result object,
  "error": {
    "code": "InvalidParameter",
    "message": "The parameter VpcId is required",
    "status": "400"
  }  # or null for success
}
```

### 错误响应

```json
{
  "request_id": "xxx-xxx-xxx",
  "result": null,
  "error": {
    "code": "InvalidParameter",
    "message": "The parameter VpcId is required",
    "status": "400"
  }
}
```

错误码 | 含义 | Agent Action
--- | --- | ---
`InvalidParameter` | 参数错误 | 检查参数值和格式
`InvalidVpc.NotFound` | VPC 不存在 | 检查 vpcId,或先 list
`InvalidSubnet.NotFound` | 子网不存在 | 检查 subnetId
`QuotaExceeded` | 配额超限 | 提示用户提升配额
`VpcCIDRConflict` | CIDR 冲突 | 检查 CIDR 范围
`InvalidSecurityGroup.NotFound` | 安全组不存在 | 检查 sgId

---

## Execution Flows

### Flow 1: 查询 VPC / 子网 / 安全组 (读取,非 destructive)

```
User Request: "列出我的 VPC"
     │
     ▼
[0] Pre-flight
    ├─ 检查 jdc CLI 可用性 (which jdc)
    ├─ 检查 ~/.jdc/config 存在
    └─ 确认 region 参数
     │
     ▼
[1] Execute (jdc first)
    └─ jdc --output json vpc describe-vpcs [--region-id REGION]
         │
         ▼
    [1a] 成功 → 解析 $.result.vpcs → 输出表格 + 详细列表
    [1b] 失败 (retry up to 3×, 0s/2s/4s backoff)
         ├─ 仍失败 → SDK fallback: VpcClient().describe_vpcs()
         └─ 仍失败 → 返回友好错误 + 重试建议
                                   
[2] Output
    └─ 格式: Markdown 表格 + JSON (如需详细)
```

### Flow 2: 创建 VPC / 子网 / 安全组 (non-destructive,需确认)

```
User Request: "创建一个 VPC 10.0.0.0/16"
     │
     ▼
[0] Pre-flight
    ├─ CIDR 格式验证 (CIDR notation / netmask >= 16)
    ├─ 名称格式验证 (32 字符限)
    ├─ region 确认
    └─ (可选)现有 VPC CIDR 冲突检查
     │
     ▼
[1] User Confirmation
    └─ "即将创建 VPC: name=xxx, cidr=10.0.0.0/16, region=cn-north-1, 确认?"
         │ user confirms
         ▼
[2] Execute
    └─ jdc --output json vpc create-vpc --vpc-name xxx [--address-prefix 10.0.0.0/16]
         │
         ▼
    [2a] 成功 → 解析 $.result.vpcId
    [2b] 失败 → SDK fallback + retry 3×
                                   
[3] Validate
    └─ jdc --output json vpc describe-vpc --vpc-id {{output.vpc_id}}
         └─ 验证 status = "available"
```

### Flow 3: 安全组规则管理 (高风险,需严格确认)

```
User Request: "开放 80 端口到 0.0.0.0/0"
     │
     ▼
[0] Pre-flight
    ├─ 确认目标安全组 ID
    ├─ 协议映射: tcp→6 udp→17 icmp→1 all→300
    ├─ 方向映射: inbound→0 outbound→1
    └─ 端口范围验证 (1-65535)
     │
     ▼
[1] **Safety Gate** — 验证规则不违反已有安全策略
    ├─ 检查是否已有相同规则 (防重复)
    ├─ 检查 0.0.0.0/0 端口范围是否必要
    └─ 高危操作(0.0.0.0/0 + 22/3389): 要求额外确认
     │
     ▼
[2] User Confirmation
    └─ "即将添加规则: sg=sg-xxx, protocol=TCP, port=80, cidr=0.0.0.0/0, direction=inbound"
         │ user confirms
         ▼
[3] Execute
    └─ jdc --output json vpc add-network-security-group-rules \
         --network-security-group-id sg-xxx \
         --network-security-group-rule-specs \
         '[{"protocol":6,"direction":0,"addressPrefix":"0.0.0.0/0","fromPort":80,"toPort":80,"description":"HTTP"}]'

[4] Validate
    └─ jdc --output json vpc describe-network-security-group \
         --network-security-group-id sg-xxx
         └─ 验证规则已添加
```

### Flow 4: 删除资源 (destructive,强安全门)

```
User Request: "删除 VPC xxx"
     │
     ▼
[0] Pre-flight
    ├─ 检查 VPC 内无子网/资源 (预删除检查)
    ├─ 识别影响范围 (所有关联资源)
    └─ 标记 high-severity
     │
     ▼
[1] **Safety Gate** — 严格逐项确认
    ├─ 安全组规则删除: 确认规则数量 + 显示将被删除的规则
    ├─ 子网删除: 确认子网内无 EIP/VM/CLB 等关联资源
    └─ VPC 删除: 确认 VPC 内所有资源已清理
     │
     ▼
[2] **Explicit User Confirmation**
    └─ "⚠️ 高危操作确认: 即将删除 VPC xxx (cidr=10.0.0.0/16)。
          将同时删除关联的 3 个子网、5 个安全组、2 个路由表。
          请输入 'I confirm deletion of VPC xxx' 以继续。"
         │ user types exact confirmation
         ▼
[3] Execute
    └─ jdc --output json vpc delete-vpc --vpc-id xxx [--region-id REGION]
         │
         ▼
    [3a] 成功 → 输出删除确认
    [3b] 错误 (VPC 内还有资源) → 列出剩余资源,提示清理
```

---

## Output Parsing Rules

| 响应字段 | JSON Path | 类型 | 说明 |
|---------|-----------|------|------|
| VPC ID | `$.result.vpc.vpcId` | string | `vpc-xxxxxxxx` |
| VPC 名称 | `$.result.vpc.vpcName` | string | — |
| VPC CIDR | `$.result.vpc.addressPrefix` | string | `10.0.0.0/16` |
| VPC 列表 | `$.result.vpcs[]` | array | 每个元素同上 |
| 总 VPC 数 | `$.result.totalCount` | int | — |
| 子网 ID | `$.result.subnet.subnetId` | string | — |
| 子网名称 | `$.result.subnet.subnetName` | string | — |
| 子网 CIDR | `$.result.subnet.addressPrefix` | string | — |
| 子网列表 | `$.result.subnets[]` | array | — |
| 安全组 ID | `$.result.networkSecurityGroup.networkSecurityGroupId` | string | — |
| 安全组名称 | `$.result.networkSecurityGroup.networkSecurityGroupName` | string | — |
| 安全组列表 | `$.result.networkSecurityGroups[]` | array | — |
| 安全组规则 ID | `$.result.networkSecurityGroupRuleIds[]` | array | 添加规则时返回 |
| 路由表 ID | `$.result.routeTable.routeTableId` | string | — |
| 路由表列表 | `$.result.routeTables[]` | array | — |
| ACL ID | `$.result.networkAcl.networkAclId` | string | — |
| 对等连接 ID | `$.result.vpcPeering.vpcPeeringId` | string | — |

### 安全组规则 JSON 格式 (protocol 数值映射)

```json
{
  "protocol": 6,        // 300=All, 6=TCP, 17=UDP, 1=ICMP
  "direction": 0,       // 0=inbound, 1=outbound
  "addressPrefix": "0.0.0.0/0",
  "fromPort": 80,
  "toPort": 80,
  "description": "HTTP inbound"
}
```

---

## State Transition Tables

### VPC

| 操作 | 起始状态 | 结果 | 备注 |
|------|---------|------|------|
| create | N/A | available | 默认 VPC 自动创建默认 sec group + route table |
| modify | available | available | 修改名称/描述 |
| delete | available | — | VPC 必须 empty (无子网/资源) |

### 子网

| 操作 | 起始状态 | 结果 |
|------|---------|------|
| create | N/A | available |
| modify | available | available |
| delete | available | — |

### 安全组规则

| 操作 | 起始状态 | 结果 | 备注 |
|------|---------|------|------|
| add | active | active | 规则瞬时生效 |
| modify | active | active | 修改后旧规则失效 |
| remove | active | — | 删除后规则消失 |

---

## Failure Recovery

| 错误模式 | jdc 错误码 | 重试 | Agent Action |
|---------|-----------|:----:|-------------|
| 参数缺失 | InvalidParameter | 0 | 检查参数后重试 |
| CIDR 冲突 | VpcCIDRConflict | 0 | 建议一个新 CIDR |
| 配额超限 | QuotaExceeded | 0 | 引导到配额提升流程 |
| 安全组不存在 | InvalidSecurityGroup.NotFound | 0 | 先 list 可用 SG |
| 子网有资源待删除 | InvalidSubnet.ServiceDependence | 0 | 列出子网内资源并清理 |
| 对等连接已存在 | InvalidVpcPeering.AlreadyExists | 0 | 检查已有对等连接 |
| VPC 不存在 | InvalidVpc.NotFound | 0 | 检查 vpcId |
| API 限流 | 429 | 3 (exp backoff) | 等待后重试 |
| CLI 超时 | N/A | 3 (2s/4s/8s) | 增加 timeout |
| SDK 连接错误 | N/A | 3 (0s/2s/4s) | fallback 到 SDK |
| CLI 不可用 | N/A | 0 | pip install jdcloud_cli |
| Python 版本不匹配 | ImportError | 0 | 提示 Python 3.10 必须 |

---

## Delegation Rules

| 能力 | 委托目标 | 说明 |
|------|---------|------|
| EIP 创建/关联/释放 | `jdcloud-eip-ops` | VPC 内资源绑定 EIP |
| CLB 负载均衡 | `jdcloud-clb-ops` | CLB 关联到 VPC 子网 |
| VM 创建/管理 | `jdcloud-vm-ops` | VM 需指定 VPC + 子网 |
| 架构评审 | `jdcloud-arch-advisor` | Mode A 采集 VPC 拓扑 |
| 拓扑发现(批量) | `jdcloud-topo-discovery` | 全资源拓扑扫描 |
| 全链路巡检 | `jdcloud-aiops-cruise` | 链路诊断依赖 VPC 拓扑 |
| NAT 网关(待建) | `jdcloud-nat-ops` | 待创建 |
| 对象存储 OSS (待建) | `jdcloud-oss-ops` | 待创建 |

---

## Quality Gate (GCL)

> This skill participates in the repository-wide **Generator-Critic-Loop**
> (GCL) defined in [`AGENTS.md` §Quality Gate](../AGENTS.md#generator-critic-loop-gcl--adversarial-quality-gate).
> The quality gate is **recommended** for this skill (per `AGENTS.md` §8).

### Parameters (override `AGENTS.md` §8 defaults)

| Parameter | Value | Reason |
|---|---|---|
| `max_iterations` | **3** | `AGENTS.md` §8 default for `jdcloud-vpc-ops` (recommended) |
| `rubric_version` | `v2` | see [rubric.md](references/rubric.md) |
| `trace_path` | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | unified with `jdcloud-audit-ops` |
| `safety_confirm_required` | **true** for `delete-vpc`, `delete-subnet`, `delete-network-security-group` | matches repository safety gate policy |
| `hallucination_check` | **recommended** | Phase 6 H layer; MANDATORY for CLI parameter existence |
| `reflexion_integration` | **enabled** | Phase 7 lightweight Reflexion; loads `docs/failure-patterns.md` |

### Loop overview

```
User request
   │
   ▼
[0] Pre-flight (Orchestrator)
    - resolve env.* and user.* variables
    - pick skill, load its rubric
    - optionally load failure-patterns.md
   │
   ▼
[1] Generate (G)
    - generate command/payload (DO NOT execute yet)
   │
   ▼
[1.5] Hallucination Detection (H) ──► pre-execution structural validity check
   │   (recommended for vpc-ops)      - CLI parameter existence
   │                                    - JSON structure compliance
   │
   ├── PASS → [1a] Execute (run jdc / SDK)
   ├── FAIL → [1b] Regenerate (H retriggers G with hallucination report; max 1 retry)
   │         still FAIL → HALT with "HALLUCINATION_ABORT"
   ▼
[2] Critique (C)
    - isolated prompt context
    - score every rubric dimension
    - emit actionable suggestions
   │
   ▼
[3] Decide (Orchestrator)
    - HALLUCINATION_ABORT → ABORT (no partial)
    - Safety=0  → ABORT (no partial)
    - all pass  → RETURN
    - else & iter<max → inject suggestions into G
    - else → RETURN best + unresolved rubric items
```

### Hallucination Detection Layer (H) — Recommended

> **Purpose**: Catch LLM-generated CLI/SDK calls that contain structurally invalid elements
> **before** they reach the JD Cloud VPC API.

**Two-Category Check (for vpc-ops):**

| Category | Check | Method |
|---|---|---|
| **CLI Parameter Existence** | Verify every `--flag` exists in `jdc vpc <operation> --help` | Compare against `references/api-sdk-usage.md` operation tables |
| **JSON Structure Compliance** | For JSON payloads in create/update operations | Validate field nesting matches OpenAPI schema |

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

**Pre-flight Retrieval (Optional):**

During GCL Pre-flight (step [0]), the Orchestrator MAY:

```bash
# 1. Load docs/failure-patterns.md (lazy-load, ~150 lines)
# 2. Filter patterns by current skill name (jdcloud-vpc-ops)
# 3. Inject top-3 relevant patterns into Generator context as prevention hints

# Example injection:
"Known failure patterns for this skill:
- InvalidVpcId: VPC ID must be in format 'vpc-xxxxxxxx'
- Subnet deletion: Must verify subnet is empty before delete-subnet
- Security group rules: 0.0.0.0/0 on high-risk ports requires explicit confirmation"
```

**This is a HINT, not a CONSTRAINT** — the Generator should use these patterns to avoid known mistakes.

**Failure Pattern Extraction:**

When a GCL iteration fails, the Orchestrator SHOULD extract a structured failure pattern:

```json
{
  "failure_pattern": {
    "category": "cli_parameter" | "skill_generation" | "cross_skill" | "runtime",
    "skill": "jdcloud-vpc-ops",
    "command": "jdc vpc describe-vpcs --vpcId vpc-xxx",
    "error": "InvalidParameter: InvalidVpcId",
    "fix": "Validated VPC ID format before execution",
    "reusable": true
  }
}
```

### Artifacts

- Rubric (concrete scoring rules): [references/rubric.md](references/rubric.md)
- Prompt templates (G / C / O / H): [references/prompt-templates.md](references/prompt-templates.md)
- Failure patterns (cross-session memory): [docs/failure-patterns.md](../docs/failure-patterns.md)

### Per-Operation Safety Rules

| 操作 | Safety 要求 | 备注 |
|------|------------|------|
| `create-*` | 无需 Safety 门 | 但需 CIDR 冲突检查 |
| `delete-vpc` | Safety=1 | VPC 必须为空 |
| `delete-subnet` | Safety=1 | 子网内无资源 |
| `delete-network-security-group` | Safety=1 | 不与其他资源关联 |
| `remove-security-group-rules` | Safety=1 | 显式确认规则列表 |
| `add-security-group-rules` | Safety=0.5 | 0.0.0.0/0 高危端口需确认 |
| `modify-*` | 常规 | — |
| `describe-*` | 无 | — |

### Operation-specific behavior

- **`delete-vpc`** — Destructive. VPC must be empty (no subnets, no resources). Safety=1 required. H layer validates vpcId format.
- **`delete-subnet`** — Destructive. Subnet must be empty. Safety=1 required.
- **`delete-network-security-group`** — Destructive. SG must not be associated with any resources. Safety=1 required.
- **`add-security-group-rules`** — Non-destructive but high-risk when adding 0.0.0.0/0 on high-risk ports (22, 3389, etc.). Safety=0.5 required.
- **`create-*`** — Non-destructive but requires CIDR validation and conflict checking.
- **`describe-*`** — Read-only. No safety gate required.

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.1.0 | 2026-06-18 | **GCL v2 rollout**: Upgraded to GCL v2 with Phase 6 (Hallucination Detection Layer H — recommended, MANDATORY for CLI parameter existence) and Phase 7 (Lightweight Reflexion Integration — enabled, loads `docs/failure-patterns.md`). Changed GCL classification from `required` to `recommended` with `max_iterations=3`. Added `HALLUCINATION_ABORT` termination condition. Added operation-specific H layer behavior for delete/create/describe operations. Rubric version bumped to v2. |
| 1.0.0 | 2026-06-08 | Initial release: VPC / Subnet / Security Group / Route Table / ACL / Peering management |