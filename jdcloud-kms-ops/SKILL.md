---
name: jdcloud-kms-ops
description: >-
  Use this skill for JD Cloud key management and encryption — create and manage
  encryption keys; encrypt/decrypt sensitive data; store and retrieve secrets;
  rotate keys; schedule key deletion. Apply when the user mentions KMS, 密钥管理,
  加密, 解密, 密钥, or asks about data encryption, key management, secrets storage,
  or protecting sensitive data on JD Cloud, even without explicit "KMS" mentions.
license: MIT
compatibility: >-
  Official JD Cloud SDK (Python 3.10+), valid API credentials, network
  access to JD Cloud endpoints, and official JD Cloud CLI (`jdc`) when this
  product is supported by the CLI (jdc-first with SDK fallback).
metadata:
  author: buhaiqing
  version: "1.1.0"
  last_updated: "2026-06-04"
  runtime: Harness AI Agent
  api_profile: "JD Cloud KMS API v1 - https://kms.jdcloud-api.com/v1"
  cli_applicability: jdc-first-with-fallback
  cli_version_locked: "1.2.12"
  sdk_version_locked: ">=1.6.26"
  cli_support_evidence: >-
    Confirmed via `jdc --help` output showing 'kms' in product list:
    `kms                 密钥管理服务`.
    Full CLI subcommand list verified:
    create-key, describe-key, describe-key-list, enable-key, disable-key,
    encrypt, decrypt, generate-data-key, key-rotation, schedule-key-deletion,
    cancel-key-deletion, create-secret, delete-secret, describe-secret-list,
    enable-secret, disable-secret, create-secret-version, etc.
    Official CLI documentation: https://docs.jdcloud.com/cn/cli/introduction
  environment:
    - JDC_ACCESS_KEY
    - JDC_SECRET_KEY
    - JDC_REGION
---

> This skill follows the [Agent Skill OpenSpec](https://agentskills.io/specification).

# JD Cloud Key Management Service (KMS) Operations Skill

## Overview

JD Cloud Key Management Service (密钥管理服务 / KMS) is a security management product that uses Hardware Security Modules (HSM) to protect key security. Users can safely, controllably, and conveniently use managed keys, focusing on developing scenarios that require encryption and decryption functionality. KMS provides centralized control of encryption keys, secrets management, and cryptographic operations (encrypt, decrypt, sign, verify). This skill is an **operational runbook** for agents: explicit scope, credential rules, pre-flight checks, **jdc-first execution with SDK/API fallback**, response validation, and failure recovery. **Do not use the web console as the primary agent execution path** in `SKILL.md`.

### CLI applicability (repository policy)

- **`cli_applicability: jdc-first-with-fallback`:** Official `jdc` supports this product. The Agent MUST attempt to use `jdc` as the **primary execution path**. If `jdc` installation or command execution fails, the Agent MUST retry up to **3 times** (with exponential backoff). Only after **3 consecutive failures** should the Agent fall back to **SDK/API**. Both paths MUST be documented. You **MUST** ship **`references/cli-usage.md`** and, in **each** execution flow below, document **both** the `jdc` step **and** the SDK fallback step for every operation the CLI exposes.

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
jdc --output json kms describe-key-list --page-number 1 --page-size 100

# WRONG (fails with "unrecognized arguments: --output json"):
jdc kms describe-key-list --page-number 1 --page-size 100 --output json
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
endpoint = kms.jdcloud-api.com
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

- User mentions "JD Cloud KMS" OR "密钥管理服务" OR "密钥管理" OR "Key Management Service" OR "KMS密钥"
- Task involves CRUD operations on cryptographic keys: create, describe, modify, delete, list, encrypt, decrypt, rotate
- Task involves secrets management: create secret, delete secret, list secrets, enable/disable secret, secret versions
- Task keywords: createKey, describeKey, encrypt, decrypt, generateDataKey, keyRotation, scheduleKeyDeletion, createSecret, describeSecretList
- User asks to deploy, configure, troubleshoot, or monitor KMS **via API, SDK, CLI, or automation**
- Task involves cryptographic operations (encrypt/decrypt data, generate data keys, sign/verify)

### SHOULD NOT Use This Skill When

- Task is purely billing / account management → delegate to: `jdcloud-billing-ops` (when present)
- Task is IAM / permission model only → delegate to: `jdcloud-iam-ops` (when present)
- Task is about VPC / subnet / security group → delegate to: `jdcloud-vpc-ops`
- Task is about monitoring metrics / alarms → delegate to: `jdcloud-cloudmonitor-ops`
- User insists on **console-only** flows with no API → state limitation; do not invent undocumented HTTP steps

### Delegation Rules

- If encryption key is needed for storage service (OSS, disk), verify or create KMS key first via this skill.
- If user asks about KMS monitoring metrics or alarm rules, delegate metric query to `jdcloud-cloudmonitor-ops`.
- Multi-product requests: handle each product with its skill; do not merge unrelated APIs into one ambiguous flow.

## Variable Convention (Agent-Readable)

Structured placeholders reduce injection ambiguity and unsafe prompts:

| Placeholder | Meaning | Agent Action |
|-------------|---------|--------------|
| `{{env.JDC_ACCESS_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_SECRET_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_REGION}}` | From runtime environment | Use `cn-north-1` as default if unset |
| `{{user.region}}` | User-supplied region | Ask once; reuse |
| `{{user.key_id}}` | User-supplied KMS key ID | Ask once; reuse |
| `{{user.key_name}}` | User-supplied key name | Ask once; reuse |
| `{{user.secret_name}}` | User-supplied secret name | Ask once; reuse |
| `{{output.key_id}}` | From last API or CLI JSON response | Parse from `$.result.keyId` |

> **`{{env.*}}` MUST NOT** be collected from the user. **`{{user.*}}`** MUST be collected interactively when missing.

> **Security Warning:** **NEVER** log, print, or expose `JDC_SECRET_KEY` (or any secret) in console output, debug messages, or logs. When verification is needed, check existence only (e.g., `if os.environ.get('JDC_SECRET_KEY')`) without printing the actual value. If logging credential status is required, use masked placeholders like `JDC_SECRET_KEY=<masked>` or `JDC_SECRET_KEY=***`. This applies to all execution flows (SDK, CLI, and debugging scripts).

## API and Response Conventions (Agent-Readable)

- **OpenAPI is canonical** for path, query, body fields, enums, and response shapes. Base path: `https://kms.jdcloud-api.com/v1`
- **Errors:** Map SDK/HTTP errors to `code` / `status` / message fields per spec.
- **Timestamps:** ISO 8601 with timezone when the API returns strings (e.g. `2026-05-08T10:00:00+08:00`).
- **Idempotency:** Document duplicate key name behavior and retry safety per API.

### Example Response Field Table

| Operation | JSON Path (API) | Type | Description |
|-----------|----------------|------|-------------|
| Create Key | `$.result.keyId` | string | New KMS key ID |
| Describe Key | `$.result.key.status` | string | Key state (Enabled, Disabled, PendingDeletion) |
| List Keys | `$.result.keys[*].keyId` | array | All key IDs |
| Encrypt | `$.result.ciphertextBlob` | string | Encrypted data (Base64) |
| Decrypt | `$.result.plaintext` | string | Decrypted data (Base64) |
| Generate Data Key | `$.result.dataKeyCiphertextBlob` | string | Encrypted data key |
| Modify/Delete | `$.requestId` or `$.error` | string / object | Per spec |

### Expected State Transitions

| Operation | Initial State | Target State | Poll Interval | Max Wait |
|-----------|---------------|--------------|---------------|----------|
| Create Key | — | `Enabled` | 5s | 60s |
| Enable Key | `Disabled` | `Enabled` | 5s | 30s |
| Disable Key | `Enabled` | `Disabled` | 5s | 30s |
| Schedule Deletion | `Enabled`/`Disabled` | `PendingDeletion` | 5s | 30s |
| Delete | `PendingDeletion` | (404 on describe) | 5s | varies (7-30 days per API) |

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.1.0 | 2026-06-04 | **GCL rollout**: Added `## Quality Gate (GCL)` chapter wiring this skill into the repository-wide Generator-Critic-Loop. Added `references/rubric.md` (5-dimension rubric, KMS-specific rules for irreversible `schedule key deletion`, `pending-window-in-days` min-7 guard, prod `disable` / `decrypt` confirm) and `references/prompt-templates.md` (G/C/O prompt skeletons; **plaintext / secret value never logged**, SHA-256 + length only). `max_iterations=2`. `safety_confirm_required=true` for `schedule key deletion`, `disable key` (prod), `decrypt` (prod). |
| 1.0.0 | 2026-05-08 | Initial version with API/SDK and `jdc` CLI dual-path support for JD Cloud KMS (密钥管理服务) |

## Execution Flows (Agent-Readable)

Every operation: **Pre-flight → Execute (jdc primary / SDK fallback) → Validate → Recover**. Do not skip phases.

**jdc-first strategy:** The Agent MUST attempt `jdc` CLI first (primary path). If `jdc` fails after **3 retries** with exponential backoff, fall back to SDK/API. Documentation below lists `jdc` before SDK to reflect execution priority.

### Operation: Create KMS Key

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| CLI / deps | `jdc --version` | Exit code 0 | Retry up to 3 times; then fall back to SDK |
| SDK / deps | `import jdcloud_sdk.services.kms.client.KmsClient` | No import error | Document install pin (fallback path) |
| Credentials | Construct credential from env or CLI config | Non-empty keys | HALT; user configures env |
| Region | Check KMS endpoint availability | `{{user.region}}` supported | Suggest valid region |

#### Execution — CLI (`jdc`) [Primary Path]

**Required** when `cli_applicability: jdc-first-with-fallback`. Use `--output json` at the **top level** (before the subcommand). Do NOT use `--no-interactive` — it is not supported by jdc CLI.

```bash
jdc --output json kms create-key \
  --key-cfg '{"keyName":"{{user.key_name}}","keyUsage":"ENCRYPT_DECRYPT","keySpec":"AES_256"}'
```

> **Note:** `key-cfg` expects a JSON string. Use proper JSON escaping. Key specs include: AES_256, AES_128, RSA_2048, RSA_4096, etc.

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
endpoint = kms.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF
printf "%s" "default" > /tmp/jdc-home/.jdc/current
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.kms.client.KmsClient import KmsClient
from jdcloud_sdk.services.kms.apis.CreateKeyRequest import CreateKeyRequest, CreateKeyParameters

credential = Credential(os.environ["JDC_ACCESS_KEY"], os.environ["JDC_SECRET_KEY"])
client = KmsClient(credential)

# Build key configuration
key_cfg = {
    "keyName": "{{user.key_name}}",
    "keyUsage": "ENCRYPT_DECRYPT",
    "keySpec": "AES_256"
}

params = CreateKeyParameters(regionId="{{user.region}}", keyCfg=key_cfg)
req = CreateKeyRequest(parameters=params)
resp = client.send(req)
key_id = resp.result["keyId"]
```

#### Post-execution Validation

1. Capture `{{output.key_id}}` from `$.result.keyId`.
2. Poll `describeKey` until `status` == `Enabled` or timeout.

```bash
# CLI poll loop (primary path) — --output json at TOP level
for i in $(seq 1 12); do
  STATUS=$(jdc --output json kms describe-key \
    --key-id "{{output.key_id}}" | jq -r '.result.key.status')
  [ "$STATUS" = "Enabled" ] && break
  sleep 5
done
```

```python
# SDK poll loop (fallback, after 3 jdc failures)
from jdcloud_sdk.services.kms.apis.DescribeKeyRequest import DescribeKeyRequest, DescribeKeyParameters

for _ in range(12):
    dparams = DescribeKeyParameters(regionId="{{user.region}}", keyId="{{output.key_id}}")
    dreq = DescribeKeyRequest(parameters=dparams)
    dresp = client.send(dreq)
    status = dresp.result["key"]["status"]
    if status == "Enabled":
        break
    if status in ["Disabled", "PendingDeletion", "Error"]:
        raise RuntimeError(f"Key creation failed: {status}")
    sleep(5)
```

3. On success, report key ID and key metadata to user.
4. On terminal failure, go to **Failure Recovery**.

#### Failure Recovery

| Error pattern | Max retries | Backoff | Agent Action |
|---------------|-------------|---------|--------------|
| `InvalidParameter` / 400 | 0–1 | — | Fix args per OpenAPI; retry once |
| `QuotaExceeded` | 0 | — | HALT; user requests quota increase |
| `KeyAlreadyExists` | 0 | — | Ask reuse vs new name |
| `InsufficientBalance` | 0 | — | HALT; user tops up account |
| Throttling / 429 | 3 | exponential | Back off; respect Retry-After |
| `InternalError` / 5xx | 3 | 2s, 4s, 8s | Retry; HALT with requestId if persists |

### Operation: Describe KMS Key

#### Execution (CLI) [Primary Path]

```bash
jdc --output json kms describe-key \
  --key-id "{{user.key_id}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.kms.apis.DescribeKeyRequest import DescribeKeyRequest, DescribeKeyParameters

params = DescribeKeyParameters(regionId="{{user.region}}", keyId="{{user.key_id}}")
req = DescribeKeyRequest(parameters=params)
resp = client.send(req)
# Access: resp.result["key"]
```

#### Present to User

| Field | JSON Path | Notes |
|-------|-----------|-------|
| Key ID | `$.result.key.keyId` | Plain text |
| Key Name | `$.result.key.keyName` | Plain text |
| Status | `$.result.key.status` | Enabled, Disabled, PendingDeletion |
| Key Usage | `$.result.key.keyUsage` | ENCRYPT_DECRYPT, SIGN_VERIFY |
| Key Spec | `$.result.key.keySpec` | AES_256, RSA_2048, etc. |
| Creation Time | `$.result.key.createTime` | Format ISO per API |

### Operation: List KMS Keys

#### Execution (CLI) [Primary Path]

```bash
jdc --output json kms describe-key-list \
  --page-number 1 \
  --page-size 100
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.kms.apis.DescribeKeyListRequest import DescribeKeyListRequest, DescribeKeyListParameters

params = DescribeKeyListParameters(regionId="{{user.region}}")
params.setPageNumber(1)
params.setPageSize(100)
req = DescribeKeyListRequest(parameters=params)
resp = client.send(req)
keys = resp.result["keys"]
```

### Operation: Encrypt Data

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| Key exists | `describeKey` | Key found and `Enabled` | HALT; verify key ID and status |
| Plaintext ready | User provides data | Base64-encoded data | Encode if needed |

#### Execution (CLI) [Primary Path]

```bash
# Plaintext must be Base64-encoded
jdc --output json kms encrypt \
  --key-id "{{user.key_id}}" \
  --plaintext "{{user.base64_plaintext}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
import base64
from jdcloud_sdk.services.kms.apis.EncryptRequest import EncryptRequest, EncryptParameters

# Encode plaintext to Base64
plaintext_b64 = base64.b64encode("{{user.plaintext_data}}".encode()).decode()

params = EncryptParameters(
    regionId="{{user.region}}",
    keyId="{{user.key_id}}",
    plaintext=plaintext_b64
)
req = EncryptRequest(parameters=params)
resp = client.send(req)
ciphertext = resp.result["ciphertextBlob"]
```

### Operation: Decrypt Data

#### Execution (CLI) [Primary Path]

```bash
jdc --output json kms decrypt \
  --key-id "{{user.key_id}}" \
  --ciphertext-blob "{{user.ciphertext_blob}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.kms.apis.DecryptRequest import DecryptRequest, DecryptParameters

params = DecryptParameters(
    regionId="{{user.region}}",
    keyId="{{user.key_id}}",
    ciphertextBlob="{{user.ciphertext_blob}}"
)
req = DecryptRequest(parameters=params)
resp = client.send(req)
plaintext_b64 = resp.result["plaintext"]
# Decode from Base64
plaintext = base64.b64decode(plaintext_b64).decode()
```

### Operation: Generate Data Key

#### Execution (CLI) [Primary Path]

```bash
jdc --output json kms generate-data-key \
  --key-id "{{user.key_id}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.kms.apis.GenerateDataKeyRequest import GenerateDataKeyRequest, GenerateDataKeyParameters

params = GenerateDataKeyParameters(
    regionId="{{user.region}}",
    keyId="{{user.key_id}}"
)
req = GenerateDataKeyRequest(parameters=params)
resp = client.send(req)
data_key_ciphertext = resp.result["dataKeyCiphertextBlob"]
plaintext_data_key = resp.result.get("plaintextDataKey")  # Optional, may not be returned
```

### Operation: Enable Key

#### Execution (CLI) [Primary Path]

```bash
jdc --output json kms enable-key \
  --key-id "{{user.key_id}}"
```

### Operation: Disable Key

#### Execution (CLI) [Primary Path]

```bash
jdc --output json kms disable-key \
  --key-id "{{user.key_id}}"
```

### Operation: Schedule Key Deletion

#### Pre-flight (Safety Gate)

- **MUST** obtain explicit confirmation: irreversible schedule deletion of `{{user.key_name}}` (`{{user.key_id}}`).
- **MUST** warn user: Key will be deleted after pending window (7-30 days per API).
- **MUST NOT** proceed without clear user assent.

#### Execution (CLI) [Primary Path]

**⚠️ Safety Gate**: MUST obtain explicit user confirmation before executing CLI command.

```bash
jdc --output json kms schedule-key-deletion \
  --key-id "{{user.key_id}}"
```

### Operation: Cancel Key Deletion

#### Execution (CLI) [Primary Path]

```bash
jdc --output json kms cancel-key-deletion \
  --key-id "{{user.key_id}}"
```

### Operation: Create Secret

#### Execution (CLI) [Primary Path]

```bash
jdc --output json kms create-secret \
  --secret-cfg '{"secretName":"{{user.secret_name}}","secretData":"{{user.secret_data}}"}'
```

### Operation: List Secrets

#### Execution (CLI) [Primary Path]

```bash
jdc --output json kms describe-secret-list \
  --page-number 1 \
  --page-size 100
```

## Quality Gate (GCL)

> This skill participates in the repository-wide **Generator-Critic-Loop**
> (GCL) defined in [`AGENTS.md` §Quality Gate](../AGENTS.md#generator-critic-loop-gcl--adversarial-quality-gate).
> The quality gate is **mandatory** for all operations exposed by this skill.

### Parameters (override `AGENTS.md` §8 defaults)

| Parameter | Value | Reason |
|---|---|---|
| `max_iterations` | **2** | `schedule key deletion` is irreversible after waiting period; do not retry repeatedly on production keys |
| `rubric_version` | `v1` | see [rubric.md](references/rubric.md) |
| `trace_path` | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | unified with `jdcloud-audit-ops` |
| `safety_confirm_required` | **true** for `schedule key deletion`, `disable key` (prod), `decrypt` (prod) | matches repository safety gate policy |

### Loop overview

```
User request
   │
   ▼
[0] Orchestrator pre-flight  ──► load rubric, classify operation
   │
   ▼
[1] Generator (G)            ──► jdc (primary) → SDK (after 3 fails)
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
executor. The Critic (C) is a new, read-only role with no `jdc` / SDK
access. The Orchestrator (O) owns the loop and persists the GCL trace.

### Operation-specific behavior

- **`create key`** — Key spec and key usage must be explicit. Default to
  `SYMMETRIC_DEFAULT` + `ENCRYPT_DECRYPT`.
- **`disable key`** — Safety = 0 without `confirm=DISABLE` for keys used
  by production services. For prod-tagged keys, additional
  `confirm=DISABLE_PROD` required.
- **`schedule key deletion`** — **IRREVERSIBLE** after waiting period.
  - Safety = 0 without `confirm=SCHEDULE_DELETE` → ABORT.
  - Default `pending-window-in-days` ≥ 7. Setting < 7 requires
    `confirm=SHORT_WINDOW`.
  - Refuse if key is still referenced by active cloud resources (EBS, RDS,
    etc.) without explicit opt-in.
- **`encrypt` / `decrypt` / `generate data key`** — **NEVER log plaintext**.
  Use SHA-256 + length only. Decrypt on prod key requires
  `confirm=DECRYPT_PROD`.
- **`create secret` / `list secrets`** — Secret value MUST NOT be logged;
  only metadata + SHA-256 of value.

## Prerequisites

> **Python 3.10 is REQUIRED, NOT 3.12.** `jdcloud_cli==1.2.12` uses `SafeConfigParser` which was removed in Python 3.12. Always use `uv venv --python 3.10`. If Python 3.10 is unavailable, install it via `brew install python@3.10` (macOS) or `uv python install 3.10`.

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
endpoint = kms.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF

# 3. Write current profile WITHOUT trailing newline
printf "%s" "default" > /tmp/jdc-home/.jdc/current

# 4. Run jdc with --output json at TOP level
jdc --output json kms describe-key-list --page-number 1 --page-size 100
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

- **Key rotation:** Enable automatic key rotation for frequently-used encryption keys.
- **Least privilege:** IAM policies scoped to required KMS APIs only (encrypt/decrypt vs full key management).
- **Secrets management:** Use KMS secrets for storing sensitive configuration data (passwords, API keys, certificates).
- **Backup:** Export and backup critical keys and secrets; test restore procedures.
- **Audit:** Enable KMS audit logging; review key usage logs regularly.
- **Security:** Use hardware-protected keys (HSM) for high-security scenarios; never store plaintext keys in code or logs.