# Integration — JD Cloud SSL Certificate

## Prerequisites

- **Python 3.10** (required; `jdcloud_cli==1.2.12` uses `SafeConfigParser`, removed in 3.12)
- `uv` package manager
- JD Cloud account with API credentials

## Setup

```bash
# 1. Create virtual environment
uv venv --python 3.10
source .venv/bin/activate

# 2. Install packages
uv pip install jdcloud_cli jdcloud_sdk

# 3. Verify
jdc --version
```

## Credential Configuration

### For SDK (env vars)

```bash
export JDC_ACCESS_KEY="your-access-key"
export JDC_SECRET_KEY="your-secret-key"
export JDC_REGION="cn-north-1"
```

### For CLI (INI file)

```bash
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc
cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = your-access-key
secret_key = your-secret-key
region_id = cn-north-1
endpoint = ssl.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF
printf "%s" "default" > /tmp/jdc-home/.jdc/current
```

## Verification

```bash
# CLI verification
jdc --output json ssl describe-certs --page-number 1 --page-size 1

# SDK verification
python -c "
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.ssl.client.SslClient import SslClient
from jdcloud_sdk.services.ssl.apis.DescribeCertsRequest import DescribeCertsRequest, DescribeCertsParameters
import os
c = Credential(os.environ['JDC_ACCESS_KEY'], os.environ['JDC_SECRET_KEY'])
client = SslClient(c)
p = DescribeCertsParameters(); p.setPageNumber(1); p.setPageSize(1)
print(client.send(DescribeCertsRequest(parameters=p)).result)
"
```

## CI/CD Integration

```bash
export JDC_ACCESS_KEY="$CI_JDC_ACCESS_KEY"
export JDC_SECRET_KEY="$CI_JDC_SECRET_KEY"
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc
# ... configure INI file ...
jdc --output json ssl describe-certs
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `JDC_ACCESS_KEY` | Yes | JD Cloud API access key |
| `JDC_SECRET_KEY` | Yes | JD Cloud API secret key |
| `JDC_REGION` | No | Default region (default: `cn-north-1`) |
