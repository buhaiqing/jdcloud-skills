# Troubleshooting MongoDB

## Common API Error Codes

| Code / HTTP | Meaning | Agent Action |
|-------------|---------|--------------|
| `InvalidParameter` / 400 | Request failed validation | Align body with OpenAPI; check parameter types |
| `MissingParameter` / 400 | Required parameter missing | Review required fields for the operation |
| `ResourceNotFound` / 404 | Instance or resource not found | Verify instance ID; check region |
| `ResourceAlreadyExists` / 409 | Instance name already in use | Choose different name or use existing instance |
| `InsufficientBalance` / 403 | Account balance insufficient | HALT; user tops up account |
| `QuotaExceeded` / 403 | Resource quota exceeded | HALT; user requests quota increase |
| `InvalidInstanceStatus` / 400 | Operation not valid for current status | Wait for instance to reach stable state |
| `SubnetIpInsufficient` / 400 | Subnet has no available IPs | HALT; user expands subnet |
| `InvalidPassword` / 400 | Password does not meet complexity | Use stronger password (8+ chars, mixed case, numbers) |
| `OperationDenied` / 403 | Operation not permitted | Check IAM permissions |
| `InternalError` / 500 | Internal server error | Retry with exponential backoff |
| `ServiceUnavailable` / 503 | Service temporarily unavailable | Retry with exponential backoff |

## Diagnostic Order

### 1. Instance Issues

```
1. Describe instance by ID
   → Check status, error messages
   
2. If status is "error":
   → Check error details in response
   → Review recent operations (backups, restores, modifications)
   
3. If status is stuck in "creating" > 10 min:
   → May indicate quota or capacity issue
   → Check account balance and quotas
```

### 2. Connection Issues

```
1. Verify instance is in "running" state
   
2. Check connection domain and port
   → Ensure using correct connection string
   
3. Verify network access:
   → Instance VPC/subnet configuration
   → Security group rules
   → IP whitelist settings
   
4. Test connectivity:
   → From same VPC: should work directly
   → From internet: requires public IP/ELB
```

### 3. Performance Issues

```
1. Check CloudMonitor metrics:
   → CPU utilization
   → Memory usage
   → Disk IOPS
   → Connection count
   
2. Analyze slow queries:
   → Enable slow query log
   → Identify missing indexes
   
3. Check instance class:
   → May need vertical scaling
   → Consider adding read replicas
```

## Common Issues and Solutions

### Issue: Instance Creation Fails

**Symptoms**: Instance stuck in `creating` or fails immediately

**Possible Causes**:
- Insufficient account balance
- Quota exceeded
- Subnet has no available IPs
- Invalid instance class for region

**Resolution**:
```bash
# 1. Check account balance
jdc --output json billing describe-account --region-id cn-north-1

# 2. Check quotas
jdc --output json mongodb describe-spec-config --region-id cn-north-1

# 3. Verify subnet
jdc --output json vpc describe-subnet --region-id cn-north-1 --subnet-id <subnet-id>
```

### Issue: Cannot Connect to Instance

**Symptoms**: Connection timeout or refused

**Possible Causes**:
- Instance not in `running` state
- Security group blocking port 27017
- IP whitelist not configured
- Wrong connection string

**Resolution**:
```bash
# 1. Check instance status
jdc --output json mongodb describe-instance \
  --region-id cn-north-1 \
  --instance-id <instance-id> | jq '.result.instance.status'

# 2. Check connection domain
jdc --output json mongodb describe-instance \
  --region-id cn-north-1 \
  --instance-id <instance-id> | jq '.result.instance.connectionDomain'
```

### Issue: High Latency

**Symptoms**: Slow queries, high response times

**Possible Causes**:
- Insufficient resources (CPU/memory)
- Missing indexes
- Large collections without proper sharding
- Network latency

**Resolution**:
```bash
# 1. Check if instance class needs upgrade
# 2. Enable slow query log via console or API
# 3. Review query patterns and add indexes
# 4. Consider read replicas for read-heavy workloads
```

### Issue: Backup Fails

**Symptoms**: Backup stuck or fails immediately

**Possible Causes**:
- Instance not in `running` state
- Insufficient storage for backup
- Concurrent backup limit reached

**Resolution**:
```bash
# 1. Check instance status
jdc --output json mongodb describe-instance \
  --region-id cn-north-1 \
  --instance-id <instance-id>

# 2. List existing backups
jdc --output json mongodb describe-backups \
  --region-id cn-north-1 \
  --instance-id <instance-id>
```

### Issue: Restore Fails

**Symptoms**: Restore operation fails or instance doesn't start

**Possible Causes**:
- Backup file corrupted
- Incompatible MongoDB versions
- Insufficient disk space

**Resolution**:
```bash
# 1. Verify backup exists and is valid
jdc --output json mongodb describe-backups \
  --region-id cn-north-1 \
  --instance-id <instance-id>

# 2. Check target instance has sufficient storage
```

## Log Locations

### Cloud Logs

Access via CloudMonitor or Log Service:

| Log Type | Access Method |
|----------|---------------|
| Slow Query Log | Console → MongoDB → Instance → Logs |
| Error Log | Console → MongoDB → Instance → Logs |
| Audit Log | Console → MongoDB → Instance → Logs (if enabled) |

### CLI Log Retrieval

```bash
# Note: Direct log access via CLI may be limited
# Use CloudMonitor for programmatic log access
```

## Recovery Procedures

### Scenario: Accidental Data Deletion

1. **Immediate**: Stop writes to the database if possible
2. **Identify**: Determine the point in time before deletion
3. **Restore**: Use point-in-time recovery or specific backup
4. **Verify**: Check restored data completeness

### Scenario: Instance Corruption

1. **Assess**: Check instance status and error logs
2. **Decision Tree**:
   - If backup available → Restore from backup
   - If no backup → May need to recreate instance
3. **Post-recovery**: Review backup policies

### Scenario: Connection Storm

1. **Identify**: Check connection count metrics
2. **Mitigate**: Restart application connection pools
3. **Scale**: Consider connection pooling or instance upgrade
4. **Monitor**: Set up connection count alarms

## Support Escalation

When to escalate to JD Cloud support:

| Situation | Action |
|-----------|--------|
| Instance stuck > 1 hour | Open ticket with instance ID |
| Data inconsistency | Open ticket with details |
| API returning 500s consistently | Report with request IDs |
| Billing discrepancy | Contact billing support |

**Ticket Information to Include**:
- Instance ID
- Region
- Timestamp of issue
- Request IDs from API responses
- Error messages (full JSON if available)
