# Troubleshooting Cloud Disk

## Common API/CLI Error Codes

| Code | HTTP | Meaning | Agent Action |
|------|------|---------|--------------|
| `DiskNotFound` | 404 | Disk does not exist | Verify disk ID |
| `InvalidDiskStatus` | 400 | Wrong state for operation | Wait for transition or check current state |
| `DiskInUse` | 400 | Disk attached to VM | Detach before delete/resize |
| `DiskNotAttached` | 400 | Disk not attached | Attach first |
| `InstanceNotFound` | 404 | VM does not exist | Verify instance ID |
| `InvalidParameter` | 400 | Parameter validation failed | Check AZ, size, type |
| `QuotaExceeded` | 400 | Disk or snapshot quota exceeded | Request quota increase |
| `InsufficientBalance` | 400 | Account balance insufficient | Top up account |
| `SnapshotNotFound` | 404 | Snapshot does not exist | Verify snapshot ID |
| `SnapshotInProgress` | 400 | Snapshot operation ongoing | Wait for completion |

## Diagnostic Order
1. Describe disk to check current status and attachment
2. If attached, verify VM exists and is accessible
3. Check quota usage if creation fails
4. Review account balance if quota is fine

## Attachment Issues
- **Symptom**: Attach fails with "device busy"
- **Cause**: Device name already in use on VM
- **Fix**: Use different device name (vdb, vdc, vdd...)

## Resize Issues
- **Symptom**: Resize succeeds but space not visible in VM
- **Cause**: Filesystem not extended
- **Fix**: Use cloud assistant to extend filesystem inside VM

## Snapshot Issues
- **Symptom**: Snapshot stuck in "creating"
- **Cause**: Large disk or high I/O
- **Fix**: Wait longer; max wait is 10+ minutes for large disks