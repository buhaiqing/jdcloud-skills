# Failure Patterns — jdcloud-vpn-ops

> Cross-session failure memory for the GCL Reflexion integration.
> This file is loaded lazily during GCL Pre-flight (step [0]) to inject
> known failure patterns as prevention hints for the Generator.

## §1 CLI Parameter Errors

### Pattern: InvalidVpnId
- **Category**: cli_parameter
- **Skill**: jdcloud-vpn-ops
- **Command**: `jdc vpn describe-vpn --vpn-id <invalid>`
- **Error**: `InvalidParameter: InvalidVpnId`
- **Fix**: VPN ID must be in valid format
- **Count**: 1
- **Reusable**: true

### Pattern: MissingRegionId
- **Category**: cli_parameter
- **Skill**: jdcloud-vpn-ops
- **Command**: `jdc vpn <command>` (missing --region-id)
- **Error**: `MissingParameter: regionId is required`
- **Fix**: Always include --region-id in every vpn command
- **Count**: 1
- **Reusable**: true

### Pattern: WrongOutputJsonPosition
- **Category**: cli_parameter
- **Skill**: jdcloud-vpn-ops
- **Command**: `jdc vpn describe-vpns --output json` (wrong position)
- **Error**: `unrecognized arguments: --output json`
- **Fix**: `--output json` MUST be placed BEFORE the subcommand
- **Count**: 1
- **Reusable**: true

## §2 Skill Generation Errors

### Pattern: DeleteVPNWithActiveTunnel
- **Category**: skill_generation
- **Skill**: jdcloud-vpn-ops
- **Command**: `jdc vpn delete-vpn --vpn-id <id>` (when VPN has active tunnel)
- **Error**: `VPNHasActiveTunnel`
- **Fix**: Delete tunnel first before deleting VPN
- **Count**: 1
- **Reusable**: true

### Pattern: InvalidPeerCIDR
- **Category**: skill_generation
- **Skill**: jdcloud-vpn-ops
- **Command**: `jdc vpn create-vpn --peer-cidr <invalid>`
- **Error**: `InvalidParameter: InvalidPeerCIDR`
- **Fix**: Peer CIDR must be valid CIDR format
- **Count**: 1
- **Reusable**: true

### Pattern: InvalidLocalCIDR
- **Category**: skill_generation
- **Skill**: jdcloud-vpn-ops
- **Command**: `jdc vpn create-vpn --local-cidr <invalid>`
- **Error**: `InvalidParameter: InvalidLocalCIDR`
- **Fix**: Local CIDR must be valid CIDR format
- **Count**: 1
- **Reusable**: true

## §3 Cross-Skill Integration Errors

### Pattern: VPCNotFound
- **Category**: cross_skill
- **Skill**: jdcloud-vpn-ops
- **Command**: VPN creation in VPC
- **Error**: VPC not found
- **Fix**: Verify VPC exists via `jdcloud-vpc-ops` before VPN creation
- **Count**: 1
- **Reusable**: true

### Pattern: VPCNotReady
- **Category**: cross_skill
- **Skill**: jdcloud-vpn-ops
- **Command**: VPN creation in VPC
- **Error**: VPC not in available state
- **Fix**: Verify VPC is in available state via `jdcloud-vpc-ops`
- **Count**: 1
- **Reusable**: true

## §4 Runtime Errors

### Pattern: ThrottlingRateLimit
- **Category**: runtime
- **Skill**: jdcloud-vpn-ops
- **Command**: Any vpn operation
- **Error**: `Throttling: Rate limit exceeded (HTTP 429)`
- **Fix**: Retry with exponential backoff; reduce request frequency
- **Count**: 1
- **Reusable**: true

### Pattern: InternalServerError
- **Category**: runtime
- **Skill**: jdcloud-vpn-ops
- **Command**: Any vpn operation
- **Error**: `InternalError: Server error (HTTP 500)`
- **Fix**: Retry with backoff; contact support if persistent
- **Count**: 1
- **Reusable**: true

### Pattern: CredentialMisconfigured
- **Category**: runtime
- **Skill**: jdcloud-vpn-ops
- **Command**: Any vpn operation
- **Error**: `Unauthorized: Invalid credentials`
- **Fix**: Verify `~/.jdc/config` has correct access_key and secret_key
- **Count**: 1
- **Reusable**: true

## §5 Token Efficiency Warnings

### Pattern: LargeVPNListResult
- **Category**: token_efficiency
- **Skill**: jdcloud-vpn-ops
- **Command**: `jdc vpn describe-vpns --page-size 100`
- **Warning**: Response too large, consumes excessive tokens
- **Fix**: Use smaller --page-size or add filters to narrow results
- **Count**: 1
- **Reusable**: true

## Pattern Extraction Format

When a GCL iteration fails, extract failure pattern using this format:

```json
{
  "category": "cli_parameter|skill_generation|cross_skill|runtime|token_efficiency",
  "skill": "jdcloud-vpn-ops",
  "command": "exact jdc command or SDK call",
  "error": "error message or code",
  "fix": "specific fix or remediation step",
  "reusable": true
}
```

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-06-19 | Initial failure patterns for `jdcloud-vpn-ops` |
