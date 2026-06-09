# Troubleshooting WAF

## Common API/CLI Error Codes

| Code | HTTP | Meaning | Agent Action |
|------|------|---------|--------------|
| `InstanceNotFound` | 404 | WAF instance does not exist | Verify instance ID |
| `DomainNotFound` | 404 | Domain not found in WAF | Verify domain ID |
| `DomainAlreadyExists` | 409 | Domain already protected | Use existing or remove first |
| `InvalidDomain` | 400 | Domain format invalid | Check domain syntax |
| `InvalidCert` | 400 | Certificate invalid | Verify cert format and validity |
| `CertMismatch` | 400 | Cert doesn't match domain | Get matching certificate |
| `OriginUnreachable` | 400 | Cannot reach origin | Check origin IP/port |
| `QuotaExceeded` | 400 | Domain/rule quota exceeded | Request quota increase |
| `InstanceNotEmpty` | 400 | Instance has domains | Remove domains before delete |
| `RuleNotFound` | 404 | Rule does not exist | Verify rule ID |
| `InvalidRule` | 400 | Rule syntax error | Check rule JSON |

## DNS Issues
- **Symptom**: Traffic not going through WAF
- **Check**: DNS lookup for domain CNAME
- **Fix**: Ensure CNAME points to WAF-provided CNAME

## SSL/TLS Issues
- **Symptom**: HTTPS errors, certificate warnings
- **Check**: Certificate validity, domain match, chain completeness
- **Fix**: Re-upload valid certificate

## False Positives
- **Symptom**: Legitimate traffic blocked
- **Fix**:
  1. Check attack logs for blocked requests
  2. Add IP to whitelist or adjust rule
  3. Change rule from "block" to "log" temporarily

## Origin Connection Failures
- **Symptom**: 502/504 errors from WAF
- **Check**: Origin server health, security group rules
- **Fix**: Ensure origin accepts connections from WAF IPs

## Performance Issues
- **Symptom**: High latency through WAF
- **Check**: QPS vs package limits, rule complexity
- **Fix**: Upgrade package or optimize rules