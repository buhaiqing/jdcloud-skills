# Failure Patterns — jdcloud-tag-audit-ops

> Cross-session failure memory for the GCL Reflexion integration.
> This file is loaded lazily during GCL Pre-flight (step [0]) to inject
> known failure patterns as prevention hints for the Generator.

## §1 CLI Parameter Errors

### Pattern: InvalidResourceId
- **Category**: cli_parameter
- **Skill**: jdcloud-tag-audit-ops
- **Command**: `jdc tag describe-resource-tags --resource-id <invalid>`
- **Error**: `InvalidParameter: InvalidResourceId`
- **Fix**: Resource ID must be in valid format
- **Count**: 1
- **Reusable**: true

### Pattern: MissingRegionId
- **Category**: cli_parameter
- **Skill**: jdcloud-tag-audit-ops
- **Command**: `jdc tag <command>` (missing --region-id)
- **Error**: `MissingParameter: regionId is required`
- **Fix**: Always include --region-id in every tag command
- **Count**: 1
- **Reusable**: true

### Pattern: WrongOutputJsonPosition
- **Category**: cli_parameter
- **Skill**: jdcloud-tag-audit-ops
- **Command**: `jdc tag describe-resource-tags --output json` (wrong position)
- **Error**: `unrecognized arguments: --output json`
- **Fix**: `--output json` MUST be placed BEFORE the subcommand
- **Count**: 1
- **Reusable**: true

## §2 Skill Generation Errors

### Pattern: AuditWithoutResourceType
- **Category**: skill_generation
- **Skill**: jdcloud-tag-audit-ops
- **Command**: `jdc tag describe-resource-tags` (missing --resource-type)
- **Error**: `MissingParameter: resource-type is required`
- **Fix**: Always specify --resource-type for tag audit
- **Count**: 1
- **Reusable**: true

### Pattern: CreateDOPSTicketWithoutConfirm
- **Category**: skill_generation
- **Skill**: jdcloud-tag-audit-ops
- **Command**: Create DOPS ticket for untagged resources (without user confirmation)
- **Error**: Safety gate violation
- **Fix**: Always obtain explicit user confirmation before creating DOPS ticket
- **Count**: 1
- **Reusable**: true

### Pattern: DuplicateTicket
- **Category**: skill_generation
- **Skill**: jdcloud-tag-audit-ops
- **Command**: Create DOPS ticket (duplicate ticket for same resource)
- **Error**: `DuplicateTicket: ticket already exists`
- **Fix**: Check for existing ticket before creating new one
- **Count**: 1
- **Reusable**: true

## §3 Cross-Skill Integration Errors

### Pattern: VMNotFound
- **Category**: cross_skill
- **Skill**: jdcloud-tag-audit-ops
- **Command**: Tag audit targeting VM
- **Error**: VM not found
- **Fix**: Verify VM exists via `jdcloud-vm-ops` before tag audit
- **Count**: 1
- **Reusable**: true

### Pattern: RedisClusterNotFound
- **Category**: cross_skill
- **Skill**: jdcloud-tag-audit-ops
- **Command**: Tag audit targeting Redis
- **Error**: Redis cluster not found
- **Fix**: Verify Redis exists via `jdcloud-redis-ops` before tag audit
- **Count**: 1
- **Reusable**: true

## §4 Runtime Errors

### Pattern: ThrottlingRateLimit
- **Category**: runtime
- **Skill**: jdcloud-tag-audit-ops
- **Command**: Any tag operation
- **Error**: `Throttling: Rate limit exceeded (HTTP 429)`
- **Fix**: Retry with exponential backoff; reduce request frequency
- **Count**: 1
- **Reusable**: true

### Pattern: InternalServerError
- **Category**: runtime
- **Skill**: jdcloud-tag-audit-ops
- **Command**: Any tag operation
- **Error**: `InternalError: Server error (HTTP 500)`
- **Fix**: Retry with backoff; contact support if persistent
- **Count**: 1
- **Reusable**: true

### Pattern: CredentialMisconfigured
- **Category**: runtime
- **Skill**: jdcloud-tag-audit-ops
- **Command**: Any tag operation
- **Error**: `Unauthorized: Invalid credentials`
- **Fix**: Verify `~/.jdc/config` has correct access_key and secret_key
- **Count**: 1
- **Reusable**: true

## §5 Token Efficiency Warnings

### Pattern: LargeTagListResult
- **Category**: token_efficiency
- **Skill**: jdcloud-tag-audit-ops
- **Command**: `jdc tag describe-resource-tags --page-size 100`
- **Warning**: Response too large, consumes excessive tokens
- **Fix**: Use smaller --page-size or add filters to narrow results
- **Count**: 1
- **Reusable**: true

## Pattern Extraction Format

When a GCL iteration fails, extract failure pattern using this format:

```json
{
  "category": "cli_parameter|skill_generation|cross_skill|runtime|token_efficiency",
  "skill": "jdcloud-tag-audit-ops",
  "command": "exact jdc command or SDK call",
  "error": "error message or code",
  "fix": "specific fix or remediation step",
  "reusable": true
}
```

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-06-19 | Initial failure patterns for `jdcloud-tag-audit-ops` |
