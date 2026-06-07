# VPC Field Mapping

**JD Cloud API**: `jdc vpc describe-vpcs` → `jdcloud_vpc` (placeholder)

## Mapping Rules

| HCL Attribute | API JSON Path | Type | Required | Notes |
|---------------|---------------|------|----------|-------|
| `vpc_name` | `vpcName` | string | ✅ | Block name derived from this |
| `cidr_block` | `addressPrefix` | string | ✅ | e.g. `10.0.0.0/16` |
| `description` | `description` | string | ❌ | Skipped if absent |
| `az_type` | `azType` | string | ❌ | `standard` / `edge` |

## Block Name

`{vpc_name_slug}` (e.g. `prod_vpc_beijing`)

## Stable Import ID

`vpc:{region}:{vpcId}` (e.g. `vpc:cn-north-1:vpc-3p9mkq2v3a`)

## Example

Input JSON (describe-vpcs):
```json
{
  "vpcId": "vpc-3p9mkq2v3a",
  "vpcName": "prod-vpc-beijing",
  "addressPrefix": "10.0.0.0/16",
  "description": "Production VPC in cn-north-1",
  "azType": "standard"
}
```

Output HCL (placeholder, NOT executable since JD Cloud has no official Terraform Provider):
```hcl
resource "jdcloud_vpc" "prod_vpc_beijing" {
  vpc_name    = "prod-vpc-beijing"
  cidr_block  = "10.0.0.0/16"
  description = "Production VPC in cn-north-1"
  az_type     = "standard"
}
```

> **Note**: The `jdcloud_vpc` resource type does not exist in any official Terraform
> provider. This HCL is **documentation only**, not executable.
