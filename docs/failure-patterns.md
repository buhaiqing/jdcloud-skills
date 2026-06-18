# Failure Patterns — Reflexion Memory

> **Purpose**: Structured failure memory extracted from GCL traces and Self-Review records.
> Agents can optionally load this file during Pre-flight to prevent known errors.
>
> **Maintenance**: Updated automatically via Self-Review Round 3 (Lessons Learned).
> **Token budget**: ≤ 200 lines. When exceeded, prune low-frequency patterns (count < 3).

---

## 1. CLI Parameter Errors

> 从 GCL trace 中提取的 CLI 参数错误模式。高频模式优先。

| Skill | Command | Error Pattern | Root Cause | Fix | Count |
|-------|---------|---------------|------------|-----|-------|
| `audit-ops` | `describe-events` | `InvalidParameter: InvalidTimeRange` | 时间范围超过 90 天保留期 | 限制 `startTime`/`endTime` ≤ 90 天 | 3 |
| `audit-ops` | `describe-events` | `InvalidParameter: InvalidRegion` | 使用无效区域 ID | 验证区域为 `cn-north-1` 等有效 JD Cloud 区域 | 2 |
| `audit-ops` | `describe-event-detail` | `InvalidParameter: EventIdNotFound` | 事件 ID 不存在或已过期 | 确认 eventId 在保留期内且拼写正确 | 2 |

---

## 2. Skill Generation Issues

> Skill 生成器（jdcloud-skill-generator）常见的结构错误模式。

| Issue Type | Frequency | Fix Pattern | First Seen |
|------------|-----------|-------------|------------|
| Missing YAML frontmatter | 8x | Always start with `---` block containing name, description, license, compatibility, metadata | 2026-06 |
| Missing SHOULD/SHOULD NOT section | 5x | Add trigger conditions chapter with delegation rules | 2026-06 |
| Broken relative links | 4x | Use `../` prefix for advanced/ → references/ links | 2026-06 |
| Missing GCL Quality Gate section | 3x | Add `## Quality Gate (GCL)` with rubric reference and parameters | 2026-06 |
| Missing Well-Architected table | 3x | Add five-pillar table (Security, Stability, Cost, Efficiency, Performance) | 2026-06 |

---

## 3. Cross-Skill Composition Failures

> 跨 Skill 调用链中的失败模式。

| Source Skill | Target Skill | Failure Pattern | Resolution | Count |
|--------------|--------------|-----------------|------------|-------|
| `audit-ops` | `vm-ops` | Audit event shows unauthorized VM change but remediation fails | Verify IAM permissions before delegating remediation | 2 |
| `aiops-cruise` | `audit-ops` | Cruise finds anomaly but audit query returns empty | Check time range alignment between cruise findings and audit query window | 3 |
| `alert-intelligence` | `audit-ops` | Alert analysis needs audit trail but trail listing fails | Ensure audit trail is enabled in the region before querying | 2 |

---

## 4. Runtime Execution Patterns

> GCL 执行中发现的运行时失败模式。

| Skill | Operation | Failure Pattern | Root Cause | Prevention |
|-------|-----------|-----------------|------------|------------|
| `audit-ops` | `describe-events` | Large result set causes timeout | 未使用分页参数 | 始终使用 `pageNumber`/`pageSize`（≤100） | 4 |
| `audit-ops` | `describe-event-detail` | Sensitive data leakage in output | 未对 `requestParameters` 中的密码/密钥脱敏 | 执行前应用 `mask_sensitive()` | 3 |
| `audit-ops` | `describe-events` | Empty result without explanation | 时间范围无事件但未说明 | 返回空结果时明确告知用户"指定时间范围内无事件" | 2 |
| `audit-ops` | All operations | Credential exposure in trace | `JDC_SECRET_KEY` 出现在 trace 中 | 写入 trace 前扫描并替换为 `<masked>` | 2 |

---

## 5. Token Efficiency Violations

> Token Efficiency 规则的常见违反模式。

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
