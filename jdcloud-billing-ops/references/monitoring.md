# Monitoring — JD Cloud Billing

## Key Billing Metrics

| Metric | Description | Use Case |
|--------|-------------|----------|
| Account Balance | Current account balance | Low balance alerts |
| Daily Consumption | Daily spending amount | Budget tracking |
| Voucher Expiry | Days until voucher expires | Optimize voucher usage |
| Resource Cost Trend | Cost changes over time | Anomaly detection |

## Billing Alerts (via Cloud Monitor)

While `jdcloud-billing-ops` is read-only, billing alerts should be configured in `jdcloud-cloudmonitor-ops`:

### Recommended Alert Rules

| Alert Name | Condition | Action |
|------------|-----------|--------|
| Low Balance | Balance < ¥1000 | Notify admin |
| Daily Budget Exceeded | Daily cost > ¥500 | Notify admin |
| Voucher Expiring | Expires in 7 days | Notify to use |
| Cost Spike | Daily cost > 150% of avg | Investigate |

### Integration Flow

```
jdcloud-billing-ops (query)
    ↓
Analyze cost patterns
    ↓
Configure alerts in jdcloud-cloudmonitor-ops
    ↓
Trigger notifications when thresholds breached
```

## Cost Analysis Patterns

### Monthly Cost Breakdown

```python
from jdcloud_sdk.services.billing.apis.QueryBillSummaryRequest import (
    QueryBillSummaryRequest,
    QueryBillSummaryParameters,
)

params = QueryBillSummaryParameters(
    regionId="cn-north-1",
    startTime="2026-05-01 00:00:00",
    endTime="2026-05-31 23:59:59",
)
params.setPageIndex(1)
params.setPageSize(1000)

req = QueryBillSummaryRequest(parameters=params)
resp = billing_client.send(req)
```

### Regional Cost Distribution

```python
# Analyze cost by region — query each region separately
regions = ["cn-north-1", "cn-south-1", "cn-east-2", "cn-east-1"]
for region in regions:
    params = QueryBillSummaryParameters(
        regionId=region,
        startTime="2026-05-01 00:00:00",
        endTime="2026-05-31 23:59:59",
    )
    params.setPageIndex(1)
    params.setPageSize(1000)
    req = QueryBillSummaryRequest(parameters=params)
    resp = billing_client.send(req)
    # Aggregate results
```

## Budget Management

| Budget Type | Tracking Method | Alert Threshold |
|-------------|-----------------|-----------------|
| Monthly Budget | Sum of daily consumption | 80%, 100% |
| Project Budget | Tag-based aggregation | 75%, 90%, 100% |
| Resource Type Budget | Product-based aggregation | 85%, 100% |
