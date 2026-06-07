# IAM SubUser Field Mapping

**JD Cloud API**: `jdc iam describe-sub-users` → `jdcloud_iam_sub_user` (placeholder)

## Mapping Rules

| HCL Attribute | API JSON Path | Type | Required | Notes |
|---------------|---------------|------|----------|-------|
| `user_name` | `subUserName` | string | ✅ | Block name derived from this |
| `description` | `description` | string | ❌ | - |
| `status` | `status` | string | ❌ | `active` / `inactive` |
| `create_time` | `createTime` | string | ❌ | ISO 8601 |

> **京东云 IAM 命名差异**:
> - 京东云用 `subUserName` 而非阿里云 `UserName`
> - 京东云子用户通过 `iam describe-sub-users` 查询
> - 阿里云用 `RAM` 产品下的 `ListUsers`
>
> 京东云 IAM 资源**不需要 regionId**(全局资源),而 jdc 接受 `--page-size` 替代 region 过滤。

## Block Name

`{user_name_slug}` (e.g. `ops_readonly`)

## Stable Import ID

`iam:global:{subUserName}` (no region qualifier — global resource)

## Deferred to Phase 3

- AccessKey (separate `describe-user-access-keys` resource, **sensitive**)
- Group membership (separate `describe-sub-user-groups`)
- Attached policies (separate `describe-attached-sub-user-policies`)
- Permissions boundary
- MFA binding (no `MFABindRequired` field in describe response — only via `update-sub-user`)

> **Security Note**: AccessKey 是高度敏感数据。`describe-user-access-keys` 返回的
> AccessKeyId 可导出,但 SecretAccessKey **永不**返回(仅在 create 时一次性返回)。
> 故 masking 主要针对 AccessKeyId 本身(虽然不算 secret,但仍可能泄露信息)。
