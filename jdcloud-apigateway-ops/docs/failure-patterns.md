# Failure Patterns — jdcloud-apigateway-ops

> Cross-session failure memory for the GCL Reflexion integration.
> This file is loaded lazily during GCL Pre-flight (step [0]) to inject
> known failure patterns as prevention hints for the Generator.

## §1 SDK Parameter Errors

### Pattern: InvalidApiGroupId
- **Category**: cli_parameter
- **Skill**: jdcloud-apigateway-ops
- **Command**: `client.describeApiGroups()` with invalid apiGroupId
- **Error**: `InvalidParameter: InvalidApiGroupId`
- **Fix**: API group ID must be in valid format
- **Count**: 1
- **Reusable**: true

### Pattern: MissingRegionId
- **Category**: cli_parameter
- **Skill**: jdcloud-apigateway-ops
- **Command**: Any SDK call (missing regionId in request)
- **Error**: `MissingParameter: regionId is required`
- **Fix**: Always include regionId in every SDK request
- **Count**: 1
- **Reusable**: true

### Pattern: InvalidStageName
- **Category**: cli_parameter
- **Skill**: jdcloud-apigateway-ops
- **Command**: `client.deployApi()` with invalid stageName
- **Error**: `InvalidParameter: InvalidStageName`
- **Fix**: Use valid stage names (test, pre, prod, etc.)
- **Count**: 1
- **Reusable**: true

## §2 Skill Generation Errors

### Pattern: DeployWithoutConfirm
- **Category**: skill_generation
- **Skill**: jdcloud-apigateway-ops
- **Command**: `client.deployApi()` to prod stage (without user confirmation)
- **Error**: Safety gate violation
- **Fix**: Always obtain explicit user confirmation before deploying to prod
- **Count**: 1
- **Reusable**: true

### Pattern: DeleteGroupWithDeployedApis
- **Category**: skill_generation
- **Skill**: jdcloud-apigateway-ops
- **Command**: `client.deleteApiGroup()` (when group has deployed APIs)
- **Error**: `GroupHasDeployedApis`
- **Fix**: Undeploy all APIs first before deleting group
- **Count**: 1
- **Reusable**: true

### Pattern: InvalidBackendUrl
- **Category**: skill_generation
- **Skill**: jdcloud-apigateway-ops
- **Command**: `client.createApi()` with invalid backend URL
- **Error**: `InvalidParameter: InvalidBackendUrl`
- **Fix**: Backend URL must be valid HTTP/HTTPS URL
- **Count**: 1
- **Reusable**: true

## §3 Cross-Skill Integration Errors

### Pattern: VPCNotReady
- **Category**: cross_skill
- **Skill**: jdcloud-apigateway-ops
- **Command**: API Gateway targeting backend in VPC
- **Error**: Backend not accessible from API Gateway
- **Fix**: Verify VPC and subnet configuration via `jdcloud-vpc-ops`
- **Count**: 1
- **Reusable**: true

### Pattern: FCFunctionNotFound
- **Category**: cross_skill
- **Skill**: jdcloud-apigateway-ops
- **Command**: API Gateway targeting Function Compute backend
- **Error**: Function not found
- **Fix**: Verify function exists via `jdcloud-fc-ops` before creating API
- **Count**: 1
- **Reusable**: true

## §4 Runtime Errors

### Pattern: ThrottlingRateLimit
- **Category**: runtime
- **Skill**: jdcloud-apigateway-ops
- **Command**: Any SDK operation
- **Error**: `Throttling: Rate limit exceeded (HTTP 429)`
- **Fix**: Retry with exponential backoff; reduce request frequency
- **Count**: 1
- **Reusable**: true

### Pattern: InternalServerError
- **Category**: runtime
- **Skill**: jdcloud-apigateway-ops
- **Command**: Any SDK operation
- **Error**: `InternalError: Server error (HTTP 500)`
- **Fix**: Retry with backoff; contact support if persistent
- **Count**: 1
- **Reusable**: true

### Pattern: CredentialMisconfigured
- **Category**: runtime
- **Skill**: jdcloud-apigateway-ops
- **Command**: Any SDK operation
- **Error**: `Unauthorized: Invalid credentials`
- **Fix**: Verify environment variables JDC_ACCESS_KEY and JDC_SECRET_KEY
- **Count**: 1
- **Reusable**: true

## §5 Token Efficiency Warnings

### Pattern: LargeApiListResult
- **Category**: token_efficiency
- **Skill**: jdcloud-apigateway-ops
- **Command**: `client.describeApis()` (large result set)
- **Warning**: Response too large, consumes excessive tokens
- **Fix**: Use pagination or filters to narrow results
- **Count**: 1
- **Reusable**: true

## Pattern Extraction Format

When a GCL iteration fails, extract failure pattern using this format:

```json
{
  "category": "cli_parameter|skill_generation|cross_skill|runtime|token_efficiency",
  "skill": "jdcloud-apigateway-ops",
  "command": "exact SDK call",
  "error": "error message or code",
  "fix": "specific fix or remediation step",
  "reusable": true
}
```

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-06-19 | Initial failure patterns for `jdcloud-apigateway-ops` |
