# Failure Patterns — jdcloud-oss-ops

> Cross-session failure memory for the GCL Reflexion integration.
> This file is loaded lazily during GCL Pre-flight (step [0]) to inject
> known failure patterns as prevention hints for the Generator.

> **Note**: `jdcloud-oss-ops` is SDK-only — OSS is not exposed via the `jdc` CLI.
> All command examples below use Python SDK calls instead of `jdc` commands.

## §1 CLI Parameter Errors

### Pattern: InvalidResourceId
- **Category**: cli_parameter
- **Skill**: jdcloud-oss-ops
- **Command**: `client.describe_bucket(bucket_name='<invalid>')`
- **Error**: `InvalidParameter: InvalidResourceId`
- **Fix**: Resource ID must be in valid format (bucket name must match DNS-compatible pattern)
- **Count**: 1
- **Reusable**: true

### Pattern: MissingRegionId
- **Category**: cli_parameter
- **Skill**: jdcloud-oss-ops
- **Command**: `client.describe_buckets()` (missing region_id)
- **Error**: `MissingParameter: regionId is required`
- **Fix**: Always include region_id in every SDK call
- **Count**: 1
- **Reusable**: true

### Pattern: WrongOutputJsonPosition
- **Category**: cli_parameter
- **Skill**: jdcloud-oss-ops
- **Command**: `client.describe_buckets(output='json')` (not supported in SDK)
- **Error**: `TypeError: unexpected keyword argument 'output'`
- **Fix**: SDK calls return Python dicts; use `json.dumps()` to serialize output
- **Count**: 1
- **Reusable**: true

## §2 Skill Generation Errors

### Pattern: DeleteResourceInUse
- **Category**: skill_generation
- **Skill**: jdcloud-oss-ops
- **Command**: `client.delete_bucket(bucket_name='<name>')` (when bucket is non-empty)
- **Error**: `ResourceInUse`
- **Fix**: Stop/detach dependent resources first before deleting (empty the bucket first)
- **Count**: 1
- **Reusable**: true

### Pattern: QuotaExceeded
- **Category**: skill_generation
- **Skill**: jdcloud-oss-ops
- **Command**: `client.create_bucket(bucket_name='<name>')`
- **Error**: `QuotaExceeded: resource quota exceeded`
- **Fix**: Request quota increase or release unused resources first
- **Count**: 1
- **Reusable**: true

## §3 Cross-Skill Integration Errors

### Pattern: VPCDependenciesNotMet
- **Category**: cross_skill
- **Skill**: jdcloud-oss-ops
- **Command**: Resource creation in VPC
- **Error**: VPC not found or not ready
- **Fix**: Verify VPC exists via `jdcloud-vpc-ops` before resource creation
- **Count**: 1
- **Reusable**: true

### Pattern: IAMPermissionDenied
- **Category**: cross_skill
- **Skill**: jdcloud-oss-ops
- **Command**: Operations with insufficient IAM permissions
- **Error**: `Unauthorized: IAM permission denied`
- **Fix**: Verify IAM permissions via `jdcloud-iam-ops`
- **Count**: 1
- **Reusable**: true

## §4 Runtime Errors

### Pattern: ThrottlingRateLimit
- **Category**: runtime
- **Skill**: jdcloud-oss-ops
- **Command**: Any operation
- **Error**: `Throttling: Rate limit exceeded (HTTP 429)`
- **Fix**: Retry with exponential backoff; reduce request frequency
- **Count**: 1
- **Reusable**: true

### Pattern: InternalServerError
- **Category**: runtime
- **Skill**: jdcloud-oss-ops
- **Command**: Any operation
- **Error**: `InternalError: Server error (HTTP 500)`
- **Fix**: Retry with backoff; contact support if persistent
- **Count**: 1
- **Reusable**: true

### Pattern: CredentialMisconfigured
- **Category**: runtime
- **Skill**: jdcloud-oss-ops
- **Command**: Any operation
- **Error**: `Unauthorized: Invalid credentials`
- **Fix**: Verify `~/.jdc/config` has correct access_key and secret_key
- **Count**: 1
- **Reusable**: true

## §5 Token Efficiency Warnings

### Pattern: LargeListResult
- **Category**: token_efficiency
- **Skill**: jdcloud-oss-ops
- **Command**: `client.list_objects(bucket_name='<name>', max_keys=1000)`
- **Warning**: Response too large, consumes excessive tokens
- **Fix**: Use smaller max_keys or add prefix filters to narrow results
- **Count**: 1
- **Reusable**: true

## Pattern Extraction Format

When a GCL iteration fails, extract failure pattern using this format:

```json
{
  "category": "cli_parameter|skill_generation|cross_skill|runtime|token_efficiency",
  "skill": "jdcloud-oss-ops",
  "command": "exact jdc command or SDK call",
  "error": "error message or code",
  "fix": "specific fix or remediation step",
  "count": 1,
  "reusable": true
}
```

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-06-19 | Initial failure patterns for `jdcloud-oss-ops` |
