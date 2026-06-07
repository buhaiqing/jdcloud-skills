# HCL Export Engine Design

This document describes the architecture of the HCL export engine
used by `export-hcl.py` and consumed by `baseline-manager.py`.

> **京东云特别说明**:京东云**目前没有官方 Terraform Provider**(无 `terraform-provider-jdcloud` 在 Terraform Registry)。
> 因此本 skill 导出的 HCL **仅供架构文档化与代码评审使用**(`terraform show` 风格),
> **不可执行** `terraform apply`。这是与 alicloud-topo-discovery 的核心差异。

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  CLI Layer:                                                 │
│    export-hcl.py (orchestrator)                             │
│    baseline-manager.py (wraps export-hcl + baseline store) │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Library Layer (scripts/lib/):                              │
│    manifest_validator  - schema compliance                 │
│    manifest_builder    - dict construction                 │
│    sensitive_masker    - password/key masking              │
│    provider_locker     - JDCloud Provider version           │
│    field_mapper        - JSON → HCL conversion             │
│    dependency_inference - topological sort                │
│    baseline_local/git/oss - storage backends               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Data Layer:                                                │
│    MAPPINGS registry (scripts/lib/mappings.py)             │
│    fixtures/*.json (test data)                             │
│    references/field-mappings/*.md (mapping specs)          │
└─────────────────────────────────────────────────────────────┘
```

## Resource Type Coverage (16 types)

| Type | terraform_type | Phase | 京东云对应 jdc 子命令 |
|------|----------------|-------|----------------------|
| vpc | `jdcloud_vpc` (placeholder) | 1 | `jdc vpc describe-vpcs` |
| subnet | `jdcloud_subnet` (placeholder) | 1 | `jdc vpc describe-subnets` |
| vm | `jdcloud_instance` (placeholder) | 1 | `jdc vm describe-instances` |
| mysql | `jdcloud_rds_instance` (placeholder) | 1 | `jdc rds describe-instances` |
| redis | `jdcloud_cache_instance` (placeholder) | 1 | `jdc redis describe-cache-instances` |
| clb | `jdcloud_lb` (placeholder) | 1 | `jdc lb describe-load-balancers` |
| eip | `jdcloud_eip` (placeholder) | 1 | `jdc eip describe-elastic-ips` |
| sg | `jdcloud_security_group` (placeholder) | 1 | `jdc vpc describe-network-security-groups` |
| kms | `jdcloud_kms_key` (placeholder) | 1 | `jdc kms describe-key-list` |
| iam | `jdcloud_iam_sub_user` (placeholder) | 1 | `jdc iam describe-sub-users` |
| postgresql | `jdcloud_rds_instance` (placeholder) | 1 | `jdc rds describe-instances` (engine=PostgreSQL) |
| mongodb | `jdcloud_mongodb_instance` (placeholder) | 1 | `jdc mongodb describe-instances` |
| es | `jdcloud_es_instance` (placeholder) | 1 | (无 jdc CLI 直接支持,需用 SKILL) |
| ag | `jdcloud_ag` (placeholder) | 1 | `jdc ag describe-ags` |
| nic | `jdcloud_network_interface` (placeholder) | 1 | `jdc vpc describe-network-interfaces` |
| nat | `jdcloud_nat_gateway` (placeholder) | 3 | (无独立 jdc 子命令,通过 `vpc` 管理) |

> **重要**:`terraform_type` 字段填的是**预留名称**,因为京东云无官方 Provider。
> 当未来有 Provider 发布时,需要修改 mappings.py 中对应字段。

## Output File Schema

For each export, 8 files are written atomically:

| File | Content |
|------|---------|
| `provider.tf` | `terraform{}` 和 `provider "jdcloud" {}` 占位块 |
| `main.tf` | 所有资源块,按拓扑顺序排列 |
| `variables.tf` | 变量声明(例如 mysql_password) |
| `outputs.tf` | 重要资源 ID 输出 |
| `terraform.tfstate` | 导入辅助状态(空) |
| `import.sh` | 每个资源的 `terraform import` 命令(由于无 Provider,实际不可执行) |
| `unsupported.tf` | 不支持类型的注释 |
| `manifest.json` | schema 验证的导出元数据 |

## Error Codes

| Code | Range | Meaning | Action |
|------|-------|---------|--------|
| 0 | - | Success | Read SUMMARY, no human action |
| 10-19 | env | Credential/network | Re-run with valid AK |
| 20-29 | config | Invalid arguments | Check CLI args |
| 30-39 | I/O | Filesystem | Check output dir perms |
| 40-49 | API | Mapping/dependency | Check fixtures, review HCL output |

## Sensitive Data Handling

The following fields are masked to variable references:
- `mysql.accountPassword` → `var.mysql_password`
- `redis.password` → `var.redis_password` (via `describe-cache-instances` 不返回密码, 仅作占位)
- `iam.accessKey` → `var.iam_access_key`

Sensitive values NEVER appear in:
- HCL output (replaced with var ref)
- manifest.json sensitive_masked (path only)
- import.sh (only IDs, not values)
- stderr/log (paths only, never values)
