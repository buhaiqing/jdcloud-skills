# Failure Patterns — jdcloud-routines-ops

> Cross-session failure memory for the GCL Reflexion integration.
> This file is loaded lazily during GCL Pre-flight (step [0]) to inject
> known failure patterns as prevention hints for the Generator.

## §1 CLI Parameter Errors

### Pattern: InvalidRegionId
- **Category**: cli_parameter
- **Skill**: jdcloud-routines-ops
- **Command**: `jdc vm describe-instances --region-id <invalid>`
- **Error**: `InvalidParameter: InvalidRegionId`
- **Fix**: Use valid JD Cloud region IDs (cn-north-1, cn-east-1, cn-south-1, etc.)
- **Count**: 1
- **Reusable**: true

### Pattern: MissingTimeRange
- **Category**: cli_parameter
- **Skill**: jdcloud-routines-ops
- **Command**: `jdc cloudmonitor describe-metric-data` (missing --start-time/--end-time)
- **Error**: `MissingParameter: time range is required`
- **Fix**: Always include --start-time and --end-time for metric queries
- **Count**: 1
- **Reusable**: true

## §2 Skill Generation Errors

### Pattern: CruiseScopeTooBroad
- **Category**: skill_generation
- **Skill**: jdcloud-routines-ops
- **Command**: Cruise all resources in all regions
- **Error**: Timeout or excessive API calls
- **Fix**: Limit cruise scope to specific regions or resource types
- **Count**: 1
- **Reusable**: true

### Pattern: RenewWithoutConfirm
- **Category**: skill_generation
- **Skill**: jdcloud-routines-ops
- **Command**: Renew expiring resources (without user confirmation)
- **Error**: Safety gate violation
- **Fix**: Always obtain explicit user confirmation before renewing resources
- **Count**: 1
- **Reusable**: true

## §3 Cross-Skill Integration Errors

### Pattern: VMNotFound
- **Category**: cross_skill
- **Skill**: jdcloud-routines-ops
- **Command**: Routine cruise targeting VM
- **Error**: VM not found in specified region
- **Fix**: Verify VM exists via `jdcloud-vm-ops` before cruise
- **Count**: 1
- **Reusable**: true

### Pattern: RedisClusterNotRunning
- **Category**: cross_skill
- **Skill**: jdcloud-routines-ops
- **Command**: Routine cruise targeting Redis
- **Error**: Redis cluster not in running state
- **Fix**: Verify Redis status via `jdcloud-redis-ops` before cruise
- **Count**: 1
- **Reusable**: true

## §4 Runtime Errors

### Pattern: ThrottlingRateLimit
- **Category**: runtime
- **Skill**: jdcloud-routines-ops
- **Command**: Any routine operation
- **Error**: `Throttling: Rate limit exceeded (HTTP 429)`
- **Fix**: Retry with exponential backoff; reduce request frequency
- **Count**: 1
- **Reusable**: true

### Pattern: LargeResultTimeout
- **Category**: runtime
- **Skill**: jdcloud-routines-ops
- **Command**: `jdc cloudmonitor describe-metric-data` (large time range)
- **Error**: Request timeout
- **Fix**: Use smaller time ranges or pagination
- **Count**: 1
- **Reusable**: true

### Pattern: CredentialMisconfigured
- **Category**: runtime
- **Skill**: jdcloud-routines-ops
- **Command**: Any routine operation
- **Error**: `Unauthorized: Invalid credentials`
- **Fix**: Verify `~/.jdc/config` has correct access_key and secret_key
- **Count**: 1
- **Reusable**: true

## §5 Token Efficiency Warnings

### Pattern: UnnecessaryDetail
- **Category**: token_efficiency
- **Skill**: jdcloud-routines-ops
- **Command**: `jdc vm describe-instances --output json` (full detail)
- **Warning**: Response too large, consumes excessive tokens
- **Fix**: Use filters or specific instance IDs to narrow results
- **Count**: 1
- **Reusable**: true

## Pattern Extraction Format

When a GCL iteration fails, extract failure pattern using this format:

```json
{
  "category": "cli_parameter|skill_generation|cross_skill|runtime|token_efficiency",
  "skill": "jdcloud-routines-ops",
  "command": "exact jdc command or SDK call",
  "error": "error message or code",
  "fix": "specific fix or remediation step",
  "reusable": true
}
```

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-06-19 | Initial failure patterns for `jdcloud-routines-ops` |
