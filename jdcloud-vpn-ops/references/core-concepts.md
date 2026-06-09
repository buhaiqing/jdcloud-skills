# Core Concepts — JD Cloud VPN

## VpnGateway (VPN网关)

A **VpnGateway** is the JD Cloud-side VPN endpoint. It is created within a specific VPC and region. The VPN gateway terminates IPsec tunnels from remote customer gateways.

- **Lifecycle**: creating → available → deleting → (deleted)
- **Binding**: One VPN gateway is bound to exactly one VPC.
- **Connections**: A VPN gateway can have multiple VPN connections to different customer gateways.
- **Bandwidth**: Supports configurable bandwidth (check regional quotas).

## CustomerGateway (客户网关)

A **CustomerGateway** represents the remote-side VPN endpoint (e.g., an on-premises router, firewall, or another cloud VPN gateway).

- **Identification**: Defined primarily by its public IPv4 address (`ipAddress`).
- **Reusability**: A single customer gateway can be used in multiple VPN connections (e.g., for redundancy).
- **Lifecycle**: creating → available → deleting → (deleted)

## VpnConnection (VPN连接)

A **VpnConnection** is the IPsec/IKE tunnel between a VpnGateway and a CustomerGateway.

- **State**: pending → available → down → deleting → (deleted)
- **IKE Version**: Supports IKEv1 and IKEv2. IKEv2 is recommended for better security and faster reconnection.
- **PSK (Pre-Shared Key)**: The authentication secret shared between both tunnel endpoints. Must be kept confidential.
- **Subnets**: Defines `localSubnets` (JD Cloud side) and `remoteSubnets` (customer side) that are allowed through the tunnel.

## IPSec / IKE

### IKE (Internet Key Exchange)

IKE negotiates the security association (SA) for the IPsec tunnel.

- **Phase 1 (IKE SA)**: Authenticates peers and establishes a secure channel.
- **Phase 2 (IPsec SA)**: Negotiates the actual data encryption parameters.

### IPsec Parameters

| Parameter | Common Values | Recommendation |
|-----------|---------------|----------------|
| Encryption | aes128, aes192, aes256 | aes256 |
| Integrity | sha1, sha256, sha384 | sha256 |
| DH Group | group2, group5, group14, group24 | group14 |
| IKE Lifetime | 28800s (default) | 28800s |
| IPsec Lifetime | 3600s (default) | 3600s |

### DPD (Dead Peer Detection)

DPD detects when the remote peer is unreachable and triggers rekey or teardown:
- **Interval**: How often to send DPD probes (seconds).
- **Retries**: Number of failed probes before declaring peer dead.

## Hybrid Cloud Connectivity Patterns

### Pattern 1: Single Tunnel (Basic)
```
[On-prem Network] ---(IPsec)--- [VpnGateway] --- [VPC]
```
Simplest setup. Single point of failure.

### Pattern 2: Redundant Tunnels (HA)
```
[On-prem Router 1] ---(IPsec)--- [VpnGateway]
[On-prem Router 2] ---(IPsec)--- [VpnGateway]
```
Two customer gateways (or two IPs on same device) with two VPN connections. Provides failover.

### Pattern 3: Multi-Site
```
[Site A] ---(IPsec)--- [VpnGateway] --- [VPC]
[Site B] ---(IPsec)--- [VpnGateway] --- [VPC]
```
Multiple customer gateways from different locations connected to the same VPN gateway.

## Routing Considerations

1. **Route Table Updates**: After creating a VPN connection, add routes in the VPC route table pointing remote subnets to the VPN gateway.
2. **Non-overlapping CIDRs**: Local and remote subnets must not overlap.
3. **Asymmetric Routing**: Ensure both directions of traffic flow through the same tunnel to avoid anti-replay drops.

## Security Best Practices

- Use **IKEv2** over IKEv1.
- Use **aes256** encryption with **sha256** integrity.
- Use a **strong PSK** (minimum 16 random characters); store in secrets manager.
- Restrict security groups to only allow necessary traffic through the tunnel.
- Enable DPD for faster failure detection.
- Monitor tunnel state and set alarms for `down` transitions.