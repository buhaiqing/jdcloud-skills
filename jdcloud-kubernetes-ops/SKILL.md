---
name: jdcloud-kubernetes-ops
description: >-
  Use this skill to manage JD Cloud JCS for Kubernetes: deploy, configure,
  troubleshoot, or monitor via API/SDK or `jdc` CLI. Trigger for Kubernetes,
  容器服务, Kubernetes集群, K8s, or tasks involving cluster lifecycle, node
  groups, kubeconfig credentials, or workload orchestration — even without
  explicit "Kubernetes" or "JCS" mention.
license: MIT
compatibility: >-
  Official JD Cloud SDK (Python 3.10+), valid API credentials, network
  access to JD Cloud endpoints. `jdc kubernetes` CLI subcommand exists but
  is BROKEN in locked version (jdcloudHeaders bug) — see Current Status.
metadata:
  author: buhaiqing
  version: "1.5.2"
  last_updated: "2026-06-19"
  runtime: Harness AI Agent
  api_profile: "JD Cloud JCS for Kubernetes API - https://nc.jdcloud-api.com/v1"
  cli_applicability: sdk-or-api-only
  cli_version_locked: "1.2.12"
  sdk_version_locked: ">=1.6.26"
  cli_support_evidence: >-
    VERIFIED: `jdc kubernetes` 子命令存在（包含 describe-clusters, create-cluster 等操作），
    但存在已知 bug：执行时返回 'Namespace' object has no attribute 'jdcloudHeaders' 错误。
    `jdc nc` 是 Native Container（容器实例），不是 Kubernetes 集群管理。
    当前锁定版本 jdcloud_cli==1.2.12 的 `jdc kubernetes` 命令不可用，
    所有 CLI 示例均为期望语法，实际执行应使用 SDK/API。
    Official CLI documentation: https://docs.jdcloud.com/cn/cli/introduction
  environment:
    - JDC_ACCESS_KEY
    - JDC_SECRET_KEY
    - JDC_REGION
  dependencies:
    - jdcloud-aiops-cruise (k8s_analyzer.py for workload analysis)
    - kubernetes>=25.3.0 (K8s Python client for storage operations)
---

> This skill follows the [Agent Skill OpenSpec](https://agentskills.io/specification).

# JD Cloud JCS for Kubernetes Operations Skill

## Overview

JD Cloud JCS for Kubernetes (容器服务/JCSKubernetes) is a fully managed Kubernetes service. This skill provides operational runbooks for cluster lifecycle, node groups, kubeconfig, storage (PV/PVC), workloads (Pod/Service/Deployment/HPA/Ingress), diagnostics, and CloudShell integration.

**Execution Strategy:** SDK/API primary (CLI `jdc kubernetes` is BROKEN in v1.2.12 — see [CLI Usage](references/cli-usage.md)).

**Key Capabilities:**
- Cluster & Node Group CRUD with safety gates
- Storage management (PV/PVC/StorageClass) via K8s Python client
- Workload operations (Pod/Service/Deployment/HPA/Ingress) with health checks
- CloudShell-based kubectl execution with graceful degradation
- Cross-resource diagnostics and performance analysis

### Dependency Notice

This skill integrates with `jdcloud-aiops-cruise` for workload analysis before destructive operations. Before deleting any cluster, the Agent MUST verify zero running workloads (via `k8s_analyzer`, `jdc describe-cluster`, or `kubectl get all`) and obtain explicit user confirmation. See [Integration](references/integration.md) for details.

## Trigger & Scope (Agent-Readable)

### SHOULD Use This Skill When

- User explicitly mentions "JD Cloud Kubernetes", "JCS for Kubernetes", "容器服务", "K8s集群", "Kubernetes cluster", "JCSKubernetes"
- Task involves cluster lifecycle: create, describe, modify, delete, list clusters
- Task involves node group management: create, scale, describe, delete node groups
- Task involves cluster credentials: obtain kubeconfig for kubectl access
- Task involves storage management: PV, PVC, StorageClass operations
- Task involves workload management: Pod, Service, Deployment, HPA, Ingress
- Task involves diagnostics: health checks, performance analysis, troubleshooting
- Task involves CloudShell: remote kubectl execution, data collection
- Keywords: createCluster, describeClusters, deleteCluster, createNodeGroup, kubeconfig, PV, PVC, Pod, Service, Deployment, HPA, Ingress, diagnostics, CloudShell

### SHOULD NOT Use This Skill When

- Task is billing/account management → delegate to: `jdcloud-billing-ops`
- Task is IAM/permission model → delegate to: `jdcloud-iam-ops`
- Task is VPC/subnet/security group → delegate to: `jdcloud-vpc-ops`
- Task is VM/ECS management → delegate to: `jdcloud-vm-ops`
- Task is container registry → delegate to: `jdcloud-cr-ops`
- Task is monitoring metrics/alarms → delegate to: `jdcloud-cloudmonitor-ops`
- Task is load balancer for K8s services → delegate to: `jdcloud-clb-ops`
- Task is helm/kubectl apply → recommend using kubectl directly

### Delegation Rules

- If cluster requires VPC/subnet resources, verify or create them via `jdcloud-vpc-ops` first.
- If cluster requires CLB for service exposure, delegate LB configuration to `jdcloud-clb-ops`.
- If user asks about cluster monitoring metrics or alarm rules, delegate metric queries to `jdcloud-cloudmonitor-ops`.
- For IAM role/policy management related to cluster access, delegate to `jdcloud-iam-ops`.
- Before deleting a cluster, use `jdcloud-aiops-cruise.kubernetes.k8s_analyzer` to check running workloads.
- Multi-product requests: handle each product with its dedicated skill; do not merge unrelated APIs into one ambiguous flow.

## Variable Convention (Agent-Readable)

Structured placeholders reduce injection ambiguity and unsafe prompts:

| Placeholder | Meaning | Agent Action |
|-------------|---------|--------------|
| `{{env.JDC_ACCESS_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_SECRET_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_REGION}}` | From runtime environment | Use `cn-north-1` as default if unset |
| `{{user.region}}` | User-supplied region | Ask once; reuse |
| `{{user.cluster_id}}` | User-supplied cluster ID | Ask once; reuse |
| `{{user.cluster_name}}` | User-supplied cluster name | Ask once; reuse |
| `{{user.node_group_id}}` | User-supplied node group ID | Ask once; reuse |
| `{{user.node_group_name}}` | User-supplied node group name | Ask once; reuse |
| `{{user.master_version}}` | Kubernetes version for cluster | Ask once; reuse |
| `{{user.node_count}}` | Node count for node group | Ask once; reuse |
| `{{user.instance_type}}` | VM instance type for nodes | Ask once; reuse |
| `{{user.vpc_id}}` | VPC ID from user or previous step | Ask once; reuse |
| `{{user.subnet_id}}` | Subnet ID from user or previous step | Ask once; reuse |
| `{{output.cluster_id}}` | From last API or CLI JSON response | Parse from `$.result.clusterId` |
| `{{output.node_group_id}}` | From last API or CLI JSON response | Parse from `$.result.nodeGroupId` |

> **`{{env.*}}` MUST NOT** be collected from the user. **`{{user.*}}`** MUST be collected interactively when missing.

> **Security Warning:** **NEVER** log, print, or expose `JDC_SECRET_KEY` (or any secret) in console output, debug messages, or logs. When verification is needed, check existence only (e.g., `if os.environ.get('JDC_SECRET_KEY')`) without printing the actual value. If logging credential status is required, use masked placeholders like `JDC_SECRET_KEY=<masked>` or `JDC_SECRET_KEY=***`. This applies to all execution flows (SDK, CLI, and debugging scripts).

## API and Response Conventions (Agent-Readable)

- **OpenAPI is canonical** for path, query, body fields, enums, and response shapes. Base path: `https://nc.jdcloud-api.com/v1/regions/{regionId}/...`
- **Errors:** Map SDK/HTTP errors to `code` / `status` / message fields per spec.
- **Timestamps:** ISO 8601 with timezone when the API returns strings.
- **Idempotency:** Cluster names are unique per region; duplicate name returns `ResourceAlreadyExists`.

For response field tables, state transitions, and detailed examples, see [API & SDK Usage](references/api-sdk-usage.md).

## Idempotency Rules (Agent-Readable)

> **Core Principle:** All snippets operations MUST be idempotent — calling the same operation multiple times MUST produce the same end state without side effects.

### Idempotency Contract

| Operation | Idempotency Behavior | Return on Repeated Call |
|-----------|---------------------|------------------------|
| **Create** (cluster, PVC, node group) | Check existence first; if exists, return existing resource info | `{"message": "... already exists (idempotent)"}` |
| **Delete** (pod, PVC, cluster) | If resource doesn't exist, return success (target state achieved) | `{"deleted": true, "message": "... does not exist (idempotent)"}` |
| **Scale/Modify** | Apply desired state; if already at desired state, no-op | Return current state with `{"message": "already at desired state"}` |
| **Health Check** | Naturally idempotent (read-only) | Always returns current state |
| **List/Describe** | Naturally idempotent (read-only) | Always returns current state |

### Implementation Rules

1. **Create operations**: MUST check resource existence before creation. If exists, return existing resource info with idempotent marker.
2. **Delete operations**: MUST handle `K8sResourceNotFoundError` gracefully. If resource doesn't exist, return `deleted: true` (target state achieved).
3. **Scale/Modify operations**: SHOULD compare current state with desired state. If already matching, return no-op result.
4. **All operations**: MUST use `K8sResourceNotFoundError` (not raw `ApiException`) for 404 handling.
5. **Return value**: Idempotent operations MUST include `"message"` field with `"(idempotent)"` marker when target state was already achieved.

### Examples

```python
# Delete Pod: second call returns idempotent success if already deleted
result = delete_pod("my-pod", "default")

# Create PVC: second call returns existing PVC info
result = create_pvc("my-pvc", "default", size="10Gi")
```

### Safety Gate Exception

**Destructive operations** (delete cluster, delete node group with workloads) still REQUIRE explicit user confirmation even though they are idempotent. Idempotency prevents accidental double-execution damage but does NOT bypass safety gates.

## Runbooks (巡检 Runbook)

This skill includes structured inspection runbooks for proactive Kubernetes cluster health monitoring and resource optimization:

- [Runbook Index](runbooks/00-index.md) — overview of all runbooks
- [01 - 集群健康巡检](runbooks/01-cluster-health-check.md) — cluster status, node health, pod distribution, ingress health, security posture
- [02 - 资源配置优化](runbooks/02-resource-optimization.md) — CPU/Mem requests alignment, HPA reasonability, resource waste detection, node water-level analysis

All runbooks follow the **Perceive → Reason → Execute** three-phase model. The Execute phase is **read-only** — it generates recommendations but delegates actual changes to the Execution Flows in [references/execution-flows.md](references/execution-flows.md).

## Changelog

See [references/changelog.md](references/changelog.md).

## Execution Flows (Agent-Readable)

Every operation: **Pre-flight → Execute (SDK/API primary) → Validate → Recover**. Do not skip phases.

**执行策略说明:** SDK/API 为主要执行路径。CLI (`jdc kubernetes`) 在当前锁定版本 (1.2.12) 中运行时崩溃，详见 [CLI Usage](references/cli-usage.md)。

**Snippets 模块:** 所有 K8s 操作已封装为可复用的 snippets 模块，位于 `scripts/snippets/`：
- `cluster_ops.py` — 集群 CRUD (jdcloud_sdk)
- `node_group_ops.py` — 节点组 CRUD + 扩缩容 (jdcloud_sdk)
- `credential_ops.py` — Kubeconfig 获取 (jdcloud_sdk)
- `storage_ops.py` — PV/PVC/StorageClass 管理 (kubernetes client)
- `workload_ops.py` — Pod/Service/Deployment/HPA/Ingress 操作 (kubernetes client)
- `cloudshell_ops.py` — CloudShell 远程 kubectl 执行
- `diagnostics_ops.py` — 跨资源异常聚合与性能分析
- `k8s_client.py` — 统一 K8s 客户端初始化和错误处理

所有操作的完整代码示例、安全门和降级策略见 [Execution Flows](references/execution-flows.md)。

## Quality Gate (GCL)

This skill uses the repository-wide **Generator-Critic-Loop** (GCL) defined in [`AGENTS.md`](../AGENTS.md#generator-critic-loop-gcl--adversarial-quality-gate).

### Parameters

| Parameter | Value | Reason |
|---|---|---|
| `max_iterations` | **3** | `AGENTS.md` §8 default for `recommended` skills |
| `rubric_version` | `v2` | See [rubric.md](references/rubric.md) |
| `trace_path` | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | Unified with `jdcloud-audit-ops` |
| `safety_confirm_required` | **true** for `delete-cluster`, `delete-node-group` | Destructive operations require explicit confirmation |
| `hallucination_check` | **recommended** | Phase 6 H layer: validate CLI parameter existence |
| `reflexion_integration` | **enabled** | Phase 7: load `docs/failure-patterns.md` |

### Loop Flow

```
User Request
  │
  ▼
[0] Pre-flight → resolve vars, load rubric, optional failure-patterns
[1] Generate → create command/payload (no execution)
[1.5] Hallucination Detection → validate CLI params / JSON structure
[2] Critique → score rubric, emit suggestions
[3] Decide → PASS / RETRY / ABORT
```

Termination: `PASS` | `MAX_ITER` | `SAFETY_FAIL` (abort) | `HALLUCINATION_ABORT` (abort).

### Operation-Specific Behavior

- **`delete-cluster`** — Destructive. MUST invoke `k8s_analyzer` pre-check. Safety=1 required.
- **`delete-node-group`** — Destructive. MUST drain nodes before deletion. Safety=1 required.
- **`create-cluster`** / **`create-node-group`** — Validate CIDR and quota.
- **`describe-*`** — Read-only. No safety gate.

For rubric details, prompt templates, and H-layer/Reflexion specifications, see [rubric.md](references/rubric.md) and [prompt-templates.md](references/prompt-templates.md).

## Reference Directory

- [Runbook Index](runbooks/00-index.md)
- [Core Concepts](references/core-concepts.md)
- [CLI Usage](references/cli-usage.md)
- [API & SDK Usage](references/api-sdk-usage.md)
- [Troubleshooting Guide](references/troubleshooting.md)
- [Monitoring & Alerts](references/monitoring.md)
- [Integration](references/integration.md)
- [GCL Rubric](references/rubric.md)
- [GCL Prompt Templates](references/prompt-templates.md)
- [Changelog](references/changelog.md)
- [Example Config](assets/example-config.yaml)

## Prerequisites

- **Python 3.10 is REQUIRED** (`jdcloud_cli==1.2.12` is incompatible with Python 3.12).
- **Runtime**: `uv` virtual environment with `jdcloud_sdk` and `kubernetes>=25.3.0`.
- **Credentials**: SDK uses `JDC_ACCESS_KEY` / `JDC_SECRET_KEY` / `JDC_REGION` env vars. `jdc` CLI reads from `~/.jdc/config` (expected syntax only — `jdc kubernetes` is broken in v1.2.12).
- **Security**: Never commit real credentials. Use `{{env.*}}` placeholders.

Complete setup, credential configuration, and SDK verification examples are in [CLI Usage](references/cli-usage.md) and [API & SDK Usage](references/api-sdk-usage.md).

For operational best practices, see [Core Concepts](references/core-concepts.md).
