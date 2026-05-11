# Troubleshooting Guide — JD Cloud KMS

## Common API Error Codes

| Code / HTTP | Meaning | Agent Action |
|-------------|---------|--------------|
| `InvalidParameter` / 400 | Request parameter invalid or missing | Align body with OpenAPI; fix parameter names/values |
| `KeyNotFound` / 404 | Key ID does not exist or has been deleted | HALT; verify key ID exists via `describeKey` |
| `SecretNotFound` / 404 | Secret ID does not exist or has been deleted | HALT; verify secret ID exists via `describeSecretList` |
| `KeyDisabled` / 403 | Key is in `Disabled` state, cannot perform cryptographic operations | Enable key via `enableKey` first |
| `KeyPendingDeletion` / 403 | Key is scheduled for deletion | Cancel deletion via `cancelKeyDeletion` or use different key |
| `KeyStateConflict` / 409 | Key state transition invalid (e.g., enable an already-enabled key) | Check current state via `describeKey` |
| `Unauthorized` / 401 | Invalid Access Key or Secret Key | HALT; user configures valid credentials |
| `AccessDenied` / 403 | IAM policy does not grant required permissions | HALT; user grants KMS permissions via IAM |
| `QuotaExceeded` / 400 | Key quota exceeded for region/account | HALT; user requests quota increase from JD Cloud support |
| `RateLimitExceeded` / 429 | Too many API requests in short time | Retry with exponential backoff; respect `Retry-After` header if present |
| `InternalError` / 500 | JD Cloud server error | Retry up to 3 times with exponential backoff (2s, 4s, 8s); HALT if persists |
| `ServiceUnavailable` / 503 | KMS service temporarily unavailable | Retry after delay; check JD Cloud status page |
| `InsufficientBalance` / 400 | Account balance insufficient | HALT; user tops up account |

## CLI Error Patterns

### Error: "unrecognized arguments: --output json"

**Root Cause:** `--output json` is a top-level argument (defined in base controller), not a subcommand-level flag.

**Diagnostic:**
```bash
$ jdc kms describe-key-list --output json
unrecognized arguments: --output json
```

**Fix:**
```bash
# Move --output json to top level (before subcommand)
jdc --output json kms describe-key-list
```

### Error: "unrecognized arguments: --no-interactive"

**Root Cause:** `--no-interactive` flag does NOT exist in jdc CLI. All commands are non-interactive by default.

**Diagnostic:**
```bash
$ jdc kms create-key --no-interactive --key-cfg '...'
unrecognized arguments: --no-interactive
```

**Fix:** Remove `--no-interactive` flag entirely:
```bash
jdc --output json kms create-key --key-cfg '...'
```

### Error: "Please use `jdc configure add` command to add cli configure first"

**Root Cause:** jdc CLI reads credentials exclusively from `~/.jdc/config` INI file. Environment variables `JDC_ACCESS_KEY` / `JDC_SECRET_KEY` are **ignored**.

**Diagnostic:**
```bash
$ export JDC_ACCESS_KEY=xxx
$ export JDC_SECRET_KEY=yyy
$ jdc kms describe-key-list
Please use `jdc configure add` command to add cli configure first.
```

**Fix:**
```bash
# Option 1: Use jdc configure add (interactive)
jdc configure add

# Option 2: Manually create config file
mkdir -p ~/.jdc
cat > ~/.jdc/config << 'CONFIGEOF'
[default]
access_key = YOUR_ACCESS_KEY
secret_key = YOUR_SECRET_KEY
region_id = cn-north-1
endpoint = kms.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF
printf "%s" "default" > ~/.jdc/current
```

### Error: `PermissionError` on ~/.jdc/ directory creation

**Root Cause:** `ProfileManager.__init__()` calls `os.makedirs("~/.jdc")`. In sandboxed environments where HOME is read-only, this fails.

**Diagnostic:**
```bash
$ jdc kms describe-key-list
PermissionError: [Errno 13] Permission denied: '/home/readonly/.jdc'
```

**Fix (sandbox-safe):**
```bash
# Redirect HOME to writable location
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc

# Create config files
cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = YOUR_ACCESS_KEY
secret_key = YOUR_SECRET_KEY
region_id = cn-north-1
endpoint = kms.jdcloud-api.com
CONFIGEOF
printf "%s" "default" > /tmp/jdc-home/.jdc/current

# Run jdc
jdc --output json kms describe-key-list
```

## Diagnostic Order

### Key Operations Troubleshooting

**Step 1: Describe key by ID**
```bash
jdc --output json kms describe-key --key-id "{{user.key_id}}"
```
Check:
- Does key exist? (`KeyNotFound` → HALT)
- Key status: `Enabled` (OK), `Disabled` (need to enable), `PendingDeletion` (cancel deletion)

**Step 2: Check key state**
- If cryptographic operation fails, verify key is `Enabled`
- If deletion operation fails, verify key is NOT `PendingDeletion` or already deleted

**Step 3: Check key permissions**
- IAM policy must grant `kms:Encrypt`, `kms:Decrypt`, etc. for user's Access Key
- Use JD Cloud IAM console to verify permissions

**Step 4: Check region**
- Ensure `region_id` matches key's region (keys are regional, not global)
- Common mistake: Key created in cn-north-1, but call from cn-east-2

### Encryption/Decryption Troubleshooting

**Encrypt failure:**

1. **Check key ID exists:**
   ```bash
   jdc --output json kms describe-key --key-id "{{user.key_id}}"
   ```

2. **Check key status:**
   - Key must be `Enabled`
   - If `Disabled`, run: `jdc kms enable-key --key-id "..."`
   - If `PendingDeletion`, cancel deletion or use different key

3. **Check plaintext encoding:**
   - Plaintext MUST be Base64-encoded before passing to API/CLI
   - Example: `echo -n "Secret" | base64` → `U2VjcmV0`

4. **Check key usage:**
   - Key must have `keyUsage: ENCRYPT_DECRYPT` (symmetric keys)
   - Asymmetric keys (`SIGN_VERIFY`) cannot encrypt data (use `sign` instead)

**Decrypt failure:**

1. **Check ciphertext format:**
   - Ciphertext must be Base64-encoded string
   - No corruption or truncation

2. **Check key ID matches:**
   - Ciphertext contains metadata pointing to original key
   - Decrypt must use same key ID (or key alias pointing to same key)

3. **Check key status:**
   - Key must be `Enabled` or `Disabled` (can decrypt with disabled keys)
   - Cannot decrypt with `PendingDeletion` keys

4. **Check data format:**
   - Ensure ciphertext blob is from KMS `encrypt` operation, not custom encryption

### Key Deletion Troubleshooting

**ScheduleDeletion failure:**

1. **Check key state:**
   - Key must be `Enabled` or `Disabled`
   - Cannot schedule deletion if already `PendingDeletion`

2. **Check IAM permissions:**
   - Must have `kms:ScheduleKeyDeletion` permission

3. **Check deletion window:**
   - API may require explicit pending window parameter (check OpenAPI)

**CancelDeletion failure:**

1. **Check key state:**
   - Key must be `PendingDeletion`
   - Cannot cancel if key is already deleted (404)

2. **Check IAM permissions:**
   - Must have `kms:CancelKeyDeletion` permission

### Secrets Management Troubleshooting

**Secret creation failure:**

1. **Check secret name uniqueness:**
   - Secret names must be unique within region/account
   - Use different name or delete existing secret first

2. **Check secret data encoding:**
   - Secret data may need Base64 encoding (check API)

3. **Check IAM permissions:**
   - Must have `kms:CreateSecret` permission

**Secret access failure:**

1. **Check secret state:**
   - Secret must be `Enabled`
   - If `Disabled`, run: `jdc kms enable-secret --secret-id "..."`
   - If `PendingDeletion`, cancel deletion

2. **Check secret ID:**
   - Verify secret ID via `describeSecretList`

## Regional Endpoint Issues

**Symptom:** API calls return 404 or timeout for certain regions.

**Diagnostic:**
1. Check KMS endpoint for target region:
   - cn-north-1: `kms.cn-north-1.jdcloud-api.com`
   - cn-east-2: `kms.cn-east-2.jdcloud-api.com`
   - cn-south-1: `kms.cn-south-1.jdcloud-api.com`

2. Check region ID matches:
   - Keys are **regional resources** (created in specific region)
   - API calls must use same region ID as key

3. Use internal endpoints for VPC:
   - Internal: `kms.internal.cn-north-1.jdcloud-api.com` (for VPC callers)
   - Public: `kms.cn-north-1.jdcloud-api.com` (for external callers)

## Performance Issues

**Slow encrypt/decrypt operations:**

1. **Use envelope encryption:**
   - For large data (>4KB), use `generateDataKey` instead of direct encrypt
   - Encrypt data locally with data key, store only encrypted data key in KMS

2. **Batch operations:**
   - Avoid encrypting multiple small pieces separately
   - Combine data into single encryption operation

3. **Internal endpoint:**
   - Use internal VPC endpoint for better performance if calling from JD Cloud VPC

4. **Cache encrypted data keys:**
   - For repetitive encryption, reuse data keys (cache encrypted data key)
   - Decrypt cached data key to get plaintext data key for local encryption

## Rate Limiting

**Symptom:** `RateLimitExceeded` / 429 errors on high-volume operations.

**Diagnostic:**
1. Check operation type:
   - Encrypt/decrypt: Higher rate limit (thousands per second)
   - CreateKey/DeleteKey: Lower rate limit (tens per second)

2. Monitor request frequency:
   - Track API calls per second

**Fix:**
- Add exponential backoff: retry after 1s, 2s, 4s delays
- Respect `Retry-After` header if provided
- Use envelope encryption to reduce encrypt/decrypt API calls
- Distribute load across multiple keys (if applicable)

## IAM Permission Errors

**Symptom:** `AccessDenied` / 403 despite valid credentials.

**Diagnostic:**
1. Check IAM policy:
   - Does user's IAM role have required KMS permissions?
   - Example: `kms:Encrypt`, `kms:Decrypt`, `kms:DescribeKey`

2. Check resource scope:
   - IAM policy may restrict access to specific key IDs
   - Wildcard (`*`) grants access to all keys in region

**Fix:**
- Grant required permissions via JD Cloud IAM console
- Create IAM policy with required actions:
  ```json
  {
    "Version": "2019-05-01",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:DescribeKey"
        ],
        "Resource": "kms:cn-north-1:*"
      }
    ]
  }
  ```

## Security Best Practices Violations

**Hardcoded credentials in code:**
- **Issue**: Storing Access Key / Secret Key in source code
- **Fix**: Use environment variables or KMS secrets for credential storage

** plaintext data keys persisted:**
- **Issue**: Storing plaintext data keys in files or databases
- **Fix**: Never persist plaintext data keys; store only encrypted data keys, decrypt on-demand

**Key reuse across environments:**
- **Issue**: Using same key for production and development
- **Fix**: Create separate keys per environment (prod, dev, test)

**Disabled key used for encryption:**
- **Issue**: Attempting encrypt with `Disabled` key
- **Fix**: Enable key before encryption operations

## Additional Diagnostic Commands

**Verify KMS service availability:**
```bash
jdc --output json kms describe-key-list --page-number 1 --page-size 1
```
- If succeeds, KMS service is available
- If fails with 503, check JD Cloud status page

**Verify credentials:**
```bash
# CLI mode: check config file exists (DO NOT print actual values)
test -f ~/.jdc/config && echo "CLI config OK" || echo "CLI config missing"

# SDK mode: check environment variables exist (DO NOT print actual values)
# SECURITY: Never print JDC_SECRET_KEY value
if [ -n "$JDC_ACCESS_KEY" ] && [ -n "$JDC_SECRET_KEY" ]; then
    echo "SDK credentials OK (JDC_SECRET_KEY=<masked>)"
else
    echo "Missing JDC_ACCESS_KEY or JDC_SECRET_KEY"
fi
```

> **SECURITY WARNING:** **NEVER** print or log the actual value of `JDC_SECRET_KEY`. The verification above only checks **existence** of credentials, not their values. If you need to log credential status, use masked placeholders like `JDC_SECRET_KEY=<masked>` or `JDC_SECRET_KEY=***`.

**Check key metadata:**
```bash
jdc --output json kms describe-key --key-id "{{user.key_id}}" | jq '.result.key'
```

## Support and Resources

- JD Cloud KMS Documentation: https://docs.jdcloud.com/cn/key-management-service/introduction
- JD Cloud CLI Documentation: https://docs.jdcloud.com/cn/cli/introduction
- JD Cloud IAM Documentation: https://docs.jdcloud.com/cn/iam/introduction
- JD Cloud Support: https://www.jdcloud.com/support