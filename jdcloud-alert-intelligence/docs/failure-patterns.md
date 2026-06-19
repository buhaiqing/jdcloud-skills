# Failure Patterns — jdcloud-alert-intelligence

> Cross-session failure memory for the GCL Reflexion integration.
> This file is loaded lazily during GCL Pre-flight (step [0]) to inject
> known failure patterns as prevention hints for the Generator.

## §1 CLI Parameter Errors

### Pattern: InvalidAlarmId
- **Category**: cli_parameter
- **Skill**: jdcloud-alert-intelligence
- **Command**: `jdc cloudmonitor describe-alarm-history --alarm-id <invalid>`
- **Error**: `InvalidParameter: InvalidAlarmId`
- **Fix**: Alarm ID must be in valid format
- **Count**: 1
- **Reusable**: true

### Pattern: MissingTimeRange
- **Category**: cli_parameter
- **Skill**: jdcloud-alert-intelligence
- **Command**: `jdc cloudmonitor describe-alarm-history` (missing --start-time/--end-time)
- **Error**: `MissingParameter: time range is required`
- **Fix**: Always include --start-time and --end-time for alarm history queries
- **Count**: 1
- **Reusable**: true

## §2 Skill Generation Errors

### Pattern: AlertAnalysisWithoutContext
- **Category**: skill_generation
- **Skill**: jdcloud-alert-intelligence
- **Command**: Analyze alert without resource context
- **Error**: Incomplete analysis or wrong recommendations
- **Fix**: Always gather resource context before alert analysis
- **Count**: 1
- **Reusable**: true

### Pattern: SuppressWithoutConfirm
- **Category**: skill_generation
- **Skill**: jdcloud-alert-intelligence
- **Command**: `jdc cloudmonitor disable-alarm-rule` (without user confirmation)
- **Error**: Safety gate violation
- **Fix**: Always obtain explicit user confirmation before suppressing alarms
- **Count**: 1
- **Reusable**: true

## §3 Cross-Skill Integration Errors

### Pattern: VMAlarmNotFound
- **Category**: cross_skill
- **Skill**: jdcloud-alert-intelligence
- **Command**: Alert analysis targeting VM alarm
- **Error**: Alarm not found for specified VM
- **Fix**: Verify alarm exists via `jdcloud-cloudmonitor-ops` before analysis
- **Count**: 1
- **Reusable**: true

### Pattern: RedisAlarmMetricsMissing
- **Category**: cross_skill
- **Skill**: jdcloud-alert-intelligence
- **Command**: Alert analysis targeting Redis alarm
- **Error**: Required metrics not available
- **Fix**: Verify Redis metrics are enabled via `jdcloud-redis-ops`
- **Count**: 1
- **Reusable**: true

## §4 Runtime Errors

### Pattern: ThrottlingRateLimit
- **Category**: runtime
- **Skill**: jdcloud-alert-intelligence
- **Command**: Any alert analysis operation
- **Error**: `Throttling: Rate limit exceeded (HTTP 429)`
- **Fix**: Retry with exponential backoff; reduce request frequency
- **Count**: 1
- **Reusable**: true

### Pattern: LargeAlarmHistoryTimeout
- **Category**: runtime
- **Skill**: jdcloud-alert-intelligence
- **Command**: `jdc cloudmonitor describe-alarm-history` (large time range)
- **Error**: Request timeout
- **Fix**: Use smaller time ranges or pagination
- **Count**: 1
- **Reusable**: true

### Pattern: CredentialMisconfigured
- **Category**: runtime
- **Skill**: jdcloud-alert-intelligence
- **Command**: Any alert analysis operation
- **Error**: `Unauthorized: Invalid credentials`
- **Fix**: Verify `~/.jdc/config` has correct access_key and secret_key
- **Count**: 1
- **Reusable**: true

## §5 Token Efficiency Warnings

### Pattern: UnnecessaryAlarmHistory
- **Category**: token_efficiency
- **Skill**: jdcloud-alert-intelligence
- **Command**: `jdc cloudmonitor describe-alarm-history --output json` (full detail)
- **Warning**: Response too large, consumes excessive tokens
- **Fix**: Use filters or specific alarm IDs to narrow results
- **Count**: 1
- **Reusable**: true

## Pattern Extraction Format

When a GCL iteration fails, extract failure pattern using this format:

```json
{
  "category": "cli_parameter|skill_generation|cross_skill|runtime|token_efficiency",
  "skill": "jdcloud-alert-intelligence",
  "command": "exact jdc command or SDK call",
  "error": "error message or code",
  "fix": "specific fix or remediation step",
  "reusable": true
}
```

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-06-19 | Initial failure patterns for `jdcloud-alert-intelligence` |
