# Troubleshooting JD Cloud MongoDB

## Common API Error Codes

| Code / HTTP | Meaning | Agent Action |
|-------------|---------|--------------|
| `InvalidParameter` / 400 | Request parameter validation failed | Align parameters with OpenAPI spec; fix format/value |
| `MissingParameter` / 400 | Required parameter missing | Add missing required parameter |
| `ResourceNotFound` / 404 | Instance or resource not found | Verify instance ID/backup ID exists and in correct region |
| `ResourceAlreadyExists` / 409 | Instance name already exists | Use different instance name or query existing instance |
| `QuotaExceeded` / 403 | Account quota limit reached | HALT; inform user to request quota increase via support ticket |
| `InsufficientBalance` / 403 | Account balance insufficient | HALT; inform user to top up account balance |
| `PermissionDenied` / 403 | IAM permission denied | Check IAM policies, verify user/role has MongoDB permissions |
| `InternalError` / 500 | Service internal error | Retry with exponential backoff (max 3 retries, 2s, 4s, 8s) |
| `ServiceUnavailable` / 503 | Service temporarily unavailable | Retry after delay; check JD Cloud status page |
| `Throttling` / 429 | Rate limit exceeded | Back off, respect `Retry-After` header if present |

## Diagnostic Order

When troubleshooting MongoDB instance issues:

### 1. Instance Status Check

```bash
# Verify instance exists and check status
jdc mongodb describe-instances \
  --region-id {{user.region}} \
  --instance-id {{user.instance_id}} \
  --output json
```

**Check**:
- Instance exists (not 404)
- Status is `running` (not `error`, `creating`, `changing`)
- Connection domain and port are available

### 2. Network Connectivity

```bash
# Test connectivity from VM (if available)
mongosh --host {{connection_domain}} --port {{port}} --version

# Or use nc to test port
nc -zv {{connection_domain}} {{port}}
```

**Common Issues**:
- Connection timeout → whitelist not configured or wrong VPC
- Connection refused → instance not in running state
- Authentication failed → wrong password or username

### 3. Whitelist Verification

```bash
# Check whitelist configuration
jdc mongodb describe-security-ips \
  --region-id {{user.region}} \
  --instance-id {{user.instance_id}} \
  --output json
```

**Check**:
- Application server IP is in whitelist
- CIDR ranges are correct
- No conflicting rules

### 4. VPC and Subnet

```bash
# Verify VPC configuration
jdc vpc describe-vpc \
  --region-id {{user.region}} \
  --vpc-id {{user.vpc_id}} \
  --output json

# Verify subnet
jdc vpc describe-subnet \
  --region-id {{user.region}} \
  --subnet-id {{user.subnet_id}} \
  --output json
```

**Check**:
- VM and MongoDB are in same VPC
- Subnet has available IP addresses
- Security groups allow MongoDB port (27017)

### 5. Backup Status

```bash
# Check recent backups
jdc mongodb describe-backups \
  --region-id {{user.region}} \
  --instance-id {{user.instance_id}} \
  --output json
```

**Check**:
- Recent backups completed successfully
- Backup size is reasonable
- No failed backups

## Common Issues and Solutions

### Issue 1: VM Cannot Connect to MongoDB

**Symptoms**:
- Connection timeout from application VM
- `connection refused` error
- Network unreachable

**Diagnosis**:
1. Check instance status (must be `running`)
2. Verify whitelist includes VM IP
3. Confirm VPC/subnet match between VM and MongoDB
4. Check security group rules for MongoDB port
5. Test with `nc -zv` or `mongosh`

**Solutions**:
- Add VM IP to whitelist: `modify-security-ips`
- Ensure VM is in same VPC as MongoDB instance
- Open port 27017 in security group
- Use internal connection domain (not public)

### Issue 2: Authentication Failed

**Symptoms**:
- `Authentication failed` error
- `unauthorized` error
- Connection closes after auth attempt

**Diagnosis**:
1. Verify username (default: `root` or custom admin user)
2. Check password correctness
3. Confirm authentication database (default: `admin`)
4. Check user permissions in MongoDB

**Solutions**:
- Reset password: `reset-password`
- Use correct auth database: `mongodb://user:pass@host:port/admin`
- Create dedicated user with appropriate roles
- Verify connection string format

### Issue 3: Instance in Error State

**Symptoms**:
- Instance status shows `error`
- Operations fail with internal error
- Instance unreachable

**Diagnosis**:
1. Check instance detail for error message
2. Review recent operations (create/modify/restart)
3. Check JD Cloud status page for service issues
4. Check resource availability (quota, AZ capacity)

**Solutions**:
- Contact JD Cloud support with instance ID and requestId
- Try restart operation: `restart-instance`
- If persistent, consider creating new instance from backup
- Check for quota or resource constraints

### Issue 4: High CPU/Memory Usage

**Symptoms**:
- Slow query performance
- Connection timeouts
- High resource utilization in monitoring

**Diagnosis**:
1. Check monitoring metrics (CPU, memory, connections)
2. Review slow queries via SmartDBA
3. Check index usage and query patterns
4. Verify working set fits in memory

**Solutions**:
- Optimize queries (add indexes, use projection)
- Scale up instance spec: `modify-instance-spec`
- Implement connection pooling
- Use read preference to distribute load

### Issue 5: Disk Space Exhaustion

**Symptoms**:
- Write operations fail
- `disk full` error
- Instance becomes read-only

**Diagnosis**:
1. Check disk usage metrics
2. Review data size and growth rate
3. Check for unnecessary data or indexes
4. Verify backup storage consumption

**Solutions**:
- Add storage (if supported) or scale up spec
- Delete unnecessary indexes
- Implement data archiving/deletion policies
- Use TTL indexes for time-series data
- Optimize document size (remove unused fields)

### Issue 6: Backup Fails

**Symptoms**:
- Backup status shows `failed`
- No recent successful backups
- Backup download URL unavailable

**Diagnosis**:
1. Check backup policy configuration
2. Verify instance is in stable state
3. Check storage quota for backups
4. Review error message from backup operation

**Solutions**:
- Ensure instance is in `running` state
- Check backup retention policy
- Retry manual backup: `create-backup`
- Contact support if persistent failure

### Issue 7: Instance Creation Timeout

**Symptoms**:
- Instance stuck in `creating` state > 10 minutes
- No connection domain assigned
- Describe shows no progress

**Diagnosis**:
1. Check region and AZ availability
2. Verify VPC/subnet resources available
3. Check account quota and balance
4. Review request parameters

**Solutions**:
- Wait for full timeout (600s) before assuming failure
- Check for resource constraints in AZ
- Try different AZ if current AZ is constrained
- Verify VPC/subnet are properly configured
- Contact support with requestId

### Issue 8: Replica Set Failover Issues

**Symptoms**:
- Primary node changes unexpectedly
- Write operations fail during failover
- Connection errors after failover

**Diagnosis**:
1. Check instance status and node roles
2. Review monitoring for replica lag
3. Verify connection string uses domain (not IP)
4. Check write concern settings

**Solutions**:
- Use connection domain (stable during failover)
- Implement retry logic in application
- Use appropriate write concern (`wmajority` for strong consistency)
- Monitor replica set health metrics

### Issue 9: Sharded Cluster Query Issues

**Symptoms**:
- Queries return incomplete results
- Slow cross-shard queries
- Balancing not progressing

**Diagnosis**:
1. Check shard status and distribution
2. Review chunk distribution
3. Verify Mongos routing
4. Check shard key selection

**Solutions**:
- Use targeted queries with shard key
- Review and optimize shard key
- Monitor balancer status
- Ensure Mongos instances are healthy

### Issue 10: Restore Operation Fails

**Symptoms**:
- Restore operation stuck or fails
- Data inconsistency after restore
- Instance not recoverable

**Diagnosis**:
1. Check backup integrity and size
2. Verify backup matches instance architecture
3. Check instance state before restore
4. Review error message

**Solutions**:
- Ensure backup status is `completed`
- Restore to new instance if current instance problematic
- Verify backup matches instance version/spec
- Contact support with backup ID and instance ID

## Monitoring for Troubleshooting

Key metrics to monitor for proactive issue detection:

| Metric | Threshold | Issue | Action |
|--------|-----------|-------|--------|
| CPU Usage | > 80% sustained | Performance bottleneck | Scale up or optimize queries |
| Memory Usage | > 85% | Cache pressure | Scale up or reduce working set |
| Connections | > 80% of max | Connection exhaustion | Implement pooling, scale up |
| Disk Usage | > 85% | Storage exhaustion | Add storage, archive data |
| Replica Lag | > 10s | Replication delay | Check network, reduce write load |
| QPS | Sudden drop | Service issue | Check instance status, errors |
| Slow Queries | > 100ms | Query optimization | Add indexes, optimize queries |

## Support Escalation

When to contact JD Cloud support:

1. **Instance in error state** for > 30 minutes
2. **Data loss suspected** after restore or failover
3. **Persistent API failures** despite retries and correct parameters
4. **Quota issues** requiring manual increase
5. **Security concerns** (suspected breach, unauthorized access)
6. **Backup/restore failures** with critical data
7. **Performance issues** not resolved by scaling/optimization

**Information to provide**:
- Instance ID
- Request ID (from failed API call)
- Error message/code
- Timestamp of issue
- Recent operations performed
- Monitoring data screenshots

## Prevention Checklist

### Pre-Deployment

- [ ] Choose appropriate spec for workload
- [ ] Configure VPC and subnet correctly
- [ ] Set up whitelist before production use
- [ ] Configure automated backup policy
- [ ] Set up monitoring alerts

### Post-Deployment

- [ ] Test connection from application VMs
- [ ] Verify authentication works
- [ ] Configure appropriate users and permissions
- [ ] Test failover behavior (replica set)
- [ ] Create initial backup manually

### Regular Maintenance

- [ ] Monitor resource usage weekly
- [ ] Review slow query logs periodically
- [ ] Test backup restore monthly
- [ ] Rotate passwords quarterly
- [ ] Update whitelist on deployment changes
- [ ] Review and optimize indexes

## Related Documentation

- [Core Concepts](core-concepts.md)
- [API & SDK Usage](api-sdk-usage.md)
- [CLI Usage](cli-usage.md)
- [Monitoring](monitoring.md)