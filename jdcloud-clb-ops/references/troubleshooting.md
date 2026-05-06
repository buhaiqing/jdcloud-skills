# Troubleshooting — JD Cloud Load Balancer (CLB)

## Common API Error Codes

| Code / HTTP | Meaning | Agent Action |
|-------------|---------|--------------|
| InvalidParameter / 400 | Request failed validation | Align body with OpenAPI; check required fields |
| ResourceNotFound / 404 | Resource does not exist | Verify resource ID; check region |
| ResourceAlreadyExists / 409 | Resource with same name exists | Use different name or reuse existing resource |
| QuotaExceeded / 400 | Quota limit reached | HALT; user requests quota increase |
| InsufficientBalance / 400 | Account balance insufficient | HALT; user tops up account |
| SubnetIpInsufficient / 400 | Subnet has no available IPs | HALT; user expands subnet or chooses different subnet |
| InvalidResourceStatus / 400 | Resource in wrong state for operation | Wait for resource to reach appropriate state |
| InternalError / 500 | Internal server error | Retry with backoff; HALT if persists |
| ServiceUnavailable / 503 | Service temporarily unavailable | Retry with exponential backoff |
| Throttling / 429 | Rate limit exceeded | Back off; respect Retry-After header |

## Diagnostic Order

### 1. Load Balancer Issues

**LB Creation Fails**
```
1. Check VPC and subnet exist: jdcloud-vpc-ops describe-vpc/subnet
2. Verify subnet has available IPs
3. Check quota: describeLoadBalancers count vs limit
4. Verify AZ is valid for the region
```

**LB Status Stuck in Creating**
```
1. Poll describeLoadBalancer for 5 minutes
2. Check VPC/subnet configuration
3. Contact JD Cloud support if stuck > 10 minutes
```

**LB Not Accessible**
```
1. Check LB status is "active"
2. Verify security group rules allow traffic
3. Check listener configuration (protocol/port)
4. Verify backend targets are healthy
```

### 2. Listener Issues

**Listener Creation Fails**
```
1. Verify LB exists and is active
2. Check port is not already in use
3. Validate protocol is supported (TCP/UDP/HTTP/HTTPS)
4. For HTTPS: verify certificate is valid
```

**Traffic Not Routing**
```
1. Check listener protocol/port matches client request
2. Verify backend port is correct
3. Check target group association
4. Review health check status of targets
```

### 3. Backend Target Issues

**Targets Unhealthy**
```
1. Check VM status: jdcloud-vm-ops describe-instance
2. Verify security group allows health check probes
3. Check application is running on backend port
4. Review health check configuration (protocol/port/path)
5. Check VM system logs
```

**Target Registration Fails**
```
1. Verify VM exists and is running
2. Check target group exists
3. Verify port is valid (1-65535)
4. Check weight is between 1-100
```

### 4. Health Check Issues

**All Targets Unhealthy**
```
1. Verify health check protocol/port matches application
2. For HTTP checks: verify URL path returns 200 OK
3. Check response timeout vs application startup time
4. Review threshold settings (too strict?)
```

**Intermittent Health Status**
```
1. Check application stability
2. Review health check interval (too frequent?)
3. Verify network latency between LB and targets
4. Check VM resource utilization (CPU/memory)
```

## CLI-Specific Issues

### jdc CLI PermissionError

**Symptom:** `PermissionError: [Errno 13] Permission denied: '/home/user/.jdc'`

**Solution:**
```bash
# Use writable HOME directory
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc
# Create config files as shown in SKILL.md
```

### jdc CLI Authentication Failed

**Symptom:** `Please use 'jdc configure add' command to add cli configure first.`

**Solution:**
```bash
# Ensure config file exists and is properly formatted
cat ~/.jdc/config
# Should contain:
# [default]
# access_key = YOUR_KEY
# secret_key = YOUR_SECRET
# region_id = cn-north-1

# Ensure current profile is set
printf "%s" "default" > ~/.jdc/current
```

### jdc CLI Unrecognized Arguments

**Symptom:** `unrecognized arguments: --output json`

**Solution:**
```bash
# --output json must be BEFORE the subcommand
# WRONG:
jdc lb describe-load-balancers --output json

# CORRECT:
jdc --output json lb describe-load-balancers
```

## SDK-Specific Issues

### Import Errors

**Symptom:** `ModuleNotFoundError: No module named 'jdcloud_sdk'`

**Solution:**
```bash
source .venv/bin/activate
uv pip install jdcloud_sdk
```

### Authentication Errors

**Symptom:** `InvalidAccessKeyId.NotFound` or signature errors

**Solution:**
```bash
# Verify environment variables
export JDC_ACCESS_KEY="your-access-key"
export JDC_SECRET_KEY="your-secret-key"
export JDC_REGION="cn-north-1"
```

## Network Connectivity Issues

### LB VIP Not Responding

```
1. Check LB is external type (has public IP)
2. Verify security group allows inbound traffic
3. Check network ACL rules
4. Test from different network location
```

### Backend Servers Not Receiving Traffic

```
1. Verify target registration succeeded
2. Check target health status is "healthy"
3. Review listener backend port configuration
4. Check VM security groups allow LB subnet
```

## Performance Issues

### High Latency

```
1. Check LB specification (upgrade if needed)
2. Review backend server performance
3. Verify health check interval is not too aggressive
4. Check for cross-AZ traffic if not needed
```

### Connection Drops

```
1. Review idle connection timeout settings
2. Check backend server connection limits
3. Verify security group connection tracking
4. Review application keep-alive settings
```

## Getting Help

If issues persist after following this guide:

1. Collect request ID from API response
2. Gather relevant resource IDs (LB, listener, target)
3. Note timestamp of issue occurrence
4. Contact JD Cloud support with above information
