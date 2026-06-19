# Failure Patterns — jdcloud-jcq-ops

> Cross-session failure memory for the GCL Reflexion integration.
> This file is loaded lazily during GCL Pre-flight (step [0]) to inject
> known failure patterns as prevention hints for the Generator.

## §1 CLI Parameter Errors

### Pattern: InvalidQueueId
- **Category**: cli_parameter
- **Skill**: jdcloud-jcq-ops
- **Command**: `jdc jcq describe-queue --queue-id <invalid>`
- **Error**: `InvalidParameter: InvalidQueueId`
- **Fix**: Queue ID must be in valid format
- **Count**: 1
- **Reusable**: true

### Pattern: MissingRegionId
- **Category**: cli_parameter
- **Skill**: jdcloud-jcq-ops
- **Command**: `jdc jcq <command>` (missing --region-id)
- **Error**: `MissingParameter: regionId is required`
- **Fix**: Always include --region-id in every jcq command
- **Count**: 1
- **Reusable**: true

### Pattern: WrongOutputJsonPosition
- **Category**: cli_parameter
- **Skill**: jdcloud-jcq-ops
- **Command**: `jdc jcq describe-queues --output json` (wrong position)
- **Error**: `unrecognized arguments: --output json`
- **Fix**: `--output json` MUST be placed BEFORE the subcommand
- **Count**: 1
- **Reusable**: true

## §2 Skill Generation Errors

### Pattern: DeleteQueueWithMessages
- **Category**: skill_generation
- **Skill**: jdcloud-jcq-ops
- **Command**: `jdc jcq delete-queue --queue-id <id>` (when queue has messages)
- **Error**: `QueueNotEmpty`
- **Fix**: Purge messages first or confirm deletion with user
- **Count**: 1
- **Reusable**: true

### Pattern: ResetConsumerGroupOffset
- **Category**: skill_generation
- **Skill**: jdcloud-jcq-ops
- **Command**: `jdc jcq reset-consumer-group-offset` (resets to latest/earliest)
- **Error**: Message loss or reprocessing
- **Fix**: Warn user about message loss/reprocessing; confirm before proceeding
- **Count**: 1
- **Reusable**: true

### Pattern: InvalidMessageType
- **Category**: skill_generation
- **Skill**: jdcloud-jcq-ops
- **Command**: `jdc jcq create-queue --message-type <invalid>`
- **Error**: `InvalidParameter: InvalidMessageType`
- **Fix**: Use valid message types (Normal, FIFO, Delay, Transaction)
- **Count**: 1
- **Reusable**: true

## §3 Cross-Skill Integration Errors

### Pattern: VPCNotReady
- **Category**: cross_skill
- **Skill**: jdcloud-jcq-ops
- **Command**: JCQ queue creation in VPC
- **Error**: VPC not found or not ready
- **Fix**: Verify VPC exists and is ready via `jdcloud-vpc-ops`
- **Count**: 1
- **Reusable**: true

### Pattern: IAMPermissionDenied
- **Category**: cross_skill
- **Skill**: jdcloud-jcq-ops
- **Command**: JCQ operations with insufficient IAM permissions
- **Error**: `Unauthorized: IAM permission denied`
- **Fix**: Verify IAM permissions via `jdcloud-iam-ops`
- **Count**: 1
- **Reusable**: true

## §4 Runtime Errors

### Pattern: ThrottlingRateLimit
- **Category**: runtime
- **Skill**: jdcloud-jcq-ops
- **Command**: Any jcq operation
- **Error**: `Throttling: Rate limit exceeded (HTTP 429)`
- **Fix**: Retry with exponential backoff; reduce request frequency
- **Count**: 1
- **Reusable**: true

### Pattern: InternalServerError
- **Category**: runtime
- **Skill**: jdcloud-jcq-ops
- **Command**: Any jcq operation
- **Error**: `InternalError: Server error (HTTP 500)`
- **Fix**: Retry with backoff; contact support if persistent
- **Count**: 1
- **Reusable**: true

### Pattern: CredentialMisconfigured
- **Category**: runtime
- **Skill**: jdcloud-jcq-ops
- **Command**: Any jcq operation
- **Error**: `Unauthorized: Invalid credentials`
- **Fix**: Verify `~/.jdc/config` has correct access_key and secret_key
- **Count**: 1
- **Reusable**: true

## §5 Token Efficiency Warnings

### Pattern: LargeMessageListResult
- **Category**: token_efficiency
- **Skill**: jdcloud-jcq-ops
- **Command**: `jdc jcq describe-messages --queue-id <id> --page-size 100`
- **Warning**: Response too large, consumes excessive tokens
- **Fix**: Use smaller --page-size or add filters to narrow results
- **Count**: 1
- **Reusable**: true

## Pattern Extraction Format

When a GCL iteration fails, extract failure pattern using this format:

```json
{
  "category": "cli_parameter|skill_generation|cross_skill|runtime|token_efficiency",
  "skill": "jdcloud-jcq-ops",
  "command": "exact jdc command or SDK call",
  "error": "error message or code",
  "fix": "specific fix or remediation step",
  "reusable": true
}
```

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-06-19 | Initial failure patterns for `jdcloud-jcq-ops` |
