# Monitoring JCQ

## Key Metrics

| Metric Name | Namespace | Description | Typical Alert Threshold |
|-------------|-----------|-------------|------------------------|
| MessageAccumulation | `JCQ/Topic` | Number of unconsumed messages in topic | > 10000 for 5 min |
| ConsumerLag | `JCQ/ConsumerGroup` | Difference between latest message offset and consumed offset | > 1000 for 5 min |
| SendMessageSuccessRate | `JCQ/Topic` | Ratio of successful send operations | < 99% for 5 min |
| ReceiveMessageSuccessRate | `JCQ/ConsumerGroup` | Ratio of successful receive operations | < 99% for 5 min |
| MessageDeliveryDelay | `JCQ/Topic` | Average delay between send and first delivery | > 5000 ms for 5 min |
| MessageRetryRate | `JCQ/ConsumerGroup` | Ratio of messages being redelivered | > 10% for 5 min |
| TopicMessageInRate | `JCQ/Topic` | Messages per second ingested | baseline deviation |
| TopicMessageOutRate | `JCQ/Topic` | Messages per second consumed | baseline deviation |

## Alert Example (CloudMonitor)

```json
{
  "metric": "MessageAccumulation",
  "namespace": "JCQ/Topic",
  "dimensions": {
    "topicName": "{{user.topic_name}}",
    "regionId": "{{user.region}}"
  },
  "threshold": 10000,
  "comparisonOperator": "GreaterThanThreshold",
  "evaluationPeriods": 1,
  "period": 300,
  "statistic": "Average",
  "alarmActions": [
    "{{user.notification_channel_arn}}"
  ]
}
```

## Consumer Lag Monitoring

Consumer lag is the most critical metric for JCQ health:

- **Healthy:** Lag stays low and stable.
- **Warning:** Lag grows slowly — consumer may be under-provisioned.
- **Critical:** Lag grows rapidly — consumer may be down or stalled.

### Diagnostic steps for high consumer lag:

1. Check consumer application health and logs.
2. Verify consumer group has active consumers via `describeConsumerGroups`.
3. Check for message processing exceptions causing retries.
4. Scale out consumer instances if CPU/memory bound.
5. Check for network latency between consumers and JCQ endpoint.

## Message Accumulation Monitoring

Message accumulation (topic depth) indicates producers are outpacing consumers:

- **Gradual growth:** Normal during traffic spikes; monitor recovery.
- **Sustained growth:** Consumer capacity insufficient; scale or optimize.
- **Sudden spike:** Possible consumer outage; investigate immediately.

## Retry Rate Monitoring

High retry rates indicate consumer processing failures:

- **Acceptable:** < 1% retry rate.
- **Warning:** 1-10% retry rate — investigate consumer errors.
- **Critical:** > 10% retry rate — consumer likely broken.

## Dashboard Recommendations

A JCQ monitoring dashboard should include:

1. **Topic Overview Panel**
   - Message in/out rate per topic
   - Message accumulation per topic
   - Active consumer groups per topic

2. **Consumer Group Panel**
   - Consumer lag per consumer group
   - Retry rate per consumer group
   - Active consumer count per group

3. **Message Health Panel**
   - Send success rate
   - Receive success rate
   - Average delivery delay
   - Messages with high receiveCount (potential DLQ candidates)

## Log Analysis

Key log patterns to monitor:

| Pattern | Meaning | Action |
|---------|---------|--------|
| `SendMessage success messageId=` | Normal send | None |
| `SendMessage failed MessageTooLarge` | Payload too big | Split or use OSS |
| `ReceiveMessage empty` | No messages available | Normal if topic empty |
| `ReceiveMessage exception` | Consumer error | Check consumer logs |
