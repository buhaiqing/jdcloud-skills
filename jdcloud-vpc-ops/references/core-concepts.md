# JD Cloud VPC Core Concepts

## VPC (Virtual Private Cloud)
A Virtual Private Cloud (VPC) is a logically isolated virtual network environment in JD Cloud. It provides a secure and controllable network space for your cloud resources.

### Key Features
- **Isolation**: Complete network isolation between different VPCs
- **Customization**: Define your own IP address range, subnets, route tables, and network gateways
- **Security**: Built-in security features including security groups and network ACLs
- **Scalability**: Automatically scales to accommodate your resource needs

### VPC Components
1. **CIDR Block**: The IP address range for the VPC (e.g., 10.0.0.0/16)
2. **Subnets**: Segments within the VPC for organizing resources
3. **Route Tables**: Control traffic routing within and outside the VPC
4. **Internet Gateway**: Enables communication between VPC and the internet
5. **NAT Gateway**: Allows instances in private subnets to access the internet
6. **VPC Peering**: Connects two VPCs privately

## Subnet
A subnet is a range of IP addresses in your VPC. Subnets allow you to segment your network and organize resources logically.

### Subnet Types
- **Public Subnet**: Has a route to an Internet Gateway
- **Private Subnet**: No direct route to the Internet Gateway

### Subnet Configuration
- Must be a subset of the VPC CIDR block
- Associated with a specific Availability Zone
- Can have its own route table and network ACL

## Security Group
A security group acts as a virtual firewall for your instance to control inbound and outbound traffic.

### Security Group Characteristics
- Stateful: Return traffic is automatically allowed
- Applied at the instance level
- Default deny all inbound, allow all outbound
- Rules can be added to allow specific traffic

## Network ACL
A network ACL is a stateless firewall that controls inbound and outbound traffic at the subnet level.

### Network ACL vs Security Group
| Feature | Network ACL | Security Group |
|---------|-------------|----------------|
| Scope | Subnet level | Instance level |
| Stateful | No | Yes |
| Rule Evaluation | Processes all rules | Processes all rules |
| Default | Allow all | Deny all inbound, allow all outbound |

## Route Table
Route tables contain a set of rules (routes) that determine where network traffic is directed.

### Route Table Components
- **Routes**: Define paths for traffic
- **Associations**: Link route tables to subnets
- **Gateway Entries**: Point to internet gateways, NAT gateways, etc.

## VPC Peering
VPC Peering enables you to connect one VPC with another via a direct network route using private IP addresses.

### Peering Connection Features
- Private connectivity between VPCs
- Supports VPCs in different regions
- No single point of failure or bandwidth bottleneck

## NAT Gateway
A NAT Gateway enables instances in a private subnet to connect to the internet or other JD Cloud services, but prevents the internet from initiating connections to these instances.

### NAT Gateway Types
- **Public NAT Gateway**: Provides internet access for private instances
- **Internal NAT Gateway**: Used for internal network communication

## Internet Gateway
An Internet Gateway is a horizontally scaled, redundant, and highly available VPC component that allows communication between your VPC and the internet.

## VPN Connection
VPN connections enable you to securely connect your on-premises network to your VPC using IPsec VPN tunnels.

## Direct Connect
Direct Connect enables you to establish a dedicated network connection from your premises to JD Cloud, bypassing internet congestion.

## Flow Log
Flow logs capture information about IP traffic going to and from network interfaces in your VPC.

## Traffic Mirroring
Traffic mirroring enables you to inspect and analyze network traffic for security, monitoring, and troubleshooting purposes.

## High Availability Virtual IP (HAVIP)
HAVIP is a private IP address that can be dynamically assigned to multiple instances to provide high availability.

## Prefix List
A prefix list is a collection of CIDR blocks that can be used in route tables and security group rules for easier management.