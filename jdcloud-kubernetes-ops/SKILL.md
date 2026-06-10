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
  access to JD Cloud endpoints, and official JD Cloud CLI (`jdc`) when this
  product is supported by the CLI (jdc-first with SDK fallback).
metadata:
  author: buhaiqing
  version: "1.1.0"
  last_updated: "2026-06-10"
  runtime: Harness AI Agent
  api_profile: "JD Cloud JCS for Kubernetes API - https://nc.jdcloud-api.com/v1"
  cli_applicability: jdc-first-with-fallback
  cli_version_locked: "1.2.12"
  sdk_version_locked: ">=1.6.26"
  cli_support_evidence: >-
    Confirmed via `jdc` help output showing 'nc' (Native Container) in product
    list which includes Kubernetes cluster operations.
    Official CLI documentation: https://docs.jdcloud.com/cn/cli/introduction
  environment:
    - JDC_ACCESS_KEY
    - JDC_SECRET_KEY
    - JDC_REGION
  dependencies:
    - jdcloud-aiops-cruise (k8s_analyzer.py for workload analysis)
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
- Keywords detected: createCluster, describeClusters, deleteCluster, createNodeGroup, describeNodeGroups, modifyNodeGroup, describeClusterCredential, kubeconfig, nodeGroup
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
| 1.1.0 | 2026-06-10 | **Runbooks added**: Added `runbooks/` directory with 2 runbooks (01-cluster-health-check, 02-resource-optimization) covering proactive K8s cluster health monitoring and resource optimization. Runbook index at `runbooks/00-index.md`. |
| 1.0.0 | 2026-06-08 | Initial version with jdc-first execution and SDK fallback for Kubernetes operations. GCL rollout with rubric (required, max_iter=2). Cluster delete safety gate with workload dependency check via jdcloud-aiops-cruise. |

## Execution Flows (Agent-Readable)

All operations follow this standardized workflow:  
**Pre-flight Checks → Execute (jdc primary / SDK fallback) → Post-execution Validation → Failure Recovery**  
Do not skip any phase.

### Execution Strategy (jdc-first with SDK Fallback)

1. **Primary Path**: Attempt `jdc` CLI first for all operations
2. **Retry Logic**: If `jdc` fails, retry up to **3 times** with exponential backoff (0s → 2s → 4s)
3. **Fallback Path**: Only use SDK/API after 3 consecutive `jdc` failures
4. **Output Preference**: When both paths succeed, prefer `jdc` output for consistency

### Operation: Create Cluster

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| CLI / deps | `jdc --version` | Exit code 0 | Retry up to 3 times; then fall back to SDK |
| SDK / deps | `import jdcloud_sdk.services.nc.client.NcClient` | No import error | Document install pin (fallback path) |
| Credentials | Construct credential from env or CLI config | Non-empty keys | HALT; user configures env |
| Region | Call `describeClusters` with small page | `{{user.region}}` supported | Suggest valid region |
| VPC/Subnet | Verify via `jdcloud-vpc-ops` | Subnet exists and has IP | HALT; create subnet first |
| Kubernetes version | Validate version string | Supported version | List available versions |
| Quota | Check cluster count vs limit | Not exceeded | HALT; request quota increase |

#### Pre-flight: Configure jdc Config File for Sandbox

Before running any `jdc` command in sandboxed environments, ensure the config file exists:

```bash
# Setup jdc config in a writable location (sandbox-safe)
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc
cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = {{env.JDC_ACCESS_KEY}}
secret_key = {{env.JDC_SECRET_KEY}}
region_id = {{user.region}}
endpoint = nc.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF
printf "%s" "default" > /tmp/jdc-home/.jdc/current
```

#### Execution — CLI (`jdc`) [Primary Path]

**Required** when `cli_applicability: jdc-first-with-fallback`. Use `--output json` at the **top level** (before the subcommand). Do NOT use `--no-interactive` — it is not supported by jdc CLI.

```bash
jdc --output json nc create-cluster \
  --region-id "{{user.region}}" \
  --cluster-name "{{user.cluster_name}}" \
  --vpc-id "{{user.vpc_id}}" \
  --subnet-id "{{user.subnet_id}}" \
  --master-version "{{user.master_version}}" \
  --node-group-name "{{user.node_group_name}}" \
  --instance-type "{{user.instance_type}}" \
  --node-count {{user.node_count}}
```

#### Execution (SDK Fallback — after 3 jdc failures)

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

#### Post-execution Validation

1. Capture `{{output.cluster_id}}` from `$.result.clusterId`.
2. Poll `describeCluster` until `state` == `running` or timeout.

```bash
# CLI poll loop (primary path) — --output json at TOP level
for i in $(seq 1 20); do
  STATE=$(jdc --output json nc describe-cluster \
    --region-id "{{user.region}}" \
    --cluster-id "{{output.cluster_id}}" | jq -r '.result.cluster.state')
  [ "$STATE" = "running" ] && break
  sleep 30
done
```

```python
# SDK poll loop (fallback, after 3 jdc failures)
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

#### Execution (CLI) [Primary Path]

```bash
jdc --output json nc delete-cluster \
  --region-id "{{user.region}}" \
  --cluster-id "{{user.cluster_id}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.nc.apis.DeleteClusterRequest import DeleteClusterRequest, DeleteClusterParameters

params = DeleteClusterParameters(
    regionId="{{user.region}}",
    clusterId="{{user.cluster_id}}"
)
req = DeleteClusterRequest(parameters=params)
resp = client.send(req)
```

#### Post-execution Validation

Poll describe until 404 or max wait (600s).

```bash
# CLI poll loop
for i in $(seq 1 20); do
  jdc --output json nc describe-cluster \
    --region-id "{{user.region}}" \
    --cluster-id "{{user.cluster_id}}" 2>&1 | grep -q "NotFound" && break
  sleep 30
done
```

### Operation: Create Node Group

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| Cluster exists | `describeCluster` | Cluster found | HALT; verify cluster ID |
| Cluster state | `describeCluster` | `running` | Wait or suggest appropriate action |
| Instance type | User input | Valid instance type | List available types |
| Node count | User input | ≥ 1, ≤ quota | Validate range |

#### Execution (CLI) [Primary Path]

```bash
jdc --output json nc create-node-group \
  --region-id "{{user.region}}" \
  --cluster-id "{{user.cluster_id}}" \
  --name "{{user.node_group_name}}" \
  --instance-type "{{user.instance_type}}" \
  --node-count {{user.node_count}} \
  --subnet-id "{{user.subnet_id}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

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

#### Post-execution Validation

1. Capture `{{output.node_group_id}}` from `$.result.nodeGroupId`.
2. Poll `describeNodeGroup` until `state` == `running` or timeout.

```bash
# CLI poll loop
for i in $(seq 1 20); do
  STATE=$(jdc --output json nc describe-node-group \
    --region-id "{{user.region}}" \
    --cluster-id "{{user.cluster_id}}" \
    --node-group-id "{{output.node_group_id}}" | jq -r '.result.nodeGroup.state')
  [ "$STATE" = "running" ] && break
  sleep 15
done
```

### Operation: Describe Node Group

#### Execution (CLI) [Primary Path]

```bash
jdc --output json nc describe-node-group \
  --region-id "{{user.region}}" \
  --cluster-id "{{user.cluster_id}}" \
  --node-group-id "{{user.node_group_id}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

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

#### Execution (CLI) [Primary Path]

```bash
jdc --output json nc delete-node-group \
  --region-id "{{user.region}}" \
  --cluster-id "{{user.cluster_id}}" \
  --node-group-id "{{user.node_group_id}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

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

#### Execution (CLI) [Primary Path]

```bash
jdc --output json nc modify-node-group \
  --region-id "{{user.region}}" \
  --cluster-id "{{user.cluster_id}}" \
  --node-group-id "{{user.node_group_id}}" \
  --node-count {{user.node_count}}
```

#### Execution (SDK Fallback — after 3 jdc failures)

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

#### Post-execution Validation

Poll `describeNodeGroup` until `nodeCount` matches target and `state` is `running`.

### Operation: Describe Cluster Credentials

#### Execution (CLI) [Primary Path]

```bash
jdc --output json nc describe-cluster-credential \
  --region-id "{{user.region}}" \
  --cluster-id "{{user.cluster_id}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

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

#### Execution (CLI) [Primary Path]

```bash
jdc --output json nc modify-cluster \
  --region-id "{{user.region}}" \
  --cluster-id "{{user.cluster_id}}" \
  --master-version "{{user.target_version}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

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

#### Post-execution Validation

Poll `describeCluster` until `masterVersion` matches target and `state` is `running`.

### Operation: Describe Node Groups (List for a Cluster)

#### Execution (CLI) [Primary Path]

```bash
jdc --output json nc describe-node-groups \
  --region-id "{{user.region}}" \
  --cluster-id "{{user.cluster_id}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

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

## Quality Gate (GCL)

> This skill participates in the repository-wide **Generator-Critic-Loop**
> (GCL) defined in [`AGENTS.md` §Quality Gate](../AGENTS.md#generator-critic-loop-gcl--adversarial-quality-gate).
> The quality gate is **required** for all operations exposed by this
> skill (per `AGENTS.md` §8). Cluster delete is destructive and requires
> the strictest review.

### Parameters (override `AGENTS.md` §8 defaults)

| Parameter | Value | Reason |
|---|---|---|
| `max_iterations` | **2** | `AGENTS.md` §8 default for `jdcloud-kubernetes-ops` (required); cluster delete is destructive and impacts all workloads |
| `rubric_version` | `v1` | see [rubric.md](references/rubric.md) |
| `trace_path` | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | unified with `jdcloud-audit-ops` |
| `safety_confirm_required` | **true** for `delete-cluster`, `delete-node-group` | matches repository safety gate policy |
| `workload_analysis_required` | **true** for `delete-cluster` | must invoke `k8s_analyzer` before cluster delete |

### Loop overview

```
User request
   │
   ▼
[0] Pre-flight (Orchestrator)
    - resolve env.* and user.* variables
    - pick skill, load its rubric
    - prepare k8s_analyzer if needed
   │
   ▼
[1] Generate (G)
    - run jdc / SDK
    - capture trace
    - run k8s_analyzer pre-check if delete-cluster
   │
   ▼
[2] Critique (C)
    - isolated prompt context
    - score every rubric dimension
    - emit actionable suggestions
   │
   ▼
[3] Decide (Orchestrator)
    - Safety=0  → ABORT (no partial)
    - all pass  → RETURN
    - else & iter<max → inject suggestions into G
    - else → RETURN best + unresolved rubric items
```

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

1. **Install uv** (system-wide, one-time per machine)

   ```bash
   # macOS / Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   # or: brew install uv

   # Windows (PowerShell)
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **Bootstrap Python environment** (idempotent — safe to re-run):

   ```bash
   uv venv --python 3.10
   source .venv/bin/activate
   uv pip install jdcloud_cli jdcloud_sdk
   jdc --version
   ```

3. **Configure Credentials** — Two methods (CLI vs SDK differ):

   **SDK (env vars):**
   ```bash
   export JDC_ACCESS_KEY="{{env.JDC_ACCESS_KEY}}"
   export JDC_SECRET_KEY="{{env.JDC_SECRET_KEY}}"
   export JDC_REGION="cn-north-1"
   ```

   **CLI (`~/.jdc/config` INI):**
   ```bash
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

4. **Verify Configuration**:
   ```bash
   jdc --output json nc describe-clusters --region-id cn-north-1 --page-number 1 --page-size 1
   ```

> **Security:** Never commit `.env` to version control (already in `.gitignore`). All credentials use `{{env.*}}` placeholders — never real values.

## Operational Best Practices

- **Least privilege:** IAM policies scoped to required APIs only (cluster CRUD, node group operations, credential retrieval).
- **Availability:** Deploy multi-AZ clusters with node groups in at least two availability zones.
- **Cost:** Right-size node instance types; use auto-scaling for node groups to optimize spend.
- **Backup:** Regularly backup etcd and persistent volumes (PV). Cluster deletion is irreversible.
- **Security:** Rotate cluster credentials regularly. Store kubeconfig securely. Use IAM roles for cross-account access.
- **Upgrades:** Always upgrade one minor version at a time. Test workload compatibility in a staging cluster first.