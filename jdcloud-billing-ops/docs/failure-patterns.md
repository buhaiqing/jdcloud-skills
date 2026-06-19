# Failure Patterns — jdcloud-billing-ops

> Cross-session failure memory for the GCL Reflexion integration.
> This file is loaded lazily during GCL Pre-flight (step [0]) to inject
> known failure patterns as prevention hints for the Generator.

## §1 SDK Parameter Errors

### Pattern: InvalidTimeRange
- **Category**: cli_parameter
- **Skill**: jdcloud-billing-ops
- **Command**: `client.queryBill()` with invalid time range
- **Error**: `InvalidParameter: InvalidTimeRange`
- **Fix**: Time range must be valid and within billing retention period
- **Count**: 1
- **Reusable**: true

### Pattern: MissingRegionId
- **Category**: cli_parameter
- **Skill**: jdcloud-billing-ops
- **Command**: Any SDK call (missing regionId in request)
- **Error**: `MissingParameter: regionId is required`
- **Fix**: Always include regionId in every SDK request
- **Count**: 1
- **Reusable**: true

## §2 Skill Generation Errors

### Pattern: QueryWithoutTimeRange
- **Category**: skill_generation
- **Skill**: jdcloud-billing-ops
- **Command**: `client.queryBill()` (missing time range)
- **Error**: `MissingParameter: time range is required`
- **Fix**: Always include start time and end time for billing queries
- **Count**: 1
- **Reusable**: true

### Pattern: EstimateCostWithoutSpec
- **Category**: skill_generation
- **Skill**: jdcloud-billing-ops
- **Command**: `client.estimateCost()` (missing resource specification)
- **Error**: `InvalidParameter: resource spec is required`
- **Fix**: Provide complete resource specification for cost estimation
- **Count**: 1
- **Reusable**: true

## §3 Cross-Skill Integration Errors

### Pattern: VMResourceNotFound
- **Category**: cross_skill
- **Skill**: jdcloud-billing-ops
- **Command**: Billing query for VM resource
- **Error**: VM resource not found in billing records
- **Fix**: Verify VM exists and is billed via `jdcloud-vm-ops`
- **Count**: 1
- **Reusable**: true

### Pattern: RedisResourceNotFound
- **Category**: cross_skill
- **Skill**: jdcloud-billing-ops
- **Command**: Billing query for Redis resource
- **Error**: Redis resource not found in billing records
- **Fix**: Verify Redis exists via `jdcloud-redis-ops`
- **Count**: 1
- **Reusable**: true

## §4 Runtime Errors

### Pattern: ThrottlingRateLimit
- **Category**: runtime
- **Skill**: jdcloud-billing-ops
- **Command**: Any SDK operation
- **Error**: `Throttling: Rate limit exceeded (HTTP 429)`
- **Fix**: Retry with exponential backoff; reduce request frequency
- **Count**: 1
- **Reusable**: true

### Pattern: InternalServerError
- **Category**: runtime
- **Skill**: jdcloud-billing-ops
- **Command**: Any SDK operation
- **Error**: `InternalError: Server error (HTTP 500)`
- **Fix**: Retry with backoff; contact support if persistent
- **Count**: 1
- **Reusable**: true

### Pattern: CredentialMisconfigured
- **Category**: runtime
- **Skill**: jdcloud-billing-ops
- **Command**: Any SDK operation
- **Error**: `Unauthorized: Invalid credentials`
- **Fix**: Verify environment variables JDC_ACCESS_KEY and JDC_SECRET_KEY
- **Count**: 1
- **Reusable**: true

## §5 Token Efficiency Warnings

### Pattern: LargeBillResult
- **Category**: token_efficiency
- **Skill**: jdcloud-billing-ops
- **Command**: `client.queryBill()` (large time range)
- **Warning**: Response too large, consumes excessive tokens
- **Fix**: Use smaller time ranges or pagination
- **Count**: 1
- **Reusable**: true

## Pattern Extraction Format

When a GCL iteration fails, extract failure pattern using this format:

```json
{
  "category": "cli_parameter|skill_generation|cross_skill|runtime|token_efficiency",
  "skill": "jdcloud-billing-ops",
  "command": "exact SDK call",
  "error": "error message or code",
  "fix": "specific fix or remediation step",
  "reusable": true
}
```

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-06-19 | Initial failure patterns for `jdcloud-billing-ops` |
