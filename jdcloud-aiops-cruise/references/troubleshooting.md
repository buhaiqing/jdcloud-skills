# Troubleshooting jdcloud-aiops-cruise

## Common Issues

### `jdc` command not found

Ensure the virtual environment is activated and `jdcloud_cli==1.2.12` is
installed in `.venv`. See `AGENTS.md` §Development Environment.

### Python 3.12 import error for `SafeConfigParser`

Recreate the venv with Python 3.10:

```bash
uv venv --python 3.10
source .venv/bin/activate
uv pip install jdcloud_cli jdcloud_sdk
```

### Customer tag returns no resources

- Verify the tag key/value exists in JD Cloud console
- Check `JDC_REGION` matches the region where resources are deployed
- Ensure the AK/SK has read permission to the relevant services

### Import errors in analyzers

Analyzers must follow the three-phase import convention:

```python
import os, sys
_scripts_dir = os.path.dirname(os.path.abspath(__file__))
_project_dir = os.path.join(_scripts_dir, "..")
sys.path.insert(0, _project_dir)
from lib.jdc_client import JdcClient
```

### Report contains mutation suggestions

Any analyzer generating `CREATE INDEX`, `DROP`, `stop`, `delete`, or
`release` advice violates the read-only mandate. Route such findings to
the corresponding product ops skill.

## Debug Flags

- `cruise_sniff.py --verbose` prints discovered resource IDs
- `cruise_link.py --json` saves the full JSON report
- Set `JDC_DOTENV_PATH` to override `.env` location

## Logs

Reports are written to `reports/output/`. GCL traces go to `audit-results/`.
