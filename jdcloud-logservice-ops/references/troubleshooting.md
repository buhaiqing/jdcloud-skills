# Troubleshooting LogService

## Common SDK Error Codes

| Code | HTTP | Meaning | Agent Action |
|------|------|---------|--------------|
| `InvalidParameter` | 400 | Request validation failed | Check required fields, name length, retention range |
| `LogSetNotFound` | 404 | LogSet UID does not exist | Verify UID; list LogSets to find correct one |
| `LogTopicNotFound` | 404 | LogTopic UID does not exist | Verify UID; list LogTopics to find correct one |
| `LogSetAlreadyExists` | 409 | LogSet name already in use | Use different name or describe existing |
| `LogTopicAlreadyExists` | 409 | LogTopic name already in LogSet | Use different name |
| `LogSetNotEmpty` | 409 | Cannot delete LogSet with LogTopics | Delete all LogTopics first, or confirm cascade |
| `InvalidQuery` | 400 | Search query syntax error | Fix Lucene syntax; check field names |
| `TimeRangeExceeded` | 400 | Search time range outside retention | Shrink range to within retention window |
| `IndexNotConfigured` | 400 | Search on field without index | Configure index for the field first |
| `QuotaExceeded` | 429 | Resource limit reached | Request quota increase or clean up resources |
| `Throttling` | 429 | API rate limit exceeded | Back off exponentially; reduce query frequency |
| `InternalError` | 500 | Server-side error | Retry with backoff; include `requestId` in support ticket |
| `ServiceUnavailable` | 503 | LogService temporarily unavailable | Retry after 10s; escalate if persistent |

## Diagnostic Order

1. **Verify resource existence**
   - Call `DescribeLogSets` to confirm LogSet UID
   - Call `DescribeLogTopics` with `logsetUID` to confirm LogTopic UID

2. **Verify retention**
   - Call `DescribeLogSet` to check `retention`
   - Ensure search `startTime` is within `createTime + retention`

3. **Verify index configuration**
   - Call `DescribeIndex` with LogTopic UID
   - Confirm queried fields are indexed

4. **Verify collection agent**
   - For `cloud_vm` type: check agent is installed and running on VM
   - For `container` type: verify DaemonSet / sidecar is deployed
   - Check `collectionInfo.paths` match actual log file locations

5. **Simplify query**
   - Start with `*` (match all) to verify data exists
   - Gradually add filters to isolate problematic syntax

## Common Issues

### No logs appearing in LogTopic

- **Symptom**: Search returns zero results
- **Causes**:
  1. Collection agent not installed or not running
  2. Log file path mismatch (`collectionInfo.paths` ≠ actual path)
  3. LogTopic created but no data source configured
  4. Logs are outside retention window
- **Mitigation**:
  1. Verify agent status on source VM/container
  2. Check `DescribeLogTopic` for `collectionInfo`
  3. Perform `*` search over last 1 hour
  4. Verify LogSet retention ≥ time since creation

### Slow search performance

- **Symptom**: Search queries take > 10 seconds
- **Causes**:
  1. Large time range without narrow filters
  2. Searching non-indexed fields
  3. Very high log volume
- **Mitigation**:
  1. Reduce time range to smallest useful window
  2. Add indexed field filters first (`level:ERROR`)
  3. Configure index on frequently queried fields
  4. Use pagination; do not fetch all results at once

### Search query syntax errors

- **Symptom**: `InvalidQuery` error
- **Common mistakes**:
  - Using `=` instead of `:` for field match (`level=ERROR` → `level:ERROR`)
  - Unclosed quotes in phrase search
  - Using unsupported operators (`~`, `^`)
- **Fix**: Validate against Lucene query syntax; test with simplest query first

### Deletion failures

- **Symptom**: `LogSetNotEmpty` when deleting LogSet
- **Fix**: Either delete all LogTopics first, or confirm user wants cascade deletion
- **Symptom**: `LogTopicNotFound` when deleting LogTopic
- **Fix**: Already deleted; report success to user

## Support Escalation

When opening a JD Cloud support ticket, always include:
1. `requestId` from the failing API call
2. Exact SDK request parameters (mask credentials)
3. Timestamp of the failure
4. Expected vs actual behavior
