# Failure Patterns — jdcloud-logservice-ops

> Cross-session failure memory for the GCL Reflexion integration.
> This file is loaded lazily during GCL Pre-flight (step [0]) to inject
> known failure patterns as prevention hints for the Generator.

## §1 CLI Parameter Errors

### Pattern: InvalidLogstoreId
- **Category**: cli_parameter
- **Skill**: jdcloud-logservice-ops
- **Command**: `jdc logservice describe-logstore --logstore-id <invalid>`
- **Error**: `InvalidParameter: InvalidLogstoreId`
- **Fix**: Logstore ID must be in valid format
- **Count**: 1
- **Reusable**: true

### Pattern: MissingRegionId
- **Category**: cli_parameter
- **Skill**: jdcloud-logservice-ops
- **Command**: `jdc logservice <command>` (missing --region-id)
- **Error**: `MissingParameter: regionId is required`
- **Fix**: Always include --region-id in every logservice command
- **Count**: 1
- **Reusable**: true

### Pattern: WrongOutputJsonPosition
- **Category**: cli_parameter
- **Skill**: jdcloud-logservice-ops
- **Command**: `jdc logservice describe-logstores --output json` (wrong position)
- **Error**: `unrecognized arguments: --output json`
- **Fix**: `--output json` MUST be placed BEFORE the subcommand
- **Count**: 1
- **Reusable**: true

## §2 Skill Generation Errors

### Pattern: DeleteLogstoreWithIndex
- **Category**: skill_generation
- **Skill**: jdcloud-logservice-ops
- **Command**: `jdc logservice delete-logstore --logstore-id <id>` (when logstore has index)
- **Error**: `LogstoreHasIndex`
- **Fix**: Delete index first before deleting logstore
- **Count**: 1
- **Reusable**: true

### Pattern: InvalidIndexConfig
- **Category**: skill_generation
- **Skill**: jdcloud-logservice-ops
- **Command**: `jdc logservice create-index --index-config <invalid>`
- **Error**: `InvalidParameter: InvalidIndexConfig`
- **Fix**: Index config must be valid JSON with required fields
- **Count**: 1
- **Reusable**: true

### Pattern: InvalidLogQuery
- **Category**: skill_generation
- **Skill**: jdcloud-logservice-ops
- **Command**: `jdc logservice get-logs --query <invalid>`
- **Error**: `InvalidParameter: InvalidLogQuery`
- **Fix**: Query must be valid LogQL syntax
- **Count**: 1
- **Reusable**: true

## §3 Cross-Skill Integration Errors

### Pattern: VPCNotReady
- **Category**: cross_skill
- **Skill**: jdcloud-logservice-ops
- **Command**: LogService creation in VPC
- **Error**: VPC not found or not ready
- **Fix**: Verify VPC exists and is ready via `jdcloud-vpc-ops`
- **Count**: 1
- **Reusable**: true

### Pattern: IAMPermissionDenied
- **Category**: cross_skill
- **Skill**: jdcloud-logservice-ops
- **Command**: LogService operations with insufficient IAM permissions
- **Error**: `Unauthorized: IAM permission denied`
- **Fix**: Verify IAM permissions via `jdcloud-iam-ops`
- **Count**: 1
- **Reusable**: true

## §4 Runtime Errors

### Pattern: ThrottlingRateLimit
- **Category**: runtime
- **Skill**: jdcloud-logservice-ops
- **Command**: Any logservice operation
- **Error**: `Throttling: Rate limit exceeded (HTTP 429)`
- **Fix**: Retry with exponential backoff; reduce request frequency
- **Count**: 1
- **Reusable**: true

### Pattern: InternalServerError
- **Category**: runtime
- **Skill**: jdcloud-logservice-ops
- **Command**: Any logservice operation
- **Error**: `InternalError: Server error (HTTP 500)`
- **Fix**: Retry with backoff; contact support if persistent
- **Count**: 1
- **Reusable**: true

### Pattern: CredentialMisconfigured
- **Category**: runtime
- **Skill**: jdcloud-logservice-ops
- **Command**: Any logservice operation
- **Error**: `Unauthorized: Invalid credentials`
- **Fix**: Verify `~/.jdc/config` has correct access_key and secret_key
- **Count**: 1
- **Reusable**: true

## §5 Token Efficiency Warnings

### Pattern: LargeLogQueryResult
- **Category**: token_efficiency
- **Skill**: jdcloud-logservice-ops
- **Command**: `jdc logservice get-logs --query <query> --line 1000`
- **Warning**: Response too large, consumes excessive tokens
- **Fix**: Use smaller --line or add filters to narrow results
- **Count**: 1
- **Reusable**: true

## Pattern Extraction Format

When a GCL iteration fails, extract failure pattern using this format:

```json
{
  "category": "cli_parameter|skill_generation|cross_skill|runtime|token_efficiency",
  "skill": "jdcloud-logservice-ops",
  "command": "exact jdc command or SDK call",
  "error": "error message or code",
  "fix": "specific fix or remediation step",
  "reusable": true
}
```

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-06-19 | Initial failure patterns for `jdcloud-logservice-ops` |
