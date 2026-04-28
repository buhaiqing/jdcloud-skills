# JD Cloud VPC CLI Usage Guide

## Idempotent Operations Overview

All VPC operations in this Skill are designed to be **idempotent**, meaning:
- **Create operations**: If resource exists, return existing resource ID without error
- **Delete operations**: If resource doesn't exist, succeed without error
- **Safe to retry**: Operations can be safely retried without side effects

### Idempotency Patterns

#### Create with Existence Check
```bash
# Pattern: Check → Create or Return Existing
EXISTING=$(jdc vpc describe-vpcs --region cn-north-1 --output json | \
  jq -r '.data[] | select(.vpcName == "my-vpc") | .vpcId' | head -n 1)

if [ -n "$EXISTING" ]; then
  echo "Resource exists: $EXISTING"
else
  jdc vpc create-vpc --region cn-north-1 --vpc-name "my-vpc" --cidr-block "10.0.0.0/16" --output json
fi
```

#### Delete with Existence Check
```bash
# Pattern: Check → Delete or Succeed
VPC_EXISTS=$(jdc vpc describe-vpc --vpc-id vpc-abc123def --region cn-north-1 --output json 2>&1)

if echo "$VPC_EXISTS" | jq -e '.error' > /dev/null 2>&1; then
  echo "Resource already deleted. Idempotent."
  exit 0
fi

jdc vpc delete-vpc --vpc-id vpc-abc123def --region cn-north-1 --output json
```

## Prerequisites
- JD Cloud CLI installed and configured
- Valid credentials set in environment variables
- Proper permissions for VPC operations

## Basic CLI Commands

### VPC Operations

#### Create VPC (Idempotent)
```bash
# Step 1: Check if VPC already exists
EXISTING_VPC=$(jdc vpc describe-vpcs \
  --region cn-north-1 \
  --output json | jq -r '.data[] | select(.vpcName == "my-vpc") | .vpcId' | head -n 1)

if [ -n "$EXISTING_VPC" ]; then
  echo "VPC already exists with ID: $EXISTING_VPC"
  # Optionally update properties
  jdc vpc modify-vpc \
    --vpc-id "$EXISTING_VPC" \
    --region cn-north-1 \
    --vpc-name "my-vpc" \
    --description "Updated description" \
    --output json \
    --no-interactive
else
  # Step 2: Create new VPC
  jdc vpc create-vpc \
    --region cn-north-1 \
    --vpc-name "my-vpc" \
    --cidr-block "10.0.0.0/16" \
    --description "My test VPC" \
    --output json \
    --no-interactive
fi
```

#### Describe VPCs
```bash
jdc vpc describe-vpcs \
  --region cn-north-1 \
  --output json
```

#### Describe Specific VPC
```bash
jdc vpc describe-vpc \
  --vpc-id vpc-abc123def \
  --region cn-north-1 \
  --output json
```

#### Modify VPC
```bash
jdc vpc modify-vpc \
  --vpc-id vpc-abc123def \
  --region cn-north-1 \
  --vpc-name "updated-vpc-name" \
  --description "Updated description" \
  --output json \
  --no-interactive
```

#### Delete VPC (Idempotent)
```bash
# Step 1: Check if VPC exists
VPC_EXISTS=$(jdc vpc describe-vpc \
  --vpc-id vpc-abc123def \
  --region cn-north-1 \
  --output json 2>&1)

if echo "$VPC_EXISTS" | jq -e '.error' > /dev/null 2>&1; then
  echo "VPC already deleted or doesn't exist. Idempotent operation."
  exit 0
fi

# Step 2: Delete VPC
jdc vpc delete-vpc \
  --vpc-id vpc-abc123def \
  --region cn-north-1 \
  --output json \
  --no-interactive
```

### Subnet Operations

#### Create Subnet (Idempotent)
```bash
# Step 1: Check if Subnet already exists
EXISTING_SUBNET=$(jdc vpc describe-subnets \
  --region cn-north-1 \
  --vpc-id vpc-abc123def \
  --output json | jq -r '.data[] | select(.subnetName == "my-subnet") | .subnetId' | head -n 1)

if [ -n "$EXISTING_SUBNET" ]; then
  echo "Subnet already exists with ID: $EXISTING_SUBNET"
  # Optionally update properties
  jdc vpc modify-subnet \
    --subnet-id "$EXISTING_SUBNET" \
    --region cn-north-1 \
    --subnet-name "my-subnet" \
    --output json \
    --no-interactive
else
  # Step 2: Create new Subnet
  jdc vpc create-subnet \
    --region cn-north-1 \
    --vpc-id vpc-abc123def \
    --subnet-name "my-subnet" \
    --cidr-block "10.0.1.0/24" \
    --availability-zone cn-north-1a \
    --output json \
    --no-interactive
fi
```

#### Describe Subnets
```bash
jdc vpc describe-subnets \
  --region cn-north-1 \
  --vpc-id vpc-abc123def \
  --output json
```

#### Describe Specific Subnet
```bash
jdc vpc describe-subnet \
  --subnet-id subnet-abc123def \
  --region cn-north-1 \
  --output json
```

#### Modify Subnet
```bash
jdc vpc modify-subnet \
  --subnet-id subnet-abc123def \
  --region cn-north-1 \
  --subnet-name "updated-subnet-name" \
  --output json \
  --no-interactive
```

#### Delete Subnet
```bash
jdc vpc delete-subnet \
  --subnet-id subnet-abc123def \
  --region cn-north-1 \
  --output json \
  --no-interactive
```

### Security Group Operations

#### Create Security Group
```bash
jdc vpc create-network-security-group \
  --region cn-north-1 \
  --vpc-id vpc-abc123def \
  --security-group-name "my-sg" \
  --description "My security group" \
  --output json \
  --no-interactive
```

#### Describe Security Groups
```bash
jdc vpc describe-network-security-groups \
  --region cn-north-1 \
  --vpc-id vpc-abc123def \
  --output json
```

#### Add Security Group Rules
```bash
jdc vpc add-network-security-group-rules \
  --region cn-north-1 \
  --security-group-id sg-abc123def \
  --rules '[{"ipProtocol":"tcp","fromPort":22,"toPort":22,"ipRange":"0.0.0.0/0","ruleAction":"allow"}]' \
  --output json \
  --no-interactive
```

#### Remove Security Group Rules
```bash
jdc vpc remove-network-security-group-rules \
  --region cn-north-1 \
  --security-group-id sg-abc123def \
  --rule-ids '["rule-abc123def"]' \
  --output json \
  --no-interactive
```

### Network ACL Operations

#### Create Network ACL
```bash
jdc vpc create-network-acl \
  --region cn-north-1 \
  --vpc-id vpc-abc123def \
  --network-acl-name "my-acl" \
  --output json \
  --no-interactive
```

#### Describe Network ACLs
```bash
jdc vpc describe-network-acls \
  --region cn-north-1 \
  --vpc-id vpc-abc123def \
  --output json
```

#### Add Network ACL Rules
```bash
jdc vpc add-network-acl-rules \
  --region cn-north-1 \
  --network-acl-id acl-abc123def \
  --rules '[{"ruleNumber":100,"protocol":"tcp","portRange":"22-22","cidrBlock":"0.0.0.0/0","ruleAction":"allow","direction":"ingress"}]' \
  --output json \
  --no-interactive
```

### Route Table Operations

#### Create Route Table
```bash
jdc vpc create-route-table \
  --region cn-north-1 \
  --vpc-id vpc-abc123def \
  --route-table-name "my-rt" \
  --output json \
  --no-interactive
```

#### Describe Route Tables
```bash
jdc vpc describe-route-tables \
  --region cn-north-1 \
  --vpc-id vpc-abc123def \
  --output json
```

#### Add Route Table Rules
```bash
jdc vpc add-route-table-rules \
  --region cn-north-1 \
  --route-table-id rt-abc123def \
  --rules '[{"destinationCidrBlock":"0.0.0.0/0","gatewayType":"internetGateway","gatewayId":"igw-abc123def"}]' \
  --output json \
  --no-interactive
```

### VPC Peering Operations

#### Create VPC Peering
```bash
jdc vpc create-vpc-peering \
  --region cn-north-1 \
  --vpc-id vpc-abc123def \
  --peer-vpc-id vpc-xyz789ghi \
  --peer-region cn-north-1 \
  --peering-name "my-peering" \
  --output json \
  --no-interactive
```

#### Describe VPC Peerings
```bash
jdc vpc describe-vpc-peerings \
  --region cn-north-1 \
  --output json
```

### NAT Gateway Operations

#### Create NAT Gateway
```bash
jdc vpc create-nat-gateway \
  --region cn-north-1 \
  --vpc-id vpc-abc123def \
  --nat-gateway-name "my-nat" \
  --output json \
  --no-interactive
```

#### Describe NAT Gateways
```bash
jdc vpc describe-nat-gateways \
  --region cn-north-1 \
  --vpc-id vpc-abc123def \
  --output json
```

## Advanced CLI Usage

### Filtering Results
```bash
jdc vpc describe-vpcs \
  --region cn-north-1 \
  --filters 'Name=vpc-name,Values=my-vpc' \
  --output json
```

### Pagination
```bash
jdc vpc describe-vpcs \
  --region cn-north-1 \
  --page-number 1 \
  --page-size 20 \
  --output json
```

### Output Formatting
```bash
# Get specific fields using jq
jdc vpc describe-vpc \
  --vpc-id vpc-abc123def \
  --region cn-north-1 \
  --output json | jq '.data.vpcName, .data.cidrBlock, .data.status'
```

## Error Handling

### Common Error Patterns
- `InvalidParameter`: Check parameter formats and values
- `ResourceNotFound`: Verify resource IDs exist
- `QuotaExceeded`: Check account quotas
- `InternalError`: Retry with exponential backoff

### Retry Logic
```bash
# Example retry logic for failed operations
for i in {1..3}; do
  jdc vpc describe-vpc --vpc-id vpc-abc123def --region cn-north-1 --output json
  if [ $? -eq 0 ]; then
    break
  fi
  sleep $((2**i))
done
```

## Best Practices

### Idempotency Best Practices
1. **Always check before create**: Use describe/list commands to check resource existence
2. **Use unique identifiers**: Name resources consistently for reliable lookups
3. **Handle errors gracefully**: Treat "already exists" as success in idempotent operations
4. **Verify state after operations**: Confirm resource is in expected state
5. **Use --no-interactive flag**: Prevent blocking on user prompts in automation

### General Best Practices
- Always use `--output json` for machine-parseable output
- Use `--no-interactive` to prevent blocking on user prompts
- Implement proper error handling and retry logic
- Use filters to reduce API response size
- Monitor quota usage to avoid unexpected failures
- Implement exponential backoff for retries
- Log all operations for audit trail