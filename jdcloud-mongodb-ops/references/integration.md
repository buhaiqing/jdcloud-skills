# Integration Guide for JD Cloud MongoDB

## Python SDK Integration

### Installation

```bash
pip install jdcloud-sdk-python
```

**Recommended Version**: >= 1.2.0

### Credential Configuration

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.mongodb.client import MongodbClient

# Use environment variables (recommended for security)
credential = Credential(
    access_key=os.environ["JDC_ACCESS_KEY"],
    secret_key=os.environ["JDC_SECRET_KEY"]
)

# Initialize client with region
client = MongodbClient(credential, region="cn-north-1")
```

### Basic Usage Pattern

```python
from jdcloud_sdk.services.mongodb.apis.CreateInstanceRequest import CreateInstanceRequest
from jdcloud_sdk.services.mongodb.apis.DescribeInstancesRequest import DescribeInstancesRequest

# Create instance
req = CreateInstanceRequest(
    regionId="cn-north-1",
    instanceName="my-mongodb",
    instanceClass="mongodb.s.1.large",
    engineVersion="4.0",
    vpcId="vpc-xxxx",
    subnetId="subnet-xxxx",
    azId="cn-north-1a"
)

resp = client.create_instance(req)
instance_id = resp.result.instanceId

# Poll until running
import time
for i in range(60):
    desc_req = DescribeInstancesRequest(
        regionId="cn-north-1",
        instanceId=instance_id
    )
    desc_resp = client.describe_instances(desc_req)
    status = desc_resp.result.instance.status
    
    if status == "running":
        break
    elif status in ["error", "deleted"]:
        raise RuntimeError(f"Instance creation failed: {status}")
    
    time.sleep(10)
```

### Error Handling

```python
from jdcloud_sdk.core.exception import ServerException

try:
    resp = client.create_instance(req)
except ServerException as e:
    if e.status == 403 and "QuotaExceeded" in str(e):
        print("Quota exceeded, please request quota increase")
    elif e.status == 400 and "InvalidParameter" in str(e):
        print(f"Invalid parameter: {e.message}")
        # Fix parameters and retry
    elif e.status == 500:
        # Internal error, retry with backoff
        print("Internal error, retrying...")
        time.sleep(2)
        # retry...
    else:
        print(f"Error: {e.status} - {e.message}")
        raise
```

### Async Operations Helper

```python
def poll_until_terminal(client, instance_id, region_id, 
                        terminal_states=["running"], 
                        failure_states=["error", "deleted"],
                        max_wait=600, poll_interval=10):
    """
    Poll instance status until terminal state or timeout.
    
    Returns: final status
    Raises: RuntimeError if failure state or timeout
    """
    import time
    elapsed = 0
    
    while elapsed < max_wait:
        req = DescribeInstancesRequest(regionId=region_id, instanceId=instance_id)
        resp = client.describe_instances(req)
        status = resp.result.instance.status
        
        if status in terminal_states:
            return status
        
        if status in failure_states:
            raise RuntimeError(f"Instance in failure state: {status}")
        
        time.sleep(poll_interval)
        elapsed += poll_interval
    
    raise RuntimeError(f"Timeout waiting for terminal state, current: {status}")

# Usage
status = poll_until_terminal(client, instance_id, "cn-north-1")
print(f"Instance ready: {status}")
```

## CLI Integration

### Installation

```bash
pip install jdcloud_cli

# Configure
jdc configure add \
  --access-key $JDC_ACCESS_KEY \
  --secret-key $JDC_SECRET_KEY \
  --region-id cn-north-1
```

### Environment Variables

```bash
export JDC_ACCESS_KEY="your-access-key"
export JDC_SECRET_KEY="your-secret-key"
export JDC_REGION="cn-north-1"
```

### Scripting with CLI

```bash
#!/bin/bash
# Create MongoDB instance script

REGION="cn-north-1"
INSTANCE_NAME="my-mongodb"
SPEC="mongodb.s.1.large"
VPC_ID="vpc-xxxx"
SUBNET_ID="subnet-xxxx"
AZ_ID="cn-north-1a"

# Create instance
echo "Creating MongoDB instance..."
INSTANCE_ID=$(jdc mongodb create-instance \
  --region-id $REGION \
  --instance-name $INSTANCE_NAME \
  --instance-class $SPEC \
  --engine-version 4.0 \
  --vpc-id $VPC_ID \
  --subnet-id $SUBNET_ID \
  --az-id $AZ_ID \
  --output json | jq -r '.result.instanceId')

echo "Instance ID: $INSTANCE_ID"

# Wait for running state
echo "Waiting for instance to be ready..."
for i in {1..60}; do
  STATUS=$(jdc mongodb describe-instances \
    --region-id $REGION \
    --instance-id $INSTANCE_ID \
    --output json | jq -r '.result.instance.status')
  
  echo "Status: $STATUS"
  
  if [ "$STATUS" = "running" ]; then
    echo "Instance is ready!"
    break
  elif [ "$STATUS" = "error" ]; then
    echo "Instance creation failed"
    exit 1
  fi
  
  sleep 10
done

# Get connection info
echo "Connection info:"
jdc mongodb describe-instances \
  --region-id $REGION \
  --instance-id $INSTANCE_ID \
  --output json | jq '.result.instance | {domain: .connectionDomain, port: .port}'
```

## Application Connection

### Connection String Format

```
mongodb://username:password@connection-domain:port/database?options
```

**Example**:
```
mongodb://root:MyPass123@mongodb-xxxx.jcs.jdcloud.com:27017/admin
```

### Connection with MongoDB Driver (Python)

```python
from pymongo import MongoClient

# Connection string
connection_string = "mongodb://root:password@mongodb-xxxx.jcs.jdcloud.com:27017/admin"

# Create client with connection pool
client = MongoClient(
    connection_string,
    maxPoolSize=100,
    minPoolSize=10,
    connectTimeoutMS=5000,
    socketTimeoutMS=30000,
    retryWrites=True,
    w="majority"
)

# Test connection
db = client.admin
result = db.command("ping")
print(f"Connected: {result}")

# Use database
mydb = client.mydatabase
collection = mydb.mycollection
```

### Connection Options

| Option | Description | Recommended Value |
|--------|-------------|-------------------|
| `maxPoolSize` | Max connections in pool | 50-200 |
| `minPoolSize` | Min connections in pool | 10 |
| `connectTimeoutMS` | Connection timeout | 5000 |
| `socketTimeoutMS` | Socket timeout | 30000 |
| `retryWrites` | Retry write operations | true |
| `w` | Write concern | "majority" |
| `readPreference` | Read preference | primary / secondaryPreferred |
| `authSource` | Auth database | admin |

### Connection Best Practices

1. **Use Connection Pooling**: Never create new connection per request
2. **Set Appropriate Pool Size**: Based on concurrency (e.g., 2-4x threads)
3. **Handle Failover**: Connection domain is stable during failover
4. **Retry Logic**: Implement retry for transient failures
5. **Timeout Configuration**: Set reasonable timeouts
6. **Health Checks**: Periodically check connection health

## MCP Integration (Optional)

### MCP Server Configuration

If using MCP for MongoDB operations:

```json
{
  "mcpServers": {
    "mongodb": {
      "command": "path-to-mongodb-mcp-server",
      "args": ["--access-key", "${JDC_ACCESS_KEY}", "--secret-key", "${JDC_SECRET_KEY}"],
      "env": {
        "JDC_REGION": "cn-north-1"
      }
    }
  }
}
```

### MCP Tools (if available)

- `create_mongodb_instance`: Create MongoDB instance
- `describe_mongodb_instance`: Query instance details
- `list_mongodb_instances`: List all instances
- `modify_mongodb_spec`: Change instance specification
- `create_mongodb_backup`: Create backup
- `restore_mongodb_backup`: Restore from backup

## Security Integration

### IAM Policy for MongoDB

```json
{
  "Version": "2019-05-01",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "mongodb:describe*",
        "mongodb:create*",
        "mongodb:modify*",
        "mongodb:delete*",
        "mongodb:restart*",
        "mongodb:reset*",
        "mongodb:restore*"
      ],
      "Resource": [
        "mongodb:instance:cn-north-1:*"
      ]
    }
  ]
}
```

### Least Privilege Principle

- **Admin**: Full access to all MongoDB operations
- **Operator**: Read + restart + backup (no delete)
- **Viewer**: Read-only (describe operations only)

## Terraform Integration (Optional)

### Terraform Provider Configuration

```hcl
provider "jdcloud" {
  access_key = var.access_key
  secret_key = var.secret_key
  region     = "cn-north-1"
}

resource "jdcloud_mongodb_instance" "example" {
  instance_name     = "terraform-mongodb"
  instance_class    = "mongodb.s.1.large"
  engine_version    = "4.0"
  vpc_id            = var.vpc_id
  subnet_id         = var.subnet_id
  availability_zone = "cn-north-1a"
  
  tags = {
    Environment = "production"
    ManagedBy   = "terraform"
  }
}
```

## Monitoring Integration

### Cloud Monitor Integration

```python
# Query MongoDB metrics from Cloud Monitor
from jdcloud_sdk.services.monitor.client import MonitorClient
from jdcloud_sdk.services.monitor.apis.DescribeMetricsRequest import DescribeMetricsRequest

monitor_client = MonitorClient(credential, region="cn-north-1")

# Query CPU metric
req = DescribeMetricsRequest(
    regionId="cn-north-1",
    resourceType="mongodb",
    metric="mongodb.cpu.usage",
    resourceId="mongodb-xxxx"
)

resp = monitor_client.describe_metrics(req)
cpu_usage = resp.result.metrics[0].value
print(f"CPU Usage: {cpu_usage}%")
```

### Alert Integration

```python
# Create alert rule
from jdcloud_sdk.services.monitor.apis.CreateAlarmRequest import CreateAlarmRequest

req = CreateAlarmRequest(
    regionId="cn-north-1",
    alarmName="mongodb-cpu-high",
    resourceType="mongodb",
    resourceId="mongodb-xxxx",
    metric="mongodb.cpu.usage",
    threshold=90,
    period=300,
    evaluationCount=1,
    notifyType=["email", "sms"]
)

resp = monitor_client.create_alarm(req)
```

## Automation Examples

### Automated Backup Script

```python
#!/usr/bin/env python3
import os
import time
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.mongodb.client import MongodbClient
from jdcloud_sdk.services.mongodb.apis.CreateBackupRequest import CreateBackupRequest

def create_daily_backup(instance_id):
    credential = Credential(os.environ["JDC_ACCESS_KEY"], os.environ["JDC_SECRET_KEY"])
    client = MongodbClient(credential, region=os.environ["JDC_REGION"])
    
    backup_name = f"daily-backup-{time.strftime('%Y%m%d-%H%M%S')}"
    
    req = CreateBackupRequest(
        regionId=os.environ["JDC_REGION"],
        instanceId=instance_id,
        backupName=backup_name
    )
    
    resp = client.create_backup(req)
    backup_id = resp.result.backupId
    
    print(f"Created backup: {backup_name} (ID: {backup_id})")
    return backup_id

# Run daily via cron
if __name__ == "__main__":
    create_daily_backup("mongodb-xxxx")
```

### Automated Scaling Script

```python
#!/usr/bin/env python3
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.mongodb.client import MongodbClient
from jdcloud_sdk.services.mongodb.apis.ModifyInstanceSpecRequest import ModifyInstanceSpecRequest
from jdcloud_sdk.services.mongodb.apis.DescribeInstancesRequest import DescribeInstancesRequest

def scale_if_needed(instance_id, current_spec, target_spec, cpu_threshold=85):
    credential = Credential(os.environ["JDC_ACCESS_KEY"], os.environ["JDC_SECRET_KEY"])
    client = MongodbClient(credential, region=os.environ["JDC_REGION"])
    
    # Check current CPU (would need Monitor client in practice)
    # For this example, assume we check CPU externally
    
    cpu_usage = get_cpu_usage(instance_id)  # Placeholder
    
    if cpu_usage > cpu_threshold:
        print(f"CPU usage {cpu_usage}% exceeds threshold {cpu_threshold}%")
        print(f"Scaling from {current_spec} to {target_spec}")
        
        req = ModifyInstanceSpecRequest(
            regionId=os.environ["JDC_REGION"],
            instanceId=instance_id,
            instanceClass=target_spec
        )
        
        resp = client.modify_instance_spec(req)
        print(f"Scale operation initiated, requestId: {resp.requestId}")
        
        # Wait for completion
        poll_until_terminal(client, instance_id, os.environ["JDC_REGION"])
        print("Scaling completed")
        
        return True
    
    return False
```

## Testing Integration

### Unit Test Example

```python
import pytest
from unittest.mock import Mock, patch
from jdcloud_sdk.services.mongodb.client import MongodbClient

@pytest.fixture
def mongodb_client():
    credential = Mock()
    client = MongodbClient(credential, region="cn-north-1")
    return client

def test_create_instance(mongodb_client):
    # Mock the API call
    mock_response = Mock()
    mock_response.result.instanceId = "mongodb-test-123"
    
    with patch.object(mongodb_client, 'create_instance', return_value=mock_response):
        from jdcloud_sdk.services.mongodb.apis.CreateInstanceRequest import CreateInstanceRequest
        
        req = CreateInstanceRequest(
            regionId="cn-north-1",
            instanceName="test-instance",
            instanceClass="mongodb.s.1.small",
            engineVersion="4.0",
            vpcId="vpc-test",
            subnetId="subnet-test",
            azId="cn-north-1a"
        )
        
        resp = mongodb_client.create_instance(req)
        
        assert resp.result.instanceId == "mongodb-test-123"
```

## Related Documentation

- [API & SDK Usage](api-sdk-usage.md)
- [CLI Usage](cli-usage.md)
- [Core Concepts](core-concepts.md)
- [Monitoring](monitoring.md)
- [Troubleshooting](troubleshooting.md)