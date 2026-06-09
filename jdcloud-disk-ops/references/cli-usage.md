# CLI — Cloud Disk (`jdc disk`)

## Install and Config
- Install: `uv pip install jdcloud_cli`
- Config: `~/.jdc/config` INI file (env vars NOT read by CLI)

## Critical CLI Behavior
- `--output json` is a **top-level argument** — MUST be placed BEFORE `disk` subcommand
- `--no-interactive` does NOT exist — commands are non-interactive by default

## Command Reference

### Disk Lifecycle
```bash
# List disks
jdc --output json disk describe-disks \
  --region-id cn-north-1 \
  --page-number 1 \
  --page-size 20

# Create disk
jdc --output json disk create-disks \
  --region-id cn-north-1 \
  --az "cn-north-1a" \
  --disk-type "ssd" \
  --disk-size 100 \
  --disk-name "my-disk"

# Describe disk
jdc --output json disk describe-disk \
  --region-id cn-north-1 \
  --disk-id "vol-xxxxxx"

# Delete disk
jdc --output json disk delete-disk \
  --region-id cn-north-1 \
  --disk-id "vol-xxxxxx"
```

### Attach/Detach
```bash
# Attach disk to VM
jdc --output json disk attach-disk \
  --region-id cn-north-1 \
  --disk-id "vol-xxxxxx" \
  --instance-id "i-xxxxxx" \
  --device "vdb"

# Detach disk from VM
jdc --output json disk detach-disk \
  --region-id cn-north-1 \
  --disk-id "vol-xxxxxx" \
  --instance-id "i-xxxxxx"
```

### Resize
```bash
jdc --output json disk resize-disk \
  --region-id cn-north-1 \
  --disk-id "vol-xxxxxx" \
  --disk-size 200
```

### Snapshots
```bash
# Create snapshot
jdc --output json disk create-snapshot \
  --region-id cn-north-1 \
  --disk-id "vol-xxxxxx" \
  --snapshot-name "backup-$(date +%Y%m%d)"

# List snapshots
jdc --output json disk describe-snapshots \
  --region-id cn-north-1 \
  --disk-id "vol-xxxxxx"

# Delete snapshot
jdc --output json disk delete-snapshot \
  --region-id cn-north-1 \
  --snapshot-id "snap-xxxxxx"
```

## CLI vs SDK Coverage Gap
| Operation | CLI | SDK | Notes |
|-----------|-----|-----|-------|
| All core operations | ✅ | ✅ | Full parity |
| Backup policy | ❓ | ✅ | Check CLI version |