---
name: jdcloud-disk-ops
description: >-
  Use when managing JD Cloud Disk (云硬盘) resources — create, delete, resize,
  attach, detach disks; manage snapshots and backup policies; query disk
  usage and performance. Works with "云硬盘", "磁盘", "Disk", "云盘",
  "数据盘", "系统盘" without saying "JD Cloud" explicitly. NOT for
  Object Storage (OSS), File Storage (NAS), or local VM filesystem operations.
license: MIT
compatibility: >-
  Official JD Cloud SDK (Python 3.10+), valid API credentials, network
  access to JD Cloud endpoints, and official JD Cloud CLI (`jdc`) with
  disk operations support.
metadata:
  author: buhaiqing
  version: "1.0.0"
  last_updated: "2026-06-08"
  runtime: Harness AI Agent
  api_profile: "Disk API v1.0 - https://docs.jdcloud.com/cn/cloud-disk-service/api"
  cli_applicability: dual-path
  cli_version_locked: "1.2.12"
  sdk_version_locked: ">=1.6.26"
  cli_support_evidence: >-
    Official `jdc` CLI supports disk operations. Verified via `jdc disk --help`
    which shows commands: create-disks, delete-disk, resize-disk, attach-disk,
    detach-disk, describe-disk, describe-disks, create-snapshot, etc.
  environment:
    - JDC_ACCESS_KEY
    - JDC_SECRET_KEY
    - JDC_REGION
---

> This skill follows the [Agent Skill OpenSpec](https://agentskills.io/specification).

# JD Cloud Disk Operations Skill

## Overview
JD Cloud Disk (云硬盘服务, CDS) provides persistent block storage for JD Cloud VMs. Disks can be created independently, attached to/detached from VMs, resized dynamically, and backed up via snapshots.

This skill covers:
- **Disk Lifecycle**: Create, delete, describe, list disks
- **Disk Attachment**: Attach to VM, detach from VM
- **Disk Expansion**: Online/offline resize (expand capacity)
- **Snapshot Management**: Create, delete, rollback from snapshots
- **Backup Policy**: Automated backup schedules

### CLI applicability (repository policy)

- **`cli_applicability: dual-path`:** Official `jdc` CLI supports disk operations. The Agent MUST attempt to use `jdc` as the **primary execution path**. If `jdc` installation or command execution fails, the Agent MUST retry up to **3 times** (with exponential backoff). Only after **3 consecutive failures** should the Agent fall back to **SDK/API**. Both paths MUST be documented.
- **Path Preference:** Follow **jdc-first with SDK fallback** strategy. See [CLI Usage](references/cli-usage.md) for detailed comparison.

## Trigger & Scope (Agent-Readable)

### SHOULD Use This Skill When
- User mentions "Disk" OR "云硬盘" OR "磁盘" OR "云盘" OR "数据盘" OR "系统盘"
- Task involves creating, deleting, resizing disks
- Task involves attaching/detaching disks to/from VMs
- Task involves creating snapshots or managing backup policies
- Task keywords: create-disk, delete-disk, resize-disk, attach-disk, detach-disk, create-snapshot, 创建磁盘, 挂载磁盘, 扩容磁盘

### SHOULD NOT Use This Skill When
- Task is about Object Storage (OSS) buckets/objects → delegate to: `jdcloud-oss-ops`
- Task is about File Storage (NAS) → delegate to: `jdcloud-nas-ops` (when available)
- Task is about VM lifecycle (start/stop/create VM) → delegate to: `jdcloud-vm-ops`
- Task is purely about VM filesystem operations (mount/umount inside OS) → use `jdcloud-vm-ops` cloud assistant
- Task is about monitoring/alarms for disks → delegate to: `jdcloud-cloudmonitor-ops`

### Delegation Rules
- If user wants a new VM with a new data disk, create disk first (this skill), then create VM with disk attachment (jdcloud-vm-ops), or attach after VM creation
- If user wants to expand a VM's system disk, resize the disk (this skill), then extend filesystem inside VM (jdcloud-vm-ops cloud assistant)
- If user wants to backup disk data, create snapshot (this skill); for cross-region backup, consider OSS (jdcloud-oss-ops)

## Variable Convention (Agent-Readable)

Structured placeholders reduce injection ambiguity and unsafe prompts:

| Placeholder | Meaning | Agent Action |
|-------------|---------|--------------|
| `{{env.JDC_ACCESS_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_SECRET_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_REGION}}` | From runtime environment | Use `cn-north-1` as default if unset |
| `{{user.region}}` | User-supplied region | Ask once; reuse |
| `{{user.disk_id}}` | Cloud disk ID | Ask once; reuse |
| `{{user.disk_name}}` | Cloud disk name | Ask once; reuse |
| `{{user.instance_id}}` | VM instance ID for attach/detach | Ask once; reuse |
| `{{user.snapshot_id}}` | Snapshot ID | Parse from output or ask |
| `{{output.disk_id}}` | Created disk ID | Parse from `$.result.diskIds[0]` (CLI) or `$.result.diskId` (SDK) |
| `{{output.snapshot_id}}` | Created snapshot ID | Parse from `$.result.snapshotId` |

> **`{{env.*}}` MUST NOT** be collected from the user. **`{{user.*}}`** MUST be collected interactively when missing.

> **Security Warning:** **NEVER** log, print, or expose `JDC_SECRET_KEY` (or any secret) in console output, debug messages, or logs. When verification is needed, check existence only (e.g., `if os.environ.get('JDC_SECRET_KEY')`) without printing the actual value. If logging credential status is required, use masked placeholders like `JDC_SECRET_KEY=<masked>` or `JDC_SECRET_KEY=***`.

## API and Response Conventions (Agent-Readable)

### Mandatory CLI Conventions
- All CLI commands MUST place `--output json` BEFORE the subcommand: `jdc --output json disk <command> ...`
- `--no-interactive` does NOT exist in `jdc` CLI — all commands are non-interactive by default; omit this flag.
- Credentials: CLI reads from `~/.jdc/config` INI only (NOT from env vars). SDK uses env vars.

### Key JSON Paths

| Operation | CLI JSON Path | SDK JSON Path | Type | Description |
|-----------|---------------|---------------|------|-------------|
| Create Disk | `$.result.diskIds[0]` | `$.result.diskId` | string | New disk ID (format: `vol-xxxxxx`) |
| Describe Disk | `$.result.disk.diskId` | `$.result.disk.diskId` | string | Disk identifier |
| Describe Disk | `$.result.disk.status` | `$.result.disk.status` | string | `available`, `in-use`, `creating`, etc. |
| Describe Disk | `$.result.disk.instanceId` | `$.result.disk.instanceId` | string | Attached VM ID (if any) |
| List Disks | `$.result.disks[*].diskId` | `$.result.disks[*].diskId` | array | Disk IDs |
| Attach Disk | `$.requestId` | `$.requestId` | string | Request tracking ID |
| Create Snapshot | `$.result.snapshotId` | `$.result.snapshotId` | string | New snapshot ID |

### Disk Status Values
- `creating` — Disk being created
- `available` — Disk ready to attach
- `in-use` — Disk attached to VM
- `detaching` — Disk being detached
- `deleting` — Disk being deleted
- `error` — Disk in error state

### Expected State Transitions

| Operation | Initial State | Target State | Poll Interval | Max Wait |
|-----------|---------------|--------------|---------------|----------|
| Create Disk | — | `available` | 5s | 300s |
| Attach Disk | `available` | `in-use` | 5s | 120s |
| Detach Disk | `in-use` | `available` | 5s | 120s |
| Resize Disk | any | same (capacity updated) | 5s | 300s |
| Create Snapshot | — | `completed` | 5s | 600s |
| Delete Disk | any | absent | 5s | 60s |

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-06-08 | Initial dual-path skill for JD Cloud Disk (jdc-first with SDK fallback) |

## Execution Flows (Agent-Readable)

Every operation: **Pre-flight → Execute (jdc primary / SDK fallback) → Validate → Recover**.

### Operation: Create Disk

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| SDK / deps | Import client; version check | No import error | Document install |
| CLI / deps | `jdc --version` | Exit code 0 | Document CLI install |
| Credentials | `~/.jdc/config` (CLI) or env (SDK) | Valid credentials | HALT; configure credentials |
| Region | `jdc --output json vm describe-regions` | Region valid | Suggest valid regions |
| AZ | Verify availability zone exists | AZ valid | Suggest valid AZs |
| Disk type | Check supported types | Type in [ssd, premium-hdd, standard-hdd] | Suggest valid types |
| Quota | Check disk quota | Sufficient quota | HALT; request quota increase |

#### Execution — CLI (Primary Path)

```bash
# Create disk via CLI
jdc --output json disk create-disks \
  --region-id "{{user.region}}" \
  --az "{{user.az}}" \
  --disk-type "{{user.disk_type|default('ssd')}}" \
  --disk-size "{{user.disk_size}}" \
  --disk-name "{{user.disk_name}}" \
  --charge-mode "postpaid_by_usage" \
  --count 1
```

> **Note:** The `--output json` flag MUST be placed BEFORE `disk` subcommand.

#### Execution — SDK (Fallback Path)

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.disk.client import DiskClient
from jdcloud_sdk.services.disk.apis.create_disks_request import CreateDisksRequest

credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"]
)
client = DiskClient(credential, os.environ.get("JDC_REGION", "cn-north-1"))

req = CreateDisksRequest(
    regionId="{{user.region}}",
    diskSpec={
        "az": "{{user.az}}",
        "name": "{{user.disk_name}}",
        "description": "Created via skill",
        "diskType": "{{user.disk_type|default('ssd')}}",
        "diskSizeGB": {{user.disk_size}},
        "chargeSpec": {
            "chargeMode": "postpaid_by_usage"
        }
    },
    maxCount=1
)
resp = client.createDisks(req)
print(f"Disk created: {resp.result.diskId}")
```

#### Post-execution Validation

1. Parse `{{output.disk_id}}` from response:
   - CLI: `$.result.diskIds[0]`
   - SDK: `$.result.diskId`
2. Poll **DescribeDisk** until status is `available`:
   ```bash
   # CLI polling
   for i in $(seq 1 60); do
     STATUS=$(jdc --output json disk describe-disk \
       --region-id "{{user.region}}" \
       --disk-id "{{output.disk_id}}" | jq -r '.result.disk.status')
     [ "$STATUS" = "available" ] && break
     sleep 5
   done
   ```
3. Report disk ID, size, type, and status to user

#### Failure Recovery

| Error pattern | Max retries | Backoff | Agent Action |
|---------------|-------------|---------|--------------|
| `InvalidParameter` / 400 | 0–1 | — | Fix parameters; retry once |
| `QuotaExceeded` | 0 | — | HALT; suggest quota increase |
| `InsufficientBalance` | 0 | — | HALT; suggest account top-up |
| `ResourceAlreadyExists` (name) | 0 | — | Suggest new disk name |
| Throttling / 429 | 3 | 2s, 4s, 8s | Back off and retry |
| `InternalError` / 5xx | 3 | 2s, 4s, 8s | Retry; then HALT |

---

### Operation: Attach Disk to VM

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| Disk exists | DescribeDisk | Disk found | HALT; create disk first |
| Disk status | `status == "available"` | Available for attach | Wait or force detach |
| VM exists | DescribeInstance (vm-ops) | VM found | HALT; create VM first |
| VM status | VM is running or stopped | Can attach disk | Wait for VM ready |
| Device mount point | Optional device name | Valid device | Auto-assign if not specified |

#### Execution — CLI (Primary Path)

```bash
jdc --output json disk attach-disk \
  --region-id "{{user.region}}" \
  --disk-id "{{user.disk_id}}" \
  --instance-id "{{user.instance_id}}" \
  --device "{{user.device|default('vdb')}}"
```

#### Execution — SDK (Fallback Path)

```python
from jdcloud_sdk.services.disk.apis.attach_disk_request import AttachDiskRequest

req = AttachDiskRequest(
    regionId="{{user.region}}",
    diskId="{{user.disk_id}}",
    instanceId="{{user.instance_id}}",
    device="{{user.device|default('vdb')}}"
)
resp = client.attachDisk(req)
print(f"Disk attached: {resp.requestId}")
```

#### Post-execution Validation

1. Poll **DescribeDisk** until status is `in-use` and `instanceId` matches:
   ```bash
   for i in $(seq 1 24); do
     RESULT=$(jdc --output json disk describe-disk \
       --region-id "{{user.region}}" \
       --disk-id "{{user.disk_id}}")
     STATUS=$(echo "$RESULT" | jq -r '.result.disk.status')
     INSTANCE=$(echo "$RESULT" | jq -r '.result.disk.instanceId')
     [ "$STATUS" = "in-use" ] && [ "$INSTANCE" = "{{user.instance_id}}" ] && break
     sleep 5
   done
   ```
2. Report attachment success and device name to user
3. Remind user to format and mount disk inside VM (use `jdcloud-vm-ops` cloud assistant if needed)

---

### Operation: Detach Disk from VM

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| Disk exists | DescribeDisk | Disk found | HALT |
| Disk attached | `status == "in-use"` | Currently attached | Already detached |
| VM ownership | `disk.instanceId == {{user.instance_id}}` | Correct VM | Verify instance ID |

#### Pre-flight (Safety Gate)

- **MUST** warn user: "Detaching disk while data is being written may cause data corruption. Ensure disk is unmounted inside VM first."
- **MUST** obtain confirmation for force detach scenarios

#### Execution — CLI (Primary Path)

```bash
jdc --output json disk detach-disk \
  --region-id "{{user.region}}" \
  --disk-id "{{user.disk_id}}" \
  --instance-id "{{user.instance_id}}"
```

#### Execution — SDK (Fallback Path)

```python
from jdcloud_sdk.services.disk.apis.detach_disk_request import DetachDiskRequest

req = DetachDiskRequest(
    regionId="{{user.region}}",
    diskId="{{user.disk_id}}",
    instanceId="{{user.instance_id}}"
)
resp = client.detachDisk(req)
print(f"Disk detached: {resp.requestId}")
```

#### Post-execution Validation

1. Poll **DescribeDisk** until status is `available`:
   ```bash
   for i in $(seq 1 24); do
     STATUS=$(jdc --output json disk describe-disk \
       --region-id "{{user.region}}" \
       --disk-id "{{user.disk_id}}" | jq -r '.result.disk.status')
     [ "$STATUS" = "available" ] && break
     sleep 5
   done
   ```
2. Confirm disk is detached and available for reattachment

---

### Operation: Resize Disk

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| Disk exists | DescribeDisk | Disk found | HALT |
| Current size | Parse from describe | Known current size | — |
| New size | User input | New size > current size | Reject; must expand |
| Max size | Check limits (max 32000 GB) | Within limit | Suggest valid size |
| Online resize | Check disk type and status | Supports online resize | May need VM stop |

#### Execution — CLI (Primary Path)

```bash
jdc --output json disk resize-disk \
  --region-id "{{user.region}}" \
  --disk-id "{{user.disk_id}}" \
  --disk-size "{{user.new_disk_size}}"
```

#### Execution — SDK (Fallback Path)

```python
from jdcloud_sdk.services.disk.apis.resize_disk_request import ResizeDiskRequest

req = ResizeDiskRequest(
    regionId="{{user.region}}",
    diskId="{{user.disk_id}}",
    diskSizeGB={{user.new_disk_size}}
)
resp = client.resizeDisk(req)
print(f"Disk resize initiated: {resp.requestId}")
```

#### Post-execution Validation

1. Poll **DescribeDisk** until `diskSizeGB` matches new size:
   ```bash
   for i in $(seq 1 60); do
     SIZE=$(jdc --output json disk describe-disk \
       --region-id "{{user.region}}" \
       --disk-id "{{user.disk_id}}" | jq -r '.result.disk.diskSizeGB')
     [ "$SIZE" = "{{user.new_disk_size}}" ] && break
     sleep 5
   done
   ```
2. Report new disk size
3. Remind user to extend filesystem inside VM for the additional space

---

### Operation: Create Snapshot

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| Disk exists | DescribeDisk | Disk found | HALT |
| Disk status | `in-use` or `available` | Valid for snapshot | Wait for stable state |
| Snapshot name | Validate format | Valid name | Reject invalid |
| Quota | Check snapshot quota | Sufficient quota | HALT |

#### Execution — CLI (Primary Path)

```bash
jdc --output json disk create-snapshot \
  --region-id "{{user.region}}" \
  --disk-id "{{user.disk_id}}" \
  --snapshot-name "{{user.snapshot_name}}" \
  --description "{{user.description|default('Created via skill')}}"
```

#### Execution — SDK (Fallback Path)

```python
from jdcloud_sdk.services.disk.apis.create_snapshot_request import CreateSnapshotRequest

req = CreateSnapshotRequest(
    regionId="{{user.region}}",
    diskId="{{user.disk_id}}",
    name="{{user.snapshot_name}}",
    description="{{user.description|default('Created via skill')}}"
)
resp = client.createSnapshot(req)
print(f"Snapshot created: {resp.result.snapshotId}")
```

#### Post-execution Validation

1. Parse `{{output.snapshot_id}}` from `resp.result.snapshotId`
2. Poll **DescribeSnapshot** until status is `completed`:
   ```bash
   for i in $(seq 1 120); do
     STATUS=$(jdc --output json disk describe-snapshot \
       --region-id "{{user.region}}" \
       --snapshot-id "{{output.snapshot_id}}" | jq -r '.result.snapshot.status')
     [ "$STATUS" = "completed" ] && break
     sleep 5
   done
   ```
3. Report snapshot ID and completion status

---

### Operation: Delete Disk

#### Pre-flight (Safety Gate)

- **MUST** check disk status:
  - If `in-use`: **HALT** and warn user to detach first
  - If snapshots exist: Warn that snapshots may be affected
- **MUST** obtain explicit confirmation: "Delete disk `{{user.disk_name}}` (`{{user.disk_id}}`)? This is irreversible and all data will be lost."
- **MUST NOT** proceed without clear user assent

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| Disk exists | DescribeDisk | Disk found | Already deleted |
| Disk status | `available` or `error` | Can be deleted | Detach first if `in-use` |
| No auto-snapshots | Check policy | Safe to delete | Warn about policy cleanup |

#### Execution — CLI (Primary Path)

```bash
jdc --output json disk delete-disk \
  --region-id "{{user.region}}" \
  --disk-id "{{user.disk_id}}"
```

#### Execution — SDK (Fallback Path)

```python
from jdcloud_sdk.services.disk.apis.delete_disk_request import DeleteDiskRequest

req = DeleteDiskRequest(
    regionId="{{user.region}}",
    diskId="{{user.disk_id}}"
)
resp = client.deleteDisk(req)
print(f"Disk deleted: {resp.requestId}")
```

#### Post-execution Validation

1. Poll **DescribeDisk** or **DescribeDisks** until disk no longer appears:
   ```bash
   for i in $(seq 1 12); do
     RESULT=$(jdc --output json disk describe-disks \
       --region-id "{{user.region}}" \
       --filters "[{'name':'diskId','values':['{{user.disk_id}}']}]")
     COUNT=$(echo "$RESULT" | jq '.result.disks | length')
     [ "$COUNT" = "0" ] && break
     sleep 5
   done
   ```
2. Confirm deletion to user

#### Failure Recovery

| Error pattern | Max retries | Backoff | Agent Action |
|---------------|-------------|---------|--------------|
| `DiskInUse` | 0 | — | HALT; user must detach first |
| `InvalidDiskStatus` | 0 | — | Wait for status transition |
| `SnapshotInProgress` | 3 | 10s | Wait for snapshot completion |
| Throttling / 429 | 3 | exponential | Back off and retry |

---

### Operation: Restore Disk from Snapshot

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| Snapshot exists | DescribeSnapshot | Snapshot found | HALT |
| Snapshot status | `completed` | Ready for restore | Wait if `creating` |
| Original disk | If restoring in-place | Disk exists | May create new disk |

#### Pre-flight (Safety Gate)

- **MUST** warn user: "Restoring from snapshot will overwrite current disk data with snapshot data. This is irreversible."
- **MUST** obtain explicit confirmation for in-place restore

#### Execution — CLI (Primary Path)

```bash
# Create new disk from snapshot
jdc --output json disk create-disks \
  --region-id "{{user.region}}" \
  --az "{{user.az}}" \
  --snapshot-id "{{user.snapshot_id}}" \
  --disk-name "{{user.new_disk_name}}" \
  --charge-mode "postpaid_by_usage"
```

#### Post-execution Validation

1. Monitor disk creation until `available`
2. If replacing existing disk, follow: create → detach old → attach new → delete old flow

## Prerequisites

> **Python 3.10 is REQUIRED, NOT 3.12.** `jdcloud_cli==1.2.12` uses `SafeConfigParser` which was removed in Python 3.12.

1. **Install uv** (system-wide, one-time):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   # or: brew install uv
   ```

2. **Bootstrap Python environment**:
   ```bash
   uv venv --python 3.10
   source .venv/bin/activate
   uv pip install jdcloud_cli jdcloud_sdk
   ```

3. **Configure Credentials for CLI** (`~/.jdc/config`):
   ```bash
   export HOME=/tmp/jdc-home
   mkdir -p /tmp/jdc-home/.jdc
   cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
   [default]
   access_key = {{env.JDC_ACCESS_KEY}}
   secret_key = {{env.JDC_SECRET_KEY}}
   region_id = cn-north-1
   endpoint = disk.jdcloud-api.com
   scheme = https
   timeout = 20
   CONFIGEOF
   printf "%s" "default" > /tmp/jdc-home/.jdc/current
   ```

4. **Verify Configuration**:
   ```bash
   # CLI verification
   jdc --output json disk describe-disks --region-id cn-north-1 --page-size 1

   # SDK verification
   python -c "
   import os
   from jdcloud_sdk.core.credential import Credential
   credential = Credential(os.environ['JDC_ACCESS_KEY'], os.environ['JDC_SECRET_KEY'])
   print('SDK credentials OK')
   "
   ```

## Reference Directory

- [Core Concepts](references/core-concepts.md)
- [API & SDK Usage](references/api-sdk-usage.md)
- [CLI Usage](references/cli-usage.md)
- [Troubleshooting Guide](references/troubleshooting.md)
- [Integration](references/integration.md)

## Operational Best Practices

- **Data safety**: Always create snapshot before major changes or disk resize
- **Detach before delete**: Never delete `in-use` disks; always detach first
- **Filesystem extension**: After disk resize, extend filesystem inside VM to use new capacity
- **Snapshot scheduling**: Use automated backup policies for critical data disks
- **Cross-AZ resilience**: Create disks in same AZ as target VM; use snapshot+copy for cross-AZ
- **Cost optimization**: Delete unused disks and old snapshots; use appropriate disk type (SSD vs HDD)

## Quality Gate (GCL)

> This skill participates in the repository-wide **Generator-Critic-Loop**
> (GCL) defined in [`AGENTS.md`](../AGENTS.md#generator-critic-loop-gcl--adversarial-quality-gate).

### Parameters

| Parameter | Value | Reason |
|---|---|---|
| `max_iterations` | **3** | `AGENTS.md` §8 default for disk ops (recommended) |
| `rubric_version` | `v1` | see [references/rubric.md](references/rubric.md) |
| `trace_path` | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | unified with `jdcloud-audit-ops` |
| `safety_confirm_required` | **true** | Delete disk requires user confirmation |

### Rubric Dimensions

| Dimension | Threshold | Notes |
|-----------|-----------|-------|
| Correctness | ≥ 0.5 | Disk ID/state matches request |
| Safety | = 1 | Delete/restore confirmed; no in-use deletion |
| Idempotency | ≥ 0.5 | Create with same name returns error consistently |
| Traceability | ≥ 0.5 | All jdc/SDK calls logged with request IDs |
| Spec Compliance | ≥ 0.5 | Follows Disk API conventions |

---

