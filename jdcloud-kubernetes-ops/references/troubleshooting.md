# Troubleshooting — JD Cloud JCS for Kubernetes

## Common API Error Codes

| Code / HTTP | Meaning | Agent Action |
|-------------|---------|--------------|
| InvalidParameter / 400 | Request failed validation | Align body with OpenAPI; check required fields |
| ResourceNotFound / 404 | Resource does not exist | Verify resource ID; check region |
| ResourceAlreadyExists / 409 | Cluster name already in use | Use different name or reuse existing cluster |
| QuotaExceeded / 400 | Cluster or node quota limit reached | HALT; user requests quota increase |
| InsufficientBalance / 400 | Account balance insufficient | HALT; user tops up account |
| InvalidVersion / 400 | Unsupported Kubernetes version | List available versions; suggest valid one |
| InvalidResourceStatus / 400 | Resource in wrong state for operation | Wait for resource to reach appropriate state |
| SubnetIpInsufficient / 400 | Subnet has no available IPs | HALT; user expands subnet or chooses different subnet |
| InternalError / 500 | Internal server error | Retry with backoff; HALT if persists |
| ServiceUnavailable / 503 | Service temporarily unavailable | Retry with exponential backoff |
| Throttling / 429 | Rate limit exceeded | Back off; respect Retry-After header |

## Diagnostic Order

### 1. Cluster Issues

**Cluster Creation Fails**
```
1. Check VPC and subnet exist: jdcloud-vpc-ops describe-vpc/subnet
2. Verify subnet has available IPs
3. Check quota: describeClusters count vs limit
4. Verify Kubernetes version is supported
5. Verify instance type is available in the AZ
```

**Cluster Stuck in Creating**
```
1. Poll describeCluster for 10 minutes (poll interval: 30s)
2. Check VPC/subnet/security group configuration
3. Contact JD Cloud support if stuck > 15 minutes
```

**Cluster Unreachable**
```
1. Check cluster state is "running"
2. Verify kubeconfig credentials are valid
3. Check network connectivity to API server endpoint
4. Verify security group allows port 6443 traffic
```

**Cluster Upgrade Fails**
```
1. Validate target version is within one minor version
2. Check all node groups are in "running" state
3. Verify no workloads are stuck (PENDING/CRASHLOOPBACKOFF)
4. Check etcd cluster health
```

### 2. Node Group Issues

**Node Group Creation Fails**
```
1. Verify cluster exists and is "running"
2. Check subnet has available IP addresses
3. Verify instance type is available in the AZ
4. Check node group count limits
```

**Node Scaling Fails**
```
1. Check target count is within min/max range
2. Verify subnet has sufficient IP addresses
3. Check account balance is sufficient for additional nodes
4. Verify instance type quota is not exceeded
```

**Nodes Not Ready**
```
1. Check VM instance is running: jdcloud-vm-ops describe-instance
2. Verify VM security group allows necessary traffic
3. Check container runtime (Docker/containerd) is running on node
4. Check kubelet service is running and registered
5. Review node system logs
```

### 3. Credential Issues

**Kubeconfig Not Working**
```
1. Verify cluster is "running"
2. Re-fetch credentials via describeClusterCredential
3. Ensure you're using kubectl version within ±1 minor version of cluster
4. Check certificate expiry date
```

**Credential Retrieval Fails**
```
1. Check cluster exists and user has permission
2. Verify region is correct
3. Ensure cluster was not deleted or in "deleting" state
```

### 4. Workload Issues

**Pods Pending**
```
1. Check node resources (CPU/Memory) are available
2. Verify PVC exists and is bound
3. Check node selector/node affinity constraints
4. Review taints and tolerations
```

**Pods CrashLoopBackOff**
```
1. Check container logs via kubectl logs
2. Verify environment variables and configmaps
3. Check resource limits are sufficient
4. Verify image exists and is accessible
```

## CLI-Specific Issues

### Invalid Credentials
**Symptom:** `Please use 'jdc configure add' command to add cli configure first.`

**Solution:** Ensure `~/.jdc/config` and `~/.jdc/current` exist and are properly formatted.

### Unrecognized nc Subcommand
**Symptom:** `Error: No such command 'nc'.`

**Solution:** Verify CLI version is 1.2.12+. The `nc` product was added in CLI v1.2.0.

## Pre-Delete Workload Analysis

Before deleting a cluster, use `k8s_analyzer.py` from `jdcloud-aiops-cruise`:

```python
try:
    from jdcloud_aiops_cruise.kubernetes import k8s_analyzer
    workloads = k8s_analyzer.check_workloads("c-xxx")
    if workloads.get("deployments", 0) > 0:
        print(f"WARNING: {workloads['deployments']} deployments running")
        print(f"Cluster has {workloads['pods']} pods and {workloads['services']} services")
except ImportError:
    print("k8s_analyzer not available. Fallback to describeCluster check.")
```

## Getting Help

If issues persist after following this guide:
1. Collect request ID from API response
2. Gather cluster ID, node group IDs
3. Note timestamp of issue occurrence
4. Contact JD Cloud support with above information