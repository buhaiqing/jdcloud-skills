---
name: jdcloud-clb-ops
description: >-
  Use when you need to deploy, configure, troubleshoot, or monitor JD Cloud
  Load Balancer (ALB/NLB/DNLB) via official API/SDK; user mentions
  Load Balancer, 负载均衡, ALB, NLB, DNLB, or tasks target load balancer
  instances, listeners, backend services, or target groups.
license: MIT
compatibility: >-
  Official JD Cloud SDK (Python 3.10+), valid API credentials, network
  access to JD Cloud endpoints. Note: Official JD Cloud CLI (jdc) does NOT
  support Load Balancer products at this time — SDK/API-only.
metadata:
  author: jdcloud
  version: "1.0.1"
  last_updated: "2026-05-03"
  runtime: Harness AI Agent
  api_profile: "Application Load Balancer API v1 / Network Load Balancer API v1"
  cli_applicability: sdk-only
  cli_support_evidence: >-
    Official JD Cloud CLI product list from `jdc --help` shows: mps, cps, rds,
    jke, vpc, xdata, mongodb, redis, nc, monitor, iam, disk, cr, vm, oss, etc.
    No alb, nlb, lb, or loadbalancer commands are present. Verified against
    official CLI documentation at https://docs.jdcloud.com/cn/cli/introduction
    and GitHub repository https://github.com/jdcloud-api/jdcloud-cli.
  environment:
    - JDC_ACCESS_KEY
    - JDC_SECRET_KEY
    - JDC_REGION
---

> This skill follows the [Agent Skill OpenSpec](https://agentskills.io/specification).

# JD Cloud Load Balancer (CLB) Operations Skill

## Overview

JD Cloud Load Balancer provides traffic distribution services across multiple backend servers, ensuring high availability and scalability for cloud applications. This skill covers three load balancer types:

- **Application Load Balancer (ALB)**: Seven-layer (L7) load balancing for HTTP/HTTPS traffic, supporting domain/URL-based routing, SSL certificates, and redirect features.
- **Network Load Balancer (NLB)**: Four-layer (L4) load balancing for TCP/UDP traffic, supporting source IP transparency and session persistence.
- **Distributed Network Load Balancer (DNLB)**: Four-layer stateless load balancing (free tier), designed for ultra-high concurrency scenarios.

This skill is an **operational runbook** for agents: explicit scope, credential rules, pre-flight checks, SDK/API execution paths, response validation, and failure recovery.

### CLI Applicability (Repository Policy)

- **`cli_applicability: sdk-only`:** Official JD Cloud CLI (`jdc`) does **not** expose Load Balancer products (ALB/NLB/DNLB). This skill operates **exclusively** via official JD Cloud SDK/API. The `references/cli-usage.md` file is omitted per governance policy.
- **Evidence:** `jdc --help` output lists supported products: `{mps,cps,rds,jke,vpc,xdata,mongodb,redis,nc,monitor,iam,disk,cr,vm,oss,...}` with no LB-related commands. Official CLI docs confirm this at https://docs.jdcloud.com/cn/cli/introduction.

## Trigger & Scope (Agent-Readable)

### SHOULD Use This Skill When

- User mentions "JD Cloud Load Balancer" OR "负载均衡" OR "ALB" OR "NLB" OR "DNLB"
- Task involves CRUD or lifecycle operations on **load balancer instances** (create, describe, modify, delete, list)
- Task involves **listeners** (create, configure, delete, manage SSL certificates)
- Task involves **backend services** and **target groups** (register/deregister servers, health checks)
- Task keywords: createLoadBalancer, describeLoadBalancers, createListener, registerTargets, ssl证书, 监听器, 后端服务
- User asks to deploy, configure, troubleshoot, or monitor Load Balancer **via API, SDK, or automation**

### SHOULD NOT Use This Skill When

- Task is purely billing / account management → delegate to: `jdcloud-billing-ops` (when present)
- Task is IAM / permission model only → delegate to: `jdcloud-iam-ops` (when present)
- Task is about **VPC / subnet** creation → delegate to: `jdcloud-vpc-ops`
- Task is about **VM instance** creation → delegate to: `jdcloud-vm-ops`
- Task is about **SSL certificate** issuance/purchase (not LB binding) → delegate to: `ssl-certificate` skill
- User insists on **console-only** flows with no API → state limitation; do not invent undocumented HTTP steps

### Delegation Rules

- If load balancer depends on VPC/subnet, verify VPC existence via `jdcloud-vpc-ops` before creating LB.
- If backend servers are VMs, verify VM status via `jdcloud-vm-ops` before registering targets.
- Multi-product requests: handle each product with its skill; do not merge unrelated APIs into one ambiguous flow.

## Variable Convention (Agent-Readable)

Structured placeholders reduce injection ambiguity and unsafe prompts:

| Placeholder | Meaning | Agent Action |
|-------------|---------|--------------|
| `{{env.JDC_ACCESS_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_SECRET_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_REGION}}` | From runtime environment | Use documented default only if skill explicitly allows |
| `{{user.region}}` | User-supplied region | Ask once; reuse |
| `{{user.loadbalancer_name}}` | User-supplied LB name | Ask once; reuse |
| `{{user.loadbalancer_id}}` | User-supplied LB ID | Ask once; reuse |
| `{{output.loadbalancer_id}}` | From last API JSON response | Parse per OpenAPI response schema for this operation |

> **`{{env.*}}` MUST NOT** be collected from the user. **`{{user.*}}`** MUST be collected interactively when missing.

## API and Response Conventions (Agent-Readable)

- **OpenAPI is canonical** for path, query, body fields, enums, and response shapes.
- **Errors:** Map SDK/HTTP errors to `code` / `status` / message fields per spec.
- **Timestamps:** ISO 8601 with timezone when the API returns strings (e.g. `2026-05-03T10:00:00+08:00`).
- **Idempotency:** Document duplicate name behavior per API — ALB/NLB names must be unique within region.

### Response Field Table (OpenAPI-Accurate Paths)

| Operation | JSON Path | Type | Description |
|-----------|-----------|------|-------------|
| Create LB | `$.result.loadBalancerId` | string | New load balancer ID |
| Describe LB | `$.result.loadBalancer.status` | string | Lifecycle state (active, creating, deleting) |
| List LBs | `$.result.loadBalancers[*].loadBalancerId` | array | IDs |
| Create Listener | `$.result.listenerId` | string | New listener ID |
| Register Targets | `$.requestId` | string | Non-empty means accepted |

### Expected State Transitions

| Operation | Initial State | Target State | Poll Interval | Max Wait |
|-----------|---------------|--------------|---------------|----------|
| Create LB | — | `active` | 5s | 300s |
| Create Listener | — | `active` | 5s | 120s |
| Delete LB | any stable | absent (404 on describe) | 5s | 300s |
| Delete Listener | `active` | absent | 5s | 60s |

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-05-03 | Initial SDK-only skill for ALB/NLB/DNLB; CLI omitted per governance (CLI does not support LB products) |
| 1.0.1 | 2026-05-03 | Added idempotency-checklist.md; expanded governance Scenario H for production LB rule mutation |

## Execution Flows (Agent-Readable)

Every operation: **Pre-flight → Execute (SDK/API) → Validate → Recover**. Do not skip phases.

### Operation: Create Load Balancer (ALB/NLB)

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| SDK / deps | Import `jdcloud_sdk.services.alb.client` | No import error | Document install pin in integration.md |
| Credentials | Construct credential from env | Non-empty keys | HALT; user configures env |
| Region | Call describeRegions if available | `{{user.region}}` supported | Suggest valid region |
| VPC exists | `describeVpc` via jdcloud-vpc-ops | VPC found | HALT; user creates VPC first |
| Quota | Check LB count via describeLoadBalancers | Within limit | HALT; user raises quota |

#### Execution (Python SDK — ALB Example)

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.alb.client import AlbClient
from jdcloud_sdk.services.alb.apis.CreateLoadBalancerRequest import CreateLoadBalancerRequest, CreateLoadBalancerSpec

credential = Credential(os.environ["JDC_ACCESS_KEY"], os.environ["JDC_SECRET_KEY"])
client = AlbClient(credential, os.environ.get("JDC_REGION", "cn-north-1"))

spec = CreateLoadBalancerSpec(
    name="{{user.loadbalancer_name}}",
    vpcId="{{user.vpc_id}}",
    type="application",  # or "network" for NLB
    chargeMode="postpaid_by_usage",
    # additional fields per OpenAPI: azs, subnetMappings, etc.
)
req = CreateLoadBalancerRequest(regionId="{{user.region}}", spec=spec)
resp = client.createLoadBalancer(req)
```

#### Post-execution Validation

1. Read `{{output.loadbalancer_id}}` from `$.result.loadBalancerId`.
2. Poll **describeLoadBalancer** until terminal success state (`active`) or timeout.

```python
# Pseudocode: use real describe request
for _ in range(max_attempts):
    dresp = client.describeLoadBalancer(describe_request)
    status = dresp.result.loadBalancer.status
    if status == "active":
        break
    if status in ("error", "failed"):
        raise RuntimeError(dresp.result.loadBalancer.errorMsg)
    sleep(poll_interval_seconds)
```

3. On success, report `{{output.loadbalancer_id}}` and VIP/EIP to user.
4. On terminal failure, go to **Failure Recovery**.

#### Failure Recovery

| Error pattern | Max retries | Backoff | Agent Action |
|---------------|-------------|---------|--------------|
| `InvalidParameter` / 400 | 0–1 | — | Fix args from OpenAPI; retry once if safe |
| `QuotaExceeded` | 0 | — | HALT |
| `InsufficientBalance` | 0 | — | HALT |
| `NameAlreadyExists` | 0 | — | Ask new name |
| Throttling / 429 | 3 | exponential | Back off; respect Retry-After |
| `InternalError` / 5xx | 3 | 2s, 4s, 8s | Retry; then HALT with requestId |

### Operation: Describe Load Balancer

#### Execution

Use SDK **describeLoadBalancer** or **describeLoadBalancers** matching OpenAPI.

```python
req = DescribeLoadBalancerRequest(regionId="{{user.region}}", loadBalancerId="{{user.loadbalancer_id}}")
resp = client.describeLoadBalancer(req)
```

#### Present to User

| Field | Path | Notes |
|-------|------|-------|
| ID | `$.result.loadBalancer.loadBalancerId` | Plain text |
| Name | `$.result.loadBalancer.name` | Plain text |
| Status | `$.result.loadBalancer.status` | Human-readable |
| VIP | `$.result.loadBalancer.vip` | IP address |
| EIP | `$.result.loadBalancer.eip` | Elastic IP if bound |

### Operation: Create Listener

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| LB exists | describeLoadBalancer | `active` status | HALT; create/wait for LB first |
| Protocol valid | Per LB type (ALB: HTTP/HTTPS; NLB: TCP/UDP) | Supported protocol | Suggest valid protocol |
| Port available | Check existing listeners | Port not in use | Suggest alternative port |

#### Execution (Python SDK — HTTPS Listener)

```python
from jdcloud_sdk.services.alb.apis.CreateListenerRequest import CreateListenerRequest, CreateListenerSpec

spec = CreateListenerSpec(
    protocol="https",
    port=443,
    loadBalancerId="{{output.loadbalancer_id}}",
    certificateSpec={"certificateId": "{{user.certificate_id}}"},
    # additional fields: tlsPolicy, connectionIdleTimeout, etc.
)
req = CreateListenerRequest(regionId="{{user.region}}", spec=spec)
resp = client.createListener(req)
```

#### Post-execution Validation

1. Capture `{{output.listener_id}}` from `$.result.listenerId`.
2. Poll describeListener until `active` status.
3. Report listener ID and bound certificate to user.

### Operation: Register Targets (Backend Servers)

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| Target group exists | describeTargetGroup | Found | Create target group first |
| Backend VM/IP reachable | Ping/describe VM | VM running | HALT; fix backend server |
| Port valid | 1-65535 | Valid range | Fix port |

#### Execution (Python SDK)

```python
from jdcloud_sdk.services.alb.apis.RegisterTargetsRequest import RegisterTargetsRequest, TargetSpec

targets = [
    TargetSpec(targetId="{{user.vm_id_1}}", port=80, weight=10),
    TargetSpec(targetId="{{user.vm_id_2}}", port=80, weight=10),
]
req = RegisterTargetsRequest(
    regionId="{{user.region}}",
    targetGroupId="{{user.target_group_id}}",
    targets=targets
)
resp = client.registerTargets(req)
```

#### Post-execution Validation

1. Call describeTargetHealth to verify backend health status.
2. Report registered targets and health check results.

### Operation: Delete Load Balancer

#### Pre-flight (Safety Gate)

- **MUST** obtain explicit confirmation: irreversible delete of `{{user.loadbalancer_name}}` (`{{user.loadbalancer_id}}`).
- **MUST NOT** proceed without clear user assent.

#### Execution

```python
req = DeleteLoadBalancerRequest(regionId="{{user.region}}", loadBalancerId="{{user.loadbalancer_id}}")
resp = client.deleteLoadBalancer(req)
```

#### Post-execution Validation

Poll describeLoadBalancer until **404**, **NotFound**, or status indicates deleted — within max wait (300s).

## Prerequisites

1. **Install** the JD Cloud SDK package(s):
   ```bash
   pip install jdcloud-sdk
   ```

2. **Configure Credentials** — Three methods:

   **Method 1: `.env` File (Recommended for Local Development)**
   ```ini
   JDC_ACCESS_KEY=your_access_key_here
   JDC_SECRET_KEY=your_secret_key_here
   JDC_REGION=cn-north-1
   ```
   > Agent Runtime auto-loads `.env` if present.

   **Method 2: Shell Environment Variables (Production)**
   ```bash
   export JDC_ACCESS_KEY="{{env.JDC_ACCESS_KEY}}"
   export JDC_SECRET_KEY="{{env.JDC_SECRET_KEY}}"
   export JDC_REGION="cn-north-1"
   ```

   **Method 3: CLI Interactive Config**
   ```bash
   jdc config init
   ```

   > Security: Never commit `.env` files to version control.

## Reference Directory

- [Core Concepts](references/core-concepts.md)
- [API & SDK Usage](references/api-sdk-usage.md)
- [Idempotency Checklist](references/idempotency-checklist.md)
- [Troubleshooting Guide](references/troubleshooting.md)
- [Monitoring & Alerts](references/monitoring.md)
- [Integration](references/integration.md)
- [SSL Certificate Management](references/ssl-certificate-management.md)

> Note: `references/cli-usage.md` is omitted because JD Cloud CLI does not support Load Balancer products.

## Operational Best Practices

- **High Availability:** Deploy load balancers across multiple availability zones.
- **Security:** Bind appropriate SSL certificates for HTTPS listeners; enable TLS 1.2+ policies.
- **Health Checks:** Configure appropriate health check intervals and thresholds for backend services.
- **Cost Optimization:** Use DNLB (free tier) for appropriate high-concurrency stateless scenarios.
- **Resource Tagging:** Tag load balancer resources for better organization and cost tracking.