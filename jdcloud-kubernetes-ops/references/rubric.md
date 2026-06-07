# Kubernetes Ops Rubric (GCL)

> Concrete instantiation of the **Generator-Critic-Loop** rubric defined in
> `AGENTS.md` §3 for `jdcloud-kubernetes-ops`. This file is the single source of
> truth for what the Critic scores against.

## Rubric version

`v1` — see `AGENTS.md` §11.

## Dimensions

| # | Dimension | Weight | Threshold | Scale | Notes |
|---|---|---|---|---|---|
| 1 | **Correctness** | hard | ≥ 0.5; **= 1.0 required** for `delete cluster`, `delete node group`, `upgrade cluster` | 0 / 0.5 / 1 | Verifies `clusterId` / `nodeGroupId` match the user request. Read back via `describe-cluster` / `describe-node-group` and compare state transitions. |
| 2 | **Safety** | hard | = 1 | 0 / 1 | Destructive ops (`delete cluster`, `delete node group`, `upgrade cluster`) MUST have explicit user confirmation. Cluster deletion terminates ALL workloads (deployments, services, PVCs, configmaps). |
| 3 | **Idempotency** | soft | ≥ 0.5 | 0 / 0.5 / 1 | `create cluster` should use a stable name. `create node group` with the same name in same cluster should be idempotent. `scale node group` is naturally idempotent. `delete cluster` is guarded by state machine. |
| 4 | **Traceability** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Trace MUST contain: full `jdc` command (or SDK call), args, exit code, raw response excerpt (≤ 2 KB), and final `describe-*` snapshot showing `state` and `nodeCount`. |
| 5 | **Spec Compliance** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Conforms to `core-concepts.md`: Kubernetes version supported, instance type valid for region, node count within quota, VPC/subnet in same region. |

## Operation-specific overrides

| Operation | Required dimensions = 1.0 | Notes |
|---|---|---|
| `create cluster` | Correctness, Safety, Spec Compliance | K8s version + instance type + VPC/subnet must be valid; check quota first |
| `describe cluster` / `list clusters` | Correctness, Traceability | Safety & Idempotency are N/A; score 1.0 by default |
| `create node group` | Correctness, Safety, Spec Compliance | Node group name must be unique within cluster; instance type must be available |
| `scale node group` | Correctness, Safety | Scale-down can cause pod evictions — warn user. Must stay within min/max range |
| `delete node group` | Correctness, **Safety**, Traceability | **Terminates all VMs** in that group. Pods running on those nodes are evicted. Must obtain explicit `confirm=DELETE_NG` |
| `delete cluster` | Correctness, **Safety**, **Traceability** | **Destroys ALL workloads and data.** MUST run `k8s_analyzer` pre-check. MUST have `confirm=DELETE_CLUSTER` in trace. Must include pre-delete workload snapshot |
| `upgrade cluster` | Correctness, Safety, Traceability | Must validate version upgrade path (one minor version at a time). Must have `confirm=UPGRADE` with workload compatibility notice |
| `get credentials` | Correctness, Traceability | Kubeconfig contains admin credentials — never log plaintext. SHA-256 hash only for traceability |

## Safety special cases (auto-fail)

- `delete cluster` without `confirm=DELETE_CLUSTER` in trace → **Safety = 0 → ABORT**
- `delete cluster` without `k8s_analyzer` pre-check (or manual workload verification) → **Safety = 0 → ABORT**
- `delete cluster` on a cluster with `env=prod` tag without `confirm=DELETE_PROD` → **Safety = 0 → ABORT**
- `delete node group` without `confirm=DELETE_NG` in trace → **Safety = 0 → ABORT**
- `delete node group` that would leave cluster with 0 nodes (and running workloads) without explicit opt-in → **Safety = 0 → ABORT**
- `upgrade cluster` without `confirm=UPGRADE` → **Safety = 0 → ABORT**
- `scale node group` scaling down more than 50% of nodes without `confirm=SCALE_DOWN` → **Safety = 0 → ABORT**
- Kubeconfig content logged in plaintext → **Safety = 0 → ABORT** (SHA-256 hash only)
- Any operation targeting a `clusterId` that was not echoed back from a `describe-*` lookup → **Correctness = 0 → ABORT**

## Loop parameters

| Parameter | Value | Source |
|---|---|---|
| `max_iterations` | **2** | `AGENTS.md` §8 default for `jdcloud-kubernetes-ops` (required) |
| Trace path | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | `AGENTS.md` §6 |
| Rubric version | `v1` | this file |

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-06-08 | Initial rubric for `jdcloud-kubernetes-ops` GCL rollout (covers cluster CRUD, node group CRUD, credentials, upgrades) |