# Core Concepts — JD Cloud Load Balancer (CLB)

## Architecture Overview

JD Cloud Load Balancer (CLB) distributes incoming application traffic across multiple backend servers to improve application availability and scalability.

### Key Components

| Component | Description |
|-----------|-------------|
| **Load Balancer (LB)** | The entry point for traffic distribution. Provides a virtual IP (VIP) and DNS name. |
| **Listener** | Defines the protocol and port for incoming traffic. Supports TCP, UDP, HTTP, HTTPS. |
| **Target Group** | A collection of backend servers that receive traffic from the load balancer. |
| **Backend Server (Target)** | VM instances or containers that process the distributed traffic. |
| **Health Check** | Monitors the health of backend servers and removes unhealthy instances from rotation. |

## Load Balancer Types

### By Network Type

| Type | Description | Use Case |
|------|-------------|----------|
| **Internal LB** | Deployed within a VPC, only accessible from internal networks | Internal microservices, backend APIs |
| **External LB** | Exposed to the internet with public IP | Public-facing web applications |

### By Specification

| Specification | Capacity | Use Case |
|-------------|----------|----------|
| **Small** | Low throughput, suitable for dev/test | Development, testing environments |
| **Medium** | Moderate throughput | Small to medium production workloads |
| **Large** | High throughput | Large-scale production applications |

## Protocol Support

### Layer 4 (Transport Layer)

| Protocol | Description | Health Check |
|----------|-------------|--------------|
| **TCP** | Raw TCP traffic forwarding | TCP connect check |
| **UDP** | UDP packet forwarding | UDP echo check |

### Layer 7 (Application Layer)

| Protocol | Description | Features |
|----------|-------------|----------|
| **HTTP** | HTTP/1.1 traffic | URL-based routing, session persistence |
| **HTTPS** | TLS-terminated HTTP | SSL offloading, certificate management |

## Key Features

### Health Checks

- **Protocol**: TCP, HTTP, or custom protocol
- **Interval**: 5-300 seconds (default: 5s)
- **Timeout**: 2-60 seconds
- **Healthy Threshold**: 2-10 consecutive successes (default: 2)
- **Unhealthy Threshold**: 2-10 consecutive failures (default: 3)

### Session Persistence

| Type | Description |
|------|-------------|
| **Source IP** | Routes requests from same client IP to same backend |
| **Cookie** | Uses HTTP cookie for session stickiness (HTTP/HTTPS only) |

### Load Balancing Algorithms

| Algorithm | Description |
|-----------|-------------|
| **Round Robin** | Distributes traffic sequentially to each backend |
| **Least Connections** | Routes to backend with fewest active connections |
| **Source IP Hash** | Uses client IP hash for consistent routing |

## Limits and Quotas

| Resource | Default Limit | Adjustable |
|----------|---------------|------------|
| Load Balancers per Region | 10 | Yes |
| Listeners per LB | 10 | Yes |
| Backend Servers per LB | 50 | Yes |
| Target Groups per LB | 5 | Yes |

## Regions and Availability Zones

CLB is available in the following regions:

| Region ID | Region Name |
|-----------|-------------|
| cn-north-1 | 华北-北京 |
| cn-east-1 | 华东-宿迁 |
| cn-south-1 | 华南-广州 |
| cn-east-2 | 华东-上海 |

## Security Considerations

1. **Security Groups**: Control inbound/outbound traffic to the load balancer
2. **Network ACLs**: Additional layer of subnet-level security
3. **SSL/TLS**: Use HTTPS listeners with valid certificates for encrypted traffic
4. **Access Logging**: Enable access logs for audit and analysis

## Integration with Other Services

| Service | Integration |
|---------|-------------|
| **VPC** | CLB must be deployed in a VPC and subnet |
| **VM** | Backend servers are typically VM instances |
| **CloudMonitor** | Metrics and alarms for CLB performance |
| **SSL Certificate** | HTTPS listeners require SSL certificates |

## Pricing Model

CLB charges based on:
- **Instance Fee**: Hourly rate per load balancer
- **Data Processing**: Per GB of data processed
- **Bandwidth**: Peak bandwidth usage (for external LBs)

For detailed pricing, refer to JD Cloud official documentation.
