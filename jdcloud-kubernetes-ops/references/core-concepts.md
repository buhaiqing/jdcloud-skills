# Core Concepts — JD Cloud JCS for Kubernetes

## Architecture Overview

JD Cloud JCS for Kubernetes (容器服务) provides a fully managed Kubernetes control plane with customizable worker node groups. It automates cluster provisioning, upgrades, scaling, and security patching.

### Key Components

| Component | Description |
|-----------|-------------|
| **Cluster** | A fully managed Kubernetes control plane (API server, etcd, scheduler, controller manager) |
| **Node Group** | A set of worker nodes (VM instances) with identical configuration (instance type, image, storage) |
| **Worker Node** | A VM instance running kubelet, container runtime, and kube-proxy |
| **Control Plane** | Managed by JD Cloud — includes API Server, etcd, Scheduler, Controller Manager |
| **Kubeconfig** | Credentials file for kubectl access to the cluster |

## Cluster Architecture

### Control Plane

| Component | Managed By | Description |
|-----------|------------|-------------|
| API Server | JD Cloud | Exposes Kubernetes API, handles authentication and authorization |
| etcd | JD Cloud | Distributed key-value store for cluster state |
| Scheduler | JD Cloud | Assigns pods to worker nodes |
| Controller Manager | JD Cloud | Manages controllers (deployments, replica sets, etc.) |

### Worker Node Components

| Component | Description |
|-----------|-------------|
| **kubelet** | Agent that manages pods on the node |
| **Container Runtime** | Docker or containerd for running containers |
| **kube-proxy** | Network proxy for service load balancing |
| **Node Exporter** | Exposes node-level metrics |

## Instance Types

| Instance Type Family | Use Case |
|----------------------|----------|
| **General Purpose (g.n2/g.s2)** | Web servers, microservices, development |
| **Compute Optimized (c.n2/c.s2)** | Batch processing, CI/CD, compute-intensive workloads |
| **Memory Optimized (m.n2/m.s2)** | In-memory databases, caching, analytics |
| **GPU (p.n1)** | Machine learning, AI inference, rendering |

## Supported Kubernetes Versions

JD Cloud JCS for Kubernetes typically supports:

- **Latest two minor versions** (e.g., v1.26.x, v1.27.x, v1.28.x)
- **Patch updates** (security and bug fixes) are applied automatically to managed control plane
- **Node group version** can lag behind control plane by up to one minor version

## Network Architecture

### VPC Integration

- Each cluster is deployed within a **VPC** and uses the VPC network for pod and service networking
- **Subnet** — Node groups are deployed in specified subnets
- **CLB Integration** — Services of type LoadBalancer automatically provision CLB instances

### Network Modes

| Mode | Description |
|------|-------------|
| **VPC-CNI** | Pods get VPC network IP addresses (higher performance) |
| **Flannel/Overlay** | Pods get overlay network IP addresses (wider compatibility) |

## Storage Integration

| Storage Type | Description |
|-------------|-------------|
| **Cloud Disk Service** | Persistent volumes backed by JD Cloud Block Storage |
| **Object Storage (OSS)** | For backup, logs, and static assets via CSI driver |
| **Local Storage** | Ephemeral storage on worker nodes |

## Regions and Availability Zones

| Region ID | Region Name |
|-----------|-------------|
| cn-north-1 | 华北-北京 |
| cn-east-1 | 华东-宿迁 |
| cn-south-1 | 华南-广州 |
| cn-east-2 | 华东-上海 |

## Limits and Quotas

| Resource | Default Limit | Adjustable |
|----------|---------------|------------|
| Clusters per Region | 5 | Yes |
| Node Groups per Cluster | 10 | Yes |
| Nodes per Node Group | 50 | Yes |
| Nodes per Cluster | 100 | Yes |
| Pods per Node | 110 (default) | Yes (via kubelet config) |

## Security Considerations

1. **IAM Policies** — Control who can create/delete clusters and manage node groups via `jdcloud-iam-ops`
2. **Kubeconfig Management** — Cluster credentials grant admin access; store and transmit securely
3. **Network Security** — Use security groups to control traffic to worker nodes
4. **Container Security** — Use private container registry (JD Cloud Container Registry) for production
5. **Audit Logging** — Enable Kubernetes audit logs for security monitoring

## Integration with Other Services

| Service | Integration |
|---------|-------------|
| **VPC** | Cluster networking and subnet selection |
| **CLB** | Services of type LoadBalancer |
| **CloudMonitor** | Cluster and node metrics |
| **IAM** | Cluster RBAC and user permissions |
| **OSS** | Backup, logs, and CSI storage driver |
| **Container Registry** | Private image registry for deployments |

## Pricing

JCS for Kubernetes charges based on:
- **Control Plane Fee** — Per cluster per hour (free for one cluster per account)
- **Worker Node Fee** — Pay-as-you-go or monthly subscription for VM instances
- **Cloud Disk Fee** — Persistent volumes used by pods
- **CLB Fee** — Load balancers created for services of type LoadBalancer

For detailed pricing, refer to JD Cloud official documentation.

## Operational Best Practices

- **Least privilege:** IAM policies scoped to required APIs only (cluster CRUD, node group operations, credential retrieval).
- **Availability:** Deploy multi-AZ clusters with node groups in at least two availability zones.
- **Cost:** Right-size node instance types; use auto-scaling for node groups to optimize spend.
- **Backup:** Regularly backup etcd and persistent volumes (PV). Cluster deletion is irreversible.
- **Security:** Rotate cluster credentials regularly. Store kubeconfig securely. Use IAM roles for cross-account access.
- **Upgrades:** Always upgrade one minor version at a time. Test workload compatibility in a staging cluster first.