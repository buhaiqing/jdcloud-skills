# JD Cloud VPC Monitoring Guide

## Idempotency Monitoring

### Why Monitor Idempotency?
Idempotent operations ensure that:
- **Create operations** don't create duplicate resources
- **Delete operations** don't fail on non-existent resources
- **Retry operations** produce consistent results
- **Automation scripts** are safe to re-run

### Idempotency Metrics to Monitor

#### Resource Duplication Rate
- **Metric**: Number of resources with same name/identifier
- **Expected**: 0 (no duplicates)
- **Alert**: If duplicates detected

#### Operation Success Rate
- **Metric**: Percentage of operations that succeed on first try
- **Expected**: >99%
- **Alert**: If success rate drops below threshold

#### Retry Operation Count
- **Metric**: Number of operations that required retries
- **Expected**: Low (ideally 0)
- **Alert**: If retry count increases significantly

### Idempotency Verification Script
```bash
#!/bin/bash
# idempotency-check.sh
# Verify VPC operations are idempotent

REGION="cn-north-1"
VPC_NAME="test-vpc"
CIDR_BLOCK="10.0.0.0/16"

echo "=== Idempotency Verification ==="

# Test 1: Create operation idempotency
echo "Test 1: Creating VPC..."
EXISTING=$(jdc vpc describe-vpcs --region $REGION --output json | \
  jq -r ".data[] | select(.vpcName == \"$VPC_NAME\") | .vpcId" | head -n 1)

if [ -n "$EXISTING" ]; then
  echo "✓ VPC already exists: $EXISTING"
  echo "✓ Create operation is idempotent"
else
  jdc vpc create-vpc --region $REGION --vpc-name $VPC_NAME --cidr-block $CIDR_BLOCK --output json
  echo "✓ VPC created successfully"
fi

# Test 2: Delete operation idempotency
echo "Test 2: Testing delete idempotency..."
VPC_EXISTS=$(jdc vpc describe-vpc --vpc-id $EXISTING --region $REGION --output json 2>&1)
if echo "$VPC_EXISTS" | jq -e '.error' > /dev/null 2>&1; then
  echo "✓ VPC already deleted"
  echo "✓ Delete operation is idempotent"
else
  jdc vpc delete-vpc --vpc-id $EXISTING --region $REGION --output json
  echo "✓ VPC deleted successfully"
fi

echo "=== Idempotency Tests Complete ==="
```

## Key Metrics

### VPC Metrics
- **VPC Count**: Total number of VPCs in the account
- **VPC Status**: Health status of VPC resources
- **CIDR Utilization**: IP address usage within VPC CIDR blocks
- **Idempotency Success Rate**: Percentage of idempotent operations that succeed

### Subnet Metrics
- **Subnet Count**: Number of subnets per VPC
- **Subnet Status**: Health status of subnet resources
- **IP Address Utilization**: Used vs available IP addresses in subnets
- **Duplicate Subnet Count**: Number of subnets with same name (should be 0)

### Network Traffic Metrics
- **Inbound Traffic**: Data received by VPC resources
- **Outbound Traffic**: Data sent from VPC resources
- **Network Packets**: Number of packets transmitted/received
- **Network Errors**: Packet errors and drops

### Security Metrics
- **Security Group Rules**: Number and configuration of security group rules
- **Network ACL Rules**: Number and configuration of network ACL rules
- **Blocked Connections**: Connections blocked by security rules

### Gateway Metrics
- **NAT Gateway Connections**: Active connections through NAT gateways
- **Internet Gateway Traffic**: Traffic through internet gateways
- **VPN Connection Status**: Status of VPN connections

### Idempotency Metrics
- **Resource Duplication Rate**: Rate of duplicate resource creation
- **Operation Retry Rate**: Rate at which operations need to be retried
- **Consistency Score**: How consistently operations produce expected results

## Monitoring Configuration

### CloudMonitor Integration
JD Cloud VPC metrics are integrated with JD Cloud Monitor for comprehensive monitoring.

#### Metric Namespaces
- `jdcloud/vpc`: VPC-specific metrics
- `jdcloud/subnet`: Subnet-specific metrics
- `jdcloud/natgateway`: NAT Gateway metrics
- `jdcloud/vpngateway`: VPN Gateway metrics

### Alert Configuration Example

#### VPC Resource Alert
```json
{
  "metricName": "vpc_count",
  "namespace": "jdcloud/vpc",
  "threshold": 10,
  "comparisonOperator": ">",
  "period": 300,
  "evaluationCount": 3,
  "alertName": "High VPC Count",
  "alertPolicy": {
    "notificationType": "email",
    "recipients": ["admin@example.com"]
  }
}
```

#### Subnet IP Utilization Alert
```json
{
  "metricName": "subnet_ip_utilization",
  "namespace": "jdcloud/subnet",
  "threshold": 80,
  "comparisonOperator": ">",
  "period": 300,
  "evaluationCount": 2,
  "alertName": "High Subnet IP Utilization",
  "alertPolicy": {
    "notificationType": "email,sms",
    "recipients": ["network-team@example.com"]
  }
}
```

#### NAT Gateway Connection Alert
```json
{
  "metricName": "nat_gateway_connections",
  "namespace": "jdcloud/natgateway",
  "threshold": 10000,
  "comparisonOperator": ">",
  "period": 300,
  "evaluationCount": 3,
  "alertName": "High NAT Gateway Connections",
  "alertPolicy": {
    "notificationType": "email",
    "recipients": ["ops-team@example.com"]
  }
}
```

## Monitoring Tools

### JD Cloud Console
- **VPC Dashboard**: Overview of all VPC resources
- **Network Topology**: Visual representation of network architecture
- **Traffic Analysis**: Real-time and historical traffic analysis
- **Security Analysis**: Security group and network ACL analysis

### CLI Monitoring Commands
```bash
# Get VPC metrics
jdc monitor get-metric-statistics \
  --namespace jdcloud/vpc \
  --metric-name vpc_count \
  --period 300 \
  --output json

# Get subnet metrics
jdc monitor get-metric-statistics \
  --namespace jdcloud/subnet \
  --metric-name subnet_ip_utilization \
  --period 300 \
  --output json
```

### API Monitoring
```bash
# Get VPC monitoring data via API
curl -X GET "https://monitor.api.jdcloud.com/api/v1/metrics/jdcloud/vpc/vpc_count" \
  -H "Authorization: Bearer $JDC_ACCESS_KEY" \
  -H "Content-Type: application/json"
```

## Performance Monitoring

### Network Performance Metrics
- **Bandwidth Utilization**: Percentage of available bandwidth being used
- **Latency**: Network delay between endpoints
- **Throughput**: Amount of data successfully transferred
- **Packet Loss Rate**: Percentage of packets lost

### Resource Utilization
- **CPU Utilization**: For instances within VPC
- **Memory Utilization**: For instances within VPC
- **Disk I/O**: Disk read/write operations

## Log Monitoring

### Flow Logs
VPC Flow Logs capture information about IP traffic going to and from network interfaces:
```bash
# Create flow log
jdc vpc create-flow-log \
  --region cn-north-1 \
  --resource-type vpc \
  --resource-id vpc-abc123def \
  --log-group-name vpc-flow-logs \
  --output json
```

### Security Logs
- **Security Group Logs**: Track security group rule matches
- **Network ACL Logs**: Track network ACL rule matches
- **Connection Logs**: Track network connections

## Dashboard Configuration

### Custom Dashboard Example
```json
{
  "dashboardName": "VPC Monitoring Dashboard",
  "widgets": [
    {
      "title": "VPC Count Over Time",
      "metric": "jdcloud/vpc/vpc_count",
      "period": 300,
      "statistic": "Average"
    },
    {
      "title": "Subnet IP Utilization",
      "metric": "jdcloud/subnet/subnet_ip_utilization",
      "period": 300,
      "statistic": "Maximum"
    },
    {
      "title": "Network Traffic",
      "metric": "jdcloud/vpc/network_traffic",
      "period": 300,
      "statistic": "Sum"
    }
  ]
}
```

## Best Practices

### Monitoring Setup
1. **Define Baselines**: Establish normal operating parameters
2. **Set Appropriate Thresholds**: Configure alerts based on business impact
3. **Monitor Critical Resources**: Focus on production and critical VPCs
4. **Regular Reviews**: Periodically review monitoring configurations

### Alert Management
1. **Tiered Alerts**: Configure different alert levels (warning, critical)
2. **Notification Channels**: Use appropriate notification methods
3. **Alert Suppression**: Avoid alert fatigue with proper suppression rules
4. **Response Procedures**: Document response procedures for each alert type

### Performance Optimization
1. **Resource Sizing**: Ensure proper resource allocation
2. **Traffic Patterns**: Analyze and optimize traffic flows
3. **Bottleneck Identification**: Identify and resolve performance bottlenecks
4. **Capacity Planning**: Plan for future growth based on trends

### Idempotency Monitoring Best Practices
1. **Continuous Verification**: Regularly verify operations are idempotent
2. **Duplicate Detection**: Monitor for duplicate resource creation
3. **State Consistency**: Ensure resource state matches expected state
4. **Audit Logging**: Log all operations for idempotency verification
5. **Automated Testing**: Implement automated idempotency tests
6. **Metrics Collection**: Collect and analyze idempotency metrics
7. **Alert on Anomalies**: Alert when idempotency patterns are violated

## Integration with Third-Party Tools

### Prometheus Integration
```yaml
# prometheus.yml configuration
scrape_configs:
  - job_name: 'jdcloud-vpc'
    static_configs:
      - targets: ['monitor.api.jdcloud.com']
    metrics_path: '/api/v1/metrics'
    bearer_token: '${JDC_ACCESS_KEY}'
```

### Grafana Dashboard
- Import JD Cloud VPC monitoring dashboards
- Configure data sources for JD Cloud metrics
- Set up custom panels for VPC-specific metrics

## Automated Monitoring

### Cloud Functions Integration
```python
# Example cloud function for automated monitoring
import json
import requests

def monitor_vpc_resources(event, context):
    # Check VPC health
    # Send alerts if issues detected
    # Log monitoring results
    pass
```

### Scheduled Reports
- Daily VPC health reports
- Weekly network performance summaries
- Monthly capacity planning reports