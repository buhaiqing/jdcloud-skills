---
name: jdcloud-tag-audit-ops
description: >-
  Use this skill for JD Cloud tag compliance auditing across multiple products and regions.
  Check resource tags for compliance, generate audit reports, and create DOPS tickets for non-compliant resources.
  Apply when the user mentions tag audit, 标签合规, compliance check, or asks about resource tagging across JD Cloud.
license: MIT
compatibility: >-
  Official JD Cloud SDK (Python 3.10+), valid API credentials, network
  access to JD Cloud endpoints, and official JD Cloud CLI (`jdc`).
metadata:
  author: buhaiqing
  version: "1.6.0"
  last_updated: "2026-06-18"
  runtime: Harness AI Agent
  api_profile: "JD Cloud Multi-Product API"
  cli_applicability: jdc-first-with-fallback
  cli_version_locked: "1.2.12"
  sdk_version_locked: ">=1.6.26"
  environment:
    - JDC_ACCESS_KEY
    - JDC_SECRET_KEY
    - JDC_REGION
---

> This skill follows the [Agent Skill OpenSpec](https://agentskills.io/specification).

# JD Cloud Tag Audit Operations Skill

## Overview

JD Cloud Tag Audit (`jdcloud-tag-audit-ops`) is a unified skill for auditing resource tags across multiple JD Cloud products and regions. It provides:
- Cross-product tag compliance checking (Redis, VM, RDS, CLB, EIP, MongoDB, Elasticsearch)
- Multi-region scanning capability
- Automated audit report generation
- DOPS ticket creation for non-compliant resources

## Supported Products

| Product | CLI Command | JSON Path | Instance ID Field | Name Field | Engine Field |
|---------|-------------|-----------|------------------|------------|--------------|
| Redis | `redis describe-cache-instances` | `$.result.cacheInstances[]` | `cacheInstanceId` | `cacheInstanceName` | N/A |
| VM | `vm describe-instances` | `$.result.instances[]` | `instanceId` | `name` | N/A |
| RDS MySQL | `rds describe-instances` | `$.result.dbInstances[]` | `instanceId` | `instanceName` | `engine` |
| RDS PostgreSQL | `rds describe-instances` | `$.result.dbInstances[]` | `instanceId` | `instanceName` | `engine` |
| MongoDB | `mongodb describe-instances` | `$.result.instances[]` | `instanceId` | `instanceName` | `engine` |
| Elasticsearch | `es describe-instances` (SDK-only) | `$.result.instances[]` | `instanceId` | `instanceName` | N/A |
| CLB | `clb describe-load-balancers` | `$.result.loadBalancers[]` | `loadBalancerId` | `loadBalancerName` | N/A |
| EIP | `eip describe-addresses` | `$.result.addresses[]` | `addressId` | `name` | N/A |

## Supported Regions

- cn-north-1 (华北-北京)
- cn-east-1 (华东-青岛)
- cn-east-2 (华东-上海)
- cn-south-1 (华南-广州)
- cn-south-2 (华南-深圳)

## Trigger & Scope

### SHOULD Use This Skill When
- User mentions "tag audit", "标签合规", "compliance check"
- User wants to check tags across multiple products/regions
- User needs to generate tag compliance reports
- User wants to create DOPS tickets for non-compliant resources

### SHOULD NOT Use This Skill When
- Task is about modifying individual resource tags → delegate to specific product skills
- Task is about IAM/permissions → delegate to jdcloud-iam-ops

## Variable Convention

| Placeholder | Meaning | Agent Action |
|-------------|---------|--------------|
| `{{env.JDC_ACCESS_KEY}}` | From runtime environment | NEVER ask the user |
| `{{env.JDC_SECRET_KEY}}` | From runtime environment | NEVER ask the user |
| `{{user.regions}}` | User-supplied regions list | Use all available if unset |
| `{{user.products}}` | User-supplied products list | Use all supported if unset |
| `{{user.required_tags}}` | Required tag keys | Default: ["环境", "客户"] |
| `{{output.audit_result}}` | Audit results JSON | Parsed from CLI/API response |

## Execution Flows

### Operation: Audit Tag Compliance

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| Credentials | Check ~/.jdc/config exists | Valid credentials | HALT; user configures |
| Available Regions | Query describe-regions | List of available regions | Use default regions |

#### Execution (CLI)

```bash
# Setup jdc config for sandbox
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc
cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = {{env.JDC_ACCESS_KEY}}
secret_key = {{env.JDC_SECRET_KEY}}
region_id = cn-north-1
scheme = https
timeout = 20
CONFIGEOF
printf "%s" "default" > /tmp/jdc-home/.jdc/current

# Audit Redis tags across regions
for region in cn-north-1 cn-east-2 cn-south-1; do
    echo "=== Redis - $region ==="
    jdc --output json redis describe-cache-instances \
      --region-id $region --page-number 1 --page-size 100 | \
    jq '.result.cacheInstances[] | 
        . as $instance |
        ($instance.tags // []) | map(.key) | . as $existing |
        [($required_tags[] | select(. as $tag | $existing | contains([$tag]) | not))] |
        select(length > 0) |
        {
            product: "redis",
            region: "'"$region"'",
            id: $instance.cacheInstanceId,
            name: $instance.cacheInstanceName,
            missingTags: .
        }'
done

# Audit CLB tags across regions
for region in cn-north-1 cn-east-2 cn-south-1; do
    echo "=== CLB - $region ==="
    jdc --output json clb describe-load-balancers \
      --region-id $region --page-number 1 --page-size 100 | \
    jq '.result.loadBalancers[] | 
        . as $instance |
        ($instance.tags // []) | map(.key) | . as $existing |
        [($required_tags[] | select(. as $tag | $existing | contains([$tag]) | not))] |
        select(length > 0) |
        {
            product: "clb",
            region: "'"$region"'",
            id: $instance.loadBalancerId,
            name: $instance.loadBalancerName,
            missingTags: .
        }'
done

# Audit EIP tags across regions
for region in cn-north-1 cn-east-2 cn-south-1; do
    echo "=== EIP - $region ==="
    jdc --output json eip describe-addresses \
      --region-id $region --page-number 1 --page-size 100 | \
    jq '.result.addresses[] | 
        . as $instance |
        ($instance.tags // []) | map(.key) | . as $existing |
        [($required_tags[] | select(. as $tag | $existing | contains([$tag]) | not))] |
        select(length > 0) |
        {
            product: "eip",
            region: "'"$region"'",
            id: $instance.addressId,
            name: ($instance.name // "N/A"),
            missingTags: .
        }'
done

# Audit RDS MySQL tags across regions
for region in cn-north-1 cn-east-2 cn-south-1; do
    echo "=== RDS MySQL - $region ==="
    jdc --output json rds describe-instances \
      --region-id $region --page-number 1 --page-size 100 | \
    jq '.result.dbInstances[] | 
        select(.engine == "MySQL") |
        . as $instance |
        ($instance.tags // []) | map(.key) | . as $existing |
        [($required_tags[] | select(. as $tag | $existing | contains([$tag]) | not))] |
        select(length > 0) |
        {
            product: "rds-mysql",
            region: "'"$region"'",
            id: $instance.instanceId,
            name: $instance.instanceName,
            engine: $instance.engine,
            missingTags: .
        }'
done

# Audit RDS PostgreSQL tags across regions
for region in cn-north-1 cn-east-2 cn-south-1; do
    echo "=== RDS PostgreSQL - $region ==="
    jdc --output json rds describe-instances \
      --region-id $region --page-number 1 --page-size 100 | \
    jq '.result.dbInstances[] | 
        select(.engine == "PostgreSQL") |
        . as $instance |
        ($instance.tags // []) | map(.key) | . as $existing |
        [($required_tags[] | select(. as $tag | $existing | contains([$tag]) | not))] |
        select(length > 0) |
        {
            product: "rds-postgresql",
            region: "'"$region"'",
            id: $instance.instanceId,
            name: $instance.instanceName,
            engine: $instance.engine,
            missingTags: .
        }'
done

# Audit MongoDB tags across regions
for region in cn-north-1 cn-east-2 cn-south-1; do
    echo "=== MongoDB - $region ==="
    jdc --output json mongodb describe-instances \
      --region-id $region --page-number 1 --page-size 100 | \
    jq '.result.instances[] | 
        . as $instance |
        ($instance.tags // []) | map(.key) | . as $existing |
        [($required_tags[] | select(. as $tag | $existing | contains([$tag]) | not))] |
        select(length > 0) |
        {
            product: "mongodb",
            region: "'"$region"'",
            id: $instance.instanceId,
            name: $instance.instanceName,
            engine: $instance.engine,
            engineVersion: $instance.engineVersion,
            missingTags: .
        }'
done

# Audit Elasticsearch tags across regions (SDK-only — jdc CLI does NOT support 'es')
# See SDK Fallback section below for Elasticsearch audit code
```

#### Execution (SDK Fallback)

```python
import os
from jdcloud_sdk.core.credential import Credential

credential = Credential(os.environ["JDC_ACCESS_KEY"], os.environ["JDC_SECRET_KEY"])

# Audit function for Redis
def audit_redis_tags(region, required_tags):
    from jdcloud_sdk.services.redis.client.RedisClient import RedisClient
    from jdcloud_sdk.services.redis.apis.DescribeCacheInstancesRequest import DescribeCacheInstancesRequest, DescribeCacheInstancesParameters
    
    client = RedisClient(credential)
    params = DescribeCacheInstancesParameters(regionId=region)
    req = DescribeCacheInstancesRequest(parameters=params)
    resp = client.send(req)
    
    results = []
    for instance in resp.result.get("cacheInstances", []):
        existing_tags = [tag["key"] for tag in instance.get("tags", [])]
        missing_tags = [tag for tag in required_tags if tag not in existing_tags]
        if missing_tags:
            results.append({
                "product": "redis",
                "region": region,
                "id": instance["cacheInstanceId"],
                "name": instance["cacheInstanceName"],
                "missingTags": missing_tags
            })
    return results

# Audit function for CLB
def audit_clb_tags(region, required_tags):
    from jdcloud_sdk.services.clb.client.ClbClient import ClbClient
    from jdcloud_sdk.services.clb.apis.DescribeLoadBalancersRequest import DescribeLoadBalancersRequest, DescribeLoadBalancersParameters
    
    client = ClbClient(credential)
    params = DescribeLoadBalancersParameters(regionId=region)
    req = DescribeLoadBalancersRequest(parameters=params)
    resp = client.send(req)
    
    results = []
    for instance in resp.result.get("loadBalancers", []):
        existing_tags = [tag["key"] for tag in instance.get("tags", [])]
        missing_tags = [tag for tag in required_tags if tag not in existing_tags]
        if missing_tags:
            results.append({
                "product": "clb",
                "region": region,
                "id": instance["loadBalancerId"],
                "name": instance["loadBalancerName"],
                "missingTags": missing_tags
            })
    return results

# Audit function for EIP
def audit_eip_tags(region, required_tags):
    from jdcloud_sdk.services.eip.client.EipClient import EipClient
    from jdcloud_sdk.services.eip.apis.DescribeAddressesRequest import DescribeAddressesRequest, DescribeAddressesParameters
    
    client = EipClient(credential)
    params = DescribeAddressesParameters(regionId=region)
    req = DescribeAddressesRequest(parameters=params)
    resp = client.send(req)
    
    results = []
    for instance in resp.result.get("addresses", []):
        existing_tags = [tag["key"] for tag in instance.get("tags", [])]
        missing_tags = [tag for tag in required_tags if tag not in existing_tags]
        if missing_tags:
            results.append({
                "product": "eip",
                "region": region,
                "id": instance["addressId"],
                "name": instance.get("name", "N/A"),
                "missingTags": missing_tags
            })
    return results

# Audit function for RDS MySQL
def audit_rds_mysql_tags(region, required_tags):
    from jdcloud_sdk.services.rds.client.RdsClient import RdsClient
    from jdcloud_sdk.services.rds.apis.DescribeInstancesRequest import DescribeInstancesRequest, DescribeInstancesParameters
    
    client = RdsClient(credential)
    params = DescribeInstancesParameters(regionId=region)
    req = DescribeInstancesRequest(parameters=params)
    resp = client.send(req)
    
    results = []
    for instance in resp.result.get("dbInstances", []):
        if instance.get("engine") != "MySQL":
            continue
        existing_tags = [tag["key"] for tag in instance.get("tags", [])]
        missing_tags = [tag for tag in required_tags if tag not in existing_tags]
        if missing_tags:
            results.append({
                "product": "rds-mysql",
                "region": region,
                "id": instance["instanceId"],
                "name": instance["instanceName"],
                "engine": instance["engine"],
                "missingTags": missing_tags
            })
    return results

# Audit function for RDS PostgreSQL
def audit_rds_postgresql_tags(region, required_tags):
    from jdcloud_sdk.services.rds.client.RdsClient import RdsClient
    from jdcloud_sdk.services.rds.apis.DescribeInstancesRequest import DescribeInstancesRequest, DescribeInstancesParameters
    
    client = RdsClient(credential)
    params = DescribeInstancesParameters(regionId=region)
    req = DescribeInstancesRequest(parameters=params)
    resp = client.send(req)
    
    results = []
    for instance in resp.result.get("dbInstances", []):
        if instance.get("engine") != "PostgreSQL":
            continue
        existing_tags = [tag["key"] for tag in instance.get("tags", [])]
        missing_tags = [tag for tag in required_tags if tag not in existing_tags]
        if missing_tags:
            results.append({
                "product": "rds-postgresql",
                "region": region,
                "id": instance["instanceId"],
                "name": instance["instanceName"],
                "engine": instance["engine"],
                "missingTags": missing_tags
            })
    return results

# Audit function for MongoDB
def audit_mongodb_tags(region, required_tags):
    from jdcloud_sdk.services.mongodb.client.MongodbClient import MongodbClient
    from jdcloud_sdk.services.mongodb.apis.DescribeInstancesRequest import DescribeInstancesRequest, DescribeInstancesParameters
    
    client = MongodbClient(credential)
    params = DescribeInstancesParameters(regionId=region)
    req = DescribeInstancesRequest(parameters=params)
    resp = client.send(req)
    
    results = []
    for instance in resp.result.get("instances", []):
        existing_tags = [tag["key"] for tag in instance.get("tags", [])]
        missing_tags = [tag for tag in required_tags if tag not in existing_tags]
        if missing_tags:
            results.append({
                "product": "mongodb",
                "region": region,
                "id": instance["instanceId"],
                "name": instance["instanceName"],
                "engine": instance.get("engine", "MongoDB"),
                "engineVersion": instance.get("engineVersion", ""),
                "missingTags": missing_tags
            })
    return results

# Audit function for Elasticsearch (SDK-only — jdc CLI does NOT support 'es')
def audit_elasticsearch_tags(region, required_tags):
    """Note: jdc CLI does NOT support 'es' product. Must use SDK only.
    Key field names from actual API: instanceVersion, instanceStatus (NOT version/status).
    Response instances may be null when empty — use .get("instances") or [].
    Valid ES regions: cn-north-1, cn-east-1, cn-east-2, cn-south-1 (cn-south-2 is invalid).
    """
    from jdcloud_sdk.services.es.client.EsClient import EsClient
    from jdcloud_sdk.services.es.apis.DescribeInstancesRequest import DescribeInstancesRequest, DescribeInstancesParameters
    
    # IMPORTANT: EsClient(credential) — NO region as second arg
    client = EsClient(credential)
    params = DescribeInstancesParameters(regionId=region)
    params.setPageNumber(1)
    params.setPageSize(100)
    req = DescribeInstancesRequest(parameters=params)
    resp = client.send(req)
    
    # IMPORTANT: instances may be null when empty
    instances = resp.result.get("instances") or []
    
    results = []
    for instance in instances:
        existing_tags = [tag["key"] for tag in instance.get("tags", []) or []]
        missing_tags = [tag for tag in required_tags if tag not in existing_tags]
        if missing_tags:
            results.append({
                "product": "elasticsearch",
                "region": region,
                "id": instance["instanceId"],
                "name": instance["instanceName"],
                "version": instance.get("instanceVersion", ""),  # NOT "version"
                "status": instance.get("instanceStatus", ""),    # NOT "status"
                "missingTags": missing_tags
            })
    return results
```

### Operation: Generate Audit Report

```bash
# Generate summary report
echo "## Tag Compliance Audit Report"
echo "### Summary"
echo "- Total resources scanned: $total_count"
echo "- Non-compliant resources: $non_compliant_count"
echo "- Compliance rate: $compliance_rate%"
echo ""
echo "### Non-compliant Resources by Product"
echo "| Product | Count |"
echo "|---------|-------|"
echo "| Redis | $redis_count |"
echo "| VM | $vm_count |"
echo "| RDS MySQL | $rds_mysql_count |"
echo "| RDS PostgreSQL | $rds_postgresql_count |"
echo "| MongoDB | $mongodb_count |"
echo "| Elasticsearch | $es_count |"
echo "| CLB | $clb_count |"
echo "| EIP | $eip_count |"
```

### Operation: Create DOPS Ticket for Non-Compliant Resources

```python
# Example: Create DOPS ticket via MCP
from mcp import run_mcp

ticket_summary = f"Tag Compliance: {non_compliant_count} resources missing required tags"
ticket_description = f"## Non-compliant Resources\n\n{audit_table}"

result = run_mcp(
    server_name="mcp_hdops_mcp",
    tool_name="create_dops_issue",
    args={
        "summary": ticket_summary,
        "description": ticket_description,
        "operator": "zhoulu",
        "accepter": "xuhao",
        "labels": "标签合规,资源管理"
    }
)
```

## Quality Gate (GCL)

> This skill participates in the repository-wide **Generator-Critic-Loop**
> (GCL) defined in [`AGENTS.md` §Quality Gate](../AGENTS.md#generator-critic-loop-gcl--adversarial-quality-gate).
> The quality gate is **optional** for this skill (per `AGENTS.md` §8) —
> audit / report are read-only; DOPS ticket creation is the single
> mutating op.

### Parameters (override `AGENTS.md` §8 defaults)

| Parameter | Value | Reason |
|---|---|---|
| `max_iterations` | **3** | `AGENTS.md` §8 default for `jdcloud-tag-audit-ops` (optional) |
| `rubric_version` | `v2` | see [rubric.md](references/rubric.md) |
| `trace_path` | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | unified with `jdcloud-audit-ops` |
| `safety_confirm_required` | **true** for `create DOPS ticket` | only mutating op |
| `hallucination_check` | **optional** | Phase 6 H layer; optional for this skill |
| `reflexion_integration` | **enabled** | Phase 7 lightweight Reflexion; loads `docs/failure-patterns.md` |

### Loop overview

```
User request
   │
   ▼
[0] Orchestrator pre-flight  ──► load rubric, classify operation
   │                              optionally load failure-patterns.md
   ▼
[1] Generator (G)            ──► jdc <product> (primary) → SDK (after 3 fails)
   │                              generate command/payload (DO NOT execute yet)
   ▼
[1.5] Hallucination Detection (H) ──► pre-execution structural validity check
   │   (optional for tag-audit-ops)   - CLI parameter existence
   │                                    - JSON structure compliance
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

**Check Categories (for tag-audit-ops):**

| Category | Check | Method |
|---|---|---|
| **CLI Parameter Existence** | Verify every `--flag` in `jdc <product>` commands exists | Compare against `references/api-sdk-usage.md` operation tables |
| **JSON Structure Compliance** | For DOPS ticket payload fields | Validate field names match DOPS API spec |

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
# 2. Filter patterns by current skill name (jdcloud-tag-audit-ops)
# 3. Inject top-3 relevant patterns into Generator context as prevention hints
```

**This is a HINT, not a CONSTRAINT** — the Generator should use these patterns to avoid known mistakes, but is not required to follow them if the context differs.

**Failure Pattern Extraction:**

When a GCL iteration fails (SAFETY_FAIL, HALLUCINATION_ABORT, or rubric dimension < threshold), the Orchestrator SHOULD extract a structured failure pattern and append it to the trace:

```json
{
  "failure_pattern": {
    "category": "cli_parameter|runtime|cross_skill",
    "skill": "jdcloud-tag-audit-ops",
    "command": "jdc --output json <product> describe-instances ...",
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
executor. The Critic (C) is a new, read-only role with no `jdc` / SDK /
DOPS access. The Orchestrator (O) owns the loop and persists the GCL
trace.
The Hallucination Detector (H) is an optional pre-execution structural check.

### Operation-specific behavior

- **`audit tag compliance`** (read-only) — Product + region + required
  tag + required value MUST be explicit. Each product/region MUST be in
  the `Supported Products` / `Supported Regions` list. For each
  resource, classify pass/fail deterministically. H layer validates product/region parameters before execution.
- **`generate audit report`** (read-only) — Output: pass count, fail
  count, fail list with resource id + missing tag + actual value.
- **`create DOPS ticket for non-compliant resources`** (mutating) —
  **MUST check for duplicate open tickets** on the same resource first.
  Each ticket payload MUST include: resource id, missing tag, actual
  value, suggested remediation, urgency level. Safety = 0 without
  `confirm=CREATE_DOPS_TICKET` in trace → ABORT. Duplicate ticket
  without opt-in → Idempotency = 0 → ABORT. H layer validates DOPS ticket payload structure before execution.

## Prerequisites

> **Python 3.10 is REQUIRED, NOT 3.12.** `jdcloud_cli==1.2.12` uses `SafeConfigParser` which was removed in Python 3.12. Always use `uv venv --python 3.10`. If Python 3.10 is unavailable, install it via `brew install python@3.10` (macOS) or `uv python install 3.10`.

```bash
# Install dependencies
uv venv --python 3.10
source .venv/bin/activate
uv pip install jdcloud_cli jdcloud_sdk
```

## Reference Directory

- [Core Concepts](references/core-concepts.md)
- [CLI Usage](references/cli-usage.md)
- [API & SDK Usage](references/api-sdk-usage.md)
- [Examples](references/examples.md)

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.6.0 | 2026-06-18 | **GCL v2 rollout**: Enhanced Quality Gate with Phase 6 Hallucination Detection Layer (H, optional) and Phase 7 Reflexion Integration. Added pre-execution structural validity check. Integrated `docs/failure-patterns.md` for cross-session failure memory. Aligned with AGENTS.md GCL v2 specification (§10-11). |
| 1.5.0 | 2026-06-04 | **GCL rollout (optional)**: Added `## Quality Gate (GCL)` chapter wiring this skill into the repository-wide Generator-Critic-Loop. Added `references/rubric.md` (5-dimension rubric, audit + report + DOPS ticket creation with duplicate-ticket idempotency check) and `references/prompt-templates.md` (G/C/O prompt skeletons). `max_iterations=5`. `safety_confirm_required=true` for `create DOPS ticket` (the only mutating op). |
| 1.4.0 | 2026-06-03 | Added Elasticsearch tag audit support |
| 1.3.0 | 2026-06-03 | Added MongoDB tag audit support |
| 1.2.0 | 2026-06-03 | Added RDS MySQL and PostgreSQL tag audit support |
| 1.1.0 | 2026-06-03 | Added CLB and EIP support |
| 1.0.0 | 2026-06-03 | Initial version with Redis, VM, RDS support |

## License

MIT License - See LICENSE file for details