# Integration

## Environment Setup (uv)

```bash
uv venv --python 3.10
source .venv/bin/activate
uv pip install jdcloud_sdk
```

## Python SDK Bootstrap

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.logs.client import LogsClient

credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"]
)
client = LogsClient(credential, os.environ.get("JDC_REGION", "cn-north-1"))
```

## Endpoint Configuration

LogService API endpoint:
- `logs.jdcloud-api.com`
- HTTPS only
- Regional routing is handled by the SDK based on `regionId`

## Integration with Other Skills

### With VM Ops (`jdcloud-vm-ops`)

VM log collection pipeline:
```python
# 1. Create VM via jdcloud-vm-ops
# 2. Create LogSet + LogTopic via this skill
# 3. Install JD Cloud log collection agent on VM
# 4. Configure collectionInfo.paths to match VM log locations
```

### With Kubernetes Ops (`jdcloud-kubernetes-ops`)

K8s container log collection:
```python
# 1. Create/verify K8s cluster via jdcloud-kubernetes-ops
# 2. Create LogSet + LogTopic via this skill
# 3. Deploy log collector DaemonSet to cluster
# 4. Configure collectionInfo.type = "container"
```

### with CloudMonitor (`jdcloud-cloudmonitor-ops`)

Set up monitoring for LogService:
```python
# 1. Create LogSet/LogTopic via this skill
# 2. Configure CloudMonitor alarms via jdcloud-cloudmonitor-ops:
#    - Logs.IngestionErrorRate > threshold
#    - Logs.QueryLatency > threshold
#    - Logs.StorageSize > threshold
```

### with OSS (`jdcloud-oss-ops`)

Long-term log archival:
```python
# 1. Create OSS bucket via jdcloud-oss-ops
# 2. Configure LogService export/shipping to OSS bucket
# 3. Set OSS lifecycle rules for cost-effective cold storage
```

### with Function Compute (`jdcloud-fc-ops`)

Serverless log processing:
```python
# 1. Create function via jdcloud-fc-ops
# 2. Configure LogService subscription to trigger function on new logs
# 3. Function processes/transforms logs and writes to downstream
```

## IAM Policy Example

Minimum IAM policy for LogService operations:

```json
{
  "Version": "1",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogSet",
        "logs:DescribeLogSet",
        "logs:DescribeLogSets",
        "logs:UpdateLogSet",
        "logs:DeleteLogSet",
        "logs:CreateLogTopic",
        "logs:DescribeLogTopic",
        "logs:DescribeLogTopics",
        "logs:UpdateLogTopic",
        "logs:DeleteLogTopic",
        "logs:SearchLog",
        "logs:DescribeIndex",
        "logs:UpdateIndex"
      ],
      "Resource": "*"
    }
  ]
}
```

For read-only access (search only):

```json
{
  "Version": "1",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:DescribeLogSet",
        "logs:DescribeLogSets",
        "logs:DescribeLogTopic",
        "logs:DescribeLogTopics",
        "logs:SearchLog",
        "logs:DescribeIndex"
      ],
      "Resource": "*"
    }
  ]
}
```

> For IAM policy management, delegate to `jdcloud-iam-ops`.
