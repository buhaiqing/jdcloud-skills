# Cloud Disk Core Concepts

## Disk Types
- **SSD**: High-performance solid-state storage, suitable for I/O-intensive workloads
- **Premium HDD**: Balanced performance and cost, suitable for general workloads
- **Standard HDD**: Cost-effective storage, suitable for backup and archival

## Disk Categories
- **System Disk**: Contains operating system, created with VM, cannot be detached
- **Data Disk**: Additional storage for user data, can be attached/detached freely

## Disk States
- `creating` — Disk being provisioned
- `available` — Ready to attach to VM
- `in-use` — Currently attached to a VM
- `detaching` — Being detached from VM
- `deleting` — Being deleted
- `error` — Error state, requires support intervention

## Snapshot
Point-in-time backup of a disk. Snapshots:
- Are incremental (only changed blocks stored)
- Can be used to create new disks
- Support cross-region copy
- Are billed based on stored data size

## Backup Policy
Automated snapshot schedule:
- Daily/weekly backup windows
- Retention policy (keep N snapshots)
- Cross-region replication option

## IOPS and Throughput
Performance characteristics vary by disk type:
- SSD: High IOPS (3000+), low latency
- Premium HDD: Medium IOPS (500-1000)
- Standard HDD: Lower IOPS (100-200)

## Multi-Attach
Some disk types support multi-attach (read-only) to multiple VMs simultaneously.