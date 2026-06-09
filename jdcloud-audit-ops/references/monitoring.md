# Monitoring Audit Log

## Key Metrics

While JD Cloud Audit Log itself is primarily a data source, you can monitor:

### Event Volume Metrics

| Metric | Description | Source |
|--------|-------------|--------|
| `audit.eventCount` | Total number of audit events | Cloud Monitor |
| `audit.eventRate` | Events per minute/hour | Derived from queries |
| `audit.queryLatency` | API query response time | SDK/CLI timing |

### Security Metrics

| Metric | Description | Detection Method |
|--------|-------------|------------------|
| Failed Login Attempts | Unauthorized access attempts | Query events by errorCode |
| After-Hours Activity | Operations outside business hours | Query events by eventTime |
| Unusual IP Addresses | Access from unexpected sources | Query events by sourceIpAddress |
| Privilege Escalation | IAM policy changes | Query events with eventName like '*Policy*' |

## Alert Example

### High-Value Resource Deletion Alert

```json
{
  "metric": "audit.eventCount",
  "dimensions": {
    "eventName": "DeleteInstance",
    "resourceType": "vm"
  },
  "threshold": 1,
  "period": 60,
  "comparisonOperator": "GreaterThanOrEqualToThreshold",
  "evaluationPeriods": 1,
  "alarmActions": ["notify:security-team"]
}
```

### Failed Login Alert

```json
{
  "metric": "audit.eventCount",
  "dimensions": {
    "eventName": "Login",
    "errorCode": "AuthenticationFailed"
  },
  "threshold": 5,
  "period": 300,
  "comparisonOperator": "GreaterThanOrEqualToThreshold",
  "evaluationPeriods": 1,
  "alarmActions": ["notify:security-team"]
}
```

## Monitoring Best Practices

### Regular Queries

Set up periodic queries to monitor:

1. **Daily Summary:** Total events by resource type
2. **Weekly Review:** All administrative actions (Create/Delete/Modify)
3. **Monthly Audit:** Complete event export for compliance

### Anomaly Detection

```python
def detect_anomalies(events):
    """Simple anomaly detection for audit events"""
    anomalies = []
    
    for event in events:
        # Detect after-hours activity (before 8am, after 8pm)
        event_time = parse(event['eventTime'])
        if event_time.hour < 8 or event_time.hour >= 20:
            anomalies.append({
                'type': 'after_hours',
                'event': event
            })
        
        # Detect administrative actions by non-admin users
        if event['eventName'] in ['CreateSubUser', 'DeletePolicy']:
            if event['username'] not in ADMIN_USERS:
                anomalies.append({
                    'type': 'privilege_escalation',
                    'event': event
                })
    
    return anomalies
```

### Compliance Reporting

```python
def generate_compliance_report(start_time, end_time):
    """Generate compliance report for time period"""
    events = query_all_events(start_time, end_time)
    
    report = {
        'period': {'start': start_time, 'end': end_time},
        'summary': {
            'totalEvents': len(events),
            'byResourceType': group_by(events, 'resourceType'),
            'byUsername': group_by(events, 'username'),
            'byEventName': group_by(events, 'eventName')
        },
        'administrativeActions': filter(events, is_admin_action),
        'failedOperations': filter(events, lambda e: e.get('errorCode'))
    }
    
    return report
```

## Integration with Cloud Monitor

To set up Cloud Monitor alerts based on audit events:

1. **Create Custom Metric:** Use Cloud Monitor API to publish audit event counts
2. **Set Alert Rules:** Define thresholds for suspicious patterns
3. **Configure Notifications:** Send alerts to email/SMS/webhook

Example workflow:

```bash
# 1. Query audit events
# NOTE: jdc audit 命令在当前锁定版本 (1.2.12) 中不可用，以下为期望语法示例
jdc --output json audit describe-events \
  --region-id cn-north-1 \
  --start-time "$(date -v-5M +%Y-%m-%dT%H:%M:%S+08:00)" \
  --end-time "$(date +%Y-%m-%dT%H:%M:%S+08:00)"

# 2. Analyze and publish metrics to Cloud Monitor
# (Custom script to transform and publish)

# 3. Cloud Monitor triggers alerts based on thresholds
```

> **⚠️ 脱敏提醒**：导出审计事件到 Cloud Monitor 或任何外部系统前，必须对 `requestParameters` / `responseElements` 中的敏感字段进行脱敏（password、secretKey、accessKey 等）。

## Log Retention Monitoring

Monitor your audit log retention to ensure compliance:

| Check | Frequency | Action if Failed |
|-------|-----------|------------------|
| Events within retention | Daily | Alert if gaps detected |
| Trail status | Hourly | Alert if trail inactive |
| Storage usage | Weekly | Expand if approaching limits |

## Dashboard Recommendations

Create Cloud Monitor dashboards showing:

1. **Event Volume Trends:** Line chart of events over time
2. **Top Users:** Bar chart of most active users
3. **Resource Type Distribution:** Pie chart of events by resource type
4. **Error Rate:** Percentage of failed operations
5. **Geographic Access:** Map of source IP addresses
