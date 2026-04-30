---
name: jdcloud-skill-generator
description: >
  Meta Skill for generating JD Cloud operational Agent Skills. Use when you need
  to create new JD Cloud product skills from documentation and API definitions.
  Generates standardized skill structures following the Agent Skill OpenSpec.
license: MIT
compatibility: Requires access to JD Cloud documentation, OpenAPI/Swagger specs, and skill template files
metadata:
  author: jdcloud
  version: "1.0.0"
  last_updated: "2026-04-30"
  runtime: Harness AI Agent
  type: meta-skill
---

# JD Cloud Skill Generator

This is a Meta Skill that generates new JD Cloud operational Agent Skills from product documentation and API definitions.

## When to Use This Skill

- User asks to create a new JD Cloud product operation skill
- User provides documentation URL and wants to generate a skill structure
- User wants to generate skill from OpenAPI/Swagger specifications
- User wants to generate skill from CLI commands and examples

## Input Requirements

When requesting skill generation, provide:

1. **Product Name**: e.g., "Cloud Monitor", "Cloud RDS", "Kubernetes Cluster"
2. **Documentation URL**: Link to official JD Cloud product documentation
3. **API Definition**: Swagger/OpenAPI file URL (optional but recommended)
4. **Operations Needed**: List of CRUD operations to include (create, describe, modify, delete, list)
5. **Target Agent Runtime**: e.g., "Harness AI Agent", "Claude Code", "Cursor"

## Generation Process

### Step 1: Analyze Product Documentation

Extract key information:
- Available CLI commands (jdc [product] [action]-[resource])
- API endpoints and parameters
- Common error codes
- Monitoring metrics namespaces

### Step 2: Generate Skill Structure

Create directory structure:
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

### Step 3: Populate SKILL.md Template

Use jdcloud-skill-template.md as base, replacing placeholders:
- `[Product Name]` → actual product name
- `[Product Chinese Name]` → Chinese name
- `[Resource Type]` → primary resource type
- `[product]` → CLI product command

### Step 4: Generate Reference Files

Generate each reference document based on product documentation:
- **core-concepts.md**: Product-specific concepts and architecture
- **cli-usage.md**: Detailed CLI command reference with examples
- **troubleshooting.md**: Error codes and diagnostic steps
- **monitoring.md**: Available metrics and alert configurations
- **integration.md**: SDK initialization and MCP server config

## Agent-Ready Quality Checklist

### P0 - MUST PASS

- [ ] Trigger & Scope section with SHOULD-use / SHOULD-NOT-use rules
- [ ] Variable conventions use `{{env.VAR_NAME}}` for credentials
- [ ] Execution flows include Pre-flight → Execute → Validate → Recovery
- [ ] Failure Recovery Matrix with error patterns and retry strategies
- [ ] Non-interactive CLI commands: `--no-interactive`
- [ ] JSON output: `--output json`
- [ ] Safety gates for destructive operations (delete, stop, terminate)
- [ ] Timeout declared for polling/waiting operations

### P1 - SHOULD PASS

- [ ] Resource declarations: what skill produces/consumes
- [ ] Consistent naming: `jdcloud-[product]-ops`
- [ ] Output keys with JSON paths for skill chaining
- [ ] Version pinning for CLI and API versions

## Output

The generated skill will:
1. Be ready to use with JD Cloud CLI
2. Include pre-flight checks and validation
3. Have proper error handling and recovery
4. Follow Agent Skill OpenSpec (https://agentskills.io/specification)

## Example

> "Generate a JD Cloud Skill for Cloud Monitor. Use docs at https://docs.jdcloud.com/cn/cloudmonitor.
> Include: alarm CRUD, metric query, dashboard monitoring. Target: Harness AI Agent."

Would generate:
- jdcloud-monitor-ops/SKILL.md
- references/core-concepts.md, cli-usage.md, troubleshooting.md, monitoring.md, integration.md
- assets/example-config.yaml

## See Also

## Reference Files

- [Skill Template](references/jdcloud-skill-template.md) - Base template for generating new JD Cloud product skills
- [JD Cloud CLI](https://github.com/jdcloud-api/jdcloud-cli)
- [Agent Skill OpenSpec](https://agentskills.io/specification)
