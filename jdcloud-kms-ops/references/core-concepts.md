# Core Concepts — JD Cloud KMS

## Architecture Overview

JD Cloud Key Management Service (KMS) is a security management product built on Hardware Security Modules (HSM) infrastructure. It provides:

1. **Key Management**: Create, store, and manage cryptographic keys (CMK - Customer Master Keys)
2. **Cryptographic Operations**: Encrypt, decrypt, sign, verify data
3. **Secrets Management**: Securely store and manage sensitive data (passwords, API keys, certificates)
4. **Key Rotation**: Automatic or manual key rotation for enhanced security
5. **Audit Logging**: Complete audit trail of key usage operations

### Key Types and Specifications

JD Cloud KMS supports multiple key types:

**Symmetric Keys (for encryption/decryption):**
- AES_256: AES-256 symmetric key (most common for data encryption)
- AES_128: AES-128 symmetric key

**Asymmetric Keys (for sign/verify or asymmetric encryption):**
- RSA_2048: RSA 2048-bit key pair
- RSA_4096: RSA 4096-bit key pair (higher security)
- ECC_P256: Elliptic curve P-256 key pair
- ECC_P384: Elliptic curve P-384 key pair
- ECC_P521: Elliptic curve P-521 key pair

### Key Usage

Each key has a `keyUsage` attribute that defines its purpose:

- **ENCRYPT_DECRYPT**: Used for data encryption and decryption (symmetric keys)
- **SIGN_VERIFY**: Used for digital signature and verification (asymmetric keys)

> **Important**: Key usage is set at creation and cannot be changed later.

## Key States and Lifecycle

KMS keys follow a defined lifecycle:

| State | Description | Allowed Operations |
|-------|-------------|-------------------|
| **Enabled** | Key is active and can be used for cryptographic operations | All operations (encrypt, decrypt, describe, rotate, etc.) |
| **Disabled** | Key is deactivated but still exists | Describe, enable, schedule deletion |
| **PendingDeletion** | Key is scheduled for deletion (waiting period) | Describe, cancel deletion |
| **Deleted** | Key has been permanently removed | No operations (404 on describe) |

### State Transitions

1. **Create**: New key starts in `Enabled` state
2. **Disable**: `Enabled` → `Disabled` (stops all cryptographic operations)
3. **Enable**: `Disabled` → `Enabled` (resumes operations)
4. **ScheduleDeletion**: `Enabled`/`Disabled` → `PendingDeletion` (enter waiting period, typically 7-30 days)
5. **CancelDeletion**: `PendingDeletion` → `Disabled` (restore key, cannot re-enable directly)
6. **Delete**: `PendingDeletion` → Deleted (permanent, irreversible)

> **Safety**: Keys in `PendingDeletion` state cannot be used for encryption/decryption. The waiting period provides a safety buffer before permanent deletion.

## Key Rotation

### Automatic Rotation

KMS supports automatic key rotation for symmetric keys:

- **Rotation Interval**: Configurable (e.g., 90 days, 180 days, 365 days)
- **Rotation Process**: Creates new key version while retaining old versions for decryption
- **Backward Compatibility**: Old encrypted data can still be decrypted using previous key versions

### Manual Rotation

For asymmetric keys or custom rotation schedules:

1. Create a new key
2. Update application configuration to use new key ID
3. (Optional) Schedule deletion of old key after migration complete

## Secrets Management

KMS provides secrets management for storing sensitive configuration data:

### Secret Structure

- **Secret Name**: Unique identifier for the secret
- **Secret Data**: The actual sensitive data (encrypted by KMS)
- **Secret Versions**: Secrets can have multiple versions (for updates)
- **Secret State**: Enabled, Disabled, PendingDeletion, Deleted

### Secret Operations

- `createSecret`: Create a new secret
- `describeSecretList`: List all secrets
- `createSecretVersion`: Create new version of existing secret
- `enableSecret/disableSecret`: Enable/disable secret access
- `deleteSecret`: Delete secret (with safety waiting period)

### Use Cases

- Database passwords
- API keys and tokens
- SSL/TLS certificates
- Application configuration secrets
- SSH keys

## Regions and Endpoints

JD Cloud KMS is available in multiple regions with different endpoints:

| Region | Region ID | Public Endpoint | Internal Endpoint (VPC) |
|--------|-----------|-----------------|------------------------|
| 华北-北京 | cn-north-1 | kms.cn-north-1.jdcloud-api.com | kms.internal.cn-north-1.jdcloud-api.com |
| 华东-上海 | cn-east-2 | kms.cn-east-2.jdcloud-api.com | kms.internal.cn-east-2.jdcloud-api.com |
| 华东-宿迁 | cn-east-1 | kms.cn-east-1.jdcloud-api.com | kms.internal.cn-east-1.jdcloud-api.com |
| 华南-广州 | cn-south-1 | kms.cn-south-1.jdcloud-api.com | kms.internal.cn-south-1.jdcloud-api.com |

> **Best Practice**: Use internal endpoints when calling KMS from JD Cloud VPC for better performance and lower cost.

## Quotas and Limits

### Key Quotas

- Default: Limited number of CMKs per region per account
- Contact support for quota increase

### Operation Rate Limits

- `encrypt`/`decrypt`: Higher rate limit (thousands of operations per second)
- `createKey`/`deleteKey`: Lower rate limit (tens of operations per second)
- `describeKey`/`listKeys`: Medium rate limit

> **Note**: Rate limits vary by region and account tier. Check official documentation for current limits.

## Security Best Practices

### Key Management

1. **Least Privilege**: Grant minimal permissions (encrypt-only for applications, full management for administrators)
2. **Separate Keys**: Use different keys for different purposes (data encryption vs. signing)
3. **Key Rotation**: Enable automatic rotation for frequently-used keys
4. **Audit**: Enable and review key usage logs regularly

### Secrets Management

1. **Never Hardcode**: Use KMS secrets instead of hardcoding sensitive data
2. **Version Management**: Use secret versions for configuration updates
3. **Access Control**: Restrict secret access to specific services/users
4. **Encryption**: All secret data is encrypted using CMKs

### Data Protection

1. **Envelope Encryption**: For large data, use `generateDataKey` to create data encryption key, encrypt data locally, store only encrypted data key
2. **Key Context**: Use encryption context for additional access control
3. **Backup**: Export encrypted data keys for backup; never export plaintext keys

## Integration with Other JD Cloud Services

KMS integrates with multiple JD Cloud services for automatic encryption:

- **OSS (Object Storage)**: Server-side encryption using KMS keys
- **Cloud Disk**: Disk encryption using KMS keys
- **RDS**: Database encryption using KMS keys
- **Redis**: Cache instance encryption using KMS keys

> **Integration**: When creating encrypted resources in other services, specify KMS key ID for encryption.

## Pricing

JD Cloud KMS pricing includes:

- **Key Management**: Monthly fee per CMK (varies by key type)
- **API Calls**: Per-operation fee for encrypt/decrypt/sign/verify
- **Secrets**: Monthly fee per secret stored
- **Free Tier**: Limited free operations during public beta (check official pricing)

> **Cost Optimization**: Use envelope encryption (generateDataKey) for high-volume encryption to reduce KMS API calls.

## References

- Official Documentation: https://docs.jdcloud.com/cn/key-management-service/introduction
- API Reference: https://docs.jdcloud.com/cn/key-management-service/api/overview
- CLI Documentation: https://docs.jdcloud.com/cn/cli/introduction
- Pricing: https://www.jdcloud.com/products/key-management-service