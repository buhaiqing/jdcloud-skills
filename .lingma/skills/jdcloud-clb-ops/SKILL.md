---
name: jdcloud-clb-ops
description: >-
  Manages JD Cloud CLB (Cloud Load Balancer) resources. Use when you need to deploy, 
  configure, troubleshoot, or monitor CLB instances on JD Cloud.
  Includes CLI usage, SDK integration, and operational best practices.
---

# JD Cloud CLB (Cloud Load Balancer) Operations Skill

## Overview
CLB (Cloud Load Balancer) is a core service on JD Cloud that provides distributed traffic distribution capabilities to improve application availability and performance. This skill enables efficient operations, including automated deployment, real-time monitoring, and rapid troubleshooting of CLB instances.

## Trigger & Scope (Agent-Readable)

### SHOULD Use This Skill When
- User mentions "JD Cloud CLB" OR "负载均衡" OR "Cloud Load Balancer"
- Task involves CRUD operations on CLB resources: create, describe, modify, delete, list
- Task keywords: load balancer, listener, backend server, health check, SSL certificate
- User asks to deploy, configure, troubleshoot, or monitor CLB resources

### SHOULD NOT Use This Skill When
- Task is purely about billing / account management → delegate to: `jdcloud-billing-ops`
- Task is about IAM / user permission management → delegate to: `jdcloud-iam-ops`
- Task is about VPC network configuration → delegate to: `jdcloud-vpc-ops`

### Delegation Rules
- If the user asks about resource B that depends on CLB created/managed here, create CLB first then suggest chaining to the B-specific Skill
- If the request spans multiple unrelated products, process each with its corresponding Skill independently

## Variable Convention (Agent-Readable)
This Skill uses structured placeholders to avoid prompt injection and parsing ambiguity:

| Placeholder | Meaning | Agent Action |
|-------------|---------|--------------|
| `{{env.JDC_ACCESS_KEY}}` | Resolved from Agent runtime environment | NEVER prompt user for this; fail if not set |
| `{{env.JDC_SECRET_KEY}}` | Resolved from Agent runtime environment | NEVER prompt user for this; fail if not set |
| `{{env.JDC_REGION}}` | Resolved from Agent runtime environment | Use `cn-north-1` as default if unset |
| `{{user.region}}` | Must be collected from user | Ask user once and reuse |
| `{{user.clb_name}}` | Must be collected from user | Ask user once and reuse |
| `{{user.clb_id}}` | Must be collected from user | Ask user once and reuse |
| `{{user.listener_id}}` | Must be collected from user | Ask user once and reuse |
| `{{user.cert_name}}` | Must be collected from user | Ask user once and reuse |
| `{{user.cert_file}}` | Must be collected from user | Ask user for certificate file path |
| `{{user.key_file}}` | Must be collected from user | Ask user for private key file path |
| `{{user.cert_id}}` | Must be collected from user | Ask user once and reuse |
| `{{user.new_cert_id}}` | Must be collected from user | Ask user for new certificate ID |
| `{{user.old_cert_id}}` | Captured from CLI output | Parse from listener describe for rollback |
| `{{user.domain}}` | Must be collected from user | Ask user for domain name |
| `{{user.clb_ip}}` | Captured from CLI output | Parse from `$.data.ipAddress` |
| `{{output.clb_id}}` | Captured from CLI JSON output | Parse from `$.data.clbId` |
| `{{output.cert_id}}` | Captured from CLI JSON output | Parse from `$.data.certificateId` |

> Rule: Placeholders wrapped in `{{env.*}}` MUST NOT be exposed to or requested from the user. Placeholders wrapped in `{{user.*}}` MUST be collected interactively.

## Output Parsing Rules (Agent-Readable)

### Mandatory CLI Conventions
- All CLI commands MUST append `--output json` for machine-parseable output
- All CLI commands SHOULD append `--no-interactive` (or equivalent) to prevent blocking on user prompts
- Timestamps are in ISO 8601 format with timezone: `2026-04-28T10:00:00+08:00`
- Resource IDs follow pattern: `clb-[hash]` (e.g., `clb-abc123def`)
- Boolean values: `true` / `false` (lowercase)

### Key JSON Paths for Common Operations
| Operation | JSON Path | Type | Description |
|-----------|-----------|------|-------------|
| Create | `$.data.clbId` | string | CLB instance ID to track |
| Describe | `$.data.status` | string | Current state (e.g. `running`, `stopped`) |
| List | `$.data[*].clbId` | array | All CLB instance IDs |
| Modify | `$.data.success` | boolean | Whether modification succeeded |
| Delete | `$.data.success` | boolean | Whether deletion succeeded |

### Expected State Transitions
| Operation | Initial State | Target State | Poll Interval | Max Wait |
|-----------|---------------|--------------|---------------|----------|
| Create | - | `running` | 5s | 300s |
| Start | `stopped` | `running` | 5s | 120s |
| Stop | `running` | `stopped` | 5s | 120s |
| Delete | `running`/`stopped` | (404 on describe) | 5s | 300s |

## Changelog

| Version | Date | Changes |
|------|------|---------|
| 1.1.0 | 2026-04-28 | Added SSL certificate management: upload, update, list, delete operations with full validation and rollback support |
| 1.0.0 | 2026-04-28 | Initial version with basic CLB operations guide and reference templates |

## Execution Flows (Agent-Readable)
Every operation follows the pattern: Pre-flight → Execute → Validate → Recover. The Agent MUST NOT skip any phase.

### Operation: Create CLB Instance

#### Pre-flight Checks
| Check | Command | Expected | On Failure |
|-------|---------|----------|------------|
| CLI installed | `jdc --version` | exit code 0 | Guide user to install jdcloud-cli |
| Credentials valid | `jdc config validate --output json` | `$.valid == true` | Prompt user to run `jdc config init` |
| Region available | `jdc clb describe-regions --output json` | `{{user.region}}` in list | Suggest nearest available region |
| Quota available | `jdc clb describe-quota --region {{user.region}} --output json` | `$.available > 0` | Inform user of quota limit, suggest increase |

#### Execution
```bash
jdc clb create-clb \
  --region {{user.region}} \
  --clb-name "{{user.clb_name}}" \
  --output json \
  --no-interactive
```

#### Post-execution Validation
1. Capture `{{output.clb_id}}` from `$.data.clbId`
2. Poll until ready:
   ```bash
   for i in $(seq 1 60); do
     STATUS=$(jdc clb describe-clb \
       --clb-id {{output.clb_id}} \
       --region {{user.region}} \
       --output json | jq -r '.data.status')
     [ "$STATUS" = "running" ] && break
     sleep 5
   done
   ```
3. If status is `running` → operation succeeded, report `{{output.clb_id}}` to user
4. If status is `error` → capture error from `$.data.errorMessage`, go to Failure Recovery

#### Failure Recovery
| Exit Code | Error Pattern (regex) | Max Retries | Backoff | Agent Action |
|-----------|-----------------------|-------------|---------|--------------|
| 1 | `InvalidParameter` | 1 | - | Re-check parameter format against API spec, retry with corrected params |
| 1 | `QuotaExceeded` | 0 | - | HALT. Inform user quota is full, suggest requesting increase |
| 1 | `InsufficientBalance` | 0 | - | HALT. Inform user to top up account |
| 2 | `ResourceAlreadyExists` | 0 | - | Ask user if they want to reuse existing resource or use a different name |
| 3 | `InternalError` | 3 | 2s, 4s, 8s | Retry with exponential backoff. After 3rd failure, report to user |
| Other | `.*` | 3 | 5s, 10s, 15s | Retry. On final failure, extract full error message and present to user |

### Operation: Describe CLB Instance

#### Execution
```bash
jdc clb describe-clb \
  --clb-id {{user.clb_id}} \
  --region {{env.JDC_REGION}} \
  --output json
```

#### Output to Present to User
| Field | JSON Path | Display Format |
|-------|-----------|----------------|
| ID | `$.data.clbId` | Plain text |
| Name | `$.data.clbName` | Plain text |
| Status | `$.data.status` | Badge: 🟢 running / 🟡 pending / 🔴 error |
| Created At | `$.data.createTime` | ISO 8601 → human-readable |
| IP Address | `$.data.ipAddress` | `-` if null |

### Operation: Delete CLB Instance

#### Pre-flight (Safety Gate)
- **MUST** ask user: "Are you sure you want to delete `{{user.clb_name}}` ({{user.clb_id}})? This is irreversible."
- **MUST** wait for explicit "yes" / "confirm" before proceeding

#### Execution
```bash
jdc clb delete-clb \
  --clb-id {{user.clb_id}} \
  --region {{env.JDC_REGION}} \
  --output json \
  --no-interactive
```

#### Post-execution Validation
1. Poll `describe` until it returns HTTP 404 or `status: "deleted"` (max 300s)

### Operation: Upload SSL Certificate

#### Pre-flight Checks
| Check | Command | Expected | On Failure |
|-------|---------|----------|------------|
| Certificate file exists | `test -f {{user.cert_file}}` | exit code 0 | Guide user to provide correct certificate path |
| Private key file exists | `test -f {{user.key_file}}` | exit code 0 | Guide user to provide correct private key path |
| Certificate format valid | `openssl x509 -in {{user.cert_file}} -noout` | exit code 0 | Validate certificate format (PEM) |
| Key matches certificate | `openssl x509 -noout -modulus -in {{user.cert_file}} \| openssl md5` vs `openssl rsa -noout -modulus -in {{user.key_file}} \| openssl md5` | MD5 hashes match | Verify certificate and key pair match |

#### Execution
```bash
jdc clb upload-certificate \
  --region {{env.JDC_REGION}} \
  --certificate-name "{{user.cert_name}}" \
  --certificate-content "$(cat {{user.cert_file}})" \
  --private-key "$(cat {{user.key_file}})" \
  --output json \
  --no-interactive
```

#### Post-execution Validation
1. Capture `{{output.cert_id}}` from `$.data.certificateId`
2. Verify certificate uploaded:
   ```bash
   jdc clb describe-certificate \
     --certificate-id {{output.cert_id}} \
     --region {{env.JDC_REGION}} \
     --output json
   ```
3. Check certificate details:
   - Common Name (CN) matches expected domain
   - Validity period (not expired)
   - Issuer information

#### Failure Recovery
| Exit Code | Error Pattern (regex) | Max Retries | Backoff | Agent Action |
|-----------|-----------------------|-------------|---------|--------------|
| 1 | `InvalidCertificate` | 0 | - | HALT. Certificate format invalid, guide user to check PEM format |
| 1 | `CertificateExpired` | 0 | - | HALT. Certificate already expired, request new certificate |
| 1 | `KeyMismatch` | 0 | - | HALT. Private key doesn't match certificate, verify key pair |
| 1 | `DuplicateCertificate` | 0 | - | Ask user if they want to update existing certificate or use different name |
| 3 | `InternalError` | 3 | 2s, 4s, 8s | Retry with exponential backoff |

### Operation: Update SSL Certificate on Listener

#### Pre-flight Checks
| Check | Command | Expected | On Failure |
|-------|---------|----------|------------|
| Listener exists | `jdc clb describe-listener --clb-id {{user.clb_id}} --listener-id {{user.listener_id}} --region {{env.JDC_REGION}} --output json` | `$.data.protocol == "HTTPS"` | Verify listener uses HTTPS protocol |
| New certificate available | `jdc clb describe-certificate --certificate-id {{user.new_cert_id}} --region {{env.JDC_REGION}} --output json` | `$.data.status == "active"` | Ensure certificate is active and valid |
| Current certificate info | Parse from listener describe output | Extract `$.data.certificateId` | Document current certificate for rollback |

#### Execution
```bash
jdc clb modify-listener \
  --clb-id {{user.clb_id}} \
  --listener-id {{user.listener_id}} \
  --region {{env.JDC_REGION}} \
  --certificate-id {{user.new_cert_id}} \
  --output json \
  --no-interactive
```

#### Post-execution Validation
1. Wait 30 seconds for changes to propagate
2. Verify listener updated:
   ```bash
   jdc clb describe-listener \
     --clb-id {{user.clb_id}} \
     --listener-id {{user.listener_id}} \
     --region {{env.JDC_REGION}} \
     --output json
   ```
3. Confirm `$.data.certificateId == {{user.new_cert_id}}`
4. Test HTTPS connectivity:
   ```bash
   curl -I https://{{user.domain}} --resolve {{user.domain}}:443:{{user.clb_ip}}
   ```
5. Verify SSL certificate served:
   ```bash
   echo | openssl s_client -connect {{user.clb_ip}}:443 -servername {{user.domain}} 2>/dev/null | openssl x509 -noout -dates
   ```

#### Rollback Plan
If validation fails:
1. Immediately revert to previous certificate:
   ```bash
   jdc clb modify-listener \
     --clb-id {{user.clb_id}} \
     --listener-id {{user.listener_id}} \
     --region {{env.JDC_REGION}} \
     --certificate-id {{user.old_cert_id}} \
     --output json \
     --no-interactive
   ```
2. Notify user of failure and provide error details

### Operation: List SSL Certificates

#### Execution
```bash
jdc clb describe-certificates \
  --region {{env.JDC_REGION}} \
  --output json
```

#### Output to Present to User
| Field | JSON Path | Display Format |
|-------|-----------|----------------|
| Certificate ID | `$.data[*].certificateId` | Plain text |
| Certificate Name | `$.data[*].certificateName` | Plain text |
| Common Name | `$.data[*].commonName` | Plain text |
| Expiration Date | `$.data[*].expireTime` | ISO 8601 → human-readable + days remaining |
| Status | `$.data[*].status` | Badge: 🟢 active / 🔴 expired |
| Created At | `$.data[*].createTime` | ISO 8601 → human-readable |

### Operation: Delete SSL Certificate

#### Pre-flight (Safety Gate)
- **MUST** check if certificate is attached to any listeners
- **MUST** ask user: "Certificate `{{user.cert_name}}` ({{user.cert_id}}) will be deleted. If attached to listeners, this may cause service disruption. Continue?"
- **MUST** wait for explicit "yes" / "confirm" before proceeding

#### Execution
```bash
jdc clb delete-certificate \
  --certificate-id {{user.cert_id}} \
  --region {{env.JDC_REGION}} \
  --output json \
  --no-interactive
```

#### Post-execution Validation
1. Verify deletion:
   ```bash
   jdc clb describe-certificate \
     --certificate-id {{user.cert_id}} \
     --region {{env.JDC_REGION}} \
     --output json
   ```
2. Should return HTTP 404 or error indicating certificate not found

## Prerequisites
1. **Install JD Cloud CLI**:
   ```bash
   pip install jdcloud-cli
   jdc config init
   ```
2. **Configure Credentials**:
   The Agent runtime MUST have the following environment variables set. These map to `{{env.*}}` placeholders used throughout this Skill:
   ```bash
   export JDC_ACCESS_KEY="{{env.JDC_ACCESS_KEY}}"
   export JDC_SECRET_KEY="{{env.JDC_SECRET_KEY}}"
   export JDC_REGION="cn-north-1"
   ```
   > The Agent MUST verify these are set before any operation. If missing, instruct user to configure via `jdc config init`.

## Reference Directory
- [Core Concepts](references/core-concepts.md)
- [CLI Usage](references/cli-usage.md)
- [Troubleshooting Guide](references/troubleshooting.md)
- [Monitoring & Alerts](references/monitoring.md)
- [Integration (MCP/SDK)](references/integration.md)
- [SSL Certificate Management Best Practices](references/ssl-certificate-management.md)

## Operational Best Practices
- **High Availability**: Always deploy across multiple availability zones.
- **Security**: Apply least-privilege IAM policies.
- **Cost Optimization**: Utilize auto-scaling and reserved instances where applicable.
- **Health Monitoring**: Configure health checks for backend servers to ensure traffic is only routed to healthy instances.
- **SSL Termination**: Use CLB for SSL termination to reduce backend server load.