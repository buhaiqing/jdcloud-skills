# Monitoring & Alerts — JD Cloud NAT Gateway

## Key Metrics

NAT Gateway metrics are available through JD Cloud Cloud Monitor (namespace: `nat_gateway`).

| Metric | Description | Unit | Aggregation |
|--------|-------------|------|-------------|
| `natGateway.bandwidth.in` | Inbound bandwidth | bps | avg, max, min |
| `natGateway.bandwidth.out` | Outbound bandwidth | bps | avg, max, min |
| `natGateway.throughput.in` | Inbound throughput | pps | avg, max |
| `natGateway.throughput.out` | Outbound throughput | pps | avg, max |
| `natGateway.connection.count` | Active connections | count | avg, max |
| `natGateway.connection.new` | New connections per second | count/s | avg, max |
| `natGateway.packets.drop` | Dropped packets | count | sum |

## Thresholds & Recommendations

| Metric | Warning Threshold | Critical Threshold | Recommendation |
|--------|-------------------|-------------------|----------------|
| `bandwidth.out` | > 70% of NAT spec | > 90% of NAT spec | Upgrade NAT specification |
| `bandwidth.in` | > 70% of NAT spec | > 90% of NAT spec | Upgrade NAT specification |
| `packets.drop` | > 0 (sustained) | > 100/min | Check for DDoS or upgrade spec |
| `connection.count` | > 80% of max | > 95% of max | Review connection usage patterns |

> **WAF-PERF-049:** If bandwidth utilization exceeds 80% for sustained periods, recommend upgrading the NAT gateway specification.

## Alert Rules

### High Bandwidth Utilization

```json
{
  "metric": "natGateway.bandwidth.out",
  "threshold": "80% of spec limit",
  "period": 300,
  "evaluation": ">= 3 consecutive periods",
  "action": "Warn user; suggest NAT spec upgrade"
}
```

### Packet Drops Detected

```json
{
  "metric": "natGateway.packets.drop",
  "threshold": 100,
  "period": 60,
  "evaluation": ">= 1 period",
  "action": "Investigate source; check for DDoS or bandwidth exhaustion"
}
```

### Connection Spike

```json
{
  "metric": "natGateway.connection.count",
  "threshold": "2x baseline",
  "period": 300,
  "evaluation": ">= 1 period",
  "action": "Review application connection patterns; potential anomaly"
}
```

## Dashboard Recommendations

| Panel | Metrics | Purpose |
|-------|---------|---------|
| Bandwidth Overview | `bandwidth.in`, `bandwidth.out` | Real-time bandwidth usage |
| Throughput | `throughput.in`, `throughput.out` | Packet processing rate |
| Connections | `connection.count`, `connection.new` | Connection volume monitoring |
| Errors | `packets.drop` | Error/drop tracking |

## Integration with Cloud Monitor

Use `jdcloud-cloudmonitor-ops` to:
- Create alarm rules for NAT metrics
- Query historical metric data
- Set up notification contacts and groups
- Configure metric dashboards