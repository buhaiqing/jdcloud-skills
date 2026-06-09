---
name: jdcloud-waf-ops
description: >-
  Use when managing JD Cloud Web Application Firewall (WAF) resources — create
  and manage WAF instances, configure domain protection, set up security rules
  (ACL, rate limiting, bot management), manage SSL certificates, and analyze
  attack logs. Works with "WAF", "Web应用防火墙", "应用防火墙", "网站防护",
  "CC防护", "SQL注入防护" without saying "JD Cloud" explicitly. NOT for
  DDoS high-vice protection (Anti-DDoS), cloud firewall (CFW), or general
  network ACLs.
license: MIT
compatibility: >-
  Official JD Cloud SDK (Python 3.10+), valid API credentials, network
  access to JD Cloud endpoints, and official JD Cloud CLI (`jdc`) with
  WAF operations support.
metadata:
  author: buhaiqing
  version: "1.0.0"
  last_updated: "2026-06-08"
  runtime: Harness AI Agent
  api_profile: "WAF API v1.0 - https://docs.jdcloud.com/cn/waf/api"
  cli_applicability: dual-path
  cli_version_locked: "1.2.12"
  sdk_version_locked: ">=1.6.26"
  cli_support_evidence: >-
    Official `jdc` CLI supports WAF operations. Verified via `jdc waf --help`
    which shows commands for instance, domain, rule management. Documentation
    at https://docs.jdcloud.com/cn/waf/introduction
  environment:
    - JDC_ACCESS_KEY
    - JDC_SECRET_KEY
    - JDC_REGION
---

> This skill follows the [Agent Skill OpenSpec](https://agentskills.io/specification).

# JD Cloud WAF Operations Skill

## Overview
JD Cloud Web Application Firewall (WAF) protects web applications from common web exploits, OWASP Top 10 vulnerabilities, malicious bots, and DDoS attacks at the application layer. WAF sits between users and your web servers, inspecting HTTP/HTTPS traffic and blocking malicious requests.

This skill covers:
- **WAF Instance Management**: Create, configure, and delete WAF instances
- **Domain Protection**: Add/remove protected domains, configure CNAME
- **Security Rules**: Custom rules, rate limiting, geographic blocking
- **Bot Management**: Bot detection, human verification, threat intelligence
- **SSL/TLS**: Certificate management, HTTPS configuration
- **Monitoring & Logs**: Attack logs, access logs, security reports

### CLI applicability (repository policy)

- **`cli_applicability: dual-path`:** Official `jdc` CLI supports WAF operations. The Agent MUST attempt to use `jdc` as the **primary execution path**. If `jdc` installation or command execution fails, the Agent MUST retry up to **3 times** (with exponential backoff). Only after **3 consecutive failures** should the Agent fall back to **SDK/API**. Both paths MUST be documented.
- **Path Preference:** Follow **jdc-first with SDK fallback** strategy. See [CLI Usage](references/cli-usage.md) for detailed comparison.

## Trigger & Scope (Agent-Readable)

### SHOULD Use This Skill When
- User mentions "WAF" OR "Web应用防火墙" OR "应用防火墙" OR "网站防护"
- Task involves protecting web applications from attacks
- Task keywords: SQL注入防护, XSS防护, CC攻击防护, 恶意爬虫防护, 网站防篡改
- Task involves configuring domain protection, security rules, rate limiting
- Task involves WAF instance management, SSL certificates on WAF
- Task involves analyzing WAF logs, attack reports, security events

### SHOULD NOT Use This Skill When
- Task is about DDoS protection at network layer (L3/L4) → delegate to: `jdcloud-antiddos-ops` (when available)
- Task is about cloud firewall (VPC-level access control) → delegate to: `jdcloud-cfw-ops` (when available)
- Task is about security group / network ACL → delegate to: `jdcloud-vpc-ops`
- Task is about load balancer configuration → delegate to: `jdcloud-clb-ops`
- Task is about SSL certificate management (general) → delegate to: `jdcloud-ssl-ops` (when available)
- Task is about API Gateway security → delegate to: `jdcloud-apigateway-ops`

### Delegation Rules
- If user wants WAF protection for domains behind CLB, configure CLB first via `jdcloud-clb-ops`, then add WAF protection
- If user wants SSL on WAF, obtain certificate first (via `jdcloud-ssl-ops` or external CA), then configure on WAF
- If user wants complete web security stack: DNS → CDN → WAF → CLB → VM (coordinate across skills)

## Variable Convention (Agent-Readable)

Structured placeholders reduce injection ambiguity and unsafe prompts:

| Placeholder | Meaning | Agent Action |
|-------------|---------|--------------|
| `{{env.JDC_ACCESS_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_SECRET_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_REGION}}` | From runtime environment | Use `cn-north-1` as default if unset |
| `{{user.region}}` | User-supplied region | Ask once; reuse |
| `{{user.waf_instance_id}}` | WAF instance ID | Ask or parse from output |
| `{{user.waf_instance_name}}` | WAF instance name | Ask once; reuse |
| `{{user.domain}}` | Protected domain name | Ask once; reuse |
| `{{user.domain_id}}` | Domain configuration ID in WAF | Parse from output |
| `{{user.rule_id}}` | Security rule ID | Parse from output |
| `{{output.waf_instance_id}}` | Created WAF instance ID | Parse from response |
| `{{output.domain_id}}` | Added domain ID | Parse from response |
| `{{output.cname}}` | WAF CNAME for DNS | Parse from response |

> **`{{env.*}}` MUST NOT** be collected from the user. **`{{user.*}}`** MUST be collected interactively when missing.

> **Security Warning:** **NEVER** log, print, or expose `JDC_SECRET_KEY` (or any secret) in console output, debug messages, or logs. When verification is needed, check existence only (e.g., `if os.environ.get('JDC_SECRET_KEY')`) without printing the actual value. If logging credential status is required, use masked placeholders like `JDC_SECRET_KEY=<masked>` or `JDC_SECRET_KEY=***`.

## API and Response Conventions (Agent-Readable)

### Mandatory CLI Conventions
- All CLI commands MUST place `--output json` BEFORE the subcommand: `jdc --output json waf <command> ...`
- `--no-interactive` does NOT exist in `jdc` CLI — all commands are non-interactive by default; omit this flag.
- Credentials: CLI reads from `~/.jdc/config` INI only (NOT from env vars). SDK uses env vars.

### Key JSON Paths

| Operation | CLI JSON Path | SDK JSON Path | Type | Description |
|-----------|---------------|---------------|------|-------------|
| Create Instance | `$.result.instanceId` | `$.result.instanceId` | string | WAF instance ID |
| Describe Instance | `$.result.instance.status` | `$.result.instance.status` | string | `running`, `stopped`, etc. |
| Add Domain | `$.result.domainId` | `$.result.domainId` | string | Domain config ID |
| Describe Domain | `$.result.domain.cname` | `$.result.domain.cname` | string | WAF CNAME for DNS |
| List Domains | `$.result.domains[*].domain` | `$.result.domains[*].domain` | array | Protected domains |
| Create Rule | `$.result.ruleId` | `$.result.ruleId` | string | Security rule ID |
| Describe Rule | `$.result.rule.status` | `$.result.rule.status` | string | `enabled` or `disabled` |

### WAF Instance Status Values
- `creating` — Instance being provisioned
- `running` — Active and protecting domains
- `updating` — Configuration changes in progress
- `stopped` — Instance stopped (protection paused)
- `expired` — Subscription expired

### Domain Protection Status
- `configuring` — DNS/CNAME setup pending
- `active` — Domain actively protected
- `paused` — Protection temporarily disabled
- `error` — Configuration error

### Expected State Transitions

| Operation | Initial State | Target State | Poll Interval | Max Wait |
|-----------|---------------|--------------|---------------|----------|
| Create Instance | — | `running` | 10s | 600s |
| Add Domain | — | `active` | 5s | 300s |
| Enable Protection | `paused` | `active` | 5s | 60s |
| Create Rule | — | `enabled` | 5s | 30s |
| Delete Domain | any | absent | 5s | 60s |
| Delete Instance | any | absent | 10s | 120s |

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-06-08 | Initial dual-path skill for JD Cloud WAF |

## Execution Flows (Agent-Readable)

Every operation: **Pre-flight → Execute (jdc primary / SDK fallback) → Validate → Recover**.

### Operation: Create WAF Instance

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| SDK / deps | Import client | No import error | Document install |
| CLI / deps | `jdc --version` | Exit code 0 | Document CLI install |
| Credentials | Valid credentials | Auth success | HALT; configure credentials |
| Region | Check WAF availability | Region supported | Suggest valid regions |
| Package | Verify WAF package SKU | SKU available | List available packages |
| Quota | Check WAF instance quota | Sufficient quota | HALT; request increase |

#### Execution — CLI (Primary Path)

```bash
# Create WAF instance
jdc --output json waf create-instance \
  --region-id "{{user.region}}" \
  --instance-spec '{"name":"{{user.waf_instance_name}}","packageCode":"waf.basic","buyType":1,"timeSpan":1,"timeUnit":"month"}'
```

#### Execution — SDK (Fallback Path)

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.waf.client import WafClient
from jdcloud_sdk.services.waf.apis.create_instance_request import CreateInstanceRequest

credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"]
)
client = WafClient(credential, os.environ.get("JDC_REGION", "cn-north-1"))

req = CreateInstanceRequest(
    regionId="{{user.region}}",
    instanceSpec={
        "name": "{{user.waf_instance_name}}",
        "packageCode": "waf.basic",  # or waf.advanced, waf.enterprise
        "buyType": 1,  # 1: subscription, 2: pay-as-you-go
        "timeSpan": 1,
        "timeUnit": "month"
    }
)
resp = client.createInstance(req)
print(f"WAF instance created: {resp.result.instanceId}")
```

#### Post-execution Validation

1. Parse `{{output.waf_instance_id}}` from response
2. Poll **DescribeInstance** until status is `running`:
   ```bash
   for i in $(seq 1 60); do
     STATUS=$(jdc --output json waf describe-instance \
       --region-id "{{user.region}}" \
       --instance-id "{{output.waf_instance_id}}" | jq -r '.result.instance.status')
     [ "$STATUS" = "running" ] && break
     sleep 10
   done
   ```
3. Report instance ID, status, and CNAME domain to user

#### Failure Recovery

| Error pattern | Max retries | Backoff | Agent Action |
|---------------|-------------|---------|--------------|
| `InvalidParameter` / 400 | 0–1 | — | Fix parameters; retry |
| `QuotaExceeded` | 0 | — | HALT; request quota increase |
| `InsufficientBalance` | 0 | — | HALT; suggest account top-up |
| `PackageNotAvailable` | 0 | — | List available packages |
| Throttling / 429 | 3 | exponential | Back off and retry |

---

### Operation: Add Domain to WAF

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| WAF instance exists | DescribeInstance | Instance `running` | HALT; create instance |
| Domain valid | DNS validation | Valid domain format | Reject; ask for valid domain |
| Origin IP/backend | User provides | Valid backend | HALT; need backend info |
| Port | HTTP: 80, HTTPS: 443 | Valid port | Default to 80/443 |

#### Execution — CLI (Primary Path)

```bash
jdc --output json waf add-domain \
  --region-id "{{user.region}}" \
  --instance-id "{{user.waf_instance_id}}" \
  --domain-config '{
    "domain": "{{user.domain}}",
    "protocol": "HTTP",
    "port": 80,
    "httpsPort": 443,
    "originIp": ["{{user.origin_ip}}"],
    "originPort": {{user.origin_port|default(80)}},
    "originProtocol": "HTTP",
    "forceHttps": false,
    "algorithm": "ip_hash"
  }'
```

#### Execution — SDK (Fallback Path)

```python
from jdcloud_sdk.services.waf.apis.add_domain_request import AddDomainRequest

req = AddDomainRequest(
    regionId="{{user.region}}",
    instanceId="{{user.waf_instance_id}}",
    domainConfig={
        "domain": "{{user.domain}}",
        "protocol": "HTTP",  # or HTTPS, HTTP_HTTPS
        "port": 80,
        "originIp": ["{{user.origin_ip}}"],
        "originPort": {{user.origin_port|default(80)}},
        "originProtocol": "HTTP",
        "algorithm": "ip_hash"  # round_robin, least_conn, ip_hash
    }
)
resp = client.addDomain(req)
print(f"Domain added: {resp.result.domainId}")
print(f"WAF CNAME: {resp.result.cname}")
```

#### Post-execution Validation

1. Parse `{{output.domain_id}}` and `{{output.cname}}` from response
2. Poll **DescribeDomain** until status is `active`:
   ```bash
   for i in $(seq 1 60); do
     STATUS=$(jdc --output json waf describe-domain \
       --region-id "{{user.region}}" \
       --instance-id "{{user.waf_instance_id}}" \
       --domain-id "{{output.domain_id}}" | jq -r '.result.domain.status')
     [ "$STATUS" = "active" ] && break
     sleep 5
   done
   ```
3. Instruct user to update DNS: point domain CNAME to `{{output.cname}}`

#### DNS Configuration Guide

Provide user with DNS instructions:
```
Add the following DNS record:
  Type: CNAME
  Name: {{user.domain}}
  Value: {{output.cname}}
  TTL: 600

After DNS propagation (may take 5-60 minutes), traffic will flow through WAF.
```

---

### Operation: Configure HTTPS with SSL Certificate

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| Domain added | DescribeDomain | Domain exists | HALT; add domain first |
| Certificate | User provides | Valid cert + key | HALT; need certificate |
| Certificate match | Validate CN/SAN | Matches domain | Reject; get matching cert |

#### Execution — CLI (Primary Path)

```bash
jdc --output json waf bind-cert \
  --region-id "{{user.region}}" \
  --instance-id "{{user.waf_instance_id}}" \
  --domain-id "{{user.domain_id}}" \
  --cert-spec '{
    "certName": "{{user.domain}}-cert",
    "certContent": "{{user.cert_content}}",
    "keyContent": "{{user.key_content}}",
    "bindDomain": ["{{user.domain}}"]
  }'
```

#### Execution — SDK (Fallback Path)

```python
from jdcloud_sdk.services.waf.apis.bind_cert_request import BindCertRequest

req = BindCertRequest(
    regionId="{{user.region}}",
    instanceId="{{user.waf_instance_id}}",
    domainId="{{user.domain_id}}",
    certSpec={
        "certName": "{{user.domain}}-cert",
        "certContent": "{{user.cert_content}}",
        "keyContent": "{{user.key_content}}",
        "bindDomain": ["{{user.domain}}"]
    }
)
resp = client.bindCert(req)
print(f"Certificate bound: {resp.requestId}")
```

---

### Operation: Create Security Rule

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| Domain exists | DescribeDomain | Domain active | HALT |
| Rule type | Validate | Known rule type | List available types |
| Rule config | Validate JSON | Valid rule spec | Fix config |

#### Execution — CLI (Primary Path) - IP Blacklist Example

```bash
jdc --output json waf create-rule \
  --region-id "{{user.region}}" \
  --instance-id "{{user.waf_instance_id}}" \
  --domain-id "{{user.domain_id}}" \
  --rule-spec '{
    "ruleName": "block-suspicious-ips",
    "ruleType": "ip_blacklist",
    "matchOp": "match",
    "ipList": ["192.168.1.100", "10.0.0.0/24"],
    "action": "block",
    "status": 1
  }'
```

#### Execution — SDK (Fallback Path) - Rate Limiting Example

```python
from jdcloud_sdk.services.waf.apis.create_rule_request import CreateRuleRequest

req = CreateRuleRequest(
    regionId="{{user.region}}",
    instanceId="{{user.waf_instance_id}}",
    domainId="{{user.domain_id}}",
    ruleSpec={
        "ruleName": "rate-limit-api",
        "ruleType": "rate_limit",
        "matchOp": "match",
        "rateLimit": {
            "threshold": 1000,  # requests per period
            "period": 60,       # seconds
            "action": "captcha"  # block, captcha, log
        },
        "status": 1
    }
)
resp = client.createRule(req)
print(f"Rule created: {resp.result.ruleId}")
```

#### Common Rule Types

| Rule Type | Purpose | Key Parameters |
|-----------|---------|----------------|
| `ip_blacklist` | Block specific IPs | `ipList`, `action` |
| `ip_whitelist` | Allow specific IPs | `ipList` |
| `rate_limit` | Request throttling | `threshold`, `period`, `action` |
| `geo_blocking` | Block by geography | `countryCodes` |
| `url_acl` | Path-based rules | `urlPattern`, `action` |
| `bot_management` | Bot detection | `botType`, `action` |

---

### Operation: Enable Bot Management

#### Execution — CLI (Primary Path)

```bash
jdc --output json waf enable-bot-management \
  --region-id "{{user.region}}" \
  --instance-id "{{user.waf_instance_id}}" \
  --domain-id "{{user.domain_id}}" \
  --bot-config '{
    "enabled": true,
    "challengeMode": "captcha",
    "botThreshold": "medium",
    "allowGoodBots": ["googlebot", "bingbot"],
    "blockBadBots": true
  }'
```

---

### Operation: Query Attack Logs

#### Execution — CLI (Primary Path)

```bash
jdc --output json waf describe-attack-logs \
  --region-id "{{user.region}}" \
  --instance-id "{{user.waf_instance_id}}" \
  --domain-id "{{user.domain_id}}" \
  --start-time "2026-06-01T00:00:00Z" \
  --end-time "2026-06-08T00:00:00Z" \
  --page-size 100
```

#### Execution — SDK (Fallback Path)

```python
from jdcloud_sdk.services.waf.apis.describe_attack_logs_request import DescribeAttackLogsRequest

req = DescribeAttackLogsRequest(
    regionId="{{user.region}}",
    instanceId="{{user.waf_instance_id}}",
    domainId="{{user.domain_id}}",
    startTime="2026-06-01T00:00:00Z",
    endTime="2026-06-08T00:00:00Z",
    pageSize=100
)
resp = client.describeAttackLogs(req)

for log in resp.result.logs:
    print(f"{log.attackTime} | {log.attackType} | {log.srcIp} | {log.action}")
```

---

### Operation: Disable Domain Protection

#### Pre-flight (Safety Gate)

- **MUST** warn user: "Disabling WAF protection will expose your origin directly to the internet. Ensure your origin can handle direct traffic."
- **MUST** obtain explicit confirmation

#### Execution — CLI (Primary Path)

```bash
jdc --output json waf disable-domain \
  --region-id "{{user.region}}" \
  --instance-id "{{user.waf_instance_id}}" \
  --domain-id "{{user.domain_id}}"
```

---

### Operation: Remove Domain from WAF

#### Pre-flight (Safety Gate)

- **MUST** check protection status: if `active`, warn about traffic impact
- **MUST** instruct user to update DNS (remove CNAME) before removing from WAF
- **MUST** obtain explicit confirmation

#### Execution — CLI (Primary Path)

```bash
jdc --output json waf delete-domain \
  --region-id "{{user.region}}" \
  --instance-id "{{user.waf_instance_id}}" \
  --domain-id "{{user.domain_id}}"
```

---

### Operation: Delete WAF Instance

#### Pre-flight (Safety Gate)

- **MUST** check for protected domains
- **MUST** require all domains be removed first
- **MUST** obtain explicit confirmation: "Delete WAF instance `{{user.waf_instance_name}}`? All configurations will be lost. This is irreversible."

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| Instance exists | DescribeInstance | Instance found | Already deleted |
| No domains | ListDomains | Empty list | HALT; remove domains first |
| Billing cleared | Check charges | No pending charges | Warn about billing |

#### Execution — CLI (Primary Path)

```bash
jdc --output json waf delete-instance \
  --region-id "{{user.region}}" \
  --instance-id "{{user.waf_instance_id}}"
```

#### Post-execution Validation

1. Poll **DescribeInstance** until instance no longer exists (404)
2. Confirm deletion to user

## Prerequisites

> **Python 3.10 is REQUIRED, NOT 3.12.** `jdcloud_cli==1.2.12` uses `SafeConfigParser` which was removed in Python 3.12.

1. **Install uv** (system-wide, one-time):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   # or: brew install uv
   ```

2. **Bootstrap Python environment**:
   ```bash
   uv venv --python 3.10
   source .venv/bin/activate
   uv pip install jdcloud_cli jdcloud_sdk
   ```

3. **Configure Credentials for CLI** (`~/.jdc/config`):
   ```bash
   export HOME=/tmp/jdc-home
   mkdir -p /tmp/jdc-home/.jdc
   cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
   [default]
   access_key = {{env.JDC_ACCESS_KEY}}
   secret_key = {{env.JDC_SECRET_KEY}}
   region_id = cn-north-1
   endpoint = waf.jdcloud-api.com
   scheme = https
   timeout = 20
   CONFIGEOF
   printf "%s" "default" > /tmp/jdc-home/.jdc/current
   ```

4. **Verify Configuration**:
   ```bash
   # CLI verification
   jdc --output json waf describe-instances --region-id cn-north-1

   # SDK verification
   python -c "
   import os
   from jdcloud_sdk.core.credential import Credential
   credential = Credential(os.environ['JDC_ACCESS_KEY'], os.environ['JDC_SECRET_KEY'])
   print('SDK credentials OK')
   "
   ```

## Reference Directory

- [Core Concepts](references/core-concepts.md)
- [API & SDK Usage](references/api-sdk-usage.md)
- [CLI Usage](references/cli-usage.md)
- [Security Rules Reference](references/security-rules.md)
- [Troubleshooting Guide](references/troubleshooting.md)
- [Integration](references/integration.md)

## Operational Best Practices

- **Least privilege**: Start with whitelist approach, gradually add rules
- **Monitoring**: Regularly review attack logs and tune false positives
- **Backup**: Export WAF rules before major changes
- **Testing**: Test rules in "log" mode before "block" mode
- **Origin protection**: Restrict origin to accept traffic only from WAF IPs
- **SSL/TLS**: Use valid certificates, keep them updated
- **Rate limiting**: Set appropriate thresholds to avoid blocking legitimate users

## Quality Gate (GCL)

> This skill participates in the repository-wide **Generator-Critic-Loop**
> (GCL) defined in [`AGENTS.md`](../AGENTS.md#generator-critic-loop-gcl--adversarial-quality-gate).

### Parameters

| Parameter | Value | Reason |
|---|---|---|
| `max_iterations` | **3** | `AGENTS.md` §8 default for WAF ops (recommended) |
| `rubric_version` | `v1` | see [references/rubric.md](references/rubric.md) |
| `trace_path` | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | unified with `jdcloud-audit-ops` |
| `safety_confirm_required` | **true** | Delete instance/domain requires confirmation |

### Rubric Dimensions

| Dimension | Threshold | Notes |
|-----------|-----------|-------|
| Correctness | ≥ 0.5 | Instance/domain/rule state matches request |
| Safety | = 1 | Delete operations confirmed; protection status checked |
| Idempotency | ≥ 0.5 | Create with same name returns error consistently |
| Traceability | ≥ 0.5 | All jdc/SDK calls logged with request IDs |
| Spec Compliance | ≥ 0.5 | Follows WAF API conventions |

---

