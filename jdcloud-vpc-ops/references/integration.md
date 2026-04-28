# JD Cloud VPC Integration & Tooling

## Idempotency in Integration

All integration patterns in this document support **idempotent operations** to ensure safe retries and consistent state management.

### Idempotency Patterns in SDK

#### Python SDK Idempotent Create
```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.vpc.client import VpcClient
from jdcloud_sdk.services.vpc.models import CreateVpcRequest, DescribeVpcsRequest

def create_vpc_idempotent(client, region, vpc_name, cidr_block):
    """Create VPC idempotently - returns existing or creates new"""
    # Check if VPC already exists
    describe_request = DescribeVpcsRequest(region)
    response = client.describe_vpcs(describe_request)
    
    for vpc in response.result.vpcs:
        if vpc.vpc_name == vpc_name:
            print(f"VPC '{vpc_name}' already exists with ID: {vpc.vpc_id}")
            return vpc.vpc_id
    
    # Create new VPC
    create_request = CreateVpcRequest(
        region=region,
        vpc_name=vpc_name,
        cidr_block=cidr_block
    )
    
    create_response = client.create_vpc(create_request)
    print(f"Created new VPC with ID: {create_response.result.vpc_id}")
    return create_response.result.vpc_id

# Usage
credential = Credential(os.environ['JDC_ACCESS_KEY'], os.environ['JDC_SECRET_KEY'])
client = VpcClient(credential, os.environ.get('JDC_REGION', 'cn-north-1'))
vpc_id = create_vpc_idempotent(client, 'cn-north-1', 'my-vpc', '10.0.0.0/16')
```

## MCP Server Configuration

### VPC MCP Server
```json
{
  "mcpServers": {
    "jdcloud-vpc": {
      "command": "uvx", 
      "args": ["run", "--python", "3.10", "@jdcloud/vpc-mcp"],
      "env": {
        "JDC_ACCESS_KEY": "{{env.JDC_ACCESS_KEY}}",
        "JDC_SECRET_KEY": "{{env.JDC_SECRET_KEY}}",
        "JDC_REGION": "{{env.JDC_REGION}}"
      }
    }
  }
}
```
> Note: MCP servers are developed with Python 3.10+ and launched using `uvx` command. Environment variables MUST be set in the Agent runtime environment. NEVER hardcode credentials in configuration files. The `{{env.*}}` placeholders are resolved by the Agent harness at runtime.

### Monitoring MCP Server
```json
{
  "mcpServers": {
    "jdcloud-monitor": {
      "command": "uvx", 
      "args": ["run", "--python", "3.10", "@jdcloud/monitor-mcp"],
      "env": {
        "JDC_ACCESS_KEY": "{{env.JDC_ACCESS_KEY}}",
        "JDC_SECRET_KEY": "{{env.JDC_SECRET_KEY}}",
        "JDC_REGION": "{{env.JDC_REGION}}"
      }
    }
  }
}
```

## SDK Integration

### Python SDK Initialization
```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.vpc.client import VpcClient

# Initialize credentials
credential = Credential(
    os.environ['JDC_ACCESS_KEY'],
    os.environ['JDC_SECRET_KEY']
)

# Create VPC client
client = VpcClient(credential, os.environ.get('JDC_REGION', 'cn-north-1'))

# Example: Create VPC
from jdcloud_sdk.services.vpc.models import CreateVpcRequest

request = CreateVpcRequest(
    region='cn-north-1',
    vpc_name='my-vpc',
    cidr_block='10.0.0.0/16',
    description='My test VPC'
)

response = client.create_vpc(request)
print(response.result)
```

### Go SDK Idempotent Delete
```go
package main

import (
    "fmt"
    "os"
    "github.com/jdcloud-api/jdcloud-sdk-go/core"
    "github.com/jdcloud-api/jdcloud-sdk-go/services/vpc/client"
    "github.com/jdcloud-api/jdcloud-sdk-go/services/vpc/models"
)

func deleteVpcIdempotent(vpcClient *client.VpcClient, vpcId, region string) error {
    // Check if VPC exists
    describeRequest := &models.DescribeVpcRequest{
        VpcId:  vpcId,
        Region: region,
    }
    
    _, describeErr := vpcClient.DescribeVpc(describeRequest)
    if describeErr != nil {
        // VPC doesn't exist, delete is idempotent
        fmt.Printf("VPC %s already deleted or doesn't exist\n", vpcId)
        return nil
    }
    
    // Delete VPC
    deleteRequest := &models.DeleteVpcRequest{
        VpcId:  vpcId,
        Region: region,
    }
    
    _, deleteErr := vpcClient.DeleteVpc(deleteRequest)
    if deleteErr != nil {
        return fmt.Errorf("failed to delete VPC: %v", deleteErr)
    }
    
    fmt.Printf("Deleted VPC: %s\n", vpcId)
    return nil
}

func main() {
    credential := core.NewCredential(
        os.Getenv("JDC_ACCESS_KEY"),
        os.Getenv("JDC_SECRET_KEY"),
    )
    
    vpcClient := client.NewVpcClient(credential, "cn-north-1")
    
    err := deleteVpcIdempotent(vpcClient, "vpc-abc123def", "cn-north-1")
    if err != nil {
        fmt.Printf("Error: %v\n", err)
        return
    }
}
```

### Java SDK Initialization
```java
import com.jdcloud.sdk.auth.Credential;
import com.jdcloud.sdk.services.vpc.client.VpcClient;
import com.jdcloud.sdk.services.vpc.models.CreateVpcRequest;

public class VpcExample {
    public static void main(String[] args) {
        // Initialize credentials
        Credential credential = new Credential(
            System.getenv("JDC_ACCESS_KEY"),
            System.getenv("JDC_SECRET_KEY")
        );
        
        // Create VPC client
        VpcClient client = new VpcClient(credential, "cn-north-1");
        
        // Example: Create VPC
        CreateVpcRequest request = new CreateVpcRequest();
        request.setRegion("cn-north-1");
        request.setVpcName("my-vpc");
        request.setCidrBlock("10.0.0.0/16");
        request.setDescription("My test VPC");
        
        // Execute request
        // Note: Actual implementation depends on SDK version
    }
}
```

## Infrastructure as Code

### Terraform Integration
```hcl
# main.tf
provider "jdcloud" {
  access_key = var.JDC_ACCESS_KEY
  secret_key = var.JDC_SECRET_KEY
  region     = var.JDC_REGION
}

# Create VPC
resource "jdcloud_vpc" "main" {
  vpc_name   = "my-vpc"
  cidr_block = "10.0.0.0/16"
  region     = "cn-north-1"
  
  tags = {
    Environment = "production"
    Team        = "platform"
  }
}

# Create Subnet
resource "jdcloud_subnet" "main" {
  vpc_id            = jdcloud_vpc.main.id
  subnet_name       = "my-subnet"
  cidr_block        = "10.0.1.0/24"
  availability_zone = "cn-north-1a"
  region            = "cn-north-1"
}
```

### CloudFormation Template
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: JD Cloud VPC Stack

Resources:
  MyVPC:
    Type: 'JDCloud::VPC::VPC'
    Properties:
      VpcName: my-vpc
      CidrBlock: 10.0.0.0/16
      Region: cn-north-1
      Tags:
        - Key: Environment
          Value: production

  MySubnet:
    Type: 'JDCloud::VPC::Subnet'
    Properties:
      VpcId: !Ref MyVPC
      SubnetName: my-subnet
      CidrBlock: 10.0.1.0/24
      AvailabilityZone: cn-north-1a
      Region: cn-north-1
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Deploy VPC Infrastructure
on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup JD Cloud CLI
        run: |
          pip install jdcloud-cli
          echo "JDC_ACCESS_KEY=${{ secrets.JDC_ACCESS_KEY }}" >> $GITHUB_ENV
          echo "JDC_SECRET_KEY=${{ secrets.JDC_SECRET_KEY }}" >> $GITHUB_ENV
          echo "JDC_REGION=cn-north-1" >> $GITHUB_ENV
      
      - name: Deploy VPC
        run: |
          jdc vpc create-vpc \
            --region cn-north-1 \
            --vpc-name "ci-vpc" \
            --cidr-block "10.0.0.0/16" \
            --output json
```

### GitLab CI Example
```yaml
deploy-vpc:
  stage: deploy
  image: python:3.10
  script:
    - pip install jdcloud-cli
    - jdc vpc create-vpc
        --region cn-north-1
        --vpc-name "ci-vpc"
        --cidr-block "10.0.0.0/16"
        --output json
  variables:
    JDC_ACCESS_KEY: $JDC_ACCESS_KEY
    JDC_SECRET_KEY: $JDC_SECRET_KEY
    JDC_REGION: "cn-north-1"
  only:
    - main
```

## API Integration

### REST API Example
```bash
# Create VPC via REST API
curl -X POST "https://vpc.api.jdcloud.com/v1/regions/cn-north-1/vpcs" \
  -H "Authorization: Bearer $JDC_ACCESS_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "vpcName": "api-vpc",
    "cidrBlock": "10.0.0.0/16",
    "description": "VPC created via API"
  }'
```

### SDK API Wrapper
```python
import requests
import os

class VpcApiWrapper:
    def __init__(self):
        self.base_url = "https://vpc.api.jdcloud.com/v1"
        self.headers = {
            "Authorization": f"Bearer {os.environ['JDC_ACCESS_KEY']}",
            "Content-Type": "application/json"
        }
    
    def create_vpc(self, region, vpc_name, cidr_block):
        url = f"{self.base_url}/regions/{region}/vpcs"
        payload = {
            "vpcName": vpc_name,
            "cidrBlock": cidr_block
        }
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()
    
    def describe_vpcs(self, region):
        url = f"{self.base_url}/regions/{region}/vpcs"
        response = requests.get(url, headers=self.headers)
        return response.json()
```

## Monitoring Integration

### Prometheus Exporter
```python
from prometheus_client import start_http_server, Gauge
import requests
import os

# VPC metrics
vpc_count = Gauge('jdcloud_vpc_count', 'Number of VPCs')
subnet_count = Gauge('jdcloud_subnet_count', 'Number of subnets')

def collect_metrics():
    # Fetch metrics from JD Cloud API
    # Update Prometheus gauges
    pass

if __name__ == '__main__':
    start_http_server(8000)
    while True:
        collect_metrics()
        time.sleep(30)
```

### Grafana Dashboard JSON
```json
{
  "dashboard": {
    "title": "JD Cloud VPC Dashboard",
    "panels": [
      {
        "title": "VPC Count",
        "type": "stat",
        "targets": [
          {
            "expr": "jdcloud_vpc_count",
            "legendFormat": "VPCs"
          }
        ]
      },
      {
        "title": "Subnet Count",
        "type": "stat",
        "targets": [
          {
            "expr": "jdcloud_subnet_count",
            "legendFormat": "Subnets"
          }
        ]
      }
    ]
  }
}
```

## Security Integration

### IAM Policy Example
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "vpc:CreateVpc",
        "vpc:DescribeVpcs",
        "vpc:DeleteVpc"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "vpc:CreateSubnet",
        "vpc:DescribeSubnets",
        "vpc:DeleteSubnet"
      ],
      "Resource": "*"
    }
  ]
}
```

### Security Group Automation
```python
# Automated security group management
import os
from jdcloud_sdk.services.vpc.client import VpcClient

def manage_security_groups():
    client = VpcClient(
        Credential(os.environ['JDC_ACCESS_KEY'], os.environ['JDC_SECRET_KEY']),
        os.environ.get('JDC_REGION', 'cn-north-1')
    )
    
    # Create security group
    # Add rules
    # Apply to instances
    pass
```

## Best Practices

### Credential Management
- Use environment variables for credentials
- Implement credential rotation policies
- Use IAM roles instead of long-term credentials when possible
- Never commit credentials to version control

### API Rate Limiting
- Implement exponential backoff for API calls
- Cache responses when appropriate
- Use batch operations when available
- Monitor API usage and quotas

### Error Handling
- Implement proper error handling for all API calls
- Log errors with sufficient context
- Implement retry logic for transient failures
- Monitor for API errors and failures

### Configuration Management
- Use configuration files for environment-specific settings
- Implement configuration validation
- Use version control for configuration files
- Document configuration requirements

### Idempotency Best Practices
- **Always check before create**: Verify resource existence before creation
- **Handle "already exists" gracefully**: Treat as success in idempotent operations
- **Use unique identifiers**: Consistent naming for reliable lookups
- **Verify state after operations**: Confirm expected state after each operation
- **Implement proper cleanup**: Use idempotent delete patterns for resource cleanup
- **Test idempotency**: Regularly verify operations are truly idempotent
- **Document idempotency**: Clearly document which operations are idempotent