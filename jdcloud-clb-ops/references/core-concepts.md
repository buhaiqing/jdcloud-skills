# Core Concepts — JD Cloud Load Balancer (CLB)

> **ponytail: trimmed to essentials. Full details in SKILL.md execution flows.**

## Key Components

| Component | Description |
|-----------|-------------|
| **Load Balancer (LB)** | Entry point providing VIP and DNS name |
| **Listener** | Defines protocol (TCP/UDP/HTTP/HTTPS) and port |
| **Target Group** | Collection of backend servers receiving traffic |
| **Backend Server** | VM instances processing traffic |
| **Health Check** | Monitors backend health, removes unhealthy instances |

## Types

| Type | Description |
|------|-------------|
| Internal LB | VPC-internal only |
| External LB | Public-facing with internet IP |
| Specs | Small / Medium / Large (throughput tiers) |

## Protocol Support

| Layer | Protocols | Features |
|-------|-----------|----------|
| L4 | TCP, UDP | Raw forwarding, simple health checks |
| L7 | HTTP, HTTPS | URL routing, session persistence, SSL offload |

## Key Features

- **Health Checks**: Interval 5-300s, timeout 2-60s, configurable thresholds
- **Session Persistence**: Source IP or Cookie (HTTP/HTTPS)
- **Algorithms**: Round Robin, Least Connections, Source IP Hash

## Default Limits

| Resource | Limit |
|----------|-------|
| LBs per region | 10 |
| Listeners per LB | 10 |
| Backend servers per LB | 50 |
| Target groups per LB | 5 |

## Security Considerations

1. Security groups control traffic to/from LB
2. HTTPS listeners need valid SSL certificates
3. Enable access logs for audit
4. Follow least-privilege for VPC/subnet placement