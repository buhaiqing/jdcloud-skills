# MongoDB Ops Rubric (GCL)

> Concrete instantiation of the **Generator-Critic-Loop** rubric defined in
> `AGENTS.md` §3 for `jdcloud-mongodb-ops`. This file is the single source of
> truth for what the Critic scores against.

## Rubric version

`v1` — see `AGENTS.md` §11.

## Dimensions

| # | Dimension | Weight | Threshold | Scale | Notes |
|---|---|---|---|---|---|
| 1 | **Correctness** | hard | ≥ 0.5; **= 1.0 required** for `delete-instance`, `restore-instance`, `dropDatabase`, `dropCollection`, `deleteMany` without filter | 0 / 0.5 / 1 | Verifies `instanceId`, region, engine version (MongoDB version), instance class, storage GB, and vpc/subnet match the user request. Read back via `describe-instances` and compare. For DB ops: read back via `show collections`, `db.collection.countDocuments()` and compare. |
| 2 | **Safety** | hard | = 1 | 0 / 1 | Destructive ops (`delete-instance`, `restore-instance`, `dropDatabase`, `dropCollection`, `deleteMany`/`updateMany` without filter, `remove` without filter) MUST have explicit user confirmation captured in trace. For DB ops: full command (BSON/JSON) MUST appear in the trace verbatim. |
| 3 | **Idempotency** | soft | ≥ 0.5 | 0 / 0.5 / 1 | `create-instance` must use a stable `client-token`; `delete`/`restore` are state-machine-guarded. Score 0 if no idempotency key on a `create` flow. For DB ops: `createCollection` is idempotent; `dropCollection` should check existence first. |
| 4 | **Traceability** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Trace MUST contain: full `jdc` command (or SDK call) or **full DB command**, args, exit code, raw response excerpt (≤ 2 KB), and final `describe-instances` or `show collections` snapshot. Score 1 only if all four present. |
| 5 | **Spec Compliance** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Conforms to `core-concepts.md`: MongoDB version supported, instance class SKU valid, storage GB within quota, AZ valid, port 27017 (or user-specified), auth DB valid. |

## Operation-specific overrides

| Operation | Required dimensions = 1.0 | Notes |
|---|---|---|
| `create-instance` | Correctness, Safety, **Idempotency** | Must set `client-token` (UUID v4 if user did not supply one) |
| `describe-instance` / `list` | Correctness, Traceability | Safety & Idempotency are N/A; score 1.0 by default |
| `modify-instance` (config: name, password reset) | Correctness, Safety | Hot-apply may cause brief reconnect — flag in trace |
| `modify-instance` (spec: class, storage) | Correctness, Safety, **Spec Compliance** | Storage shrink is **forbidden** — Safety = 0 if shrinking without explicit opt-in |
| `delete-instance` | Correctness, Safety, **Traceability** | Must include pre-delete snapshot (instance id + status + oplog position) |
| `create-backup` | Correctness, Traceability | Backup id must be echoed back in trace |
| `restore-instance` | Correctness, **Safety**, Spec Compliance | `backupId` must be a real, recent backup owned by the same instance; cross-instance restore requires explicit confirm |
| DB `createCollection` | Correctness, **Idempotency**, Traceability | Prefer explicit name; full command must appear in trace |
| DB `dropCollection` / `dropDatabase` | Correctness, **Safety**, Traceability | ALWAYS Safety = 0 without explicit `confirm=DROP` in trace → ABORT. `dropDatabase` cascades to ALL collections — extra caution |
| DB `insertOne` / `insertMany` | Correctness, Traceability | `insertMany` with `ordered: false` preferred for batch |
| DB `updateOne` / `updateMany` | Correctness, **Safety**, Traceability | **MUST have filter**. Safety = 0 if `{}` or missing filter → ABORT. Capture `modifiedCount` and `matchedCount` |
| DB `deleteOne` / `deleteMany` / `remove` | Correctness, **Safety**, Traceability | **MUST have filter**. Safety = 0 if `{}` or missing filter → ABORT. Capture `deletedCount` |
| DB `find` | Correctness, Traceability | Read-only; Safety = 1 by default. **EXCEPTION**: if `find` includes `$out`, `$merge`, or `$lookup` to a write target → re-score Safety |
| DB `aggregate` | Correctness, **Safety**, Traceability | If pipeline includes `$out`, `$merge` → re-score Safety. `allowDiskUse: true` requires user opt-in |
| DB `createIndex` | Correctness, **Idempotency**, Traceability | Idempotent by default; but unique index on existing dup data will fail — pre-check via `getIndexes()` |
| Admin `shutdown` / `fsyncLock` / `repairDatabase` | Correctness, **Safety**, Traceability | All block clients; `confirm=SHUTDOWN`/`confirm=LOCK`/`confirm=REPAIR` required in trace → ABORT otherwise |
| Admin `replSetReconfig` | Correctness, **Safety**, Traceability | Affects HA; Safety = 0 without `confirm=RECONFIG` in trace → ABORT |

## Safety special cases (auto-fail)

- Delete / restore on an instance tagged `env=prod` **without** an explicit
  `confirm=DELETE` or `confirm=RESTORE` in the trace → **Safety = 0 → ABORT**
- Restore from a backup that belongs to a **different** instance without
  explicit cross-instance confirmation → **Safety = 0 → ABORT**
- Storage shrink (GB decreased) without explicit user opt-in → **Safety = 0 → ABORT**
- `dropCollection` / `dropDatabase` / `shutdown` / `fsyncLock` / `repairDatabase`
  / `replSetReconfig` without `confirm=*` in trace → **Safety = 0 → ABORT**
- `updateOne` / `updateMany` / `deleteOne` / `deleteMany` / `remove` whose
  filter is `{}`, empty, or missing → **Safety = 0 → ABORT**
- Any operation targeting an `instanceId` that was not echoed back from a
  `describe-instances` lookup → **Correctness = 0 → ABORT**
- DB ops against a `database` or `collection` that was not echoed back from
  a `show dbs` / `show collections` lookup → **Correctness = 0 → ABORT**

## DB execution path

The `jdc` CLI does **not** currently expose MongoDB `exec-command`. DB ops
are performed via the SDK low-level `pymongo` path. This is an
**explicitly non-CLI** path:

- Always prefer a read-only pre-check first (e.g., `show collections`,
  `db.<col>.countDocuments(filter)`, `db.getMongo().getDBs()`) and include
  the result in the trace.
- Wrap mutating ops in a session (`client.start_session()`) for transaction
  support (requires replica set); capture `acknowledged`, `matched_count`,
  `modified_count`, `deleted_count`, `inserted_count` as appropriate.
- For destructive ops, additionally `mongodump` the affected database
  **before** executing (via SDK subprocess).
- For `allowDiskUse: true` or `writeConcern: { w: 0 }` operations, capture
  user opt-in in trace.

## Loop parameters

| Parameter | Value | Source |
|---|---|---|
| `max_iterations` | **2** | `AGENTS.md` §8 default for `jdcloud-mongodb-ops` |
| Trace path | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | `AGENTS.md` §6 |
| Rubric version | `v1` | this file |

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-06-04 | Initial rubric for `jdcloud-mongodb-ops` GCL rollout (covers instance + DB-level paths; MongoDB-specific rules for `dropDatabase` cascade, `updateMany` filter check, `$out`/`$merge` in aggregate) |
