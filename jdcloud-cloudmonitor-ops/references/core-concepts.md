# Cloud Monitor Core Concepts

## 1. Monitoring Service

A monitoring service refers to a JD Cloud product that can be monitored, such as Virtual Machine (VM), Relational Database Service (RDS), Load Balancer (LB), etc. Each service has a unique service code.

### Major Monitoring Services

| Service Code | Service Name | Description |
|-------------|-------------|-------------|
| vm | Virtual Machine | VM instance monitoring |
| nativecontainer | Native Container | Container instance monitoring |
| lb | Load Balancer | Classic load balancer monitoring |
| nlb | Network Load Balancer | Layer 4 load balancer monitoring |
| alb | Application Load Balancer | Layer 7 load balancer monitoring |
| eip | Elastic IP | Public IP monitoring |
| natgateway | NAT Gateway | NAT gateway monitoring |
| disk | Cloud Disk | Cloud disk monitoring |
| rds | RDS MySQL | RDS MySQL monitoring |
| mongodb | MongoDB | MongoDB monitoring |
| redis | Redis | Redis monitoring |
| memcached | Memcached | Memcached monitoring |
| jcq | JCQ | JCQ monitoring |
| kafka | Kafka | Kafka monitoring |
| elasticsearch | Elasticsearch | Elasticsearch monitoring |

## 2. Metric

A metric is an indicator that describes a specific performance or state of a cloud resource, such as CPU utilization, memory usage, disk read/write rate, etc.

### Metric Attributes

| Attribute | Description | Example |
|-----------|-------------|---------|
| metric | Metric name | vm.cpu.util |
| metricName | Metric display name | CPUUtilization |
| unit | Unit | %, Bps, bps, count |
| period | Collection interval | 60s, 300s |

### Metric Naming Convention

Metric names typically follow this format:
```
<serviceCode>.<resourceType>.<metricName>
```

For example:
- `vm.cpu.util` — VM CPU utilization
- `rds.memory.util` — RDS memory usage
- `lb.activeconnection` — LB active connection count

## 3. Metric Data

Metric data refers to the metric values collected at specific timestamps.

### Data Types

| Type | Description |
|------|-------------|
| Raw data | Raw metric values collected at a fixed interval |
| Aggregated data | Data statistically aggregated from raw data |

### Aggregation Methods

| Method | Description |
|--------|-------------|
| avg | Average |
| max | Maximum |
| min | Minimum |
| sum | Sum |
| count | Count |

## 4. Alarm

An alarm defines a notification triggered when a metric meets specific conditions.

### Alarm Rule Components

| Component | Description |
|-----------|-------------|
| Metric | The metric to monitor |
| Statistics period | The time window for data aggregation (e.g., 5 minutes) |
| Statistics method | The aggregation method within the period |
| Comparison operator | >, <, >=, <=, =, != |
| Threshold | The critical value that triggers the alarm |
| Consecutive periods | How many consecutive periods must meet the condition to trigger |
| Notification target | Contacts or contact groups to receive alarm notifications |

### Alarm States

| State | Description |
|-------|-------------|
| ALARM | Alarming — the metric has triggered the alarm condition |
| OK | Normal — the metric has not triggered the alarm condition |
| INSUFFICIENT_DATA | Insufficient data — cannot determine the state |

### Alarm Severity

| Severity | Description | Response Time |
|----------|-------------|---------------|
| critical | Critical | Respond immediately |
| warning | Warning | Respond within 30 minutes |
| notice | Notice | Respond within 2 hours |

## 5. Alarm Template

An alarm template is a predefined set of alarm rules that can be quickly applied to multiple resources.

### Template Types

| Type | Description |
|------|-------------|
| System default template | Default alarm templates provided by JD Cloud for each product |
| Custom template | Templates created by users based on business needs |

## 6. Custom Metric

Custom metric allows users to report their own business metrics to the cloud monitoring platform.

### Use Cases

- Application custom metrics (e.g., order volume, online user count)
- Business KPI monitoring
- Third-party system data integration

### Core Concepts

| Concept | Description |
|---------|-------------|
| Namespace | Namespace for isolating metrics from different businesses |
| MetricName | Metric name |
| Dimensions | Dimensions used to identify the source of the metric (e.g., instance ID) |
| Value | Metric value |
| Timestamp | Data collection timestamp |

## 7. Dashboard

A dashboard is a customizable panel for visualizing monitoring data.

### Components

| Component | Description |
|-----------|-------------|
| Panel | A dashboard contains multiple charts |
| Widget | A visualization component that displays one or more metrics |
| Template variable | Variables used to dynamically switch resources |

### Chart Types

| Type | Use Case |
|------|----------|
| Line chart | Trend display |
| Bar chart | Value comparison |
| Pie chart | Proportion display |
| Number | Latest value display |
| Table | Multi-dimensional data display |

## 8. Dimension

A dimension is an attribute used to identify the source of monitoring data, such as VM ID or disk ID.

### Common Dimensions

| Dimension | Description | Example |
|-----------|-------------|---------|
| resourceId | Resource ID | i-xxx, disk-xxx |
| instanceId | Instance ID | rds-xxx |
| clusterId | Cluster ID | k8s-xxx |
| device | Device name | vda, eth0 |

## 9. Tag

A tag is a user-defined resource identifier that can be used for batch resource selection in alarm rules.

### Tag Applications

- Mark by environment (e.g., env:prod, env:test)
- Mark by business (e.g., business:order, business:user)
- Mark by owner (e.g., owner:zhangsan)

## 10. Notification Methods

Cloud Monitor supports multiple alarm notification methods.

### Notification Types

| Type | Description |
|------|-------------|
| SMS | Send SMS to contact's phone |
| Email | Send email to contact's email address |
| Callback | Call back user's HTTP/HTTPS endpoint |
| DingTalk | Send message to DingTalk group |

### Notification Policies

| Policy | Description |
|--------|-------------|
| Notification interval | How often to repeat notification while alarm persists |
| Notification time window | Only send notifications during specified time periods |
| Notification condition | Notify only on state change or notify every time |