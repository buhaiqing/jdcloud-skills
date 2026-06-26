# JD Cloud VM Core Concepts

> **ponytail: condensed from 166 to ~100 lines.**

## What is a JD Cloud VM

Elastic, scalable cloud computing service providing variable processing power. Configurations adjust on-demand.

## Instance Types

| Series | Use Cases |
|--------|-----------|
| General Purpose (g) | Web servers, small/mid databases |
| Compute Optimized (c) | HPC, batch processing |
| Memory Optimized (r) | Large databases, caches |
| GPU (gn) | AI training, rendering |
| Local SSD (i) | NoSQL, data warehouses |

## Instance Lifecycle

```
Creating → Running ↔ Stopped → Deleting → Deleted
               ↓
           Rebooting
```

| State | Operable Actions |
|-------|-----------------|
| Running | Reboot, stop, create snapshot, associate EIP |
| Stopped | Start, delete, resize (spec change requires stopped state) |
| Error | Reinstall OS or recover from console |

## Storage

- **Cloud Disks**: Standard / Performance / SSD (persistent, can be detached and re-attached)
- **Local Storage**: Ephemeral, lost on instance release

## Networking

- **VPC**: Isolated network with custom CIDR, subnets, route tables
- **Security Groups**: Stateful firewall per instance
- **EIP**: Independently purchasable public IP, bindable to any instance

## Billing

- **Subscription** (monthly/yearly): Long-term, lower unit price
- **Pay-As-You-Go**: Hourly, no commitment, higher unit price

## Security Best Practices

1. Least-privilege security group rules (only open needed ports)
2. Use key pairs over passwords for SSH
3. Regular OS security patching
4. Enable Cloud Monitor alerts
5. Encrypt sensitive data at rest

## See Also

- [SKILL.md execution flows](../SKILL.md) for operational runbooks
- `jdcloud-disk-ops` for disk lifecycle
- `jdcloud-vpc-ops` for VPC / subnet / security group management