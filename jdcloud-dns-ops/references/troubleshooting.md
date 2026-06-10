# Troubleshooting — JD Cloud DNS

## Common Issues

### Domain Addition Failures

| Symptom | Cause | Solution |
|---------|-------|----------|
| `InvalidParameter` | Invalid domain name format | Use valid FQDN (e.g., `example.com`) |
| `QuotaExceeded` | Domain limit reached | Upgrade package or remove unused domains |
| `InsufficientBalance` | Insufficient funds for paid package | Top up account |
| Duplicate domain error | Domain already exists in account | Use `describe-domains` to check |

### Resource Record Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| Record creation fails | Invalid value format | Validate per type (A=IPv4, AAAA=IPv6, etc.) |
| CNAME at apex error | CNAME at zone apex violates RFC | Use A/AAAA records instead |
| MX missing priority | MX record requires priority field | Add priority (e.g., `10 mail.example.com.`) |
| Conflicting records | Same host+type already exists | Modify existing or use different host |
| TTL too low/high | TTL outside valid range | Use 60-86400 seconds |

### Resolution Not Working

| Symptom | Cause | Solution |
|---------|-------|----------|
| DNS not resolving | Propagation delay | Wait up to TTL + propagation time |
| Wrong IP returned | Incorrect record value | Verify with `describe-resource-record` |
| CNAME chain broken | Target CNAME doesn't resolve | Verify target hostname exists |
| Record disabled | Record status is `off` | Enable with `modify-resource-record-status --action on` |

### CLI-Specific Errors

| Symptom | Cause | Solution |
|---------|-------|----------|
| `unrecognized arguments: --output json` | `--output json` placed after subcommand | Place BEFORE subcommand |
| `PermissionError` on `~/.jdc/` | Sandbox home not writable | `export HOME=/tmp/jdc-home` |
| `TypeError` on `--help` | Known jdc CLI bug in help formatter | Use SKILL.md for parameter reference |
| Authentication failure | Config file missing or wrong | Verify `~/.jdc/config` and `~/.jdc/current` |

### SDK-Specific Errors

| Symptom | Cause | Solution |
|---------|-------|----------|
| `ImportError` for `domainservice` | SDK version too old | `uv pip install --upgrade jdcloud_sdk` |
| `JDCloudRequestException` | API error | Check `e.code` and `e.message` |
| Empty response | Pagination issue | Check `pageNumber` and `pageSize` |

### Rate Limiting

| Symptom | Solution |
|---------|----------|
| HTTP 429 / Throttling | Implement exponential backoff (0s → 2s → 4s) |
| Frequent 429s | Reduce request rate; batch operations where possible |

### Permission Errors

| Symptom | Solution |
|---------|----------|
| Access denied | Verify IAM policy includes DNS permissions |
| Region mismatch | DNS is global; use `cn-north-1` as default region |
