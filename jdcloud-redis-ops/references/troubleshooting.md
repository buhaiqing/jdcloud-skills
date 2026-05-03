# Troubleshooting JD Cloud Redis

## Common API Error Codes

| Code / HTTP | Meaning | Agent Action |
|-------------|---------|--------------|
| InvalidParameter / 400 | Request parameter validation failed | Check parameter format, values, and required fields per OpenAPI spec |
| QuotaExceeded / 400 | User resource quota limit reached | HALT; instruct user to request quota increase via console or support |
| ResourceAlreadyExists / 400 | Instance name or resource already exists | Ask user to choose different name or verify existing resource |
| SubnetIpInsufficient / 400 | Subnet has insufficient IP addresses for instance nodes | HALT; user must expand subnet CIDR range or use different subnet |
| InsufficientBalance / 400 | Account balance insufficient for operation | HALT; user must top up account balance |
| PermissionDenied / 403 | IAM policy denies this operation | HALT; user must check IAM permissions or contact admin |
| ResourceNotFound / 404 | Instance or resource ID does not exist | Verify instance ID; check if instance was deleted |
| OperationNotSupported / 400 | Operation not supported for this instance type | Check instance architecture compatibility with operation |
| RateLimitExceeded / 429 | API rate limit exceeded | Retry with exponential backoff; respect Retry-After header |
| InternalError / 500 | Server internal error | Retry up to 3 times with backoff; report requestId if persists |
| ServiceUnavailable / 503 | Service temporarily unavailable | Retry after delay; check service status page |

## Diagnostic Order

When troubleshooting Redis issues, follow this systematic approach:

### 1. Verify Instance Status

**Step**: Describe the Redis instance to check current state.

```bash
jdc redis describe-cache-instance \
  --region-id "{{user.region}}" \
  --cache-instance-id "{{user.instance_id}}" \
  --output json
```

**Check**:
- Status field: `running`, `creating`, `error`, `modifying`, `deleted`
- If `error`: Check `errorMessage` field for details
- If `modifying`: Wait for operation completion

### 2. Check Instance Configuration

**Step**: Query instance configuration parameters.

```bash
jdc redis describe-instance-config \
  --region-id "{{user.region}}" \
  --cache-instance-id "{{user.instance_id}}" \
  --output json
```

**Check**:
- `maxmemory-policy`: Memory eviction strategy
- `timeout`: Connection timeout
- `maxclients`: Maximum connection limit

### 3. Analyze Performance Metrics

**Step**: Query Cloud Monitor metrics (delegate to `jdcloud-cloudmonitor-ops`).

**Check**:
- CPU utilization
- Memory usage percentage
- Connection count vs. max connections
- QPS and bandwidth usage
- Slow log count

### 4. Examine Slow Log

**Step**: Query slow operation logs.

```bash
jdc redis describe-slow-log \
  --region-id "{{user.region}}" \
  --cache-instance-id "{{user.instance_id}}" \
  --start-time "2026-05-01T00:00:00Z" \
  --end-time "2026-05-03T00:00:00Z" \
  --output json
```

**Check**:
- Commands with high execution time
- Frequent slow operations patterns
- Key names causing slow operations

### 5. Check Network Connectivity

**Step**: Verify VPC/subnet configuration and IP whitelist.

```bash
jdc redis describe-ip-white-list \
  --region-id "{{user.region}}" \
  --cache-instance-id "{{user.instance_id}}" \
  --output json
```

**Check**:
- Client IP is in whitelist
- VPC/subnet routing is correct
- Security groups allow Redis port (6379)

### 6. Query Connected Clients

**Step**: Check active client connections.

```bash
jdc redis describe-client-list \
  --region-id "{{user.region}}" \
  --cache-instance-id "{{user.instance_id}}" \
  --output json
```

**Check**:
- Number of connected clients vs. max limit
- Client IP addresses
- Idle or stuck connections

## Common Issues and Solutions

### Issue: Instance Creation Failed

**Symptoms**: Instance status shows `error` after creation.

**Possible Causes**:
- Insufficient subnet IP addresses
- Invalid specification code
- VPC/subnet mismatch
- Quota exceeded

**Resolution**:
1. Check error message in `describeCacheInstance` response
2. Verify subnet has available IPs (delegate to `jdcloud-vpc-ops`)
3. Validate spec code via `describeSpecConfig`
4. Check quota via `describeUserQuota`
5. Retry creation with corrected parameters

### Issue: High Memory Usage

**Symptoms**: Memory usage >90%, eviction occurring, OOM errors.

**Possible Causes**:
- Large number of keys
- Big keys consuming memory
- Insufficient memory allocation
- No eviction policy set

**Resolution**:
1. Run big key analysis:
   ```bash
   jdc redis create-big-key-analysis \
     --region-id "{{user.region}}" \
     --cache-instance-id "{{user.instance_id}}" \
     --output json
   ```
2. Check memory eviction policy
3. Scale up instance if needed (modifyCacheInstanceClass)
4. Delete unused keys or optimize data structures

### Issue: Connection Refused

**Symptoms**: Clients cannot connect to Redis.

**Possible Causes**:
- IP not in whitelist
- Wrong connection address/port
- Password authentication failure
- Instance not in `running` state

**Resolution**:
1. Verify instance is `running`
2. Check connection domain and port from `describeCacheInstance`
3. Add client IP to whitelist via `modifyIpWhiteList`
4. Reset password if authentication fails

### Issue: High Latency

**Symptoms**: Slow response times, high execution time.

**Possible Causes**:
- Slow commands (e.g., KEYS, HGETALL on large keys)
- Network latency
- CPU saturation
- Insufficient bandwidth

**Resolution**:
1. Analyze slow log to identify slow commands
2. Check CPU and bandwidth metrics via Cloud Monitor
3. Optimize commands (avoid KEYS, use SCAN)
4. Scale up instance if CPU/bandwidth saturated

### Issue: Hot Key Problem

**Symptoms**: Uneven load, single shard overloaded.

**Possible Causes**:
- Frequently accessed single key
- Poor key distribution in cluster

**Resolution**:
1. Run cache analysis for hot keys:
   ```bash
   jdc redis create-cache-analysis \
     --region-id "{{user.region}}" \
     --cache-instance-id "{{user.instance_id}}" \
     --output json
   ```
2. Identify hot keys from analysis results
3. Redistribute keys using hash tags
4. Split hot keys into multiple keys

### Issue: Instance Cannot Be Deleted

**Symptoms**: Delete operation fails or blocked.

**Possible Causes**:
- Deletion protection enabled
- Instance in `modifying` state
- Backup restore in progress
- Account balance issue (prepaid instances)

**Resolution**:
1. Wait for any ongoing modifications
2. Check if deletion protection is enabled
3. Verify account balance for prepaid instances
4. Retry delete after resolving blockers

### Issue: Backup Restore Failed

**Symptoms**: Restore operation fails or instance stuck in restoring.

**Possible Causes**:
- Backup file corrupted
- Backup incompatible with instance version
- Insufficient memory for backup data

**Resolution**:
1. Check backup file size vs. instance memory
2. Verify backup Redis version matches instance
3. Try different backup if available
4. Create new instance from backup (clone)

### Issue: Client Disconnection

**Symptoms**: Clients disconnected frequently.

**Possible Causes**:
- Connection timeout too short
- Max connection limit reached
- Network instability
- Client idle timeout

**Resolution**:
1. Check connection count vs. maxclients
2. Increase `timeout` parameter if needed
3. Scale up instance for more connections
4. Optimize client connection pooling

## Error Recovery Procedures

### Recovery: Rate Limit Exceeded

**Procedure**:
1. Stop sending requests immediately
2. Wait for `Retry-After` duration (if provided)
3. Implement exponential backoff in retry logic
4. Reduce request frequency

### Recovery: InternalError

**Procedure**:
1. Retry request after 2 seconds
2. If retry fails, wait 4 seconds and retry
3. If retry fails, wait 8 seconds and retry
4. If all retries fail, HALT and report requestId to support

### Recovery: Instance in Error State

**Procedure**:
1. Query instance details to identify error cause
2. If recoverable (e.g., config error), fix and retry operation
3. If unrecoverable, delete and recreate instance
4. Restore data from backup if available

### Recovery: Network Connectivity Failure

**Procedure**:
1. Verify VPC/subnet configuration
2. Check IP whitelist configuration
3. Test connectivity from same VPC
4. Delegate network troubleshooting to `jdcloud-vpc-ops`

## Prevention Best Practices

### Prevent Creation Failures

- Verify subnet IP availability before creation
- Check quota limits before large deployments
- Use valid spec codes from `describeSpecConfig`
- Test small instance first before scaling

### Prevent Performance Issues

- Regularly analyze slow logs
- Monitor memory usage trends
- Run periodic hot key/big key analysis
- Set appropriate eviction policy
- Scale proactively before saturation

### Prevent Connectivity Issues

- Configure IP whitelist before deployment
- Use VPC endpoints for internal access
- Test connectivity after creation
- Monitor connection metrics

### Prevent Data Loss

- Enable automatic backups
- Test restore procedures regularly
- Use multi-AZ deployment for HA
- Keep backups in different region if critical

## Support Escalation

When to escalate to JD Cloud support:

- Persistent InternalError with multiple requestId failures
- Unknown error codes not in documentation
- Instance stuck in unrecoverable state
- Data recovery needed after critical failure
- Quota increase requests
- Advanced technical issues requiring backend investigation

**Information to provide**:
- requestId from failed operations
- Instance ID and region
- Error code and message
- Operation attempted
- Timestamp of occurrence