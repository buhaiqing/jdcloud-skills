# Core Concepts - JD Cloud EIP

## Overview

JD Cloud Elastic IP (EIP) is a static public IP address that can be dynamically associated with or detached from cloud resources such as Virtual Machines (VMs), Load Balancers (CLB), and NAT Gateways.

## Key Concepts

### Elastic IP Address

A public IP address that can be:
- Allocated and released on demand
- Associated with or dissociated from resources
- Retained independently of the resources it's associated with

### Bandwidth

The maximum data transfer rate for the EIP, measured in Mbps. Bandwidth can be adjusted dynamically.

### Billing Methods

- **Pay-as-you-go**: Charged based on actual usage
- **Monthly package**: Flat monthly fee for guaranteed bandwidth

### Association

Linking an EIP to a resource (VM, CLB, NAT Gateway). Only one resource can be associated at a time.

### Dissociation

Unlinking an EIP from a resource. The EIP returns to `available` state and can be reused.

## Resource States

| State | Description |
|-------|-------------|
| `available` | EIP is created but not associated with any resource |
| `in-use` | EIP is associated with a resource |
| `releasing` | EIP is being released/deleted |
| `error` | Error state, contact support |

## Supported Resources

- Virtual Machines (VM/ECS)
- Load Balancers (CLB)
- NAT Gateways
- Other JD Cloud resources that support public IP assignment

## Network Architecture

EIP provides public network connectivity while maintaining private network isolation through VPC security groups and network ACLs.
