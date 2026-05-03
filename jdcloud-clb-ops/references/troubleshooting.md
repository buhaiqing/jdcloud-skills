# Troubleshooting JD Cloud Load Balancer

## Common API Error Codes

| Code / HTTP | Meaning | Agent Action |
|-------------|---------|--------------|
| `InvalidParameter` / 400 | Request failed validation | Align request body with OpenAPI; check required fields, enums, and formats |
| `NameAlreadyExists` / 409 | LB name duplicate in region | Ask user for unique name; retry create |
| `ResourceNotFound` / 404 | LB, listener, or target group does not exist | Verify ID; check region consistency |
| `QuotaExceeded` / 400 | LB count limit reached | HALT; user requests quota increase via support |
| `InsufficientBalance` / 400 | Account balance insufficient | HALT; user tops up account |
| `VpcNotFound` / 404 | VPC ID invalid or not in this region | Verify VPC via `jdcloud-vpc-ops`; create if needed |
| `SubnetNotFound` / 404 | Subnet ID invalid | Verify subnet exists in target AZ |
| `CertificateNotFound` / 404 | SSL certificate not found | Verify certificate ID via SSL service |
| `PermissionDenied` / 403 | IAM policy restricts this operation | HALT; user adjusts IAM permissions |
| `Throttling` / 429 | Request rate exceeded | Back off exponentially; respect Retry-After header |
| `InternalError` / 500 | Server-side error | Retry up to 3 times with backoff; then HALT with requestId |
| `DependencyError` / 500 | Dependent resource error (e.g., EIP bind failed) | Check dependent resource status; retry after fix |

## Diagnostic Order

### Load Balancer Creation Failure

1. **Check credentials**: Verify `JDC_ACCESS_KEY` and `JDC_SECRET_KEY` are set.
2. **Check region**: Ensure `regionId` matches a supported region (cn-north-1, cn-east-1, etc.).
3. **Check VPC**: Call describeVpc to confirm VPC exists and is in the same region.
4. **Check subnet**: Verify subnet IDs exist and belong to target AZs.
5. **Check quota**: List existing LBs; compare against quota limit.
6. **Check name uniqueness**: List LBs to verify name is not duplicate.

### Listener Creation Failure

1. **Check LB status**: describeLoadBalancer must return `active`.
2. **Check protocol**: ALB supports HTTP/HTTPS/TLS; NLB supports TCP/UDP.
3. **Check port availability**: List existing listeners; verify port not in use.
4. **Check certificate (HTTPS/TLS)**: Verify certificate ID and binding permissions.
5. **Check TLS policy**: If custom, verify policy exists.

### Target Registration Failure

1. **Check target group**: describeTargetGroup must return valid group.
2. **Check backend type**: VM ID, container ID, or IP address format.
3. **Check VM status**: VM must be `running` (verify via `jdcloud-vm-ops`).
4. **Check port range**: 1-65535 valid range.
5. **Check weight**: 0-100 valid range (0 means no traffic).
6. **Check network ACL**: Backend subnet ACL must allow LB VIP traffic.

### Health Check Failures

1. **Check health check config**: Protocol, port, path, interval, threshold values.
2. **Check backend response**: Backend service must respond correctly on health check path.
3. **Check firewall rules**: Backend VM security group must allow health check port.
4. **Check network ACL**: Subnet ACL must allow health check source IP.
5. **Check backend logs**: Review backend application logs for connection issues.

## Common Issue Patterns

### Issue: Backend Servers Show "unhealthy"

**Symptoms**: All or some targets marked unhealthy in describeTargetHealth.

**Diagnosis**:
1. Check health check protocol/port matches backend application.
2. Verify backend application responds on health check path (HTTP: `/health`, etc.).
3. Check security group inbound rules for health check port.
4. Verify subnet network ACL allows LB VIP → backend traffic.
5. Check backend application logs for errors.

**Resolution**: Adjust health check parameters, fix security group rules, or repair backend application.

### Issue: HTTPS Listener Certificate Error

**Symptoms**: TLS handshake fails, client receives certificate errors.

**Diagnosis**:
1. Check certificate validity period (not expired).
2. Verify certificate domain matches client request host.
3. Check certificate is correctly bound to listener (describeListener).
4. Verify TLS policy enables required cipher suites.
5. Check SNI configuration for multi-domain certificates.

**Resolution**: Replace expired certificate, add matching domain certificate, or adjust TLS policy.

### Issue: Load Balancer VIP Not Accessible

**Symptoms**: VIP unreachable from clients.

**Diagnosis**:
1. Check EIP binding for public LB (describeLoadBalancer → eip field).
2. Check LB status is `active`.
3. Verify listener exists on target port.
4. Check VPC/subnet routing tables.
5. Check security group rules on LB (if bound).
6. Verify client network connectivity to region.

**Resolution**: Bind EIP, wait for LB activation, configure listener, adjust routing/security rules.

### Issue: Session Persistence Not Working

**Symptoms**: Client requests distributed to different backends despite session config.

**Diagnosis**:
1. Verify session persistence enabled on backend service.
2. Check session persistence type matches protocol (cookie for HTTP, source IP for TCP).
3. Verify cookie name configuration (HTTP cookie persistence).
4. Check backend weights are non-zero.
5. Verify health check not failing (unhealthy targets excluded).

**Resolution**: Enable/reconfigure session persistence, fix health check issues.

### Issue: Cross-AZ Failover Not Working

**Symptoms**: Traffic not redistributed when AZ fails.

**Diagnosis**:
1. Check LB AZ configuration (must have multiple AZs).
2. Verify backend servers distributed across AZs.
3. Check AZ health status.
4. Verify routing tables allow cross-AZ traffic.

**Resolution**: Configure multi-AZ deployment, distribute backends across AZs.

## Error Resolution Matrix

| Error | Resolution |
|-------|------------|
| `InvalidParameter.NameAlreadyExists` | Rename LB; ensure uniqueness |
| `InvalidParameter.PortInUse` | Choose different port; delete existing listener |
| `InvalidParameter.VpcNotFound` | Create VPC first; verify region match |
| `InvalidParameter.SubnetNotFound` | Create subnet; verify AZ match |
| `InvalidParameter.QuotaExceeded` | Request quota increase via JD Cloud support |
| `InvalidParameter.InsufficientBalance` | Top up account balance |
| `InvalidParameter.CertificateNotFound` | Upload/bind certificate first |
| `DependencyError.EipBindFailed` | Check EIP status; verify EIP not already bound |
| `InternalError` | Retry with exponential backoff; report requestId to support |

## Logging and Debugging

### SDK Debug Mode

Enable SDK debug logging to trace request/response:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
# SDK will log HTTP request/response details
```

### Request Correlation

Capture `requestId` from every API response for troubleshooting:

```python
resp = client.createLoadBalancer(req)
request_id = resp.requestId  # Use this for support ticket
```

### Health Check Debug

Use describeTargetHealth to inspect backend status:

```python
resp = client.describeTargetHealth(req)
for target in resp.result.targets:
    print(f"Target: {target.targetId}, Health: {target.healthStatus}")
```

## Support Resources

- JD Cloud Support: https://ticket.jdcloud.com/
- ALB Documentation: https://docs.jdcloud.com/cn/application-load-balancer/
- NLB Documentation: https://docs.jdcloud.com/cn/network-load-balancer/
- API Reference: https://docs.jdcloud.com/cn/application-load-balancer/api-overview