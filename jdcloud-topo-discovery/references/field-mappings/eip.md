# EIP (Elastic IP) Field Mapping

**JD Cloud API**: `jdc eip describe-elastic-ips` → `jdcloud_eip` (placeholder)

## Mapping Rules

| HCL Attribute | API JSON Path | Type | Required | Notes |
|---------------|---------------|------|----------|-------|
| `name` | `name` | string | ❌ | Optional EIP name |
| `bandwidth_mbps` | `bandwidthMbps` | int | ✅ | Bandwidth in Mbps |
| `charge_type` | `chargeType` | string | ❌ | `postpaid_by_traffic` / `postpaid_by_bandwidth` / `prepaid` |
| `instance_type` | `instanceType` | string | ❌ | `vm` / `clb` / `nat` / `nic` |
| `instance_id` | `instanceId` | string | ❌ | Bound resource ID |

> **京东云 EIP 与阿里云对比**:
> - 京东云: `elasticIpId` / `elasticIpAddress` / `chargeType`
> - 阿里云: `AllocationId` / `IpAddress` / `InternetChargeType`
>
> 注意 ID 字段命名不同,HCL generator 会做映射。

## Block Name

`{name_slug}` if name exists, else `eip_{id_suffix}`

## Stable Import ID

`eip:{region}:{elasticIpId}`

## Status

`status` field (e.g. `InUse` / `Available`) is **not exported to HCL** by default,
but can be added as `tags` for drift detection.
