# KMS Key Field Mapping

**JD Cloud API**: `jdc kms describe-key-list` + `describe-key` → `jdcloud_kms_key` (placeholder)

## Mapping Rules

| HCL Attribute | API JSON Path | Type | Required | Notes |
|---------------|---------------|------|----------|-------|
| `key_name` | `keyName` | string | ❌ | Optional human-readable name |
| `description` | `description` | string | ❌ | - |
| `key_spec` | `keySpec` | string | ❌ | `AES_256` / `AES_128` / `RSA_2048` / `EC_P256` |
| `key_usage` | `keyUsage` | string | ❌ | `ENCRYPT/DECRYPT` / `SIGN/VERIFY` |
| `origin` | `origin` | string | ❌ | `JDCLOUD` (managed) / `EXTERNAL` (BYOK) |
| `rotation_enabled` | `rotationEnabled` | bool | ❌ | KMS automatic rotation |
| `rotation_interval_days` | `rotationIntervalDays` | int | ❌ | Valid when rotation enabled |

> **京东云 KMS 关键差异**:
> - 京东云有 `keySpec`(对称 vs 非对称)+ `keyUsage`(加解密 vs 签名/验签)的明确区分
> - 阿里云 KMS 用 `KeySpec` 字段名相同,但枚举值不同
> - 京东云 KMS 轮转通过 `rotationEnabled` 布尔标识,无阿里云的 `RotationStatus` 状态机

## Block Name

`{key_name_slug}` if name exists, else `kms_{key_id_suffix}`

## Stable Import ID

`kms:{region}:{keyId}`

## Sensitive

- Key material is **NEVER** returned in describe response
- `keyId` is the only stable identifier
- IAM policy details (who can use) NOT in describe-key response, requires separate `describe-key-policy`
