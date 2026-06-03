# Troubleshooting JD Cloud RDS MySQL

## Common API Error Codes

| Code / HTTP | Meaning | Agent Action |
|-------------|---------|--------------|
| InvalidParameter | Request failed validation | Align body with OpenAPI spec; check required fields |
| InsufficientBalance | Account balance insufficient | HALT; user tops up account |
| QuotaExceeded | Instance quota exceeded | HALT; user requests quota increase |
| ResourceAlreadyExists | Instance name already exists | Ask user to choose different name |
| SubnetIpInsufficient | Subnet has no available IPs | HALT; user expands subnet or chooses different subnet |
| InternalError | Server error | Retry up to 3 times with exponential backoff |
| ServiceUnavailable | Service temporarily unavailable | Retry with backoff |
| Forbidden | Insufficient permissions | HALT; user checks IAM permissions |

## Diagnostic Order

1. **Check credentials:** Verify `JDC_ACCESS_KEY` and `JDC_SECRET_KEY` are set correctly
2. **Verify region:** Ensure region ID is valid for the account
3. **Describe resource:** Call `describeInstance` to check current state
4. **List related resources:** Check VPC/subnet existence via `jdcloud-vpc-ops`
5. **Check account balance:** Verify account has sufficient funds
6. **Review quota:** Check RDS instance quota

## Common Issues

### Connection Refused

**Possible causes:**
- Instance is not in `running` state
- Security group/IP whitelist does not allow incoming connections
- Incorrect connection endpoint or port
- Network ACL blocking traffic

**Resolution:**
1. Check instance status with `describeInstance`
2. Verify security group rules
3. Confirm connection domain and port
4. Check VPC network ACLs

### Slow Query Performance

**Possible causes:**
- Insufficient instance class
- Missing indexes
- Poor query optimization
- High connection count

**Resolution:**
1. Monitor instance metrics via `jdcloud-cloudmonitor-ops`
2. Analyze slow query logs
3. Optimize indexes
4. Consider scaling up instance class

### Backup Failed

**Possible causes:**
- Instance not in `running` state
- Insufficient storage space
- Network issues

**Resolution:**
1. Check instance status
2. Verify storage usage
3. Retry backup operation

## Recovery Procedures

### Instance in Error State

1. Describe instance to get error details
2. Check error code and message
3. Follow error-specific resolution
4. If unresolved, contact JD Cloud support

### Data Recovery

1. Check available backups
2. Restore to existing or new instance
3. Verify restored data
4. Update application connection strings if needed