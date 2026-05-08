# API & SDK — JD Cloud KMS

## OpenAPI Specification

- **API Version**: v1
- **Base Path**: `https://kms.jdcloud-api.com/v1`
- **Protocol**: HTTPS (TLS 1.2+)
- **Style**: RESTful RPC
- **Official Documentation**: https://docs.jdcloud.com/cn/key-management-service/api/overview

## SDK Package

**Python SDK:**
```python
from jdcloud_sdk.services.kms.client.KmsClient import KmsClient
```

**Package Installation:**
```bash
pip install jdcloud_sdk
```

**GitHub Repository:**
https://github.com/jdcloud-api/jdcloud-sdk-python

## API Operations Map

### Key Management Operations

| Goal | API operationId | SDK Request Class | CLI Command |
|------|-----------------|-------------------|-------------|
| Create key | createKey | CreateKeyRequest | `kms create-key` |
| Describe key | describeKey | DescribeKeyRequest | `kms describe-key` |
| List keys | describeKeyList | DescribeKeyListRequest | `kms describe-key-list` |
| Enable key | enableKey | EnableKeyRequest | `kms enable-key` |
| Disable key | disableKey | DisableKeyRequest | `kms disable-key` |
| Update key description | updateKeyDescription | UpdateKeyDescriptionRequest | `kms update-key-description` |
| Schedule key deletion | scheduleKeyDeletion | ScheduleKeyDeletionRequest | `kms schedule-key-deletion` |
| Cancel key deletion | cancelKeyDeletion | CancelKeyDeletionRequest | `kms cancel-key-deletion` |

### Cryptographic Operations

| Goal | API operationId | SDK Request Class | CLI Command |
|------|-----------------|-------------------|-------------|
| Encrypt data | encrypt | EncryptRequest | `kms encrypt` |
| Decrypt data | decrypt | DecryptRequest | `kms decrypt` |
| Generate data key | generateDataKey | GenerateDataKeyRequest | `kms generate-data-key` |
| Get public key | getPublicKey | GetPublicKeyRequest | `kms get-public-key` |
| Sign data | sign | SignRequest | `kms sign` |
| Verify signature | validate | ValidateRequest | `kms validate` |

### Key Version Operations

| Goal | API operationId | SDK Request Class | CLI Command |
|------|-----------------|-------------------|-------------|
| Describe key detail | describeKeyDetail | DescribeKeyDetailRequest | `kms describe-key-detail` |
| Enable key version | enableKeyVersion | EnableKeyVersionRequest | `kms enable-key-version` |
| Disable key version | disableKeyVersion | DisableKeyVersionRequest | `kms disable-key-version` |
| Schedule key version deletion | scheduleKeyVersionDeletion | ScheduleKeyVersionDeletionRequest | `kms schedule-key-version-deletion` |
| Cancel key version deletion | cancelKeyVersionDeletion | CancelKeyVersionDeletionRequest | `kms cancel-key-version-deletion` |

### Secrets Management Operations

| Goal | API operationId | SDK Request Class | CLI Command |
|------|-----------------|-------------------|-------------|
| Create secret | createSecret | CreateSecretRequest | `kms create-secret` |
| Delete secret | deleteSecret | DeleteSecretRequest | `kms delete-secret` |
| List secrets | describeSecretList | DescribeSecretListRequest | `kms describe-secret-list` |
| Enable secret | enableSecret | EnableSecretRequest | `kms enable-secret` |
| Disable secret | disableSecret | DisableSecretRequest | `kms disable-secret` |
| Update secret | updateSecret | UpdateSecretRequest | `kms update-secret` |
| Create secret version | createSecretVersion | CreateSecretVersionRequest | `kms create-secret-version` |
| Describe secret version info | describeSecretVersionInfo | DescribeSecretVersionInfoRequest | `kms describe-secret-version-info` |
| Describe secret version list | describeSecretVersionList | DescribeSecretVersionListRequest | `kms describe-secret-version-list` |
| Update secret version | updateSecretVersion | UpdateSecretVersionRequest | `kms update-secret-version` |
| Enable secret version | enableSecretVersion | EnableSecretVersionRequest | `kms enable-secret-version` |
| Disable secret version | disableSecretVersion | DisableSecretVersionRequest | `kms disable-secret-version` |

## Request/Response Examples

### CreateKey

**Request Structure:**
```python
from jdcloud_sdk.services.kms.apis.CreateKeyRequest import CreateKeyRequest, CreateKeyParameters

key_cfg = {
    "keyName": "my-encryption-key",
    "keyUsage": "ENCRYPT_DECRYPT",
    "keySpec": "AES_256",
    "description": "Key for encrypting application data"
}

params = CreateKeyParameters(regionId="cn-north-1", keyCfg=key_cfg)
req = CreateKeyRequest(parameters=params)
resp = client.send(req)
```

**Response Structure:**
```json
{
  "requestId": "xxxx-xxxx-xxxx-xxxx",
  "result": {
    "keyId": "key-abc123def456",
    "keyName": "my-encryption-key",
    "status": "Enabled",
    "keyUsage": "ENCRYPT_DECRYPT",
    "keySpec": "AES_256",
    "createTime": "2026-05-08T10:00:00Z"
  }
}
```

**Key Fields:**
- `keyId` (string): Unique identifier for the created key
- `status` (string): Initial state is `Enabled`
- `keyUsage` (string): Either `ENCRYPT_DECRYPT` or `SIGN_VERIFY`
- `keySpec` (string): Key specification (AES_256, RSA_2048, etc.)

### Encrypt

**Request Structure:**
```python
import base64
from jdcloud_sdk.services.kms.apis.EncryptRequest import EncryptRequest, EncryptParameters

plaintext = "Sensitive data to encrypt"
plaintext_b64 = base64.b64encode(plaintext.encode()).decode()

params = EncryptParameters(
    regionId="cn-north-1",
    keyId="key-abc123def456",
    plaintext=plaintext_b64
)
req = EncryptRequest(parameters=params)
resp = client.send(req)
```

**Response Structure:**
```json
{
  "requestId": "xxxx-xxxx-xxxx-xxxx",
  "result": {
    "ciphertextBlob": "base64-encoded-ciphertext...",
    "keyId": "key-abc123def456"
  }
}
```

**Key Fields:**
- `ciphertextBlob` (string): Base64-encoded encrypted data
- Store this value for later decryption

### Decrypt

**Request Structure:**
```python
from jdcloud_sdk.services.kms.apis.DecryptRequest import DecryptRequest, DecryptParameters

params = DecryptParameters(
    regionId="cn-north-1",
    keyId="key-abc123def456",
    ciphertextBlob="base64-encoded-ciphertext..."
)
req = DecryptRequest(parameters=params)
resp = client.send(req)

# Decode plaintext
plaintext_b64 = resp.result["plaintext"]
plaintext = base64.b64decode(plaintext_b64).decode()
```

**Response Structure:**
```json
{
  "requestId": "xxxx-xxxx-xxxx-xxxx",
  "result": {
    "plaintext": "base64-encoded-decrypted-data...",
    "keyId": "key-abc123def456"
  }
}
```

### GenerateDataKey (Envelope Encryption)

**Request Structure:**
```python
from jdcloud_sdk.services.kms.apis.GenerateDataKeyRequest import GenerateDataKeyRequest, GenerateDataKeyParameters

params = GenerateDataKeyParameters(
    regionId="cn-north-1",
    keyId="key-abc123def456"
)
req = GenerateDataKeyRequest(parameters=params)
resp = client.send(req)

# Get data key
data_key_ciphertext = resp.result["dataKeyCiphertextBlob"]  # Encrypted data key
plaintext_data_key = resp.result.get("plaintextDataKey")     # Optional plaintext data key
```

**Response Structure:**
```json
{
  "requestId": "xxxx-xxxx-xxxx-xxxx",
  "result": {
    "dataKeyCiphertextBlob": "base64-encoded-encrypted-data-key...",
    "plaintextDataKey": "base64-encoded-plaintext-data-key...",
    "keyId": "key-abc123def456"
  }
}
```

**Envelope Encryption Workflow:**
1. Call `generateDataKey` to get plaintext data key + encrypted data key
2. Use plaintext data key to encrypt your data locally (AES encryption)
3. Store encrypted data + encrypted data key
4. Delete plaintext data key from memory (never persist it)
5. To decrypt: call `decrypt` with encrypted data key to get plaintext data key, then decrypt your data locally

## Pagination

For list operations (`describeKeyList`, `describeSecretList`):

**Request:**
```python
params = DescribeKeyListParameters(regionId="cn-north-1")
params.setPageNumber(1)
params.setPageSize(100)
```

**Response:**
```json
{
  "result": {
    "keys": [...],
    "totalCount": 150,
    "pageNumber": 1,
    "pageSize": 100
  }
}
```

**Pagination Strategy:**
- Default pageSize: 20
- Max pageSize: 100 (verify with API docs)
- Iterate by incrementing pageNumber until result array is empty

## Error Handling

### Common Error Codes

| Error Code | HTTP Status | Meaning | Agent Action |
|------------|-------------|---------|--------------|
| `InvalidParameter` | 400 | Request parameter invalid | Fix per OpenAPI; retry once |
| `KeyNotFound` | 404 | Key ID does not exist | HALT; verify key ID |
| `KeyDisabled` | 403 | Key is disabled | Enable key first |
| `KeyPendingDeletion` | 403 | Key is scheduled for deletion | Cancel deletion or use different key |
| `Unauthorized` | 401 | Invalid credentials | HALT; user configures credentials |
| `AccessDenied` | 403 | Insufficient IAM permissions | HALT; user grants permissions |
| `QuotaExceeded` | 400 | Key quota exceeded | HALT; user requests quota increase |
| `RateLimitExceeded` | 429 | Too many requests | Retry with backoff |
| `InternalError` | 500 | Server error | Retry up to 3 times |

### Error Response Structure

```json
{
  "requestId": "xxxx-xxxx-xxxx-xxxx",
  "error": {
    "code": "KeyNotFound",
    "message": "Key 'key-xxx' does not exist",
    "status": "404"
  }
}
```

## SDK Client Initialization

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.kms.client.KmsClient import KmsClient

# From environment variables
credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"]
)

client = KmsClient(credential)

# Optional: Set custom endpoint (for internal VPC access)
from jdcloud_sdk.core.config import Config
config = Config()
config.setEndpoint("kms.internal.cn-north-1.jdcloud-api.com")
client.setConfig(config)
```

## Request Signature

JD Cloud SDK handles request signing automatically using HMAC-SHA256. Each request includes:

- **Access Key**: Identification
- **Secret Key**: Signature generation
- **Timestamp**: Request time
- **Signature**: Calculated from request parameters

> **Security**: Never expose `JDC_SECRET_KEY`. SDK reads from environment variables only.

## Additional SDK Operations

### Key Rotation

```python
from jdcloud_sdk.services.kms.apis.KeyRotationRequest import KeyRotationRequest, KeyRotationParameters

params = KeyRotationParameters(regionId="cn-north-1", keyId="key-abc123def456")
req = KeyRotationRequest(parameters=params)
resp = client.send(req)
```

### Get Public Key (for asymmetric keys)

```python
from jdcloud_sdk.services.kms.apis.GetPublicKeyRequest import GetPublicKeyRequest, GetPublicKeyParameters

params = GetPublicKeyParameters(regionId="cn-north-1", keyId="key-rsa2048")
req = GetPublicKeyRequest(parameters=params)
resp = client.send(req)
public_key_pem = resp.result["publicKey"]
```

### Sign (for asymmetric keys)

```python
import base64
from jdcloud_sdk.services.kms.apis.SignRequest import SignRequest, SignParameters

message = "Data to sign"
message_b64 = base64.b64encode(message.encode()).decode()

params = SignParameters(
    regionId="cn-north-1",
    keyId="key-rsa2048",
    message=message_b64
)
req = SignRequest(parameters=params)
resp = client.send(req)
signature = resp.result["signature"]
```

### Verify Signature

```python
from jdcloud_sdk.services.kms.apis.ValidateRequest import ValidateRequest, ValidateParameters

params = ValidateParameters(
    regionId="cn-north-1",
    keyId="key-rsa2048",
    message="base64-encoded-message",
    signature="base64-encoded-signature"
)
req = ValidateRequest(parameters=params)
resp = client.send(req)
is_valid = resp.result["valid"]  # true/false
```

## Best Practices

1. **Reuse Client**: Initialize KmsClient once and reuse for multiple requests
2. **Error Handling**: Wrap SDK calls in try-except; check `error` field in response
3. **Pagination**: Use page-based iteration for list operations
4. **Envelope Encryption**: For large data, use `generateDataKey` instead of direct encrypt/decrypt
5. **Key Rotation**: Enable automatic rotation for production keys
6. **Audit**: Log all key operations for compliance and troubleshooting