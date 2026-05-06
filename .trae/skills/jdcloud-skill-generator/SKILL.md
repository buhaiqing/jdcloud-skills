---
name: jdcloud-skill-generator
description: >-
  Use when adding or scaffolding a new JD Cloud operational Agent Skill under
  `jdcloud-*-ops` in this repository, regenerating structure from official docs
  or OpenAPI, or aligning an existing ops skill to the API/SDK template and P0/P1
  bar. Not for executing live changes against a JD Cloud account.
license: MIT
compatibility: >-
  Access to JD Cloud official documentation, OpenAPI/Swagger for the product,
  `jdcloud-skill-generator/references/jdcloud-skill-template.md`,
  `references/governance-and-adversarial-review.md`, and agentskills.io
  frontmatter conventions.
metadata:
  author: jdcloud
  version: "1.4.0"
  last_updated: "2026-05-03"
  runtime: Harness AI Agent, Claude Code, Cursor, or compatible Agent runtimes
  type: meta-skill
---

# JD Cloud Skill Generator (Meta-Skill)

## Overview

This **meta-skill** defines **how** to author a new **product-scoped** operational skill (e.g. `jdcloud-rds-ops`) **inside this repo**. It does **not** perform maintenance against a user’s cloud account. Live work uses the generated **`jdcloud-[product]-ops`** skills (official **SDK/API** and, when applicable, official **`jdc` CLI**).

**Repository scope:** All generated layout and policies apply **only** to the `jdcloud-skills` monorepo unless explicitly stated otherwise elsewhere.

**Execution surface — dual path when CLI exists:** For every **new or materially updated** ops skill, you **MUST** document **SDK/API** (or direct REST per OpenAPI) **and** **`jdc`** for **every operation** that the official CLI exposes for this product. If the CLI supports **only a subset** of API operations, you **MUST** still document **full** SDK/API coverage in `references/api-sdk-usage.md` and **`jdc` for the subset** in `references/cli-usage.md`, with an explicit **coverage gap** table (which flows are SDK-only). **Console click-paths** are not an agent execution surface in `SKILL.md` except brief optional notes in `references/troubleshooting.md`. All `jdc` examples MUST be **machine-parseable** (`--output json` or equivalent), **non-interactive** where supported, and **verified** against real CLI output for JSON paths. Semantics MUST stay consistent with **OpenAPI/official API docs**—see [governance-and-adversarial-review.md](references/governance-and-adversarial-review.md).

**SDK-only exception:** Allowed **only** when the **official** JD Cloud CLI does **not** ship commands for this product. The skill **MUST** contain a short **“CLI applicability”** subsection (e.g. under Overview or Prerequisites) stating that fact and citing **evidence** (e.g. `jdc help` product list, official CLI README, or doc URL). Reviewers **MUST** accept that evidence before merge.

**Core principle:** Generated skills are **agent-readable runbooks**: triggers, env vs user placeholders, pre-flight → execute → validate → recover, safety gates, and outputs **grounded in OpenAPI and verified SDK and (when applicable) CLI behavior**, not guessed.

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

6. **Dual-path readiness**  
   - Confirm whether **`jdc` supports this product** (official CLI docs / `jdc <product> --help`). If yes, plan **both** `api-sdk-usage.md` and `cli-usage.md` and **parallel** execution subsections in `SKILL.md` for each documented operation. If no, prepare **SDK-only** text plus **CLI applicability** evidence for the exception.

## Input Requirements (from Requester)

1. **Product name** (English; Chinese/aliases in Trigger & Scope if useful for matching user wording).  
2. **Primary resource type** and **API service** identifier (as in OpenAPI tags or SDK package).  
3. **Official documentation URL(s)**.  
4. **OpenAPI/Swagger URL or path** (**strongly recommended**; required to claim API-accurate fields and error mapping).  
5. **Operation list** (create, describe, modify, delete, list, product-specific).  
6. **SDK language/runtime** if not Python (default examples in template are Python).  
7. **CLI support verdict:** Does official **`jdc`** expose this product? If **yes**: CLI product slug, link or command used to confirm, and note any **partial** CLI coverage vs OpenAPI. If **no**: evidence for the **SDK-only exception** (see above).

## Generation Process

### Step 0: Environment Setup

Before analyzing sources, the Agent MUST ensure environment variables are available for SDK/CLI validation during Skill generation.

#### Environment Variable Sources (Priority Order)

| Priority | Source | Description |
|----------|--------|-------------|
| 1 (highest) | Shell environment | Explicitly set `export JDC_ACCESS_KEY=...` |
| 2 | `.env` file | Project root or custom path via parameter |
| 3 (lowest) | Default values | `JDC_REGION=cn-north-1` only |

#### `.env` File Support

For local development convenience, the Agent MAY load environment variables from a `.env` file:

**Location options:**
- **Working directory (cwd)**: Agent Runtime's current working directory (recommended for cross-project mixing)
- Project root: `/path/to/jdcloud-skills/.env` (when working within this repo)
- Custom path: User specifies via `--env-file` parameter

> **Cross-project mixing:** When using JD Cloud Skills in other projects (e.g., mixing with Aliyun/AWS Skills), place `.env` in the **working directory** of that project. All Skills share the same environment variables loaded by Agent Runtime.

**Format (INI-style):**
```ini
# JD Cloud credentials
JDC_ACCESS_KEY=your_access_key_here
JDC_SECRET_KEY=your_secret_key_here
JDC_REGION=cn-north-1

# Optional: CLI configuration
JDC_CLI_OUTPUT=json
```

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

#### Dual-Path Support (CLI and SDK)

The `.env` file supports both execution modes:

- **CLI mode**: Agent Runtime loads `.env` and passes vars to `jdc` commands
- **SDK mode**: Agent Runtime loads `.env` and injects into `os.environ` for SDK calls

Both modes share the same credential source, ensuring consistency.

#### Safety Rules (Per Governance)

- **NEVER** commit `.env` files to version control (already in `.gitignore`)
- **NEVER** write `.env` values into generated Skill documents
- Generated Skills continue using `{{env.*}}` placeholders
- `.env` is for **local development convenience only**, not production

#### Verification

After loading, the Agent SHOULD verify credentials before proceeding to Step 1:
```bash
# Quick CLI validation
jdc vm describe-instance-types --region-id cn-north-1 --output json --page-number 1 --page-size 1
```

If validation fails:
- HALT with clear message: "Credentials invalid or network unreachable"
- Suggest: Check `.env` file or run `jdc config init`

### Step 1: Analyze sources

Extract:

- Operations, parameters, enums, errors, and **response schemas** from OpenAPI.
- When `jdc` applies: **full** command map vs SDK operation list; flag parity; **actual JSON** shape per command (may differ from raw API—verify).
- Async behavior (polling, terminal states) from docs or API patterns.
- Metrics/alarm dimensions if monitoring is in scope.
- **Delegation** targets (monitoring, VPC, LB, billing).

### Step 2: Create directory layout

```text
jdcloud-[product]-ops/
├── SKILL.md
├── references/
│   ├── core-concepts.md
│   ├── api-sdk-usage.md
│   ├── cli-usage.md          # required if jdc supports this product; omit only under SDK-only exception (documented)
│   ├── troubleshooting.md
│   ├── monitoring.md
│   └── integration.md
└── assets/
    └── example-config.yaml
```

Add **`references/idempotency-checklist.md`** when retries or automation require documented idempotent behavior (pattern: `jdcloud-vpc-ops/references/idempotency-checklist.md`).

### Step 3: Populate `SKILL.md` from template

Base: [jdcloud-skill-template.md](references/jdcloud-skill-template.md).

Replace placeholders and **wire JSON paths / SDK calls / `jdc` invocations** to verified OpenAPI and **measured** CLI output where applicable. Generic examples in the template are not authoritative.

### Step 4: Fill reference files

- **core-concepts.md** — Architecture, limits, regions, quotas.  
- **api-sdk-usage.md** — Operation map, required fields, pagination, example request/response snippets (**no secrets**).  
- **cli-usage.md** — **Required** when `jdc` supports this product: command cheat sheet, `--output json`, non-interactive flags, **CLI–API coverage gap** table if CLI is partial, and **documented JSON paths** (verify with a real run). Omit **only** under the documented **SDK-only exception**.  
- **troubleshooting.md** — API/CLI error codes, ordered diagnostics.  
- **monitoring.md** — Metrics, dashboards, alerts.  
- **integration.md** — SDK install pins, **`jdc` install/config** when CLI applies (required for dual-path skills), env vars, optional MCP notes.

### Step 5: Frontmatter and versioning

- `name` matches the directory.  
- **`description`** on the **ops** skill: third person, **when to use** only (triggers); do not summarize the full workflow ([OpenSpec](https://agentskills.io/specification)).  
- Bump `metadata.version` and `last_updated`; update **Changelog** in `SKILL.md`.

### Step 6: Verify

- Complete **P0/P1** below.  
- Run **[governance adversarial scenarios](references/governance-and-adversarial-review.md#minimal-adversarial-scenarios)** (mentally or with a fresh agent context) and patch gaps.

## Governance (Expert Recommendation)

**Minimal adversarial review** gives high return for low cost: it catches destructive-action shortcuts, credential leaks in instructions, and API hallucination **before** merge. Treat [governance-and-adversarial-review.md](references/governance-and-adversarial-review.md) as the **reviewer companion** to this meta-skill: pre-merge checklist + seven short scenarios. Expand scenarios only when a skill adds high-risk operations (public exposure, data export, production traffic mutation).

Optional later improvements (not required to start): PR template checkbox linking to that doc; periodic check that CLI-documented skills stay aligned with OpenAPI when APIs change.

## Agent-Ready Quality Checklist

### P0 — MUST PASS

- [ ] **Trigger & Scope** with SHOULD-use / SHOULD-NOT-use and delegation.  
- [ ] **Variables:** `{{env.*}}` vs `{{user.*}}`; no secret literals.  
- [ ] **Flows:** Pre-flight → Execute → Validate → Recover for **each** critical operation; **each** flow documents **SDK/API** and, when `jdc` supports it, **parallel `jdc`** (or explicit **SDK-only** exception with evidence).  
- [ ] **Failure recovery:** HALT vs retry; throttling; non-retryable business errors.  
- [ ] **API fidelity:** Fields and paths traceable to OpenAPI/SDK for the stated version.  
- [ ] **Dual-path completeness:** If the product has official `jdc` support: `references/cli-usage.md` present; `SKILL.md` execution sections include **both** SDK and `jdc` for every CLI-covered operation; partial CLI documented with a **gap** table.  
- [ ] **CLI fidelity (when `jdc` applies):** Subcommands/flags match official CLI docs; JSON paths **verified** with a real `--output json` run.  
- [ ] **Safety gates** for destructive operations (before **each** documented path: SDK **and** `jdc` when dual-path).  
- [ ] **Timeouts** for polling and long-running operations (state for **each** path or shared semantics).  
- [ ] **CLI quality (when `jdc` applies):** `--output json` (or equivalent), non-interactive where supported, no console-only primary flows in `SKILL.md`.

### P1 — SHOULD PASS

- [ ] **Chaining:** Stable output fields for downstream skills.  
- [ ] **Naming:** `jdcloud-[product]-ops` consistent with repo.  
- [ ] **Pinned** SDK/API baseline where drift matters.  
- [ ] **Idempotency** or duplicate-resource behavior documented when automation applies.  
- [ ] **Adversarial scenarios** considered using the governance doc.  
- [ ] **Path preference:** When dual-path, `SKILL.md` states when to prefer SDK vs `jdc` if non-obvious.  
- [ ] **Metadata:** Ops skill frontmatter includes `cli_applicability` and `cli_support_evidence` per template.

## Example Request

> Add a JD Cloud skill for Cloud Monitor in this repo: alarms, metric query, dashboards. Docs: `https://docs.jdcloud.com/cn/cloudmonitor`. OpenAPI: [URL]. Python SDK.

**Expected output:** `jdcloud-cloudmonitor-ops` tree (or extend if present) with **real** operationIds, SDK types, response paths, **and** matching `jdc` commands if the CLI supports the product (otherwise SDK-only with **CLI applicability** evidence).

## See Also

- [Skill template](references/jdcloud-skill-template.md)  
- [Governance & adversarial review](references/governance-and-adversarial-review.md)  
- [JD Cloud CLI](https://github.com/jdcloud-api/jdcloud-cli)  
- [Agent Skills Open Specification](https://agentskills.io/specification)  
- Example ops skills (target: dual-path where CLI exists): `jdcloud-vm-ops`, `jdcloud-vpc-ops`, `jdcloud-clb-ops`, `jdcloud-redis-ops`, `jdcloud-cloudmonitor-ops`  
- Idempotency pattern: `jdcloud-vpc-ops/references/idempotency-checklist.md`
