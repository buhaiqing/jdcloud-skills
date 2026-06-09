# API & SDK — Cloud Disk

## OpenAPI
- Base URL: `https://disk.jdcloud-api.com/v1`
- Protocol: HTTPS only
- Authentication: JD Cloud signature V3

## SDK Operations Map

| Goal | API Operation | SDK Method | Notes |
|------|---------------|------------|-------|
| Create Disk | `CreateDisks` | `createDisks` | Returns disk ID |
| Delete Disk | `DeleteDisk` | `deleteDisk` | Disk must be available |
| Describe Disk | `DescribeDisk` | `describeDisk` | Single disk details |
| List Disks | `DescribeDisks` | `describeDisks` | With filters |
| Attach Disk | `AttachDisk` | `attachDisk` | To running/stopped VM |
| Detach Disk | `DetachDisk` | `detachDisk` | Unmount first! |
| Resize Disk | `ResizeDisk` | `resizeDisk` | Online or offline |
| Create Snapshot | `CreateSnapshot` | `createSnapshot` | From disk |
| Delete Snapshot | `DeleteSnapshot` | `deleteSnapshot` | Irreversible |
| Describe Snapshot | `DescribeSnapshot` | `describeSnapshot` | Snapshot details |
| List Snapshots | `DescribeSnapshots` | `describeSnapshots` | With filters |
| Restore Disk | CreateDisk from snapshot | `createDisks` | With snapshotId |

## Common Request Patterns

### Create SSD Disk
```python
req = CreateDisksRequest(
    regionId="cn-north-1",
    diskSpec={
        "az": "cn-north-1a",
        "name": "my-data-disk",
        "diskType": "ssd",
        "diskSizeGB": 100,
        "chargeSpec": {"chargeMode": "postpaid_by_usage"}
    }
)
```

### Create Disk from Snapshot
```python
req = CreateDisksRequest(
    regionId="cn-north-1",
    diskSpec={
        "az": "cn-north-1a",
        "name": "restored-disk",
        "snapshotId": "snapshot-xxx",
        "diskType": "ssd",
        "diskSizeGB": 100,  # Must be >= snapshot size
        "chargeSpec": {"chargeMode": "postpaid_by_usage"}
    }
)
```