# Failure Patterns — jdcloud-disk-ops

> Cross-session failure memory for the GCL Reflexion integration.
> This file is loaded lazily during GCL Pre-flight (step [0]) to inject
> known failure patterns as prevention hints for the Generator.

## §1 CLI Parameter Errors

### Pattern: InvalidResourceId
- **Category**: cli_parameter
- **Skill**: jdcloud-disk-ops
- **Command**: `jdc disk describe-disk --disk-id <invalid>`
- **Error**: `InvalidParameter: InvalidResourceId`
- **Fix**: Resource ID must be in valid format (disk-xxxxxxxx or vol-xxxxxxxx)
- **Count**: 1
- **Reusable**: true

### Pattern: MissingRegionId
- **Category**: cli_parameter
- **Skill**: jdcloud-disk-ops
- **Command**: `jdc disk describe-disks` (missing --region-id)
- **Error**: `MissingParameter: regionId is required`
- **Fix**: Always include --region-id in every command
- **Count**: 1
- **Reusable**: true

### Pattern: WrongOutputJsonPosition
- **Category**: cli_parameter
- **Skill**: jdcloud-disk-ops
- **Command**: `jdc disk describe-disks --output json` (wrong position)
- **Error**: `unrecognized arguments: --output json`
- **Fix**: `--output json` MUST be placed BEFORE the subcommand
- **Count**: 1
- **Reusable**: true

## §2 Skill Generation Errors

### Pattern: DeleteResourceInUse
- **Category**: skill_generation
- **Skill**: jdcloud-disk-ops
- **Command**: `jdc disk delete-disk --disk-id <id>` (when disk is attached to a VM)
- **Error**: `ResourceInUse`
- **Fix**: Stop/detach dependent resources first before deleting (detach disk from VM first)
- **Count**: 1
- **Reusable**: true

### Pattern: QuotaExceeded
- **Category**: skill_generation
- **Skill**: jdcloud-disk-ops
- **Command**: `jdc disk create-disk`
- **Error**: `QuotaExceeded: resource quota exceeded`
- **Fix**: Request quota increase or release unused resources first
- **Count**: 1
- **Reusable**: true

## §3 Cross-Skill Integration Errors

### Pattern: VPCDependenciesNotMet
- **Category**: cross_skill
- **Skill**: jdcloud-disk-ops
- **Command**: Resource creation in VPC
- **Error**: VPC not found or not ready
- **Fix**: Verify VPC exists via `jdcloud-vpc-ops` before resource creation
- **Count**: 1
- **Reusable**: true

### Pattern: IAMPermissionDenied
- **Category**: cross_skill
- **Skill**: jdcloud-disk-ops
- **Command**: Operations with insufficient IAM permissions
- **Error**: `Unauthorized: IAM permission denied`
- **Fix**: Verify IAM permissions via `jdcloud-iam-ops`
- **Count**: 1
- **Reusable**: true

## §4 Runtime Errors

### Pattern: ThrottlingRateLimit
- **Category**: runtime
- **Skill**: jdcloud-disk-ops
- **Command**: Any operation
- **Error**: `Throttling: Rate limit exceeded (HTTP 429)`
- **Fix**: Retry with exponential backoff; reduce request frequency
- **Count**: 1
- **Reusable**: true

### Pattern: InternalServerError
- **Category**: runtime
- **Skill**: jdcloud-disk-ops
- **Command**: Any operation
- **Error**: `InternalError: Server error (HTTP 500)`
- **Fix**: Retry with backoff; contact support if persistent
- **Count**: 1
- **Reusable**: true

### Pattern: CredentialMisconfigured
- **Category**: runtime
- **Skill**: jdcloud-disk-ops
- **Command**: Any operation
- **Error**: `Unauthorized: Invalid credentials`
- **Fix**: Verify `~/.jdc/config` has correct access_key and secret_key
- **Count**: 1
- **Reusable**: true

## §5 Token Efficiency Warnings

### Pattern: LargeListResult
- **Category**: token_efficiency
- **Skill**: jdcloud-disk-ops
- **Command**: `jdc disk describe-disks --page-size 100`
- **Warning**: Response too large, consumes excessive tokens
- **Fix**: Use smaller --page-size or add filters to narrow results
- **Count**: 1
- **Reusable**: true

## Pattern Extraction Format

When a GCL iteration fails, extract failure pattern using this format:

```json
{
  "category": "cli_parameter|skill_generation|cross_skill|runtime|token_efficiency",
  "skill": "jdcloud-disk-ops",
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
| 1.0.0 | 2026-06-19 | Initial failure patterns for `jdcloud-disk-ops` |
