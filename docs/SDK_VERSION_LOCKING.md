# SDK Version Locking Mechanism

> **Version Control Strategy for JD Cloud Skills**

## Overview

This document defines the SDK version locking mechanism for JD Cloud Skills, ensuring reproducible and stable execution environments across different machines and CI/CD pipelines.

## Why Version Locking?

| Risk | Without Locking | With Locking |
|------|-----------------|--------------|
| **API Changes** | SDK updates may break API compatibility | Guaranteed API behavior |
| **Reproducibility** | Different machines get different versions | Identical versions everywhere |
| **CI/CD Stability** | Pipeline failures due to version drift | Consistent pipeline results |
| **Debugging** | Version-specific bugs hard to trace | Known version for debugging |

## Version Locking Strategy

### 1. Project-Level Locking (pyproject.toml)

**Recommended for team projects and CI/CD environments.**

The project root `pyproject.toml` defines pinned versions:

```toml
[project]
name = "jdcloud-skills"
version = "1.0.0"
requires-python = ">=3.10"
dependencies = [
    "jdcloud_cli==1.2.12",   # Locked version
    "jdcloud_sdk>=1.6.26",   # Minimum version
]

[tool.uv]
python-version = "3.10"
index-url = "https://mirrors.aliyun.com/pypi/simple/"

# Optional: development dependencies
[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "black>=23.0.0",
]
```

### 2. Skill-Level Version Declaration

Each Skill should declare its tested SDK version in `SKILL.md` frontmatter:

```yaml
---
metadata:
  sdk_version_locked: "1.6.26"
  cli_version_locked: "1.2.30"
---
```

### 3. Integration.md Version Section

Each Skill's `references/integration.md` should include:

```markdown
## SDK Version Pinning

### Recommended Versions

| Package | Version | Notes |
|---------|---------|-------|
| jdcloud_cli | 1.2.12 | CLI for [Product] operations |
| jdcloud_sdk | >=1.6.26 | SDK fallback for CLI failures |

### Install Locked Versions

```bash
# CLI (exact version - latest stable)
uv pip install jdcloud_cli==1.2.12

# SDK (minimum version - allows updates within range)
uv pip install jdcloud_sdk>=1.6.26
```

### Verify Versions

```bash
jdc --version
python -c "import jdcloud_sdk; print(f'SDK version: {jdcloud_sdk.__version__}')"
```
```

## Implementation Methods

### Method A: uv.lock File (Automatic)

When using `uv sync`, uv automatically creates `uv.lock`:

```bash
# Sync environment (creates uv.lock automatically)
uv sync

# The uv.lock file contains exact versions
# Include uv.lock in version control for reproducibility
```

**uv.lock example structure**:
```toml
version = 1
requires-python = ">=3.10"

[[package]]
name = "jdcloud-cli"
version = "1.2.30"
source = { registry = "https://mirrors.aliyun.com/pypi/simple/" }

[[package]]
name = "jdcloud-sdk"
version = "1.6.26"
source = { registry = "https://mirrors.aliyun.com/pypi/simple/" }
```

### Method B: Manual Version Pinning

```bash
# Install specific versions
uv pip install jdcloud_cli==1.2.30 jdcloud_sdk==1.6.26

# Verify installation
uv pip list | grep jdcloud
# Expected output:
# jdcloud-cli    1.2.30
# jdcloud-sdk    1.6.26
```

### Method C: requirements.txt (Legacy)

For compatibility with pip-only environments:

```txt
jdcloud_cli==1.2.30
jdcloud_sdk==1.6.26
```

## Version Update Process

### When to Update Versions

1. **Security vulnerabilities** - Immediate update required
2. **API deprecation** - Plan migration, then update
3. **New features needed** - Verify compatibility, then update

### Update Workflow

```bash
# 1. Check current versions
uv pip list | grep jdcloud

# 2. Check available versions
pip index versions jdcloud_cli
pip index versions jdcloud_sdk

# 3. Test new version in isolated environment
uv venv --python 3.10
source .venv/bin/activate
uv pip install jdcloud_cli==<new_version> jdcloud_sdk==<new_version>

# 4. Verify functionality
jdc --version
jdc --output json vm describe-instance-types --region-id cn-north-1 --page-number 1 --page-size 1

# 5. Update pyproject.toml if tests pass
# Edit dependencies section

# 6. Re-sync environment
uv sync

# 7. Update Skill SKILL.md frontmatter
# Update sdk_version_locked and cli_version_locked

# 8. Update Skill Changelog
# Document version change
```

## Version Compatibility Matrix

| SDK Version | CLI Version | Python | API Profile | Status |
|-------------|-------------|--------|-------------|--------|
| >=1.6.26 | 1.2.12 | 3.10+ | VM API v1.0 | ✅ Tested |
| >=1.6.26 | 1.2.12 | 3.10+ | Redis API v1.0 | ✅ Tested |
| >=1.6.26 | 1.2.12 | 3.10+ | Monitor API v1.0 | ✅ Tested |
| >=1.6.26 | 1.2.12 | 3.10+ | IAM API v1.0 | ✅ Tested |

## CI/CD Integration

### GitHub Actions Example

```yaml
name: JD Cloud Skills Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      
      - name: Sync environment with locked versions
        run: |
          uv venv --python 3.10
          source .venv/bin/activate
          uv sync
      
      - name: Verify versions
        run: |
          source .venv/bin/activate
          jdc --version
          python -c "import jdcloud_sdk; print(jdcloud_sdk.__version__)"
      
      - name: Run tests
        run: |
          source .venv/bin/activate
          pytest tests/
```

### Docker Example

```dockerfile
FROM python:3.10-slim

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Copy project files
COPY pyproject.toml uv.lock ./

# Sync environment (uses locked versions)
RUN uv sync --frozen

# Verify versions
RUN jdc --version && python -c "import jdcloud_sdk; print(jdcloud_sdk.__version__)"

ENTRYPOINT ["jdc"]
```

## Verification Commands

### Quick Version Check

```bash
# Check CLI version
jdc --version

# Check SDK version
python -c "import jdcloud_sdk; print(f'SDK: {jdcloud_sdk.__version__}')"

# Check all jdcloud packages
uv pip list | grep jdcloud
```

### Detailed Version Verification

```bash
# Show detailed package info
uv pip show jdcloud_cli
uv pip show jdcloud_sdk

# Check version against pyproject.toml
python -c "
import tomllib
with open('pyproject.toml', 'rb') as f:
    data = tomllib.load(f)
    deps = data['project']['dependencies']
    for dep in deps:
        if 'jdcloud' in dep:
            print(dep)
"
```

## Troubleshooting

### Version Mismatch

```bash
# Problem: Installed version differs from locked version
# Solution: Re-sync with frozen flag

uv sync --frozen  # Uses exact versions from uv.lock
```

### Version Not Available

```bash
# Problem: Specified version not found
# Solution: Check available versions

pip index versions jdcloud_sdk
# If version not listed, update to latest available version
```

### Dependency Conflict

```bash
# Problem: Version conflicts with other dependencies
# Solution: Use uv's dependency resolver

uv pip install jdcloud_cli==1.2.30 jdcloud_sdk==1.6.26 --resolution lowest-direct
```

## Best Practices

1. **Always include uv.lock in version control** - Ensures reproducibility
2. **Test before updating versions** - Verify compatibility in isolated environment
3. **Document version changes in Changelog** - Track version history
4. **Use frozen sync in CI/CD** - Prevent unexpected version updates
5. **Regularly audit for security updates** - Check for vulnerabilities
6. **Maintain version matrix** - Document tested combinations

## Related Files

- `/pyproject.toml` - Project-level version definitions
- `/uv.lock` - Auto-generated lock file (include in git)
- `/references/integration.md` (per Skill) - Skill-level version documentation
- `SKILL.md` frontmatter - SDK version locked metadata

## See Also

- [JD Cloud CLI Releases](https://github.com/jdcloud-api/jdcloud-cli/releases)
- [JD Cloud SDK PyPI](https://pypi.org/project/jdcloud-sdk/)
- [uv Documentation](https://docs.astral.sh/uv/)