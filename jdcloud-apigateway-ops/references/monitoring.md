# Monitoring API Gateway

## Key Metrics

API Gateway metrics are available through JD Cloud CloudMonitor. Use `jdcloud-cloudmonitor-ops` to set up alarms.

### Invocation Metrics

| Metric Name | Namespace | Description | Unit |
|-------------|-----------|-------------|------|
| `ApiGatewayInvocationCount` | `JDC_APIGATEWAY` | Total API invocations | Count |
| `ApiGatewayInvocationErrorCount` | `JDC_APIGATEWAY` | Failed API invocations | Count |
| `ApiGatewayInvocationLatency` | `JDC_APIGATEWAY` | API response time | ms |
| `ApiGateway4xxErrorCount` | `JDC_APIGATEWAY` | 4xx client errors | Count |
| `ApiGateway5xxErrorCount` | `JDC_APIGATEWAY` | 5xx server errors | Count |

### Traffic Metrics

| Metric Name | Namespace | Description | Unit |
|-------------|-----------|-------------|------|
| `ApiGatewayInboundTraffic` | `JDC_APIGATEWAY` | Incoming traffic bytes | Bytes |
| `ApiGatewayOutboundTraffic` | `JDC_APIGATEWAY` | Outgoing traffic bytes | Bytes |

### Throttling Metrics

| Metric Name | Namespace | Description | Unit |
|-------------|-----------|-------------|------|
| `ApiGatewayThrottledCount` | `JDC_APIGATEWAY` | Requests blocked by throttling | Count |
| `ApiGatewayThrottledRate` | `JDC_APIGATEWAY` | Throttled request percentage | % |

## Metric Dimensions

When querying metrics, use these dimensions to filter:

| Dimension | Description |
|-----------|-------------|
| `apiGroupId` | API group identifier |
| `apiId` | API identifier |
| `stageName` | Deployment stage |
| `regionId` | Region identifier |

## Alert Examples

### High Error Rate
```json
{
  "metric": "ApiGatewayInvocationErrorCount",
  "namespace": "JDC_APIGATEWAY",
  "dimensions": {
    "apiGroupId": "group-xxx",
    "stageName": "prod"
  },
  "threshold": 100,
  "period": 300,
  "evaluationPeriods": 1,
  "comparisonOperator": "GreaterThanOrEqualToThreshold",
  "statistic": "Sum"
}
```

### High Latency
```json
{
  "metric": "ApiGatewayInvocationLatency",
  "namespace": "JDC_APIGATEWAY",
  "dimensions": {
    "apiGroupId": "group-xxx",
    "apiId": "api-xxx",
    "stageName": "prod"
  },
  "threshold": 5000,
  "period": 60,
  "evaluationPeriods": 3,
  "comparisonOperator": "GreaterThanThreshold",
  "statistic": "Average"
}
```

### Throttling Alert
```json
{
  "metric": "ApiGatewayThrottledCount",
  "namespace": "JDC_APIGATEWAY",
  "dimensions": {
    "apiGroupId": "group-xxx",
    "stageName": "prod"
  },
  "threshold": 50,
  "period": 300,
  "evaluationPeriods": 1,
  "comparisonOperator": "GreaterThanOrEqualToThreshold",
  "statistic": "Sum"
}
```

## Access Logs

API Gateway access logs contain detailed information about each API call:
- Request ID
- Timestamp
- Client IP
- Request path and method
- Response status code
- Response time
- Backend response time
- Error details (if any)

Access logs can be shipped to Log Service or OSS for long-term storage and analysis.

## Recommended Dashboard Panels

1. **Traffic Overview**: Invocation count by API group (line chart)
2. **Error Analysis**: 4xx vs 5xx errors by API (stacked bar chart)
3. **Latency Percentiles**: p50, p95, p99 latency (line chart)
4. **Throttling Overview**: Throttled requests by policy (bar chart)
5. **Top APIs**: Most called APIs (table)
