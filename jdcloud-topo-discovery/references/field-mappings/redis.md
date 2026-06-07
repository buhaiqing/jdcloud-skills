# Redis Field Mapping

**JD Cloud API**: `jdc redis describe-cache-instances` → `jdcloud_cache_instance` (placeholder)

## Mapping Rules

| HCL Attribute | API JSON Path | Type | Required | Notes |
|---------------|---------------|------|----------|-------|
| `instance_name` | `cacheInstanceName` | string | ✅ | Block name derived from this |
| `instance_class` | `instanceClass` | string | ✅ | e.g. `redis.cluster.2g` |
| `instance_type` | `instanceType` | string | ❌ | `RedisCluster` / `RedisMasterSlave` / `RedisStandard` |
| `engine_version` | `engineVersion` | string | ❌ | e.g. `7.0` |
| `vpc_id` | `vpcId` | string | ✅ | Parent ref via VPC |
| `subnet_id` | `subnetId` | string | ✅ | Parent ref via Subnet |
| `az` | `az` | string | ✅ | - |
| `port` | `port` | int | ❌ | Default 6379 |
| `connection_domain` | `connectionDomain` | string | ❌ | DNS name |

> **京东云 Redis 架构区分**:
> - `RedisStandard`: 单机版
> - `RedisMasterSlave`: 主从版
> - `RedisCluster`: 集群版(分片)
>
> 与阿里云 Redis/Tair 不同,京东云 Redis 直接用 `instanceType` 标识集群模式。

## Block Name

`{instance_name_slug}` (e.g. `prod_redis_01`)

## Stable Import ID

`redis:{region}:{cacheInstanceId}`
