---
name: jdcloud-skill-generator
description: >-
  Use when the user wants to create, scaffold, standardize, refactor, or
  regenerate a JD Cloud operational skill (jdcloud-*-ops); update an existing
  skill to match the latest OpenAPI, jdc CLI, or SDK changes; or verify a skill
  against the P0/P1 quality bar. Also use when the user mentions jdc CLI,
  jdcloud_sdk, OpenAPI, skill templates, or asks to add a new JD Cloud product
  to the skill repository — even if they do not explicitly say 'skill' or
  'scaffold'. Do not use for live operational execution against a JD Cloud
  account; use the generated jdcloud-[product]-ops skill instead.
license: MIT
compatibility: >-
  Access to JD Cloud official documentation, OpenAPI/Swagger for the product,
  `jdcloud-skill-generator/references/jdcloud-skill-template.md`,
  `references/governance-and-adversarial-review.md`, and agentskills.io
  frontmatter conventions.
metadata:
  author: buhaiqing
  version: "1.6.0"
  last_updated: "2026-06-04"
  runtime: Harness AI Agent, Claude Code, Cursor, or compatible Agent runtimes
  type: meta-skill
---

# JD Cloud Skill Generator (Meta-Skill)

## Overview

This **meta-skill** defines **how** to author a new **product-scoped** operational skill (e.g. `jdcloud-rds-ops`) **inside this repo**. It does **not** perform maintenance against a user's cloud account. Live work uses the generated **`jdcloud-[product]-ops`** skills (official **`jdc` CLI** with **SDK/API fallback**).

**Repository scope:** All generated layout and policies apply **only** to the `jdcloud-skills` monorepo unless explicitly stated otherwise elsewhere.

**Execution surface — jdc-first with fallback:** For every **new or materially updated** ops skill, the Agent MUST attempt to use the **`jdc` CLI** as the primary execution path. If `jdc` installation or command execution fails, the Agent MUST retry up to **3 times** (with exponential backoff). Only after **3 consecutive failures** should the Agent fall back to **SDK/API** (or direct REST per OpenAPI). Both paths MUST be documented so that either is executable depending on environment readiness. **Console click-paths** are not an agent execution surface in `SKILL.md` except brief optional notes in `references/troubleshooting.md`. Semantics MUST stay consistent with **OpenAPI/official API docs**—see [governance-and-adversarial-review.md](references/governance-and-adversarial-review.md).

**Core principle:** Generated skills are **agent-readable runbooks**: triggers, env vs user placeholders, pre-flight → execute → validate → recover, safety gates, and outputs **grounded in OpenAPI and verified CLI/SDK behavior**, not guessed.

## Role Boundary (Agent-Readable)

| This meta-skill **does** | This meta-skill **does not** |
|--------------------------|------------------------------|
| Choose **extend** vs **new** `jdcloud-[product]-ops` | Replace deep product knowledge already in an existing ops skill |
| Scaffold `SKILL.md`, `references/*`, `assets/*` from the template | Call JD Cloud APIs on behalf of the user |
| Enforce naming, frontmatter, P0/P1, delegation, and **governance** hooks | Invent request/response fields or CLI flags without official doc verification |
| Point authors to **adversarial review** before merge | Store or echo real credentials |

If the user wants **operational execution** (e.g. “create a resource”), load the appropriate **`jdcloud-*-ops`** skill for that product—not this generator.

## When to Use This Skill

- A new JD Cloud product needs a **first** ops skill in **this repo**.
- An existing skill lacks P0 elements (triggers, placeholders, flows, recovery, destructive gates).
- OpenAPI or official docs changed; the skill should be **realigned** (bump version/changelog).
- A contributor needs the **standard directory layout** for a new `jdcloud-[product]-ops`.

## When **Not** to Use

- One-off debugging with no intent to maintain a reusable skill.
- Non–JD-Cloud application work.
- You only need billing/IAM execution—use dedicated ops skills when they exist; this meta-skill **authors** skills, it does not bypass them.

## Before You Generate: Decisions

1. **Extend vs new directory**  
   - **Extend** same product and resource model (new operation section, paths, troubleshooting rows).  
   - **New** `jdcloud-[product]-ops` when the **service/API surface** or **primary resource** is distinct (e.g. load balancer vs VM).

2. **Naming**  
   - Pattern: `jdcloud-[product]-ops` (lowercase, hyphenated). Search the repo for collisions.

3. **Dependencies**  
   - Cross-product chains: document **delegation** in Trigger & Scope; avoid duplicating another product’s full flows.

4. **Sources of truth**  
   - **OpenAPI + official docs** beat forums and chat logs. Pin an **API/SDK profile** in skill `metadata` or `references/integration.md`.

5. **Secrets**  
   - Only `{{env.*}}` **names** and documentation; never real keys or customer data.

6. **Dual-path readiness (jdc-first with fallback)**  
   - The **primary** execution path is the **`jdc` CLI**. The Agent MUST attempt `jdc` setup and execution first.  
   - If `jdc` installation/execution fails after **3 retries**, fall back to the **JD Cloud Python SDK** (`jdcloud_sdk`).  
   - Both paths (`jdc` + SDK/API) MUST be documented in the generated skill so either is executable.  
   - Verify the SDK package name for the target product. If unknown, check PyPI or JD Cloud SDK documentation.

## Input Requirements (from Requester)

1. **Product name** (English; Chinese/aliases in Trigger & Scope if useful for matching user wording).  
2. **Primary resource type** and **API service** identifier (as in OpenAPI tags or SDK package).  
3. **Official documentation URL(s)**.  
4. **OpenAPI/Swagger URL or path** (**strongly recommended**; required to claim API-accurate fields and error mapping).  
5. **Operation list** (create, describe, modify, delete, list, product-specific).  
6. **SDK language/runtime** if not Python (default examples in template are Python).  
7. **CLI support evidence:** Confirm the official **`jdc`** product slug (via `jdc <product> --help` or CLI docs). If `jdc` does not support this product, note the **SDK-only** gap for the fallback path.

## Generation Process

### Step 0: Environment Setup

Before analyzing sources, the Agent MUST ensure a working execution environment. The setup follows a **jdc-first with fallback** strategy:

1. **Attempt `jdc` CLI setup** via `uv` (primary path)
2. On failure, **retry up to 3 times** with exponential backoff
3. After **3 consecutive failures**, fall back to **SDK-only** setup

#### Python Runtime (uv)

Both `jdc` CLI and the JD Cloud Python SDK require a Python runtime. Use **`uv`** for local, isolated, and **idempotent** environment management. Every command below is safe to re-run — designed for zero side effects on repeated execution.

**Install uv (system-wide, one-time per machine):**
```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via Homebrew
brew install uv

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

> **Note:** Installing uv itself is a one-time system setup. The commands below (`uv venv`, `uv pip install`) are **idempotent** and safe to re-run.

> **Python 3.10 is REQUIRED, NOT 3.12.** `jdcloud_cli==1.2.12` uses `SafeConfigParser` which was removed in Python 3.12. Always use `uv venv --python 3.10`. If Python 3.10 is unavailable, install it via `brew install python@3.10` (macOS) or `uv python install 3.10`.

#### Phase 1: jdc CLI Setup (Primary Path)

**Create and activate a local virtual environment (idempotent):**
```bash
# From the skill directory root — creates .venv if not exists
uv venv --python 3.10

# Activate (required per shell session)
# macOS / Linux:
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate
```

> `uv venv` is **idempotent**: re-running on an existing `.venv` is a safe no-op. Include it in every bootstrap script without guards.

**Install jdc CLI and JD Cloud SDK (idempotent):**
```bash
uv pip install jdcloud_cli jdcloud_sdk
```

> `uv pip install` against an existing environment is **idempotent**: already-satisfied packages are skipped; only missing or outdated packages are touched.

**One-shot bootstrap (copy-paste ready, fully idempotent):**
```bash
uv venv --python 3.10
source .venv/bin/activate
uv pip install jdcloud_cli jdcloud_sdk
jdc --version
```

**Verification after bootstrap:**
```bash
source .venv/bin/activate
jdc --version
python -c "import jdcloud_sdk; print('SDK OK')"
```

##### Retry Logic (Up to 3 Attempts)

If `jdc --version` or any `jdc` command fails, use the following retry procedure:

```bash
# Retry 1: re-run pip install
uv pip install jdcloud_cli jdcloud_sdk
jdc --version && echo "OK" || echo "FAIL"

# Wait 2 seconds, then Retry 2
sleep 2
uv pip install --force-reinstall jdcloud_cli
jdc --version && echo "OK" || echo "FAIL"

# Wait 4 seconds, then Retry 3
sleep 4
uv pip install --force-reinstall jdcloud_cli jdcloud_sdk
jdc --version && echo "OK" || echo "FAIL"
```

> Exponential backoff: retry 1 (instant) → retry 2 (2s delay) → retry 3 (4s delay).

If all **3 retries** fail, proceed to **Phase 2: SDK Fallback**.

**Phase 1 failure message:**
```
jdc CLI setup failed after 3 attempts. Falling back to SDK-only mode.
```

#### Phase 2: SDK Fallback (After 3 jdc Failures)

When `jdc` is unavailable after retries, set up the SDK-only environment:

```bash
# Ensure SDK is installed (jdc may be partially installed; SDK should still work)
uv venv --python 3.10
source .venv/bin/activate
uv pip install jdcloud_sdk
python -c "import jdcloud_sdk; print('SDK OK')"
```

**Verification after fallback:**
```bash
source .venv/bin/activate
python -c "import jdcloud_sdk; print('SDK OK')"
```

If SDK verification also fails:
- HALT with clear message: "uv Python environment setup failed"
- Suggest: Check `uv --version`, Python 3.10+ availability, and network access to PyPI

#### Environment Variable Sources (Priority Order)

| Priority | Source | Description |
|----------|--------|-------------|
| 1 (highest) | Shell environment | SDK mode only. CLI mode does NOT read env vars. |
| 2 | `.env` file | Project root or custom path via parameter |
| 3 (lowest) | Default values | `JDC_REGION=cn-north-1` only |

> **CRITICAL: CLI vs SDK credential handling differs.** The `jdc` CLI reads credentials exclusively from `~/.jdc/config` (INI format). Environment variables `JDC_ACCESS_KEY` / `JDC_SECRET_KEY` are **ignored** by the CLI. The SDK (fallback path) reads credentials from environment variables. See `Critical jdc CLI Behavioral Notes` below for details and sandbox workaround.

#### `.env` File Support

For local development convenience, the Agent MAY load environment variables from a `.env` file:

**Location options:**
- **Working directory (cwd)**: Agent Runtime's current working directory (recommended for cross-project mixing)
- Project root: `/path/to/jdcloud-skills/.env` (when working within this repo)
- Custom path: User specifies via `--env-file` parameter

> **Cross-project mixing:** When using JD Cloud Skills in other projects (e.g., mixing with Aliyun/AWS Skills), place `.env` in the **working directory** of that project. All Skills share the same environment variables loaded by Agent Runtime.

**Format (INI-style):**
```ini
# JD Cloud credentials (used by SDK mode)
JDC_ACCESS_KEY=your_access_key_here
JDC_SECRET_KEY=your_secret_key_here
JDC_REGION=cn-north-1
```

> **Note:** The `jdc` CLI does NOT read environment variables `JDC_ACCESS_KEY`/`JDC_SECRET_KEY`. The `.env` file is for SDK mode only. CLI credentials must be configured in `~/.jdc/config` INI file. See "Critical jdc CLI Behavioral Notes" below for details.

**Multi-cloud mixing (recommended namespace prefixes):**
```ini
# JD Cloud - use JDC_* prefix
JDC_ACCESS_KEY=...
JDC_SECRET_KEY=...
JDC_REGION=cn-north-1

# Aliyun - use ALIYUN_* prefix
ALIYUN_ACCESS_KEY_ID=...
ALIYUN_ACCESS_KEY_SECRET=...
ALIYUN_REGION=cn-hangzhou

# AWS - use AWS_* prefix (standard)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1
```

> **Namespace best practice:** Use platform-specific prefixes to avoid credential conflicts when mixing multiple cloud provider Skills.

**Priority rule:**
- Shell environment variables **MUST** override `.env` values
- Example: If `export JDC_REGION=cn-east-2` is set, use `cn-east-2` even if `.env` says `cn-north-1`

#### Loading Mechanism

**Python reference implementation (if Agent Runtime supports):**
```python
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env with priority: shell env > .env
env_file = Path.cwd() / '.env'
load_dotenv(env_file, override=False)  # False = shell env has priority

# Verify critical variables
required_vars = ['JDC_ACCESS_KEY', 'JDC_SECRET_KEY']
for var in required_vars:
    if not os.environ.get(var):
        raise EnvironmentError(f"Missing required environment variable: {var}")
```

#### Dual-Path Credential Support (CLI and SDK)

The `.env` file supports both execution modes:

- **CLI mode**: Agent Runtime loads `.env` and passes vars to `jdc` commands (primary path)
- **SDK mode**: Agent Runtime loads `.env` and injects into `os.environ` for SDK calls (fallback path)

Both modes share the same credential source, ensuring consistency across retry/fallback transitions.

#### Safety Rules (Per Governance)

- **NEVER** commit `.env` files to version control (already in `.gitignore`)
- **NEVER** write `.env` values into generated Skill documents
- Generated Skills continue using `{{env.*}}` placeholders
- `.env` is for **local development convenience only**, not production

#### Verification

After loading, the Agent SHOULD verify credentials before proceeding to Step 1:

```bash
# Primary: try jdc CLI validation
# NOTE: --output json MUST be placed BEFORE the subcommand (top-level argument)
jdc --output json vm describe-instance-types --region-id cn-north-1 --page-number 1 --page-size 1
```

If `jdc` validation fails, attempt retries per the **Retry Logic** above. After 3 failures, fall back to SDK credential check:

```bash
python -c "
import os
ak = os.environ.get('JDC_ACCESS_KEY')
sk = os.environ.get('JDC_SECRET_KEY')
# SECURITY: NEVER print the actual secret key value
if ak and sk:
    print('Credentials OK (SDK fallback mode)')
else:
    print('Missing JDC_ACCESS_KEY or JDC_SECRET_KEY')
    exit(1)
"
```

> **SECURITY WARNING:** The verification code above **ONLY checks for existence** of credentials. **NEVER** log, print, or expose `JDC_SECRET_KEY` (or any secret) in console output, debug messages, or logs. If you need to log credential status, use masked placeholders like `JDC_SECRET_KEY=<masked>` or `JDC_SECRET_KEY=***`. This rule applies to all execution paths (SDK, CLI, and any debugging scripts).

If all verification paths fail:
- HALT with clear message: "Credentials invalid or environment not set up"
- Suggest: Check `.env` file or run `uv venv` / `uv pip install jdcloud_cli jdcloud_sdk`

## Critical jdc CLI Behavioral Notes (Reproductive Evidence from Empirical Testing)

---

## Post-Generation Self-Check (生成后自检 — 宪章执行)

> **机制：生成完成后自动执行，不符合则循环修复直到通过。**
> **参考：** `references/governance-and-adversarial-review.md` §0 Charter

### Charter Compliance Checklist (强制执行)

| # | Check | Pass Criteria | Auto-Fix |
|---|-------|--------------|----------|
| C1 | Frontmatter | Starts with `---`, has `name`, `description`, `license`, `compatibility`, `metadata` | Add from jdcloud-skill-template.md |
| C2 | SHOULD/SHOULD NOT | Both trigger sections present | Add Trigger & Scope section |
| C3 | Trigger & Scope | Complete with product keywords | Add from template |
| C4 | CLI applicability | `cli_applicability` declared (dual-path/sdk-only) | Add CLI policy section |
| C5 | Variables | `{{env.JDC_*}}`, `{{user.*}}`, `{{output.*}}` | Add placeholder table |

> **自解流程**：C1-C5 失败 → HALT → REPORT → REMEDIATE → RE-CHECK → LOOP

---

## Governance (Expert Recommendation)

**Minimal adversarial review** gives high return for low cost: it catches destructive-action shortcuts, credential leaks in instructions, and API hallucination **before** merge. Treat [governance-and-adversarial-review.md](references/governance-and-adversarial-review.md) as the **reviewer companion** to this meta-skill: pre-merge checklist + seven short scenarios. Expand scenarios only when a skill adds high-risk operations (public exposure, data export, production traffic mutation).

Optional later improvements (not required to start): PR template checkbox linking to that doc; periodic check that CLI-documented skills stay aligned with OpenAPI when APIs change.

## Agent-Ready Quality Checklist

### P0 — MUST PASS

- [ ] **Trigger & Scope** with SHOULD-use / SHOULD-NOT-use and delegation.  
- [ ] **Variables:** `{{env.*}}` vs `{{user.*}}`; no secret literals.  
- [ ] **Flows:** Pre-flight → Execute → Validate → Recover for **each** critical operation; **each** flow documents **`jdc` as primary path** and **SDK/API as fallback**.  
- [ ] **Failure recovery:** HALT vs retry; throttling; non-retryable business errors.  
- [ ] **API fidelity:** Fields and paths traceable to OpenAPI/SDK for the stated version.  
- [ ] **jdc-first with fallback:** `references/cli-usage.md` present as primary path; `SKILL.md` execution sections include both `jdc` and SDK/API paths; explicit **3-retry fallback** documented.  
- [ ] **CLI fidelity:** Subcommands/flags match official CLI docs; JSON paths **verified** with a real `--output json` run.  
- [ ] **Safety gates** for destructive operations (before **each** documented path: `jdc` **and** SDK fallback).  
- [ ] **Timeouts** for polling and long-running operations.  
- [ ] **CLI quality:** `--output json` (MUST be top-level, BEFORE subcommand), no `--no-interactive` (does NOT exist), no console-only primary flows in `SKILL.md`.

### P1 — SHOULD PASS

- [ ] **Chaining:** Stable output fields for downstream skills.  
- [ ] **Naming:** `jdcloud-[product]-ops` consistent with repo.  
- [ ] **Pinned** SDK/API baseline where drift matters.  
- [ ] **Idempotency** or duplicate-resource behavior documented when automation applies.  
- [ ] **Adversarial scenarios** considered using the governance doc.  
- [ ] **Path preference:** `SKILL.md` states when to prefer `jdc` vs SDK fallback if non-obvious.  
- [ ] **Metadata:** Ops skill frontmatter includes appropriate metadata per template.

## Example Request

> Add a JD Cloud skill for Cloud Monitor in this repo: alarms, metric query, dashboards. Docs: `https://docs.jdcloud.com/cn/cloudmonitor`. OpenAPI: [URL]. Python SDK.

**Expected output:** `jdcloud-cloudmonitor-ops` tree (or extend if present) with **real** operationIds, SDK types, response paths, **and** matching `jdc` commands (primary path), plus SDK fallback documentation.

## Quality Gate (GCL)

> This skill participates in the repository-wide **Generator-Critic-Loop**
> (GCL) defined in [`AGENTS.md` §Quality Gate](../AGENTS.md#generator-critic-loop-gcl--adversarial-quality-gate).
> The quality gate is **optional** for this meta-skill (per `AGENTS.md` §8).

### Parameters (override `AGENTS.md` §8 defaults)

| Parameter | Value | Reason |
|---|---|---|
| `max_iterations` | **3** | `AGENTS.md` §8 default for `jdcloud-skill-generator` (optional, meta); generation is iterative and benefits from up to 3 retries |
| `rubric_version` | `v1` | see [rubric.md](references/rubric.md) |
| `trace_path` | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | unified with `jdcloud-audit-ops` |
| `safety_confirm_required` | **false** | output is the generated `*.md` content; the human user decides whether to commit |

### Loop overview

```
User request
   │
   ▼
[0] Orchestrator pre-flight  ──► load rubric, classify generation step
   │
   ▼
[1] Generator (G)            ──► jdc <product> --help (for verification)
   │
   ▼
[2] Critic (C)               ──► isolated context, blind to user request
   │
   ▼
[3] Orchestrator decider
   ├─ Safety=0 / blocking   → ABORT
   ├─ all pass              → RETURN
   ├─ iter<3 & not all pass → RETRY (inject suggestions)
   └─ iter=3 & not all pass → RETURN_BEST
```

### Artifacts

- Rubric (concrete scoring rules): [references/rubric.md](references/rubric.md)
- Prompt templates (G / C / O): [references/prompt-templates.md](references/prompt-templates.md)

### Integration with existing flows

The GCL **wraps** the `## Generation Process` (Step 0 + 5 steps) defined
above. The Generator (G) IS the existing generation agent. The Critic (C)
audits the generated `*.md` content for OpenSpec compliance, secret
leakage, and 2-round self-review completion. The Orchestrator (O) owns
the loop and persists the GCL trace.

### Generation-step-specific behavior

- **Step 0. Environment Setup** — Verifies Python 3.10 (not 3.12) and
  `uv` available. Never logs credentials.
- **Step 1. Source Analysis** — OpenAPI URL + jdc help output + SDK
  module list ALL captured in trace.
- **Step 2. Operation Mapping** — Every operationId mapped to a real
  jdc command + SDK method. Cross-checked against both sources.
- **Step 3. SKILL.md Generation** — Generated SKILL.md passes Agent
  Skill OpenSpec; **NEVER includes any `.env` value, secret key,
  access-key id/secret, password, or PII** (hard rule per
  `references/critical-jdc-cli-notes.md`).
- **Step 4. References Generation** — Generated `cli-usage.md` /
  `api-sdk-usage.md` / `core-concepts.md` / `troubleshooting.md` (at
  minimum) with verified commands and imports.
- **Step 5. Post-Generation Self-Check** — 2-round self-review per repo
  policy. Score 0 if fewer than 2 rounds were performed.

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.6.0 | 2026-06-04 | **GCL rollout (optional)**: Added `## Quality Gate (GCL)` chapter wiring this meta-skill into the repository-wide Generator-Critic-Loop. Added `references/rubric.md` (5-dimension rubric, secret-leak guard, OpenSpec + 2-round self-review enforcement) and `references/prompt-templates.md` (G/C/O prompt skeletons). `max_iterations=3`. `safety_confirm_required=false` (output is generated `*.md` content; the human user decides whether to commit). |
| 1.5.0 | 2026-05-06 | (pre-existing; details in repo history) |

## See Also

- [Skill template](references/jdcloud-skill-template.md)  
- [Governance & adversarial review](references/governance-and-adversarial-review.md)  
- [JD Cloud CLI](https://github.com/jdcloud-api/jdcloud-cli)  
- [Agent Skills Open Specification](https://agentskills.io/specification)  
- Example ops skills (jdc-first with SDK fallback): `jdcloud-vm-ops`, `jdcloud-vpc-ops`, `jdcloud-clb-ops`, `jdcloud-redis-ops`, `jdcloud-cloudmonitor-ops`  
- Idempotency pattern: `jdcloud-vpc-ops/references/idempotency-checklist.md`
