# CLI — JD Cloud KMS (`jdc`)

## Install and Config

### Installation

**Install via pip:**
```bash
pip install jdcloud_cli jdcloud_sdk
```

**Or use uv (recommended):**
```bash
uv pip install jdcloud_cli jdcloud_sdk
```

**Verify installation:**
```bash
jdc --version
```

### CLI Configuration (Mandatory)

**CRITICAL**: The `jdc` CLI reads credentials **exclusively** from `~/.jdc/config` (INI format). Environment variables `JDC_ACCESS_KEY` / `JDC_SECRET_KEY` are **ignored** by the CLI.

**Standard configuration (non-sandbox):**
```bash
jdc configure add
# Follow prompts to enter:
# - Access Key
# - Secret Key
# - Region ID (e.g., cn-north-1)
# - Endpoint (e.g., kms.jdcloud-api.com)
```

**Manual configuration (sandbox-safe):**
```bash
# 1. Set HOME to writable location (sandbox workaround)
export HOME=/tmp/jdc-home

# 2. Create config directory
mkdir -p /tmp/jdc-home/.jdc

# 3. Write config file (INI format)
cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = YOUR_ACCESS_KEY
secret_key = YOUR_SECRET_KEY
region_id = cn-north-1
endpoint = kms.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF

# 4. Write current profile (NO trailing newline)
printf "%s" "default" > /tmp/jdc-home/.jdc/current
```

> **Why sandbox workaround**: `ProfileManager.__init__()` calls `os.makedirs("~/.jdc")` which fails in sandboxed environments where HOME is not writable.

## Conventions (Agent Execution)

### Critical CLI Behavioral Notes

**1. `--output json` must be TOP-LEVEL, not subcommand-level**

The `--output` argument is defined in `base_controller.py` (Cement framework), not in individual subcommands.

```
# CORRECT (works):
jdc --output json kms describe-key-list --page-number 1 --page-size 100

# WRONG (fails with "unrecognized arguments: --output json"):
jdc kms describe-key-list --page-number 1 --page-size 100 --output json
```

**Fix:** Always place `--output json` immediately after `jdc`, before the subcommand.

**2. `--no-interactive` does NOT exist**

The `--no-interactive` flag is not defined in jdc CLI. All commands are non-interactive by default.

```
# WRONG (fails with "unrecognized arguments: --no-interactive"):
jdc kms create-key --no-interactive --key-cfg '...'

# CORRECT (no flag needed):
jdc --output json kms create-key --key-cfg '...'
```

**Fix:** Remove `--no-interactive` from all CLI commands.

**3. Credentials must be in config file, not environment variables**

```
# WRONG (environment variables ignored):
export JDC_ACCESS_KEY=xxx
export JDC_SECRET_KEY=yyy
jdc kms describe-key-list

# ERROR: "Please use `jdc configure add` command to add cli configure first."

# CORRECT (config file):
jdc configure add
jdc kms describe-key-list
```

**Fix:** Always use `jdc configure add` or manually create `~/.jdc/config` INI file.

### JSON Path Verification

Document **exact** JSON paths after verifying with a real invocation (CLI output may differ from raw API):

```bash
# Example: describe-key-list
jdc --output json kms describe-key-list --page-number 1 --page-size 10 | jq '.'

# Verify response structure:
{
  "requestId": "...",
  "result": {
    "keys": [
      {
        "keyId": "key-xxx",
        "keyName": "my-key",
        "status": "Enabled",
        ...
      }
    ],
    "totalCount": 10
  }
}
```

> **Best Practice**: Always run a test command and inspect JSON output before documenting paths.

## CLI vs API Coverage Gap

| Operation (API / SDK) | Available via `jdc`? | CLI Command | Notes |
|------------------------|---------------------|-------------|-------|
| Create key | ✓ yes | `kms create-key` | Uses `--key-cfg` JSON parameter |
| Describe key | ✓ yes | `kms describe-key` | Direct mapping |
| List keys | ✓ yes | `kms describe-key-list` | Pagination via `--page-number`, `--page-size` |
| Enable key | ✓ yes | `kms enable-key` | Direct mapping |
| Disable key | ✓ yes | `kms disable-key` | Direct mapping |
| Encrypt | ✓ yes | `kms encrypt` | Plaintext must be Base64-encoded |
| Decrypt | ✓ yes | `kms decrypt` | Ciphertext is Base64-encoded |
| Generate data key | ✓ yes | `kms generate-data-key` | Envelope encryption |
| Key rotation | ✓ yes | `kms key-rotation` | Manual rotation trigger |
| Schedule key deletion | ✓ yes | `kms schedule-key-deletion` | Safety waiting period |
| Cancel key deletion | ✓ yes | `kms cancel-key-deletion` | Cancel scheduled deletion |
| Get public key | ✓ yes | `kms get-public-key` | For asymmetric keys |
| Sign | ✓ yes | `kms sign` | For asymmetric keys |
| Verify | ✓ yes | `kms validate` | For asymmetric keys |
| Create secret | ✓ yes | `kms create-secret` | Uses `--secret-cfg` JSON parameter |
| List secrets | ✓ yes | `kms describe-secret-list` | Pagination supported |
| Delete secret | ✓ yes | `kms delete-secret` | Safety waiting period |
| Enable/disable secret | ✓ yes | `kms enable-secret`, `kms disable-secret` | Direct mapping |

> **Coverage**: jdc CLI provides **full coverage** of JD Cloud KMS API operations. No SDK-only gap.

## Command Map

### Key Management Commands

| Goal | Example `jdc` invocation | Notes |
|------|--------------------------|-------|
| Create symmetric key | `jdc --output json kms create-key --key-cfg '{"keyName":"my-aes-key","keyUsage":"ENCRYPT_DECRYPT","keySpec":"AES_256"}'` | `key-cfg` is JSON string |
| Create asymmetric key | `jdc --output json kms create-key --key-cfg '{"keyName":"my-rsa-key","keyUsage":"SIGN_VERIFY","keySpec":"RSA_2048"}'` | RSA key for signing |
| Describe key | `jdc --output json kms describe-key --key-id "key-abc123def456"` | Returns key metadata |
| List keys | `jdc --output json kms describe-key-list --page-number 1 --page-size 100` | Pagination supported |
| Enable key | `jdc --output json kms enable-key --key-id "key-abc123def456"` | Key must be `Disabled` |
| Disable key | `jdc --output json kms disable-key --key-id "key-abc123def456"` | Key must be `Enabled` |
| Update key description | `jdc --output json kms update-key-description --key-id "key-abc123def456" --description "Updated description"` | Optional |
| Schedule deletion | `jdc --output json kms schedule-key-deletion --key-id "key-abc123def456"` | Enters `PendingDeletion` state |
| Cancel deletion | `jdc --output json kms cancel-key-deletion --key-id "key-abc123def456"` | Restores to `Disabled` |

### Cryptographic Operations

| Goal | Example `jdc` invocation | Notes |
|------|--------------------------|-------|
| Encrypt data | `jdc --output json kms encrypt --key-id "key-abc123" --plaintext "$(echo -n 'Secret data' | base64)"` | Plaintext is Base64-encoded |
| Decrypt data | `jdc --output json kms decrypt --key-id "key-abc123" --ciphertext-blob "base64-ciphertext..."` | Returns Base64 plaintext |
| Generate data key | `jdc --output json kms generate-data-key --key-id "key-abc123"` | Returns plaintext + ciphertext data key |
| Manual key rotation | `jdc --output json kms key-rotation --key-id "key-abc123"` | Creates new key version |

### Asymmetric Key Operations

| Goal | Example `jdc` invocation | Notes |
|------|--------------------------|-------|
| Get public key | `jdc --output json kms get-public-key --key-id "key-rsa2048"` | Returns PEM-encoded public key |
| Sign data | `jdc --output json kms sign --key-id "key-rsa2048" --message "$(echo -n 'Message' | base64)"` | Message is Base64-encoded |
| Verify signature | `jdc --output json kms validate --key-id "key-rsa2048" --message "base64-message" --signature "base64-signature"` | Returns `valid: true/false` |

### Secrets Management Commands

| Goal | Example `jdc` invocation | Notes |
|------|--------------------------|-------|
| Create secret | `jdc --output json kms create-secret --secret-cfg '{"secretName":"db-password","secretData":"my-db-password"}'` | `secret-cfg` is JSON string |
| List secrets | `jdc --output json kms describe-secret-list --page-number 1 --page-size 100` | Pagination supported |
| Delete secret | `jdc --output json kms delete-secret --secret-id "secret-xxx"` | Safety waiting period |
| Enable secret | `jdc --output json kms enable-secret --secret-id "secret-xxx"` | Restores access |
| Disable secret | `jdc --output json kms disable-secret --secret-id "secret-xxx"` | Blocks access |
| Create secret version | `jdc --output json kms create-secret-version --secret-id "secret-xxx" --secret-data "new-password"` | Version management |

## JSON Output Parsing Examples

### CreateKey Response

```bash
jdc --output json kms create-key --key-cfg '{"keyName":"test-key","keyUsage":"ENCRYPT_DECRYPT","keySpec":"AES_256"}' | jq '.'

# Extract keyId:
KEY_ID=$(jdc --output json kms create-key --key-cfg '...' | jq -r '.result.keyId')
echo "Created key: $KEY_ID"
```

### Encrypt Response

```bash
# Encrypt and extract ciphertext
CIPHERTEXT=$(jdc --output json kms encrypt \
  --key-id "key-abc123" \
  --plaintext "$(echo -n 'Secret' | base64)" | jq -r '.result.ciphertextBlob')

echo "Ciphertext: $CIPHERTEXT"
```

### Decrypt Response

```bash
# Decrypt and decode plaintext
PLAINTEXT_B64=$(jdc --output json kms decrypt \
  --key-id "key-abc123" \
  --ciphertext-blob "$CIPHERTEXT" | jq -r '.result.plaintext')

PLAINTEXT=$(echo "$PLAINTEXT_B64" | base64 -d)
echo "Decrypted: $PLAINTEXT"
```

## Batch Operations via Shell Scripts

### Create Multiple Keys

```bash
#!/bin/bash
# Create 5 encryption keys
for i in {1..5}; do
  jdc --output json kms create-key \
    --key-cfg "{\"keyName\":\"batch-key-$i\",\"keyUsage\":\"ENCRYPT_DECRYPT\",\"keySpec\":\"AES_256\"}" \
    | jq -r '.result.keyId'
  sleep 1  # Avoid rate limiting
done
```

### Encrypt Multiple Files

```bash
#!/bin/bash
KEY_ID="key-abc123def456"

for file in *.txt; do
  # Read file, encode to Base64
  PLAINTEXT_B64=$(base64 -w 0 "$file")
  
  # Encrypt
  CIPHERTEXT=$(jdc --output json kms encrypt \
    --key-id "$KEY_ID" \
    --plaintext "$PLAINTEXT_B64" | jq -r '.result.ciphertextBlob')
  
  # Save encrypted file
  echo "$CIPHERTEXT" > "${file}.encrypted"
done
```

## Troubleshooting CLI Commands

### Common CLI Errors

**Error 1: "unrecognized arguments: --output json"**

```
$ jdc kms describe-key-list --output json
unrecognized arguments: --output json
```

**Fix:** Move `--output json` to top level:
```bash
jdc --output json kms describe-key-list
```

**Error 2: "Please use `jdc configure add` command to add cli configure first"**

```
$ jdc kms describe-key-list
Please use `jdc configure add` command to add cli configure first.
```

**Fix:** Configure credentials via `jdc configure add` or create `~/.jdc/config` INI file.

**Error 3: PermissionError on ~/.jdc/ creation (sandbox)**

```
PermissionError: [Errno 13] Permission denied: '~/.jdc'
```

**Fix:** Set HOME to writable location:
```bash
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc
# Create config files...
```

### Debug Mode

Enable verbose logging (if supported by jdc version):
```bash
jdc --output json kms describe-key-list --debug  # If available
```

Or inspect HTTP requests via SDK (fallback):
```python
# SDK mode for debugging
import logging
logging.basicConfig(level=logging.DEBUG)
# Make SDK call...
```

## CLI Performance Tips

1. **Batch Operations**: Use shell loops with `sleep` to avoid rate limits
2. **JSON Processing**: Use `jq` for fast JSON parsing (install: `brew install jq` or `apt-get install jq`)
3. **Reuse Config**: Configure once; reuse profile for multiple calls
4. **Internal Endpoint**: For VPC workloads, use internal endpoint in config for better performance

## Integration with Other Tools

### Ansible

```yaml
- name: Encrypt secret data
  shell: |
    jdc --output json kms encrypt \
      --key-id "{{ kms_key_id }}" \
      --plaintext "{{ secret_data | b64encode }}" \
      | jq -r '.result.ciphertextBlob'
  register: encrypted_data
```

### Terraform

Use JD Cloud Terraform provider for KMS resource management (not direct CLI calls):
- https://registry.terraform.io/providers/jdcloud/jdcloud/

## References

- Official CLI Documentation: https://docs.jdcloud.com/cn/cli/introduction
- KMS API Overview: https://docs.jdcloud.com/cn/key-management-service/api/overview
- CLI GitHub: https://github.com/jdcloud-api/jdcloud-cli