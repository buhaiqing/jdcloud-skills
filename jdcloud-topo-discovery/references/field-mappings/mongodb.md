# MongoDB Field Mapping

**JD Cloud API**: `jdc mongodb describe-instances` → `jdcloud_mongodb_instance` (placeholder)

> **与阿里云 MongoDB 对比**:
> - 京东云有独立 `jdc mongodb` CLI
> - 阿里云 MongoDB 走 `alikafka`-like 独立产品,API 完全不同
> - 京东云 MongoDB 描述 API 返回 `instanceId` / `instanceName` / `engineVersion` / `mongoShardList` 等

## Mapping Rules

| HCL Attribute | API JSON Path | Type | Required | Notes |
|---------------|---------------|------|----------|-------|
| `instance_name` | `instanceName` | string | ✅ | Block name derived from this |
| `engine_version` | `engineVersion` | string | ✅ | e.g. `6.0` / `5.0` / `4.4` |
| `instance_class` | `instanceClass` | string | ✅ | - |
| `vpc_id` | `vpcId` | string | ✅ | Parent ref via VPC |
| `subnet_id` | `subnetId` | string | ✅ | Parent ref via Subnet |
| `az` | `az` | string | ✅ | - |

> Phase 1 简化:暂不导出 `mongoShardList`(分片信息),
> 该字段结构复杂且需关联 shard/mongos/config server 三个子资源。

## Block Name

`{instance_name_slug}` (e.g. `prod_mongo_01`)

## Stable Import ID

`mongodb:{region}:{instanceId}`
