# Security Group Field Mapping

**JD Cloud API**: `jdc vpc describe-network-security-groups` → `jdcloud_security_group` (placeholder)

## Mapping Rules

| HCL Attribute | API JSON Path | Type | Required | Notes |
|---------------|---------------|------|----------|-------|
| `security_group_name` | `networkSecurityGroupName` | string | ✅ | Block name derived from this |
| `vpc_id` | `vpcId` | string | ✅ | Parent ref via VPC |
| `description` | `description` | string | ❌ | Skipped if absent |
| `security_group_type` | `networkSecurityGroupType` | string | ❌ | `default` / `custom` |

## Security Group Rules

The `securityGroupRules` field is a **list of rule objects**, each with:

| Field | API JSON Path | Notes |
|-------|---------------|-------|
| `rule_id` | `ruleId` | For reference only |
| `direction` | `direction` | `0` = ingress, `1` = egress |
| `protocol` | `protocol` | `6` = TCP, `17` = UDP, `1` = ICMP, `300` = ALL |
| `from_port` | `fromPort` | 1-65535, 0 for non-L4 protocols |
| `to_port` | `toPort` | 1-65535, 0 for non-L4 protocols |
| `address_prefix` | `addressPrefix` | CIDR |
| `description` | `description` | Free text |

> **京东云 SG 特殊编码**:
> - `protocol` 用数字(`6`=TCP, `17`=UDP)而非 `tcp`/`udp` 字符串
> - `direction` 用 `0`(入) / `1`(出)
> - 阿里云 ECS SG 用 `IpProtocol: tcp` 字符串

## Block Name

`{security_group_name_slug}` (e.g. `web_sg`)

## Stable Import ID

`sg:{region}:{networkSecurityGroupId}`

## Deferred to Phase 3

- Rule modification (separate `add-network-security-group-rules` resource)
- Cross-VPC SG references
