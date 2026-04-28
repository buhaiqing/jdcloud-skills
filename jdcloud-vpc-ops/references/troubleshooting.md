# JD Cloud VPC Troubleshooting Guide

## Idempotency Troubleshooting

### Common Idempotency Issues

#### Issue: Duplicate Resource Creation
**Symptom**: Multiple resources created with same name
**Cause**: Race condition in concurrent operations
**Solution**: 
```bash
# Use locking mechanism or serialized execution
# Add unique identifier to resource names
jdc vpc create-vpc --vpc-name "my-vpc-$(date +%s)" --cidr-block "10.0.0.0/16"
```

#### Issue: Delete Operation Fails on Non-existent Resource
**Symptom**: Error when deleting already deleted resource
**Cause**: Not implementing idempotent delete pattern
**Solution**:
```bash
# Always check existence before delete
VPC_EXISTS=$(jdc vpc describe-vpc --vpc-id vpc-abc123def --region cn-north-1 --output json 2>&1)
if echo "$VPC_EXISTS" | jq -e '.error' > /dev/null 2>&1; then
  echo "Resource already deleted. Idempotent."
  exit 0
fi
```

#### Issue: Inconsistent Resource State
**Symptom**: Resource shows different states on consecutive queries
**Cause**: Eventual consistency in cloud APIs
**Solution**: Implement polling with proper wait intervals

## Common Error Codes

| Error Code | Description | Solution | Idempotency Impact |
|------------|-------------|----------|-------------------|
| `InvalidParameter` | A required parameter is missing or invalid | Check the CLI command syntax and parameter values | No impact |
| `InsufficientBalance` | Account balance is insufficient | Top up your JD Cloud account | No impact |
| `ResourceAlreadyExists` | A resource with the same name already exists | Use a different name or delete the existing resource | **Expected in idempotent create** |
| `QuotaExceeded` | You have reached the maximum number of resources allowed | Request a quota increase or delete unused resources | No impact |
| `ResourceNotFound` | The specified resource does not exist | Verify the resource ID is correct | **Expected in idempotent delete** |
| `ForbiddenOperation` | Insufficient permissions to perform the operation | Check IAM permissions and policies | No impact |
| `InternalError` | Internal server error occurred | Retry the operation with exponential backoff | No impact |
| `DependencyError` | Resource cannot be modified due to dependencies | Check dependent resources and their states | No impact |

## Diagnostic Steps

### VPC Issues
1. **Check VPC Status**: 
   ```bash
   jdc vpc describe-vpcs --region {{user.region}}
   ```
2. **Verify CIDR Block**: Ensure CIDR blocks don't overlap
3. **Check VPC State**: Confirm VPC is in `running` state
4. **Review VPC Attributes**: Verify VPC configuration settings

### Subnet Issues
1. **Check Subnet Status**: 
   ```bash
   jdc vpc describe-subnets --vpc-id {{user.vpc_id}} --region {{user.region}}
   ```
2. **Verify CIDR Range**: Ensure subnet CIDR is within VPC CIDR
3. **Check Availability Zone**: Confirm AZ is available in the region
4. **Review Subnet Configuration**: Verify subnet settings and associations

### Connectivity Issues
1. **Network Connectivity**: Use `ping` and `telnet` from a bastion host to verify network access
2. **Route Table Analysis**: Check route tables for proper routing
3. **Security Group Review**: Verify security group rules allow required traffic
4. **Network ACL Check**: Ensure network ACL rules are not blocking traffic

### Security Group Issues
1. **List Security Groups**: 
   ```bash
   jdc vpc describe-network-security-groups --vpc-id {{user.vpc_id}} --region {{user.region}}
   ```
2. **Check Rules**: Verify inbound and outbound rules
3. **Test Connectivity**: Test if security groups are allowing/denying expected traffic
4. **Review Associations**: Check which instances are associated with security groups

### NAT Gateway Issues
1. **Check NAT Gateway Status**: 
   ```bash
   jdc vpc describe-nat-gateways --vpc-id {{user.vpc_id}} --region {{user.region}}
   ```
2. **Verify Elastic IPs**: Ensure NAT gateway has associated elastic IPs
3. **Check DNAT/SNAT Rules**: Verify NAT rules are configured correctly
4. **Test Internet Connectivity**: Test if instances can reach the internet through NAT

### VPC Peering Issues
1. **Check Peering Status**: 
   ```bash
   jdc vpc describe-vpc-peerings --region {{user.region}}
   ```
2. **Verify Peering Configuration**: Check both sides of the peering connection
3. **Check Route Tables**: Ensure routes exist for peered VPC CIDRs
4. **Test Connectivity**: Test connectivity between peered VPCs

## Network Troubleshooting

### Ping Tests
```bash
# Test connectivity between instances
ping -c 4 <target-instance-ip>

# Test internet connectivity
ping -c 4 8.8.8.8
```

### Traceroute Analysis
```bash
# Trace network path
traceroute <target-ip>

# Check routing to internet
traceroute 8.8.8.8
```

### Port Testing
```bash
# Test specific port connectivity
telnet <target-ip> <port>

# Using nc (netcat)
nc -zv <target-ip> <port>
```

## Performance Issues

### High Latency
1. **Check Network Path**: Verify traffic is taking optimal route
2. **Monitor Bandwidth**: Check if bandwidth limits are being reached
3. **Review Instance Types**: Ensure instance types support required network performance
4. **Check Cross-AZ Traffic**: Minimize cross-availability zone traffic when possible

### Packet Loss
1. **Monitor Network Metrics**: Check for packet loss patterns
2. **Check Security Groups**: Verify no rules are dropping packets
3. **Review Route Tables**: Ensure proper routing configuration
4. **Test Different Paths**: Test connectivity through different network paths

## Configuration Validation

### VPC Configuration Check
```bash
# Validate VPC configuration
jdc vpc describe-vpc --vpc-id {{user.vpc_id}} --region {{user.region}} --output json | jq '.data'
```

### Subnet Configuration Check
```bash
# Validate subnet configuration
jdc vpc describe-subnet --subnet-id {{user.subnet_id}} --region {{user.region}} --output json | jq '.data'
```

### Security Group Configuration Check
```bash
# Validate security group configuration
jdc vpc describe-network-security-group --security-group-id {{user.security_group_id}} --region {{user.region}} --output json | jq '.data'
```

## Recovery Procedures

### Failed VPC Creation
1. Check error message for specific failure reason
2. Verify CIDR block doesn't conflict with existing VPCs
3. Ensure account has sufficient quota
4. Retry with corrected parameters
5. **Idempotent retry**: Check if VPC was created before retrying

### Stuck Resources
1. Check resource status and state
2. Verify no dependencies are blocking operations
3. Force delete if necessary (with caution)
4. Contact support if resource cannot be recovered
5. **Idempotent cleanup**: Use idempotent delete pattern for cleanup

### Configuration Rollback
1. Document current configuration before changes
2. Use version control for configuration files
3. Implement change management procedures
4. Test changes in non-production environments first
5. **Idempotent rollback**: Ensure rollback operations are also idempotent

### Idempotency Verification
```bash
# Verify idempotent create
EXISTING=$(jdc vpc describe-vpcs --region cn-north-1 --output json | \
  jq -r '.data[] | select(.vpcName == "my-vpc") | .vpcId' | head -n 1)

if [ -n "$EXISTING" ]; then
  echo "✓ VPC exists: $EXISTING"
  echo "✓ Operation is idempotent"
else
  echo "✗ VPC not found"
fi

# Verify idempotent delete
VPC_EXISTS=$(jdc vpc describe-vpc --vpc-id vpc-abc123def --region cn-north-1 --output json 2>&1)
if echo "$VPC_EXISTS" | jq -e '.error' > /dev/null 2>&1; then
  echo "✓ VPC deleted"
  echo "✓ Delete operation is idempotent"
else
  echo "✗ VPC still exists"
fi
```

## Support Resources
- JD Cloud Documentation: https://docs.jdcloud.com/cn/virtual-private-cloud/
- API Reference: https://docs.jdcloud.com/cn/virtual-private-cloud/api-reference/
- Support Center: https://support.jdcloud.com/
- Community Forum: https://community.jdcloud.com/