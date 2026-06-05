# PostgreSQL Ops Rubric (GCL)

> Concrete instantiation of the **Generator-Critic-Loop** rubric defined in
> `AGENTS.md` §3 for `jdcloud-postgresql-ops`. This file is the single source
> of truth for what the Critic scores against.

## Rubric version

`v1` — see `AGENTS.md` §11.

## Dimensions

| # | Dimension | Weight | Threshold | Scale | Notes |
|---|---|---|---|---|---|
| 1 | **Correctness** | hard | ≥ 0.5; **= 1.0 required** for `delete-instance`, `restore-instance`, DDL (`DROP`/`ALTER`/`TRUNCATE`), DML (`DELETE`/`UPDATE` without WHERE) | 0 / 0.5 / 1 | Verifies `instanceId`, region, engine version, instance class, storage GB, and vpc/subnet match the user request. Read back via `describe-instances` and compare. For DDL/DML: read back via `pg_catalog` queries (`\dt`, `SELECT count(*)`) and compare. |
| 2 | **Safety** | hard | = 1 | 0 / 1 | Destructive ops (`delete-instance`, `restore-instance`, `DROP TABLE`, `DROP SCHEMA`, `TRUNCATE`, `DELETE`/`UPDATE` without WHERE) MUST have explicit user confirmation captured in trace. For DDL/DML: SQL text MUST appear in the trace verbatim. |
| 3 | **Idempotency** | soft | ≥ 0.5 | 0 / 0.5 / 1 | `create-instance` must use a stable `client-token`; `delete`/`restore` are state-machine-guarded. Score 0 if no idempotency key on a `create` flow. For DDL: `CREATE TABLE IF NOT EXISTS` is preferred. |
| 4 | **Traceability** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Trace MUST contain: full `jdc` command (or SDK call) or **full SQL text**, args, exit code, raw response excerpt (≤ 2 KB), and final `describe-instances` or catalog snapshot. Score 1 only if all four present. |
| 5 | **Spec Compliance** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Conforms to `core-concepts.md`: engine version supported in region, instance class SKU valid, storage GB within quota, AZ valid, port 5432 (or user-specified). |

## Operation-specific overrides

| Operation | Required dimensions = 1.0 | Notes |
|---|---|---|
| `create-instance` | Correctness, Safety, **Idempotency** | Must set `client-token` (UUID v4 if user did not supply one) |
| `describe-instance` / `list` | Correctness, Traceability | Safety & Idempotency are N/A; score 1.0 by default |
| `describe-slow-logs` | Correctness, Traceability | Read-only query; Safety = 1.0 by default. Must validate `startTime` and `endTime` are within 7-day window |
| `modify-instance` (config: name, password reset, params) | Correctness, Safety | Hot-apply may cause brief reconnect — flag in trace |
| `modify-instance` (spec: class, storage) | Correctness, Safety, **Spec Compliance** | Storage shrink is **forbidden** — Safety = 0 if shrinking without explicit opt-in |
| `delete-instance` | Correctness, Safety, **Traceability** | Must include pre-delete snapshot (instance id + status + WAL LSN) |
| `create-backup` | Correctness, Traceability | Backup id must be echoed back in trace |
| `restore-instance` | Correctness, **Safety**, Spec Compliance | `backupId` must be a real, recent backup owned by the same instance; cross-instance restore requires explicit confirm |
| DDL `CREATE TABLE` / `CREATE INDEX` | Correctness, **Idempotency**, Traceability | Prefer `IF NOT EXISTS`; full DDL must appear in trace |
| DDL `DROP TABLE` / `DROP SCHEMA` | Correctness, **Safety**, Traceability | ALWAYS Safety = 0 without explicit `confirm=DROP` in trace → ABORT. `DROP SCHEMA` cascades to all objects — extra caution |
| DDL `ALTER TABLE` (add column / change column) | Correctness, Safety, Traceability | For PG 10+ prefer `ADD COLUMN ... DEFAULT` (non-blocking); full ALTER must appear in trace |
| DDL `TRUNCATE TABLE` | Correctness, **Safety**, Traceability | ALWAYS Safety = 0 without explicit `confirm=TRUNCATE` in trace → ABORT. `TRUNCATE ... RESTART IDENTITY` resets sequences — extra caution |
| DDL `VACUUM` / `ANALYZE` (maintenance) | Correctness, Traceability | Read-only maintenance; Safety = 1 by default. `VACUUM FULL` is destructive (rewrites table) → Safety = 0 without `confirm=VACUUM_FULL` |
| DML `INSERT` | Correctness, Traceability | `INSERT ... ON CONFLICT (col) DO UPDATE` preferred for idempotency |
| DML `UPDATE` | Correctness, **Safety**, Traceability | **MUST have WHERE clause**. Safety = 0 if no WHERE → ABORT |
| DML `DELETE` | Correctness, **Safety**, Traceability | **MUST have WHERE clause**. Safety = 0 if no WHERE → ABORT |
| DML `SELECT` | Correctness, Traceability | Read-only; Safety = 1 by default. **EXCEPTION**: if SELECT text contains `FOR UPDATE`, `FOR NO KEY UPDATE`, `FOR SHARE`, or `INTO OUTFILE` → Safety must be re-scored; missing user confirm → Safety = 0 |

## Safety special cases (auto-fail)

- Delete / restore on an instance tagged `env=prod` **without** an explicit
  `confirm=DELETE` or `confirm=RESTORE` in the trace → **Safety = 0 → ABORT**
- Restore from a backup that belongs to a **different** instance without
  explicit cross-instance confirmation → **Safety = 0 → ABORT**
- Storage shrink (GB decreased) without explicit user opt-in → **Safety = 0 → ABORT**
- `DROP TABLE` / `DROP SCHEMA` / `TRUNCATE` / `VACUUM FULL` without
  `confirm=*` in trace → **Safety = 0 → ABORT**
- `UPDATE` / `DELETE` SQL text missing a `WHERE` clause → **Safety = 0 → ABORT**
- Any operation targeting an `instanceId` that was not echoed back from a
  `describe-instances` lookup → **Correctness = 0 → ABORT**
- DDL/DML against a `schema` or `table` that was not echoed back from a
  catalog lookup (`pg_catalog.pg_tables`, `pg_catalog.pg_namespace`) →
  **Correctness = 0 → ABORT**

## DDL/DML execution path

The `jdc` CLI does **not** currently expose `exec-sql`. DDL/DML is performed
via the SDK low-level `psycopg2` / `psycopg` path. This is an
**explicitly non-CLI** path:

- Always prefer a read-only pre-check first (e.g., `SELECT count(*) FROM
  pg_tables WHERE schemaname=...`, `SELECT count(*) FROM <table>`) and
  include the result in the trace.
- Wrap the mutating SQL in a transaction; capture `rowcount` (cursor.rowcount)
  and PG `WARNING` messages.
- For destructive SQL, additionally `pg_dump` the affected table **before**
  executing (via SDK subprocess).
- For DDL on large tables in production, prefer `pg_repack` or built-in online
  DDL where applicable (PG 11+ `ALTER TABLE ... ADD COLUMN ... DEFAULT`).

## Loop parameters

| Parameter | Value | Source |
|---|---|---|
| `max_iterations` | **2** | `AGENTS.md` §8 default for `jdcloud-postgresql-ops` |
| Trace path | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | `AGENTS.md` §6 |
| Rubric version | `v1` | this file |

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-06-04 | Initial rubric for `jdcloud-postgresql-ops` GCL rollout (covers instance + DDL/DML paths; PG-specific rules for `VACUUM FULL`, `DROP SCHEMA`, sequence reset) |
