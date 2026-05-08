# JD Cloud IAM CLI Usage (jdc)

## Overview

This document provides the **CLI-first operational reference** for JD Cloud IAM. The `jdc` CLI is the **primary execution path** for IAM operations. If CLI fails after 3 retries with exponential backoff, fall back to SDK/API.

## Installation and Configuration

### Install jdc CLI

```bash
# Using uv (recommended)
uv pip install jdcloud_cli

# Or using pip
pip install jdcloud_cli

# Verify installation
jdc --version
```

### Configure jdc Credentials

**CRITICAL:** The `jdc` CLI does NOT read `JDC_ACCESS_KEY` / `JDC_SECRET_KEY` environment variables. It reads credentials exclusively from `~/.jdc/config` (INI format).

#### Method 1: Interactive Configuration (Recommended)

```bash
jdc configure add
# Follow prompts to enter:
# - Access Key
# - Secret Key
# - Region ID (default: cn-north-1)
# - Endpoint (default: iam.jdcloud-api.com)
# - Scheme (default: https)
# - Timeout (default: 20)
```

#### Method 2: Manual Config File Creation

For sandboxed environments where `~` is not writable:

```bash
# 1. Set HOME to a writable location
export HOME=/tmp/jdc-home

# 2. Create config directory
mkdir -p /tmp/jdc-home/.jdc

# 3. Write config file
cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = YOUR_ACCESS_KEY_HERE
secret_key = YOUR_SECRET_KEY_HERE
region_id = cn-north-1
endpoint = iam.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF

# 4. Write current profile WITHOUT trailing newline
printf "%s" "default" > /tmp/jdc-home/.jdc/current
```

### CLI Behavioral Notes

**CRITICAL:** The `jdc` CLI has specific constraints that MUST be followed:

#### 1. `--output json` MUST be Top-Level

The `--output` argument is a top-level flag, not a subcommand flag. It MUST be placed **before** the subcommand:

```bash
# CORRECT:
jdc --output json iam describe-sub-users

# WRONG (fails with "unrecognized arguments: --output json"):
jdc iam describe-sub-users --output json
```

#### 2. `--no-interactive` Does NOT Exist

The `jdc` CLI does not support `--no-interactive`. All commands are non-interactive by default. Omit this flag entirely:

```bash
# WRONG (fails with "unrecognized arguments: --no-interactive"):
jdc --output json iam create-sub-user --no-interactive

# CORRECT:
jdc --output json iam create-sub-user
```

#### 3. CLI Reads Credentials from Config File Only

Setting environment variables `JDC_ACCESS_KEY` / `JDC_SECRET_KEY` has NO effect on CLI. The CLI reads credentials from `~/.jdc/config` only.

#### 4. PermissionError on ~/.jdc/ in Sandbox

In sandboxed environments where home is not writable, `jdc` crashes on startup. The fix:
- Set `HOME=/tmp/jdc-home`
- Pre-create `~/.jdc/config` and `~/.jdc/current` files

## IAM CLI Command Reference

### Sub-user Management

#### Create Sub-user

```bash
jdc --output json iam create-sub-user \
  --sub-user-name "dev-user-01" \
  --description "Developer account for project X"
```

**Response:**
```json
{
  "requestId": "...",
  "result": {
    "subUser": {
      "subUserId": "12345",
      "subUserName": "dev-user-01",
      "description": "Developer account for project X",
      "createTime": "2026-05-08T10:00:00+08:00"
    }
  }
}
```

#### Describe Sub-user

```bash
jdc --output json iam describe-sub-user \
  --sub-user-name "dev-user-01"
```

#### List Sub-users

```bash
jdc --output json iam describe-sub-users \
  --page-number 1 \
  --page-size 50
```

#### Update Sub-user

```bash
jdc --output json iam update-sub-user \
  --sub-user-name "dev-user-01" \
  --description "Updated description"
```

#### Delete Sub-user

**⚠️ Safety Gate:** MUST obtain explicit user confirmation before executing.

```bash
# Confirm deletion: "Are you sure you want to delete dev-user-01? This is IRREVERSIBLE."
jdc --output json iam delete-sub-user \
  --sub-user-name "dev-user-01"
```

### Group Management

#### Create Group

```bash
jdc --output json iam create-group \
  --group-name "devops-team" \
  --description "DevOps team group"
```

#### Describe Group

```bash
jdc --output json iam describe-group \
  --group-name "devops-team"
```

#### List Groups

```bash
jdc --output json iam describe-groups \
  --page-number 1 \
  --page-size 50
```

#### Add Sub-user to Group

```bash
jdc --output json iam add-sub-user-to-group \
  --group-name "devops-team" \
  --sub-user-name "dev-user-01"
```

#### Remove Sub-user from Group

```bash
jdc --output json iam remove-sub-user-from-group \
  --group-name "devops-team" \
  --sub-user-name "dev-user-01"
```

#### Delete Group

```bash
jdc --output json iam delete-group \
  --group-name "devops-team"
```

### Role Management

#### Create Role

```bash
jdc --output json iam create-role \
  --role-name "cross-account-role" \
  --description "Cross-account access role" \
  --assume-role-policy-document '{"version":"2018-10-01","statement":[{"effect":"Allow","principal":{"jdcloud":["arn:jdcloud:iam::ACCOUNT_ID:user/*"]},"action":["iam:assumeRole"]}]}'
```

**Note:** `assume-role-policy-document` must be valid JSON defining who can assume this role.

#### Describe Role

```bash
jdc --output json iam describe-role \
  --role-name "cross-account-role"
```

#### List Roles

```bash
jdc --output json iam describe-roles \
  --page-number 1 \
  --page-size 50
```

#### Update Assume Role Policy

```bash
jdc --output json iam update-assume-role-policy \
  --role-name "cross-account-role" \
  --assume-role-policy-document '{"version":"2018-10-01","statement":[]}'
```

#### Delete Role

```bash
jdc --output json iam delete-role \
  --role-name "cross-account-role"
```

### Policy Management

#### Create Policy

```bash
jdc --output json iam create-policy \
  --policy-name "vm-readonly-policy" \
  --description "Read-only access to VM instances" \
  --policy-document '{"version":"2018-10-01","statement":[{"effect":"Allow","action":["vm:describe*"],"resource":["*"]}]}'
```

**Note:** `policy-document` must be valid JSON defining permissions.

#### Describe Policy

```bash
jdc --output json iam describe-policy \
  --policy-name "vm-readonly-policy"
```

#### List Policies

```bash
jdc --output json iam describe-policies \
  --page-number 1 \
  --page-size 50
```

#### Update Policy Description

```bash
jdc --output json iam update-policy-description \
  --policy-name "vm-readonly-policy" \
  --description "Updated description"
```

#### Delete Policy

```bash
jdc --output json iam delete-policy \
  --policy-name "vm-readonly-policy"
```

### Policy Attachment Operations

#### Attach Policy to Sub-user

```bash
jdc --output json iam attach-sub-user-policy \
  --sub-user-name "dev-user-01" \
  --policy-name "vm-readonly-policy"
```

#### Detach Policy from Sub-user

```bash
jdc --output json iam detach-sub-user-policy \
  --sub-user-name "dev-user-01" \
  --policy-name "vm-readonly-policy"
```

#### Attach Policy to Group

```bash
jdc --output json iam attach-group-policy \
  --group-name "devops-team" \
  --policy-name "vm-readonly-policy"
```

#### Detach Policy from Group

```bash
jdc --output json iam detach-group-policy \
  --group-name "devops-team" \
  --policy-name "vm-readonly-policy"
```

#### Attach Policy to Role

```bash
jdc --output json iam attach-role-policy \
  --role-name "cross-account-role" \
  --policy-name "vm-readonly-policy"
```

#### Detach Policy from Role

```bash
jdc --output json iam detach-role-policy \
  --role-name "cross-account-role" \
  --policy-name "vm-readonly-policy"
```

### Access Key (AK/SK) Management

#### Create Main Account AccessKey

```bash
jdc --output json iam create-user-access-key
```

**Response:**
```json
{
  "requestId": "...",
  "result": {
    "accessKey": {
      "accessKeyId": "JDCLOUD-ACCESSKEY-ID",
      "secretKey": "JDCLOUD-SECRETKEY-VALUE",
      "createTime": "2026-05-08T10:00:00+08:00",
      "status": "active"
    }
  }
}
```

**⚠️ CRITICAL:** The `secretKey` value is **only returned once** during creation. Save it securely immediately.

#### List Main Account AccessKeys

```bash
jdc --output json iam describe-user-access-keys
```

#### Disable Main Account AccessKey

```bash
jdc --output json iam disabled-user-access-key \
  --access-key-id "JDCLOUD-ACCESSKEY-ID"
```

#### Enable Main Account AccessKey

```bash
jdc --output json iam enabled-user-access-key \
  --access-key-id "JDCLOUD-ACCESSKEY-ID"
```

#### Delete Main Account AccessKey

```bash
jdc --output json iam delete-user-access-key \
  --access-key-id "JDCLOUD-ACCESSKEY-ID"
```

#### Sub-user AccessKey Operations

Sub-user AK/SK operations follow similar patterns:
- `delete-sub-user-access-key` — Delete sub-user's AK/SK
- `enable-sub-user-access-key` — Enable sub-user's AK/SK
- `disable-sub-user-access-key` — Disable sub-user's AK/SK

### STS (Security Token Service)

#### Assume Role

```bash
jdc --output json sts assume-role \
  --role-name "cross-account-role" \
  --duration-seconds 3600
```

**Response:**
```json
{
  "requestId": "...",
  "result": {
    "credentials": {
      "accessKeyId": "TEMP-AK-ID",
      "secretKey": "TEMP-SK-VALUE",
      "sessionToken": "TEMP-SESSION-TOKEN",
      "expiration": "2026-05-08T11:00:00+08:00"
    }
  }
}
```

**Note:** Temporary credentials expire after `durationSeconds` (default/max varies by role configuration).

## CLI vs API Coverage Gap

| Operation | CLI Support | Notes |
|-----------|-------------|-------|
| Sub-user CRUD | ✓ Full | create, describe, update, delete |
| Group CRUD | ✓ Full | create, describe, update, delete |
| Role CRUD | ✓ Full | create, describe, update assume policy, delete |
| Policy CRUD | ✓ Full | create, describe, update description, delete |
| Policy Attachment | ✓ Full | attach/detach for user, group, role |
| Main Account AK/SK | ✓ Full | create, describe, disable/enable, delete |
| Sub-user AK/SK | ✓ Partial | delete, enable/disable only (no create via CLI) |
| STS assumeRole | ✓ Full | assume-role command |
| MFA Operations | ✓ Partial | bind, unbind, create virtual device, describe |
| SAML assumeRole | ✗ None | SDK/API only for assumeRoleWithSAML |

## Pagination and Filtering

Most `describe-*` commands support pagination:

```bash
jdc --output json iam describe-sub-users \
  --page-number 1 \
  --page-size 50
```

**Response pagination fields:**
- `totalCount` — Total number of records
- `pageNumber` — Current page (1-based)
- `pageSize` — Records per page

## Output Parsing

Use `jq` for JSON parsing:

```bash
# Get sub-user ID from create response
SUBUSER_ID=$(jdc --output json iam create-sub-user ... | jq -r '.result.subUser.subUserId')

# List all sub-user names
jdc --output json iam describe-sub-users | jq -r '.result.subUsers[].subUserName'

# Count sub-users
jdc --output json iam describe-sub-users | jq '.result.totalCount'
```

## Retry Strategy (jdc-first with fallback)

If CLI fails:

1. **Retry 1:** Immediate retry (same command)
2. **Retry 2:** Wait 2 seconds, retry
3. **Retry 3:** Wait 4 seconds, retry with force-reinstall CLI

```bash
# Retry loop example
for i in 0 2 4; do
  sleep $i
  jdc --output json iam describe-sub-users && break
done || echo "CLI failed after 3 retries; falling back to SDK"
```

If all retries fail, fall back to SDK/API (see [api-sdk-usage.md](api-sdk-usage.md)).