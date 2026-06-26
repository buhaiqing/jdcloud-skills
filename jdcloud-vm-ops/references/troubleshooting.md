# JD Cloud VM Troubleshooting Reference

> **ponytail: trimmed — generic Linux troubleshooting removed. Only JD Cloud-specific error codes and diagnostic commands kept.**

## Common API Error Codes

| Code | HTTP | Likely Cause | Agent Action |
|------|------|-------------|--------------|
| `InvalidParameter` | 400 | Parameter validation failed | Check per OpenAPI, retry once |
| `InvalidInstanceType` | 400 | Instance type not supported | Query describe-instance-types, suggest alternatives |
| `InvalidImageId` | 400 | Image ID invalid | Verify image exists |
| `InvalidSubnetId` | 400 | Subnet ID invalid | Verify subnet in VPC |
| `QuotaExceeded` | 400 | Quota limit | HALT; suggest quota increase |
| `InsufficientBalance` | 400 | Account balance | HALT; top up |
| `InsufficientResource` | 400 | No capacity in AZ | Suggest another AZ |
| `ResourceNotFound` | 404 | Resource not found | Verify resource ID |
| `ForbiddenOperation` | 403 | Permission denied | Check IAM policies |
| `InternalError` | 500 | Server error | Retry with exponential backoff |
| `ServiceUnavailable` | 503 | Service down | Retry with backoff |

## Instance State Diagnostics

```bash
# Quick status check
jdc --output json vm describe-instances --region-id cn-north-1 --instance-ids '["i-xxx"]' | \
  jq '{id: .result.instances[0].instanceId, status: .result.instances[0].status, privateIp: .result.instances[0].primaryNetworkInterface.privateIpAddress}'

# Check security group rules
jdc --output json vpc describe-security-group --region-id cn-north-1 --security-group-id sg-xxx | \
  jq '.result.securityGroup.rules[] | select(.direction == "ingress")'

# Check EIP binding
jdc --output json vpc describe-elastic-ips --region-id cn-north-1 | \
  jq '.result.elasticIps[] | select(.instanceId == "i-xxx")'
```

## Common OS-Level Checks (quick reference)

| Symptom | Inside-VM Check |
|---------|-----------------|
| SSH timeout | Check security group port 22; check EIP binding |
| Disk full | `df -h` / `du -sh /* \| sort -rh \| head -10` |
| High CPU | `ps aux --sort=-%cpu \| head -10` / `top -bn1` |
| OOM | `dmesg \| grep -i "out of memory"` |
| No internet | `ip route show` (should have default gateway) |

> **Note**: OS-level troubleshooting is outside this skill's scope. For persistent issues, use VNC login from JD Cloud console to debug.