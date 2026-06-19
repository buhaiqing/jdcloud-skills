---
name: jdcloud-clb-ops
description: >-
  Use this skill to manage JD Cloud Load Balancer (CLB): deploy, configure,
  troubleshoot, or monitor via API/SDK or `jdc` CLI. Trigger for CLB, 负载均衡,
  Load Balancer, SLB, or tasks involving load balancer instances, listeners,
  backend servers, target groups, health checks, or traffic distribution —
  even without explicit "CLB" mention.
license: MIT
compatibility: >-
  Official JD Cloud SDK (Python 3.10+), valid API credentials, network
  access to JD Cloud endpoints, and official JD Cloud CLI (`jdc`) when this
  product is supported by the CLI (jdc-first with SDK fallback).
metadata:
  author: buhaiqing
  version: "1.3.1"
  last_updated: "2026-06-19"
  runtime: Harness AI Agent
  api_profile: "JD Cloud CLB API v1 - https://lb.jdcloud-api.com/v1"
  cli_applicability: jdc-first-with-fallback
  cli_version_locked: "1.2.12"
  sdk_version_locked: ">=1.6.26"
  cli_support_evidence: >-
    Confirmed via `jdc` help output showing 'lb' in product list.
    Official CLI documentation: https://docs.jdcloud.com/cn/cli/introduction
  environment:
    - JDC_ACCESS_KEY
    - JDC_SECRET_KEY
    - JDC_REGION
---

> This skill follows the [Agent Skill OpenSpec](https://agentskills.io/specification).

# JD Cloud Load Balancer (CLB) Operations Skill

## Overview

JD Cloud Load Balancer (CLB/负载均衡) distributes Layer 4/7 traffic across backend servers. This skill is an operational runbook: pre-flight checks, **jdc-first execution with SDK fallback**, validation, and failure recovery. Do not use the web console as the primary path.

### Path Preference

1. `jdc` CLI first for every operation.
2. Retry up to **3 times** with backoff (0s → 2s → 4s).
3. SDK/API fallback only after 3 consecutive `jdc` failures.
4. Prefer `jdc` output when both paths succeed.

### Critical jdc CLI Behavioral Notes

- `--output json` is **top-level**: `jdc --output json lb ...` works; `jdc lb ... --output json` fails.
- `--no-interactive` does **not exist** — omit it.
- CLI credentials come **only** from `~/.jdc/config` + `~/.jdc/current`; env vars are ignored by the CLI (SDK uses env vars).
- In sandboxed environments set `export HOME=/tmp/jdc-home` and pre-create `~/.jdc/config` to avoid `PermissionError`.

See [references/cli-usage.md](references/cli-usage.md) and [references/integration.md](references/integration.md) for full setup.

## Trigger & Scope (Agent-Readable)

### SHOULD Use This Skill When

- User explicitly mentions "JD Cloud CLB", "负载均衡", "Load Balancer", "SLB", or "CLB实例"
- User wants to **deploy**, **configure**, **troubleshoot**, or **monitor** load balancers via automation
- Task involves CRUD operations: create, describe, modify, delete, or list load balancer instances
- Task involves listener management: create, modify, or delete TCP/UDP/HTTP/HTTPS listeners
- Task involves backend server management: register/deregister targets, manage target groups
- Task involves health check configuration or status verification
- Task involves traffic distribution, session persistence, or load balancing algorithms
- Keywords detected: createLoadBalancer, describeLoadBalancers, createListener, registerTargets, healthCheck, listener, backend, target
- User describes load balancing needs without naming "CLB" (e.g., "distribute traffic across my servers", "set up a VIP for my web app", "configure health checks for backend servers")

### SHOULD NOT Use This Skill When

- Task is purely billing / account management → delegate to: `jdcloud-billing-ops` (when present)
- Task is IAM / permission model only → delegate to: `jdcloud-iam-ops` (when present)
- Task is about VPC / subnet / security group configuration → delegate to: `jdcloud-vpc-ops`
- Task is about VM / ECS instance management → delegate to: `jdcloud-vm-ops`
- Task is about SSL certificate management → delegate to: `jdcloud-ssl-ops` (when present)
- Task is about monitoring metrics / alarms → delegate to: `jdcloud-cloudmonitor-ops`
- User insists on **console-only** flows with no API → state limitation; do not invent undocumented HTTP steps
- Task involves database load balancing (not CLB) → delegate to appropriate database skill

### Delegation Rules

- If CLB requires VPC/subnet resources, verify or create them via `jdcloud-vpc-ops` first.
- If CLB backend targets are VMs, verify VM instances exist via `jdcloud-vm-ops` first.
- If user asks about CLB monitoring metrics or alarm rules, delegate metric queries to `jdcloud-cloudmonitor-ops`.
- For SSL certificate installation on HTTPS listeners, coordinate with `jdcloud-ssl-ops` to get certificate IDs.
- Multi-product requests: handle each product with its dedicated skill; do not merge unrelated APIs into one ambiguous flow.

## Variable Convention (Agent-Readable)

Structured placeholders reduce injection ambiguity and unsafe prompts:

| Placeholder | Meaning | Agent Action |
|-------------|---------|--------------|
| `{{env.JDC_ACCESS_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_SECRET_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_REGION}}` | From runtime environment | Use `cn-north-1` as default if unset |
| `{{user.region}}` | User-supplied region | Ask once; reuse |
| `{{user.lb_id}}` | User-supplied load balancer ID | Ask once; reuse |
| `{{user.lb_name}}` | User-supplied load balancer name | Ask once; reuse |
| `{{user.lb_spec}}` | LB specification (`small`/`medium`/`large`) | Ask once; reuse |
| `{{user.vpc_id}}` | User-supplied VPC ID | Ask once; reuse |
| `{{user.subnet_id}}` | User-supplied subnet ID | Ask once; reuse |
| `{{user.az}}` | User-supplied availability zone | Ask once; reuse |
| `{{user.listener_id}}` | User-supplied listener ID | Ask once; reuse |
| `{{user.protocol}}` | Listener protocol (`TCP`/`UDP`/`HTTP`/`HTTPS`) | Ask once; reuse |
| `{{user.listener_port}}` | Listener frontend port | Ask once; reuse |
| `{{user.backend_port}}` | Backend port | Ask once; reuse |
| `{{user.target_group_id}}` | Target group ID | Ask once; reuse |
| `{{user.vm_id}}` | Backend VM instance ID | Ask once; reuse |
| `{{user.target_port}}` | Backend target port | Ask once; reuse |
| `{{user.weight}}` | Backend weight | Optional; default `100` |
| `{{user.backend_server_id}}` | User-supplied backend server ID | Ask once; reuse |
| `{{user.new_name}}` | New LB name for modify | Ask once; reuse |
| `{{user.new_listener_name}}` | New listener name for modify | Ask once; reuse |
| `{{user.target_ids}}` | Target IDs for deregister | Ask once; reuse |
| `{{user.hc_protocol}}` | Health check protocol | Ask once; reuse |
| `{{user.hc_port}}` | Health check port | Ask once; reuse |
| `{{user.hc_interval}}` | Health check interval (s) | Optional; default `5` |
| `{{user.hc_healthy}}` | Healthy threshold | Optional; default `2` |
| `{{user.hc_unhealthy}}` | Unhealthy threshold | Optional; default `3` |
| `{{output.lb_id}}` | From last API or CLI JSON response | Parse from `$.result.loadBalancerId` |
| `{{output.listener_id}}` | From last API or CLI JSON response | Parse from `$.result.listenerId` |

> **`{{env.*}}` MUST NOT** be collected from the user; **`{{user.*}}`** MUST be collected interactively when missing. **Security Warning:** **NEVER** log, print, or expose `JDC_SECRET_KEY` (or any secret); check existence only and use `<masked>`/`*` placeholders when logging credential status.

## API and Response Conventions

- Base path: `https://lb.jdcloud-api.com/v1/regions/{regionId}/...`
- Errors map to `code` / `status` / `message`; timestamps are ISO 8601.
- Key response paths: `$.result.loadBalancerId`, `$.result.listenerId`, `$.result.loadBalancer.status`.
- See [references/api-sdk-usage.md](references/api-sdk-usage.md) for full request/response schemas.

### Expected State Transitions

| Operation | Initial State | Target State | Poll Interval | Max Wait |
|-----------|---------------|--------------|---------------|----------|
| Create LB | — | `active` | 10s | 300s |
| Create Listener | — | `active` | 10s | 120s |
| Modify LB | `active` | `active` | 10s | 120s |
| Delete LB | `active`/`inactive` | (404 on describe) | 10s | 300s |
| Register Targets | — | `healthy`/`unhealthy` | 10s | 120s |

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.3.1 | 2026-06-19 | Slimmed SKILL.md to ≤500 lines; unified `create-listener` params; completed Variable Convention; added listener/target/health-check execution flows; fixed `rubric_version` to `v2`. |
| 1.3.0 | 2026-06-18 | GCL v2 rollout: H layer + Reflexion; aligned with AGENTS.md §10-11. |
| 1.2.0 | 2026-06-18 | Initial GCL v2 H/Reflexion sections. |
| 1.1.0 | 2026-06-04 | GCL rollout; added `references/rubric.md` + `references/prompt-templates.md`; `max_iterations=3`. |
| 1.0.0 | 2026-05-06 | Initial jdc-first + SDK fallback SKILL.md. |

## Execution Flows

### Operation: Create Load Balancer

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| CLI / SDK deps | `jdc --version`, import `LbClient` | Exit code 0, no import error | Retry / install; fallback to SDK |
| Credentials | Env or `~/.jdc/config` | Non-empty keys | HALT; configure credentials |
| Region | `describeLoadBalancers` small page | `{{user.region}}` valid | Suggest valid region |
| VPC/Subnet/AZ | Delegate `jdcloud-vpc-ops` | Subnet exists, AZ valid | HALT; fix VPC/subnet first |

#### Execution — CLI (`jdc`) [Primary Path]

```bash
jdc --output json lb create-load-balancer \
  --region-id "{{user.region}}" \
  --load-balancer-name "{{user.lb_name}}" \
  --vpc-id "{{user.vpc_id}}" \
  --subnet-id "{{user.subnet_id}}" \
  --azs '["{{user.az}}"]' \
  --load-balancer-spec "{{user.lb_spec|default:"small"}}"
```

#### Post-execution Validation

1. Capture `{{output.lb_id}}` from `$.result.loadBalancerId`.
2. Poll `describeLoadBalancer` until `status` == `active` or timeout.

```bash
# CLI poll loop (primary path) — --output json at TOP level
for i in $(seq 1 30); do
  STATUS=$(jdc --output json lb describe-load-balancer \
    --region-id "{{user.region}}" \
    --load-balancer-id "{{output.lb_id}}" | jq -r '.result.loadBalancer.status')
  [ "$STATUS" = "active" ] && break
  sleep 10
done
```

```python
# SDK poll loop (fallback, after 3 jdc failures)
from jdcloud_sdk.services.lb.apis.DescribeLoadBalancerRequest import DescribeLoadBalancerRequest, DescribeLoadBalancerParameters

for _ in range(30):
    dparams = DescribeLoadBalancerParameters(regionId="{{user.region}}", loadBalancerId="{{output.lb_id}}")
    dreq = DescribeLoadBalancerRequest(parameters=dparams)
    dresp = client.send(dreq)
    status = dresp.result["loadBalancer"]["status"]
    if status == "active":
        break
    if status in ["error", "deleted"]:
        raise RuntimeError(f"LB creation failed: {status}")
    sleep(10)
```

1. On success, report LB ID, VIP address, and DNS name to user.
2. On terminal failure, go to **Failure Recovery**.

#### Failure Recovery

| Error pattern | Retries | Agent Action |
|---|---|---|
| `InvalidParameter` / 400 | 0–1 | Fix args; retry once |
| `QuotaExceeded`, `InsufficientBalance`, `SubnetIpInsufficient` | 0 | HALT; user resolves |
| `ResourceAlreadyExists` | 0 | Ask reuse vs new name |
| Throttling / 429, `InternalError` / 5xx | 3 | Back off (2s, 4s, 8s); HALT with `requestId` if persists |

### Operation: Describe Load Balancer

#### Execution (CLI) [Primary Path]

```bash
jdc --output json lb describe-load-balancer \
  --region-id "{{user.region}}" \
  --load-balancer-id "{{user.lb_id}}"
```

### Operation: List Load Balancers

#### Execution (CLI) [Primary Path]

```bash
jdc --output json lb describe-load-balancers \
  --region-id "{{user.region}}" \
  --page-number 1 \
  --page-size 100
```

### Operation: Create Listener

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| LB exists/state | `describeLoadBalancer` | LB found and `active` | HALT; verify LB ID |
| Protocol/port | User input | valid protocol, 1-65535 | Validate and reject invalid input |

#### Execution (CLI) [Primary Path]

```bash
jdc --output json lb create-listener \
  --region-id "{{user.region}}" \
  --load-balancer-id "{{user.lb_id}}" \
  --protocol "{{user.protocol}}" \
  --port {{user.listener_port}} \
  --backend-port {{user.backend_port}}
```

#### Post-execution Validation

Poll `describe-listeners` until listener is `active`.

### Operation: Describe Listener(s)

#### Execution (CLI) [Primary Path]

```bash
jdc --output json lb describe-listeners \
  --region-id "{{user.region}}" \
  --load-balancer-id "{{user.lb_id}}"
```

### Operation: Modify Listener

#### Pre-flight Checks

- Verify LB and listener exist (`describeLoadBalancer`, `describeListeners`).

#### Execution (CLI) [Primary Path]

```bash
jdc --output json lb modify-listener \
  --region-id "{{user.region}}" \
  --load-balancer-id "{{user.lb_id}}" \
  --listener-id "{{user.listener_id}}" \
  --listener-name "{{user.new_listener_name}}"
```

#### Post-execution Validation

Poll `describe-listeners` until name reflects.

### Operation: Delete Listener

#### Pre-flight (Safety Gate)

- **MUST** obtain explicit confirmation: irreversible delete of listener `{{user.listener_id}}`.
- **MUST** warn user that traffic on this listener/port will be dropped.

#### Execution (CLI) [Primary Path]

```bash
jdc --output json lb delete-listener \
  --region-id "{{user.region}}" \
  --load-balancer-id "{{user.lb_id}}" \
  --listener-id "{{user.listener_id}}"
```

#### Post-execution Validation

Poll `describe-listeners` until listener absent (max 120s).

### Operation: Register Targets (Backend Servers)

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| LB exists | `describeLoadBalancer` | LB found | HALT; verify LB ID |
| Targets valid | `jdcloud-vm-ops` + user input | VMs found, ports 1-65535 | HALT; verify targets |

#### Execution (CLI) [Primary Path]

```bash
jdc --output json lb register-targets \
  --region-id "{{user.region}}" \
  --load-balancer-id "{{user.lb_id}}" \
  --target-group-id "{{user.target_group_id}}" \
  --target-specs '[{"instanceId":"{{user.vm_id}}","port":{{user.target_port}},"weight":{{user.weight|default:100}}}]'
```

#### Post-execution Validation

Poll `describe-targets` until `healthStatus` is `healthy` or timeout.

### Operation: Describe Targets

#### Execution (CLI) [Primary Path]

```bash
jdc --output json lb describe-targets \
  --region-id "{{user.region}}" \
  --load-balancer-id "{{user.lb_id}}" \
  --target-group-id "{{user.target_group_id}}"
```

#### Post-execution Validation

Verify `$.result.targets[*].targetId`, `instanceId`, `healthStatus`.

### Operation: Deregister Targets

#### Pre-flight (Safety Gate)

- Calculate % of total targets being removed:
  - > 50% → `confirm=DRAIN` required
  - > 80% → `confirm=DRAIN_ALL` required
- **MUST** warn user about capacity reduction.

#### Execution (CLI) [Primary Path]

```bash
jdc --output json lb deregister-targets \
  --region-id "{{user.region}}" \
  --load-balancer-id "{{user.lb_id}}" \
  --target-group-id "{{user.target_group_id}}" \
  --target-ids '["{{user.target_ids}}"]'
```

#### Post-execution Validation

Poll `describe-targets` until target IDs absent or health status updated (max 120s).

### Operation: Modify Load Balancer

#### Pre-flight Checks

- Verify LB exists and is `active`; confirm with user for production LBs (may cause brief interruption).

#### Execution (CLI) [Primary Path]

```bash
jdc --output json lb modify-load-balancer \
  --region-id "{{user.region}}" \
  --load-balancer-id "{{user.lb_id}}" \
  --load-balancer-name "{{user.new_name}}"
```

#### Post-execution Validation

Poll `describe-load-balancer` until modification reflects.

### Operation: Delete Load Balancer

#### Pre-flight (Safety Gate)

- **MUST** obtain explicit confirmation: irreversible delete of `{{user.lb_name}}` (`{{user.lb_id}}`) with listeners/targets noted.
- **MUST NOT** proceed without clear user assent.

#### Execution (CLI) [Primary Path]

```bash
jdc --output json lb delete-load-balancer \
  --region-id "{{user.region}}" \
  --load-balancer-id "{{user.lb_id}}"
```

#### Post-execution Validation

Poll `describe-load-balancer` until 404 or max wait (300s).

```bash
for i in $(seq 1 30); do
  jdc --output json lb describe-load-balancer \
    --region-id "{{user.region}}" \
    --load-balancer-id "{{user.lb_id}}" 2>&1 | grep -q "NotFound" && break
  sleep 10
done
```

### Operation: Describe Health Check

#### Execution (CLI) [Primary Path]

```bash
jdc --output json lb describe-health-check \
  --region-id "{{user.region}}" \
  --load-balancer-id "{{user.lb_id}}" \
  --listener-id "{{user.listener_id}}"
```

### Operation: Health Check Management

#### Execution (CLI) [Primary Path]

```bash
jdc --output json lb update-health-check \
  --region-id "{{user.region}}" \
  --load-balancer-id "{{user.lb_id}}" \
  --listener-id "{{user.listener_id}}" \
  --health-check-spec '{"protocol":"{{user.hc_protocol}}","port":{{user.hc_port}},"interval":{{user.hc_interval|default:5}},"healthyThreshold":{{user.hc_healthy|default:2}},"unhealthyThreshold":{{user.hc_unhealthy|default:3}}}'
```

## Quality Gate (GCL)

This skill participates in the repository-wide GCL ([`AGENTS.md` §Quality Gate](../AGENTS.md#generator-critic-loop-gcl--adversarial-quality-gate)). Loop: Pre-flight → Generate → Hallucination Check → Execute → Critic → Decide (max 3 iterations).

### Parameters

| Parameter | Value | Reason |
|---|---|---|
| `max_iterations` | **3** | `AGENTS.md` §8 default for `jdcloud-clb-ops` (recommended) |
| `rubric_version` | `v2` | see [references/rubric.md](references/rubric.md) |
| `trace_path` | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | unified with `jdcloud-audit-ops` |
| `safety_confirm_required` | **true** for `delete-lb`, `deregister-targets` (>50%) | repository safety gate policy |
| `hallucination_check` | **recommended** | Phase 6 H layer: validate CLI params before execution |
| `reflexion_integration` | **enabled** | Phase 7: load `docs/failure-patterns.md` |

### Hallucination Detection (H)

| Category | Check | Method |
|---|---|---|
| CLI Parameter Existence | Every `--flag` exists for `jdc lb <operation>` | Compare against `references/api-sdk-usage.md` |
| JSON Structure Compliance | JSON payloads match OpenAPI schema | `--target-specs`, `--health-check-spec`, etc. |

**Key parameters to validate:**

| Operation | Critical Parameters |
|---|---|
| `create-load-balancer` | `--load-balancer-name`, `--vpc-id`, `--subnet-id`, `--azs`, `--load-balancer-spec` |
| `create-listener` | `--load-balancer-id`, `--protocol`, `--port`, `--backend-port` |
| `register-targets` | `--load-balancer-id`, `--target-group-id`, `--target-specs` |
| `deregister-targets` | `--load-balancer-id`, `--target-group-id`, `--target-ids` |
| `update-health-check` | `--load-balancer-id`, `--listener-id`, `--health-check-spec` |

### Operation-specific safety rules

- `create-lb`: type + AZ explicit; check quota first.
- `create-listener`: protocol/port valid; default action set.
- `register-targets`: backend must be `running`; refuse `stopped`/`error` without opt-in.
- `deregister-targets`: >50% needs `confirm=DRAIN`; >80% needs `confirm=DRAIN_ALL`.
- `modify-lb`: bandwidth shrink forbidden without opt-in.
- `delete-lb`: cuts all traffic; needs `confirm=DELETE` (prod LB needs `confirm=DELETE_PROD`) plus pre-delete snapshot.
- `health-check`: disabling without opt-in is refused.

### Artifacts

- Rubric: [references/rubric.md](references/rubric.md)
- Prompt templates: [references/prompt-templates.md](references/prompt-templates.md)
- Failure patterns: [docs/failure-patterns.md](docs/failure-patterns.md)

## Prerequisites

Python 3.10, `uv`, and JD Cloud credentials are required. See [references/integration.md](references/integration.md) for environment setup, SDK/CLI install, and credential configuration.
