# Troubleshooting JD Cloud Elasticsearch

## Common API Error Codes

| Code / HTTP | Meaning | Agent Action |
|-------------|---------|--------------|
| `InvalidParameter` / 400 | Request failed validation | Align body with OpenAPI; check parameter types |
| `MissingParameter` / 400 | Required parameter missing | Add all required fields per API spec |
| `ResourceNotFound` / 404 | Instance or resource not found | Verify instance ID and region |
| `ResourceInUse` / 409 | Resource is busy with another operation | Wait and retry with exponential backoff |
| `QuotaExceeded` / 429 | Resource quota exceeded | HALT; user requests quota increase |
| `InsufficientBalance` / 400 | Account balance insufficient | HALT; user tops up account |
| `SubnetIpInsufficient` / 400 | Subnet has no available IPs | HALT; user expands subnet or chooses another |
| `InvalidVersion` / 400 | Unsupported ES version | Check available versions via describeInstanceClass |
| `InvalidInstanceClass` / 400 | Invalid instance specification | Check available classes via describeInstanceClass |
| `InternalError` / 500 | Internal server error | Retry with backoff; HALT if persists |
| `ServiceUnavailable` / 503 | Service temporarily unavailable | Retry with exponential backoff |

## Diagnostic Order

### For Instance Creation Failures

1. **Check VPC/Subnet**
   ```bash
   jdc --output json vpc describe-vpc --region-id cn-north-1 --vpc-id vpc-xxx
   jdc --output json vpc describe-subnet --region-id cn-north-1 --subnet-id subnet-xxx
   ```
   - Verify VPC exists and is in correct region
   - Verify subnet has available IP addresses

2. **Check Instance Class Availability**
   ```bash
   jdc --output json es describe-instance-class --region-id cn-north-1
   ```
   - Verify instance class is available in region
   - Check version compatibility

3. **Check Quotas**
   - Instance count quota per region
   - Node count quota per instance

### For Instance Operation Failures

1. **Describe Instance Status**
   ```bash
   jdc --output json es describe-instance --region-id cn-north-1 --instance-id es-xxx
   ```
   - Check `status` field
   - Valid states: `creating`, `running`, `stopping`, `stopped`, `error`, `deleting`, `deleted`

2. **Check Instance Health**
   - Use CloudMonitor metrics
   - Check cluster health via ES API (if accessible)

### For Snapshot/Restore Failures

1. **List Snapshots**
   ```bash
   jdc --output json es describe-snapshots --region-id cn-north-1 --instance-id es-xxx
   ```

2. **Check OSS Bucket**
   - Verify snapshot repository is accessible
   - Check OSS bucket permissions

## Common Issues and Solutions

### Issue: Instance stuck in "creating" state

**Possible Causes:**
- Subnet IP exhaustion
- Insufficient account balance
- Resource quota exceeded

**Resolution:**
1. Check account balance
2. Verify subnet has available IPs
3. Check resource quotas
4. Contact support if persists > 30 minutes

### Issue: Cannot connect to ES endpoint

**Possible Causes:**
- Security group rules blocking access
- IP whitelist not configured
- Network connectivity issues
- Instance not in "running" state

**Resolution:**
1. Verify instance status is "running"
   ```bash
   jdc --output json es describe-instance --region-id cn-north-1 --instance-id es-xxx
   ```
2. Check security group rules allow traffic on port 9200
3. Verify IP whitelist includes client IP (if public access enabled)
4. Test connectivity from within VPC

### Issue: Kibana not accessible

**Possible Causes:**
- Kibana node not enabled
- Network/firewall issues
- Kibana service not ready

**Resolution:**
1. Verify Kibana node is configured
2. Check Kibana URL in describe-instance response
3. Wait for Kibana to fully start (can take 5-10 minutes)
4. Check security group rules for port 5601

### Issue: Snapshot creation fails

**Possible Causes:**
- Insufficient OSS bucket permissions
- Snapshot repository not configured
- Instance in unstable state

**Resolution:**
1. Verify OSS bucket exists and is accessible
2. Check instance status is "running"
3. Retry after ensuring cluster is healthy
4. Check OSS bucket policy and permissions

### Issue: High memory usage / OOM

**Possible Causes:**
- Insufficient heap size for workload
- Too many shards per node
- Memory-intensive queries

**Resolution:**
1. Scale up to larger instance class
2. Optimize index settings (reduce shard count)
3. Review and optimize queries
4. Add more data nodes to distribute load

### Issue: Cluster health red/yellow

**Possible Causes:**
- Unassigned shards
- Node failures
- Disk space issues

**Resolution:**
1. Check node status via CloudMonitor
2. Verify disk space is not full
3. Check for unassigned shards via ES API
4. Restart failed nodes if necessary
5. Scale storage or add nodes if disk full

## Log Locations

| Log Type | Location | Access Method |
|----------|----------|---------------|
| ES Logs | Cloud Logs Service | Via console or API |
| Audit Logs | Cloud Logs Service | Via console or API |
| Slow Query Logs | Cloud Logs Service | Via console or API |
| Access Logs | Cloud Logs Service | Via console or API |

## Support and Escalation

| Issue Severity | Response Time | Action |
|----------------|---------------|--------|
| Critical (production down) | 15 minutes | Open urgent ticket |
| High (performance degraded) | 1 hour | Open high priority ticket |
| Medium (non-critical issue) | 4 hours | Open standard ticket |
| Low (question/inquiry) | 1 business day | Open general ticket |

**Ticket Information to Include:**
- Instance ID
- Region
- Request ID (from API response)
- Timestamp of issue
- Error message / code
- Steps to reproduce
