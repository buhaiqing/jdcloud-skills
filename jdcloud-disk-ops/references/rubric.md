# Disk Ops Rubric (GCL)

> Concrete instantiation of the **Generator-Critic-Loop** rubric defined in
> `AGENTS.md` §3 for `jdcloud-disk-ops`. This file is the single source of
> truth for what the Critic scores against.

## Rubric version

`v1` — see `AGENTS.md` §11.

## Dimensions

| # | Dimension | Weight | Threshold | Scale | Notes |
|---|---|---|---|---|---|
| 1 | **Correctness** | hard | ≥ 0.5; **= 1.0 required** for `delete disk`, `delete snapshot` | 0 / 0.5 / 1 | Verifies `diskId` / `snapshotId` matches request. Read back via `describe-disk` and compare status. |
| 2 | **Safety** | hard | = 1 | 0 / 1 | Destructive ops (`delete disk`, `delete snapshot`, `detach in-use disk`) MUST have explicit user confirmation. |
| 3 | **Idempotency** | soft | ≥ 0.5 | 0 / 0.5 / 1 | `create disks` with same name/size/AZ should check for duplicates. `resize` is idempotent (only expand allowed). |
| 4 | **Traceability** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Trace MUST contain: full jdc command (or SDK call), args, exit code, raw response excerpt, and final `describe-disk` snapshot. |
| 5 | **Spec Compliance** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Conforms to `core-concepts.md`: disk type supported, size constraints (min 20GB SSD), AZ exists, snapshot source verified. |

## Operation-specific overrides

| Operation | Required dimensions = 1.0 | Notes |
|---|---|---|
| `create disks` | Correctness, Safety, Spec Compliance | DiskType must be [ssd, premium-hdd, standard-hdd]; size >= 20GB |
| `describe disk` / `list disks` | Correctness, Traceability | Safety & Idempotency N/A; score 1.0 by default |
| `attach disk` | Correctness, Safety, Spec Compliance | Disk must be `available`; VM instance must exist in same AZ |
| `detach disk` | Correctness, Safety, Traceability | **Data corruption risk** if filesystem not unmounted first; require confirm |
| `resize disk` | Correctness, Safety, Spec Compliance | Only expand (not shrink); max size varies by type |
| `create snapshot` | Correctness, Safety, Traceability | Disk must not be in `deleting` state |
| `delete snapshot` | Correctness, Safety, Traceability | Irreversible; check if snapshot is source for other disks |
| `restore disk` (create from snapshot) | Correctness, Safety, Spec Compliance | New disk size >= source snapshot size |
| `delete disk` | Correctness, Safety, Traceability | **Data loss risk**. Disk must be `available`. Check if any snapshots reference it. Require `confirm=DELETE` |

## Safety special cases (auto-fail)

- `delete disk` on a disk tagged `env=prod` without `confirm=DELETE_PROD` → **Safety = 0 → ABORT**
- `detach disk` that is an OS system disk → **Safety = 0 → ABORT** (system disks cannot be detached)
- `detach disk` with no warning about filesystem mount → **Safety = 0 → ABORT**
- `delete disk` without checking status == `available` first → **Safety = 0 → ABORT**
- `delete snapshot` that is the only restore point for a running VM → **Safety = 0 → ABORT**
- `resize disk` attempting to shrink (set smaller size) → **Spec Compliance = 0**
- `attach disk` to a VM in a different AZ → **Correctness = 0 → ABORT**

## Loop parameters

| Parameter | Value | Source |
|---|---|---|
| `max_iterations` | **2** | `AGENTS.md` §8 default for `jdcloud-disk-ops` (required) |
| Trace path | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | `AGENTS.md` §6 |
| Rubric version | `v1` | this file |

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-06-08 | Initial rubric for `jdcloud-disk-ops` GCL rollout (covers disk CRUD, attach/detach, resize, snapshot, restore) |