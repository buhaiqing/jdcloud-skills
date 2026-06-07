# JD Cloud Skills Farm

## Quick Identity

**JD Cloud Skills Farm** is a collection of AI Agent Skill definitions (structured Markdown documents following the Agent Skill OpenSpec) that enable AI agents to perform JD Cloud (京东云) operations. Each skill maps to one JD Cloud product.

## Repo Layout

```
jdcloud-skills/
├── README.md / README_EN.md       # Bilingual project docs
├── QUICK_START.md / QUICK_START_EN.md  # Bilingual quick start
├── jdcloud-skill-generator/       # Meta Skill — generates new product skills
├── jdcloud-vm-ops/                # VM lifecycle + cloud assistant
├── jdcloud-redis-ops/             # Redis cache management
├── jdcloud-oss-ops/               # OSS — object storage
├── jdcloud-nat-ops/               # NAT — NAT gateway
├── jdcloud-kubernetes-ops/        # K8s — Kubernetes cluster management
├── jdcloud-cloudmonitor-ops/      # Cloud Monitor — metrics, alarms
├── jdcloud-iam-ops/               # IAM — users, groups, roles, policies
├── jdcloud-kms-ops/               # KMS — key management, encryption
├── jdcloud-clb-ops/               # CLB — load balancer management
├── jdcloud-alert-intelligence/    # Alert post-processing (aggregation, suppression, reporting)
├── .env.example / pyproject.toml / uv.lock
└── AGENTS.md                      # ← this file
```

## Every Skill Directory Follows

```
jdcloud-[product]-ops/
├── SKILL.md                    # Main skill definition (entry point)
├── assets/example-config.yaml  # Sample configs
└── references/
    ├── cli-usage.md
    ├── core-concepts.md
    ├── integration.md
    ├── monitoring.md
    └── troubleshooting.md
```

## Development Environment

**Python 3.10** | **`uv`** (package manager) | **`jdc`** (JD Cloud CLI)

> **IMPORTANT: Python version must be 3.10, NOT 3.12.**
> `jdcloud_cli==1.2.12` imports `SafeConfigParser` from `configparser`, which was **removed in Python 3.12**. Using Python 3.12+ will cause an `ImportError` and make the CLI unusable.
>
> Always use `uv venv --python 3.10` to create the virtual environment. If Python 3.10 is not installed on your system, install it first:
> - macOS: `brew install python@3.10`
> - Linux: `apt install python3.10 python3.10-dev` or `uv python install 3.10`
> - Windows: Download from https://www.python.org/downloads/release/python-3100/

### Setup

```bash
uv venv --python 3.10
source .venv/bin/activate
uv pip install jdcloud_cli jdcloud_sdk
```

`pyproject.toml` pins `jdcloud_cli==1.2.12`. The default pip index is `https://mirrors.aliyun.com/pypi/simple/` (configured under `[tool.uv]`).

### Credentials

Three methods (priority order: shell env > `.env` > `~/.jdc/config`):

```bash
# Method 1: .env file (recommended for local dev)
cp .env.example .env
# Edit with real credentials; .env is in .gitignore

# Method 2: CLI config for jdc
jdc config init              # interactive
# Or manual:
export HOME=/tmp/jdc-home    # sandbox-safe writable home
mkdir -p /tmp/jdc-home/.jdc
cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = {{env.JDC_ACCESS_KEY}}
secret_key = {{env.JDC_SECRET_KEY}}
region_id = cn-north-1
endpoint = vm.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF
printf "%s" "default" > /tmp/jdc-home/.jdc/current
```

**CRITICAL: jdc CLI reads credentials ONLY from `~/.jdc/config` INI file, NOT from environment variables.** The SDK reads from `JDC_ACCESS_KEY`/`JDC_SECRET_KEY` env vars. Both must be configured.

**NEVER** print or log `JDC_SECRET_KEY`. Only check existence with `test -n`.

## jdc CLI Quirks (Hard-Earned)

These are the most common agent mistakes — get them right every time:

| Rule | Wrong | Correct |
|------|-------|---------|
| `--output json` placement | `jdc vm list --output json` | `jdc --output json vm list` |
| `--no-interactive` flag | `jdc --no-interactive vm delete` | **Omit entirely** — not supported |
| Credentials | `export JDC_ACCESS_KEY=...` (CLI ignores) | Must write `~/.jdc/config` INI file |
| `~/.jdc/current` newline | `echo "default" > file` (adds newline) | `printf "%s" "default" > file` (no trailing newline) |

## Execution Strategy

**jdc-first with SDK fallback** — the repository-wide policy:

1. Try `jdc --output json <command>` first
2. On failure, retry up to 3 times with exponential backoff (0s → 2s → 4s)
3. After 3 consecutive failures, fall back to Python SDK (`jdcloud_sdk`)
4. Document which path was used

## Skill SKILL.md Anatomy

Every `SKILL.md` uses:
- **YAML frontmatter** with `name`, `version`, `metadata` (including `cli_applicability`, `cli_version_locked`, `sdk_version_locked`)
- **Trigger & Scope** — `SHOULD Use` / `SHOULD NOT Use` with delegation rules
- **Variable Convention** — `{{env.*}}` (runtime, never prompt user), `{{user.*}}` (ask once, cache), `{{output.*}}` (parse from JSON response)
- **Execution Flows** — Pre-flight → Execute (jdc primary / SDK fallback) → Validate → Recover
- **Output Parsing Rules** — JSON paths (`$.result.*`) and state transition tables
- **Failure Recovery** — Error pattern tables with retry counts, backoff, and agent actions
- **Safety Gates** — Delete/recovery operations REQUIRE explicit user confirmation

## Cross-Skill Delegation

When a user's request spans multiple JD Cloud products:

| If they ask about | Delegate to |
|---|---|
| VM create/stop/delete | `jdcloud-vm-ops` |
| Redis instance CRUD | `jdcloud-redis-ops` |
| VPC/Subnet/Security Group/Route Table/ACL management | `jdcloud-vpc-ops` |
| Architecture review / WAF assessment / Recommendation | `jdcloud-arch-advisor` |
| Monitoring metrics, alarm rules | `jdcloud-cloudmonitor-ops` |
| Alert analysis, suppression, reporting | `jdcloud-alert-intelligence` |
| IAM users, policies, keys | `jdcloud-iam-ops` |
| Key management, encryption | `jdcloud-kms-ops` |
| Load balancer config | `jdcloud-clb-ops` |
| OSS bucket/object CRUD, storage management | `jdcloud-oss-ops` |
| NAT gateway/SNAT/DNAT rules | `jdcloud-nat-ops` |
| Kubernetes cluster/node group mgmt | `jdcloud-kubernetes-ops` |
| Generate a new product skill | `jdcloud-skill-generator` |

- `jdcloud-alert-intelligence` is **read-only** — it analyzes alerts but delegates alarm rule changes back to `jdcloud-cloudmonitor-ops`.
- Each skill's `SHOULD NOT Use` section lists exactly where to route.

## Validation

```bash
npm install -g markdownlint-cli
markdownlint jdcloud-[product]-ops/SKILL.md
```

## Versioning

SemVer in `SKILL.md` frontmatter. Update `version` field + Changelog table when modifying. The `version` field reflects the skill document version, not the SDK version (tracked separately in `metadata.sdk_version_locked`).

## Security Rules

- `{{env.*}}` placeholders are resolved from agent runtime — **never prompt the user**
- `.env` is gitignored; never commit real credentials
- Delete/stop/restore operations require explicit user confirmation ("safety gate")
- `jdcloud-alert-intelligence` is read-only — no resource mutations
- Credential status checks: `test -n "$VAR"` only, print `<masked>` if logging status

## Self-Review Policy

Every skill update MUST follow a **2-round self-review process** to ensure quality and correctness:

### Round 1: Initial Review
After creating or modifying a skill:
1. Review the skill against the template and existing reference skills
2. Verify all required sections are present (frontmatter, Trigger & Scope, Variable Convention, Execution Flows, etc.)
3. Check for consistency with jdc-first with SDK fallback strategy
4. Validate safety gates are in place for destructive operations

### Round 2: Deep Review
After Round 1 fixes are applied:
1. Verify API accuracy against official OpenAPI specifications
2. Validate CLI command syntax and JSON output paths
3. Check cross-skill delegation rules are correctly defined
4. Confirm versioning follows SemVer and changelog is updated

### Auto-Fix Requirement
All issues discovered during both review rounds MUST be proactively fixed before the skill is considered complete. This includes:
- Correcting API parameters and response paths
- Fixing CLI command syntax
- Adding missing safety gates
- Updating documentation inconsistencies
- Ensuring alignment with repository-wide conventions

---

## Generator-Critic-Loop (GCL) — Adversarial Quality Gate

> Inspired by GAN's Generator/Discriminator idea, but deliberately **not** a real GAN.
> Naming: **GCL (Generator-Critic-Loop)** to avoid misleading reviewers and LLM trainees.

### 1. Purpose

Apply an adversarial **Generator ↔ Critic** loop with a quantitative rubric to every skill execution.
Most valuable in **high-side-effect cloud operations** (delete, stop, restore, IAM/KMS/DDL) where a single
mistake is unrecoverable.

| GAN (real) | GCL (this spec) |
|---|---|
| Discriminator learns sample distribution | Critic scores an **explicit rubric** |
| No termination condition | Must terminate: **PASS / MAX_ITER / SAFETY_FAIL** |
| G and D train in parallel | G and C run **sequentially** |
| Goal: "fool the D" | Goal: "pass the rubric threshold" |

### 2. Roles

| Role | Job | Input | Output | Forbidden |
|---|---|---|---|---|
| **Generator (G)** | Execute the cloud operation | user request + previous Critic feedback | result + execution trace | modifying the rubric; self-scoring |
| **Critic (C)** | Independently audit G's output | G's result + trace + rubric | scores + suggestions | calling jdc / SDK / mutating anything |
| **Orchestrator (O)** | Loop control, termination, final return | context + C scores + budget | continue / final result | executing or scoring on its own |

**Hard constraint:** G and C MUST live in **isolated prompt contexts** (preferably isolated sessions
or sub-agents). A shared context is a "pseudo-GCL" and is explicitly banned — see §9.

### 3. Rubric (mandatory per skill)

Each `SKILL.md` MUST declare its skill-specific rubric. Minimum 5 dimensions:

| Dimension | Meaning | Scale | Default threshold |
|---|---|---|---|
| **Correctness** | Resource id / state / config actually matches the request | 0 / 0.5 / 1 | ≥ 0.5 (1.0 required for `delete` / `stop` / IAM / KMS / DDL) |
| **Safety** | Destructive op (`delete` / `stop` / `restore` / IAM / KMS / DDL) was confirmed or guarded | 0 / 1 | = 1 |
| **Idempotency** | Retrying the same call will not cause duplicate side-effects | 0 / 0.5 / 1 | ≥ 0.5 |
| **Traceability** | Output is auditable: command, params, raw response, errors all captured | 0 / 0.5 / 1 | ≥ 0.5 |
| **Spec Compliance** | Conforms to the skill's `core-concepts.md` constraints | 0 / 0.5 / 1 | ≥ 0.5 |

**Safety = 0 → ABORT immediately, regardless of total score.**

### 4. Loop Flow

```
User Request
     │
     ▼
[0] Pre-flight (Orchestrator)
    - resolve env.* and user.* variables
    - pick skill, load its rubric
     │
     ▼
[1] Generate (G) ───────────────────────┐
    - run jdc / SDK                     │
    - capture trace                     │
     │                                  │
     ▼                                  │
[2] Critique (C)                       │
    - isolated prompt context           │
    - score every rubric dimension      │
    - emit actionable suggestions       │
     │                                  │
     ▼                                  │
[3] Decide (Orchestrator)              │
    - Safety=0  → ABORT (no partial)   │
    - all pass  → RETURN                │
    - else & iter<max → inject         │
       suggestions into G               │
    - else → RETURN best + unresolved   │
       rubric items                     │
     └──────────────────────────────────┘
```

### 5. Termination (first match wins)

| Condition | Behavior |
|---|---|
| **PASS** | Every rubric dimension meets its threshold → return G's result |
| **MAX_ITER** | Reached `max_iterations` (default 3) → return **best-so-far** + unresolved rubric items |
| **SAFETY_FAIL** | Safety = 0 → **ABORT**; never return partial or "best-effort" output |

`max_iterations` defaults per skill class — see §8.

### 6. Trace & Audit (mandatory)

Every GCL run MUST persist a JSON trace:

```json
{
  "skill": "jdcloud-vm-ops",
  "request": "<sanitized user request>",
  "rubric_version": "v1",
  "iterations": [
    {
      "iter": 1,
      "generator": { "command": "...", "args": {...}, "exit_code": 0, "result_excerpt": "..." },
      "critic": {
        "scores": {
          "correctness": 1, "safety": 1, "idempotency": 0.5,
          "traceability": 1, "spec_compliance": 1
        },
        "suggestions": ["..."],
        "blocking": false
      },
      "decision": "RETRY"
    }
  ],
  "final": { "status": "PASS", "iter": 2, "output": "..." }
}
```

Path: `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` — unified with the existing
`audit-results/` directory used by `jdcloud-audit-ops` and `jdcloud-tag-audit-ops`.

### 7. Prompt Templates (mandatory per skill)

Each skill's `references/prompt-templates.md` MUST contain:

1. **Generator Prompt Template** — placeholders: `{{user.request}}`, `{{output.critic_feedback}}`, `{{output.rubric}}`
2. **Critic Prompt Template** — placeholders: `{{output.generator_output}}`, `{{output.trace}}`, `{{output.rubric}}`

> **Placeholder syntax** MUST follow the repository-wide convention
> (see top-level **Variable Convention**): `{{env.*}}` / `{{user.*}}` / `{{output.*}}`.
> Bare `{...}` placeholders are NOT allowed in skill prompt templates.

**Critic prompt must hide the raw user request** to prevent "answer-aligned" rubber-stamping.
Recommended skeleton:

```text
You are an independent cloud-operation auditor.
You will see one execution result and its trace. Score it STRICTLY against the rubric below.
Do NOT consider the original user request — judge only what was actually done.

rubric: {{output.rubric}}
generator_output: {{output.generator_output}}
trace: {{output.trace}}

Return strict JSON:
{
  "scores": { "correctness": 0|0.5|1, "safety": 0|0.5|1, "idempotency": 0|0.5|1,
              "traceability": 0|0.5|1, "spec_compliance": 0|0.5|1 },
  "suggestions": ["≤ 3 concrete, executable improvements"],
  "blocking": true|false
}
```

### 8. Per-Skill Defaults

| Skill | GCL | Default max_iter | Notes |
|---|---|---|---|
| `jdcloud-vm-ops` | **required** | 2 | delete/stop are destructive |
| `jdcloud-redis-ops` | **required** | 2 | flushall / instance delete |
| `jdcloud-mysql-ops` | **required** | 2 | DROP / DELETE / TRUNCATE |
| `jdcloud-postgresql-ops` | **required** | 2 | DROP / DELETE / TRUNCATE |
| `jdcloud-mongodb-ops` | **required** | 2 | dropDatabase / delete |
| `jdcloud-elasticsearch-ops` | **required** | 2 | delete index / cluster |
| `jdcloud-iam-ops` | **required** | 2 | detach policy / delete role / rotate keys |
| `jdcloud-kms-ops` | **required** | 2 | schedule key deletion is irreversible |
| `jdcloud-eip-ops` | **required** | 2 | release EIP can break production |
| `jdcloud-clb-ops` | recommended | 3 | listener / backend delete |
| `jdcloud-cloudmonitor-ops` | recommended | 3 | alarm rule delete |
| `jdcloud-alert-intelligence` | optional | 5 | read-only |
| `jdcloud-oss-ops` | recommended | 3 | delete bucket / delete object / set public ACL |
| `jdcloud-audit-ops` | optional | 5 | read-only |
| `jdcloud-tag-audit-ops` | optional | 5 | read-only |
| `jdcloud-skill-generator` | optional | 3 | meta operation |

Each skill may override `max_iter` in its own `SKILL.md` (under `## Quality Gate`).

### 9. Anti-Patterns (banned)

- ❌ **Shared context G+C** — defeats independence → banned
- ❌ **Subjective scoring** — Critic must use the rubric, not "vibes" → banned
- ❌ **Unbounded loop** — always hard-cap iterations → banned
- ❌ **Critic sees the user request** — encourages rubber-stamping → banned
- ❌ **Silently downgrade on Safety fail** — must ABORT visibly → banned
- ❌ **Trace not persisted** — no post-mortem possible → banned
- ❌ **Critic mutates resources** — Critic is read-only by definition → banned

### 10. Rollout Roadmap

- **Phase 1 (this commit)** — add this section to `AGENTS.md`; pilot on **`jdcloud-vm-ops` only** (most representative
  destructive workload) with its `prompt-templates.md` and `rubric.md`. `jdcloud-redis-ops` follows in the next PR.
- **Phase 2** — add `scripts/gcl_runner.py` as a reusable Orchestrator
- **Phase 3** — feed `gcl-trace-*.json` into `jdcloud-audit-ops` for quality dashboards
- **Phase 4** — wire rubric pass-rate to Cloud Monitor alarms (real incidents refine thresholds)

### 11. Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-06-04 | Initial GCL specification added to AGENTS.md (Correctness threshold relaxed to ≥0.5; pilot scoped to `jdcloud-vm-ops`) |
| 1.1.0 | 2026-06-04 | `jdcloud-redis-ops` rollout: added `references/rubric.md` and `references/prompt-templates.md`; `## Quality Gate (GCL)` chapter inserted; per-op Safety rules for spec-shrink and cross-instance restore |
| 1.2.0 | 2026-06-04 | `jdcloud-mysql-ops` rollout: rubric expanded to cover DDL/DML paths (instance-level + SQL-level); WHERE-clause check and DDL confirm gates added; prompt templates include pre-check + transaction + affected_rows rules |
| 1.3.0 | 2026-06-04 | `jdcloud-postgresql-ops` rollout: rubric + prompts cover instance + DDL/DML/maintenance paths; PG-specific rules for `VACUUM FULL`, `DROP SCHEMA` cascade, `SELECT FOR UPDATE` re-score |
| 1.3.1 | 2026-06-04 | `jdcloud-mongodb-ops` rollout: rubric + prompts cover instance + DB-level paths; MongoDB-specific rules for `dropDatabase` cascade, `updateMany` empty-filter check, `$out`/`$merge` in aggregate |
| 1.3.2 | 2026-06-04 | `jdcloud-elasticsearch-ops` rollout: rubric + prompts cover instance + ES REST paths; ES-specific rules for wildcard `DELETE /<index>`, `match_all` in `_update_by_query`/`_delete_by_query`, `_forcemerge max_num_segments=1` |
| 1.4.0 | 2026-06-04 | `jdcloud-iam-ops` rollout: rubric + prompts cover sub-user, group, role, policy, access-key, STS; IAM-specific rules for `attach AdministratorAccess` / `*:*`, `create main-account key`, `delete sub-user` with attached policies, `Principal: *` trust policy; **secret value never logged** |
| 1.4.1 | 2026-06-04 | `jdcloud-kms-ops` rollout: rubric + prompts cover key lifecycle, encrypt/decrypt, secret; KMS-specific rules for irreversible `schedule key deletion`, `pending-window-in-days` min-7 guard, prod `disable` / `decrypt` confirm; **plaintext / secret value never logged** (SHA-256 + length only) |
| 1.4.2 | 2026-06-04 | `jdcloud-eip-ops` rollout: rubric + prompts cover allocate, associate, dissociate, release; EIP-specific rules for irreversible `release EIP` (InUse refusal), prod `dissociate` / `release` confirm, `associate` force-rebind guard |
| 1.5.0 | 2026-06-04 | `jdcloud-clb-ops` rollout (recommended, max_iter=3): rubric + prompts cover LB, listener, target register/deregister, health check; CLB-specific rules for `delete-lb` traffic cut, `deregister-targets` >50% DRAIN guard, `register-targets` non-running backend refusal |
| 1.5.1 | 2026-06-04 | `jdcloud-cloudmonitor-ops` rollout (recommended, max_iter=3): rubric + prompts cover alarm rule CRUD + metric query; silent-failure guards for `delete-alarm-rule` / `disable-alarm-rule`, `DELETE_AFTER_FIRING` rule, prod tag double-confirm, empty notification channel refusal |
| 1.6.0 | 2026-06-04 | `jdcloud-alert-intelligence` rollout (optional, max_iter=5, read-only): rubric enforces "report must NOT recommend delete/disable/modify on alert rule" + 4-tuple citation + next-hop suggestion; PII / secret mask |
| 1.6.1 | 2026-06-04 | `jdcloud-audit-ops` rollout (optional, max_iter=5, read-only): rubric + prompts cover `describe-events` / `describe-event-detail` / `describe-trails`; PII masking guard for `requestParameters` (password / secret / accessKey) |
| 1.6.2 | 2026-06-04 | `jdcloud-tag-audit-ops` rollout (optional, max_iter=5): rubric + prompts cover audit + report + DOPS ticket creation; DOPS ticket payload completeness + duplicate-ticket idempotency check |
| 1.6.3 | 2026-06-04 | `jdcloud-skill-generator` rollout (optional, max_iter=3, meta): rubric + prompts cover generation steps; secret-leak guard, OpenSpec + 2-round self-review enforcement, jdc CLI / SDK cross-validation |
| 1.7.0 | 2026-06-08 | `jdcloud-oss-ops` rollout: SDK-only SKILL.md (OSS not exposed via `jdc` CLI); rubric + prompts cover bucket CRUD, object CRUD, ACL, lifecycle, versioning, CRR, presigned URL; safety gates for delete bucket/object, public ACL on prod |

### 12. See also

- [`docs/GCL_RETROSPECTIVE.md`](docs/GCL_RETROSPECTIVE.md) — post-rollout retrospective and Phase 3 dashboard design contract (2026-06-04)
- Each skill's `references/rubric.md` — the rubric instance
- Each skill's `references/prompt-templates.md` — the G/C/O prompt skeletons