# Elasticsearch Ops Rubric (GCL)

> Concrete instantiation of the **Generator-Critic-Loop** rubric defined in
> `AGENTS.md` §3 for `jdcloud-elasticsearch-ops`. This file is the single
> source of truth for what the Critic scores against.

## Rubric version

`v1` — see `AGENTS.md` §11.

## Dimensions

| # | Dimension | Weight | Threshold | Scale | Notes |
|---|---|---|---|---|---|
| 1 | **Correctness** | hard | ≥ 0.5; **= 1.0 required** for `delete-instance`, `delete-index`, `delete-by-query` without query, `forcemerge` | 0 / 0.5 / 1 | Verifies `instanceId`, region, ES version, instance class (e.g., `es.s2.medium`), node count, storage GB, and vpc/subnet match the user request. Read back via `describe-instances` and `GET _cluster/health` and compare. For index ops: read back via `GET _cat/indices` and compare. |
| 2 | **Safety** | hard | = 1 | 0 / 1 | Destructive ops (`delete-instance`, `delete-index`, `close-index`, `delete-by-query` without query, `forcemerge` with `max_num_segments=1`, snapshot deletion) MUST have explicit user confirmation captured in trace. For ES ops: full URL + JSON body MUST appear in trace verbatim. |
| 3 | **Idempotency** | soft | ≥ 0.5 | 0 / 0.5 / 1 | `create-instance` must use a stable `client-token`; `delete` is state-machine-guarded. Score 0 if no idempotency key on a `create` flow. For ES index ops: `PUT /<index>` with same name + same settings is idempotent; `delete-index` should check existence first via `HEAD /<index>`. |
| 4 | **Traceability** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Trace MUST contain: full `jdc` command (or SDK call) or **full HTTP method + URL + body**, args, exit code, raw response excerpt (≤ 2 KB), and final `describe-instances` or `GET _cat/indices` snapshot. Score 1 only if all four present. |
| 5 | **Spec Compliance** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Conforms to `core-concepts.md`: ES version supported in region, instance class SKU valid, storage GB within quota, AZ valid, port 9200 (or user-specified), security enabled (HTTPS) and auth required. |

## Operation-specific overrides

| Operation | Required dimensions = 1.0 | Notes |
|---|---|---|
| `create-instance` | Correctness, Safety, **Idempotency** | Must set `client-token` (UUID v4 if user did not supply one) |
| `describe-instance` / `list` / `GET _cluster/health` | Correctness, Traceability | Safety & Idempotency are N/A; score 1.0 by default |
| `modify-instance` (config: name, password) | Correctness, Safety | Hot-apply may cause brief reconnect — flag in trace |
| `modify-instance` (spec: class, node count, storage) | Correctness, Safety, **Spec Compliance** | Node count shrink and storage shrink are **forbidden** — Safety = 0 without explicit opt-in |
| `delete-instance` | Correctness, Safety, **Traceability** | Must include pre-delete snapshot (instance id + status + cluster health) |
| `create-backup` (snapshot) | Correctness, Traceability | Snapshot id must be echoed back in trace |
| `restore-instance` | Correctness, **Safety**, Spec Compliance | `snapshotId` must be a real, recent snapshot owned by the same instance; cross-instance restore requires explicit confirm |
| ES `POST /<index>/_create/<id>` (index doc) | Correctness, Traceability | Captures `result: created` vs `updated` |
| ES `PUT /<index>` (create index) | Correctness, **Idempotency**, Traceability | Full settings + mappings in body must appear in trace |
| ES `DELETE /<index>` (delete index) | Correctness, **Safety**, Traceability | ALWAYS Safety = 0 without explicit `confirm=DELETE_INDEX` in trace → ABORT. `wildcard_delete` (e.g., `logs-*`) is **especially dangerous** — additional `confirm=DELETE_WILDCARD_INDEX` required |
| ES `POST /<index>/_close` | Correctness, **Safety**, Traceability | Closes index (blocks reads/writes); Safety = 0 without `confirm=CLOSE` → ABORT |
| ES `POST /<index>/_update/<id>` | Correctness, **Safety**, Traceability | Partial update; if `script` is inline and mutating, capture in trace |
| ES `POST /<index>/_update_by_query` | Correctness, **Safety**, Traceability | **MUST have non-empty query**. Safety = 0 if `query: {}` or `match_all` only without additional filter → ABORT. Prefer `?conflicts=proceed&scroll_size=1000&wait_for_completion=false` for large ops |
| ES `POST /<index>/_delete_by_query` | Correctness, **Safety**, Traceability | **MUST have non-empty query**. Safety = 0 if `query: {}` or `match_all` only without additional filter → ABORT. ALWAYS snapshot the index first |
| ES `POST /<index>/_search` | Correctness, Traceability | Read-only; Safety = 1 by default. **EXCEPTION**: if body includes `terminate_after: 0` or other abuse patterns → re-score Safety |
| ES `POST /_reindex` | Correctness, **Safety**, Traceability | Cross-index op; `source` and `dest` must be echoed; Safety = 0 if `dest` index is `logs-*` wildcard or production without opt-in |
| ES `POST /<index>/_forcemerge` | Correctness, **Safety**, Traceability | `max_num_segments=1` is destructive (large IO); Safety = 0 without `confirm=FORCEMERGE` → ABORT |
| ES `PUT /_snapshot/<repo>/<snap>` (create snapshot) | Correctness, Traceability | Repo and snapshot name must be echoed |
| ES `DELETE /_snapshot/<repo>/<snap>` (delete snapshot) | Correctness, **Safety**, Traceability | Safety = 0 without `confirm=DELETE_SNAPSHOT` → ABORT |
| ES `PUT /_ilm/policy/<name>` (ILM policy) | Correctness, **Safety**, Traceability | Affects index lifecycle; Safety = 0 if `delete` action included without opt-in |

## Safety special cases (auto-fail)

- Delete / restore on an instance tagged `env=prod` **without** an explicit
  `confirm=DELETE` or `confirm=RESTORE` in the trace → **Safety = 0 → ABORT**
- Restore from a snapshot that belongs to a **different** instance without
  explicit cross-instance confirmation → **Safety = 0 → ABORT**
- Node count or storage shrink without explicit user opt-in → **Safety = 0 → ABORT**
- `DELETE /<index>` (especially wildcard) / `_close` / `_delete_by_query` /
  `_forcemerge` / snapshot deletion without `confirm=*` in trace →
  **Safety = 0 → ABORT**
- `_update_by_query` / `_delete_by_query` whose query is `{}`, `match_all`,
  or missing → **Safety = 0 → ABORT**
- Any operation targeting an `instanceId` that was not echoed back from a
  `describe-instances` lookup → **Correctness = 0 → ABORT**
- ES ops against an `index` that was not echoed back from a
  `GET _cat/indices` lookup → **Correctness = 0 → ABORT**

## ES execution path

The `jdc` CLI does **not** currently expose `exec-es-command`. ES ops are
performed via the SDK low-level `elasticsearch-py` / raw HTTPS path. This is
an **explicitly non-CLI** path:

- Always prefer a read-only pre-check first (e.g., `GET _cat/indices?v`,
  `GET _cluster/health`, `GET /<index>/_count`) and include the result in
  the trace.
- For mutating ops, capture full HTTP method + URL + body in the trace.
- For destructive ops (`DELETE /<index>`, `_delete_by_query`, `_forcemerge`),
  create a snapshot **before** executing (via `PUT /_snapshot/...`).
- For `_update_by_query` / `_delete_by_query` on large indices, use
  `wait_for_completion=false` and poll task status; capture task id in trace.

## Loop parameters

| Parameter | Value | Source |
|---|---|---|
| `max_iterations` | **2** | `AGENTS.md` §8 default for `jdcloud-elasticsearch-ops` |
| Trace path | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | `AGENTS.md` §6 |
| Rubric version | `v1` | this file |

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-06-04 | Initial rubric for `jdcloud-elasticsearch-ops` GCL rollout (covers instance + ES REST paths; ES-specific rules for wildcard delete, `match_all` queries in update/delete-by-query, `_forcemerge max_num_segments=1`) |
