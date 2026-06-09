# JD Cloud Disk Quick Reference

> Quick command reference for Cloud Disk operations. For full details, see [SKILL.md](SKILL.md) and [CLI Usage](references/cli-usage.md).

## Disk Lifecycle Quick Reference

### 1. Query Disks
```bash
# List all disks
jdc --output json disk describe-disks \
  --region-id cn-north-1 --page-number 1 --page-size 20

# Filter by status
jdc --output json disk describe-disks \
  --region-id cn-north-1 \
  --filters '[{"name":"status","values":["available"]}]'

# Single disk detail
jdc --output json disk describe-disk \
  --region-id cn-north-1 --disk-id vol-xxxxx
```

### 2. Create → Attach → Detach → Resize → Delete
```bash
# Create data disk
jdc --output json disk create-disks \
  --region-id cn-north-1 --az "cn-north-1a" \
  --disk-type "ssd" --disk-size 100 \
  --disk-name "data-disk"

# Attach to VM
jdc --output json disk attach-disk \
  --region-id cn-north-1 --disk-id vol-xxxxx \
  --instance-id i-xxxxx --device "vdb"

# Detach from VM
jdc --output json disk detach-disk \
  --region-id cn-north-1 --disk-id vol-xxxxx \
  --instance-id i-xxxxx

# Resize (expand only)
jdc --output json disk resize-disk \
  --region-id cn-north-1 --disk-id vol-xxxxx --disk-size 200

# Delete (must be available)
jdc --output json disk delete-disk \
  --region-id cn-north-1 --disk-id vol-xxxxx
```

## Snapshot Quick Reference

```bash
# Create snapshot
jdc --output json disk create-snapshot \
  --region-id cn-north-1 --disk-id vol-xxxxx \
  --snapshot-name "backup-$(date +%Y%m%d)"

# List snapshots
jdc --output json disk describe-snapshots \
  --region-id cn-north-1 --disk-id vol-xxxxx

# Delete snapshot
jdc --output json disk delete-snapshot \
  --region-id cn-north-1 --snapshot-id snap-xxxxx

# Create disk from snapshot
jdc --output json disk create-disks \
  --region-id cn-north-1 --az "cn-north-1a" \
  --disk-type "ssd" --disk-size 100 \
  --snapshot-id snap-xxxxx \
  --disk-name "restored-disk"
```

## Disk States

| Status | Description | Allowed Operations |
|--------|-------------|-------------------|
| `creating` | Provisioning | Wait |
| `available` | Ready to attach | Attach, Resize, Delete |
| `in-use` | Attached to VM | Detach, Resize |
| `detaching` | Being detached | Wait |
| `deleting` | Being deleted | Wait |
| `error` | Error | Support required |

## Disk Types & Performance

| Type | IOPS | Latency | Best For |
|------|------|---------|----------|
| `ssd` | 3000+ | Very low | Databases, high I/O |
| `premium-hdd` | 500-1000 | Low | General workloads |
| `standard-hdd` | 100-200 | Medium | Backup, archival |

## JSON Extraction Quick Reference

```bash
# Table format: id, name, status, size, attached VM
jdc --output json disk describe-disks --region-id cn-north-1 \
  | jq -r '.result.disks[] | "\(.diskId)\t\(.name)\t\(.status)\t\(.diskSizeGB)GB\t\(.instanceId // "-")"' \
  | column -t -s $'\t'

# List only available disks (can be attached)
jdc --output json disk describe-disks --region-id cn-north-1 \
  | jq -r '.result.disks[] | select(.status == "available") | .diskId'

# Check if disk is attached before delete
jdc --output json disk describe-disk --region-id cn-north-1 --disk-id vol-xxxxx \
  | jq '.result.disk.status'
```

## Python SDK Quick Start

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.disk.client import DiskClient
from jdcloud_sdk.services.disk.apis.DescribeDisksRequest import DescribeDisksRequest, DescribeDisksParameters

credential = Credential(
    os.environ['JDC_ACCESS_KEY'],
    os.environ['JDC_SECRET_KEY']
)
client = DiskClient(credential, os.environ.get('JDC_REGION', 'cn-north-1'))

# List disks
params = DescribeDisksParameters(regionId='cn-north-1', pageNumber=1, pageSize=20)
request = DescribeDisksRequest(parameters=params)
response = client.describeDisks(request)

if response.error is None:
    for disk in response.result.disks:
        print(f"{disk.diskId}: {disk.name} ({disk.status}, {disk.diskSizeGB}GB)")
```

## Common Error Codes

| Code | Meaning | Fix |
|------|---------|-----|
| `DiskNotFound` | Wrong disk ID | Verify ID |
| `DiskInUse` | Still attached | Detach first |
| `InvalidDiskStatus` | Wrong state | Wait for `available` |
| `QuotaExceeded` | Too many disks | Request quota increase |

## Related Documents

| Document | Description |
|----------|-------------|
| [SKILL.md](SKILL.md) | Full skill definition |
| [CLI Usage](references/cli-usage.md) | Complete CLI reference |
| [API & SDK](references/api-sdk-usage.md) | SDK operations map |
| [Troubleshooting](references/troubleshooting.md) | Detailed troubleshooting |
| [Core Concepts](references/core-concepts.md) | Disk types, states, snapshots |
