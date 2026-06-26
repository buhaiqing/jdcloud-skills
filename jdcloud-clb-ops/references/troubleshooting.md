# Troubleshooting — JD Cloud Load Balancer (CLB)

> **ponytail: trimmed — error codes + diagnostic order kept. General network troubleshooting is OS-level, out of scope.**

## Common API Error Codes

| Code / HTTP | Likely Cause | Agent Action |
|-------------|--------------|--------------|
| InvalidParameter / 400 | Parameter validation failed | Align with OpenAPI; retry once |
| ResourceNotFound / 404 | LB/resource not found | Verify ID and region |
| ResourceAlreadyExists / 409 | Duplicate name | Use different name or reuse |
| QuotaExceeded / 400 | Quota full | HALT; request increase |
| InsufficientBalance / 400 | Balance low | HALT; top up account |
| SubnetIpInsufficient / 400 | Subnet full | HALT; expand subnet or choose another |
| InternalError / 500 | Server error | Retry with backoff (2s/4s/8s) |
| ServiceUnavailable / 503 | Service down | Retry with backoff |
| Throttling / 429 | Rate limit | Back off; respect Retry-After |

## Diagnostic Flows

### LB Not Accessible
1. Check LB status is `active` (`describeLoadBalancer`)
2. Verify security group allows traffic
3. Check listener config (protocol/port match)
4. Verify backend targets are healthy

### Targets Marked Unhealthy
1. Check VM is `running` via `jdcloud-vm-ops`
2. Verify security group allows health check probes
3. Confirm app is listening on backend port
4. Review health check config (protocol/port/path)
5. Check VM CPU/memory/utilization

### Traffic Not Reaching Backend
1. Verify target registration succeeded
2. Check target health is `healthy`
3. Confirm listener backend port matches target port
4. Check VM's security group allows LB subnet CIDR

## CLI-Specific Issues

| Symptom | Fix |
|---------|-----|
| `PermissionError: .jdc` | `export HOME=/tmp/jdc-home` (writable) |
| `unrecognized arguments: --output json` | Put `--output json` BEFORE subcommand |
| Auth failed | Check `~/.jdc/config` exists and is valid |
| SDK `ModuleNotFoundError` | `source .venv/bin/activate` then reinstall |