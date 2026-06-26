# JD Cloud Cloud Assistant Reference

> **ponytail: trimmed — core concepts and state table kept. Execution flows are in SKILL.md.**

## Overview

Cloud Assistant (云助手) is a native automation tool for JD Cloud VMs. It batch-executes Shell/PowerShell scripts without SSH.

- **API Endpoint**: `assistant.jdcloud-api.com` (separate from VM API)
- **Cost**: Free
- **Limitation**: `jdc` CLI does NOT support cloud assistant → **SDK only**

## Core Concepts

| Concept | Description |
|---------|-------------|
| Command | Reusable script (Shell or PowerShell) |
| Execution User | Default: `root` (Linux) / `administrator` (Windows) |
| Timeout | 10-86400s; force-killed on timeout |
| Custom Parameters | `{{key}}` placeholders resolved at invocation |

## Command States

### Invocation-Level
| State | Description |
|-------|-------------|
| `pending` | Dispatching |
| `running` | Executing |
| `finished` | Exit code 0 |
| `failed` | Non-zero exit or timeout |
| `partial_failed` | Mixed across instances |

## SDK Operations

| Operation | Method |
|-----------|--------|
| Create Command | `AssistantClient.create_command()` |
| Describe Commands | `AssistantClient.describe_commands()` |
| Delete Commands | `AssistantClient.delete_commands()` |
| Invoke Command | `AssistantClient.invoke_command()` |
| Describe Invocations | `AssistantClient.describe_invocations()` |

> See [SKILL.md](../SKILL.md) "Cloud Assistant Operations" for full execution flows.