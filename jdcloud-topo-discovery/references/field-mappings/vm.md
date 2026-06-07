# VM Instance Field Mapping

**JD Cloud API**: `jdc vm describe-instances` → `jdcloud_instance` (placeholder)

## Mapping Rules

| HCL Attribute | API JSON Path | Type | Required | Notes |
|---------------|---------------|------|----------|-------|
| `instance_name` | `instanceName` | string | ✅ | Block name derived from this |
| `instance_type` | `instanceType` | string | ✅ | e.g. `g.n2.large` |
| `image_id` | `imageId` | string | ✅ | OS image |
| `host_name` | `hostName` | string | ❌ | Skipped if absent |
| `subnet_id` | `subnetId` | string | ✅ | Parent ref via Subnet |
| `private_ip` | `privateIpAddress` | string | ❌ | Skipped if absent |
| `security_group_ids` | `networkSecurityGroupIds` | list | ❌ | Empty if absent |
| `az` | `az` | string | ✅ | e.g. `cn-north-1a` |

> **密码不在 `describe-instances` 响应中**(仅 `create-instances` 接收),故无需敏感字段掩码。

## Block Name

`{instance_name_slug}` (e.g. `web_01`)

## Stable Import ID

`instance:{region}:{instanceId}`

## Deferred to Phase 3

- Disks (data disks) — 需要 `describe-disks` API
- Network interfaces — 需要 `describe-network-interfaces`
- IAM role attachment — 需要 `describe-instance-iam-role`
- User data / custom metadata
- Tags — 需要单独 `describe-tags`
