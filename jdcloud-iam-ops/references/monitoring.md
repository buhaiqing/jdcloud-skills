# IAM Monitoring & Alerts

## Overview

IAM is a global control-plane service; its metrics focus on **access patterns**, **permission changes**, and **credential usage** rather than compute/storage metrics. Monitoring IAM helps detect unauthorized access, track permission changes, and identify credential anomalies.

## Key Monitoring Dimensions

### Access Patterns

Monitor API call patterns to detect anomalies:
- **Unusual access sources** — API calls from unexpected IP ranges
- **High-volume operations** — Spike in IAM API calls (possible automation or attack)
- **Failed authentication attempts** — Repeated InvalidAccessKey or PermissionDenied errors
- **Cross-account access** — AssumeRole frequency from external accounts

### Permission Changes

Track permission modifications for security audit:
- **Policy creation/deletion** — New policies added or removed
- **Policy attachment/detachment** — Permission changes for users/groups/roles
- **Role creation/deletion** — New roles that could enable cross-account access
- **AssumeRole policy updates** — Changes to who can assume roles

### Credential Management

Monitor AccessKey lifecycle:
- **AK/SK creation** — New credentials generated (possible account expansion or compromise)
- **AK/SK disable/enable** — Credential status changes
- **AK/SK deletion** — Credentials removed (rotation or cleanup)
- **AK/SK age** — Credentials older than recommended rotation period

## JD Cloud Monitor Integration

IAM operations can be tracked via JD Cloud Monitor (云监控) if the account has enabled IAM operation logging.

### Metric Categories

| Category | Metric | Description |
|----------|--------|-------------|
| API Call Count | `iam:ApiCallCount` | Total IAM API calls per time window |
| Failed Calls | `iam:FailedCallCount` | Failed API calls (400/403/404/5xx) |
| Permission Changes | `iam:PolicyChangeCount` | Policy create/update/delete operations |
| Credential Changes | `iam:CredentialChangeCount` | AK/SK create/disable/enable/delete operations |
| AssumeRole Count | `sts:AssumeRoleCount` | Role assumption frequency |

**Note:** Metric names may vary; consult JD Cloud Monitor documentation for official IAM namespace.

### Alert Rules

#### High Failed Call Rate

**Condition:** Failed IAM API calls > threshold in 5-minute window
**Threshold:** > 10 failed calls / 5 min (adjust based on account scale)
**Severity:** Medium-High (possible permission misconfiguration or attack)

**Alert Template:**
```yaml
metric: iam:FailedCallCount
threshold: 10
period: 300  # 5 minutes
comparison: GreaterThanThreshold
actions:
  - notify: email
    recipients: security-team@example.com
  - notify: sms
    recipients: security-oncall
```

#### Unusual Permission Change

**Condition:** Policy creation or attachment spike
**Threshold:** > 5 policy changes / hour (during non-business hours)
**Severity:** High (possible privilege escalation)

**Alert Template:**
```yaml
metric: iam:PolicyChangeCount
threshold: 5
period: 3600  # 1 hour
comparison: GreaterThanThreshold
schedule: "off-business-hours"  # 20:00-08:00
actions:
  - notify: email
    recipients: security-team@example.com
  - notify: webhook
    url: https://security.example.com/alert-handler
```

#### AK/SK Created Without Approval

**Condition:** New AccessKey created
**Threshold:** Any creation event
**Severity:** Medium (requires approval for new credentials)

**Alert Template:**
```yaml
metric: iam:CredentialChangeCount
filter: operation=create
threshold: 1
period: 60  # 1 minute
comparison: GreaterThanThreshold
actions:
  - notify: email
    recipients: security-team@example.com
    message: "New AccessKey created; verify approval status"
```

#### AssumeRole Spike

**Condition:** High AssumeRole frequency from unexpected accounts
**Threshold:** > 20 AssumeRole calls / hour from non-whitelisted accounts
**Severity:** High (possible cross-account access attempt)

**Alert Template:**
```yaml
metric: sts:AssumeRoleCount
filter: sourceAccount != whitelist
threshold: 20
period: 3600
comparison: GreaterThanThreshold
actions:
  - notify: email
    recipients: security-team@example.com
```

## Manual Monitoring Techniques

### Periodic Audit Commands

#### List All Sub-users and Permissions

```bash
# List sub-users
jdc --output json iam describe-sub-users | jq '.result.subUsers[] | {name: .subUserName, status: .status}'

# Check each sub-user's permissions
for name in $(jdc --output json iam describe-sub-users | jq -r '.result.subUsers[].subUserName'); do
  echo "Sub-user: $name"
  jdc --output json iam describe-attached-sub-user-policies --sub-user-name "$name" | jq '.result.policies[] | {name: .policyName, type: .policyType}'
done
```

#### List All Roles and Trust Policies

```bash
# List roles with assume policies
jdc --output json iam describe-roles | jq '.result.roles[] | {name: .roleName, assumePolicy: .assumeRolePolicyDocument}'
```

#### List AccessKey Age

```bash
# List AK/SK and check age
jdc --output json iam describe-user-access-keys | jq '.result.accessKeys[] | {id: .accessKeyId, createTime: .createTime, status: .status}'

# For each AK, calculate age from createTime
# Alert if age > 90 days (recommended rotation period)
```

#### Check for Orphaned Policies

```bash
# List policies without attachments
jdc --output json iam describe-policies | jq '.result.policies[] | select(.attachmentCount == 0) | {name: .policyName, id: .policyId}'
```

### Security Audit Checklist

**Monthly Audit:**
1. Review all sub-user accounts — disable unused accounts
2. Check policy attachments — remove unnecessary permissions
3. Verify role assume policies — remove outdated principals
4. Rotate AK/SK older than 90 days
5. Review MFA enablement status for admin accounts

**Quarterly Audit:**
1. Audit all custom policies — validate permissions are still needed
2. Review cross-account roles — verify external accounts are still trusted
3. Check sub-user group assignments — update group membership
4. Clean up orphaned policies and unused roles
5. Review security alert thresholds — adjust based on operational patterns

## Integration with jdcloud-cloudmonitor-ops

For comprehensive monitoring, integrate with `jdcloud-cloudmonitor-ops`:

1. **Metric Collection:** Use cloudmonitor-ops to query IAM-related metrics
2. **Alert Configuration:** Configure IAM alert rules via cloudmonitor APIs
3. **Historical Analysis:** Query historical IAM operation data for trend analysis

**Delegation Rule:** If user asks to create IAM-specific alerts or query IAM metrics, delegate metric operations to `jdcloud-cloudmonitor-ops`.

## External Monitoring Tools

IAM operations can also be monitored via:
- **JD Cloud Logs Service (日志服务)** — API call logs with request/response details
- **JD Cloud Event Service (云事件服务)** — IAM operation events for audit trails
- **Custom Scripts** — Periodic IAM state checks via CLI/SDK

## Best Practices

1. **Enable Operation Logging:** Ensure IAM API calls are logged for audit
2. **Set Up Alerts:** Configure alerts for high failed call rate and permission changes
3. **Regular Audits:** Conduct monthly/quarterly IAM security audits
4. **Credential Rotation:** Monitor AK/SK age and rotate regularly
5. **Review Alerts:** Periodically review alert thresholds and recipients
6. **Document Changes:** Track permission changes in change management system