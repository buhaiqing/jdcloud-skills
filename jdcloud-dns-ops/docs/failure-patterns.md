# Failure Patterns — jdcloud-dns-ops

> Cross-session failure memory for the GCL Reflexion integration.
> This file is loaded lazily during GCL Pre-flight (step [0]) to inject
> known failure patterns as prevention hints for the Generator.

## §1 CLI Parameter Errors

### Pattern: InvalidDomainId
- **Category**: cli_parameter
- **Skill**: jdcloud-dns-ops
- **Command**: `jdc dns describe-domain --domain-id <invalid>`
- **Error**: `InvalidParameter: InvalidDomainId`
- **Fix**: Domain ID must be in valid format
- **Count**: 1
- **Reusable**: true

### Pattern: MissingRegionId
- **Category**: cli_parameter
- **Skill**: jdcloud-dns-ops
- **Command**: `jdc dns <command>` (missing --region-id)
- **Error**: `MissingParameter: regionId is required`
- **Fix**: Always include --region-id in every dns command
- **Count**: 1
- **Reusable**: true

### Pattern: WrongOutputJsonPosition
- **Category**: cli_parameter
- **Skill**: jdcloud-dns-ops
- **Command**: `jdc dns describe-domains --output json` (wrong position)
- **Error**: `unrecognized arguments: --output json`
- **Fix**: `--output json` MUST be placed BEFORE the subcommand
- **Count**: 1
- **Reusable**: true

## §2 Skill Generation Errors

### Pattern: DeleteDomainWithRecords
- **Category**: skill_generation
- **Skill**: jdcloud-dns-ops
- **Command**: `jdc dns delete-domain --domain-id <id>` (when domain has records)
- **Error**: `DomainHasRecords`
- **Fix**: Delete all records first before deleting domain
- **Count**: 1
- **Reusable**: true

### Pattern: InvalidRecordType
- **Category**: skill_generation
- **Skill**: jdcloud-dns-ops
- **Command**: `jdc dns add-record --type <invalid>`
- **Error**: `InvalidParameter: InvalidRecordType`
- **Fix**: Use valid record types (A, AAAA, CNAME, MX, TXT, etc.)
- **Count**: 1
- **Reusable**: true

### Pattern: BatchSetOverwrite
- **Category**: skill_generation
- **Skill**: jdcloud-dns-ops
- **Command**: `jdc dns batch-set-records` (overwrites all existing records)
- **Error**: Unexpected record deletion
- **Fix**: Warn user that batch-set overwrites all records; confirm before proceeding
- **Count**: 1
- **Reusable**: true

## §3 Cross-Skill Integration Errors

### Pattern: DomainNotRegistered
- **Category**: cross_skill
- **Skill**: jdcloud-dns-ops
- **Command**: DNS operations on unregistered domain
- **Error**: Domain not found in JD Cloud DNS
- **Fix**: Verify domain is registered and managed in JD Cloud DNS
- **Count**: 1
- **Reusable**: true

### Pattern: CLBNotFound
- **Category**: cross_skill
- **Skill**: jdcloud-dns-ops
- **Command**: DNS record pointing to CLB
- **Error**: CLB not found
- **Fix**: Verify CLB exists via `jdcloud-clb-ops` before creating DNS record
- **Count**: 1
- **Reusable**: true

## §4 Runtime Errors

### Pattern: ThrottlingRateLimit
- **Category**: runtime
- **Skill**: jdcloud-dns-ops
- **Command**: Any dns operation
- **Error**: `Throttling: Rate limit exceeded (HTTP 429)`
- **Fix**: Retry with exponential backoff; reduce request frequency
- **Count**: 1
- **Reusable**: true

### Pattern: InternalServerError
- **Category**: runtime
- **Skill**: jdcloud-dns-ops
- **Command**: Any dns operation
- **Error**: `InternalError: Server error (HTTP 500)`
- **Fix**: Retry with backoff; contact support if persistent
- **Count**: 1
- **Reusable**: true

### Pattern: CredentialMisconfigured
- **Category**: runtime
- **Skill**: jdcloud-dns-ops
- **Command**: Any dns operation
- **Error**: `Unauthorized: Invalid credentials`
- **Fix**: Verify `~/.jdc/config` has correct access_key and secret_key
- **Count**: 1
- **Reusable**: true

## §5 Token Efficiency Warnings

### Pattern: LargeRecordListResult
- **Category**: token_efficiency
- **Skill**: jdcloud-dns-ops
- **Command**: `jdc dns describe-records --domain-id <id> --page-size 100`
- **Warning**: Response too large, consumes excessive tokens
- **Fix**: Use smaller --page-size or add filters to narrow results
- **Count**: 1
- **Reusable**: true

## Pattern Extraction Format

When a GCL iteration fails, extract failure pattern using this format:

```json
{
  "category": "cli_parameter|skill_generation|cross_skill|runtime|token_efficiency",
  "skill": "jdcloud-dns-ops",
  "command": "exact jdc command or SDK call",
  "error": "error message or code",
  "fix": "specific fix or remediation step",
  "reusable": true
}
```

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-06-19 | Initial failure patterns for `jdcloud-dns-ops` |
