# Failure Patterns — jdcloud-cert-ops

> Cross-session failure memory for the GCL Reflexion integration.
> This file is loaded lazily during GCL Pre-flight (step [0]) to inject
> known failure patterns as prevention hints for the Generator.

## §1 CLI Parameter Errors

### Pattern: InvalidCertId
- **Category**: cli_parameter
- **Skill**: jdcloud-cert-ops
- **Command**: `jdc cert describe-certificate --certificate-id <invalid>`
- **Error**: `InvalidParameter: InvalidCertificateId`
- **Fix**: Certificate ID must be in valid format
- **Count**: 1
- **Reusable**: true

### Pattern: MissingRegionId
- **Category**: cli_parameter
- **Skill**: jdcloud-cert-ops
- **Command**: `jdc cert <command>` (missing --region-id)
- **Error**: `MissingParameter: regionId is required`
- **Fix**: Always include --region-id in every cert command
- **Count**: 1
- **Reusable**: true

### Pattern: WrongOutputJsonPosition
- **Category**: cli_parameter
- **Skill**: jdcloud-cert-ops
- **Command**: `jdc cert describe-certificates --output json` (wrong position)
- **Error**: `unrecognized arguments: --output json`
- **Fix**: `--output json` MUST be placed BEFORE the subcommand
- **Count**: 1
- **Reusable**: true

## §2 Skill Generation Errors

### Pattern: DeleteCertInUse
- **Category**: skill_generation
- **Skill**: jdcloud-cert-ops
- **Command**: `jdc cert delete-certificate --certificate-id <id>` (when cert is bound to CLB/CDN)
- **Error**: `CertificateInUse`
- **Fix**: Unbind certificate from CLB/CDN first before deleting
- **Count**: 1
- **Reusable**: true

### Pattern: UploadInvalidCert
- **Category**: skill_generation
- **Skill**: jdcloud-cert-ops
- **Command**: `jdc cert upload-certificate` (with invalid certificate content)
- **Error**: `InvalidCertificate: certificate content is invalid`
- **Fix**: Verify certificate and private key are valid PEM format
- **Count**: 1
- **Reusable**: true

### Pattern: CertDomainMismatch
- **Category**: skill_generation
- **Skill**: jdcloud-cert-ops
- **Command**: `jdc cert upload-certificate` (certificate domain doesn't match)
- **Error**: `CertificateDomainMismatch`
- **Fix**: Ensure certificate CN/SAN matches the domain
- **Count**: 1
- **Reusable**: true

## §3 Cross-Skill Integration Errors

### Pattern: CLBNotFound
- **Category**: cross_skill
- **Skill**: jdcloud-cert-ops
- **Command**: Certificate operations targeting CLB
- **Error**: CLB not found
- **Fix**: Verify CLB exists via `jdcloud-clb-ops` before certificate operations
- **Count**: 1
- **Reusable**: true

### Pattern: CDNDomainNotFound
- **Category**: cross_skill
- **Skill**: jdcloud-cert-ops
- **Command**: Certificate operations targeting CDN domain
- **Error**: CDN domain not found
- **Fix**: Verify CDN domain exists before certificate operations
- **Count**: 1
- **Reusable**: true

## §4 Runtime Errors

### Pattern: ThrottlingRateLimit
- **Category**: runtime
- **Skill**: jdcloud-cert-ops
- **Command**: Any cert operation
- **Error**: `Throttling: Rate limit exceeded (HTTP 429)`
- **Fix**: Retry with exponential backoff; reduce request frequency
- **Count**: 1
- **Reusable**: true

### Pattern: InternalServerError
- **Category**: runtime
- **Skill**: jdcloud-cert-ops
- **Command**: Any cert operation
- **Error**: `InternalError: Server error (HTTP 500)`
- **Fix**: Retry with backoff; contact support if persistent
- **Count**: 1
- **Reusable**: true

### Pattern: CredentialMisconfigured
- **Category**: runtime
- **Skill**: jdcloud-cert-ops
- **Command**: Any cert operation
- **Error**: `Unauthorized: Invalid credentials`
- **Fix**: Verify `~/.jdc/config` has correct access_key and secret_key
- **Count**: 1
- **Reusable**: true

## §5 Token Efficiency Warnings

### Pattern: LargeCertificateListResult
- **Category**: token_efficiency
- **Skill**: jdcloud-cert-ops
- **Command**: `jdc cert describe-certificates --page-size 100`
- **Warning**: Response too large, consumes excessive tokens
- **Fix**: Use smaller --page-size or add filters to narrow results
- **Count**: 1
- **Reusable**: true

## Pattern Extraction Format

When a GCL iteration fails, extract failure pattern using this format:

```json
{
  "category": "cli_parameter|skill_generation|cross_skill|runtime|token_efficiency",
  "skill": "jdcloud-cert-ops",
  "command": "exact jdc command or SDK call",
  "error": "error message or code",
  "fix": "specific fix or remediation step",
  "reusable": true
}
```

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-06-19 | Initial failure patterns for `jdcloud-cert-ops` |
