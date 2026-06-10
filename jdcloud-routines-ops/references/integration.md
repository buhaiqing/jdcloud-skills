# Integration — `jdcloud-routines-ops`

> How this skill talks to other skills, to the runtime, and to external systems.

## 1. Cross-Skill Delegation

### 1.1 What this skill consumes

| Need | Delegate to |
|---|---|
| Query Cloud Monitor metrics | `jdcloud-cloudmonitor-ops` |
| Analyze alert bursts during a cruise window | `jdcloud-alert-intelligence` |
| Run a pre-renewal health check on an expiring resource | `jdcloud-aiops-cruise` |
| Tag compliance audit on expired-but-untagged resources | `jdcloud-tag-audit-ops` |
| Modify / renew / delete a resource after cruise finds it | The matching product ops skill (e.g. `jdcloud-vm-ops` for VM renewal) |

### 1.2 What this skill produces (consumed by others)

| Output | Consumer | Notes |
|---|---|---|
| `outputs/expiry/expiry-report-*.json` | `jdcloud-alert-intelligence` (planned) | Feeds suppression-rule generation |
| `outputs/expiry/expiry-report-*.json` | `jdcloud-cloudmonitor-ops` (planned) | Feeds "expiring resource" alarms |
| Console summary (stdout) | Human / Feishu / ticket system | The default consumer |

## 2. Credential Loading Chain

This skill uses **both** the CLI credential path and the SDK credential path.
Both must be present.

```
┌────────────────────────────┐
│ ~/.jdc/config (INI)        │  ← required by jdc CLI
│  [default]                 │
│   access_key = ...         │
│   secret_key = ...         │
│   region_id  = cn-north-1  │
└────────────────────────────┘
            │
            ├── jdc reads via configparser
            │
            └── (for SDK fallback) lib/jdc_client.py reads the same INI
                and injects into JDC_ACCESS_KEY / JDC_SECRET_KEY env vars
```

> **CRITICAL**:
>
> - `jdc` CLI ignores `JDC_ACCESS_KEY` / `JDC_SECRET_KEY` env vars.
> - `jdcloud_sdk` ignores `~/.jdc/config`.
> - The script bridges the two by reading the INI and populating the env vars
>   before instantiating the SDK. This is done in `scripts/lib/jdc_client.py`.

### 2.1 Sandbox / non-writable HOME

If `~` is not writable (CI, container), override `HOME`:

```bash
export HOME=/tmp/jdc-home
mkdir -p $HOME/.jdc
# create $HOME/.jdc/config as shown in cli-usage.md §1.2
```

The script's `_find_venv()` walks up to 5 levels looking for `.venv`. If your
repo layout differs, set `VIRTUAL_ENV` env var explicitly.

## 3. Runtime conventions

### 3.1 Python version

**Python 3.10 only.** `jdcloud_cli==1.2.12` uses `configparser.SafeConfigParser`,
removed in 3.12.

### 3.2 venv location

Expected at the repo root: `<repo>/.venv`. The script walks up from
`scripts/lib/` looking for `.venv`. If not found, it falls back to system `jdc`
(requires `jdc` on `PATH`).

### 3.3 sys.path convention

`scripts/expiry_cruise.py` does:

```python
_script_dir = Path(__file__).resolve().parent
_project_dir = _script_dir.parent
sys.path.insert(0, str(_project_dir))
from lib.jdc_client import JdcClient
```

This matches the AGENTS.md convention: scripts at any depth insert the
`scripts/` directory (one level above) before importing `lib.*`.

## 4. Output paths

| Channel | Default path | Override |
|---|---|---|
| JSON report | `~/.jdcloud-routines-ops/outputs/expiry/expiry-report-YYYYMMDD-HHMMSS.json` | `--output-dir` |
| Project-local fallback | `<repo>/jdcloud-routines-ops/outputs/expiry/` | (auto-fallback if HOME unwritable) |

The script writes into the **home dir** by default (long-lived retention). For
ephemeral / CI runs, prefer `--output-dir` so reports can be cleaned up with the
workspace.

## 5. Cleanup

```bash
# Keep last 7 days
find ~/.jdcloud-routines-ops/outputs -type f -mtime +7 -delete
```

Wrapped as `scripts/cleanup_outputs.sh` for cron convenience.

## 6. Trigger sources

| Source | How |
|---|---|
| Manual | Operator runs the script directly |
| Weekly cron | `0 9 * * 1 cd /path && .venv/bin/python scripts/expiry_cruise.py` |
| CI pipeline | GitHub Actions / DOPS — see `jdcloud-skill-generator` template |
| Feishu bot | (planned) — bot forwards `expiry-cruise` slash command to this skill |

## 7. Integration tests

```python
# tests/test_integration.py (planned)
import json
import subprocess
from pathlib import Path

def test_expiry_cruise_writes_report(tmp_path):
    result = subprocess.run(
        ["python", "scripts/expiry_cruise.py",
         "--warning-days", "60",
         "--output-dir", str(tmp_path)],
        capture_output=True, text=True,
    )
    # exit code is 0 (findings) or 1 (clean / error) — both are acceptable here
    assert result.returncode in (0, 1)
    reports = list(tmp_path.glob("expiry-report-*.json"))
    assert reports, "no report file produced"
    payload = json.loads(reports[0].read_text(encoding="utf-8"))
    assert "summary" in payload
    assert "details" in payload
```

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-06-10 | Initial integration doc for `jdcloud-routines-ops` (1.1.0 batch) |