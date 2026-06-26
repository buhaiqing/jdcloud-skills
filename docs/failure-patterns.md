# Failure Patterns — Reflexion Memory

> **Purpose**: Structured failure memory extracted from GCL traces and Self-Review records.
> Agents can optionally load this file during Pre-flight to prevent known errors.
>
> **Maintenance**: Updated automatically via Self-Review Round 3 (Lessons Learned).
> **Token budget**: ≤ 200 lines. When exceeded, prune low-frequency patterns (count < 3).

---

## 1. CLI Parameter Errors

> CLI parameter error patterns extracted from GCL traces. High-frequency patterns prioritized.

| Skill | Command | Error Pattern | Root Cause | Fix | Count |
|-------|---------|---------------|------------|-----|-------|
| `audit-ops` | `describe-events` | `InvalidParameter: InvalidTimeRange` | Time range exceeds 90-day retention limit | Limit `startTime`/`endTime` ≤ 90 days | 3 |
| `audit-ops` | `describe-events` | `InvalidParameter: InvalidRegion` | Invalid region ID used | Verify region is a valid JD Cloud region such as `cn-north-1` | 2 |
| `audit-ops` | `describe-event-detail` | `InvalidParameter: EventIdNotFound` | Event ID does not exist or has expired | Confirm eventId is within retention period and spelled correctly | 2 |

---

## 2. Skill Generation Issues

> Common structural error patterns for the skill generator (jdcloud-skill-generator).

| Issue Type | Frequency | Fix Pattern | First Seen |
|------------|-----------|-------------|------------|
| Missing YAML frontmatter | 8x | Always start with `---` block containing name, description, license, compatibility, metadata | 2026-06 |
| Missing SHOULD/SHOULD NOT section | 5x | Add trigger conditions chapter with delegation rules | 2026-06 |
| Broken relative links | 4x | Use `../` prefix for advanced/ → references/ links | 2026-06 |
| Missing GCL Quality Gate section | 3x | Add `## Quality Gate (GCL)` with rubric reference and parameters | 2026-06 |
| Missing Well-Architected table | 3x | Add five-pillar table (Security, Stability, Cost, Efficiency, Performance) | 2026-06 |

---

## 3. Cross-Skill Composition Failures

> Failure patterns across skill call chains.

| Source Skill | Target Skill | Failure Pattern | Resolution | Count |
|--------------|--------------|-----------------|------------|-------|
| `audit-ops` | `vm-ops` | Audit event shows unauthorized VM change but remediation fails | Verify IAM permissions before delegating remediation | 2 |
| `aiops-cruise` | `audit-ops` | Cruise finds anomaly but audit query returns empty | Check time range alignment between cruise findings and audit query window | 3 |
| `alert-intelligence` | `audit-ops` | Alert analysis needs audit trail but trail listing fails | Ensure audit trail is enabled in the region before querying | 2 |

---

## 4. Runtime Execution Patterns

> Runtime failure patterns discovered during GCL execution.

| Skill | Operation | Failure Pattern | Root Cause | Prevention | Count |
|-------|-----------|-----------------|------------|------------|-------|
| `audit-ops` | `describe-events` | Large result set causes timeout | Pagination parameters not used | Always use `pageNumber`/`pageSize` (≤100) | 4 |
| `audit-ops` | `describe-event-detail` | Sensitive data leakage in output | Passwords/keys in `requestParameters` not masked | Apply `mask_sensitive()` before output | 3 |
| `audit-ops` | `describe-events` | Empty result without explanation | No events in time range but no explanation given | Inform user explicitly "no events in the specified time range" when returning empty results | 2 |
| `audit-ops` | All operations | Credential exposure in trace | `JDC_SECRET_KEY` appears in trace | Scan and replace with `<masked>` before writing trace | 2 |

---

## 5. Token Efficiency Violations

> Common violation patterns of Token Efficiency rules.

| TE Rule | Common Violation | Fix | Frequency |
|---------|------------------|-----|-----------|
| TE-1 | Hardcoded region lists in references/ | Use `jdc vm describe-regions` query | 2x |
| TE-3 | Error table with > 3 columns | Merge columns, 1 error code per row | 2x |
| TE-4 | JSON paths scattered across file | Declare at file top in one block | 3x |
| TE-6 | Same script in SKILL.md and references/ | Delete from references, keep SKILL.md copy | 4x |

---

## Usage Guidelines

### For Agents (Pre-flight)

```
# Optional: Load failure patterns before executing a skill
# 1. Read this file (lazy-load, ~150 lines)
# 2. Filter patterns by current skill name
# 3. Inject relevant patterns into Generator context as prevention hints
```

### For Self-Review (Round 3: Lessons Learned)

```
# After completing R1 + R2:
# 1. Extract new failure patterns from this session
# 2. Check if pattern already exists (dedup by skill + command + error)
# 3. If new: append to appropriate section with count=1
# 4. If existing: increment count
# 5. If total lines > 200: prune patterns with count < 3
```

### For GCL Traces

```
# When a GCL iteration fails, record the failure pattern:
{
  "failure_pattern": {
    "category": "cli_parameter" | "skill_generation" | "cross_skill" | "runtime" | "token_efficiency",
    "skill": "jdcloud-audit-ops",
    "command": "GET https://audit.jdcloud-api.com/v1/...",
    "error": "InvalidParameter: ...",
    "fix": "Adjusted time range to ≤ 90 days",
    "reusable": true | false
  }
}
```

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-06-18 | Initial failure patterns for `jdcloud-audit-ops` and cross-skill composition |