# Integration

## Environment Setup (uv)

```bash
uv venv --python 3.10
source .venv/bin/activate
uv pip install jdcloud_cli jdcloud_sdk
```

## Integration with VM Operations

### Create VM with Data Disk
```python
# 1. Create data disk (this skill)
# 2. Create VM with disk attachment (jdcloud-vm-ops)
#    OR create VM then attach disk
```

### Expand VM Storage
```python
# 1. Resize disk (this skill)
# 2. Extend filesystem inside VM (jdcloud-vm-ops cloud assistant)
#    - For Linux: resize2fs or xfs_growfs
#    - For Windows: Extend-Volume in Disk Management
```

### Backup VM Data
```python
# 1. Stop VM for consistent backup (jdcloud-vm-ops)
# 2. Create snapshot of system disk (this skill)
# 3. Create snapshots of data disks (this skill)
# 4. Start VM (jdcloud-vm-ops)
```

## Monitoring Integration

### With CloudMonitor (`jdcloud-cloudmonitor-ops`)
Set up alarms for:
- Disk IOPS utilization
- Disk throughput
- Disk capacity usage
- Snapshot storage billing