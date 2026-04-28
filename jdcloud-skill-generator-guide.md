# JD Cloud Skill Generator Guide

## 1. Introduction
The `jdcloud-skill-generator` is a Meta Skill designed to accelerate the creation of operational Agent Skills for JD Cloud products. It automates the extraction of product documentation and API definitions into a standardized Skill structure.

## 2. How to Use
To generate a new Skill, provide the following inputs to the generator:
- **Product Name**: e.g., "JD Cloud VM" or "JCS".
- **Documentation URL**: Link to the official JD Cloud product docs.
- **API Definition**: Swagger/OpenAPI file (optional but recommended).

### Example Prompt
> "Generate a JD Cloud Skill for 'Cloud Monitor'. Use docs at [URL].
>  Include: alarm CRUD operations, metric query, dashboard monitoring.
>  For each operation: provide pre-flight checks, execution commands, post-execution validation, and failure recovery matrix.
>  Target Agent runtime: Harness AI Agent with shell tool access and environment variable injection."

## 3. Generated Structure
The generator will produce a directory with the following layout:
```
jdcloud-[product]-ops/
├── SKILL.md
├── references/
│   ├── core-concepts.md
│   ├── cli-usage.md
│   ├── troubleshooting.md
│   ├── monitoring.md
│   └── integration.md
└── assets/
    └── example-config.yaml
```

## 4. Customization
After generation, you should:
1. Verify CLI commands against the latest [JD Cloud CLI](https://github.com/jdcloud-api/jdcloud-cli) version.
2. Update IAM role examples in `integration.md`.
3. Add specific error codes to `troubleshooting.md` based on recent incidents.

### JD Cloud CLI GitHub Repository
- **Repository**: https://github.com/jdcloud-api/jdcloud-cli
- **Documentation**: https://docs.jdcloud.com/cn/cli/introduction
- **Installation**: `pip install jdcloud-cli` or download from [Releases](https://github.com/jdcloud-api/jdcloud-cli/releases)

## 5. Agent-Ready Quality Checklist

### Human-Readable Basics
- [ ] All placeholders (`[Product Name]`) are replaced with real product names
- [ ] CLI commands include region and project ID parameters
- [ ] Troubleshooting section covers top 5 common errors
- [ ] Monitoring queries use correct metric namespaces

### Agent-Executable Readiness (P0 — MUST PASS)
- [ ] **Trigger & Scope**: Skill has a `## Trigger & Scope (Agent-Readable)` section with SHOULD-use / SHOULD-NOT-use rules
- [ ] **Variable Convention**: All credentials/secrets use `{{env.VAR_NAME}}` placeholders, NEVER hardcoded
- [ ] **Execution Flows**: At least Create and Delete operations have Pre-flight → Execution → Validation → Recovery phases
- [ ] **Failure Recovery Matrix**: Each error pattern maps to: max retries, backoff strategy, and specific Agent action
- [ ] **Non-Interactive**: All CLI commands default to `--no-interactive` (or equivalent) to prevent Agent blocking
- [ ] **Output Format**: All CLI commands default to `--output json` for machine parsing
- [ ] **Safety Gates**: Destructive operations (delete, stop, terminate) include mandatory user confirmation step
- [ ] **Timeouts Declared**: Every polling/waiting operation has an explicit Max Wait (e.g., "max 300s")
- [ ] **Credentials Validation**: Skill includes a pre-flight check for `jdc config validate` before any operation

### Agent Composability (P1 — SHOULD PASS)
- [ ] **Resource Declarations**: Skill declares what it `produces` (creates) and `consumes` (depends on) in a structured format
- [ ] **Consistent Naming**: Skill follows `jdcloud-[product]-ops` naming convention for predictable discovery
- [ ] **Output Keys**: Resource IDs and key fields are declared with their JSON paths for downstream Skill chaining
- [ ] **Version Pinning**: Skill declares tested CLI version and API version

## 6. Variable & Output Format Conventions

### Placeholder System
All Skills MUST use the following placeholder taxonomy to prevent LLM prompt injection and parsing ambiguity:

| Placeholder Pattern | Scope | Usage Example | Agent Behavior |
|---------------------|-------|---------------|----------------|
| `{{env.VAR_NAME}}` | Runtime environment | `{{env.JDC_ACCESS_KEY}}` | Resolve from env; NEVER ask user; fail if missing |
| `{{user.field}}` | Interactive collection | `{{user.region}}` | Ask user once, cache, reuse |
| `{{output.field}}` | Inter-step data | `{{output.resource_id}}` | Captured from previous command output |

### Shell Command Conventions
```bash
# Template for all CLI commands in any Skill
jdc [product] [action]-[resource] \
  --region {{env.JDC_REGION}} \
  --output json \
  --no-interactive
```

### Credential Safety Rules
- `os.environ['KEY']` for credentials (fail-fast if missing)
- `os.environ.get('KEY', default)` for optional config (e.g., region)
- NEVER use `"your_key_here"` or `${VARIABLE}` shell expansion syntax in Skill documents
