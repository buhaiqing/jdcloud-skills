# Integration - JD Cloud Redis

## Python SDK Bootstrap

### Installation

```bash
pip install jdcloud-sdk
```

### Basic Setup

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.redis.client import RedisClient

credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"]
)

client = RedisClient(credential, os.environ.get("JDC_REGION", "cn-north-1"))
```

### Environment Variables

**Method 1: `.env` File (Recommended for Local Development)**
```ini
JDC_ACCESS_KEY=your_access_key_here
JDC_SECRET_KEY=your_secret_key_here
JDC_REGION=cn-north-1
```

**Method 2: Shell Environment Variables (Production)**
```bash
export JDC_ACCESS_KEY="{{env.JDC_ACCESS_KEY}}"
export JDC_SECRET_KEY="{{env.JDC_SECRET_KEY}}"
export JDC_REGION="cn-north-1"  # Default region
```

**Method 3: CLI Interactive Config**
```bash
jdc configure add --access-key YOUR_KEY --secret-key YOUR_SECRET --region-id cn-north-1
```

> **Priority**: Shell env vars > `.env` file > CLI config > Defaults. Never commit `.env` to version control.

> **Security Note**: Use `os.environ['KEY']` for secrets (fail-fast if missing). Use `.get` only for optional non-secret config.

### SDK Package Structure

- `jdcloud_sdk.services.redis.client.RedisClient`: Main client class
- `jdcloud_sdk.services.redis.apis.*`: Request classes for each API
- `jdcloud_sdk.services.redis.models.*`: Response and data models

## JD Cloud CLI Setup

### Installation

```bash
pip install jdcloud_cli
```

### Configuration

Interactive configuration:
```bash
jdc configure add \
  --access-key YOUR_ACCESS_KEY \
  --secret-key YOUR_SECRET_KEY \
  --region-id cn-north-1
```

Non-interactive configuration (for automation):
```bash
export JDC_ACCESS_KEY="YOUR_ACCESS_KEY"
export JDC_SECRET_KEY="YOUR_SECRET_KEY"
export JDC_REGION="cn-north-1"
```

### Verify Installation

```bash
jdc --version
jdc redis help
```

### Auto-Complete Setup (Optional)

```bash
# Bash
echo 'eval "$(register-python-argcomplete jdc)"' >> ~/.bashrc
source ~/.bashrc

# Zsh (macOS)
echo 'eval "$(register-python-argcomplete jdc)"' >> ~/.zshrc
source ~/.zshrc
```

## Redis Client Connection

After creating a Redis instance, connect using standard Redis clients:

### Connection Parameters

From `describeCacheInstance` response:
- `connectionDomain`: Redis connection address
- `port`: Redis port (default: 6379)
- `password`: Redis authentication password

### Python Redis Client (redis-py)

```python
import redis

# Get connection info from JD Cloud Redis API
# connection_domain = resp.result.cacheInstance.connectionDomain
# port = resp.result.cacheInstance.port
# password = user_provided_password

r = redis.Redis(
    host='redis-xxx.redis.jdcloud.com',
    port=6379,
    password='YourPassword',
    decode_responses=True
)

# Test connection
r.ping()  # Returns True if successful
```

### Jedis (Java)

```java
import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPool;
import redis.clients.jedis.JedisPoolConfig;

JedisPoolConfig poolConfig = new JedisPoolConfig();
poolConfig.setMaxTotal(100);
poolConfig.setMaxIdle(20);
poolConfig.setMinIdle(5);

JedisPool jedisPool = new JedisPool(
    poolConfig,
    "redis-xxx.redis.jdcloud.com",
    6379,
    2000,  // timeout
    "YourPassword"
);

try (Jedis jedis = jedisPool.getResource()) {
    jedis.ping();
}
```

### Node.js (ioredis)

```javascript
const Redis = require('ioredis');

const redis = new Redis({
  host: 'redis-xxx.redis.jdcloud.com',
  port: 6379,
  password: 'YourPassword',
  // For cluster version
  // slotsRefreshTimeout: 1000,
});

redis.ping().then(result => {
  console.log('Connected:', result);
});
```

### Go (go-redis)

```go
import "github.com/go-redis/redis/v8"

rdb := redis.NewClient(&redis.Options{
    Addr:     "redis-xxx.redis.jdcloud.com:6379",
    Password: "YourPassword",
    DB:       0,
})

ctx := context.Background()
status, err := rdb.Ping(ctx).Result()
if err != nil {
    panic(err)
}
fmt.Println("Connected:", status)
```

### Cluster Version Connection

For native-cluster instances, use cluster-aware clients:

```python
from redis.cluster import RedisCluster as Redis

# Native cluster connection
rc = Redis(
    host='redis-xxx.redis.jdcloud.com',
    port=6379,
    password='YourPassword',
    decode_responses=True
)
```

Or use SmartProxy for standard client compatibility (if enabled during creation).

## VPC Network Integration

### Prerequisites

Redis instances must be created in a VPC with subnet:

1. Create or identify VPC via `jdcloud-vpc-ops`
2. Create subnet with sufficient IP addresses
3. Subnet CIDR must accommodate instance nodes (master + slaves + proxies)

### Network Requirements

- Subnet must have available IPs (at least 4 for standard, more for cluster)
- Application servers should be in same VPC for optimal latency
- Security groups must allow Redis port (6379)
- Cross-VPC access requires special configuration

### Network Configuration

```python
# When creating Redis instance, specify VPC/subnet
cache_instance_spec = {
    "vpcId": "{{user.vpc_id}}",  # From jdcloud-vpc-ops
    "subnetId": "{{user.subnet_id}}",  # From jdcloud-vpc-ops
    ...
}
```

## IAM Integration

### Access Control

JD Cloud Redis supports IAM for access control:

- Access keys must have appropriate IAM permissions
- IAM policies control who can create, modify, delete Redis instances
- Account-level permissions (Redis 6.2+) for fine-grained Redis ACL

### IAM Policy Example

```json
{
  "Version": "2019-05-01",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "redis:createCacheInstance",
        "redis:describeCacheInstance",
        "redis:modifyCacheInstanceAttribute"
      ],
      "Resource": [
        "redis:cn-north-1:*"
      ]
    }
  ]
}
```

### Redis Account Management (Redis 6.2+)

```bash
# Create Redis ACL account
jdc redis create-account \
  --region-id "{{user.region}}" \
  --cache-instance-id "{{user.instance_id}}" \
  --account-name "readonly_user" \
  --account-password "SecurePassword" \
  --account-privilege "read" \
  --output json
```

## Cloud Monitor Integration

### Delegate Monitoring Tasks

Monitoring and alerting for Redis is handled by `jdcloud-cloudmonitor-ops`:

- Query Redis metrics (CPU, memory, connections, QPS)
- Configure alert rules
- View metric dashboards
- Access historical metric data

### Example Integration

```python
# When CPU alert triggers, scale up Redis
# (Automated workflow integrating Cloud Monitor and Redis)

# 1. Cloud Monitor detects high CPU
# 2. Trigger workflow to call modifyCacheInstanceClass
# 3. Redis scales up
# 4. Cloud Monitor continues tracking metrics
```

## Backup Integration with Object Storage

### Backup Storage

- Redis backups are stored in JD Cloud infrastructure
- Backup files can be downloaded via `describeDownloadUrl`
- For long-term retention, download and store in Object Storage

### Download Backup

```bash
jdc redis describe-download-url \
  --region-id "{{user.region}}" \
  --cache-instance-id "{{user.instance_id}}" \
  --backup-id "{{backup_id}}" \
  --output json
```

Store backup in Object Storage (delegate to `jdcloud-oss-ops` if skill exists):

```bash
# Download backup file
curl -o backup.rdb "$(jq -r '.result.downloadUrl' response.json)"

# Upload to Object Storage for long-term retention
# Use jdcloud-oss-ops skill if available
```

## Data Migration Integration

### Migration Tools

JD Cloud provides RDTS (Redis Data Transfer Service) for migration:
- Online migration with minimal downtime
- Support for cross-cloud migration
- Data verification after migration

### Self-managed Migration

Using redis-cli for offline migration:

```bash
# Source Redis
redis-cli -h source.redis.host -p 6379 --rdb /tmp/dump.rdb

# Import to JD Cloud Redis
cat /tmp/dump.rdb | redis-cli -h redis-xxx.redis.jdcloud.com -p 6379 -a password --pipe
```

## Application Integration Patterns

### Session Cache Pattern

```python
# Store user session in Redis
session_key = f"session:{user_id}"
r.setex(session_key, 3600, json.dumps(session_data))

# Retrieve session
session_data = r.get(session_key)
if session_data:
    session = json.loads(session_data)
```

### Data Cache Pattern

```python
# Cache database query results
def get_user_info(user_id):
    cache_key = f"user:{user_id}"
    cached = r.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Query from database
    user_info = db.query_user(user_id)
    # Cache for 1 hour
    r.setex(cache_key, 3600, json.dumps(user_info))
    return user_info
```

### Rate Limiting Pattern

```python
# Rate limiting with Redis
def check_rate_limit(user_id, limit=100):
    key = f"ratelimit:{user_id}"
    count = r.incr(key)
    if count == 1:
        r.expire(key, 60)  # 1 minute window
    return count <= limit
```

### Leaderboard Pattern

```python
# Gaming leaderboard with Sorted Set
r.zadd("leaderboard", {user_id: score})
top_10 = r.zrevrange("leaderboard", 0, 9, withscores=True)
```

## Integration Testing

### Test Connection

```python
def test_redis_connection():
    try:
        return r.ping()
    except redis.ConnectionError:
        return False
```

### Test Operations

```python
def test_redis_operations():
    # Test basic operations
    r.set("test_key", "test_value")
    assert r.get("test_key") == "test_value"
    r.delete("test_key")
    assert r.get("test_key") is None
    return True
```

## CI/CD Integration

### Infrastructure as Code

Use JD Cloud Redis API in deployment pipelines:

```yaml
# Example: Create Redis instance in deployment pipeline
- name: Create Redis Instance
  run: |
    jdc redis create-cache-instance \
      --region-id "${{ env.REGION }}" \
      --cache-instance-name "app-redis-${{ env.ENV }}" \
      --cache-instance-class "${{ env.REDIS_SPEC }}" \
      --vpc-id "${{ env.VPC_ID }}" \
      --subnet-id "${{ env.SUBNET_ID }}" \
      --output json > redis_info.json
    
    REDIS_ID=$(jq -r '.result.cacheInstanceId' redis_info.json)
    echo "REDIS_INSTANCE_ID=$REDIS_ID" >> $GITHUB_ENV
```

### Environment Configuration

Configure application environment with Redis connection:

```yaml
- name: Configure Redis Connection
  run: |
    REDIS_HOST=$(jdc redis describe-cache-instance \
      --region-id "${{ env.REGION }}" \
      --cache-instance-id "${{ env.REDIS_INSTANCE_ID }}" \
      --output json | jq -r '.result.cacheInstance.connectionDomain')
    
    echo "REDIS_HOST=$REDIS_HOST" >> $GITHUB_ENV
    echo "REDIS_PORT=6379" >> $GITHUB_ENV
```

## MCP Server Integration

If MCP server is configured for JD Cloud Redis, additional tools may be available for enhanced integration.

Check MCP server capabilities:
- List MCP servers in workspace
- Review available tools for Redis operations
- Integrate MCP tools into workflows if applicable