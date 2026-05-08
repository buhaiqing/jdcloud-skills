# IAM Troubleshooting Guide

## Common Error Codes

| HTTP Status | Error Code | Meaning | Agent Action |
|-------------|------------|---------|--------------|
| 400 | `InvalidParameter` | Request parameter validation failed | Fix parameters per OpenAPI spec; retry once |
| 400 | `SubUserAlreadyExists` | Sub-user with same name already exists | Ask user: reuse existing or create with new name? |
| 400 | `GroupAlreadyExists` | Group with same name already exists | Ask user: reuse existing or create with new name? |
| 400 | `RoleAlreadyExists` | Role with same name already exists | Ask user: reuse existing or create with new name? |
| 400 | `PolicyAlreadyExists` | Policy with same name already exists | Ask user: reuse existing or create with new name? |
| 400 | `InvalidPolicyDocument` | Policy JSON is malformed or invalid | Fix policy syntax per IAM policy grammar |
| 400 | `InvalidAssumeRolePolicy` | Assume role policy JSON is malformed | Fix assume role policy syntax |
| 400 | `SubUserLimitExceeded` | Sub-user quota limit reached | HALT; user requests quota increase |
| 400 | `GroupLimitExceeded` | Group quota limit reached | HALT; user requests quota increase |
| 400 | `RoleLimitExceeded` | Role quota limit reached | HALT; user requests quota increase |
| 400 | `PolicyLimitExceeded` | Policy quota limit reached | HALT; user requests quota increase |
| 400 | `AccessKeyLimitExceeded` | AK/SK per sub-user limit reached (default: 2) | HALT; delete old keys first |
| 403 | `PermissionDenied` | Caller lacks required IAM permission | HALT; user adjusts caller's IAM permissions |
| 403 | `InvalidAccessKey` | AccessKey is invalid, disabled, or deleted | HALT; user checks AK/SK status |
| 403 | `AccessKeyDisabled` | AccessKey is disabled | HALT; user enables the AccessKey |
| 403 | `AssumeRoleDenied` | Caller not authorized to assume role | HALT; role's assume policy must include caller |
| 403 | `OperationProtectionRequired` | MFA required for sensitive operation | HALT; user must provide MFA token |
| 404 | `SubUserNotFound` | Sub-user does not exist | HALT; verify sub-user name or ID |
| 404 | `GroupNotFound` | Group does not exist | HALT; verify group name |
| 404 | `RoleNotFound` | Role does not exist | HALT; verify role name |
| 404 | `PolicyNotFound` | Policy does not exist | HALT; verify policy name |
| 404 | `AccessKeyNotFound` | AccessKey does not exist | HALT; verify AccessKey ID |
| 409 | `QuotaExceeded` | Resource quota limit reached | HALT; user requests quota increase |
| 409 | `ResourceConflict` | Concurrent modification conflict | Retry with exponential backoff |
| 429 | `Throttling` | API rate limit exceeded | Retry with exponential backoff; respect Retry-After header |
| 500 | `InternalError` | JD Cloud server internal error | Retry 3 times (2s, 4s, 8s); HALT with requestId if persists |
| 502 | `BadGateway` | Network/gateway error | Retry with exponential backoff |
| 503 | `ServiceUnavailable` | Service temporarily unavailable | Retry with exponential backoff |

## Diagnostic Order

### General Diagnostic Steps

1. **Verify credentials**
   - Ensure AK/SK are valid and active (not disabled)
   - Check AK/SK have sufficient IAM permissions
   - Verify environment variables or CLI config file

2. **Verify resource existence**
   - Call `describe` API/CLI to confirm resource exists
   - Check resource name spelling (case-sensitive)
   - Verify resource ID if using ID-based operations

3. **Verify permissions**
   - Check caller's attached policies
   - Ensure caller has required action permission (e.g., `iam:createSubUser`)
   - Verify permission scope (resource level if applicable)

4. **Check quotas**
   - Verify sub-user/group/role/policy count limits
   - Check AK/SK per sub-user limit (default: 2)
   - Request quota increase if needed

5. **Validate input parameters**
   - Ensure JSON policy documents are valid syntax
   - Check assume role policy principal format
   - Verify action/resource names per IAM grammar

6. **Check endpoint and region**
   - IAM is global service; region may not apply
   - Verify endpoint: `iam.jdcloud-api.com`
   - Check network connectivity to endpoint

### CLI-Specific Diagnostics

#### Problem: `jdc` command not found

**Symptom:** `jdc: command not found`

**Diagnosis:**
1. Verify `jdcloud_cli` installed: `pip list | grep jdcloud_cli`
2. Check virtual environment activation: `which python`
3. Ensure PATH includes pip install location

**Fix:**
```bash
source .venv/bin/activate
uv pip install jdcloud_cli
jdc --version
```

#### Problem: `unrecognized arguments: --output json`

**Symptom:** CLI rejects `--output json` when placed after subcommand

**Root Cause:** `--output` is a top-level flag, not subcommand flag

**Fix:** Move `--output json` to top level (before subcommand):
```bash
# WRONG:
jdc iam describe-sub-users --output json

# CORRECT:
jdc --output json iam describe-sub-users
```

#### Problem: `Please use 'jdc configure add' command to add cli configure first`

**Symptom:** CLI fails even with env vars set

**Root Cause:** CLI does NOT read environment variables `JDC_ACCESS_KEY` / `JDC_SECRET_KEY`

**Fix:** Create `~/.jdc/config` INI file:
```bash
mkdir -p ~/.jdc
cat > ~/.jdc/config << 'CONFIGEOF'
[default]
access_key = YOUR_ACCESS_KEY
secret_key = YOUR_SECRET_KEY
region_id = cn-north-1
endpoint = iam.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF
printf "%s" "default" > ~/.jdc/current
```

#### Problem: `PermissionError: [Errno 13] Permission denied: '~/.jdc'`

**Symptom:** CLI crashes on startup in sandboxed environment

**Root Cause:** Home directory is not writable; CLI tries to create `~/.jdc/`

**Fix:** Redirect `HOME` and pre-create config:
```bash
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc
# ... create config files as above
```

### SDK-Specific Diagnostics

#### Problem: `ModuleNotFoundError: No module named 'jdcloud_sdk'`

**Diagnosis:** SDK not installed or virtual environment not activated

**Fix:**
```bash
source .venv/bin/activate
uv pip install jdcloud_sdk
python -c "import jdcloud_sdk; print('OK')"
```

#### Problem: `AttributeError: module 'jdcloud_sdk' has no attribute '__version__'`

**Diagnosis:** SDK does not expose `__version__` attribute

**Fix:** Ignore version check; verify functionality:
```python
import jdcloud_sdk
from jdcloud_sdk.services.iam.client.IamClient import IamClient
print("SDK OK")
```

#### Problem: `JdcloudSDKException: status_code=403, code=PermissionDenied`

**Diagnosis:** Caller's AK/SK lacks required IAM permission

**Fix:**
1. Check caller's attached policies: `jdc --output json iam describe-attached-sub-user-policies`
2. Add required permission policy: e.g., `iam:createSubUser`, `iam:createPolicy`
3. Ensure policy Effect="Allow" and Action includes required operation

#### Problem: `JdcloudSDKException: status_code=404, code=SubUserNotFound`

**Diagnosis:** Sub-user name does not exist (case-sensitive)

**Fix:**
1. List sub-users to verify: `jdc --output json iam describe-sub-users`
2. Check spelling and case
3. Create sub-user if needed

### Permission-Related Issues

#### Problem: Cannot create sub-user despite having IAM permissions

**Symptom:** 403 PermissionDenied on `createSubUser`

**Possible Causes:**
1. Caller lacks `iam:createSubUser` action
2. Caller's policy has resource-level restriction (e.g., specific sub-user names)
3. Account quota exceeded

**Diagnosis:**
```bash
# Check caller's permissions
jdc --output json iam describe-attached-sub-user-policies --sub-user-name "caller-name"

# Check account quota (via describe-sub-users totalCount)
jdc --output json iam describe-sub-users | jq '.result.totalCount'
```

**Fix:**
1. Attach policy with `iam:createSubUser` action
2. Request quota increase if limit reached

#### Problem: Cannot assume role despite having AssumeRole permission

**Symptom:** 403 AssumeRoleDenied

**Root Cause:** Role's assume policy does not include caller as principal

**Diagnosis:**
```bash
# Check role's assume policy
jdc --output json iam describe-role --role-name "target-role"
# Parse assumeRolePolicyDocument to verify principal
```

**Fix:** Update role's assume policy to include caller:
```json
{
  "version": "2018-10-01",
  "statement": [
    {
      "effect": "Allow",
      "principal": {
        "jdcloud": ["arn:jdcloud:iam::CALLER_ACCOUNT_ID:user/caller-name"]
      },
      "action": ["iam:assumeRole"]
    }
  ]
}
```

### Policy Validation Issues

#### Problem: `InvalidPolicyDocument` error on createPolicy

**Symptom:** 400 InvalidPolicyDocument

**Possible Causes:**
1. JSON syntax error (missing braces, quotes)
2. Missing required fields (version, statement, effect, action)
3. Invalid action/resource names
4. Invalid condition syntax

**Diagnosis:** Validate policy JSON structure:
- Required fields: `version`, `statement` (array)
- Statement required fields: `effect` ("Allow" or "Deny"), `action` (array)
- Optional fields: `resource`, `condition`

**Fix Example:**
```json
{
  "version": "2018-10-01",
  "statement": [
    {
      "effect": "Allow",
      "action": ["vm:describeInstance"],
      "resource": ["*"]
    }
  ]
}
```

**Common Mistakes:**
- Wrong: `"effect": "allow"` (must be capitalized: `"Allow"`)
- Wrong: `"action": "vm:describeInstance"` (must be array: `["vm:describeInstance"]`)
- Wrong: `"version": "1"` (must be `"2018-10-01"`)

### AK/SK Management Issues

#### Problem: Created AccessKey but forgot to save SecretKey

**Symptom:** Lost SecretKey after creation

**Root Cause:** SecretKey is only returned once during creation

**Fix:** SecretKey cannot be retrieved; create new AccessKey:
```bash
jdc --output json iam create-user-access-key
# Save SecretKey IMMEDIATELY
```

Then delete old AccessKey:
```bash
jdc --output json iam delete-user-access-key --access-key-id "OLD-AK-ID"
```

#### Problem: AccessKey disabled but need to enable

**Symptom:** API calls fail with `AccessKeyDisabled`

**Fix:**
```bash
jdc --output json iam enabled-user-access-key --access-key-id "YOUR-AK-ID"
```

#### Problem: Too many AccessKeys per sub-user

**Symptom:** 400 AccessKeyLimitExceeded

**Root Cause:** Sub-user AK/SK limit reached (default: 2)

**Fix:** Delete old keys before creating new:
```bash
jdc --output json iam describe-sub-user-access-keys
jdc --output json iam delete-sub-user-access-key --access-key-id "OLD-AK-ID"
jdc --output json iam create-user-access-key  # Then create new
```

## Error Response Structure

IAM API errors follow standard JD Cloud error format:

```json
{
  "requestId": "abc123-def456-ghi789",
  "error": {
    "status": "BAD_REQUEST",
    "code": "InvalidParameter",
    "message": "Parameter 'subUserName' is required"
  }
}
```

**Key Fields:**
- `requestId` — Unique request identifier (for support tickets)
- `error.status` — HTTP status text (e.g., "BAD_REQUEST", "FORBIDDEN")
- `error.code` — Error code (e.g., "InvalidParameter", "PermissionDenied")
- `error.message` — Human-readable error description

## Retry Strategy

### Retryable Errors

- 500 InternalError
- 502 BadGateway
- 503 ServiceUnavailable
- 504 GatewayTimeout
- 429 Throttling

### Non-Retryable Errors

- 400 InvalidParameter (fix parameters)
- 403 PermissionDenied (fix permissions)
- 404 NotFound (verify resource)
- 409 QuotaExceeded (request quota)

### Retry Implementation

```bash
# CLI retry loop
for i in 0 2 4; do
  sleep $i
  jdc --output json iam describe-sub-users && break
done

# SDK retry (Python)
for attempt in range(3):
  try:
    resp = client.send(req)
    break
  except Exception as e:
    if attempt < 2 and is_retryable(e):
      time.sleep(2 ** attempt)
      continue
    raise
```

## Contact Support

If troubleshooting fails:
- Collect `requestId` from error response
- Document operation, parameters, and timestamps
- Contact JD Cloud support: https://docs.jdcloud.com/cn/common/contact-us