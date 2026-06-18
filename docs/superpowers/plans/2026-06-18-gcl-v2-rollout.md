# GCL v2 Rollout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade all 32 JD Cloud skills from GCL v1 to GCL v2 (Phase 6 Hallucination Detection Layer + Phase 7 Reflexion Integration), following the pattern established in jdcloud-audit-ops v1.4.0.

**Architecture:** Each skill's SKILL.md Quality Gate section will be enhanced with: (1) Phase 6 H layer parameters and loop flow integration, (2) Phase 7 Reflexion Integration with failure-patterns.md reference, (3) Version bump and Changelog entry. The upgrade is mechanical and follows a template pattern from jdcloud-audit-ops.

**Tech Stack:** Markdown (SKILL.md), GCL v2 specification (AGENTS.md §10-11), failure-patterns.md (docs/)

**Priority Levels (per AGENTS.md §8):**
- **required** (10 skills): vm-ops, redis-ops, mysql-ops, postgresql-ops, mongodb-ops, elasticsearch-ops, iam-ops, kms-ops, eip-ops, disk-ops
- **recommended** (11 skills): clb-ops, cloudmonitor-ops, oss-ops, fc-ops, waf-ops, apigateway-ops, jcq-ops, logservice-ops, vpn-ops, dns-ops, cert-ops
- **optional** (6 skills): alert-intelligence, tag-audit-ops, skill-generator, aiops-cruise, routines-ops, billing-ops

---

## File Structure

**Files to Modify (32 skills × 1 file each):**
- `jdcloud-vm-ops/SKILL.md` - Add GCL v2 Quality Gate enhancements
- `jdcloud-redis-ops/SKILL.md` - Add GCL v2 Quality Gate enhancements
- `jdcloud-mysql-ops/SKILL.md` - Add GCL v2 Quality Gate enhancements
- `jdcloud-postgresql-ops/SKILL.md` - Add GCL v2 Quality Gate enhancements
- `jdcloud-mongodb-ops/SKILL.md` - Add GCL v2 Quality Gate enhancements
- `jdcloud-elasticsearch-ops/SKILL.md` - Add GCL v2 Quality Gate enhancements
- `jdcloud-iam-ops/SKILL.md` - Add GCL v2 Quality Gate enhancements
- `jdcloud-kms-ops/SKILL.md` - Add GCL v2 Quality Gate enhancements
- `jdcloud-eip-ops/SKILL.md` - Add GCL v2 Quality Gate enhancements
- `jdcloud-disk-ops/SKILL.md` - Add GCL v2 Quality Gate enhancements
- `jdcloud-clb-ops/SKILL.md` - Add GCL v2 Quality Gate enhancements
- `jdcloud-cloudmonitor-ops/SKILL.md` - Add GCL v2 Quality Gate enhancements
- `jdcloud-oss-ops/SKILL.md` - Add GCL v2 Quality Gate enhancements
- `jdcloud-fc-ops/SKILL.md` - Add GCL v2 Quality Gate enhancements
- `jdcloud-waf-ops/SKILL.md` - Add GCL v2 Quality Gate enhancements
- `jdcloud-apigateway-ops/SKILL.md` - Add GCL v2 Quality Gate enhancements
- `jdcloud-jcq-ops/SKILL.md` - Add GCL v2 Quality Gate enhancements
- `jdcloud-logservice-ops/SKILL.md` - Add GCL v2 Quality Gate enhancements
- `jdcloud-vpn-ops/SKILL.md` - Add GCL v2 Quality Gate enhancements
- `jdcloud-dns-ops/SKILL.md` - Add GCL v2 Quality Gate enhancements
- `jdcloud-cert-ops/SKILL.md` - Add GCL v2 Quality Gate enhancements
- `jdcloud-alert-intelligence/SKILL.md` - Add GCL v2 Quality Gate enhancements
- `jdcloud-tag-audit-ops/SKILL.md` - Add GCL v2 Quality Gate enhancements
- `jdcloud-skill-generator/SKILL.md` - Add GCL v2 Quality Gate enhancements
- `jdcloud-aiops-cruise/SKILL.md` - Add GCL v2 Quality Gate enhancements
- `jdcloud-routines-ops/SKILL.md` - Add GCL v2 Quality Gate enhancements
- `jdcloud-billing-ops/SKILL.md` - Add GCL v2 Quality Gate enhancements
- `jdcloud-kubernetes-ops/SKILL.md` - Add GCL v2 Quality Gate enhancements
- `jdcloud-topo-discovery/SKILL.md` - Add GCL v2 Quality Gate enhancements
- `jdcloud-arch-advisor/SKILL.md` - Add GCL v2 Quality Gate enhancements
- `jdcloud-vpc-ops/SKILL.md` - Add GCL v2 Quality Gate enhancements

**Reference Files (read-only):**
- `jdcloud-audit-ops/SKILL.md` - GCL v2 template (v1.4.0)
- `AGENTS.md` - GCL v2 specification (§10-11)
- `docs/failure-patterns.md` - Reflexion memory (already exists)

---

## Task 1: Upgrade required-level skills (Batch 1: vm-ops, redis-ops, mysql-ops)

**Files:**
- Modify: `jdcloud-vm-ops/SKILL.md`
- Modify: `jdcloud-redis-ops/SKILL.md`
- Modify: `jdcloud-mysql-ops/SKILL.md`

- [ ] **Step 1: Read current vm-ops Quality Gate section**

Run: `grep -n "## Quality Gate" jdcloud-vm-ops/SKILL.md`
Expected: Line number (e.g., 318)

Run: `sed -n '318,350p' jdcloud-vm-ops/SKILL.md`
Expected: Current GCL v1 Quality Gate content

- [ ] **Step 2: Enhance vm-ops Quality Gate with Phase 6 H layer**

Edit `jdcloud-vm-ops/SKILL.md` line ~318-350, replace existing Quality Gate section with:

```markdown
## Quality Gate (GCL)

> This skill participates in the repository-wide **Generator-Critic-Loop**
> (GCL) defined in [`AGENTS.md` §Quality Gate](../AGENTS.md#generator-critic-loop-gcl--adversarial-quality-gate).
> The quality gate is **required** for this skill (per `AGENTS.md` §8).

### Parameters (override `AGENTS.md` §8 defaults)

| Parameter | Value | Reason |
|---|---|---|
| `max_iterations` | **2** | `AGENTS.md` §8 default for `jdcloud-vm-ops` (required, destructive ops) |
| `rubric_version` | `v1` | see [rubric.md](references/rubric.md) |
| `trace_path` | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | unified with `jdcloud-audit-ops` (self) |
| `safety_confirm_required` | **true** | destructive ops (delete/stop) require explicit user confirmation |
| `hallucination_check` | **mandatory** | Phase 6 H layer; required for all `required` skills |
| `reflexion_integration` | **enabled** | Phase 7 lightweight Reflexion; loads `docs/failure-patterns.md` |

### Loop overview

```
User request
   │
   ▼
[0] Orchestrator pre-flight  ──► load rubric, classify operation
   │                              optionally load failure-patterns.md
   ▼
[1] Generator (G)            ──► jdc CLI (primary) → SDK (fallback)
   │                              generate command/payload (DO NOT execute yet)
   ▼
[1.5] Hallucination Detection (H) ──► pre-execution structural validity check
   │   (mandatory for vm-ops)        - CLI parameter existence
   │                                   - JSON structure compliance (if applicable)
   │
   ├── PASS → [1a] Execute (run the CLI/SDK call)
   ├── FAIL → [1b] Regenerate (H retriggers G with hallucination report; max 1 retry)
   │         still FAIL → HALT with "HALLUCINATION_ABORT"
   ▼
[2] Critic (C)               ──► isolated context, blind to user request
   │                              score every rubric dimension
   │                              assess test accuracy + regression gate
   ▼
[3] Orchestrator decider
   ├─ HALLUCINATION_ABORT     → ABORT (no partial)
   ├─ Safety=0 / blocking     → ABORT
   ├─ all pass                → RETURN
   ├─ iter<2 & not all pass   → RETRY (inject suggestions)
   └─ iter=2 & not all pass   → RETURN_BEST
```

### Hallucination Detection Layer (H) — Mandatory

> **Purpose**: Catch LLM-generated CLI commands that contain structurally invalid elements
> **before** they reach the JD Cloud VM API. This is a **pre-execution** gate placed between
> G's generation and actual API execution.

**Two-Category Check (for vm-ops):**

| Category | Check | Method |
|---|---|---|
| **CLI Parameter Existence** | Verify every `--flag` exists in `jdc vm <operation> --help` | Compare against `references/cli-usage.md` operation tables |
| **JSON Structure Compliance** | For operations with JSON payloads (e.g., `create-instances`) | Validate field nesting matches OpenAPI schema |

**Termination:**

| Condition | Exit Code | Action |
|---|---|---|
| **H_PASS** | — | Continue to [1a] Execute |
| **H_FAIL → Regenerate** | — | Inject hallucination report into G; max 1 regeneration attempt |
| **HALLUCINATION_ABORT** | 5 | HALT — structural hallucinations persist after regeneration |

**Trace Integration:**

The H result is embedded in the GCL trace JSON under `iterations[].hallucination_detector`:

```json
{
  "iter": 1,
  "hallucination_detector": {
    "status": "PASS|FAIL",
    "checks": {
      "cli_parameters": { "status": "PASS|FAIL", "unrecognized_params": [] },
      "json_structure": { "status": "PASS|FAIL", "issues": [] }
    },
    "report": "..."
  },
  "regenerated": false,
  "generator": { ... },
  "critic": { ... }
}
```

### Reflexion Integration (Lightweight Reflexion)

> **Purpose**: Enable cross-session learning from failure patterns, complementing the within-session
> GCL loop with persistent failure memory.

**Architecture:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    GCL Execution (per-session)                   │
│   [0] Pre-flight → [1] Generate → [1.5] H → [2] C → [3] Decide │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                    failure_pattern (in trace)
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              Reflexion Memory (cross-session)                    │
│   docs/failure-patterns.md (structured text, ≤200 lines)        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                    Pre-flight retrieval (optional)
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              Prevention (next session)                           │
│   Inject known patterns into Generator context                  │
└─────────────────────────────────────────────────────────────────┘
```

**Pre-flight Retrieval (Optional):**

During GCL Pre-flight (step [0]), the Orchestrator MAY:

```bash
# 1. Load docs/failure-patterns.md (lazy-load, ~150 lines)
# 2. Filter patterns by current skill name (jdcloud-vm-ops)
# 3. Inject top-3 relevant patterns into Generator context as prevention hints
```

**This is a HINT, not a CONSTRAINT** — the Generator should use these patterns to avoid known mistakes, but is not required to follow them if the context differs.

### Artifacts

- Rubric (concrete scoring rules): [references/rubric.md](references/rubric.md)
- Prompt templates (G / C / O / H): [references/prompt-templates.md](references/prompt-templates.md)
- Failure patterns (cross-session memory): [docs/failure-patterns.md](../docs/failure-patterns.md)

### Integration with existing flows

The GCL **wraps** the jdc-first-with-SDK-fallback flow defined under
`## Execution Flows` above. The Generator (G) IS the existing jdc/SDK
executor. The Critic (C) is a new, read-only role with no `jdc` / SDK
access. The Orchestrator (O) owns the loop and persists the GCL trace.
The Hallucination Detector (H) is a mandatory pre-execution structural check.

### Operation-specific behavior

- **`create-instances`** — Instance count, spec, and region MUST be explicit.
  H layer validates CLI parameters (`--instanceType`, `--az`, `--subnetId`) exist.
  Trace MUST include `instanceIds` from response.
- **`delete-instance`** — **SAFETY GATE**: MUST confirm with user before execution.
  Unconfirmed delete → Safety = 0 → ABORT.
  H layer validates `--instanceId` parameter exists.
- **`stop-instance`** — **SAFETY GATE**: MUST confirm with user before execution.
  Unconfirmed stop → Safety = 0 → ABORT.
  H layer validates `--instanceId` parameter exists.
```

- [ ] **Step 3: Bump vm-ops version and update Changelog**

Edit `jdcloud-vm-ops/SKILL.md` line ~15-16:

```yaml
  version: "1.8.0"
  last_updated: "2026-06-18"
```

Edit `jdcloud-vm-ops/SKILL.md` Changelog section (line ~109), add new entry at top:

```markdown
| 1.8.0 | 2026-06-18 | **GCL v2 rollout**: Enhanced Quality Gate with Phase 6 Hallucination Detection Layer (H, mandatory) and Phase 7 Reflexion Integration. Added pre-execution structural validity check for CLI parameters and JSON payloads. Integrated `docs/failure-patterns.md` for cross-session failure memory. Aligned with AGENTS.md GCL v2 specification (§10-11). |
```

- [ ] **Step 4: Repeat Steps 1-3 for redis-ops and mysql-ops**

For each skill:
1. Read current Quality Gate section
2. Enhance with Phase 6 H layer (mandatory for required skills) and Phase 7 Reflexion
3. Bump version (minor version: 1.x.0 → 1.(x+1).0)
4. Update Changelog with GCL v2 rollout entry

**Key differences per skill:**
- **redis-ops**: `max_iterations=2`, `safety_confirm_required=true` for flushall/delete
- **mysql-ops**: `max_iterations=2`, `safety_confirm_required=true` for DDL/DML with WHERE clause

- [ ] **Step 5: Commit batch 1**

```bash
git add jdcloud-vm-ops/SKILL.md jdcloud-redis-ops/SKILL.md jdcloud-mysql-ops/SKILL.md
git commit -m "feat(gcl): upgrade vm-ops, redis-ops, mysql-ops to GCL v2

- Add Phase 6 Hallucination Detection Layer (H, mandatory)
- Add Phase 7 Reflexion Integration
- Bump versions to 1.8.0
- Update Changelogs with GCL v2 rollout entries

Aligned with AGENTS.md GCL v2 specification (§10-11)."
```

---

## Task 2: Upgrade required-level skills (Batch 2: postgresql-ops, mongodb-ops, elasticsearch-ops)

**Files:**
- Modify: `jdcloud-postgresql-ops/SKILL.md`
- Modify: `jdcloud-mongodb-ops/SKILL.md`
- Modify: `jdcloud-elasticsearch-ops/SKILL.md`

- [ ] **Step 1: Read current Quality Gate sections**

Run: `grep -n "## Quality Gate" jdcloud-postgresql-ops/SKILL.md jdcloud-mongodb-ops/SKILL.md jdcloud-elasticsearch-ops/SKILL.md`

- [ ] **Step 2: Enhance each skill with GCL v2**

Follow the same pattern as Task 1, Step 2, but adapt for each skill:

**postgresql-ops:**
- `max_iterations=2`, `safety_confirm_required=true` for DDL (DROP SCHEMA CASCADE) / DML (DELETE without WHERE)
- H layer validates CLI parameters for `jdc postgresql` operations
- Operation-specific: `VACUUM FULL` requires confirm, `SELECT FOR UPDATE` re-score

**mongodb-ops:**
- `max_iterations=2`, `safety_confirm_required=true` for dropDatabase / updateMany with empty filter
- H layer validates CLI parameters for `jdc mongodb` operations
- Operation-specific: `$out`/`$merge` in aggregate require confirm

**elasticsearch-ops:**
- `max_iterations=2`, `safety_confirm_required=true` for delete index / cluster
- H layer validates CLI parameters for `jdc elasticsearch` operations
- Operation-specific: wildcard `DELETE /<index>` requires confirm, `match_all` in `_update_by_query` re-score

- [ ] **Step 3: Bump versions and update Changelogs**

For each skill:
- Bump version (minor version: 1.x.0 → 1.(x+1).0)
- Add Changelog entry with GCL v2 rollout details

- [ ] **Step 4: Commit batch 2**

```bash
git add jdcloud-postgresql-ops/SKILL.md jdcloud-mongodb-ops/SKILL.md jdcloud-elasticsearch-ops/SKILL.md
git commit -m "feat(gcl): upgrade postgresql-ops, mongodb-ops, elasticsearch-ops to GCL v2

- Add Phase 6 Hallucination Detection Layer (H, mandatory)
- Add Phase 7 Reflexion Integration
- Bump versions
- Update Changelogs with GCL v2 rollout entries

Aligned with AGENTS.md GCL v2 specification (§10-11)."
```

---

## Task 3: Upgrade required-level skills (Batch 3: iam-ops, kms-ops, eip-ops, disk-ops)

**Files:**
- Modify: `jdcloud-iam-ops/SKILL.md`
- Modify: `jdcloud-kms-ops/SKILL.md`
- Modify: `jdcloud-eip-ops/SKILL.md`
- Modify: `jdcloud-disk-ops/SKILL.md`

- [ ] **Step 1: Read current Quality Gate sections**

Run: `grep -n "## Quality Gate" jdcloud-iam-ops/SKILL.md jdcloud-kms-ops/SKILL.md jdcloud-eip-ops/SKILL.md jdcloud-disk-ops/SKILL.md`

- [ ] **Step 2: Enhance each skill with GCL v2**

Follow the same pattern, but adapt for each skill:

**iam-ops:**
- `max_iterations=2`, `safety_confirm_required=true` for detach policy / delete role / rotate keys
- H layer validates CLI parameters for `jdc iam` operations
- Operation-specific: `attach AdministratorAccess` / `*:*` requires confirm, `create main-account key` requires confirm, `Principal: *` trust policy requires confirm
- **Secret value never logged** (SHA-256 + length only)

**kms-ops:**
- `max_iterations=2`, `safety_confirm_required=true` for schedule key deletion / disable key
- H layer validates CLI parameters for `jdc kms` operations
- Operation-specific: `schedule-key-deletion` with `pending-window-in-days < 7` requires confirm, prod `disable` / `decrypt` requires confirm
- **Plaintext / secret value never logged** (SHA-256 + length only)

**eip-ops:**
- `max_iterations=2`, `safety_confirm_required=true` for release EIP
- H layer validates CLI parameters for `jdc eip` operations
- Operation-specific: irreversible `release EIP` (InUse refusal), prod `dissociate` / `release` confirm, `associate` force-rebind guard

**disk-ops:**
- `max_iterations=2`, `safety_confirm_required=true` for delete disk / resize shrink
- H layer validates CLI parameters for `jdc disk` operations
- Operation-specific: delete disk with in-use check, resize shrink prevention, system disk detach guard

- [ ] **Step 3: Bump versions and update Changelogs**

For each skill:
- Bump version (minor version: 1.x.0 → 1.(x+1).0)
- Add Changelog entry with GCL v2 rollout details

- [ ] **Step 4: Commit batch 3**

```bash
git add jdcloud-iam-ops/SKILL.md jdcloud-kms-ops/SKILL.md jdcloud-eip-ops/SKILL.md jdcloud-disk-ops/SKILL.md
git commit -m "feat(gcl): upgrade iam-ops, kms-ops, eip-ops, disk-ops to GCL v2

- Add Phase 6 Hallucination Detection Layer (H, mandatory)
- Add Phase 7 Reflexion Integration
- Bump versions
- Update Changelogs with GCL v2 rollout entries

Aligned with AGENTS.md GCL v2 specification (§10-11)."
```

---

## Task 4: Upgrade recommended-level skills (Batch 1: clb-ops, cloudmonitor-ops, oss-ops, fc-ops, waf-ops)

**Files:**
- Modify: `jdcloud-clb-ops/SKILL.md`
- Modify: `jdcloud-cloudmonitor-ops/SKILL.md`
- Modify: `jdcloud-oss-ops/SKILL.md`
- Modify: `jdcloud-fc-ops/SKILL.md`
- Modify: `jdcloud-waf-ops/SKILL.md`

- [ ] **Step 1: Read current Quality Gate sections**

Run: `grep -n "## Quality Gate" jdcloud-clb-ops/SKILL.md jdcloud-cloudmonitor-ops/SKILL.md jdcloud-oss-ops/SKILL.md jdcloud-fc-ops/SKILL.md jdcloud-waf-ops/SKILL.md`

- [ ] **Step 2: Enhance each skill with GCL v2**

Follow the same pattern as Task 1, but adapt for recommended skills:

**Key differences from required skills:**
- `hallucination_check` = **recommended** (not mandatory)
- `max_iterations` = **3** (per AGENTS.md §8)
- H layer checks are recommended but not mandatory

**clb-ops:**
- `max_iterations=3`, `safety_confirm_required=true` for delete-lb / deregister-targets > 50%
- Operation-specific: `delete-lb` traffic cut, `deregister-targets` >50% DRAIN guard, `register-targets` non-running backend refusal

**cloudmonitor-ops:**
- `max_iterations=3`, `safety_confirm_required=true` for delete-alarm-rule / disable-alarm-rule
- Operation-specific: silent-failure guards for `delete-alarm-rule` / `disable-alarm-rule`, `DELETE_AFTER_FIRING` rule, prod tag double-confirm, empty notification channel refusal

**oss-ops:**
- `max_iterations=3`, `safety_confirm_required=true` for delete bucket / delete object / set public ACL
- Operation-specific: SDK-only (OSS not exposed via `jdc` CLI), safety gates for delete bucket/object, public ACL on prod

**fc-ops:**
- `max_iterations=3`, `safety_confirm_required=true` for delete service / prod invoke
- Operation-specific: SDK-only (FC not exposed via `jdc` CLI), safety gates for delete service cascade, prod invoke confirm, runtime/handler validation

**waf-ops:**
- `max_iterations=3`, `safety_confirm_required=true` for delete instance / disable domain
- Operation-specific: safety gates for delete instance with domain check, disable domain origin-exposure warning, cert-domain mismatch guard

- [ ] **Step 3: Bump versions and update Changelogs**

For each skill:
- Bump version (minor version: 1.x.0 → 1.(x+1).0)
- Add Changelog entry with GCL v2 rollout details

- [ ] **Step 4: Commit batch 1**

```bash
git add jdcloud-clb-ops/SKILL.md jdcloud-cloudmonitor-ops/SKILL.md jdcloud-oss-ops/SKILL.md jdcloud-fc-ops/SKILL.md jdcloud-waf-ops/SKILL.md
git commit -m "feat(gcl): upgrade clb-ops, cloudmonitor-ops, oss-ops, fc-ops, waf-ops to GCL v2

- Add Phase 6 Hallucination Detection Layer (H, recommended)
- Add Phase 7 Reflexion Integration
- Bump versions
- Update Changelogs with GCL v2 rollout entries

Aligned with AGENTS.md GCL v2 specification (§10-11)."
```

---

## Task 5: Upgrade recommended-level skills (Batch 2: apigateway-ops, jcq-ops, logservice-ops, vpn-ops, dns-ops, cert-ops)

**Files:**
- Modify: `jdcloud-apigateway-ops/SKILL.md`
- Modify: `jdcloud-jcq-ops/SKILL.md`
- Modify: `jdcloud-logservice-ops/SKILL.md`
- Modify: `jdcloud-vpn-ops/SKILL.md`
- Modify: `jdcloud-dns-ops/SKILL.md`
- Modify: `jdcloud-cert-ops/SKILL.md`

- [ ] **Step 1: Read current Quality Gate sections**

Run: `grep -n "## Quality Gate" jdcloud-apigateway-ops/SKILL.md jdcloud-jcq-ops/SKILL.md jdcloud-logservice-ops/SKILL.md jdcloud-vpn-ops/SKILL.md jdcloud-dns-ops/SKILL.md jdcloud-cert-ops/SKILL.md`

- [ ] **Step 2: Enhance each skill with GCL v2**

Follow the same pattern as Task 4, but adapt for each skill:

**apigateway-ops:**
- `max_iterations=3`, `safety_confirm_required=true` for API publish / unpublish / delete
- Operation-specific: API publish / unpublish / delete are reversible but affect live traffic

**jcq-ops:**
- `max_iterations=3`, `safety_confirm_required=true` for topic delete / consumer group reset
- Operation-specific: topic delete + consumer group reset can lose messages

**logservice-ops:**
- `max_iterations=3`, `safety_confirm_required=true` for index delete
- Operation-specific: index delete is irreversible (data loss); metric/config changes are recoverable

**vpn-ops:**
- `max_iterations=3`, `safety_confirm_required=true` for VPN tunnel delete
- Operation-specific: VPN tunnel delete breaks hybrid cloud connectivity

**dns-ops:**
- `max_iterations=3`, `safety_confirm_required=true` for delete domain / batch set
- Operation-specific: delete domain removes all records irreversibly; batch set can overwrite all records

**cert-ops:**
- `max_iterations=3`, `safety_confirm_required=true` for delete cert / update cert
- Operation-specific: delete cert breaks HTTPS for bound CLB/CDN; update cert replaces content

- [ ] **Step 3: Bump versions and update Changelogs**

For each skill:
- Bump version (minor version: 1.x.0 → 1.(x+1).0)
- Add Changelog entry with GCL v2 rollout details

- [ ] **Step 4: Commit batch 2**

```bash
git add jdcloud-apigateway-ops/SKILL.md jdcloud-jcq-ops/SKILL.md jdcloud-logservice-ops/SKILL.md jdcloud-vpn-ops/SKILL.md jdcloud-dns-ops/SKILL.md jdcloud-cert-ops/SKILL.md
git commit -m "feat(gcl): upgrade apigateway-ops, jcq-ops, logservice-ops, vpn-ops, dns-ops, cert-ops to GCL v2

- Add Phase 6 Hallucination Detection Layer (H, recommended)
- Add Phase 7 Reflexion Integration
- Bump versions
- Update Changelogs with GCL v2 rollout entries

Aligned with AGENTS.md GCL v2 specification (§10-11)."
```

---

## Task 6: Upgrade optional-level skills (alert-intelligence, tag-audit-ops, skill-generator, aiops-cruise, routines-ops, billing-ops)

**Files:**
- Modify: `jdcloud-alert-intelligence/SKILL.md`
- Modify: `jdcloud-tag-audit-ops/SKILL.md`
- Modify: `jdcloud-skill-generator/SKILL.md`
- Modify: `jdcloud-aiops-cruise/SKILL.md`
- Modify: `jdcloud-routines-ops/SKILL.md`
- Modify: `jdcloud-billing-ops/SKILL.md`

- [ ] **Step 1: Read current Quality Gate sections**

Run: `grep -n "## Quality Gate" jdcloud-alert-intelligence/SKILL.md jdcloud-tag-audit-ops/SKILL.md jdcloud-skill-generator/SKILL.md jdcloud-aiops-cruise/SKILL.md jdcloud-routines-ops/SKILL.md jdcloud-billing-ops/SKILL.md`

- [ ] **Step 2: Enhance each skill with GCL v2**

Follow the same pattern, but adapt for optional skills:

**Key differences from required/recommended skills:**
- `hallucination_check` = **optional** (not mandatory, not even recommended)
- `max_iterations` = **5** (per AGENTS.md §8 for optional skills)
- H layer checks are optional and may be skipped

**alert-intelligence:**
- `max_iterations=5`, `safety_confirm_required=false` (read-only)
- Operation-specific: rubric enforces "report must NOT recommend delete/disable/modify on alert rule" + 4-tuple citation + next-hop suggestion; PII / secret mask

**tag-audit-ops:**
- `max_iterations=5`, `safety_confirm_required=false` (read-only for tag inspection)
- Operation-specific: DOPS ticket payload completeness + duplicate-ticket idempotency check

**skill-generator:**
- `max_iterations=5`, `safety_confirm_required=false` (meta operation)
- Operation-specific: secret-leak guard, OpenSpec + 2-round self-review enforcement, jdc CLI / SDK cross-validation

**aiops-cruise:**
- `max_iterations=5`, `safety_confirm_required=false` (read-only cruise)
- Operation-specific: Phase 1 sniff + Phase 2 analyze + Phase 3 suggestions (no mutations)

**routines-ops:**
- `max_iterations=5`, `safety_confirm_required=false` (read-only by default)
- Operation-specific: read-only by default; on-demand GCL recommended; renewal flows must confirm

**billing-ops:**
- `max_iterations=5`, `safety_confirm_required=false` (read-only billing queries)
- Operation-specific: SDK-only billing operations

- [ ] **Step 3: Bump versions and update Changelogs**

For each skill:
- Bump version (minor version: 1.x.0 → 1.(x+1).0)
- Add Changelog entry with GCL v2 rollout details

- [ ] **Step 4: Commit optional skills**

```bash
git add jdcloud-alert-intelligence/SKILL.md jdcloud-tag-audit-ops/SKILL.md jdcloud-skill-generator/SKILL.md jdcloud-aiops-cruise/SKILL.md jdcloud-routines-ops/SKILL.md jdcloud-billing-ops/SKILL.md
git commit -m "feat(gcl): upgrade optional-level skills to GCL v2

- Add Phase 6 Hallucination Detection Layer (H, optional)
- Add Phase 7 Reflexion Integration
- Bump versions
- Update Changelogs with GCL v2 rollout entries

Skills: alert-intelligence, tag-audit-ops, skill-generator, aiops-cruise, routines-ops, billing-ops

Aligned with AGENTS.md GCL v2 specification (§10-11)."
```

---

## Task 7: Upgrade remaining skills (kubernetes-ops, topo-discovery, arch-advisor, vpc-ops)

**Files:**
- Modify: `jdcloud-kubernetes-ops/SKILL.md`
- Modify: `jdcloud-topo-discovery/SKILL.md`
- Modify: `jdcloud-arch-advisor/SKILL.md`
- Modify: `jdcloud-vpc-ops/SKILL.md`

- [ ] **Step 1: Read current Quality Gate sections**

Run: `grep -n "## Quality Gate" jdcloud-kubernetes-ops/SKILL.md jdcloud-topo-discovery/SKILL.md jdcloud-arch-advisor/SKILL.md jdcloud-vpc-ops/SKILL.md`

- [ ] **Step 2: Enhance each skill with GCL v2**

Follow the same pattern, but adapt for each skill:

**kubernetes-ops:**
- Determine GCL level (likely recommended, `max_iterations=3`)
- Add Phase 6 H layer and Phase 7 Reflexion
- Operation-specific: cluster/node group management, safety gates for delete operations

**topo-discovery:**
- Determine GCL level (likely optional, `max_iterations=5`)
- Add Phase 6 H layer and Phase 7 Reflexion
- Operation-specific: topology graph rendering, read-only discovery

**arch-advisor:**
- Determine GCL level (likely optional, `max_iterations=5`)
- Add Phase 6 H layer and Phase 7 Reflexion
- Operation-specific: architecture review / WAF assessment / Recommendation

**vpc-ops:**
- Determine GCL level (likely recommended, `max_iterations=3`)
- Add Phase 6 H layer and Phase 7 Reflexion
- Operation-specific: VPC/Subnet/Security Group/Route Table/ACL management

- [ ] **Step 3: Bump versions and update Changelogs**

For each skill:
- Bump version (minor version: 1.x.0 → 1.(x+1).0)
- Add Changelog entry with GCL v2 rollout details

- [ ] **Step 4: Commit remaining skills**

```bash
git add jdcloud-kubernetes-ops/SKILL.md jdcloud-topo-discovery/SKILL.md jdcloud-arch-advisor/SKILL.md jdcloud-vpc-ops/SKILL.md
git commit -m "feat(gcl): upgrade kubernetes-ops, topo-discovery, arch-advisor, vpc-ops to GCL v2

- Add Phase 6 Hallucination Detection Layer (H)
- Add Phase 7 Reflexion Integration
- Bump versions
- Update Changelogs with GCL v2 rollout entries

Aligned with AGENTS.md GCL v2 specification (§10-11)."
```

---

## Task 8: Update AGENTS.md with GCL v2 rollout status

**Files:**
- Modify: `AGENTS.md`

- [ ] **Step 1: Update AGENTS.md §12 Rollout Roadmap**

Edit `AGENTS.md` line ~680-690, update Phase 5 status:

```markdown
- **Phase 5** ✅ — GCL rollout extended to all `recommended` skills (CLB, CloudMonitor, OSS, FC, WAF, APIGateway, JCQ, LogService, VPN, DNS, Cert). Each gets lean `references/rubric.md` + `references/prompt-templates.md` + `## Quality Gate (GCL)` section with `max_iter=3`.
- **Phase 6** ✅ — **Hallucination Detection Layer (H)** shipped. §10 added to spec; `scripts/gcl_runner.py` extended with `--enable-hallucination-check` flag and `hallucination_detect()` function (parameter existence, JSON structure, time range validity). Every `required`/`recommended` skill now gets a `HALLUCINATION_ABORT` exit path in addition to the existing `SAFETY_FAIL`.
- **Phase 7** ✅ — **Lightweight Reflexion Integration** shipped. §11 added to spec; `docs/failure-patterns.md` created as centralized Reflexion memory; GCL trace schema extended with `failure_pattern` field; Pre-flight updated with optional pattern retrieval. Cross-session failure pattern learning enabled.
- **Phase 8** ✅ — **Complete GCL v2 rollout**: All 32 skills upgraded from GCL v1 to GCL v2. Required skills (10) have mandatory H layer; recommended skills (11) have recommended H layer; optional skills (6) have optional H layer. All skills integrated with Phase 7 Reflexion via `docs/failure-patterns.md`. Aligned with AGENTS.md GCL v2 specification (§10-11).
```

- [ ] **Step 2: Update AGENTS.md §13 Changelog**

Edit `AGENTS.md` line ~700-710, add new entry:

```markdown
| 2.1.0 | 2026-06-18 | **Complete GCL v2 rollout for all skills**: Upgraded 32 skills from GCL v1 to GCL v2. Required skills (vm-ops, redis-ops, mysql-ops, postgresql-ops, mongodb-ops, elasticsearch-ops, iam-ops, kms-ops, eip-ops, disk-ops) have mandatory Phase 6 H layer. Recommended skills (clb-ops, cloudmonitor-ops, oss-ops, fc-ops, waf-ops, apigateway-ops, jcq-ops, logservice-ops, vpn-ops, dns-ops, cert-ops) have recommended H layer. Optional skills (alert-intelligence, tag-audit-ops, skill-generator, aiops-cruise, routines-ops, billing-ops, kubernetes-ops, topo-discovery, arch-advisor, vpc-ops) have optional H layer. All skills integrated with Phase 7 Reflexion via `docs/failure-patterns.md`. |
```

- [ ] **Step 3: Commit AGENTS.md update**

```bash
git add AGENTS.md
git commit -m "docs(gcl): update AGENTS.md with complete GCL v2 rollout status

- Update §12 Rollout Roadmap with Phase 8 completion
- Add v2.1.0 Changelog entry for all 32 skills upgrade

All skills now aligned with AGENTS.md GCL v2 specification (§10-11)."
```

---

## Task 9: Verify all upgrades with consistency check

**Files:**
- Read: All 32 upgraded SKILL.md files
- Read: AGENTS.md

- [ ] **Step 1: Verify all skills have GCL v2 sections**

Run: `grep -l "Hallucination Detection Layer" jdcloud-*/SKILL.md | wc -l`
Expected: 33 (32 upgraded + 1 audit-ops already done)

- [ ] **Step 2: Verify all skills have Reflexion Integration**

Run: `grep -l "Reflexion Integration" jdcloud-*/SKILL.md | wc -l`
Expected: 33

- [ ] **Step 3: Verify version bumps**

Run: `grep -h "version:" jdcloud-*/SKILL.md | sort | uniq -c`
Expected: All versions bumped (no duplicates of old versions)

- [ ] **Step 4: Verify Changelog entries**

Run: `grep -h "GCL v2 rollout" jdcloud-*/SKILL.md | wc -l`
Expected: 33

- [ ] **Step 5: Run markdownlint on all upgraded files**

Run: `markdownlint jdcloud-*/SKILL.md`
Expected: No errors

- [ ] **Step 6: Final commit (if any fixes needed)**

```bash
git add .
git commit -m "chore(gcl): final consistency check and fixes for GCL v2 rollout

- Verified all 32 skills upgraded to GCL v2
- Verified Phase 6 H layer and Phase 7 Reflexion Integration present
- Verified version bumps and Changelog entries
- Ran markdownlint on all upgraded files

Complete GCL v2 rollout finished."
```

---

## Execution Summary

**Total Tasks:** 9

**Total Skills Upgraded:** 32

**Breakdown by Priority:**
- Required (10 skills): vm-ops, redis-ops, mysql-ops, postgresql-ops, mongodb-ops, elasticsearch-ops, iam-ops, kms-ops, eip-ops, disk-ops
- Recommended (11 skills): clb-ops, cloudmonitor-ops, oss-ops, fc-ops, waf-ops, apigateway-ops, jcq-ops, logservice-ops, vpn-ops, dns-ops, cert-ops
- Optional (11 skills): alert-intelligence, tag-audit-ops, skill-generator, aiops-cruise, routines-ops, billing-ops, kubernetes-ops, topo-discovery, arch-advisor, vpc-ops

**Total Commits:** 9 (one per task batch)

**Estimated Time:** 2-3 hours (depending on execution speed)

**Success Criteria:**
- All 32 skills have Phase 6 H layer (mandatory/recommended/optional per AGENTS.md §8)
- All 32 skills have Phase 7 Reflexion Integration
- All 32 skills have version bumps and Changelog entries
- AGENTS.md updated with Phase 8 completion status
- All files pass markdownlint

---

**Plan complete and saved to `docs/superpowers/plans/2026-06-18-gcl-v2-rollout.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
