# JD Cloud VM Core Concepts

## What is a Virtual Machine (VM)

JD Cloud Virtual Machine (VM) is a scalable computing service that provides variable processing power resources. You can adjust configurations at any time based on your business needs. VMs help you build stable and secure application environments more efficiently.

## Core Components

### 1. Instance Types

JD Cloud offers various instance types to meet different business requirements:

| Instance Series | Use Cases | Features |
|----------------|-----------|----------|
| General Purpose (g-series) | Web servers, small to medium databases | Balanced CPU and memory ratio |
| Compute Optimized (c-series) | High-performance computing, batch processing | High CPU performance |
| Memory Optimized (r-series) | Large databases, caching systems | Large memory capacity |
| GPU (gn-series) | AI training, graphics rendering | Equipped with GPU accelerators |
| Local SSD (i-series) | NoSQL databases, data warehouses | High-performance local storage |

### 2. Images

Images are templates for creating VM instances, containing the operating system and pre-installed software:

- **Public Images**: Standard OS images officially provided by JD Cloud
- **Custom Images**: Personalized images created from existing instances
- **Shared Images**: Images shared by other users
- **Marketplace Images**: Pre-installed application images provided by third parties

### 3. Storage

#### Cloud Disk
- **Standard Cloud Disk**: Suitable for general application scenarios
- **High-performance Cloud Disk**: Provides higher IOPS performance
- **SSD Cloud Disk**: Provides the highest IOPS and low latency

#### Local Storage
- Some instance types provide local SSD or HDD storage
- Data is not persistent and will be lost when the instance is released

### 4. Networking

#### VPC (Virtual Private Cloud)
- Logically isolated private network environment
- Customizable IP address range, subnets, and route tables

#### Security Group
- Virtual firewall controlling inbound and outbound traffic for instances
- Supports rule configuration based on protocol, port, and IP address

#### Elastic IP (EIP)
- Public IP address that can be purchased and held independently
- Can be bound to or unbound from VM instances at any time

### 5. Key Pair

- Used for SSH login authentication on Linux instances
- Consists of a public key and a private key
- The private key must be kept safe and cannot be recovered if lost

## Instance Lifecycle

### State Transitions

```
Creating → Running ↔ Stopped
               ↓
           Rebooting
               ↓
           Deleting → Deleted
```

### Main States

| State | Description | Operable Actions |
|-------|-------------|------------------|
| Creating | Instance being created | None |
| Running | Instance running normally | Reboot, stop, reinstall OS, create snapshot |
| Stopped | Instance stopped | Start, delete, modify configuration |
| Rebooting | Instance rebooting | None |
| Deleting | Instance being deleted | None |
| Deleted | Instance deleted | None |

## Billing Models

### By Configuration

1. **Subscription (Monthly/Yearly)**
   - Suitable for long-term stable running businesses
   - More cost-effective, up to 3 years purchase
   - Cannot be canceled at any time

2. **Pay-As-You-Go**
   - Suitable for short-term testing or fluctuating businesses
   - Billed by the hour, can be released at any time
   - Relatively higher unit price

### Billing Items

- Instance specifications (CPU + Memory)
- System disk and data disks
- Public network bandwidth (if used)
- Images (some marketplace images are charged)

## High Availability Architecture

### Availability Zone

- Physically independent areas within the same region with separate power and networks
- It is recommended to deploy critical services across multiple availability zones
- Availability zones are interconnected via internal network with low latency

### Best Practices

1. **Multi-AZ Deployment**: Distribute instances across at least 2 availability zones
2. **Load Balancing**: Use load balancers to distribute traffic
3. **Auto Scaling**: Configure scaling groups to handle traffic fluctuations
4. **Regular Backups**: Use snapshots to regularly back up data

## Security Best Practices

1. **Principle of Least Privilege**: Only open necessary ports and services
2. **Regular Updates**: Promptly install OS and security patches
3. **Key Management**: Use key pairs instead of passwords for login
4. **Security Group Rules**: Regularly review and optimize security group rules
5. **Monitoring & Alerting**: Configure resource usage and abnormal access alerts
6. **Data Encryption**: Encrypt sensitive data for storage

## Performance Optimization Tips

1. **Choose the Right Instance Type**: Select matching instance specifications based on workload
2. **Use High-performance or SSD Disks**: Improve I/O performance
3. **Enable Enhanced Networking**: Get higher network bandwidth and lower latency
4. **Configure Security Groups Reasonably**: Avoid excessive security group rules affecting performance
5. **Monitor System Metrics**: Identify and resolve performance bottlenecks in a timely manner

## Common Use Cases

### 1. Web Application Hosting
- Use general-purpose instances
- Combine with load balancers for high availability
- Use cloud disks for application data storage

### 2. Database Services
- Use memory-optimized or compute-optimized instances
- Use SSD cloud disks to improve I/O performance
- Configure master-slave replication for high availability

### 3. Big Data Processing
- Use compute-optimized instance clusters
- Leverage local SSDs to improve data processing speed
- Combine with object storage for massive data retention

### 4. AI / Machine Learning
- Use GPU instances
- Pre-install deep learning frameworks
- Utilize high-speed networks to accelerate data transfer

## Related Services

- **Cloud Monitor**: Monitor VM resource usage
- **Auto Scaling**: Automatically adjust instance count based on load
- **Load Balancer**: Distribute traffic across multiple instances
- **Cloud Disk**: Provide persistent storage for VMs
- **Object Storage**: Store unstructured data
- **Container Service**: Run containerized applications
