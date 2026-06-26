# Prerequisites & Environment Configuration

> This document is extracted from `SKILL.md`.
> Environment setup follows the **jdc-first fallback strategy**.

## Overview

1. **Attempt to install `jdc` CLI via `uv`** (primary path)
2. On failure, **retry up to 3 times** (exponential backoff: 0s → 2s → 4s)
3. **After 3 consecutive failures**, fall back to **SDK-only** environment

## Python Runtime (uv)

Both `jdc` CLI and JD Cloud Python SDK require a Python runtime. Use **`uv`** for locally isolated idempotent environment management.

**Install uv (system-level, one-time per machine):**
```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
# or via Homebrew: brew install uv
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Phase 1: jdc CLI Installation (Primary Path)

> **Python 3.10 is required, NOT 3.12.** `jdcloud_cli==1.2.12` uses `SafeConfigParser`, which was **removed in Python 3.12**. Always use `uv venv --python 3.10`.

```bash
uv venv --python 3.10
source .venv/bin/activate
uv pip install jdcloud_cli jdcloud_sdk
jdc --version
python -c "import jdcloud_sdk; print('SDK OK')"
```

### Retry Logic (Max 3 attempts)

If `jdc --version` or any `jdc` command fails:

```bash
# Retry 1
uv pip install jdcloud_cli jdcloud_sdk
jdc --version && echo "OK" || echo "FAIL"

# Retry 2 (wait 2 seconds)
sleep 2
uv pip install --force-reinstall jdcloud_cli
jdc --version && echo "OK" || echo "FAIL"

# Retry 3 (wait 4 seconds)
sleep 4
uv pip install --force-reinstall jdcloud_cli jdcloud_sdk
jdc --version && echo "OK" || echo "FAIL"
```

If all **3 retries** fail, proceed to **Phase 2: SDK Fallback**.

## Phase 2: SDK Fallback (after 3 jdc failures)

> **Python 3.10 is required, NOT 3.12.**

```bash
uv venv --python 3.10
source .venv/bin/activate
uv pip install jdcloud_sdk
python -c "import jdcloud_sdk; print('SDK OK')"
```

## Configure Credentials

> **CRITICAL:** The `jdc` CLI reads credentials **only** from `~/.jdc/config` INI file. Environment variables (`JDC_ACCESS_KEY`, `JDC_SECRET_KEY`) are **ignored** by the CLI. The SDK mode reads from environment variables. Use the appropriate method below.

### Method A: Configure SDK Credentials (Environment Variables)

The Agent runtime must set the following environment variables, corresponding to the `{{env.*}}` placeholders in this Skill:
```bash
export JDC_ACCESS_KEY="{{env.JDC_ACCESS_KEY}}"
export JDC_SECRET_KEY="{{env.JDC_SECRET_KEY}}"
export JDC_REGION="cn-north-1"
```

### Method B: Configure CLI Credentials (`~/.jdc/config` INI File)

```bash
# Sandbox environment: redirect HOME to a writable directory
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc
cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = {{env.JDC_ACCESS_KEY}}
secret_key = {{env.JDC_SECRET_KEY}}
region_id = {{env.JDC_REGION}}
endpoint = monitor.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF
# Key: ~/.jdc/current must contain "default" with no trailing newline
printf "%s" "default" > /tmp/jdc-home/.jdc/current
```