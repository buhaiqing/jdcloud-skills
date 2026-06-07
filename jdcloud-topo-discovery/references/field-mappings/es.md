# Elasticsearch Field Mapping

**JD Cloud API**: 无独立 `jdc elasticsearch` CLI,**需通过 `jdcloud-elasticsearch-ops` skill 委托**。

> **重要**:`jdc` CLI **不提供** `elasticsearch` 子命令。
> Elasticsearch 资源采集需通过 `jdcloud-elasticsearch-ops` skill 调用
> `jcloud.Elasticsearch.DescribeInstances` REST API 或 Python SDK。

## Mapping Rules (via REST API)

| HCL Attribute | API JSON Path | Type | Required | Notes |
|---------------|---------------|------|----------|-------|
| `instance_name` | `data.instanceIdNameMap[].name` | string | ✅ | Block name derived from this |
| `instance_id` | `data.instanceIdNameMap[].id` | string | ✅ | - |
| `engine_version` | `data.instanceConfigList[].esVersion` | string | ❌ | e.g. `7.10` |
| `node_num` | `data.instanceConfigList[].nodeNum` | int | ❌ | 数据节点数 |
| `az` | `data.instanceConfigList[].azId` | string | ❌ | - |

> **REST API 响应结构**:
> - 京东云 ES 描述 API 用 `data` 包装,与 jdc 标准 `result` 不一致
> - 这就是为什么本 skill 不能直接 `jdc elasticsearch describe` 采集

## Block Name

`{instance_name_slug}` (e.g. `prod_es_01`)

## Stable Import ID

`es:{region}:{instanceId}`

## Phase 1 状态

**es 资源类型在 Phase 1 标记为 `partial`**:仅记录 instance_id 和 instance_name,
完整字段需通过 `jdcloud-elasticsearch-ops` skill 采集。
