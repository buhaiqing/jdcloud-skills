# Skill Generator Rubric (GCL)

> Concrete instantiation of the **Generator-Critic-Loop** rubric defined in
> `AGENTS.md` §3 for `jdcloud-skill-generator`. This skill is a **meta
> operation** — it generates new Skill documents. Its output is the
> generated `SKILL.md` / `references/*.md` **content**; the human user
> decides whether to commit them.

## Rubric version

`v1` — see `AGENTS.md` §11.

## Dimensions

| # | Dimension | Weight | Threshold | Scale | Notes |
|---|---|---|---|---|---|
| 1 | **Correctness** | hard | ≥ 0.5; **= 1.0 required** for operation-id mapping, SDK import paths, jdc CLI command syntax | 0 / 0.5 / 1 | Verifies every claimed `operationId` matches the actual OpenAPI / SDK / jdc CLI. Verifies SDK import paths use the PascalCase module names (per `references/critical-jdc-cli-notes.md`). |
| 2 | **Safety** | hard | = 1 | 0 / 1 | **Hard rule**: the generated skill MUST NOT contain any `.env` value, secret key, access-key id/secret, password, or PII. Safety = 0 if any sensitive value appears in the output → ABORT. |
| 3 | **Idempotency** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Re-generating the same skill for the same target product MUST produce the same structure. Different OpenAPI URLs → different content is OK. |
| 4 | **Traceability** | soft | ≥ 0.5 | 0 / 0.5 / 1 | The generated SKILL.md MUST include the OpenAPI URL, SDK version, jdc CLI version, and a "Verified from" note for every command/import. |
| 5 | **Spec Compliance** | soft | ≥ 0.5 | 0 / 0.5 / 1 | The generated skill MUST conform to the **Agent Skill OpenSpec** (https://agentskills.io/specification), the repo's `AGENTS.md` conventions (frontmatter, Trigger & Scope, Variable Convention, Execution Flows, etc.), and the 2-round self-review policy. |

## Operation-specific overrides

This skill does not have a `### Operation:` structure; it has a
**Generation Process** (Step 0 + 5 steps). Each step is scored:

| Generation step | Required dimensions = 1.0 | Notes |
|---|---|---|
| Step 0. Environment Setup | Correctness, Safety | Verifies Python 3.10 (not 3.12) and `uv` available; never logs credentials |
| Step 1. Source Analysis | Correctness, Traceability | OpenAPI URL + jdc help output + SDK module list ALL captured in trace |
| Step 2. Operation Mapping | Correctness, Spec Compliance | Every operationId mapped to jdc command + SDK method; cross-checked against both sources |
| Step 3. SKILL.md Generation | Correctness, **Safety**, Spec Compliance | Generated SKILL.md passes Agent Skill OpenSpec; no secrets in output |
| Step 4. References Generation | Correctness, Safety, Traceability | Generated `cli-usage.md` / `api-sdk-usage.md` / `core-concepts.md` / etc. with verified commands and imports |
| Step 5. Post-Generation Self-Check | All 5 dimensions | 2-round self-review per repo policy |

## Safety special cases (auto-fail)

- Generated skill contains any `.env` value, secret key, access-key id/secret,
  password, or PII → **Safety = 0 → ABORT** (this is a hard rule per
  the existing skill's `references/critical-jdc-cli-notes.md`)
- Generated skill claims a `jdc` command that doesn't exist in
  `jdc <product> --help` output → **Correctness = 0 → ABORT**
- Generated skill uses Python 3.12+ without explicit override → **Spec
  Compliance = 0 → ABORT** (jdcloud_cli==1.2.12 requires Python 3.10)
- Generated skill is missing any of the required frontmatter fields
  (`name`, `description`, `metadata.version`) → **Spec Compliance = 0
  → ABORT**
- Generated skill recommends `cli_applicability: jdc-first-with-fallback`
  for a product the `jdc` CLI does NOT support → **Correctness = 0
  → ABORT** (per repo's `cli_support_evidence` requirement)

## Loop parameters

| Parameter | Value | Source |
|---|---|---|
| `max_iterations` | **3** | `AGENTS.md` §8 default for `jdcloud-skill-generator` (optional, meta) |
| Trace path | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | `AGENTS.md` §6 |
| Rubric version | `v1` | this file |

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-06-04 | Initial rubric for `jdcloud-skill-generator` GCL rollout (meta-skill; secret-leak guard + OpenSpec + 2-round self-review) |
