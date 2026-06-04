---
name: jdcloud-elasticsearch-ops
description: >-
  Use this skill for JD Cloud Elasticsearch (云搜索Elasticsearch) management — create, configure,
  manage Elasticsearch clusters; monitor cluster health and performance; analyze index metrics;
  troubleshoot cluster issues; perform snapshot and restore operations. Apply when the user mentions
  Elasticsearch, 云搜索, ES集群, 搜索引擎, or asks about full-text search, log analytics, or 
  Elasticsearch clusters on JD Cloud, even without explicit "Elasticsearch" mentions.
license: MIT
compatibility: >-
  Official JD Cloud SDK (Python 3.10+), valid API credentials, network
  access to JD Cloud endpoints. This product is NOT supported by the `jdc` CLI;
  SDK/API is the only execution path.
metadata:
  author: buhaiqing
  version: "2.2.0"
  last_updated: "2026-06-04"
  runtime: Harness AI Agent
  api_profile: "JD Cloud Elasticsearch API v1 - https://es.jdcloud-api.com/v1"
  cli_applicability: sdk-only
  cli_version_locked: "N/A"
  sdk_version_locked: ">=1.6.26"
  cli_support_evidence: >-
    Verified on 2026-06-03: `jdc --help` output does NOT include 'es' in the product list.
    Elasticsearch operations must use the Python SDK (`jdcloud_sdk.services.es`) exclusively.
  environment:
    - JDC_ACCESS_KEY
    - JDC_SECRET_KEY
    - JDC_REGION
---

> This skill follows the [Agent Skill OpenSpec](https://agentskills.io/specification).

# JD Cloud Elasticsearch Operations Skill

## Overview

JD Cloud Elasticsearch (云搜索Elasticsearch) is a fully managed, scalable search and analytics engine service. This skill is an **operational runbook** for agents: explicit scope, credential rules, pre-flight checks, **SDK-only execution** (jdc CLI does NOT support this product), response validation, and failure recovery.

### CLI applicability (repository policy)

- **`cli_applicability: sdk-only`:** Official `jdc` CLI does **NOT** support this product (verified 2026-06-03). **All operations MUST use the Python SDK** (`jdcloud_sdk.services.es`). The `references/cli-usage.md` file is **omitted** per repository policy for `sdk-only` skills.

### Path Preference (SDK-Only)

1. **SDK/API (only path)** — Use `jdcloud_sdk.services.es` for all operations.
2. **Client init:** `EsClient(credential)` — no region param; region goes into request params.
3. **Response handling:** `resp.result` is a dict. `instances` may be `null` — use `or []`.

### Critical SDK Behavioral Notes (Verified 2026-06-03)

| # | Finding | Workaround |
|---|---------|------------|
| 1 | `EsClient(credential, "cn-north-1")` raises `AttributeError` (region is not 2nd arg) | `EsClient(credential)` + `params.setRegionId()` |
| 2 | Empty region returns `"instances": null` (not `[]`) | `resp.result.get("instances") or []` |
| 3 | Field names are `instanceVersion`/`instanceStatus` (not `version`/`status`) | Use the verified field names from API Field Table below |
| 4 | `cn-south-2` returns `400 INVALID_ARGUMENT` | Valid: `cn-north-1`, `cn-east-1`, `cn-east-2`, `cn-south-1` |
| 5 | `tags` field may be `null` | `inst.get("tags") or []` |

**Available SDK modules:**

```python
from jdcloud_sdk.services.es.client.EsClient import EsClient
from jdcloud_sdk.services.es.apis.CreateInstanceRequest import CreateInstanceRequest, CreateInstanceParameters
from jdcloud_sdk.services.es.apis.DeleteInstanceRequest import DeleteInstanceRequest, DeleteInstanceParameters
from jdcloud_sdk.services.es.apis.DescribeInstanceRequest import DescribeInstanceRequest, DescribeInstanceParameters
from jdcloud_sdk.services.es.apis.DescribeInstancesRequest import DescribeInstancesRequest, DescribeInstancesParameters
from jdcloud_sdk.services.es.apis.ModifyInstanceSpecRequest import ModifyInstanceSpecRequest, ModifyInstanceSpecParameters
```

## Trigger & Scope (Agent-Readable)

### SHOULD Use This Skill When

- User mentions "JD Cloud Elasticsearch" OR "云搜索" OR "ES集群" OR "Elasticsearch集群" OR "搜索引擎"
- Task involves CRUD on ES instances: create, describe, modify, delete, list
- Keywords: createInstance, describeInstances, modifyInstanceSpec, deleteInstance, cluster, index
- User asks to deploy, configure, troubleshoot, or monitor ES clusters via API/SDK/automation
- **Resource Audit Tasks**: tag compliance (标签合规), resource inventory (资源清单), compliance report generation, cross-region auditing

### SHOULD NOT Use This Skill When

- Pure billing / account management → `jdcloud-billing-ops`
- IAM / permission model only → `jdcloud-iam-ops`
- VPC / subnet / security group only → `jdcloud-vpc-ops`
- Monitoring metrics / alarms only → `jdcloud-cloudmonitor-ops`
- User insists on console-only flows with no API → state limitation

### Delegation Rules

- If ES cluster requires VPC/subnet, verify or create network resources via `jdcloud-vpc-ops` first.
- ES monitoring metrics and alarm rules → `jdcloud-cloudmonitor-ops`.
- Multi-product requests: handle each product with its own skill.

## Variable Convention (Agent-Readable)

| Placeholder | Meaning | Agent Action |
|-------------|---------|--------------|
| `{{env.JDC_ACCESS_KEY}}` | From runtime environment | NEVER ask user; fail if unset |
| `{{env.JDC_SECRET_KEY}}` | From runtime environment | NEVER ask user; fail if unset |
| `{{env.JDC_REGION}}` | From runtime environment | Default `cn-north-1` if unset |
| `{{user.region}}` | User-supplied region | Ask once; reuse |
| `{{user.instance_id}}` | User-supplied ES instance ID | Ask once; reuse |
| `{{user.instance_name}}` | User-supplied instance name | Ask once; reuse |
| `{{output.instance_id}}` | From last API response | Parse from `$.result.instanceId` |

> **`{{env.*}}` MUST NOT** be collected from the user. **`{{user.*}}`** MUST be collected interactively when missing.

> **Security:** **NEVER** log or print `JDC_SECRET_KEY`. Check existence only via `if os.environ.get('JDC_SECRET_KEY')`. Use `<masked>` when logging status.

## API Response Field Table (Verified from API 2026-06-03)

| Operation | JSON Path | Type | Description |
|-----------|-----------|------|-------------|
| Create Instance | `$.result.instanceId` | string | New ES instance ID |
| Describe Instance | `$.result.instance.instanceStatus` | string | running, creating, error, changing, stop, processing |
| Describe Instance | `$.result.instance.instanceVersion` | string | ES version (6.5.4, 7.10.0, etc.) |
| Describe Instance | `$.result.instance.instanceName` | string | Instance display name |
| Describe Instance | `$.result.instance.instanceClass` | object | `{nodeClass, nodeCount, nodeDiskGB, nodeDiskType, kibana, kibanaClass}` |
| Describe Instance | `$.result.instance.tags` | array | `[{key, value}]` |
| Describe Instance | `$.result.instance.endpoint` | string | ES HTTP endpoint |
| Describe Instance | `$.result.instance.kibanaUrl` | string | Kibana dashboard URL |
| Describe Instance | `$.result.instance.charge` | object | `{chargeMode, chargeStatus, chargeStartTime, chargeExpiredTime}` |
| List Instances | `$.result.instances[*].instanceId` | array | All instance IDs (may be null) |
| List Instances | `$.result.totalCount` | int | Total instance count |
| Modify/Delete | `$.requestId` or `$.error` | — | Per spec |

### Expected State Transitions

| Operation | Initial State | Target State | Poll Interval | Max Wait |
|-----------|---------------|--------------|---------------|----------|
| Create | — | `running` | 30s | 1800s (30min) |
| Modify Spec | `running` | `running` | 60s | 1800s (30min) |
| Delete | `running`/`stopped` | 404 on describe | 10s | 600s |

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 2.2.0 | 2026-06-04 | **GCL rollout**: Added `## Quality Gate (GCL)` chapter wiring this skill into the repository-wide Generator-Critic-Loop. Added `references/rubric.md` (5-dimension rubric, instance-level + ES REST paths, ES-specific rules for wildcard `DELETE /<index>`, `match_all` queries in `_update_by_query` / `_delete_by_query`, `_forcemerge max_num_segments=1`) and `references/prompt-templates.md` (G/C/O prompt skeletons). `max_iterations=2`. `safety_confirm_required=true` for delete, restore, node count / storage shrink, `DELETE /<index>`, `_close`, `_delete_by_query`, `_forcemerge max_num_segments=1`, snapshot deletion. |
| 2.1.0 | 2026-06-03 | **Refactored**: Moved quick inspection snippets, operational best practices to `references/`. SKILL.md is now concise (<300 lines). |
| 2.0.0 | 2026-06-03 | **Breaking**: Corrected `cli_applicability` to `sdk-only`. Added verified API field names. |
| 1.0.0 | 2026-06-03 | Initial version (incorrectly assumed CLI support) |

## Execution Flows (Agent-Readable)

Every operation: **Pre-flight → Execute (SDK only) → Validate → Recover**.

### Operation: Create Elasticsearch Instance

**Pre-flight:** SDK installed, credentials present, region valid, VPC/subnet exists (use `jdcloud-vpc-ops`).

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.es.client.EsClient import EsClient
from jdcloud_sdk.services.es.apis.CreateInstanceRequest import CreateInstanceRequest, CreateInstanceParameters

credential = Credential(os.environ["JDC_ACCESS_KEY"], os.environ["JDC_SECRET_KEY"])
client = EsClient(credential)

params = CreateInstanceParameters(
    regionId="{{user.region}}",
    instance={
        "instanceName": "{{user.instance_name}}",
        "instanceClass": "{{user.instance_class}}",
        "instanceVersion": "{{user.es_version}}",
        "vpcId": "{{user.vpc_id}}",
        "subnetId": "{{user.subnet_id}}",
        "azId": "{{user.az_id}}",
        "nodeSpec": {
            "nodeClass": "{{user.data_node_class}}",
            "nodeCount": {{user.data_node_count|default:3}},
            "nodeDiskGB": {{user.data_node_disk_gb}},
            "nodeDiskType": "{{user.data_node_disk_type}}"
        },
        "kibana": True,
        "kibanaSpec": {"kibanaClass": "{{user.kibana_class}}"}
    }
)
resp = client.send(CreateInstanceRequest(parameters=params))
instance_id = resp.result["instanceId"]
```

**Validate:** Poll `describeInstance` until `instanceStatus == "running"` (max 30 min, 30s interval). On `error`/`deleted` → HALT.

**Failure recovery:**

| Error | Retries | Backoff | Action |
|-------|---------|---------|--------|
| `InvalidParameter` / 400 | 0–1 | — | Fix args per OpenAPI; retry once |
| `QuotaExceeded` | 0 | — | HALT; user requests quota increase |
| `InsufficientBalance` | 0 | — | HALT; user tops up |
| `ResourceAlreadyExists` | 0 | — | Ask reuse vs new name |
| `INVALID_ARGUMENT` (region) | 0 | — | Use valid regions only |
| Throttling / 429 | 3 | exponential | Respect Retry-After |
| `InternalError` / 5xx | 3 | 2s, 4s, 8s | Retry; HALT with requestId if persists |

### Operation: Describe / List Instances

```python
from jdcloud_sdk.services.es.apis.DescribeInstanceRequest import DescribeInstanceRequest, DescribeInstanceParameters
from jdcloud_sdk.services.es.apis.DescribeInstancesRequest import DescribeInstancesRequest, DescribeInstancesParameters

# Single instance
resp = client.send(DescribeInstanceRequest(parameters=DescribeInstanceParameters(
    regionId="{{user.region}}", instanceId="{{user.instance_id}}"
)))
instance = resp.result["instance"]

# List (all instances in region)
params = DescribeInstancesParameters(regionId="{{user.region}}")
params.setPageNumber(1)
params.setPageSize(100)
resp = client.send(DescribeInstancesRequest(parameters=params))
instances = resp.result.get("instances") or []  # may be null!
total = resp.result.get("totalCount", len(instances))
```

**List filters** (use `params.setFilters([{...}])`): `instanceId` (exact, multi), `instanceVersion` (exact, single), `azId` (exact, single), `instanceName` (fuzzy, single), `instanceStatus` (exact, multi: running/error/creating/changing/stop/processing), `chargeMode`. Tag filter: `params.setTagFilters([{key, values}])`.

### Operation: Modify Instance Spec

**Pre-flight:** `describeInstance` returns valid state. **Confirm with user** — node scaling may cause brief service interruption.

```python
from jdcloud_sdk.services.es.apis.ModifyInstanceSpecRequest import ModifyInstanceSpecRequest, ModifyInstanceSpecParameters

resp = client.send(ModifyInstanceSpecRequest(parameters=ModifyInstanceSpecParameters(
    regionId="{{user.region}}",
    instanceId="{{user.instance_id}}",
    instanceSpec={"nodeSpec": {
        "nodeClass": "{{user.new_node_class}}",
        "nodeCount": {{user.new_node_count}},
        "nodeDiskGB": {{user.new_disk_gb}},
        "nodeDiskType": "{{user.new_disk_type}}"
    }}
)))
```

### Operation: Delete Elasticsearch Instance

**Safety Gate (REQUIRED):** MUST obtain explicit user confirmation: "Are you sure you want to delete {{user.instance_name}} ({{user.instance_id}})? This is IRREVERSIBLE." Proceed only after clear "yes"/"confirm" response.

```python
from jdcloud_sdk.services.es.apis.DeleteInstanceRequest import DeleteInstanceRequest, DeleteInstanceParameters

resp = client.send(DeleteInstanceRequest(parameters=DeleteInstanceParameters(
    regionId="{{user.region}}", instanceId="{{user.instance_id}}"
)))
```

**Validate:** Poll `describeInstance` until 404 / deleted (max 600s, 10s interval).

## Quality Gate (GCL)

> This skill participates in the repository-wide **Generator-Critic-Loop**
> (GCL) defined in [`AGENTS.md` §Quality Gate](../AGENTS.md#generator-critic-loop-gcl--adversarial-quality-gate).
> The quality gate is **mandatory** for all operations exposed by this skill.

### Parameters (override `AGENTS.md` §8 defaults)

| Parameter | Value | Reason |
|---|---|---|
| `max_iterations` | **2** | `delete-instance` / `delete-index` (especially wildcard) / `_delete_by_query` / `_forcemerge max_num_segments=1` are destructive; do not retry repeatedly on production data |
| `rubric_version` | `v1` | see [rubric.md](references/rubric.md) |
| `trace_path` | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | unified with `jdcloud-audit-ops` |
| `safety_confirm_required` | **true** for `delete`, `restore`, node count / storage shrink, `DELETE /<index>`, `_close`, `_delete_by_query`, `_forcemerge max_num_segments=1`, snapshot deletion | matches repository safety gate policy |

### Loop overview

```
User request
   │
   ▼
[0] Orchestrator pre-flight  ──► load rubric, classify operation
   │
   ▼
[1] Generator (G)            ──► jdc (primary) → SDK / elasticsearch-py (after 3 fails)
   │
   ▼
[2] Critic (C)               ──► isolated context, blind to user request
   │
   ▼
[3] Orchestrator decider
   ├─ Safety=0 / blocking   → ABORT
   ├─ all pass              → RETURN
   ├─ iter<2 & not all pass → RETRY (inject suggestions)
   └─ iter=2 & not all pass → RETURN_BEST
```

### Artifacts

- Rubric (concrete scoring rules): [references/rubric.md](references/rubric.md)
- Prompt templates (G / C / O): [references/prompt-templates.md](references/prompt-templates.md)

### Integration with existing flows

The GCL **wraps** the jdc-first / SDK-fallback flow defined under
`## Execution Flows` above. The Generator (G) IS the existing jdc-or-SDK
executor. The Critic (C) is a new, read-only role with no `jdc` / SDK /
ES HTTP access. The Orchestrator (O) owns the loop and persists the GCL
trace.

### Operation-specific behavior

- **`create-instance`** — Critic verifies `--client-token` was set
  (Idempotency = 1 required). Missing → Idempotency = 0.
- **`delete-instance`** — Critic checks the trace contains both a pre-delete
  `describe-instance` snapshot and a post-delete 404. Missing either →
  Correctness = 0.
- **`restore-instance`** — `snapshotId` must belong to the same `instanceId`;
  cross-instance restore requires explicit user confirm in trace or Safety = 0.
- **`modify-instance` (node count / storage)** — Node count shrink and
  storage shrink are **forbidden** without user opt-in. Safety = 0 otherwise.
- **`PUT /<index>` (create index)** — Full settings + mappings must appear
  in trace. Idempotency check: re-creating with same name + same settings is
  idempotent.
- **`DELETE /<index>` (delete index)** — Always Safety = 0 without
  `confirm=DELETE_INDEX` in trace → ABORT. **Wildcard delete (e.g.,
  `logs-*`) requires additional `confirm=DELETE_WILDCARD_INDEX`**.
- **`POST /<index>/_close`** — Closes index (blocks reads/writes); Safety = 0
  without `confirm=CLOSE` → ABORT.
- **`POST /<index>/_update_by_query`** — Query MUST be non-empty (not `{}`,
  not `match_all` only). Missing query → Safety = 0 → ABORT. Prefer
  `?conflicts=proceed&wait_for_completion=false&scroll_size=1000` for large
  ops; capture task id in trace.
- **`POST /<index>/_delete_by_query`** — Query MUST be non-empty. Missing
  query → Safety = 0 → ABORT. ALWAYS snapshot the index first
  (`PUT /_snapshot/...`); capture task id in trace.
- **`POST /<index>/_forcemerge`** — `max_num_segments=1` is destructive
  (large IO); Safety = 0 without `confirm=FORCEMERGE` → ABORT.
- **`POST /_reindex`** — `source` and `dest` must be echoed. Safety = 0 if
  `dest` is wildcard (`logs-*`) or production index without opt-in.
- **`POST /<index>/_search`** — Read-only; Safety = 1.0 by default.
- **`DELETE /_snapshot/<repo>/<snap>`** — Safety = 0 without
  `confirm=DELETE_SNAPSHOT` → ABORT.
- **`PUT /_ilm/policy/<name>` (ILM policy)** — Affects index lifecycle;
  Safety = 0 if `delete` action included without opt-in.
- **All ES ops** — Always pre-check via `GET _cat/indices?v` /
  `GET _cluster/health` / `GET /<index>/_count` and include result in trace;
  full HTTP method + URL + body must appear verbatim.

## Prerequisites

> **Python 3.10 is REQUIRED, NOT 3.12.** `jdcloud_cli==1.2.12` uses `SafeConfigParser` removed in 3.12. Always use `uv venv --python 3.10`.

```bash
uv venv --python 3.10 && source .venv/bin/activate
uv pip install jdcloud_sdk python-dotenv
python -c "from jdcloud_sdk.services.es.client.EsClient import EsClient; print('ES SDK OK')"
```

SDK reads `JDC_ACCESS_KEY`/`JDC_SECRET_KEY` from environment (or `.env` via `python-dotenv`). Never commit `.env`.

## Reference Directory

| Document | Purpose |
|----------|---------|
| [Core Concepts](references/core-concepts.md) | Domain knowledge: ES architecture, instance classes, billing |
| [API & SDK Usage](references/api-sdk-usage.md) | Full SDK operations map, request/response examples |
| [Quick Snippets](references/quick-snippets.md) | **Ready-to-use scripts**: tag audit, resource inventory, expiring alert, DOPS ticket |
| [Troubleshooting](references/troubleshooting.md) | Common errors, debugging steps |
| [Monitoring](references/monitoring.md) | CloudMonitor metrics, alarm rules |
| [Integration](references/integration.md) | Cross-skill delegation patterns |
| [Resource Audit](references/resource-audit.md) | Tag compliance auditing and inventory |
| [Operational Best Practices](references/operational-best-practices.md) | Architecture, HA, security, scaling, ILM |

> `references/cli-usage.md` is **omitted** per repository policy for `sdk-only` skills.
