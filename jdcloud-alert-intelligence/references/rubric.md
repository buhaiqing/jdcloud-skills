# Alert Intelligence Rubric (GCL)

> Concrete instantiation of the **Generator-Critic-Loop** rubric defined in
> `AGENTS.md` §3 for `jdcloud-alert-intelligence`. This skill is **read-only**
> (analyzes alerts but never mutates them) per its **核心约束** section.

## Rubric version

`v1` — see `AGENTS.md` §11.

## Dimensions

| # | Dimension | Weight | Threshold | Scale | Notes |
|---|---|---|---|---|---|
| 1 | **Correctness** | hard | ≥ 0.5; **= 1.0 required** for severity classification, suppression rule application | 0 / 0.5 / 1 | Verifies the aggregation key `(service, resource, metric)` is fully populated for every cluster. Verifies severity matrix lookup matches the actual metric behavior. |
| 2 | **Safety** | hard | = 1 | 0 / 1 | **Read-only by definition**. Safety = 0 if the report recommends `delete` / `disable` / `modify` on an alert rule (that's `jdcloud-cloudmonitor-ops`'s job). Also: Safety = 0 if any `.env` value, secret, or PII appears in the report. |
| 3 | **Idempotency** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Re-running the same alert intelligence analysis on the same input should produce the same severity classification. Different (newer) input → different result is OK. |
| 4 | **Traceability** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Every severity classification MUST cite the metric value, threshold, time window, and the source `jdc monitor` query. Score 1 only if every cluster has a 4-tuple citation. |
| 5 | **Spec Compliance** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Conforms to `severity-matrix.md` and `suppression-rules.md`. Every suppression applied MUST cite the matching rule. |

## Operation-specific overrides

This skill does not have a `### Operation:` structure; it has a 5-step
**工作流** (workflow). Each step is scored separately:

| Workflow step | Required dimensions = 1.0 | Notes |
|---|---|---|
| 1. 加载时间窗告警 | Correctness, Traceability | Time window MUST be explicit; default 24h; max 15d (per 核心约束) |
| 2. 聚合 (aggregate) | Correctness, Spec Compliance | Aggregation key `(service, resource, metric)` MUST be complete; cluster count = number of unique triples |
| 3. 分级 (classify) | Correctness, Traceability | Each cluster gets P0-P3 per `severity-matrix.md`; cite metric value + threshold + window for every classification |
| 4. 抑制 (suppress) | Spec Compliance | Every suppression MUST cite the matching rule in `suppression-rules.md`; never silently drop a cluster |
| 5. 报告输出 (report) | Correctness, Safety, Traceability | Report MUST include 下一跳建议 (next-hop suggestion) for every P0/P1 cluster pointing to a specific `jdcloud-*-ops` skill |

## Safety special cases (auto-fail)

- Report recommends `delete` / `disable` / `modify` an alert rule
  → **Safety = 0 → ABORT** (this skill is read-only by mandate)
- Any `.env` value, secret key, access-key id, or PII appears in the report
  → **Safety = 0 → ABORT**
- A P0/P1 cluster has no 下一跳建议 → **Traceability = 0 → ABORT**
- Severity classification made without citing the threshold + time window
  → **Traceability = 0 → ABORT**
- Aggregation dropped a cluster without a cited suppression rule
  → **Correctness = 0 → ABORT**
- Time window > 15d → **Spec Compliance = 0 → ABORT** (raw data retention limit)

## Loop parameters

| Parameter | Value | Source |
|---|---|---|
| `max_iterations` | **5** | `AGENTS.md` §8 default for `jdcloud-alert-intelligence` (optional, read-only) |
| Trace path | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | `AGENTS.md` §6 |
| Rubric version | `v1` | this file |

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-06-04 | Initial rubric for `jdcloud-alert-intelligence` GCL rollout (read-only report generator; severity + suppression + traceability guards) |
