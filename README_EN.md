---
name: jdcloud-skills
description: JD Cloud Operations Agent Skills Collection
license: MIT
---

> **[中文版本](README.md)** | **English Version**

# Skills Farm - JDCloud Skills Development Guide

## Core Value

**Skills Farm is a Meta Skill system** - transforming operational knowledge into structured, AI Agent-parseable, executable, and verifiable declarative specifications.

### Key Features

| Feature | Description |
|---------|-------------|
| **Placeholder Mechanism** | `{{env.*}}` (environment variables), `{{user.*}}` (user input), `{{output.*}}` (output capture), enabling human-machine dual channels |
| **Delegation** | `SHOULD/SHOULD NOT Use` defines boundaries, cross-product operations are automatically delegated |
| **Generator** | Auto-generates Skill framework templates based on OpenAPI specifications, supports manual review and refinement |
| **jdc-first Execution** | Prioritizes `jdc` CLI, falls back to SDK/API after 3 failures |
| **Security Mechanism** | Credential isolation (`{{env.*}}` not exposed), operation safety gates (delete/recovery requires confirmation) |
| **Cross-platform Design** | Based on standard Markdown + OpenSpec, supports multiple Agent frameworks |

### What is Meta Skill

**Meta Skill** is a "Skill that generates Skills" - not specific cloud product operations capabilities, but the **ability to produce operational knowledge**.

| Comparison | Regular Skill | Meta Skill |
|------------|---------------|------------|
| Responsibility | Execute specific operational tasks | Generate/orchestrate other Skills |
| Example | jdcloud-vm-ops manages VMs | jdcloud-skill-generator generates new Skills |
| Input | Environment variables + user instructions | Product documentation URL + API definition |
| Output | Execution results | Structured Skill documents |

Core Value: **"Give a man a fish, feed him for a day. Give an AI a Skill, empower it for operations. Better yet, give it a Meta Skill to generate Skills."**

> Core Principle: Credentials marked with `{{env.*}}` **MUST NEVER be requested from users**, preventing leakage at the mechanism level.

> **One-line Summary**: Skills Farm enables AI Agents to evolve from "answering questions" to "autonomous operations" - every JD Cloud product has an "AI-native" operations assistant.

## Project Structure

```
jdcloud-skills/
├── README.md                          # Chinese version (this file)
├── README_EN.md                       # English version
├── QUICK_START.md                     # Quick start guide (Chinese)
├── QUICK_START_EN.md                  # Quick start guide (English)
├── jdcloud-skill-generator/           # Skill generator (Meta Skill)
│   ├── SKILL.md
│   └── references/
├── jdcloud-vm-ops/                    # VM operations Skill
│   ├── SKILL.md
│   ├── QUICK_REFERENCE.md
│   ├── assets/
│   └── references/
├── jdcloud-redis-ops/                 # Redis operations Skill
│   ├── SKILL.md
│   ├── assets/
│   └── references/
├── jdcloud-cloudmonitor-ops/          # Cloud Monitor operations Skill
│   ├── SKILL.md
│   ├── assets/
│   └── references/
├── jdcloud-iam-ops/                   # IAM operations Skill
│   ├── SKILL.md
│   └── references/
├── jdcloud-kms-ops/                   # KMS operations Skill
│   ├── SKILL.md
│   └── references/
├── jdcloud-clb-ops/                   # CLB operations Skill
│   ├── SKILL.md
│   └── references/
├── .env.example                       # Environment variable template
├── pyproject.toml                     # Python project configuration
└── .gitignore                         # Git ignore rules
```

## What is Skill

A structured Markdown document that guides AI Agents to complete specific tasks. Contains: metadata, core functions, usage guide, best practices, reference documents.

## Developed Skills

| Skill Name | Product | Description | Status |
|------------|---------|-------------|--------|
| [jdcloud-vm-ops](jdcloud-vm-ops/) | VM | VM lifecycle management, monitoring, troubleshooting, **Cloud Assistant batch command execution** | ✅ Available |
| [jdcloud-redis-ops](jdcloud-redis-ops/) | Redis | Redis instance management, performance analysis, backup/recovery | ✅ Available |
| [jdcloud-cloudmonitor-ops](jdcloud-cloudmonitor-ops/) | Cloud Monitor | Alarm rule management, metric query, monitoring dashboard | ✅ Available |
| [jdcloud-iam-ops](jdcloud-iam-ops/) | IAM | Sub-user, group, role, policy, AK/SK management | ✅ Available |
| [jdcloud-kms-ops](jdcloud-kms-ops/) | KMS | Key management, encryption/decryption operations | ✅ Available |
| [jdcloud-clb-ops](jdcloud-clb-ops/) | CLB | Load balancer management, listener configuration | ✅ Available |
| [jdcloud-skill-generator](jdcloud-skill-generator/) | Meta Skill | Auto-generate new product Skills | ✅ Available |

## JD Cloud CLI

All Skills interact with JD Cloud via the official CLI (`jdc`) and API.

### Installation

**Method 1: uv (Recommended, idempotent and reproducible)**

Using [uv](https://docs.astral.sh/uv/) for Python environment management, supports virtual environments and dependency locking:

```bash
# Install uv (one-time)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create environment and install (idempotent, can be re-run)
uv venv --python 3.10
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install jdcloud_cli

# The project's pyproject.toml is configured with Aliyun mirror by default
# For temporary use of other mirrors, use --index-url:
# uv pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple/ jdcloud_cli
```

**Method 2: pip**

```bash
pip install jdcloud_cli
```

**Method 3: Binary**

```bash
curl -fsSL https://github.com/jdcloud-api/jdcloud-cli/releases/latest/download/jdc-linux-amd64.tar.gz | tar -xz && sudo mv jdc /usr/local/bin/
```

### Configure Credentials

#### Method 1: `.env` File (Recommended for local development)

```bash
# Copy example file
cp .env.example .env

# Edit .env and fill in real credentials
# Agent Runtime will auto-load
```

```ini
# .env file example
JDC_ACCESS_KEY=your_access_key_here
JDC_SECRET_KEY=your_secret_key_here
JDC_REGION=cn-north-1
```

#### Method 2: CLI Configuration File

```bash
# Interactive configuration
jdc config init

# Or manually add configuration
jdc configure add --access-key YOUR_KEY --secret-key YOUR_SECRET --region-id cn-north-1
```

Configuration file location: `~/.jdc/config`

```ini
[default]
access_key = YOUR_ACCESS_KEY
secret_key = YOUR_SECRET_KEY
region_id = cn-north-1
endpoint = redis.jdcloud-api.com
scheme = https
timeout = 20
```

#### Method 3: Shell Environment Variables

```bash
export JDC_ACCESS_KEY="your_access_key"
export JDC_SECRET_KEY="your_secret_key"
export JDC_REGION="cn-north-1"
```

> **Priority**: Shell environment variables > `.env` file > CLI config file > Default values
> **Security**: `.env` is in `.gitignore`, won't be committed. Generated Skills use `{{env.*}}` placeholders, no real credentials.

> **⚠️ Security Warning**: **NEVER** print `JDC_SECRET_KEY` value in logs, console output, or debug messages. When verifying credentials, only check existence (e.g., `[ -n "$JDC_SECRET_KEY" ]`). For status logging, use masked placeholders like `JDC_SECRET_KEY=<masked>`.

#### ⚠️ Important: jdc CLI Credential Configuration

**jdc CLI does NOT read environment variables**, it only reads credentials from `~/.jdc/config` file. In sandbox/container environments, special handling is needed:

```bash
# Set writable HOME directory
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc

# Create configuration file
cat > /tmp/jdc-home/.jdc/config << 'EOF'
[default]
access_key = YOUR_ACCESS_KEY
secret_key = YOUR_SECRET_KEY
region_id = cn-north-1
endpoint = redis.jdcloud-api.com
scheme = https
timeout = 20
EOF

# Set current profile
printf "%s" "default" > /tmp/jdc-home/.jdc/current
```

## Developing New Skills

### 1. Preparation

Reference template and guide:

```
@jdcloud-skill-generator/SKILL.md
@jdcloud-skill-generator/references/jdcloud-skill-template.md
```

### 2. Development Process

**Provide prompt**:
> "Generate JD Cloud [product] Skill, name jdcloud-xxx-ops, core functions [description]"

**Generated structure**:
```
jdcloud-[product]-ops/
├── SKILL.md
├── assets/example-config.yaml
└── references/
    ├── cli-usage.md
    ├── core-concepts.md
    ├── integration.md
    ├── monitoring.md
    └── troubleshooting.md
```

### 3. Skill File Specification

#### 3.1 Metadata Header

```yaml
---
name: jdcloud-[product]-ops
version: 1.0.0
description: Manage JD Cloud [product] resources, including CLI usage, SDK integration, and operations best practices.
---
```

#### 3.2 Required Sections

Changelog, Overview, Prerequisites, Environment Variables, Core Functions, Common Commands, Best Practices, Related Links.

### 4. Writing Guidelines

- CLI examples: use `bash`, JSON use `json`, YAML use `yaml`
- Table display: product list, monitoring metrics, alarm thresholds
- Credential configuration: see environment variables section above

### 6. Verification

```bash
npm install -g markdownlint-cli
markdownlint jdcloud-[product]-ops/SKILL.md
```

Verification: CLI commands are executable, links are valid, examples are correct.

### 7. Version Management

Use SemVer: `major.minor.patch`.

Update process: modify content → update changelog → update version field → commit.

## Usage Examples

### Example 1: Query VM List

```bash
# After configuring credentials, execute
jdc --output json vm describe-instances --region-id cn-north-1 --page-number 1 --page-size 10
```

### Example 2: Query Redis Instance

```bash
# Use jdc CLI to query Redis instance list
jdc --output json redis describe-cache-instances --region-id cn-north-1 --page-number 1 --page-size 100

# Query specific instance details
jdc --output json redis describe-cache-instance --region-id cn-north-1 --cache-instance-id redis-xxxxx
```

### Example 3: Create New Skill

```bash
mkdir -p jdcloud-[product]-ops/references jdcloud-[product]-ops/assets

# Reference generator and provide prompt: "Generate JD Cloud [product] Skill"

# Verify generated SKILL.md
head -20 jdcloud-[product]-ops/SKILL.md
```

## Skill Generator

Meta Skill, auto-generates operations Agent Skills from product documentation.

### Usage

Provide: product name, documentation URL, API definition (optional), CRUD operation list, target runtime.

**Example**:
> "Generate JD Cloud Cloud Monitor Skill, documentation URL: https://docs.jdcloud.com/cn/cloudmonitor, includes alarm CRUD, metric query"

### Quality Check

**P0 Required**: Trigger & Scope, `{{env.*}}` placeholders, Pre-flight→Execute→Validate→Recovery, failure recovery matrix, `--no-interactive`/`--output json`, safety confirmation, timeout declaration

**P1 Recommended**: Resource declaration, consistent naming, output key declaration, version locking

## Quick Start

If you're new to this project, refer to [QUICK_START_EN.md](QUICK_START_EN.md) for detailed quick start guide.

## Reference Resources

- [Quick Start Guide](QUICK_START_EN.md)
- [Skill Generator](jdcloud-skill-generator/SKILL.md)
- [Skill Template](jdcloud-skill-generator/references/jdcloud-skill-template.md)
- [JD Cloud CLI](https://github.com/jdcloud-api/jdcloud-cli)
- [Agent Skill OpenSpec](https://agentskills.io/specification)

## FAQ

| Q | A |
|---|---|
| Skill vs MCP Server relationship? | Skill is documentation, MCP is execution service |
| One Skill covers multiple products? | Recommend single responsibility, cross-reference via References |
| How to update Skill? | Modify content, update version and changelog |

## Contributing

1. Fork 2. Create Skill directory 3. Follow guide to write 4. Submit PR

### Commit & PR conventions

- **Commit messages** follow [Conventional Commits](https://www.conventionalcommits.org/)
  (`feat` / `fix` / `docs` / `refactor` / `test` / `chore` / `security`).
  A full template lives in [`.gitmessage.txt`](.gitmessage.txt).
  Enable it: `git config commit.template .gitmessage.txt`.
- **PR descriptions** use the GitHub PR template
  ([`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md)).
  If your PR modifies a `SKILL.md`, you MUST complete the
  GCL checklist in the template.
- **New-skill GCL onboarding** uses the issue template
  ([`.github/ISSUE_TEMPLATE/gcl-rollout.md`](.github/ISSUE_TEMPLATE/gcl-rollout.md)).

---

See [jdcloud-vm-ops](jdcloud-vm-ops/) as example.