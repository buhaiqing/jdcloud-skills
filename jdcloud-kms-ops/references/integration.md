# Integration — JD Cloud KMS

## Environment Setup (uv)

Both `jdc` CLI and the JD Cloud Python SDK require a Python runtime. Use **`uv`** for local, isolated, and **idempotent** environment management.

### Quick Start (Command-based)

**Install uv (system-wide, one-time per machine):**
```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
# Or via Homebrew: brew install uv

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Bootstrap Python environment (idempotent — safe to re-run):**
```bash
# Create virtual environment
uv venv --python 3.10

# Activate: macOS/Linux
source .venv/bin/activate
# Activate: Windows
# .venv\Scripts\activate

# Install dependencies
uv pip install jdcloud_cli jdcloud_sdk

# Verify installation
jdc --version
python -c "import jdcloud_sdk; print('SDK OK')"
```

> `uv venv` is idempotent: re-running on an existing `.venv` is a no-op. `uv pip install` skips already-satisfied packages.

**Pin versions for reproducibility (optional):**
```bash
uv pip install jdcloud_cli==1.2.30 jdcloud_sdk==1.6.26
```
> Replace version numbers with the latest stable releases from PyPI.

### Advanced: Project-based Setup (Recommended for Teams)

For reproducible, version-locked environments, use `pyproject.toml` with `uv sync`:

**1. Create `pyproject.toml`:**
```toml
[project]
name = "jdcloud-kms-ops"
version = "1.0.0"
requires-python = ">=3.10"
dependencies = [
    "jdcloud_cli>=1.2.0",
    "jdcloud_sdk>=1.6.0",
]

[tool.uv]
python-version = "3.10"
```

**2. Sync environment (idempotent):**
```bash
# Creates .venv and installs all dependencies in one command
uv sync

# Activate
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows
```

**Benefits:**
- **Fully idempotent**: `uv sync` always produces the same environment
- **Lock file**: `uv.lock` pins exact versions for reproducibility
- **Team consistency**: All developers use identical dependencies
- **CI/CD ready**: `uv sync` works identically in pipelines

## Python SDK Bootstrap

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.kms.client.KmsClient import KmsClient
from jdcloud_sdk.core.config import Config

# From environment variables
credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"]
)

# Initialize client
client = KmsClient(credential)

# Optional: Set custom config (e.g., internal endpoint for VPC)
config = Config()
config.setEndpoint("kms.internal.cn-north-1.jdcloud-api.com")  # Internal endpoint
config.setScheme("https")
config.setTimeout(20)
client.setConfig(config)
```

> Use `os.environ['KEY']` for secrets (fail-fast if missing). Use `.get` only for optional non-secret config.

## Credential Configuration

### SDK Mode (Environment Variables)

SDK reads credentials from environment variables:

```bash
export JDC_ACCESS_KEY="your_access_key_here"
export JDC_SECRET_KEY="your_secret_key_here"
export JDC_REGION="cn-north-1"  # Optional default
```

**Best Practices:**
- Store credentials in `.env` file (never commit to version control)
- Use secret management system (JD Cloud KMS secrets, HashiCorp Vault)
- Rotate credentials periodically

### CLI Mode (Config File)

CLI reads credentials from `~/.jdc/config` INI file:

```bash
jdc configure add
# Or manually create config file:
mkdir -p ~/.jdc
cat > ~/.jdc/config << 'CONFIGEOF'
[default]
access_key = YOUR_ACCESS_KEY
secret_key = YOUR_SECRET_KEY
region_id = cn-north-1
endpoint = kms.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF
printf "%s" "default" > ~/.jdc/current
```

**Sandbox Workaround (if HOME is read-only):**
```bash
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc
cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = YOUR_ACCESS_KEY
secret_key = YOUR_SECRET_KEY
region_id = cn-north-1
endpoint = kms.jdcloud-api.com
CONFIGEOF
printf "%s" "default" > /tmp/jdc-home/.jdc/current
```

## Integration with JD Cloud Services

### OSS (Object Storage) Encryption

Use KMS key for OSS server-side encryption:

```bash
# Create KMS key for OSS encryption
jdc --output json kms create-key \
  --key-cfg '{"keyName":"oss-encryption-key","keyUsage":"ENCRYPT_DECRYPT","keySpec":"AES_256"}'

# Get key ID
KEY_ID=$(jdc --output json kms describe-key-list | jq -r '.result.keys[0].keyId')

# Configure OSS bucket encryption (via OSS skill or console)
# Server-side encryption type: KMS
# KMS key ID: $KEY_ID
```

**OSS Skill Integration:**
- Delegate OSS operations to `jdcloud-oss-ops` skill
- Pass KMS key ID to OSS bucket creation/encryption configuration

### Cloud Disk Encryption

Use KMS key for disk encryption:

```bash
# Create KMS key for disk encryption
KEY_ID=$(jdc --output json kms create-key \
  --key-cfg '{"keyName":"disk-encryption-key","keyUsage":"ENCRYPT_DECRYPT","keySpec":"AES_256"}' \
  | jq -r '.result.keyId')

# Create encrypted disk (via VM skill)
# Disk encryption: enabled
# KMS key ID: $KEY_ID
```

**VM Skill Integration:**
- Delegate disk creation to `jdcloud-vm-ops` skill
- Pass KMS key ID for encrypted disk parameter

### Database Encryption (RDS)

Use KMS key for RDS encryption:

```bash
# Create KMS key for database encryption
KEY_ID=$(jdc --output json kms create-key \
  --key-cfg '{"keyName":"rds-encryption-key","keyUsage":"ENCRYPT_DECRYPT","keySpec":"AES_256"}' \
  | jq -r '.result.keyId')

# Create encrypted RDS instance (via RDS skill)
# Storage encryption: enabled
# KMS key ID: $KEY_ID
```

### Application Encryption Workflow

**Envelope Encryption Pattern:**

```python
import os
import base64
from jdcloud_sdk.services.kms.client.KmsClient import KmsClient
from jdcloud_sdk.services.kms.apis.GenerateDataKeyRequest import GenerateDataKeyRequest, GenerateDataKeyParameters
from jdcloud_sdk.services.kms.apis.DecryptRequest import DecryptRequest, DecryptParameters
# Additional imports for local encryption (e.g., cryptography library)
from cryptography.fernet import Fernet

# 1. Generate data key from KMS
client = KmsClient(Credential(os.environ["JDC_ACCESS_KEY"], os.environ["JDC_SECRET_KEY"]))
params = GenerateDataKeyParameters(regionId="cn-north-1", keyId="key-abc123")
req = GenerateDataKeyRequest(parameters=params)
resp = client.send(req)

data_key_ciphertext = resp.result["dataKeyCiphertextBlob"]  # Encrypted data key
plaintext_data_key_b64 = resp.result["plaintextDataKey"]     # Plaintext data key (Base64)

# 2. Decode plaintext data key
plaintext_data_key = base64.b64decode(plaintext_data_key_b64)

# 3. Encrypt data locally (using plaintext data key)
# Example: Use cryptography library for AES encryption
cipher = Fernet(base64.urlsafe_b64encode(plaintext_data_key))
encrypted_data = cipher.encrypt("Sensitive application data".encode())

# 4. Store encrypted data + encrypted data key
# Save to file, database, or object storage:
# - encrypted_data (ciphertext)
# - data_key_ciphertext (encrypted data key from KMS)

# 5. DELETE plaintext data key from memory (never persist it)
plaintext_data_key = None
plaintext_data_key_b64 = None

# 6. Decrypt workflow (retrieve encrypted data + encrypted data key)
# Decrypt data key from KMS:
params = DecryptParameters(regionId="cn-north-1", keyId="key-abc123", ciphertextBlob=data_key_ciphertext)
req = DecryptRequest(parameters=params)
resp = client.send(req)
plaintext_data_key_b64 = resp.result["plaintext"]
plaintext_data_key = base64.b64decode(plaintext_data_key_b64)

# Decrypt data locally:
cipher = Fernet(base64.urlsafe_b64encode(plaintext_data_key))
decrypted_data = cipher.decrypt(encrypted_data).decode()
```

**Benefits:**
- Minimize KMS API calls (only data key generation/decryption)
- Encrypt large data locally without calling KMS for each encryption
- Store encrypted data key with encrypted data (portable)

## Secrets Management Integration

**Application Secrets Storage:**

```bash
# Store database password in KMS secret
jdc --output json kms create-secret \
  --secret-cfg '{"secretName":"db-password","secretData":"my_db_password_123"}'

# Retrieve secret ID
SECRET_ID=$(jdc --output json kms describe-secret-list | jq -r '.result.secrets[0].secretId')

# Application retrieves secret via SDK:
# 1. Call describeSecretVersionInfo to get secret data
# 2. Use secret data to configure database connection
```

**Secret Rotation Workflow:**

```bash
# Update secret with new version (password rotation)
jdc --output json kms create-secret-version \
  --secret-id "$SECRET_ID" \
  --secret-data "new_password_456"

# Application uses latest version automatically (or explicit version selection)
```

## CI/CD Integration

### GitLab CI Example

```yaml
stages:
  - deploy

deploy_encrypted_data:
  stage: deploy
  script:
    - uv venv --python 3.10
    - source .venv/bin/activate
    - uv pip install jdcloud_sdk
    
    - export JDC_ACCESS_KEY="${JD_ACCESS_KEY}"
    - export JDC_SECRET_KEY="${JD_SECRET_KEY}"
    
    - python encrypt_data.py  # Encrypt deployment secrets via KMS
    - scp encrypted_data.bin server:/app/data/
```

### Jenkins Pipeline Example

```groovy
pipeline {
  agent any
  stages {
    stage('Encrypt Secrets') {
      steps {
        sh '''
          uv venv --python 3.10
          source .venv/bin/activate
          uv pip install jdcloud_sdk
          
          export JDC_ACCESS_KEY="${JD_ACCESS_KEY}"
          export JDC_SECRET_KEY="${JD_SECRET_KEY}"
          
          python encrypt_secrets.py
        '''
      }
    }
  }
  environment {
    JD_ACCESS_KEY = credentials('jdcloud-access-key')
    JD_SECRET_KEY = credentials('jdcloud-secret-key')
  }
}
```

## Terraform Integration

JD Cloud Terraform provider supports KMS resource management:

**Example Terraform configuration:**
```hcl
resource "jdcloud_kms_key" "encryption_key" {
  region_id    = "cn-north-1"
  key_name     = "terraform-encryption-key"
  key_usage    = "ENCRYPT_DECRYPT"
  key_spec     = "AES_256"
  description  = "Key managed by Terraform"
}

output "kms_key_id" {
  value = jdcloud_kms_key.encryption_key.key_id
}
```

**Terraform Provider Documentation:**
- https://registry.terraform.io/providers/jdcloud/jdcloud/

## Ansible Integration

```yaml
- name: Encrypt application secrets via JD Cloud KMS
  hosts: localhost
  tasks:
    - name: Install jdcloud SDK
      pip:
        name: jdcloud_sdk
        state: present
    
    - name: Encrypt secrets
      python:
        script: |
          import os
          import base64
          from jdcloud_sdk.services.kms.client.KmsClient import KmsClient
          from jdcloud_sdk.services.kms.apis.EncryptRequest import EncryptRequest, EncryptParameters
          
          credential = Credential(os.environ["JDC_ACCESS_KEY"], os.environ["JDC_SECRET_KEY"])
          client = KmsClient(credential)
          
          plaintext = "{{ ansible_secrets }}"
          plaintext_b64 = base64.b64encode(plaintext.encode()).decode()
          
          params = EncryptParameters(regionId="cn-north-1", keyId="{{ kms_key_id }}", plaintext=plaintext_b64)
          req = EncryptRequest(parameters=params)
          resp = client.send(req)
          
          print(resp.result["ciphertextBlob"])
      environment:
        JDC_ACCESS_KEY: "{{ jd_access_key }}"
        JDC_SECRET_KEY: "{{ jd_secret_key }}"
```

## Kubernetes Integration

**Secret Encryption with KMS:**

1. Store application secrets in JD Cloud KMS
2. Use Kubernetes external-secrets operator to sync KMS secrets to Kubernetes secrets
3. Configure KMS encryption provider for Kubernetes etcd encryption

**External Secrets Operator Example:**
```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: db-credentials
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: jdcloud-kms-store
    kind: SecretStore
  target:
    name: db-credentials
    creationPolicy: Owner
  data:
    - secretKey: password
      remoteRef:
        key: db-password  # KMS secret name
```

## MCP (Model Context Protocol) Integration

JD Cloud KMS skill can be integrated with MCP for AI agent workflows:

**Potential MCP Operations:**
- `kms_encrypt`: Encrypt data via KMS
- `kms_decrypt`: Decrypt data via KMS
- `kms_create_key`: Create new KMS key
- `kms_describe_key`: Get key metadata

**MCP Server Example (conceptual):**
```json
{
  "name": "jdcloud-kms",
  "operations": [
    {
      "name": "encrypt",
      "description": "Encrypt data using JD Cloud KMS key",
      "parameters": {
        "key_id": "string",
        "plaintext": "string (Base64-encoded)"
      },
      "returns": {
        "ciphertext_blob": "string"
      }
    }
  ]
}
```

## Testing and Validation

### Local Testing Environment

**Setup test environment:**
```bash
uv venv --python 3.10
source .venv/bin/activate
uv pip install jdcloud_sdk pytest

# Create test KMS key
jdc --output json kms create-key \
  --key-cfg '{"keyName":"test-key","keyUsage":"ENCRYPT_DECRYPT","keySpec":"AES_256"}'
```

### Unit Tests

```python
import pytest
import os
import base64
from jdcloud_sdk.services.kms.client.KmsClient import KmsClient
from jdcloud_sdk.services.kms.apis.EncryptRequest import EncryptRequest, EncryptParameters
from jdcloud_sdk.services.kms.apis.DecryptRequest import DecryptRequest, DecryptParameters

@pytest.fixture
def kms_client():
    credential = Credential(os.environ["JDC_ACCESS_KEY"], os.environ["JDC_SECRET_KEY"])
    return KmsClient(credential)

def test_encrypt_decrypt(kms_client):
    plaintext = "Test data"
    plaintext_b64 = base64.b64encode(plaintext.encode()).decode()
    
    # Encrypt
    params = EncryptParameters(regionId="cn-north-1", keyId="test-key-id", plaintext=plaintext_b64)
    req = EncryptRequest(parameters=params)
    resp = kms_client.send(req)
    ciphertext = resp.result["ciphertextBlob"]
    
    # Decrypt
    params = DecryptParameters(regionId="cn-north-1", keyId="test-key-id", ciphertextBlob=ciphertext)
    req = DecryptRequest(parameters=params)
    resp = kms_client.send(req)
    decrypted_b64 = resp.result["plaintext"]
    decrypted = base64.b64decode(decrypted_b64).decode()
    
    assert decrypted == plaintext
```

## References

- JD Cloud SDK GitHub: https://github.com/jdcloud-api/jdcloud-sdk-python
- JD Cloud CLI GitHub: https://github.com/jdcloud-api/jdcloud-cli
- uv Documentation: https://docs.astral.sh/uv/
- JD Cloud Terraform Provider: https://registry.terraform.io/providers/jdcloud/jdcloud/
- External Secrets Operator: https://external-secrets.io/