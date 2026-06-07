# Subnet Field Mapping

**JD Cloud API**: `jdc vpc describe-subnets` → `jdcloud_subnet` (placeholder)

## Mapping Rules

| HCL Attribute | API JSON Path | Type | Required | Notes |
|---------------|---------------|------|----------|-------|
| `subnet_name` | `subnetName` | string | ✅ | Block name derived from this |
| `vpc_id` | `vpcId` | string | ✅ | Parent ref via VPC |
| `cidr_block` | `addressPrefix` | string | ✅ | e.g. `10.0.1.0/24` |
| `availability_zone` | `az` | string | ✅ | e.g. `cn-north-1a` |
| `route_table_id` | `routeTableId` | string | ❌ | Optional |
| `description` | `description` | string | ❌ | Skipped if absent |

## Block Name

`{subnet_name_slug}` (e.g. `app_subnet`)

## Stable Import ID

`subnet:{region}:{subnetId}`

## Example

Input JSON:
```json
{
  "subnetId": "subnet-3p9mkq2v3a-app",
  "subnetName": "app-subnet",
  "vpcId": "vpc-3p9mkq2v3a",
  "addressPrefix": "10.0.1.0/24",
  "az": "cn-north-1a",
  "routeTableId": "rtb-3p9mkq2v3a-rt"
}
```

Output HCL:
```hcl
resource "jdcloud_subnet" "app_subnet" {
  subnet_name       = "app-subnet"
  vpc_id            = jdcloud_vpc.prod_vpc_beijing.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "cn-north-1a"
  route_table_id    = "rtb-3p9mkq2v3a-rt"
}
```
