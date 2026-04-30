# Integration & Tooling


## SDK Initialization

### Python SDK

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.jcsforredis.client import JcsforredisClient
from jdcloud_sdk.services.jcsforredis.models import CreateCacheInstanceRequest

# Initialize credential
credential = Credential(
    os.environ['JDC_ACCESS_KEY'],
    os.environ['JDC_SECRET_KEY']
)

# Initialize client
client = JcsforredisClient(
    credential, 
    os.environ.get('JDC_REGION', 'cn-north-1')
)

# Create instance
request = CreateCacheInstanceRequest(
    region_id='cn-north-1',
    az_id='cn-north-1a',
    cache_instance_name='my-redis-instance',
    instance_class='redis.sw.4g',
    vpc_id='vpc-abc123',
    subnet_id='subnet-def456',
    password='MyStr0ng!Pass#2026',
    redis_version='6.2',
    charge_mode='postpaid_by_duration'
)

response = client.create_cache_instance(request)
print(f"Instance ID: {response.result.instance_id}")
```

> Rule: Use `os.environ['KEY']` (not `.get()`) for credentials to fail-fast if missing. Use `os.environ.get('KEY', default)` for optional config like region.

### Java SDK

```java
import com.jdcloud.sdk.auth.CredentialsProvider;
import com.jdcloud.sdk.auth.StaticCredentialsProvider;
import com.jdcloud.sdk.http.HttpRequestConfig;
import com.jdcloud.sdk.http.Protocol;
import com.jdcloud.sdk.client.Client;
import com.jdcloud.sdk.client.DefaultClient;
import com.jdcloud.sdk.client.Environment;
import com.jdcloud.sdk.service.jcsforredis.client.JcsforredisClient;
import com.jdcloud.sdk.service.jcsforredis.model.CreateCacheInstanceRequest;
import com.jdcloud.sdk.service.jcsforredis.model.CreateCacheInstanceResponse;

public class RedisExample {
    public static void main(String[] args) {
        // Initialize credentials
        String accessKeyId = System.getenv("JDC_ACCESS_KEY");
        String secretAccessKey = System.getenv("JDC_SECRET_KEY");
        
        CredentialsProvider credentialsProvider = new StaticCredentialsProvider(
            accessKeyId, 
            secretAccessKey
        );
        
        // Initialize client
        Client client = new DefaultClient.Builder()
            .credentialsProvider(credentialsProvider)
            .httpRequestConfig(new HttpRequestConfig.Builder()
                .protocol(Protocol.HTTPS)
                .build())
            .environment(Environment.fromValue(System.getenv("JDC_REGION")))
            .build();
        
        JcsforredisClient redisClient = new JcsforredisClient(client);
        
        // Create instance
        CreateCacheInstanceRequest request = new CreateCacheInstanceRequest();
        request.setRegionId("cn-north-1");
        request.setAzId("cn-north-1a");
        request.setCacheInstanceName("my-redis-instance");
        request.setInstanceClass("redis.sw.4g");
        request.setVpcId("vpc-abc123");
        request.setSubnetId("subnet-def456");
        request.setPassword("MyStr0ng!Pass#2026");
        request.setRedisVersion("6.2");
        request.setChargeMode("postpaid_by_duration");
        
        CreateCacheInstanceResponse response = redisClient.createCacheInstance(request);
        System.out.println("Instance ID: " + response.getResult().getInstanceId());
    }
}
```

### Go SDK

```go
package main

import (
    "fmt"
    "os"
    
    "github.com/jdcloud-api/jdcloud-sdk-go/core"
    "github.com/jdcloud-api/jdcloud-sdk-go/services/jcsforredis"
)

func main() {
    // Initialize credentials
    accessKey := os.Getenv("JDC_ACCESS_KEY")
    secretKey := os.Getenv("JDC_SECRET_KEY")
    region := os.Getenv("JDC_REGION")
    if region == "" {
        region = "cn-north-1"
    }
    
    // Initialize client
    config := &core.Config{
        AccessKey:  accessKey,
        SecretKey:  secretKey,
        Region:     region,
        Scheme:     "https",
    }
    
    redisClient := jcsforredis.NewJcsforredisClient(config)
    
    // Create instance
    request := jcsforredis.NewCreateCacheInstanceRequest(
        "cn-north-1",
        "cn-north-1a",
        "my-redis-instance",
        "redis.sw.4g",
        "vpc-abc123",
        "subnet-def456",
        "MyStr0ng!Pass#2026",
        "6.2",
        "postpaid_by_duration",
    )
    
    response, err := redisClient.CreateCacheInstance(request)
    if err != nil {
        fmt.Printf("Error: %v\n", err)
        return
    }
    
    fmt.Printf("Instance ID: %s\n", response.Result.InstanceId)
}
```

## Redis Client Connection Examples

### Python (redis-py)

```python
import redis
import os

# Connection configuration
REDIS_HOST = os.environ.get('REDIS_HOST', 'your-redis-endpoint')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', 'your-password')

# Create connection pool
pool = redis.ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    max_connections=50,
    socket_timeout=5,
    socket_connect_timeout=5,
    retry_on_timeout=True,
    decode_responses=True
)

# Create Redis client
r = redis.Redis(connection_pool=pool)

# Test connection
try:
    r.ping()
    print("Connected to Redis successfully")
except redis.ConnectionError as e:
    print(f"Failed to connect to Redis: {e}")

# Example operations
r.set('mykey', 'myvalue', ex=3600)  # Set with 1 hour TTL
value = r.get('mykey')
print(f"Value: {value}")

# Use pipeline for batch operations
pipe = r.pipeline()
pipe.set('key1', 'value1')
pipe.set('key2', 'value2')
pipe.incr('counter')
results = pipe.execute()
print(f"Pipeline results: {results}")
```

### Java (Jedis)

```java
import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPool;
import redis.clients.jedis.JedisPoolConfig;

public class RedisClientExample {
    private static JedisPool pool;
    
    public static void initPool() {
        String host = System.getenv("REDIS_HOST");
        int port = Integer.parseInt(System.getenv("REDIS_PORT"));
        String password = System.getenv("REDIS_PASSWORD");
        
        JedisPoolConfig poolConfig = new JedisPoolConfig();
        poolConfig.setMaxTotal(50);
        poolConfig.setMaxIdle(20);
        poolConfig.setMinIdle(10);
        poolConfig.setMaxWaitMillis(3000);
        poolConfig.setTestOnBorrow(true);
        poolConfig.setTestOnReturn(true);
        
        pool = new JedisPool(poolConfig, host, port, 3000, password);
    }
    
    public static void main(String[] args) {
        initPool();
        
        try (Jedis jedis = pool.getResource()) {
            // Test connection
            System.out.println(jedis.ping());
            
            // Set with TTL
            jedis.setex("mykey", 3600, "myvalue");
            
            // Get value
            String value = jedis.get("mykey");
            System.out.println("Value: " + value);
            
            // Use pipeline
            Pipeline pipeline = jedis.pipelined();
            pipeline.set("key1", "value1");
            pipeline.set("key2", "value2");
            pipeline.incr("counter");
            List<Object> results = pipeline.syncAndReturnAll();
            System.out.println("Pipeline results: " + results);
        }
    }
}
```

### Java (Lettuce)

```java
import io.lettuce.core.RedisClient;
import io.lettuce.core.RedisURI;
import io.lettuce.core.api.StatefulRedisConnection;
import io.lettuce.core.api.sync.RedisCommands;
import io.lettuce.core.resource.ClientResources;
import io.lettuce.core.resource.DefaultClientResources;

public class LettuceExample {
    public static void main(String[] args) {
        String host = System.getenv("REDIS_HOST");
        int port = Integer.parseInt(System.getenv("REDIS_PORT"));
        String password = System.getenv("REDIS_PASSWORD");
        
        // Build Redis URI
        RedisURI redisUri = RedisURI.builder()
            .withHost(host)
            .withPort(port)
            .withPassword(password.toCharArray())
            .build();
        
        // Create client with resources
        ClientResources resources = DefaultClientResources.create();
        RedisClient client = RedisClient.create(resources, redisUri);
        
        // Connect
        StatefulRedisConnection<String, String> connection = client.connect();
        RedisCommands<String, String> commands = connection.sync();
        
        // Test connection
        System.out.println(commands.ping());
        
        // Operations
        commands.setex("mykey", 3600, "myvalue");
        String value = commands.get("mykey");
        System.out.println("Value: " + value);
        
        // Close
        connection.close();
        client.shutdown();
        resources.shutdown();
    }
}
```

### Node.js (ioredis)

```javascript
const Redis = require('ioredis');

// Create Redis client
const redis = new Redis({
  host: process.env.REDIS_HOST || 'your-redis-endpoint',
  port: parseInt(process.env.REDIS_PORT || '6379'),
  password: process.env.REDIS_PASSWORD || 'your-password',
  maxRetriesPerRequest: 3,
  retryStrategy: (times) => {
    const delay = Math.min(times * 50, 2000);
    return delay;
  },
  reconnectOnError: (err) => {
    const targetError = 'READONLY';
    if (err.message.includes(targetError)) {
      return true;
    }
    return false;
  },
});

redis.on('connect', () => {
  console.log('Connected to Redis');
});

redis.on('error', (err) => {
  console.error('Redis connection error:', err);
});

// Test connection
redis.ping((err, result) => {
  if (err) {
    console.error('Ping failed:', err);
  } else {
    console.log('Ping result:', result);
  }
});

// Operations
async function example() {
  // Set with TTL
  await redis.setex('mykey', 3600, 'myvalue');
  
  // Get value
  const value = await redis.get('mykey');
  console.log('Value:', value);
  
  // Use pipeline
  const pipeline = redis.pipeline();
  pipeline.set('key1', 'value1');
  pipeline.set('key2', 'value2');
  pipeline.incr('counter');
  const results = await pipeline.exec();
  console.log('Pipeline results:', results);
}

example();
```

### Go (go-redis)

```go
package main

import (
    "context"
    "fmt"
    "os"
    "time"
    
    "github.com/go-redis/redis/v8"
)

var ctx = context.Background()

func main() {
    // Create Redis client
    rdb := redis.NewClient(&redis.Options{
        Addr:         os.Getenv("REDIS_HOST") + ":" + os.Getenv("REDIS_PORT"),
        Password:     os.Getenv("REDIS_PASSWORD"),
        DB:           0,
        MaxRetries:   3,
        DialTimeout:  5 * time.Second,
        ReadTimeout:  3 * time.Second,
        WriteTimeout: 3 * time.Second,
        PoolSize:     50,
        MinIdleConns: 10,
    })
    
    // Test connection
    pong, err := rdb.Ping(ctx).Result()
    if err != nil {
        fmt.Printf("Failed to connect: %v\n", err)
        return
    }
    fmt.Println("Connected:", pong)
    
    // Set with TTL
    err = rdb.Set(ctx, "mykey", "myvalue", 1*time.Hour).Err()
    if err != nil {
        fmt.Printf("Set error: %v\n", err)
        return
    }
    
    // Get value
    val, err := rdb.Get(ctx, "mykey").Result()
    if err != nil {
        fmt.Printf("Get error: %v\n", err)
        return
    }
    fmt.Println("Value:", val)
    
    // Use pipeline
    pipe := rdb.Pipeline()
    pipe.Set(ctx, "key1", "value1", 0)
    pipe.Set(ctx, "key2", "value2", 0)
    pipe.Incr(ctx, "counter")
    cmds, err := pipe.Exec(ctx)
    if err != nil {
        fmt.Printf("Pipeline error: %v\n", err)
        return
    }
    fmt.Println("Pipeline results:", cmds)
}
```

## Infrastructure as Code

### Terraform

```hcl
provider "jdcloud" {
  access_key = var.jdcloud_access_key
  secret_key = var.jdcloud_secret_key
  region     = var.jdcloud_region
}

variable "jdcloud_access_key" {
  type      = string
  sensitive = true
}

variable "jdcloud_secret_key" {
  type      = string
  sensitive = true
}

variable "jdcloud_region" {
  type    = string
  default = "cn-north-1"
}

resource "jdcloud_jcsforredis_cache_instance" "redis_prod" {
  az_id              = "cn-north-1a"
  cache_instance_name = "prod-redis-01"
  instance_class     = "redis.sw.8g"
  vpc_id             = jdcloud_vpc.main.id
  subnet_id          = jdcloud_subnet.redis.id
  password           = var.redis_password
  redis_version      = "6.2"
  charge_mode        = "postpaid_by_duration"
  
  tags = {
    Environment = "production"
    ManagedBy   = "terraform"
  }
}

resource "jdcloud_jcsforredis_ip_white_list" "redis_whitelist" {
  cache_instance_id = jdcloud_jcsforredis_cache_instance.redis_prod.id
  ip_white_list     = ["10.0.1.0/24", "10.0.2.0/24"]
}

output "redis_endpoint" {
  value = "${jdcloud_jcsforredis_cache_instance.redis_prod.connection_domain}:${jdcloud_jcsforredis_cache_instance.redis_prod.connection_port}"
}

output "redis_instance_id" {
  value = jdcloud_jcsforredis_cache_instance.redis_prod.id
}
```

### Pulumi (Python)

```python
import pulumi
import pulumi_jdcloud as jdcloud

# Create VPC
vpc = jdcloud.vpc.Vpc("redis-vpc",
    vpc_name="redis-vpc",
    address_cidr="10.0.0.0/16"
)

# Create subnet
subnet = jdcloud.vpc.Subnet("redis-subnet",
    vpc_id=vpc.id,
    subnet_name="redis-subnet",
    address_cidr="10.0.1.0/24",
    az_id="cn-north-1a"
)

# Create Redis instance
redis_instance = jdcloud.jcsforredis.CacheInstance("prod-redis",
    az_id="cn-north-1a",
    cache_instance_name="prod-redis-01",
    instance_class="redis.sw.8g",
    vpc_id=vpc.id,
    subnet_id=subnet.id,
    password=pulumi.Config("redis").get("password"),
    redis_version="6.2",
    charge_mode="postpaid_by_duration"
)

# Export connection info
pulumi.export("redis_endpoint", 
    redis_instance.connection_domain.apply(lambda d: f"{d}:6379"))
pulumi.export("redis_instance_id", redis_instance.id)
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Deploy Redis Infrastructure

on:
  push:
    branches: [main]
    paths:
      - 'infrastructure/redis/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup JD Cloud CLI
        run: |
          pip install jdcloud_cli
          jdc configure add \
            --access-key ${{ secrets.JDC_ACCESS_KEY }} \
            --secret-key ${{ secrets.JDC_SECRET_KEY }} \
            --region-id cn-north-1
      
      - name: Deploy Redis Instance
        run: |
          jdc redis create-cache-instance \
            --region-id cn-north-1 \
            --az-id "cn-north-1a" \
            --cache-instance-name "ci-redis-${{ github.sha }}" \
            --instance-class "redis.sw.4g" \
            --vpc-id "vpc-abc123" \
            --subnet-id "subnet-def456" \
            --password "${{ secrets.REDIS_PASSWORD }}" \
            --redis-version "6.2" \
            --charge-mode "postpaid_by_duration" \
            --output json
        env:
          JDC_ACCESS_KEY: ${{ secrets.JDC_ACCESS_KEY }}
          JDC_SECRET_KEY: ${{ secrets.JDC_SECRET_KEY }}
```

### GitLab CI

```yaml
stages:
  - deploy

deploy-redis:
  stage: deploy
  image: python:3.10
  script:
    - pip install jdcloud_cli
    - jdc configure add --access-key $JDC_ACCESS_KEY --secret-key $JDC_SECRET_KEY --region-id cn-north-1
    - jdc redis create-cache-instance --region-id cn-north-1 --az-id "cn-north-1a" --cache-instance-name "ci-redis-$CI_COMMIT_SHA" --instance-class "redis.sw.4g" --vpc-id "vpc-abc123" --subnet-id "subnet-def456" --password "$REDIS_PASSWORD" --redis-version "6.2" --charge-mode "postpaid_by_duration" --output json
  only:
    - main
  variables:
    JDC_ACCESS_KEY: $JDC_ACCESS_KEY
    JDC_SECRET_KEY: $JDC_SECRET_KEY
    REDIS_PASSWORD: $REDIS_PASSWORD
```

## Testing

### Connection Test Script

```bash
#!/bin/bash

# Redis Connection Test Script
# Usage: ./test-redis-connection.sh <endpoint> <port> <password>

ENDPOINT=$1
PORT=${2:-6379}
PASSWORD=$3

if [ -z "$ENDPOINT" ] || [ -z "$PASSWORD" ]; then
  echo "Usage: $0 <endpoint> [port] <password>"
  exit 1
fi

echo "Testing Redis connection..."
echo "Endpoint: $ENDPOINT:$PORT"

# Install redis-cli if not present
if ! command -v redis-cli &> /dev/null; then
  echo "Installing redis-cli..."
  apt-get update && apt-get install -y redis-tools
fi

# Test connection
RESULT=$(redis-cli -h "$ENDPOINT" -p "$PORT" -a "$PASSWORD" ping 2>&1)

if [ "$RESULT" == "PONG" ]; then
  echo "✅ Connection successful!"
  
  # Test write
  redis-cli -h "$ENDPOINT" -p "$PORT" -a "$PASSWORD" set test_key "test_value" EX 60
  echo "✅ Write test passed"
  
  # Test read
  VALUE=$(redis-cli -h "$ENDPOINT" -p "$PORT" -a "$PASSWORD" get test_key)
  if [ "$VALUE" == "test_value" ]; then
    echo "✅ Read test passed"
  else
    echo "❌ Read test failed"
    exit 1
  fi
  
  # Test delete
  redis-cli -h "$ENDPOINT" -p "$PORT" -a "$PASSWORD" del test_key
  echo "✅ Delete test passed"
  
  # Get info
  echo ""
  echo "=== Redis Info ==="
  redis-cli -h "$ENDPOINT" -p "$PORT" -a "$PASSWORD" INFO server | grep -E "redis_version|tcp_port|uptime"
  redis-cli -h "$ENDPOINT" -p "$PORT" -a "$PASSWORD" INFO memory | grep -E "used_memory_human|maxmemory_human"
  
else
  echo "❌ Connection failed: $RESULT"
  exit 1
fi
```

### Performance Test Script

```bash
#!/bin/bash

# Redis Performance Test Script
# Usage: ./test-redis-performance.sh <endpoint> <port> <password>

ENDPOINT=$1
PORT=${2:-6379}
PASSWORD=$3

echo "Running Redis performance test..."
echo "Endpoint: $ENDPOINT:$PORT"

# Install redis-tools if not present
if ! command -v redis-benchmark &> /dev/null; then
  echo "Installing redis-tools..."
  apt-get update && apt-get install -y redis-tools
fi

# Run benchmark
redis-benchmark \
  -h "$ENDPOINT" \
  -p "$PORT" \
  -a "$PASSWORD" \
  -t set,get,incr,lpush,lpop \
  -c 50 \
  -n 10000 \
  -r 100000
```

## Security Best Practices

### 1. Credential Management

**NEVER** hardcode credentials in code or configuration files:

```python
# ❌ BAD
password = "MyRedisPassword123"

# ✅ GOOD
password = os.environ['REDIS_PASSWORD']
```

### 2. Use Environment Variables

```bash
# .env file (add to .gitignore)
REDIS_HOST=your-redis-endpoint
REDIS_PORT=6379
REDIS_PASSWORD=your-secure-password
JDC_ACCESS_KEY=your-access-key
JDC_SECRET_KEY=your-secret-key
JDC_REGION=cn-north-1
```

### 3. Use Secret Management Services

- **JD Cloud KMS**: Store and manage secrets
- **HashiCorp Vault**: Centralized secret management
- **AWS Secrets Manager**: If using multi-cloud
- **Kubernetes Secrets**: For containerized applications

### 4. Network Security

- Use VPC private network (never public endpoint for production)
- Configure IP whitelist (only allow application server IPs)
- Use security groups to control access
- Enable TLS if supported (for data in transit encryption)

### 5. IAM Policies

Create dedicated IAM user for Redis operations:

```json
{
  "Version": "1",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "jcsforredis:DescribeCacheInstance",
        "jcsforredis:DescribeCacheInstances",
        "jcsforredis:CreateCacheInstance",
        "jcsforredis:DeleteCacheInstance"
      ],
      "Resource": "*"
    }
  ]
}
```

## Troubleshooting Integration Issues

### Issue 1: SDK Authentication Failed

**Symptoms:**
- `InvalidAccessKeyId` error
- `SignatureDoesNotMatch` error

**Solutions:**
1. Verify access key and secret key are correct
2. Check system time (must be synchronized)
3. Verify region configuration
4. Test with CLI first: `jdc redis describe-cache-instances --output json`

### Issue 2: Connection Timeout

**Symptoms:**
- Client cannot connect to Redis
- Timeout errors

**Solutions:**
1. Verify endpoint and port
2. Check IP whitelist includes client IP
3. Verify VPC and subnet configuration
4. Test network connectivity: `telnet <endpoint> <port>`
5. Check instance status is `running`

### Issue 3: SDK Version Compatibility

**Symptoms:**
- Import errors
- Missing methods

**Solutions:**
1. Check SDK version compatibility with CLI version
2. Update SDK: `pip install --upgrade jdcloud-sdk-python`
3. Refer to SDK documentation for version matrix

## Additional Resources

- [JD Cloud CLI Documentation](https://docs.jdcloud.com/cn/cli/introduction)
- [JD Cloud Python SDK](https://github.com/jdcloud-api/jdcloud-sdk-python)
- [JD Cloud Java SDK](https://github.com/jdcloud-api/jdcloud-sdk-java)
- [JD Cloud Go SDK](https://github.com/jdcloud-api/jdcloud-sdk-go)
- [Redis Official Documentation](https://redis.io/documentation)
- [Agent Skill OpenSpec](https://agentskills.io/specification)
