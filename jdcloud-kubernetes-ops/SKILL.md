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
  version: "1.4.0"
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

JD Cloud JCS for Kubernetes (容器服务/JCSKubernetes) is a fully managed Kubernetes service that simplifies deploying, managing, and scaling containerized applications. It provides automated cluster lifecycle management, node group scaling, security patching, and integration with JD Cloud networking and storage services. This skill is an **operational runbook** for agents: explicit scope, credential rules, pre-flight checks, **jdc-first execution with SDK/API fallback**, response validation, and failure recovery. **Do not use the web console as the primary agent execution path** in `SKILL.md`.

### CLI applicability (repository policy)

- **`cli_applicability: jdc-first-with-fallback`:** Official `jdc` supports this product through the `nc` (Native Container) subcommand. The Agent MUST attempt to use `jdc` as the **primary execution path**. If `jdc` installation or command execution fails, the Agent MUST retry up to **3 times** (with exponential backoff). Only after **3 consecutive failures** should the Agent fall back to **SDK/API**. Both paths MUST be documented. You **MUST** ship **`references/cli-usage.md`** and, in **each** execution flow below, document **both** the `jdc` step **and** the SDK fallback step for every operation the CLI exposes.

### Path Preference (jdc-first with SDK Fallback)

The Agent MUST follow this execution priority:

1. **`jdc` CLI (primary path)** — Attempt `jdc` first for every operation. Quick ad-hoc operations, shell automation, and single-operation tasks benefit most from CLI.
2. **Retry up to 3 times** if `jdc` fails (with exponential backoff: 0s → 2s → 4s).
3. **SDK/API (fallback path, after 3 jdc failures)** — Use only when `jdc` is persistently unavailable. Complex multi-step workflows with conditional logic, CI/CD pipelines with Python tooling, and integration tests may require SDK.

When both paths succeed, prefer `jdc` output for consistency with the primary path.

### Critical jdc CLI Behavioral Notes (from empirical testing)

**Failure 1: `--output json` must be TOP-LEVEL, not subcommand-level**
The `--output json` argument is defined in the base controller (`base_controller.py`), not in individual subcommands. Cement's nested argparse structure restricts `--output` to be placed **before** the subcommand.

```
# CORRECT (works):
jdc --output json nc describe-clusters --region-id cn-north-1 --page-number 1 --page-size 100

# WRONG (fails with "unrecognized arguments: --output json"):
jdc nc describe-clusters --region-id cn-north-1 --page-number 1 --page-size 100 --output json
```

**Failure 2: jdc CLI does NOT support `--no-interactive`**
The `--no-interactive` flag does not exist in the jdc CLI argument definition. Using it will cause an `unrecognized arguments` error. Omit this flag entirely.

**Failure 3: jdc CLI does NOT read `JDC_ACCESS_KEY` / `JDC_SECRET_KEY` environment variables**
The CLI's `ProfileManager` class reads credentials exclusively from `~/.jdc/config` (INI format). Setting environment variables alone is insufficient. The config file must be pre-created with the following structure:
```ini
[default]
access_key = YOUR_ACCESS_KEY
secret_key = YOUR_SECRET_KEY
region_id = cn-north-1
endpoint = nc.jdcloud-api.com
scheme = https
timeout = 20
```

Plus a `~/.jdc/current` file containing just `default` (no newline at end).

**Failure 4: `PermissionError` on `~/.jdc/` directory creation**
The CLI's `ProfileManager.__init__()` calls `__make_config_dir()` which does `os.makedirs(os.path.expanduser("~") + "/.jdc")`. In sandboxed environments (trae-sandbox, containers) where home is not writable, this crashes with `PermissionError`. The fix is:
1. Set `HOME` to a writable path: `export HOME=/tmp/jdc-home`
2. Pre-create `~/.jdc/config` and `~/.jdc/current` files before running `jdc`

### Dependency Notice

This skill integrates with `jdcloud-aiops-cruise` for workload analysis before destructive operations. The `k8s_analyzer.py` module provides:
- `check_workloads(cluster_id)` — returns running deployments, services, and pods for a cluster
- `check_namespaces(cluster_id)` — returns active namespaces
- `analyze_delete_impact(cluster_id)` — analyzes blast radius of cluster deletion

**Pre-delete safety gate:** Before deleting any cluster, the Agent MUST invoke `k8s_analyzer.py` (if available) or use `jdc describe-cluster` / `kubectl get all` (via SSH to master or Cloud Shell) to verify the cluster has zero running workloads. If workloads exist, MUST warn the user and obtain explicit confirmation.

## Trigger & Scope (Agent-Readable)

### SHOULD Use This Skill When

- User explicitly mentions "JD Cloud Kubernetes", "JCS for Kubernetes", "容器服务", "K8s集群", "Kubernetes cluster", "JCSKubernetes"
- User wants to **deploy**, **configure**, **troubleshoot**, or **monitor** Kubernetes clusters via automation
- Task involves CRUD operations: create, describe, modify, delete, or list Kubernetes clusters
- Task involves node group management: create, scale, describe, or delete node groups
- Task involves cluster credentials: obtain kubeconfig for kubectl access
- Task involves cluster upgrades: upgrade cluster control plane or node groups
- Task involves workload analysis for cluster deletion safety
- Task involves storage management: PV, PVC, StorageClass operations, storage health checks
- Keywords detected: createCluster, describeClusters, deleteCluster, createNodeGroup, describeNodeGroups, modifyNodeGroup, describeClusterCredential, kubeconfig, nodeGroup, PersistentVolume, PersistentVolumeClaim, PVC, PV, StorageClass, storage
- User describes container orchestration needs without naming "Kubernetes" (e.g., "manage my container cluster", "deploy a K8s cluster", "scale worker nodes", "get kubectl config")

### SHOULD NOT Use This Skill When

- Task is purely billing / account management → delegate to: `jdcloud-billing-ops` (when present)
- Task is IAM / permission model only → delegate to: `jdcloud-iam-ops` (when present)
- Task is about VPC / subnet / security group configuration → delegate to: `jdcloud-vpc-ops`
- Task is about VM / ECS instance management → delegate to: `jdcloud-vm-ops`
- Task is about container registry (JD Cloud Container Registry) → delegate to: `jdcloud-cr-ops` (when present)
- Task is about monitoring metrics / alarms → delegate to: `jdcloud-cloudmonitor-ops`
- Task is about load balancer configuration for K8s services → delegate to: `jdcloud-clb-ops`
- User insists on **console-only** flows with no API → state limitation; do not invent undocumented HTTP steps
- Task involves deploying applications inside Kubernetes (helm, kubectl apply) — not covered by this skill; recommend using kubectl directly

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
- **Timestamps:** ISO 8601 with timezone when the API returns strings (e.g. `2026-06-08T10:00:00+08:00`).
- **Idempotency:** Cluster names are unique per region; duplicate name returns `ResourceAlreadyExists`.

### Example Response Field Table

| Operation | JSON Path (API) | Type | Description |
|-----------|----------------|------|-------------|
| Create Cluster | `$.result.clusterId` | string | New cluster ID |
| Describe Cluster | `$.result.cluster.state` | string | Cluster state (running, creating, deleting, error) |
| List Clusters | `$.result.clusters[*].clusterId` | array | All cluster IDs |
| Create Node Group | `$.result.nodeGroupId` | string | New node group ID |
| Describe Node Group | `$.result.nodeGroup.state` | string | Node group state |
| Modify Node Group | `$.result.nodeGroupId` | string | Modified node group ID |
| Delete Cluster | `$.requestId` or `$.error` | string / object | Per spec |
| Describe Credentials | `$.result.kubeconfig` | string | Base64-encoded kubeconfig |

### Expected State Transitions

| Operation | Initial State | Target State | Poll Interval | Max Wait |
|-----------|---------------|--------------|---------------|----------|
| Create Cluster | — | `running` | 30s | 600s |
| Create Node Group | — | `running` | 15s | 300s |
| Scale Node Group | `running` | `running` | 15s | 300s |
| Upgrade Cluster | `running` | `running` | 30s | 600s |
| Delete Cluster | any stable state | (404 on describe) | 30s | 600s |
| Delete Node Group | any stable state | (404 on describe) | 15s | 300s |

## Runbooks (巡检 Runbook)

This skill includes structured inspection runbooks for proactive Kubernetes cluster health monitoring and resource optimization:

- [Runbook Index](runbooks/00-index.md) — overview of all runbooks
- [01 - 集群健康巡检](runbooks/01-cluster-health-check.md) — cluster status, node health, pod distribution, ingress health, security posture
- [02 - 资源配置优化](runbooks/02-resource-optimization.md) — CPU/Mem requests alignment, HPA reasonability, resource waste detection, node water-level analysis

All runbooks follow the **Perceive → Reason → Execute** three-phase model. The Execute phase is **read-only** — it generates recommendations but delegates actual changes to the Execution Flows in this SKILL.md.

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.4.0 | 2026-06-19 | **Storage operations added**: 新增 `scripts/snippets/storage_ops.py`，使用 K8s Python client 管理 PV/PVC/StorageClass。支持 list_storage_classes、create_pvc、list_pvcs、delete_pvc、list_pvs、check_pvc_health、get_storage_summary。添加 `kubernetes>=25.3.0` 依赖。 |
| 1.3.0 | 2026-06-19 | **CLI 策略变更**: 从 `jdc-first-with-fallback` 改为 `sdk-or-api-only`。原因：`jdc kubernetes` 命令运行时崩溃（`jdcloudHeaders` bug），`jdc nc` 是 Native Container（容器实例）而非 Kubernetes 集群管理。所有 CLI 示例标记为期望语法，实际执行必须使用 SDK/API。 |
| 1.2.0 | 2026-06-18 | **GCL v2 rollout**: Upgraded to GCL v2 with Phase 6 (Hallucination Detection Layer H — recommended, MANDATORY for CLI parameter existence) and Phase 7 (Lightweight Reflexion Integration — enabled, loads `docs/failure-patterns.md`). Changed GCL classification from `required` to `recommended` with `max_iterations=3`. Added `HALLUCINATION_ABORT` termination condition. Added operation-specific H layer behavior for delete-cluster, delete-node-group, create operations. Rubric version bumped to v2. |
| 1.1.0 | 2026-06-10 | **Runbooks added**: Added `runbooks/` directory with 2 runbooks (01-cluster-health-check, 02-resource-optimization) covering proactive K8s cluster health monitoring and resource optimization. Runbook index at `runbooks/00-index.md`. |
| 1.0.0 | 2026-06-08 | Initial version with jdc-first execution and SDK fallback for Kubernetes operations. GCL rollout with rubric (required, max_iter=2). Cluster delete safety gate with workload dependency check via jdcloud-aiops-cruise. |

## Execution Flows (Agent-Readable)

Every operation: **Pre-flight → Execute (SDK/API primary) → Validate → Recover**. Do not skip phases.

**执行策略说明:** 当前锁定版本 CLI (`jdcloud_cli==1.2.12`) 中 `jdc kubernetes` 命令运行时崩溃，`jdc nc` 是 Native Container（容器实例）而非 Kubernetes 集群管理。以下 CLI 示例均为**期望语法**，Agent SHOULD NOT 直接执行未验证的命令。

> 安全执行路径：通过 SDK (`jdcloud_sdk`) 或原始 REST API (`https://nc.jdcloud-api.com/v1/...`) 执行。详见 [API & SDK Usage](references/api-sdk-usage.md)。

### Operation: Create Cluster

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| SDK / deps | `import jdcloud_sdk.services.nc.client.NcClient` | No import error | Install pin: `uv pip install jdcloud_sdk>=1.6.26` |
| Credentials | Construct credential from env | Non-empty keys | HALT; user configures env |
| Region | Call `describeClusters` with small page | `{{user.region}}` supported | Suggest valid region |
| VPC/Subnet | Verify via `jdcloud-vpc-ops` | Subnet exists and has IP | HALT; create subnet first |
| Kubernetes version | Validate version string | Supported version | List available versions |
| Quota | Check cluster count vs limit | Not exceeded | HALT; request quota increase |

#### Execution (SDK — Primary Path)

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.nc.client.NcClient import NcClient
from jdcloud_sdk.services.nc.apis.CreateClusterRequest import CreateClusterRequest, CreateClusterParameters

credential = Credential(os.environ["JDC_ACCESS_KEY"], os.environ["JDC_SECRET_KEY"])
client = NcClient(credential)

# Build cluster spec
cluster_spec = {
    "clusterName": "{{user.cluster_name}}",
    "vpcId": "{{user.vpc_id}}",
    "subnetId": "{{user.subnet_id}}",
    "masterVersion": "{{user.master_version}}",
    "nodeGroup": {
        "name": "{{user.node_group_name}}",
        "instanceType": "{{user.instance_type}}",
        "nodeCount": {{user.node_count}}
    }
}

params = CreateClusterParameters(regionId="{{user.region}}", clusterSpec=cluster_spec)
req = CreateClusterRequest(parameters=params)
resp = client.send(req)
cluster_id = resp.result["clusterId"]
```

#### Execution — CLI (`jdc`) [期望语法 — 当前锁定版本不可用]

> **⚠️ 注意**: `jdc kubernetes` 命令在当前锁定版本 (1.2.12) 中运行时崩溃，以下为期望语法示例，实际执行前请确认 CLI 版本支持。

```bash
# NOTE: jdc kubernetes 命令在当前锁定版本 (1.2.12) 中不可用，以下为期望语法示例
jdc --output json kubernetes create-cluster \
  --region-id "{{user.region}}" \
  --cluster-name "{{user.cluster_name}}" \
  --vpc-id "{{user.vpc_id}}" \
  --subnet-id "{{user.subnet_id}}" \
  --master-version "{{user.master_version}}" \
  --node-group-name "{{user.node_group_name}}" \
  --instance-type "{{user.instance_type}}" \
  --node-count {{user.node_count}}
```

#### Post-execution Validation

1. Capture `{{output.cluster_id}}` from `$.result.clusterId`.
2. Poll `describeCluster` until `state` == `running` or timeout.

```python
# SDK poll loop (primary path)
from jdcloud_sdk.services.nc.apis.DescribeClusterRequest import DescribeClusterRequest, DescribeClusterParameters

for _ in range(20):
    dparams = DescribeClusterParameters(regionId="{{user.region}}", clusterId="{{output.cluster_id}}")
    dreq = DescribeClusterRequest(parameters=dparams)
    dresp = client.send(dreq)
    state = dresp.result["cluster"]["state"]
    if state == "running":
        break
    if state in ["error", "deleted"]:
        raise RuntimeError(f"Cluster creation failed: {state}")
    sleep(30)
```

3. On success, report cluster ID, endpoint, and state to user.
4. On terminal failure, go to **Failure Recovery**.

#### Failure Recovery

| Error pattern | Max retries | Backoff | Agent Action |
|---------------|-------------|---------|--------------|
| `InvalidParameter` / 400 | 0–1 | — | Fix args per OpenAPI; retry once |
| `QuotaExceeded` | 0 | — | HALT; user requests quota increase |
| `InsufficientBalance` | 0 | — | HALT; user tops up account |
| `ResourceAlreadyExists` | 0 | — | Ask reuse vs new name |
| `SubnetIpInsufficient` | 0 | — | HALT; user expands subnet |
| `InvalidVersion` | 0 | — | Suggest valid Kubernetes version |
| Throttling / 429 | 3 | exponential | Back off; respect Retry-After |
| `InternalError` / 5xx | 3 | 2s, 4s, 8s | Retry; HALT with requestId if persists |

### Operation: Describe Cluster

#### Execution (CLI) [Primary Path]

```bash
jdc --output json nc describe-cluster \
  --region-id "{{user.region}}" \
  --cluster-id "{{user.cluster_id}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.nc.apis.DescribeClusterRequest import DescribeClusterRequest, DescribeClusterParameters

params = DescribeClusterParameters(regionId="{{user.region}}", clusterId="{{user.cluster_id}}")
req = DescribeClusterRequest(parameters=params)
resp = client.send(req)
# Access: resp.result["cluster"]
```

#### Present to User

| Field | JSON Path | Notes |
|-------|-----------|-------|
| Cluster ID | `$.result.cluster.clusterId` | Plain text |
| Name | `$.result.cluster.clusterName` | Plain text |
| State | `$.result.cluster.state` | running, creating, deleting, error |
| Version | `$.result.cluster.masterVersion` | Kubernetes version |
| Endpoint | `$.result.cluster.endpoint` | API server endpoint |
| VPC ID | `$.result.cluster.vpcId` | Associated VPC |
| Subnet ID | `$.result.cluster.subnetId` | Associated subnet |
| Node Groups | `$.result.cluster.nodeGroups[*].nodeGroupId` | Array of node group IDs |
| Created Time | `$.result.cluster.createdTime` | ISO 8601 format |

### Operation: List Clusters

#### Execution (CLI) [Primary Path]

```bash
jdc --output json nc describe-clusters \
  --region-id "{{user.region}}" \
  --page-number 1 \
  --page-size 100
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.nc.apis.DescribeClustersRequest import DescribeClustersRequest, DescribeClustersParameters

params = DescribeClustersParameters(regionId="{{user.region}}")
params.setPageNumber(1)
params.setPageSize(100)
req = DescribeClustersRequest(parameters=params)
resp = client.send(req)
clusters = resp.result["clusters"]
```

### Operation: Delete Cluster

#### Pre-flight (Safety Gate)

- **MUST** check if cluster has running workloads using `jdcloud-aiops-cruise k8s_analyzer.py`:
  ```python
  try:
      from jdcloud_aiops_cruise.kubernetes import k8s_analyzer
      workloads = k8s_analyzer.check_workloads("{{user.cluster_id}}")
  except ImportError:
      workloads = {}
  ```
- **MUST** obtain explicit confirmation: irreversible delete of cluster `{{user.cluster_name}}` (`{{user.cluster_id}}`).
- **MUST** warn user about workloads, persistent volumes, and LoadBalancer services that will be lost.
- **MUST NOT** proceed without clear user assent.

#### Execution (SDK — Primary Path)

```python
from jdcloud_sdk.services.nc.apis.DeleteClusterRequest import DeleteClusterRequest, DeleteClusterParameters

params = DeleteClusterParameters(
    regionId="{{user.region}}",
    clusterId="{{user.cluster_id}}"
)
req = DeleteClusterRequest(parameters=params)
resp = client.send(req)
```

#### Execution — CLI (`jdc`) [期望语法 — 当前锁定版本不可用]

> **⚠️ 注意**: `jdc kubernetes` 命令在当前锁定版本 (1.2.12) 中运行时崩溃，以下为期望语法示例，实际执行前请确认 CLI 版本支持。

```bash
# NOTE: jdc kubernetes 命令在当前锁定版本 (1.2.12) 中不可用，以下为期望语法示例
jdc --output json kubernetes delete-cluster \
  --region-id "{{user.region}}" \
  --cluster-id "{{user.cluster_id}}"
```

#### Post-execution Validation

Poll describe until 404 or max wait (600s).

```python
# SDK poll loop
from jdcloud_sdk.services.nc.apis.DescribeClusterRequest import DescribeClusterRequest, DescribeClusterParameters

for _ in range(20):
    try:
        dparams = DescribeClusterParameters(regionId="{{user.region}}", clusterId="{{user.cluster_id}}")
        dreq = DescribeClusterRequest(parameters=dparams)
        dresp = client.send(dreq)
        sleep(30)
    except Exception as e:
        if "NotFound" in str(e) or "404" in str(e):
            break
        raise
```

### Operation: Create Node Group

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| Cluster exists | `describeCluster` | Cluster found | HALT; verify cluster ID |
| Cluster state | `describeCluster` | `running` | Wait or suggest appropriate action |
| Instance type | User input | Valid instance type | List available types |
| Node count | User input | ≥ 1, ≤ quota | Validate range |

#### Execution (SDK — Primary Path)

```python
from jdcloud_sdk.services.nc.apis.CreateNodeGroupRequest import CreateNodeGroupRequest, CreateNodeGroupParameters

ng_spec = {
    "name": "{{user.node_group_name}}",
    "instanceType": "{{user.instance_type}}",
    "nodeCount": {{user.node_count}},
    "subnetId": "{{user.subnet_id}}"
}

params = CreateNodeGroupParameters(
    regionId="{{user.region}}",
    clusterId="{{user.cluster_id}}",
    nodeGroupSpec=ng_spec
)
req = CreateNodeGroupRequest(parameters=params)
resp = client.send(req)
node_group_id = resp.result["nodeGroupId"]
```

#### Execution — CLI (`jdc`) [期望语法 — 当前锁定版本不可用]

> **⚠️ 注意**: `jdc kubernetes` 命令在当前锁定版本 (1.2.12) 中运行时崩溃，以下为期望语法示例，实际执行前请确认 CLI 版本支持。

```bash
# NOTE: jdc kubernetes 命令在当前锁定版本 (1.2.12) 中不可用，以下为期望语法示例
jdc --output json kubernetes create-node-group \
  --region-id "{{user.region}}" \
  --cluster-id "{{user.cluster_id}}" \
  --name "{{user.node_group_name}}" \
  --instance-type "{{user.instance_type}}" \
  --node-count {{user.node_count}} \
  --subnet-id "{{user.subnet_id}}"
```

#### Post-execution Validation

1. Capture `{{output.node_group_id}}` from `$.result.nodeGroupId`.
2. Poll `describeNodeGroup` until `state` == `running` or timeout.

```python
# SDK poll loop
from jdcloud_sdk.services.nc.apis.DescribeNodeGroupRequest import DescribeNodeGroupRequest, DescribeNodeGroupParameters

for _ in range(20):
    ng_params = DescribeNodeGroupParameters(
        regionId="{{user.region}}",
        clusterId="{{user.cluster_id}}",
        nodeGroupId="{{output.node_group_id}}"
    )
    ng_req = DescribeNodeGroupRequest(parameters=ng_params)
    ng_resp = client.send(ng_req)
    state = ng_resp.result["nodeGroup"]["state"]
    if state == "running":
        break
    sleep(15)
```

### Operation: Describe Node Group

#### Execution (SDK — Primary Path)

```python
from jdcloud_sdk.services.nc.apis.DescribeNodeGroupRequest import DescribeNodeGroupRequest, DescribeNodeGroupParameters

params = DescribeNodeGroupParameters(
    regionId="{{user.region}}",
    clusterId="{{user.cluster_id}}",
    nodeGroupId="{{user.node_group_id}}"
)
req = DescribeNodeGroupRequest(parameters=params)
resp = client.send(req)
# Access: resp.result["nodeGroup"]
```

#### Execution — CLI (`jdc`) [期望语法 — 当前锁定版本不可用]

> **⚠️ 注意**: `jdc kubernetes` 命令在当前锁定版本 (1.2.12) 中运行时崩溃，以下为期望语法示例，实际执行前请确认 CLI 版本支持。

```bash
# NOTE: jdc kubernetes 命令在当前锁定版本 (1.2.12) 中不可用，以下为期望语法示例
jdc --output json kubernetes describe-node-group \
  --region-id "{{user.region}}" \
  --cluster-id "{{user.cluster_id}}" \
  --node-group-id "{{user.node_group_id}}"
```

#### Present to User

| Field | JSON Path | Notes |
|-------|-----------|-------|
| Node Group ID | `$.result.nodeGroup.nodeGroupId` | Plain text |
| Name | `$.result.nodeGroup.name` | Plain text |
| State | `$.result.nodeGroup.state` | running, creating, deleting, error |
| Instance Type | `$.result.nodeGroup.instanceType` | VM spec |
| Node Count | `$.result.nodeGroup.nodeCount` | Current number of nodes |
| Min/Max Count | `$.result.nodeGroup.minCount` / `maxCount` | For auto-scaling |
| Subnet ID | `$.result.nodeGroup.subnetId` | Associated subnet |
| Created Time | `$.result.nodeGroup.createdTime` | ISO 8601 format |

### Operation: Delete Node Group

#### Pre-flight (Safety Gate)

- **MUST** obtain explicit confirmation: this will terminate all VM instances in `{{user.node_group_name}}` (`{{user.node_group_id}}`).
- **MUST** inform user about pod evictions and data on non-persistent volumes.
- **MUST NOT** proceed without clear user assent.

#### Execution (SDK — Primary Path)

```python
from jdcloud_sdk.services.nc.apis.DeleteNodeGroupRequest import DeleteNodeGroupRequest, DeleteNodeGroupParameters

params = DeleteNodeGroupParameters(
    regionId="{{user.region}}",
    clusterId="{{user.cluster_id}}",
    nodeGroupId="{{user.node_group_id}}"
)
req = DeleteNodeGroupRequest(parameters=params)
resp = client.send(req)
```

#### Execution — CLI (`jdc`) [期望语法 — 当前锁定版本不可用]

> **⚠️ 注意**: `jdc kubernetes` 命令在当前锁定版本 (1.2.12) 中运行时崩溃，以下为期望语法示例，实际执行前请确认 CLI 版本支持。

```bash
# NOTE: jdc kubernetes 命令在当前锁定版本 (1.2.12) 中不可用，以下为期望语法示例
jdc --output json kubernetes delete-node-group \
  --region-id "{{user.region}}" \
  --cluster-id "{{user.cluster_id}}" \
  --node-group-id "{{user.node_group_id}}"
```

#### Post-execution Validation

Poll describe until 404 or max wait (300s).

### Operation: Scale Node Group

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| Node group exists | `describeNodeGroup` | Found | HALT; verify IDs |
| Node group state | `describeNodeGroup` | `running` | Wait for ready state |
| Target count | User input | ≥ 1, ≤ quota | Validate range |
| Subnet capacity | Verify available IPs | Sufficient IPs | HALT; expand subnet |

#### Execution (SDK — Primary Path)

```python
from jdcloud_sdk.services.nc.apis.ModifyNodeGroupRequest import ModifyNodeGroupRequest, ModifyNodeGroupParameters

params = ModifyNodeGroupParameters(
    regionId="{{user.region}}",
    clusterId="{{user.cluster_id}}",
    nodeGroupId="{{user.node_group_id}}"
)
params.setNodeCount({{user.node_count}})
req = ModifyNodeGroupRequest(parameters=params)
resp = client.send(req)
```

#### Execution — CLI (`jdc`) [期望语法 — 当前锁定版本不可用]

> **⚠️ 注意**: `jdc kubernetes` 命令在当前锁定版本 (1.2.12) 中运行时崩溃，以下为期望语法示例，实际执行前请确认 CLI 版本支持。

```bash
# NOTE: jdc kubernetes 命令在当前锁定版本 (1.2.12) 中不可用，以下为期望语法示例
jdc --output json kubernetes modify-node-group \
  --region-id "{{user.region}}" \
  --cluster-id "{{user.cluster_id}}" \
  --node-group-id "{{user.node_group_id}}" \
  --node-count {{user.node_count}}
```

#### Post-execution Validation

Poll `describeNodeGroup` until `nodeCount` matches target and `state` is `running`.

### Operation: Describe Cluster Credentials

#### Execution (SDK — Primary Path)

```python
from jdcloud_sdk.services.nc.apis.DescribeClusterCredentialRequest import DescribeClusterCredentialRequest, DescribeClusterCredentialParameters

params = DescribeClusterCredentialParameters(
    regionId="{{user.region}}",
    clusterId="{{user.cluster_id}}"
)
req = DescribeClusterCredentialRequest(parameters=params)
resp = client.send(req)
kubeconfig = resp.result["kubeconfig"]  # Base64-encoded kubeconfig
```

#### Execution — CLI (`jdc`) [期望语法 — 当前锁定版本不可用]

> **⚠️ 注意**: `jdc kubernetes` 命令在当前锁定版本 (1.2.12) 中运行时崩溃，以下为期望语法示例，实际执行前请确认 CLI 版本支持。

```bash
# NOTE: jdc kubernetes 命令在当前锁定版本 (1.2.12) 中不可用，以下为期望语法示例
jdc --output json kubernetes describe-cluster-credential \
  --region-id "{{user.region}}" \
  --cluster-id "{{user.cluster_id}}"
```

#### Present to User

| Field | JSON Path | Notes |
|-------|-----------|-------|
| Kubeconfig | `$.result.kubeconfig` | Base64-encoded string; decode before use |
| Kubeconfig (decoded) | base64 decode of `$.result.kubeconfig` | Raw YAML kubeconfig |

**⚠️ Security:** The kubeconfig grants admin-level access to the cluster. **NEVER** log, print, or expose the raw kubeconfig content. Only confirm it was retrieved and provide instructions to the user on how to save it securely.

### Operation: Upgrade Cluster

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| Cluster exists | `describeCluster` | Found | HALT; verify cluster ID |
| Cluster state | `describeCluster` | `running` | Wait or suggest appropriate action |
| Target version | Validate against available versions | Supported upgrade path | List available upgrade targets |
| Workload health | `jdcloud-aiops-cruise k8s_analyzer` | Running workloads healthy | Warn user about upgrade impact |

#### Execution (SDK — Primary Path)

```python
from jdcloud_sdk.services.nc.apis.ModifyClusterRequest import ModifyClusterRequest, ModifyClusterParameters

params = ModifyClusterParameters(
    regionId="{{user.region}}",
    clusterId="{{user.cluster_id}}",
    masterVersion="{{user.target_version}}"
)
req = ModifyClusterRequest(parameters=params)
resp = client.send(req)
```

#### Execution — CLI (`jdc`) [期望语法 — 当前锁定版本不可用]

> **⚠️ 注意**: `jdc kubernetes` 命令在当前锁定版本 (1.2.12) 中运行时崩溃，以下为期望语法示例，实际执行前请确认 CLI 版本支持。

```bash
# NOTE: jdc kubernetes 命令在当前锁定版本 (1.2.12) 中不可用，以下为期望语法示例
jdc --output json kubernetes modify-cluster \
  --region-id "{{user.region}}" \
  --cluster-id "{{user.cluster_id}}" \
  --master-version "{{user.target_version}}"
```

#### Post-execution Validation

Poll `describeCluster` until `masterVersion` matches target and `state` is `running`.

### Operation: Describe Node Groups (List for a Cluster)

#### Execution (SDK — Primary Path)

```python
from jdcloud_sdk.services.nc.apis.DescribeNodeGroupsRequest import DescribeNodeGroupsRequest, DescribeNodeGroupsParameters

params = DescribeNodeGroupsParameters(
    regionId="{{user.region}}",
    clusterId="{{user.cluster_id}}"
)
req = DescribeNodeGroupsRequest(parameters=params)
resp = client.send(req)
node_groups = resp.result["nodeGroups"]
```

#### Execution — CLI (`jdc`) [期望语法 — 当前锁定版本不可用]

> **⚠️ 注意**: `jdc kubernetes` 命令在当前锁定版本 (1.2.12) 中运行时崩溃，以下为期望语法示例，实际执行前请确认 CLI 版本支持。

```bash
# NOTE: jdc kubernetes 命令在当前锁定版本 (1.2.12) 中不可用，以下为期望语法示例
jdc --output json kubernetes describe-node-groups \
  --region-id "{{user.region}}" \
  --cluster-id "{{user.cluster_id}}"
```

### Operation: Storage Management (PV/PVC/StorageClass)

> **Note**: Storage operations use the Kubernetes Python client (`kubernetes` package), not `jdcloud_sdk`. These operations manage K8s-native storage resources (PersistentVolume, PersistentVolumeClaim, StorageClass) within a cluster.

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| K8s client deps | `import kubernetes` | No import error | Install: `uv pip install kubernetes>=25.3.0` |
| Kubeconfig | `credential_ops.get_kubeconfig_decoded()` | Valid kubeconfig | Obtain via `describeClusterCredential` |
| Cluster access | `list_storage_classes()` | Returns storage classes | Verify kubeconfig and cluster connectivity |

#### Execution (K8s Python client — Primary Path)

**List StorageClasses:**

```python
from snippets.storage_ops import list_storage_classes

result = list_storage_classes(kubeconfig_path="{{user.kubeconfig_path}}")
storage_classes = result["storage_classes"]
default_class = result["default_class"]
```

**Create PVC:**

```python
from snippets.storage_ops import create_pvc

result = create_pvc(
    name="{{user.pvc_name}}",
    namespace="{{user.namespace}}",
    storage_class="{{user.storage_class}}",
    size="{{user.size}}",
    access_mode="{{user.access_mode}}",
    kubeconfig_path="{{user.kubeconfig_path}}"
)
pvc_name = result["name"]
```

**List PVCs:**

```python
from snippets.storage_ops import list_pvcs

result = list_pvcs(
    namespace="{{user.namespace}}",
    kubeconfig_path="{{user.kubeconfig_path}}"
)
pvcs = result["pvcs"]
```

**Delete PVC:**

> **⚠️ Safety Gate**: PVC deletion is IRREVERSIBLE. Data on the underlying PV may be lost depending on reclaim policy. MUST confirm with user before calling.

```python
from snippets.storage_ops import delete_pvc

# SAFETY: Caller MUST confirm with user before calling
result = delete_pvc(
    name="{{user.pvc_name}}",
    namespace="{{user.namespace}}",
    kubeconfig_path="{{user.kubeconfig_path}}"
)
```

**Check PVC Health:**

```python
from snippets.storage_ops import check_pvc_health

result = check_pvc_health(
    name="{{user.pvc_name}}",
    namespace="{{user.namespace}}",
    kubeconfig_path="{{user.kubeconfig_path}}"
)
healthy = result["healthy"]
issues = result["issues"]
```

**Get Storage Summary:**

```python
from snippets.storage_ops import get_storage_summary

result = get_storage_summary(
    namespace="{{user.namespace}}",
    kubeconfig_path="{{user.kubeconfig_path}}"
)
storage_classes_count = result["storage_classes"]
pvs_status = result["pvs"]
pvcs_status = result["pvcs"]
```

#### Post-execution Validation

- **Create PVC**: Verify PVC status transitions from `Pending` to `Bound`
- **Delete PVC**: Verify PVC no longer exists via `list_pvcs()`
- **Health Check**: Verify `healthy == true` and no issues in `issues` array

## Quality Gate (GCL)

> This skill participates in the repository-wide **Generator-Critic-Loop**
> (GCL) defined in [`AGENTS.md` §Quality Gate](../AGENTS.md#generator-critic-loop-gcl--adversarial-quality-gate).
> The quality gate is **recommended** for this skill (per `AGENTS.md` §8).

### Parameters (override `AGENTS.md` §8 defaults)

| Parameter | Value | Reason |
|---|---|---|
| `max_iterations` | **3** | `AGENTS.md` §8 default for `jdcloud-kubernetes-ops` (recommended) |
| `rubric_version` | `v2` | see [rubric.md](references/rubric.md) |
| `trace_path` | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | unified with `jdcloud-audit-ops` |
| `safety_confirm_required` | **true** for `delete-cluster`, `delete-node-group` | matches repository safety gate policy |
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
    - prepare k8s_analyzer if needed
   │
   ▼
[1] Generate (G)
    - generate command/payload (DO NOT execute yet)
    - run k8s_analyzer pre-check if delete-cluster
   │
   ▼
[1.5] Hallucination Detection (H) ──► pre-execution structural validity check
   │   (recommended for k8s-ops)      - CLI parameter existence
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
> **before** they reach the JD Cloud Kubernetes API.

**Two-Category Check (for k8s-ops):**

| Category | Check | Method |
|---|---|---|
| **CLI Parameter Existence** | Verify every `--flag` exists in `jdc nc <operation> --help` | Compare against `references/api-sdk-usage.md` operation tables |
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
# 2. Filter patterns by current skill name (jdcloud-kubernetes-ops)
# 3. Inject top-3 relevant patterns into Generator context as prevention hints

# Example injection:
"Known failure patterns for this skill:
- InvalidClusterId: Cluster ID must be in format 'c-xxxxxxxx'
- NodeGroup cascade delete: Must drain nodes before delete-node-group
- Kubeconfig expiry: Regenerate kubeconfig if > 24h old"
```

**This is a HINT, not a CONSTRAINT** — the Generator should use these patterns to avoid known mistakes.

**Failure Pattern Extraction:**

When a GCL iteration fails, the Orchestrator SHOULD extract a structured failure pattern:

```json
{
  "failure_pattern": {
    "category": "cli_parameter" | "skill_generation" | "cross_skill" | "runtime",
    "skill": "jdcloud-kubernetes-ops",
    "command": "jdc nc describe-cluster --clusterId c-xxx",
    "error": "InvalidParameter: InvalidClusterId",
    "fix": "Validated cluster ID format before execution",
    "reusable": true
  }
}
```

### Artifacts

- Rubric (concrete scoring rules): [references/rubric.md](references/rubric.md)
- Prompt templates (G / C / O / H): [references/prompt-templates.md](references/prompt-templates.md)
- Failure patterns (cross-session memory): [docs/failure-patterns.md](../docs/failure-patterns.md)

### Operation-specific behavior

- **`delete-cluster`** — Destructive. MUST invoke `k8s_analyzer` pre-check to identify workload dependencies. Safety=1 required. H layer validates clusterId format.
- **`delete-node-group`** — Destructive. MUST drain nodes before deletion. Safety=1 required.
- **`create-cluster`** / **`create-node-group`** — Non-destructive but requires CIDR validation and resource quota check.
- **`describe-*`** — Read-only. No safety gate required.

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
- [Example Config](assets/example-config.yaml)

## Prerequisites

> **Python 3.10 is REQUIRED, NOT 3.12.** `jdcloud_cli==1.2.12` uses `SafeConfigParser` which was removed in Python 3.12. Always use `uv venv --python 3.10`. If Python 3.10 is unavailable, install it via `brew install python@3.10` (macOS) or `uv python install 3.10`.

Environment setup follows a **SDK/API 优先（当前 CLI 不可用）** strategy. Complete setup guide is in [CLI Usage](references/cli-usage.md) and [API & SDK Usage](references/api-sdk-usage.md).

### Quick Setup Summary

1. **Attempt SDK/API setup** via `uv` (current executable path)
2. **`jdc` CLI** — only after confirming the CLI version fixes the `jdcloudHeaders` bug
3. If CLI is not working, use **SDK/API** directly

### Python Runtime (uv)

Both `jdc` CLI and the JD Cloud Python SDK require a Python runtime. Use **`uv`** for local, isolated, and **idempotent** environment management.

**Install uv (system-wide, one-time per machine):**
```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
# Or via Homebrew: brew install uv

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Configure Credentials

**CRITICAL**: The `jdc` CLI reads credentials exclusively from `~/.jdc/config` (INI format). The SDK reads from environment variables. Complete credential setup guide is in [CLI Usage](references/cli-usage.md).

**SDK (env vars) — Primary Path:**
```bash
export JDC_ACCESS_KEY="{{env.JDC_ACCESS_KEY}}"
export JDC_SECRET_KEY="{{env.JDC_SECRET_KEY}}"
export JDC_REGION="cn-north-1"
```

**CLI (`~/.jdc/config` INI) — Expected Syntax Only:**
```bash
# NOTE: jdc kubernetes 命令在当前锁定版本 (1.2.12) 中不可用
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc
cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = {{env.JDC_ACCESS_KEY}}
secret_key = {{env.JDC_SECRET_KEY}}
region_id = {{env.JDC_REGION}}
endpoint = nc.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF
printf "%s" "default" > /tmp/jdc-home/.jdc/current
```

### Verify Configuration

```python
# SDK verification (primary path)
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.nc.client.NcClient import NcClient
from jdcloud_sdk.services.nc.apis.DescribeClustersRequest import DescribeClustersRequest, DescribeClustersParameters

credential = Credential(os.environ["JDC_ACCESS_KEY"], os.environ["JDC_SECRET_KEY"])
client = NcClient(credential)
params = DescribeClustersParameters(regionId="cn-north-1")
params.setPageNumber(1)
params.setPageSize(1)
req = DescribeClustersRequest(parameters=params)
resp = client.send(req)
print(f"SDK connection OK, clusters: {len(resp.result.get('clusters', []))}")
```

> **Security:** Never commit `.env` to version control (already in `.gitignore`). All credentials use `{{env.*}}` placeholders — never real values.

## Operational Best Practices

- **Least privilege:** IAM policies scoped to required APIs only (cluster CRUD, node group operations, credential retrieval).
- **Availability:** Deploy multi-AZ clusters with node groups in at least two availability zones.
- **Cost:** Right-size node instance types; use auto-scaling for node groups to optimize spend.
- **Backup:** Regularly backup etcd and persistent volumes (PV). Cluster deletion is irreversible.
- **Security:** Rotate cluster credentials regularly. Store kubeconfig securely. Use IAM roles for cross-account access.
- **Upgrades:** Always upgrade one minor version at a time. Test workload compatibility in a staging cluster first.