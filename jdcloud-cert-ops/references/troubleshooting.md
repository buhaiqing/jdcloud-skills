# Troubleshooting — JD Cloud SSL Certificate

## Common Issues

### Upload Failures

| Symptom | Cause | Solution |
|---------|-------|----------|
| `InvalidParameter` | Invalid PEM format | Verify cert/key are valid PEM |
| File not found | Incorrect file path | Use absolute paths |
| Key mismatch | Private key doesn't match cert | Verify key pair matches certificate |
| Expired cert | Certificate already expired | Upload a valid (non-expired) certificate |

### Download Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| MFA required | Download requires MFA | Enable MFA on account |
| Invalid server type | Unsupported server type | Use: Nginx, Apache, Tomcat, IIS, Other |

### Certificate Binding Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| CLB HTTPS not working | Certificate expired or mismatched | Check cert expiry; update CLB listener |
| CDN HTTPS not working | Certificate not applied to CDN domain | Update CDN domain cert binding |
| Domain mismatch | Cert domain doesn't match service domain | Upload cert for correct domain |

### Delete Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| MFA required | Delete requires MFA | Enable MFA on account |
| Cert still in use | Certificate bound to CLB/CDN | Unbind first, then delete |
| Service disruption | Deleting active cert breaks HTTPS | Verify no active bindings before delete |

### CLI-Specific Errors

| Symptom | Cause | Solution |
|---------|-------|----------|
| `unrecognized arguments: --output json` | `--output json` placed after subcommand | Place BEFORE subcommand |
| `PermissionError` on `~/.jdc/` | Sandbox home not writable | `export HOME=/tmp/jdc-home` |
| Authentication failure | Config file missing or wrong | Verify `~/.jdc/config` and `~/.jdc/current` |

### SDK-Specific Errors

| Symptom | Cause | Solution |
|---------|-------|----------|
| `ImportError` for `ssl` | SDK version too old | `uv pip install --upgrade jdcloud_sdk` |
| `JDCloudRequestException` | API error | Check `e.code` and `e.message` |

### Certificate Expiry Cruise Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| CLB listeners not found | Wrong region or no ALB | Verify region; check loadBalancerType filter |
| CDN certs not found | CDN not configured | Verify CDN domains exist |
| Date parsing error | Unexpected date format | Use `datetime.fromisoformat()` |
