# JD Cloud CLB Core Concepts

## Overview
JD Cloud CLB (Cloud Load Balancer) is a fully managed load balancing service that distributes incoming application traffic across multiple backend servers. It helps improve the availability, scalability, and reliability of your applications.

## Key Components

### CLB Instance
- A virtual load balancer that serves as the single point of contact for clients
- Can be internet-facing (public) or internal (private)
- Has a unique ID and IP address

### Listener
- Configures how the CLB handles incoming traffic
- Supports Layer 4 (TCP/UDP) and Layer 7 (HTTP/HTTPS) protocols
- Defines rules for forwarding traffic to backend servers

### Backend Server Group
- A collection of backend servers that receive traffic from the CLB
- Servers can be added or removed dynamically
- Health checks determine which servers are available to receive traffic

### Health Check
- Monitors the health status of backend servers
- Automatically removes unhealthy servers from the rotation
- Supports various protocols and health check methods

### SSL Certificate
- Used for HTTPS listeners to encrypt traffic between clients and the CLB
- Manages SSL/TLS certificates for secure communication
- Supports certificate upload, rotation, and deletion
- Certificate formats: PEM (Privacy Enhanced Mail)
- Key features:
  - **Certificate Chain**: Supports intermediate CA certificates
  - **Multiple Formats**: RSA, ECDSA certificates
  - **Automatic Validation**: Validates certificate-key pair matching
  - **Expiration Monitoring**: Tracks certificate validity period
  - **Domain Binding**: Associates certificates with specific domains

### SSL Policy
- Defines allowed TLS/SSL protocol versions and cipher suites
- Common policies:
  - `tls-1-0`: Allows TLS 1.0 and above
  - `tls-1-1`: Allows TLS 1.1 and above
  - `tls-1-2`: Allows TLS 1.2 and above (recommended)
  - `tls-1-3`: Allows TLS 1.3 only (most secure)
- Helps balance security and compatibility requirements

## Architecture
The CLB architecture consists of:
1. **Frontend**: Receives client requests on configured ports and protocols
2. **Load Balancing Algorithm**: Distributes traffic based on selected algorithm (Round Robin, Least Connections, etc.)
3. **Backend**: Forwards requests to healthy backend servers
4. **Health Monitoring**: Continuously checks backend server health

## Use Cases
- Web application load balancing
- API gateway traffic distribution
- Microservices architecture traffic management
- High-availability application deployment
- SSL termination offloading
- Secure HTTPS traffic handling with certificate management
- Multi-domain SSL certificate management
- Automated certificate rotation for compliance