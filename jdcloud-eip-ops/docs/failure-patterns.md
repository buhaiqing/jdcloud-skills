# Failure Patterns — `jdcloud-eip-ops`

> Cross-session failure memory for the GCL Reflexion integration.
> This file is loaded lazily during GCL Pre-flight (step [0]) to inject
> known failure patterns as prevention hints for the Generator.

## §1 CLI Parameter Errors

### Pattern: InvalidAddressId
- **Category**: cli_parameter
- **Skill**: jdcloud-eip-ops
- **Command**: `jdc eip describe-address --address-id <id>`
- **Error**: `InvalidParameter: InvalidAddressId`
- **Fix**: EIP ID must be in valid format (e.g., `eip-xxxxxxxx`)
- **Count**: 1
- **Reusable**: true

### Pattern: MissingRegionId
- **Category**: cli_parameter
- **Skill**: jdcloud-eip-ops
- **Command**: `jdc eip <command>` (missing `--region-id`)
- **Error**: `MissingParameter: regionId is required`
- **Fix**: Always include `--region-id` in every eip command
- **Count**: 1
- **Reusable**: true

### Pattern: WrongOutputJsonPosition
- **Category**: cli_parameter
- **Skill**: jdcloud-eip-ops
- **Command**: `jdc eip describe-address --output json` (wrong position)
- **Error**: `unrecognized arguments: --output json`
- **Fix**: `--output json` MUST be placed BEFORE the subcommand
- **Count**: 1
- **Reusable**: true

## §2 Skill Generation Errors

### Pattern: EIPAlreadyInUse
- **Category**: skill_generation
- **Skill**: jdcloud-eip-ops
- **Command**: `jdc eip associate-address --address-id <id>` (when EIP is in-use)
- **Error**: `AddressAlreadyAssociated`
- **Fix**: Check EIP status before associating; dissociate first if needed
- **Count**: 1
- **Reusable**: true

### Pattern: CannotReleaseInUseEIP
- **Category**: skill_generation
- **Skill**: jdcloud-eip-ops
- **Command**: `jdc eip release-address --address-id <id>` (when EIP is in-use)
- **Error**: `AddressInUse` or similar
- **Fix**: EIP must be in `available` state before release; dissociate first
- **Count**: 1
- **Reusable**: true

### Pattern: InstanceNotRunning
- **Category**: skill_generation
- **Skill**: jdcloud-eip-ops
- **Command**: `jdc eip associate-address --instance-id <id>` (when instance is stopped)
- **Error**: `InvalidInstanceState` or similar
- **Fix**: Target instance must be in `running` state; start instance first
- **Count**: 1
- **Reusable**: true

### Pattern: QuotaExceeded
- **Category**: skill_generation
- **Skill**: jdcloud-eip-ops
- **Command**: `jdc eip allocate-address`
- **Error**: `QuotaExceeded: EIP quota exceeded`
- **Fix**: Request quota increase or release unused EIPs first
- **Count**: 1
- **Reusable**: true

## §3 Cross-Skill Integration Errors

### Pattern: VMDependenciesNotMet
- **Category**: cross_skill
- **Skill**: jdcloud-eip-ops
- **Command**: EIP operations targeting VM
- **Error**: VM not found or not in running state
- **Fix**: Verify VM exists and is running via `jdcloud-vm-ops` before EIP operations
- **Count**: 1
- **Reusable**: true

### Pattern: CLBDependenciesNotMet
- **Category**: cross_skill
- **Skill**: jdcloud-eip-ops
- **Command**: EIP operations targeting CLB
- **Error**: CLB not found or not active
- **Fix**: Verify CLB exists and is active via `jdcloud-clb-ops` before EIP operations
- **Count**: 1
- **Reusable**: true

## §4 Runtime Errors

### Pattern: ThrottlingRateLimit
- **Category**: runtime
- **Skill**: jdcloud-eip-ops
- **Command**: Any eip operation
- **Error**: `Throttling: Rate limit exceeded (HTTP 429)`
- **Fix**: Retry with exponential backoff; reduce request frequency
- **Count**: 1
- **Reusable**: true

### Pattern: InternalServerError
- **Category**: runtime
- **Skill**: jdcloud-eip-ops
- **Command**: Any eip operation
- **Error**: `InternalError: Server error (HTTP 500)`
- **Fix**: Retry with backoff; contact support if persistent
- **Count**: 1
- **Reusable**: true

### Pattern: CredentialMisconfigured
- **Category**: runtime
- **Skill**: jdcloud-eip-ops
- **Command**: Any eip operation
- **Error**: `Unauthorized: Invalid credentials`
- **Fix**: Verify `~/.jdc/config` has correct access_key and secret_key
- **Count**: 1
- **Reusable**: true

## §5 Token Efficiency Warnings

### Pattern: LargeListResult
- **Category**: token_efficiency
- **Skill**: jdcloud-eip-ops
- **Command**: `jdc eip describe-addresses --page-size 100`
- **Warning**: Response too large, consumes excessive tokens
- **Fix**: Use smaller `--page-size` or add filters to narrow results
- **Count**: 1
- **Reusable**: true

## Pattern Extraction Format

When a GCL iteration fails, extract failure pattern using this format:

```json
{
  "category": "cli_parameter|skill_generation|cross_skill|runtime|token_efficiency",
  "skill": "jdcloud-eip-ops",
  "command": "exact jdc command or SDK call",
  "error": "error message or code",
  "fix": "specific fix or remediation step",
  "reusable": true
}
```

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-06-04 | Initial failure patterns for `jdcloud-eip-ops` |
