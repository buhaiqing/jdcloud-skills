# Core Concepts — JD Cloud NAT Gateway

## What is JD Cloud NAT Gateway?

JD Cloud NAT Gateway (NAT网关) is a managed network address translation service that enables instances within a VPC to access the internet (SNAT) or allows external users to access instances within the VPC (DNAT). It provides a highly available, scalable, and secure way to manage internet traffic for VPC resources.

## Key Resources

### NAT Gateway Instance

A NAT gateway is a regional resource that resides within a specific VPC. It provides:
- **SNAT (Source Network Address Translation)**: Allows instances in private subnets to initiate outbound traffic to the internet
- **DNAT (Destination Network Address Translation)**: Allows external users to access services running on private instances via port forwarding
- **Elastic IP Association**: One or more elastic IPs can be associated for SNAT/DNAT traffic

| Property | Description |
|----------|-------------|
| `natGatewayId` | Unique identifier (e.g., `nat-xxxxxxxx`) |
| `natGatewayName` | User-defined name |
| `state` | Lifecycle state: `available`, `creating`, `deleting`, `error` |
| `vpcId` | Associated VPC (one NAT per VPC) |
| `elasticIpAddresses` | List of associated elastic IP addresses |
| `snatRuleCount` | Number of SNAT rules |
| `dnatRuleCount` | Number of DNAT rules |
| `description` | Optional user description |

### SNAT Rule

SNAT rules define which subnets can access the internet through the NAT gateway and which elastic IPs to use for outbound traffic.

| Property | Description |
|----------|-------------|
| `snatRuleId` | Unique identifier |
| `natGatewayId` | Associated NAT gateway |
| `subnetId` | Target subnet for outbound access |
| `elasticIpIds` | Elastic IP IDs for the outbound traffic |
| `state` | Rule state |

### DNAT Rule

DNAT rules define port forwarding from the NAT gateway's elastic IP to a private IP within the VPC.

| Property | Description |
|----------|-------------|
| `dnatRuleId` | Unique identifier |
| `natGatewayId` | Associated NAT gateway |
| `protocol` | TCP or UDP |
| `elasticIpId` | Elastic IP ID for inbound traffic |
| `publicPort` | External port (1-65535) |
| `privateIp` | Target private IP address |
| `privatePort` | Internal port (1-65535) |

## State Transitions

```
[Creating] ──► [Available] ◄── [Updating]
     │               │
     ▼               ▼
  [Error]        [Deleting] ──► (Deleted / 404)
```

## Key Constraints

- **One NAT Gateway per VPC**: A VPC can only have one NAT gateway at a time
- **EIP Requirements**: At least one elastic IP must be associated for SNAT/DNAT to function
- **SNAT Subnet Uniqueness**: Each subnet can only have one SNAT rule
- **DNAT Port Uniqueness**: Each (EIP, publicPort, protocol) tuple must be unique
- **Regional Resource**: NAT gateways are regional (not zonal)

## Use Cases

| Use Case | Approach |
|----------|----------|
| Private subnet internet access | Create NAT Gateway + SNAT rule for the subnet |
| Expose private web server | Create DNAT rule (EIP:80 → privateIP:80) |
| Multiple outbound IPs | Associate multiple EIPs for SNAT source diversity |
| Production HA | Associate ≥2 EIPs, configure on different ISPs |

## Related Services

| Service | Relationship |
|---------|-------------|
| VPC | NAT must belong to a VPC |
| Elastic IP | NAT requires EIPs for SNAT/DNAT |
| Route Table | Subnet route table must point 0.0.0.0/0 to NAT |
| Subnet | SNAT rules target specific subnets |
| Cloud Monitor | Bandwidth and connection metrics |