---
name: jdcloud-iam-ops
description: >-
  Use when you need to create, manage, or troubleshoot JD Cloud IAM (Identity
  and Access Management) resources including sub-users, groups, roles, policies,
  and access keys via official API/SDK or official `jdc` CLI; user mentions IAM,
  访问控制, 子用户, 用户组, 角色, 策略, AKSK, or tasks target identity and
  permission management.
license: MIT
compatibility: >-
  Official JD Cloud SDK (Python 3.10+), valid API credentials, network
  access to JD Cloud endpoints, and official JD Cloud CLI (`jdc`) when this
  product is supported by the CLI (jdc-first with SDK fallback).
metadata:
  author: jdcloud
  version: "1.0.0"
  last_updated: "2026-05-08"
  runtime: Harness AI Agent
  api_profile: "JD Cloud IAM API v1 - https://iam.jdcloud-api.com/v1"
  cli_applicability: jdc-first-with-fallback
  cli_version_locked: "1.2.12"
  sdk_version_locked: ">=1.6.26"
  cli_support_evidence: >-
    Confirmed via `jdc iam --help` output showing full IAM subcommands:
    create-sub-user, create-group, create-role, create-policy, create-user-access-key,
    describe-sub-users, describe-groups, describe-roles, describe-policies,
    attach/detach policies, and AKSK management operations.
    Official CLI documentation: https://docs.jdcloud.com/cn/cli/introduction
  environment:
    - JDC_ACCESS_KEY
    - JDC_SECRET_KEY
    - JDC_REGION
---

> This skill follows the [Agent Skill OpenSpec](https://agentskills.io/specification).

# JD Cloud IAM Operations Skill

## Overview

JD Cloud IAM (访问控制 - Identity and Access Management) provides centralized identity management and resource access control for JD Cloud accounts. It enables creating sub-users, groups, roles, policies, and managing access keys (AK/SK) with fine-grained permission control. This skill is an **operational runbook** for agents: explicit scope, credential rules, pre-flight checks, **jdc-first execution with SDK/API fallback**, response validation, and failure recovery. **Do not use the web console as the primary agent execution path** in `SKILL.md`.

### CLI applicability (repository policy)

- **`cli_applicability: jdc-first-with-fallback`:** Official `jdc` supports this product with comprehensive subcommands. The Agent MUST attempt to use `jdc` as the **primary execution path**. If `jdc` installation or command execution fails, the Agent MUST retry up to **3 times** (with exponential backoff). Only after **3 consecutive failures** should the Agent fall back to **SDK/API**. Both paths MUST be documented. You **MUST** ship **`references/cli-usage.md`** and, in **each** execution flow below, document **both** the `jdc` step **and** the SDK fallback step for every operation the CLI exposes.

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
jdc --output json iam describe-sub-users

# WRONG (fails with "unrecognized arguments: --output json"):
jdc iam describe-sub-users --output json
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
endpoint = iam.jdcloud-api.com
scheme = https
timeout = 20
```

Plus a `~/.jdc/current` file containing just `default` (no newline at end).

**Failure 4: `PermissionError` on `~/.jdc/` directory creation**
The CLI's `ProfileManager.__init__()` calls `__make_config_dir()` which does `os.makedirs(os.path.expanduser("~") + "/.jdc")`. In sandboxed environments (trae-sandbox, containers) where home is not writable, this crashes with `PermissionError`. The fix is:
1. Set `HOME` to a writable path: `export HOME=/tmp/jdc-home`
2. Pre-create `~/.jdc/config` and `~/.jdc/current` files before running `jdc`

## Trigger & Scope (Agent-Readable)

### SHOULD Use This Skill When

- User mentions "JD Cloud IAM" OR "访问控制" OR "子用户" OR "用户组" OR "角色" OR "策略" OR "AKSK" OR "AccessKey"
- Task involves CRUD operations on IAM resources: sub-users, groups, roles, policies, access keys
- Task keywords: createSubUser, createGroup, createRole, createPolicy, attachPolicy, detachPolicy, assumeRole
- User asks to create, manage, authorize, or troubleshoot identity and permission resources **via API, SDK, CLI, or automation**
- Task involves permission management (attach/detach policies to users, groups, or roles)
- Task involves AKSK management (create, disable, enable, delete access keys)

### SHOULD NOT Use This Skill When

- Task is purely billing / account management → delegate to: `jdcloud-billing-ops` (when present)
- Task is about VPC / subnet / security group → delegate to: `jdcloud-vpc-ops`
- Task is about monitoring metrics / alarms → delegate to: `jdcloud-cloudmonitor-ops`
- User insists on **console-only** flows with no API → state limitation; do not invent undocumented HTTP steps

### Delegation Rules

- If IAM operations require monitoring (e.g., tracking policy changes), delegate to `jdcloud-cloudmonitor-ops` for metric collection.
- Multi-product requests: handle each product with its skill; do not merge unrelated APIs into one ambiguous flow.

## Variable Convention (Agent-Readable)

Structured placeholders reduce injection ambiguity and unsafe prompts:

| Placeholder | Meaning | Agent Action |
|-------------|---------|--------------|
| `{{env.JDC_ACCESS_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_SECRET_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_REGION}}` | From runtime environment | Use `cn-north-1` as default if unset |
| `{{user.subuser_name}}` | User-supplied sub-user name | Ask once; reuse |
| `{{user.group_name}}` | User-supplied group name | Ask once; reuse |
| `{{user.role_name}}` | User-supplied role name | Ask once; reuse |
| `{{user.policy_name}}` | User-supplied policy name | Ask once; reuse |
| `{{output.subuser_id}}` | From last API or CLI JSON response | Parse from response per operation |

> **`{{env.*}}` MUST NOT** be collected from the user. **`{{user.*}}`** MUST be collected interactively when missing.

> **Security Warning:** **NEVER** log, print, or expose `JDC_SECRET_KEY` (or any secret) in console output, debug messages, or logs. When verification is needed, check existence only (e.g., `if os.environ.get('JDC_SECRET_KEY')`) without printing the actual value. If logging credential status is required, use masked placeholders like `JDC_SECRET_KEY=<masked>` or `JDC_SECRET_KEY=***`. This applies to all execution flows (SDK, CLI, and debugging scripts).

## API and Response Conventions (Agent-Readable)

- **OpenAPI is canonical** for path, query, body fields, enums, and response shapes. Base path: `https://iam.jdcloud-api.com/v1/...`
- **Errors:** Map SDK/HTTP errors to `code` / `status` / message fields per spec.
- **Timestamps:** ISO 8601 with timezone when the API returns strings (e.g. `2026-05-08T10:00:00+08:00`).
- **Idempotency:** IAM operations are generally idempotent for updates; create operations may fail if resource name already exists.

### Example Response Field Table

| Operation | JSON Path (API) | Type | Description |
|-----------|----------------|------|-------------|
| Create Sub-user | `$.result.subUser.subUserId` | string | New sub-user ID |
| Describe Sub-user | `$.result.subUser.status` | string | Sub-user state (active, disabled) |
| List Sub-users | `$.result.subUsers[*].subUserId` | array | All sub-user IDs |
| Create Group | `$.result.group.groupId` | string | New group ID |
| Create Role | `$.result.role.roleId` | string | New role ID |
| Create Policy | `$.result.policy.policyId` | string | New policy ID |
| Create AccessKey | `$.result.accessKey.accessKeyId` | string | New AK ID |
| Attach/Detach Policy | `$.requestId` or `$.error` | string / object | Per spec |

### Expected State Transitions

IAM resources are typically **immediate** in state changes:
- Create → `active` / `available` immediately
- Update → changes reflected immediately (no polling needed)
- Delete → resource removed (404 on subsequent describe)
- Disable/Enable AK → status changes immediately

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-05-08 | Initial version with comprehensive IAM support: sub-users, groups, roles, policies, AKSK, STS, MFA; jdc-first with SDK fallback |

## Execution Flows (Agent-Readable)

Every operation: **Pre-flight → Execute (jdc primary / SDK fallback) → Validate → Recover**. Do not skip phases.

**jdc-first strategy:** The Agent MUST attempt `jdc` CLI first (primary path). If `jdc` fails after **3 retries** with exponential backoff, fall back to SDK/API. Documentation below lists `jdc` before SDK to reflect execution priority.

### Operation: Create Sub-user

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| CLI / deps | `jdc --version` | Exit code 0 | Retry up to 3 times; then fall back to SDK |
| SDK / deps | `import jdcloud_sdk.services.iam.client.IamClient` | No import error | Document install pin (fallback path) |
| Credentials | Construct credential from env or CLI config | Non-empty keys | HALT; user configures env |
| User input | Collect sub-user name and description | Valid names | Ask user |

#### Execution — CLI (`jdc`) [Primary Path]

**Required** when `cli_applicability: jdc-first-with-fallback`. Use `--output json` at the **top level** (before the subcommand). Do NOT use `--no-interactive` — it is not supported by jdc CLI.

```bash
jdc --output json iam create-sub-user \
  --sub-user-name "{{user.subuser_name}}" \
  --description "{{user.description}}"
```

#### Pre-flight: Configure jdc Config File for Sandbox

Before running any `jdc` command in sandboxed environments, ensure the config file exists:

```bash
# Setup jdc config in a writable location (sandbox-safe)
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc
cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[{{user.profile_name|default:"default"}}]
access_key = {{env.JDC_ACCESS_KEY}}
secret_key = {{env.JDC_SECRET_KEY}}
region_id = {{user.region}}
endpoint = iam.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF
printf "%s" "default" > /tmp/jdc-home/.jdc/current
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.iam.client.IamClient import IamClient
from jdcloud_sdk.services.iam.apis.CreateSubUserRequest import CreateSubUserRequest, CreateSubUserParameters

credential = Credential(os.environ["JDC_ACCESS_KEY"], os.environ["JDC_SECRET_KEY"])
client = IamClient(credential)

params = CreateSubUserParameters(
    subUserName="{{user.subuser_name}}",
    description="{{user.description}}"
)
req = CreateSubUserRequest(parameters=params)
resp = client.send(req)
subuser_id = resp.result["subUser"]["subUserId"]
```

#### Post-execution Validation

1. Capture `{{output.subuser_id}}` from response.
2. Verify sub-user creation by calling describe (optional for IAM).

#### Failure Recovery

| Error pattern | Max retries | Backoff | Agent Action |
|---------------|-------------|---------|--------------|
| `InvalidParameter` / 400 | 0–1 | — | Fix args per OpenAPI; retry once |
| `QuotaExceeded` | 0 | — | HALT; user requests quota increase |
| `SubUserAlreadyExists` | 0 | — | Ask reuse vs new name |
| Throttling / 429 | 3 | exponential | Back off; respect Retry-After |
| `InternalError` / 5xx | 3 | 2s, 4s, 8s | Retry; HALT with requestId if persists |

### Operation: Create Group

#### Execution (CLI) [Primary Path]

```bash
jdc --output json iam create-group \
  --group-name "{{user.group_name}}" \
  --description "{{user.description}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.iam.apis.CreateGroupRequest import CreateGroupRequest, CreateGroupParameters

params = CreateGroupParameters(
    groupName="{{user.group_name}}",
    description="{{user.description}}"
)
req = CreateGroupRequest(parameters=params)
resp = client.send(req)
group_id = resp.result["group"]["groupId"]
```

### Operation: Create Role

#### Execution (CLI) [Primary Path]

```bash
jdc --output json iam create-role \
  --role-name "{{user.role_name}}" \
  --description "{{user.description}}" \
  --assume-role-policy-document '{{user.assume_role_policy_json}}'
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.iam.apis.CreateRoleRequest import CreateRoleRequest, CreateRoleParameters

params = CreateRoleParameters(
    roleName="{{user.role_name}}",
    description="{{user.description}}",
    assumeRolePolicyDocument="{{user.assume_role_policy_json}}"
)
req = CreateRoleRequest(parameters=params)
resp = client.send(req)
role_id = resp.result["role"]["roleId"]
```

### Operation: Create Policy

#### Execution (CLI) [Primary Path]

```bash
jdc --output json iam create-policy \
  --policy-name "{{user.policy_name}}" \
  --description "{{user.description}}" \
  --policy-document '{{user.policy_json}}'
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.iam.apis.CreatePolicyRequest import CreatePolicyRequest, CreatePolicyParameters

params = CreatePolicyParameters(
    policyName="{{user.policy_name}}",
    description="{{user.description}}",
    policyDocument="{{user.policy_json}}"
)
req = CreatePolicyRequest(parameters=params)
resp = client.send(req)
policy_id = resp.result["policy"]["policyId"]
```

### Operation: Attach Policy to Sub-user

#### Execution (CLI) [Primary Path]

```bash
jdc --output json iam attach-sub-user-policy \
  --sub-user-name "{{user.subuser_name}}" \
  --policy-name "{{user.policy_name}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.iam.apis.AttachSubUserPolicyRequest import AttachSubUserPolicyRequest, AttachSubUserPolicyParameters

params = AttachSubUserPolicyParameters(
    subUserName="{{user.subuser_name}}",
    policyName="{{user.policy_name}}"
)
req = AttachSubUserPolicyRequest(parameters=params)
resp = client.send(req)
```

### Operation: Attach Policy to Group

#### Execution (CLI) [Primary Path]

```bash
jdc --output json iam attach-group-policy \
  --group-name "{{user.group_name}}" \
  --policy-name "{{user.policy_name}}"
```

### Operation: Attach Policy to Role

#### Execution (CLI) [Primary Path]

```bash
jdc --output json iam attach-role-policy \
  --role-name "{{user.role_name}}" \
  --policy-name "{{user.policy_name}}"
```

### Operation: Create AccessKey (Main Account)

#### Execution (CLI) [Primary Path]

```bash
jdc --output json iam create-user-access-key
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.iam.apis.CreateUserAccessKeyRequest import CreateUserAccessKeyRequest, CreateUserAccessKeyParameters

params = CreateUserAccessKeyParameters()
req = CreateUserAccessKeyRequest(parameters=params)
resp = client.send(req)
access_key_id = resp.result["accessKey"]["accessKeyId"]
secret_key = resp.result["accessKey"]["secretKey"]
```

### Operation: Delete Sub-user

#### Pre-flight (Safety Gate)

- **MUST** obtain explicit confirmation: irreversible delete of `{{user.subuser_name}}` (`{{user.subuser_id}}`).
- **MUST NOT** proceed without clear user assent.

#### Execution (CLI) [Primary Path]

**⚠️ Safety Gate**: MUST obtain explicit user confirmation before executing CLI command.

```bash
# Confirm deletion with user first
jdc --output json iam delete-sub-user \
  --sub-user-name "{{user.subuser_name}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

**⚠️ Safety Gate**: MUST obtain explicit user confirmation before calling SDK delete method.

```python
from jdcloud_sdk.services.iam.apis.DeleteSubUserRequest import DeleteSubUserRequest, DeleteSubUserParameters

# Confirm deletion with user: "Are you sure you want to delete {{user.subuser_name}}? This is IRREVERSIBLE."
# Proceed only after explicit "yes" / "confirm" response

params = DeleteSubUserParameters(subUserName="{{user.subuser_name}}")
req = DeleteSubUserRequest(parameters=params)
resp = client.send(req)
```

### Operation: Assume Role (STS)

#### Execution (CLI) [Primary Path]

```bash
jdc --output json sts assume-role \
  --role-name "{{user.role_name}}" \
  --duration-seconds "{{user.duration}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.sts.client.StsClient import StsClient
from jdcloud_sdk.services.sts.apis.AssumeRoleRequest import AssumeRoleRequest, AssumeRoleParameters

sts_client = StsClient(credential)
params = AssumeRoleParameters(
    roleName="{{user.role_name}}",
    durationSeconds="{{user.duration}}"
)
req = AssumeRoleRequest(parameters=params)
resp = sts_client.send(req)
# Returns temporary credentials: accessKeyId, secretKey, sessionToken
```

## Prerequisites

Environment setup follows a **jdc-first with fallback** strategy:

1. **Attempt `jdc` CLI setup** via `uv` (primary path)
2. On failure, **retry up to 3 times** with exponential backoff (0s → 2s → 4s)
3. After **3 consecutive failures**, fall back to **SDK-only** setup

### Python Runtime (uv)

Both `jdc` CLI and the JD Cloud Python SDK require a Python runtime. Use **`uv`** for local, isolated, and **idempotent** environment management:

**Install uv (system-wide, one-time per machine):**
```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
# Or via Homebrew: brew install uv

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Phase 1: jdc CLI Setup (Primary Path)

```bash
# Create and activate virtual environment (idempotent)
uv venv --python 3.10
source .venv/bin/activate

# Install jdc CLI and SDK
uv pip install jdcloud_cli jdcloud_sdk

# Verify
jdc --version
python -c "import jdcloud_sdk; print('SDK OK')"
```

#### Retry Logic (Up to 3 Attempts)

If `jdc --version` or any `jdc` command fails:

```bash
# Retry 1: re-run pip install
uv pip install jdcloud_cli jdcloud_sdk
jdc --version && echo "OK" || echo "FAIL"

# Retry 2 (wait 2s)
sleep 2
uv pip install --force-reinstall jdcloud_cli
jdc --version && echo "OK" || echo "FAIL"

# Retry 3 (wait 4s)
sleep 4
uv pip install --force-reinstall jdcloud_cli jdcloud_sdk
jdc --version && echo "OK" || echo "FAIL"
```

If all **3 retries** fail, proceed to **Phase 2: SDK Fallback**.

### Phase 2: SDK Fallback (After 3 jdc Failures)

```bash
uv venv --python 3.10
source .venv/bin/activate
uv pip install jdcloud_sdk
python -c "import jdcloud_sdk; print('SDK OK')"
```

### Configure jdc Credentials (Sandbox-Safe)

**CRITICAL**: The `jdc` CLI does NOT read `JDC_ACCESS_KEY` / `JDC_SECRET_KEY` environment variables. It reads credentials exclusively from `~/.jdc/config` (INI format). In sandboxed environments where `~` is not writable, follow these steps:

```bash
# 1. Set HOME to a writable location
export HOME=/tmp/jdc-home

# 2. Pre-create the config directory and files
mkdir -p /tmp/jdc-home/.jdc

cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = {{env.JDC_ACCESS_KEY}}
secret_key = {{env.JDC_SECRET_KEY}}
region_id = {{user.region}}
endpoint = iam.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF

# 3. Write current profile WITHOUT trailing newline
printf "%s" "default" > /tmp/jdc-home/.jdc/current

# 4. Run jdc with --output json at TOP level
jdc --output json iam describe-sub-users
```

### Configure Credentials for SDK (Environment Variables)

SDK reads credentials from environment variables — no config file needed:

```bash
export JDC_ACCESS_KEY="{{env.JDC_ACCESS_KEY}}"
export JDC_SECRET_KEY="{{env.JDC_SECRET_KEY}}"
export JDC_REGION="cn-north-1"
```

> Security: Never commit `.env` files to version control.

## Reference Directory

- [Core Concepts](references/core-concepts.md)
- [API & SDK Usage](references/api-sdk-usage.md)
- [CLI Usage](references/cli-usage.md)
- [Troubleshooting Guide](references/troubleshooting.md)
- [Monitoring & Alerts](references/monitoring.md)
- [Integration](references/integration.md)

## Operational Best Practices

- **Least privilege:** Grant minimum permissions required for each sub-user, group, or role; use JD Cloud managed policies when available.
- **Regular review:** Periodically audit policies and permissions; remove unused accounts and outdated permissions.
- **AKSK rotation:** Rotate access keys regularly; disable and delete old keys after creating new ones.
- **MFA enablement:** Enable MFA for sensitive operations and administrative accounts.
- **Role-based access:** Use roles for cross-account access and service-to-service authorization.
- **Group management:** Organize users into groups with shared permissions to simplify access control.
- **Policy naming:** Use descriptive policy names with environment or service prefixes for clarity.