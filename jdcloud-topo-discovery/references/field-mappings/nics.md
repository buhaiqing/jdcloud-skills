# Network Interface (ENI) Field Mapping

**JD Cloud API**: `jdc vpc describe-network-interfaces` → `jdcloud_network_interface` (placeholder)

> 京东云 ENI 资源在 `jdc vpc` 子命令下,与阿里云 ECS 下不同。

## Mapping Rules

| HCL Attribute | API JSON Path | Type | Required | Notes |
|---------------|---------------|------|----------|-------|
| `nic_name` | `networkInterfaceName` | string | ✅ | Block name derived from this |
| `vpc_id` | `vpcId` | string | ✅ | Parent ref via VPC |
| `subnet_id` | `subnetId` | string | ✅ | Parent ref via Subnet |
| `private_ip` | `privateIpAddress` | string | ❌ | - |
| `mac_address` | `macAddress` | string | ❌ | - |
| `az` | `az` | string | ❌ | - |
| `security_group_ids` | `networkSecurityGroupIds` | list | ❌ | - |

## Block Name

`{nic_name_slug}` (e.g. `web_01_nic_0`)

## Stable Import ID

`eni:{region}:{networkInterfaceId}`

## Phase 1 状态

Phase 1 简化:仅记录 NIC 基础信息,secondary IP 列表(`secondaryIpAddresses`)
推迟到 Phase 3 处理。
