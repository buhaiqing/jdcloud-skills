# Execution Flows — JD Cloud JCS for Kubernetes

Every operation: **Pre-flight → Execute (SDK/API primary) → Validate → Recover**. Do not skip phases.

**执行策略说明:** SDK/API 为主要执行路径。CLI (`jdc kubernetes`) 在当前锁定版本 (1.2.12) 中运行时崩溃，详见 [CLI Usage](cli-usage.md)。

**Snippets 模块:** 所有 K8s 操作已封装为可复用的 snippets 模块，位于 `scripts/snippets/`：
- `cluster_ops.py` — 集群 CRUD (jdcloud_sdk)
- `node_group_ops.py` — 节点组 CRUD + 扩缩容 (jdcloud_sdk)
- `credential_ops.py` — Kubeconfig 获取 (jdcloud_sdk)
- `storage_ops.py` — PV/PVC/StorageClass 管理 (kubernetes client)
- `workload_ops.py` — Pod/Service/Deployment/HPA/Ingress 操作 (kubernetes client)
- `cloudshell_ops.py` — CloudShell 远程 kubectl 执行
- `diagnostics_ops.py` — 跨资源异常聚合与性能分析
- `k8s_client.py` — 统一 K8s 客户端初始化和错误处理

## Operation: Cluster Lifecycle

**Create Cluster:**
```python
from snippets.cluster_ops import create_cluster
from snippets.wait_utils import wait_for_cluster_running

result = create_cluster(client, region_id, cluster_name, vpc_id, subnet_id, master_version, node_group_name, instance_type, node_count)
cluster_id = result["clusterId"]
wait_for_cluster_running(client, region_id, cluster_id)
```

**Delete Cluster (Safety Gate):**
```python
# Pre-flight: Check workloads
try:
    from jdcloud_aiops_cruise.kubernetes import k8s_analyzer
    workloads = k8s_analyzer.check_workloads(cluster_id)
    if workloads:
        # MUST warn user and get explicit confirmation
except ImportError:
    pass

from snippets.cluster_ops import delete_cluster
delete_cluster(client, region_id, cluster_id)
```

**Describe/List Clusters:**
```python
from snippets.cluster_ops import describe_cluster, list_clusters

cluster = describe_cluster(client, region_id, cluster_id)
clusters = list_clusters(client, region_id)
```

## Operation: Node Group Management

**Create/Scale/Delete Node Group:**
```python
from snippets.node_group_ops import create_node_group, scale_node_group, delete_node_group

# Create
ng_id = create_node_group(client, region_id, cluster_id, ng_name, instance_type, node_count, subnet_id)["nodeGroupId"]

# Scale
scale_node_group(client, region_id, cluster_id, ng_id, new_node_count)

# Delete (Safety Gate: MUST confirm with user)
delete_node_group(client, region_id, cluster_id, ng_id)
```

## Operation: Storage Management (PV/PVC/StorageClass)

**Pre-flight:** Ensure kubeconfig is available via `credential_ops.get_kubeconfig_decoded()`.

```python
from snippets.storage_ops import (
    list_storage_classes, create_pvc, list_pvcs, delete_pvc,
    list_pvs, check_pvc_health, get_storage_summary
)

# List StorageClasses
sc_result = list_storage_classes(kubeconfig_path)

# Create PVC
pvc_result = create_pvc(name, namespace, storage_class, size, access_mode, kubeconfig_path)

# Check PVC Health
health = check_pvc_health(pvc_name, namespace, kubeconfig_path)

# Delete PVC (Safety Gate: IRREVERSIBLE, MUST confirm with user)
delete_pvc(pvc_name, namespace, kubeconfig_path)
```

## Operation: Workload Management (Pod/Service/Deployment/HPA/Ingress)

**Pre-flight:** Ensure kubeconfig is available.

```python
from snippets.workload_ops import (
    list_pods, get_pod_logs, delete_pod, check_pod_health,
    list_services, check_service_health,
    list_deployments, scale_deployment, restart_deployment, check_deployment_health,
    list_hpas, check_hpa_health,
    list_ingresses, check_ingress_health,
    get_workload_summary
)

# Pod operations
pods = list_pods(namespace, label_selector="app=nginx", kubeconfig_path=kubeconfig_path)
logs = get_pod_logs(pod_name, namespace, kubeconfig_path=kubeconfig_path)
health = check_pod_health(pod_name, namespace, kubeconfig_path)

# Deployment operations
deployments = list_deployments(namespace, kubeconfig_path=kubeconfig_path)
scale_deployment(deploy_name, namespace, replicas=3, kubeconfig_path=kubeconfig_path)
health = check_deployment_health(deploy_name, namespace, kubeconfig_path)

# HPA operations
hpas = list_hpas(namespace, kubeconfig_path=kubeconfig_path)
health = check_hpa_health(hpa_name, namespace, kubeconfig_path)

# Service/Ingress operations
services = list_services(namespace, kubeconfig_path=kubeconfig_path)
ingresses = list_ingresses(namespace, kubeconfig_path=kubeconfig_path)

# Workload summary
summary = get_workload_summary(namespace, kubeconfig_path=kubeconfig_path)
```

## Operation: CloudShell Integration

**Remote kubectl execution with graceful degradation:**
```python
from snippets.cloudshell_ops import CloudShellExecutor, execute_kubectl_with_fallback

# Method 1: Direct execution
result = execute_kubectl_with_fallback(
    "get pods -n default",
    region_id="cn-north-1",
    kubeconfig_path="~/.kube/config"
)
if result["success"]:
    print(result["output"])
else:
    print(f"Error: {result['error']}")
    if result["method"] == "manual":
        # Follow manual_steps in result

# Method 2: Executor with diagnostics collection
executor = CloudShellExecutor(region_id="cn-north-1", kubeconfig_path="~/.kube/config")
diagnostics = executor.collect_diagnostics(namespace="default")
```

**Degradation Strategy:**
1. Try CloudShell API (if available)
2. Fall back to local kubectl (if kubeconfig available)
3. Return structured error with manual steps and documentation links

## Operation: Diagnostics & Performance Analysis

**Cross-resource diagnostic analysis:**
```python
from snippets.diagnostics_ops import (
    diagnose_namespace,
    analyze_performance_bottlenecks,
    correlate_events
)

# Comprehensive namespace diagnosis
report = diagnose_namespace(namespace, kubeconfig_path=kubeconfig_path)
if report["severity"] == "critical":
    print(f"Critical issues: {report['summary']['critical_issues']}")
    for rec in report["recommendations"]:
        print(f"  - {rec}")

# Performance bottleneck analysis
bottlenecks = analyze_performance_bottlenecks(namespace, kubeconfig_path)
for b in bottlenecks["bottlenecks"]:
    print(f"{b['severity']}: {b['description']}")

# Event correlation
events = correlate_events(namespace, since_minutes=60, kubeconfig_path)
for pattern in events["patterns"]:
    print(f"Pattern: {pattern['description']}")
```

**DiagnosticReport Structure:**
- `severity`: info | warning | critical
- `resources`: Health status for pods, services, deployments, HPAs, ingresses, PVCs
- `issues`: List of identified issues with severity classification
- `root_causes`: Correlated root cause patterns (e.g., Pod failures → Service endpoints missing)
- `recommendations`: Actionable remediation steps
