# CLI Usage

## Prerequisites

```bash
# Install jdcloud CLI
uv pip install jdcloud_cli

# Configure credentials
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc
cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = YOUR_ACCESS_KEY
secret_key = YOUR_SECRET_KEY
region_id = cn-north-1
scheme = https
timeout = 20
CONFIGEOF
printf "%s" "default" > /tmp/jdc-home/.jdc/current
```

## Basic Audit Command

### Audit All Products in All Regions

```bash
# Run comprehensive audit
./audit.sh --regions all --products all --tags "环境,客户"
```

### Audit Specific Products

```bash
# Audit only Redis and VM
./audit.sh --regions cn-north-1,cn-east-2 --products redis,vm
```

### Check Single Region

```bash
# Check only cn-north-1 region
./audit.sh --regions cn-north-1 --products all
```

## Manual Audit Commands

### Redis Audit

```bash
jdc --output json redis describe-cache-instances \
  --region-id cn-north-1 --page-number 1 --page-size 100 | \
jq '.result.cacheInstances[] | 
    select((.tags // []) | map(.key) | contains(["环境"]) | not) | 
    {id: .cacheInstanceId, name: .cacheInstanceName}'
```

### VM Audit

```bash
jdc --output json vm describe-instances \
  --region-id cn-north-1 --page-number 1 --page-size 100 | \
jq '.result.instances[] | 
    select((.tags // []) | map(.key) | contains(["环境"]) | not) | 
    {id: .instanceId, name: .name}'
```

### RDS Audit

```bash
jdc --output json rds describe-instances \
  --region-id cn-north-1 --page-number 1 --page-size 100 | \
jq '.result.dbInstances[] | 
    select((.tags // []) | map(.key) | contains(["环境"]) | not) | 
    {id: .instanceId, name: .instanceName}'
```

### CLB Audit

```bash
jdc --output json clb describe-load-balancers \
  --region-id cn-north-1 --page-number 1 --page-size 100 | \
jq '.result.loadBalancers[] | 
    select((.tags // []) | map(.key) | contains(["环境"]) | not) | 
    {id: .loadBalancerId, name: .loadBalancerName}'
```

### EIP Audit

```bash
jdc --output json eip describe-addresses \
  --region-id cn-north-1 --page-number 1 --page-size 100 | \
jq '.result.addresses[] | 
    select((.tags // []) | map(.key) | contains(["环境"]) | not) | 
    {id: .addressId, name: (.name // "N/A")}'
```

## Output Format

### JSON Output

```json
{
  "product": "redis",
  "region": "cn-north-1",
  "id": "redis-abc123",
  "name": "my-redis-instance",
  "missingTags": ["环境", "客户"]
}
```

### Text Report

```
## Tag Compliance Audit Report
### Summary
- Total resources scanned: 150
- Non-compliant resources: 25
- Compliance rate: 83.33%

### Non-compliant Resources by Product
| Product | Count |
|---------|-------|
| Redis | 5 |
| VM | 12 |
| RDS | 4 |
| CLB | 2 |
| EIP | 2 |
```