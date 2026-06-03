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
| Monitoring metrics, alarm rules | `jdcloud-cloudmonitor-ops` |
| Alert analysis, suppression, reporting | `jdcloud-alert-intelligence` |
| IAM users, policies, keys | `jdcloud-iam-ops` |
| Key management, encryption | `jdcloud-kms-ops` |
| Load balancer config | `jdcloud-clb-ops` |
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