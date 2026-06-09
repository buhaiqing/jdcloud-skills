# LogService Ops Rubric (GCL)

> Concrete instantiation of the **Generator-Critic-Loop** rubric defined in
> `AGENTS.md` §3 for `jdcloud-logservice-ops`. This file is the single source
> of truth for what the Critic scores against.

## Rubric version

`v1` — see `AGENTS.md` §11.

## Dimensions

| # | Dimension | Weight | Threshold | Scale | Notes |
|---|---|---|---|---|---|
| 1 | **Correctness** | hard | ≥ 0.5; **= 1.0 required** for `delete logset`, `delete logtopic` | 0 / 0.5 / 1 | Verifies `logsetUID` / `logtopicUID` match request. Read back via `describe-*` and compare. |
| 2 | **Safety** | hard | = 1 | 0 / 1 | Destructive ops (`delete logset`, `delete logtopic`) MUST have explicit user confirmation. LogSet deletion cascade-deletes LogTopics. |
| 3 | **Idempotency** | soft | ≥ 0.5 | 0 / 0.5 / 1 | `create logset` / `create logtopic` with same name should check for duplicates. `search` is naturally idempotent. |
| 4 | **Traceability** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Trace MUST contain: full SDK call, args, response excerpt, and final `describe-*` snapshot. |
| 5 | **Spec Compliance** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Conforms to `core-concepts.md`: retention in [1, 3650], name length ≤ 128, query syntax valid, collection type supported. |

## Operation-specific overrides

| Operation | Required dimensions = 1.0 | Notes |
|---|---|---|
| `create logset` | Correctness, Safety, Spec Compliance | Retention must be ≥ 1 and ≤ 3650; name unique |
| `describe logset` / `describe logsets` | Correctness, Traceability | Safety & Idempotency N/A; score 1.0 by default |
| `update logset` | Correctness, Safety, Spec Compliance | Retention decrease warns about data loss |
| `delete logset` | Correctness, Safety, Traceability | **Cascade deletes all LogTopics**. Must check empty or confirm cascade |
| `create logtopic` | Correctness, Safety, Spec Compliance | LogSet must exist; collection type valid |
| `describe logtopic` / `describe logtopics` | Correctness, Traceability | Safety & Idempotency N/A; score 1.0 by default |
| `update logtopic` | Correctness, Safety, Spec Compliance | Collection info change may disrupt ingestion |
| `delete logtopic` | Correctness, Safety, Traceability | **Permanently deletes all logs**. Require confirm |
| `search log` | Correctness, Traceability | Query syntax valid; time range within retention |
| `describe index` / `update index` | Correctness, Spec Compliance | Field types must be in supported list |

## Safety special cases (auto-fail)

- `delete logset` without explicit confirmation → **Safety = 0 → ABORT**
- `delete logset` without checking for contained LogTopics first → **Safety = 0 → ABORT**
- `delete logset` on a LogSet tagged `env=prod` without `confirm=DELETE_PROD` → **Safety = 0 → ABORT**
- `delete logtopic` without explicit user confirmation → **Safety = 0 → ABORT**
- `delete logtopic` on a production LogTopic without `confirm=DELETE_PROD` → **Safety = 0 → ABORT**
- `update logset` with `retention` decrease that drops logs < 1 hour old without warning → **Safety = 0 → ABORT**
- `search log` with hardcoded credentials in query string → **Safety = 0 → ABORT**
- `create logtopic` with `collectionInfo.type` not in supported list → **Spec Compliance = 0**
- `create logset` with `retention` < 1 or > 3650 → **Spec Compliance = 0**

## Loop parameters

| Parameter | Value | Source |
|---|---|---|
| `max_iterations` | **3** | `AGENTS.md` §8 default for `jdcloud-logservice-ops` (recommended) |
| Trace path | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | `AGENTS.md` §6 |
| Rubric version | `v1` | this file |

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-06-08 | Initial rubric for `jdcloud-logservice-ops` GCL rollout (covers LogSet, LogTopic, Search, Index) |
