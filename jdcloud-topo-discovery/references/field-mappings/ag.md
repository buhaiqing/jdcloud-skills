# AG (Availability Group) Field Mapping

**JD Cloud API**: `jdc ag describe-ags` → `jdcloud_ag` (placeholder)

> **京东云特有资源**:
> AG(高可用组)将一组 VM 绑定到统一调度策略,**与 AWS Auto Scaling Group 类似**。
> 阿里云对应概念是 ESS(Scaling Group),通过 `ess` CLI 单独管理。
> 京东云通过 `jdc ag` 子命令管理。

## Mapping Rules

| HCL Attribute | API JSON Path | Type | Required | Notes |
|---------------|---------------|------|----------|-------|
| `ag_name` | `name` | string | ✅ | Block name derived from this |
| `description` | `description` | string | ❌ | - |
| `vpc_id` | `vpcId` | string | ✅ | - |
| `az` | `az` | string | ❌ | - |
| `instance_template` | `instanceTemplate` | object | ❌ | 含 instanceType / imageId / 系统盘配置 |

## Block Name

`{ag_name_slug}` (e.g. `web_ag`)

## Stable Import ID

`ag:{region}:{agId}`

## Deferred to Phase 3

- AG 内实例列表 (`ag describe-instances` 嵌套资源)
- 伸缩策略 / 告警规则
- 模板与实例的关联关系
