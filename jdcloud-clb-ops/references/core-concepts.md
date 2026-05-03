# Core Concepts — JD Cloud Load Balancer

## Product Overview

JD Cloud Load Balancer distributes incoming traffic across multiple backend servers, ensuring service availability, scalability, and fault tolerance. Three types are available:

### Application Load Balancer (ALB)

- **Layer**: Layer 7 (Application Layer)
- **Protocols**: HTTP, HTTPS, TLS
- **Features**:
  - Domain-based and URL-based routing
  - SSL/TLS certificate management with SNI support
  - Request redirection (HTTP → HTTPS)
  - Session persistence via cookies
  - Custom forwarding rules (UrlMap, Rules)
- **Use Cases**: Web applications, API gateways, microservices requiring L7 routing

### Network Load Balancer (NLB)

- **Layer**: Layer 4 (Transport Layer)
- **Protocols**: TCP, UDP
- **Features**:
  - Source IP transparency (client IP preserved)
  - Session persistence based on source IP
  - High-performance connection handling
  - Support for both public and private network types
- **Use Cases**: Game servers, IoT applications, high-throughput TCP/UDP services

### Distributed Network Load Balancer (DNLB)

- **Layer**: Layer 4 (Transport Layer)
- **Protocols**: TCP, UDP
- **Features**:
  - Stateless, fully distributed architecture
  - **Free tier** (no charges for basic usage)
  - Ultra-high forwarding performance
  - No single-point-of-failure (software-defined)
- **Use Cases**: High-concurrency stateless services, microservices internal traffic

## Core Components

### Load Balancer Instance

The primary resource entity that receives traffic and distributes it to backend servers.

- **Attributes**: ID, name, VIP, EIP (if public), status, VPC binding
- **States**: `creating`, `active`, `updating`, `deleting`, `error`
- **Network Types**: 
  - Public (with EIP bound) — accessible from internet
  - Private (internal) — accessible within VPC only

### Listener (监听器)

Defines how the load balancer handles incoming traffic on specific protocol/port combinations.

- **Attributes**: ID, protocol, port, status, associated certificate (for HTTPS/TLS)
- **Protocols by Type**:
  - ALB: HTTP, HTTPS, TLS
  - NLB: TCP, UDP
  - DNLB: TCP, UDP
- **Certificate Binding**: HTTPS/TLS listeners require SSL certificates

### Backend Service (后端服务)

Defines the target group and traffic distribution policy for a listener.

- **Attributes**: ID, targetGroupId, healthCheckConfig, sessionPersistenceConfig
- **Scheduling Algorithms**: Round Robin, Weighted Round Robin, Source IP Hash
- **Health Check**: Configurable intervals, thresholds, and health criteria

### Target Group / Virtual Server Group (虚拟服务器组)

Collection of backend servers (targets) that receive distributed traffic.

- **Attributes**: ID, name, targets (list of server references)
- **Target Types**:
  - VM instances (云主机)
  - Native containers (原生容器)
  - IP addresses (直接IP)
  - High Availability Groups (高可用组)
- **Target Configuration**: Port, weight (for weighted algorithms)

### Forwarding Rules (转发规则)

ALB-specific L7 routing configuration based on domain/URL patterns.

- **UrlMap**: Top-level forwarding rule group
- **Rules**: Individual conditions and actions (e.g., host match, path match, redirect)
- **Use Case**: Route `/api/*` to one backend, `/static/*` to another

### TLS Security Policy

Controls TLS protocol versions and cipher suites for HTTPS/TLS listeners.

- **Predefined Policies**: System-provided secure configurations
- **Custom Policies**: User-defined cipher suite selections
- **Minimum TLS Version**: TLS 1.0, 1.1, 1.2, 1.3

## Regions and Availability Zones

JD Cloud Load Balancer supports multi-region deployment:

| Region | Region ID |
|--------|-----------|
| 华北-北京 | cn-north-1 |
| 华东-宿迁 | cn-east-1 |
| 华东-上海 | cn-east-2 |
| 华南-广州 | cn-south-1 |

**Multi-AZ Support**: ALB and NLB support cross-AZ deployment for high availability. Specify multiple AZs during creation.

## Limits and Quotas

| Resource | Default Limit | Adjustable |
|----------|---------------|------------|
| Load Balancers per region | 20 | Yes (quota request) |
| Listeners per LB | 50 | Yes |
| Target Groups per region | 100 | Yes |
| Targets per Target Group | 100 | Yes |
| Forwarding Rules per Listener | 100 | Yes |

**Naming Constraints**:
- Load Balancer name: 1-32 characters, alphanumeric and hyphens
- Listener name: 1-32 characters
- Target Group name: 1-32 characters

## Billing

| Product | Billing Mode | Notes |
|---------|--------------|-------|
| ALB | Postpaid by usage | Based on active connections, traffic volume |
| NLB | Postpaid by usage | Based on active connections, traffic volume |
| DNLB | Free | No charge for standard usage |

**EIP Charges**: Public load balancers require EIP binding, billed separately.

## High Availability Architecture

### Cross-AZ Deployment

- ALB/NLB can span multiple availability zones
- VIP is assigned per AZ; traffic distributed across AZs
- Backend servers can be distributed across AZs for fault isolation

### Health Check Integration

- Automatic health check for all backend servers
- Unhealthy targets are removed from traffic distribution
- Health restoration triggers automatic re-registration

### Failover Scenarios

| Failure Type | Automatic Response |
|--------------|-------------------|
| Backend server failure | Traffic redirected to healthy servers |
| AZ failure | Traffic redirected to healthy AZs |
| Listener failure | Other listeners unaffected |

## Integration with Other JD Cloud Products

| Product | Integration |
|---------|-------------|
| VPC | Load Balancer must be created within a VPC |
| Elastic IP | Required for public network access |
| VM (CVM) | Backend servers as VM instances |
| Native Container | Backend servers as containers |
| High Availability Group | Auto-scaling backend pool |
| Cloud Monitor | Metrics collection and alerting |
| SSL Certificate | HTTPS/TLS listener certificate binding |
| Log Service | Access log collection (ALB) |

## Key Terms (Glossary)

| Term | Description |
|------|-------------|
| VIP | Virtual IP address assigned to load balancer |
| EIP | Elastic Public IP bound for internet access |
| Listener | Protocol/port configuration for traffic handling |
| Target Group | Set of backend servers for traffic distribution |
| Health Check | Automatic detection of backend server status |
| Session Persistence | Keeping client requests on same backend |
| SNI | Server Name Indication for multi-certificate support |
| UrlMap | ALB forwarding rule group for domain/URL routing |