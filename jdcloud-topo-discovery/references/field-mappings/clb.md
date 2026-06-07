# CLB (Cloud Load Balancer) Field Mapping

**JD Cloud API**: `jdc lb describe-load-balancers` → `jdcloud_lb` (placeholder)

## Mapping Rules

| HCL Attribute | API JSON Path | Type | Required | Notes |
|---------------|---------------|------|----------|-------|
| `load_balancer_name` | `loadBalancerName` | string | ✅ | Block name derived from this |
| `load_balancer_type` | `loadBalancerType` | string | ✅ | `application` / `network` / `ingress` |
| `vpc_id` | `vpcId` | string | ✅ | Parent ref via VPC |
| `subnet_id` | `subnetId` | string | ✅ | Parent ref via Subnet |
| `az` | `az` | string | ✅ | - |
| `private_ip` | `privateIp` | string | ❌ | Skipped if absent |
| `elastic_ip_id` | `elasticIpId` | string | ❌ | Skipped if absent |
| `elastic_ip_address` | `elasticIpAddress` | string | ❌ | EIP if associated |
| `internet_charge_type` | `internetChargeType` | string | ❌ | `traffic` / `bandwidth` |
| `bandwidth_mbps` | `bandwidthMbps` | int | ❌ | - |

> **京东云 CLB 特殊字段**:
> - `loadBalancerType` 用 `application` / `network` / `ingress` 三种(类似 AWS ALB/NLB)
> - 阿里云 SLB 用 `LoadBalancerSpec`(如 `slb.s1.small`)
> - 京东云 CLB 通过 `internetChargeType` 区分按流量 / 按带宽

## Block Name

`{load_balancer_name_slug}` (e.g. `prod_web_clb`)

## Stable Import ID

`lb:{region}:{loadBalancerId}`

## Deferred to Phase 3

- Listeners (separate resources, `describe-listeners`)
- Backend server groups
- Health check config
- SSL certificates
