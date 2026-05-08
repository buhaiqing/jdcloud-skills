# Monitoring & Alerts — JD Cloud KMS

## Key Metrics Overview

JD Cloud KMS operations can be monitored through JD Cloud Monitor (云监控). Key metrics help track usage patterns, detect anomalies, and ensure compliance.

### Available Metrics (via JD Cloud Monitor)

| Metric Name | Namespace | Description | Usage |
|-------------|-----------|-------------|-------|
| **API Call Count** | `kms` | Number of API calls per operation type (encrypt, decrypt, createKey, etc.) | Track usage volume, detect abnormal spikes |
| **API Error Count** | `kms` | Number of failed API calls (4xx, 5xx errors) | Monitor service health, detect permission issues |
| **API Latency** | `kms` | Average latency per API call (encrypt, decrypt, describe) | Performance monitoring |
| **Key Count** | `kms` | Total number of keys per region/account | Capacity planning |
| **Key Rotation Events** | `kms` | Number of key rotation operations | Security compliance |

> **Note**: Exact metric names and namespaces depend on JD Cloud Monitor implementation. Check JD Cloud Monitor documentation for current KMS metrics: https://docs.jdcloud.com/cn/cloudmonitor/introduction

## Key Monitoring Dimensions

Metrics can be filtered by dimensions:

- **Region ID**: cn-north-1, cn-east-2, cn-south-1
- **Key ID**: Individual key monitoring
- **API Operation**: encrypt, decrypt, createKey, describeKey, etc.
- **Error Type**: InvalidParameter, KeyNotFound, AccessDenied, etc.

## Recommended Monitoring Setup

### 1. Key Usage Monitoring

**Goal:** Track key operations per day/week to detect anomalies.

**Metrics to monitor:**
- `encrypt` call count
- `decrypt` call count
- `generateDataKey` call count

**Dashboard:**
```yaml
Dashboard: "KMS Key Usage"
Panels:
  - Panel: Encrypt Operations
    Metric: kms.encrypt.callCount
    Dimensions: regionId=cn-north-1, keyId=*
    Aggregation: Sum (per day)
    
  - Panel: Decrypt Operations
    Metric: kms.decrypt.callCount
    Dimensions: regionId=cn-north-1, keyId=*
    Aggregation: Sum (per day)
```

### 2. Error Rate Monitoring

**Goal:** Detect permission issues, quota limits, or service errors.

**Metrics to monitor:**
- API error count (total)
- Error count by type (AccessDenied, KeyNotFound, RateLimitExceeded)

**Alert rule:**
```yaml
Alert: "KMS High Error Rate"
Condition:
  Metric: kms.error.count
  Aggregation: Sum (per 5 minutes)
  Threshold: > 10 errors
Actions:
  - Send notification to admin
  - Log incident in audit system
```

### 3. Key Creation/Deletion Monitoring

**Goal:** Track key lifecycle changes for compliance.

**Metrics to monitor:**
- `createKey` call count
- `scheduleKeyDeletion` call count
- Key count (total)

**Alert rule:**
```yaml
Alert: "KMS Key Deletion Scheduled"
Condition:
  Metric: kms.scheduleKeyDeletion.callCount
  Aggregation: Sum (per day)
  Threshold: > 0 (any deletion)
Actions:
  - Send notification to security team
  - Require approval for deletion
```

### 4. Performance Monitoring

**Goal:** Ensure API latency meets performance requirements.

**Metrics to monitor:**
- Encrypt latency (average)
- Decrypt latency (average)
- Describe key latency

**Alert rule:**
```yaml
Alert: "KMS High Latency"
Condition:
  Metric: kms.encrypt.latency
  Aggregation: Average (per 5 minutes)
  Threshold: > 200ms
Actions:
  - Send notification to operations team
  - Investigate network or service issues
```

### 5. Key Rotation Compliance

**Goal:** Ensure automatic key rotation is functioning.

**Metrics to monitor:**
- Key rotation events count
- Key age (days since creation or last rotation)

**Compliance check:**
```yaml
Alert: "KMS Key Rotation Reminder"
Condition:
  Metric: kms.key.age
  Aggregation: Max
  Threshold: > 90 days (no rotation)
Actions:
  - Send reminder to rotate key
  - Check if automatic rotation is enabled
```

## Audit Logging

JD Cloud KMS provides audit logs for all key operations (check JD Cloud Audit/ActionTrail documentation):

**Logged Operations:**
- createKey
- enableKey / disableKey
- encrypt / decrypt
- scheduleKeyDeletion / cancelKeyDeletion
- keyRotation
- createSecret / deleteSecret

**Log Fields:**
- Timestamp
- User identity (Access Key)
- Operation type
- Key ID
- Source IP
- Request parameters
- Response status (success/failure)

**Audit Analysis:**
```bash
# Example: Query audit logs for key deletions (via JD Cloud Audit API)
# Search for events: operation = "scheduleKeyDeletion"
# Filter: last 7 days, status = "success"
```

## Alert Configuration Best Practices

### Alert Severity Levels

| Severity | Metric Condition | Example |
|----------|------------------|---------|
| **Critical** | Service unavailable or security breach | API error rate > 50%, unauthorized key deletion |
| **High** | Significant performance degradation | Encrypt latency > 500ms, rate limit exceeded |
| **Medium** | Compliance policy violation | Key not rotated in 90 days, key count > quota |
| **Low** | Normal operational events | Daily key creation, routine encrypt operations |

### Notification Channels

- **Email**: For medium/high severity alerts
- **SMS**: For critical alerts (immediate response)
- **Webhook**: For integration with incident management systems (PagerDuty, Slack)
- **JD Cloud Event Service**: For automated workflows

## Monitoring Dashboard Example

**KMS Operations Dashboard:**

```yaml
Panels:
  1. Key Count by Region:
     Metric: kms.key.count
     Dimensions: regionId
     Visualization: Pie chart
     
  2. Encrypt/Decrypt Operations (24h):
     Metric: kms.encrypt.callCount, kms.decrypt.callCount
     Dimensions: keyId
     Visualization: Line chart
     
  3. API Error Rate (5m):
     Metric: kms.error.count
     Dimensions: operation
     Visualization: Bar chart
     
  4. Key Creation Events (7d):
     Metric: kms.createKey.callCount
     Dimensions: regionId
     Visualization: Counter
     
  5. Top 5 Keys by Usage:
     Metric: kms.encrypt.callCount
     Dimensions: keyId
     Aggregation: Top 5
     Visualization: Table
```

## Compliance Monitoring

### Security Compliance Checks

**1. Key Age Compliance:**
- Alert if key age > policy threshold (e.g., 365 days)
- Track key rotation frequency

**2. Key Usage Compliance:**
- Monitor keys with zero usage (orphaned keys)
- Alert if unused keys exist for > 30 days

**3. Access Control Compliance:**
- Monitor access denied errors
- Track unauthorized key operation attempts

**4. Encryption Compliance:**
- Monitor encrypt/decrypt ratio (unusual patterns may indicate security issue)
- Track secrets management usage

### Compliance Reports

Generate periodic reports:
- Key inventory (all keys per region, status, age)
- Key rotation history (last 90 days)
- API call statistics (encrypt/decrypt volume)
- Error summary (permission issues, quota limits)

## Integration with JD Cloud Monitor

**Setup Steps:**

1. Enable JD Cloud Monitor for KMS (if not enabled by default)
2. Create custom monitoring dashboard
3. Configure alert rules for key metrics
4. Set up notification channels (email, SMS, webhook)
5. Periodically review metrics and adjust thresholds

**Monitor Service:**
- Official Documentation: https://docs.jdcloud.com/cn/cloudmonitor/introduction
- API Reference: https://docs.jdcloud.com/cn/cloudmonitor/api/overview

## Cost Monitoring

**KMS Billing Metrics:**
- Key count (monthly fee per key)
- API call count (per-operation fee)
- Secrets count (monthly fee per secret)

**Cost Optimization:**
- Delete unused keys to reduce key management fees
- Use envelope encryption to reduce encrypt/decrypt API calls
- Monitor secret count to optimize secrets management fees

## Monitoring via CLI (Optional)

If JD Cloud Monitor API is available via `jdc`:

```bash
# Example: Query KMS metrics (if supported)
jdc --output json monitor describe-metric-data \
  --namespace kms \
  --metric-name encrypt.callCount \
  --dimensions '{"regionId":"cn-north-1"}'
```

## References

- JD Cloud Monitor Documentation: https://docs.jdcloud.com/cn/cloudmonitor/introduction
- JD Cloud Audit Documentation: https://docs.jdcloud.com/cn/audit/introduction
- JD Cloud Event Service: https://docs.jdcloud.com/cn/event-service/introduction
- KMS Monitoring Best Practices: https://docs.jdcloud.com/cn/key-management-service/best-practices