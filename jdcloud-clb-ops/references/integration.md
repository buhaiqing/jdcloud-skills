# JD Cloud CLB Integration & Tooling

## MCP Server Configuration
```json
{
  "mcpServers": {
    "jdcloud-clb": {
      "command": "uvx", 
      "args": ["run", "--python", "3.10", "@jdcloud/clb-mcp"],
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

## SDK Initialization (Python)
```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.clb.client import ClbClient

credential = Credential(
    os.environ['JDC_ACCESS_KEY'],
    os.environ['JDC_SECRET_KEY']
)
client = ClbClient(credential, os.environ.get('JDC_REGION', 'cn-north-1'))
```
> Rule: Use `os.environ['KEY']` (not `.get()`) for credentials to fail-fast if missing. Use `os.environ.get('KEY', default)` for optional config like region.

## SDK Examples

### Create CLB Instance
```python
from jdcloud_sdk.services.clb.client import ClbClient
from jdcloud_sdk.services.clb.models import CreateClbRequest

client = ClbClient(credential, 'cn-north-1')

request = CreateClbRequest(
    region='cn-north-1',
    clb_name='my-clb',
    clb_specification='2',
    network_type='BGP'
)

response = client.create_clb(request)
if response.result:
    clb_id = response.result.clb_id
    print(f"Created CLB: {clb_id}")
```

### Describe CLB Instance
```python
from jdcloud_sdk.services.clb.models import DescribeClbRequest

request = DescribeClbRequest(
    region='cn-north-1',
    clb_id='clb-xxxxx'
)

response = client.describe_clb(request)
if response.result:
    clb = response.result
    print(f"CLB Name: {clb.clb_name}")
    print(f"CLB Status: {clb.status}")
    print(f"CLB IP: {clb.ip_address}")
```

### Create Listener
```python
from jdcloud_sdk.services.clb.models import CreateListenerRequest

request = CreateListenerRequest(
    region='cn-north-1',
    clb_id='clb-xxxxx',
    listener_name='http-listener',
    protocol='HTTP',
    listener_port=80,
    backend_server_group_id='bsg-xxxxx'
)

response = client.create_listener(request)
if response.result:
    listener_id = response.result.listener_id
    print(f"Created Listener: {listener_id}")
```

### Upload SSL Certificate
```python
from jdcloud_sdk.services.clb.models import UploadCertificateRequest

# Read certificate and key from files
with open('/path/to/certificate.pem', 'r') as f:
    cert_content = f.read()

with open('/path/to/private-key.pem', 'r') as f:
    private_key = f.read()

request = UploadCertificateRequest(
    region='cn-north-1',
    certificate_name='my-domain-cert',
    certificate_content=cert_content,
    private_key=private_key
)

response = client.upload_certificate(request)
if response.result:
    cert_id = response.result.certificate_id
    print(f"Uploaded Certificate: {cert_id}")
```

### Update HTTPS Listener with New Certificate
```python
from jdcloud_sdk.services.clb.models import ModifyListenerRequest

request = ModifyListenerRequest(
    region='cn-north-1',
    clb_id='clb-xxxxx',
    listener_id='listener-xxxxx',
    certificate_id='cert-yyyyy'  # New certificate ID
)

response = client.modify_listener(request)
if response.result:
    print("Listener certificate updated successfully")
```

### List SSL Certificates
```python
from jdcloud_sdk.services.clb.models import DescribeCertificatesRequest

request = DescribeCertificatesRequest(
    region='cn-north-1'
)

response = client.describe_certificates(request)
if response.result:
    for cert in response.result.certificates:
        print(f"Certificate ID: {cert.certificate_id}")
        print(f"Name: {cert.certificate_name}")
        print(f"Common Name: {cert.common_name}")
        print(f"Expiration: {cert.expire_time}")
        print(f"Status: {cert.status}")
        print("---")
```

### Delete SSL Certificate
```python
from jdcloud_sdk.services.clb.models import DeleteCertificateRequest

request = DeleteCertificateRequest(
    region='cn-north-1',
    certificate_id='cert-xxxxx'
)

response = client.delete_certificate(request)
if response.result:
    print("Certificate deleted successfully")
```

### Create HTTPS Listener with SSL Certificate
```python
from jdcloud_sdk.services.clb.models import CreateListenerRequest

request = CreateListenerRequest(
    region='cn-north-1',
    clb_id='clb-xxxxx',
    listener_name='https-listener',
    protocol='HTTPS',
    listener_port=443,
    backend_server_group_id='bsg-xxxxx',
    certificate_id='cert-xxxxx',
    ssl_policy='tls-1-2'
)

response = client.create_listener(request)
if response.result:
    listener_id = response.result.listener_id
    print(f"Created HTTPS Listener: {listener_id}")
```

## Integration with Other Services

### CLB with ECS (Elastic Cloud Server)
```python
# Add ECS instances as backend servers
from jdcloud_sdk.services.clb.models import AddBackendServersRequest

request = AddBackendServersRequest(
    region='cn-north-1',
    clb_id='clb-xxxxx',
    backend_server_group_id='bsg-xxxxx',
    backend_servers=[
        {"backendServerId": "vm-xxxxx", "weight": 10}
    ]
)

response = client.add_backend_servers(request)
```

### CLB with VPC
```python
# Create CLB in specific VPC subnet
from jdcloud_sdk.services.clb.models import CreateClbRequest

request = CreateClbRequest(
    region='cn-north-1',
    clb_name='vpc-clb',
    subnet_id='subnet-xxxxx',
    vpc_id='vpc-xxxxx'
)

response = client.create_clb(request)
```

## Automation with Terraform
```hcl
resource "jdcloud_clb" "example" {
  clb_name         = "terraform-clb"
  clb_specification = "2"
  network_type     = "BGP"
  region           = "cn-north-1"
}

resource "jdcloud_clb_listener" "example" {
  clb_id                 = jdcloud_clb.example.id
  listener_name          = "http-listener"
  protocol               = "HTTP"
  listener_port          = 80
  backend_server_group_id = jdcloud_clb_backend_server_group.example.id
}
```

## CI/CD Integration
### GitHub Actions Example
```yaml
name: Deploy CLB
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
          echo "${{ secrets.JDC_ACCESS_KEY }}" > access_key
          echo "${{ secrets.JDC_SECRET_KEY }}" > secret_key
      - name: Create CLB
        run: |
          jdc clb create-clb \
            --region cn-north-1 \
            --clb-name "ci-cd-clb" \
            --output json
```

## Best Practices
- Use environment variables for credentials in all integrations
- Implement proper error handling in SDK calls
- Use retry logic for transient failures
- Monitor CLB resources through integrated monitoring solutions
- Implement infrastructure as code for reproducible deployments
- Use RBAC policies to control access to CLB resources