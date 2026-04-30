# Troubleshooting JD Cloud Redis

## Common Error Codes

### API Errors

| Error Code | HTTP Status | Description | Solution |
|------------|-------------|-------------|----------|
| `InvalidParameter` | 400 | A required parameter is missing or invalid | Check CLI command syntax and parameter format |
| `InvalidParameter.Password` | 400 | Password does not meet complexity requirements | Use 8-32 chars with letters, numbers, and special chars |
| `InvalidParameter.Whitelist` | 400 | IP whitelist format is invalid | Use valid IP or CIDR notation (e.g., 192.168.1.0/24) |
| `ResourceNotFound` | 404 | Instance does not exist | Verify instance ID and region |
| `ResourceAlreadyExists` | 409 | Instance with same name already exists | Use a different name or reuse existing instance |
| `QuotaExceeded` | 403 | Instance quota exceeded | Request quota increase or delete unused instances |
| `InsufficientBalance` | 403 | Account balance insufficient | Top up account |
| `InsufficientResource` | 403 | Spec not available in AZ | Try different AZ or spec |
| `OperationDenied.InstanceStatus` | 403 | Instance not in correct state for operation | Wait for instance to reach target state |
| `InternalError` | 500 | Internal service error | Retry with backoff, contact support if persists |

### Connection Errors

| Error | Description | Solution |
|-------|-------------|----------|
| `Connection refused` | Cannot connect to Redis endpoint | Check whitelist, network, and instance status |
| `NOAUTH Authentication required` | Password not provided | Provide password in connection string |
| `WRONGPASS invalid username-password pair` | Incorrect password | Reset password or verify credentials |
| `DENIED Redis is running in protected mode` | Protected mode enabled | Configure whitelist or disable protected mode |
| `MAXCLIENTS reached` | Max connections reached | Increase instance spec or optimize connection pool |
| `OOM command not allowed` | Out of memory | Delete unused keys or scale up instance |
| `BUSY Redis is busy` | Running blocking command | Wait for command to complete or optimize query |
| `LOADING Redis is loading` | Instance loading dataset | Wait for loading to complete |

## Diagnostic Steps

### Step 1: Check Instance Status

```bash
jdc redis describe-cache-instance \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --output json | jq '.result.cacheInstance.status'
```

**Expected states:**
- `running`: Normal operation
- `creating`: Wait for provisioning to complete
- `changing`: Configuration change in progress
- `error`: Contact support

### Step 2: Verify Network Connectivity

From application server:

```bash
# Test TCP connectivity
telnet <redis-endpoint> 6379

# Or use nc
nc -zv <redis-endpoint> 6379

# Test with redis-cli
redis-cli -h <redis-endpoint> -p 6379 -a <password> ping
```

**Expected response:** `PONG`

### Step 3: Check IP Whitelist

```bash
jdc redis describe-ip-white-list \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --output json
```

**Verify:**
- Application server IP is in whitelist
- CIDR notation is correct
- No conflicting rules

### Step 4: Check Memory Usage

```bash
# Via CLI
jdc redis describe-cache-instance \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --output json | jq '.result.cacheInstance.usedMemoryMB, .result.cacheInstance.capacityMB'

# Via redis-cli
redis-cli -h <endpoint> -p 6379 -a <password> INFO memory
```

**Key metrics:**
- `used_memory`: Current memory usage
- `maxmemory`: Configured max memory
- `mem_fragmentation_ratio`: Memory fragmentation (>1.5 is concerning)

### Step 5: Check Slow Logs

```bash
jdc redis describe-slow-log \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --start-time "2026-04-30T00:00:00+08:00" \
  --end-time "2026-04-30T23:59:59+08:00" \
  --output json
```

**Look for:**
- Commands with high execution time (>100ms)
- Blocking commands: KEYS, FLUSHALL, HGETALL (large hashes)
- Optimizable patterns: multiple small commands vs pipeline

### Step 6: Check Connected Clients

```bash
# Via CLI
jdc redis describe-client-list \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --output json

# Via redis-cli
redis-cli -h <endpoint> -p 6379 -a <password> CLIENT LIST
```

**Check for:**
- Too many idle connections (connection leak)
- Single client with excessive connections
- Unexpected client IPs

## Common Issues and Solutions

### Issue 1: Cannot Connect to Redis Instance

**Symptoms:**
- Connection timeout or refused
- Application logs show connection errors

**Possible Causes & Solutions:**

1. **Whitelist not configured**
   ```bash
   # Add application server IP to whitelist
   jdc redis modify-ip-white-list \
     --region-id cn-north-1 \
     --cache-instance-id jcs-redis-abc123 \
     --ip-white-list '["10.0.1.100"]' \
     --output json
   ```

2. **Wrong endpoint or port**
   ```bash
   # Get correct connection info
   jdc redis describe-cache-instance \
     --region-id cn-north-1 \
     --cache-instance-id jcs-redis-abc123 \
     --output json | jq '{
       domain: .result.cacheInstance.connectionDomain,
       port: .result.cacheInstance.connectionPort
     }'
   ```

3. **Instance not in running state**
   ```bash
   # Check status
   jdc redis describe-cache-instance \
     --region-id cn-north-1 \
     --cache-instance-id jcs-redis-abc123 \
     --output json | jq '.result.cacheInstance.status'
   ```

4. **VPC/subnet mismatch**
   - Ensure application server and Redis are in same VPC
   - Check subnet routing and security groups

### Issue 2: High Memory Usage

**Symptoms:**
- Memory usage > 90%
- OOM errors
- Keys being evicted unexpectedly

**Solutions:**

1. **Analyze memory usage**
   ```bash
   redis-cli -h <endpoint> -p 6379 -a <password> INFO memory
   redis-cli -h <endpoint> -p 6379 -a <password> DBSIZE
   ```

2. **Find big keys**
   ```bash
   # Use JD Cloud analysis feature
   jdc redis create-big-key-analysis \
     --region-id cn-north-1 \
     --cache-instance-id jcs-redis-abc123 \
     --output json
   
   # Or use redis-cli
   redis-cli -h <endpoint> -p 6379 -a <password> --bigkeys
   ```

3. **Optimize eviction policy**
   ```bash
   jdc redis modify-instance-config \
     --region-id cn-north-1 \
     --cache-instance-id jcs-redis-abc123 \
     --instance-config '[{"parameterName":"maxmemory-policy","parameterValue":"allkeys-lru"}]' \
     --output json
   ```

4. **Scale up instance**
   ```bash
   jdc redis modify-cache-instance-class \
     --region-id cn-north-1 \
     --cache-instance-id jcs-redis-abc123 \
     --instance-class "redis.sw.16g" \
     --output json
   ```

### Issue 3: High CPU Usage

**Symptoms:**
- CPU usage > 80%
- High latency
- Slow command execution

**Solutions:**

1. **Check slow logs**
   ```bash
   jdc redis describe-slow-log \
     --region-id cn-north-1 \
     --cache-instance-id jcs-redis-abc123 \
     --output json
   ```

2. **Avoid blocking commands**
   - Replace `KEYS pattern` with `SCAN`
   - Avoid `HGETALL` on large hashes (use `HSCAN`)
   - Avoid `SMEMBERS` on large sets (use `SSCAN`)

3. **Optimize application code**
   - Use pipeline for batch operations
   - Avoid frequent small commands
   - Use appropriate data structures

4. **Check for hot keys**
   ```bash
   jdc redis create-cache-analysis \
     --region-id cn-north-1 \
     --cache-instance-id jcs-redis-abc123 \
     --output json
   ```

### Issue 4: Connection Pool Exhaustion

**Symptoms:**
- MAXCLIENTS errors
- Cannot create new connections
- Application connection timeout

**Solutions:**

1. **Check current connections**
   ```bash
   redis-cli -h <endpoint> -p 6379 -a <password> INFO clients
   ```

2. **Optimize connection pool**
   ```python
   # Python example (redis-py)
   import redis
   
   pool = redis.ConnectionPool(
       host='<endpoint>',
       port=6379,
       password='<password>',
       max_connections=50,  # Adjust based on needs
       socket_timeout=5,
       socket_connect_timeout=5
   )
   r = redis.Redis(connection_pool=pool)
   ```

3. **Check for connection leaks**
   - Ensure connections are properly closed
   - Use connection pool instead of creating new connections
   - Monitor idle connections

4. **Scale up instance** (higher specs support more connections)

### Issue 5: Replication Lag

**Symptoms:**
- Master-slave replication delay > 10 seconds
- Read inconsistency
- Failover risk

**Solutions:**

1. **Check replication status**
   ```bash
   redis-cli -h <endpoint> -p 6379 -a <password> INFO replication
   ```

2. **Identify causes:**
   - Network bandwidth saturation
   - Large write operations (big key creation)
   - Slow disk I/O (AOF persistence)

3. **Optimize:**
   - Reduce write throughput
   - Avoid big keys
   - Monitor network bandwidth
   - Consider cluster architecture for high write load

### Issue 6: Backup Failures

**Symptoms:**
- Backup status shows "failed"
- Backup size is 0
- Backup takes too long

**Solutions:**

1. **Check backup policy**
   ```bash
   jdc redis describe-backup-policy \
     --region-id cn-north-1 \
     --cache-instance-id jcs-redis-abc123 \
     --output json
   ```

2. **Verify storage quota**
   ```bash
   jdc redis describe-user-quota \
     --region-id cn-north-1 \
     --output json
   ```

3. **Retry manual backup**
   ```bash
   jdc redis create-backup \
     --region-id cn-north-1 \
     --cache-instance-id jcs-redis-abc123 \
     --backup-name "retry-backup-$(date +%Y%m%d%H%M%S)" \
     --output json
   ```

4. **Contact support** if backup consistently fails

## Performance Optimization Checklist

### Application Level
- [ ] Use connection pooling
- [ ] Implement retry logic with exponential backoff
- [ ] Use pipeline for batch operations
- [ ] Avoid blocking commands (KEYS, FLUSHALL)
- [ ] Set appropriate timeouts (connection, socket, command)
- [ ] Handle connection errors gracefully
- [ ] Use SCAN instead of KEYS for pattern matching

### Instance Level
- [ ] Choose appropriate instance spec (memory, connections)
- [ ] Configure eviction policy (allkeys-lru recommended)
- [ ] Enable AOF for data durability (if needed)
- [ ] Set maxmemory appropriately (70-80% of total)
- [ ] Disable dangerous commands (FLUSHALL, KEYS, CONFIG)
- [ ] Configure whitelist (least privilege)
- [ ] Enable monitoring and alerts

### Architecture Level
- [ ] Use master-slave for high availability
- [ ] Use cluster for horizontal scaling
- [ ] Deploy across multiple AZs for disaster recovery
- [ ] Implement read/write splitting if applicable
- [ ] Use local cache for hot keys
- [ ] Plan for capacity growth

## Emergency Procedures

### Procedure 1: Instance Unresponsive

1. **Check status**
   ```bash
   jdc redis describe-cache-instance \
     --region-id cn-north-1 \
     --cache-instance-id jcs-redis-abc123 \
     --output json
   ```

2. **Try restart** (if status allows)
   - Contact JD Cloud support for forced restart
   - Do NOT delete instance (data loss)

3. **Failover to backup** (if available)
   ```bash
   jdc redis restore-instance \
     --region-id cn-north-1 \
     --cache-instance-id jcs-redis-abc123 \
     --backup-id <latest-backup-id> \
     --output json
   ```

### Procedure 2: Data Corruption

1. **Stop writes** to prevent further corruption
2. **Identify corruption scope**
3. **Restore from backup**
   ```bash
   jdc redis restore-instance \
     --region-id cn-north-1 \
     --cache-instance-id jcs-redis-abc123 \
     --backup-id <backup-id-before-corruption> \
     --output json
   ```
4. **Verify data integrity**
5. **Resume operations**

### Procedure 3: Accidental Data Deletion

1. **Immediately stop application writes**
2. **Check available backups**
   ```bash
   jdc redis describe-backups \
     --region-id cn-north-1 \
     --cache-instance-id jcs-redis-abc123 \
     --output json
   ```
3. **Restore from latest backup before deletion**
4. **Replay recent writes** (if applicable)
5. **Implement safeguards** (disable FLUSHALL, use multiple accounts)

## Getting Help

### JD Cloud Support Channels

1. **Console**: Submit ticket via JD Cloud Console
2. **Phone**: Contact JD Cloud support hotline
3. **Documentation**: https://docs.jdcloud.com/cn/jcs-for-redis

### Information to Provide

When contacting support, include:
- Instance ID and region
- Error messages and codes
- Timestamp of issue
- Steps to reproduce
- Application logs (if applicable)
- Network topology (VPC, subnet, security groups)
