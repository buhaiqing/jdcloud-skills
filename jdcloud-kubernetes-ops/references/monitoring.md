# Monitoring — JD Cloud JCS for Kubernetes

## Key Metrics

Kubernetes cluster metrics are available through JD Cloud Monitor service. Use `jdcloud-cloudmonitor-ops` for metric queries.

### Cluster-Level Metrics

| Metric Name | Namespace | Unit | Description |
|-------------|-----------|------|-------------|
| k8s_cluster_cpu_util | jcs.kubernetes | % | Cluster CPU utilization |
| k8s_cluster_mem_util | jcs.kubernetes | % | Cluster memory utilization |
| k8s_cluster_pod_count | jcs.kubernetes | Count | Number of running pods |
| k8s_cluster_deployment_count | jcs.kubernetes | Count | Number of deployments |
| k8s_cluster_service_count | jcs.kubernetes | Count | Number of services |
| k8s_cluster_node_count | jcs.kubernetes | Count | Number of worker nodes |

### Node-Level Metrics

| Metric Name | Namespace | Unit | Description |
|-------------|-----------|------|-------------|
| k8s_node_cpu_util | jcs.kubernetes | % | Node CPU utilization |
| k8s_node_mem_util | jcs.kubernetes | % | Node memory utilization |
| k8s_node_disk_util | jcs.kubernetes | % | Node disk utilization |
| k8s_node_network_in | jcs.kubernetes | Bytes | Node incoming network traffic |
| k8s_node_network_out | jcs.kubernetes | Bytes | Node outgoing network traffic |
| k8s_node_pod_count | jcs.kubernetes | Count | Number of pods on node |
| k8s_node_condition_ready | jcs.kubernetes | 0/1 | Node ready status |

### Component Status Metrics

| Metric Name | Namespace | Unit | Description |
|-------------|-----------|------|-------------|
| k8s_apiserver_up | jcs.kubernetes | 0/1 | API server health |
| k8s_scheduler_up | jcs.kubernetes | 0/1 | Scheduler health |
| k8s_controller_manager_up | jcs.kubernetes | 0/1 | Controller manager health |
| k8s_etcd_up | jcs.kubernetes | 0/1 | etcd health |

## Metric Dimensions

| Dimension | Description | Example |
|-----------|-------------|---------|
| clusterId | Cluster ID | c-xxx |
| nodeGroupId | Node group ID | ng-xxx |
| nodeId | Worker node ID | i-xxx |

## Alert Rules (Recommended)

### Critical Alerts

```json
{
  "alertName": "K8s-Cluster-Down",
  "metric": "k8s_apiserver_up",
  "threshold": 1,
  "comparison": "<",
  "period": 60,
  "evaluationPeriods": 2,
  "alarmActions": ["notify-oncall"]
}
```

```json
{
  "alertName": "K8s-Node-Not-Ready",
  "metric": "k8s_node_condition_ready",
  "threshold": 1,
  "comparison": "<",
  "period": 300,
  "evaluationPeriods": 1,
  "alarmActions": ["notify-oncall"]
}
```

### Warning Alerts

```json
{
  "alertName": "K8s-High-CPU",
  "metric": "k8s_cluster_cpu_util",
  "threshold": 80,
  "comparison": ">=",
  "period": 300,
  "evaluationPeriods": 3,
  "alarmActions": ["notify-team"]
}
```

```json
{
  "alertName": "K8s-High-Memory",
  "metric": "k8s_cluster_mem_util",
  "threshold": 85,
  "comparison": ">=",
  "period": 300,
  "evaluationPeriods": 3,
  "alarmActions": ["notify-team"]
}
```

## Dashboard Recommendations

### Cluster Overview Dashboard

- Cluster state and health
- Node count and status distribution
- Pod count and capacity utilization
- API server request rate and latency

### Node-Level Dashboard

- Per-node CPU/Memory/Disk utilization
- Pod density per node
- Network I/O per node
- Node conditions (Ready, DiskPressure, MemoryPressure)

### Workload Dashboard

- Deployment replica counts
- Service endpoints
- Pod restart counts
- Resource quota usage

## Integration with CloudMonitor

For detailed metric queries and alarm configuration, see `jdcloud-cloudmonitor-ops` skill.

### Example: Query Kubernetes Metrics

```python
from jdcloud_sdk.services.monitor.client.MonitorClient import MonitorClient
from jdcloud_sdk.services.monitor.apis.DescribeMetricDataRequest import DescribeMetricDataRequest, DescribeMetricDataParameters

params = DescribeMetricDataParameters(
    regionId="cn-north-1",
    metric="k8s_cluster_cpu_util",
    serviceCode="jcs.kubernetes",
    resourceId="c-xxx",
    startTime="2026-06-08T00:00:00Z",
    endTime="2026-06-08T23:59:59Z"
)
req = DescribeMetricDataRequest(parameters=params)
resp = client.send(req)
```