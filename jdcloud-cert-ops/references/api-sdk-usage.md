# API & SDK — JD Cloud SSL Certificate (`jdcloud_sdk`)

## Install and Config

```bash
uv pip install jdcloud_sdk
```

Credentials from environment variables:
```bash
export JDC_ACCESS_KEY="..."
export JDC_SECRET_KEY="..."
```

## Client Initialization

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.ssl.client.SslClient import SslClient

credential = Credential(os.environ["JDC_ACCESS_KEY"], os.environ["JDC_SECRET_KEY"])
client = SslClient(credential)
```

## API Operations

### Upload Certificate

```python
from jdcloud_sdk.services.ssl.apis.UploadCertRequest import UploadCertRequest, UploadCertParameters

with open("cert.pem") as f: cert_content = f.read()
with open("key.pem") as f: key_content = f.read()
params = UploadCertParameters(certName="my-cert", keyFile=key_content, certFile=cert_content)
params.setAliasName("my-alias")  # optional
resp = client.send(UploadCertRequest(parameters=params))
cert_id = resp.result["certId"]
```

### Describe Certificates (List)

```python
from jdcloud_sdk.services.ssl.apis.DescribeCertsRequest import DescribeCertsRequest, DescribeCertsParameters

params = DescribeCertsParameters()
params.setPageNumber(1); params.setPageSize(100)
# Optional filters:
# params.setDomainName("example.com")
# params.setCertIds("cert-xxx")
resp = client.send(DescribeCertsRequest(parameters=params))
for cert in resp.result["certListDetails"]:
    print(cert["certId"], cert["domainName"], cert["endDate"])
```

### Describe Certificate (Detail)

```python
from jdcloud_sdk.services.ssl.apis.DescribeCertRequest import DescribeCertRequest, DescribeCertParameters

params = DescribeCertParameters(certId="cert-xxx")
resp = client.send(DescribeCertRequest(parameters=params))
detail = resp.result
print(detail["domainName"], detail["endDate"])
```

### Download Certificate

```python
from jdcloud_sdk.services.ssl.apis.DownloadCertRequest import DownloadCertRequest, DownloadCertParameters

params = DownloadCertParameters(certId="cert-xxx", serverType="Nginx")
resp = client.send(DownloadCertRequest(parameters=params))
cert_info = resp.result["certInfo"]
```

### Update Certificate Name

```python
from jdcloud_sdk.services.ssl.apis.UpdateCertNameRequest import UpdateCertNameRequest, UpdateCertNameParameters

params = UpdateCertNameParameters(certId="cert-xxx", certName="new-name")
resp = client.send(UpdateCertNameRequest(parameters=params))
```

### Update Certificate

```python
from jdcloud_sdk.services.ssl.apis.UpdateCertRequest import UpdateCertRequest, UpdateCertParameters

with open("new-cert.pem") as f: cert = f.read()
with open("new-key.pem") as f: key = f.read()
params = UpdateCertParameters(certId="cert-xxx", keyFile=key, certFile=cert)
resp = client.send(UpdateCertRequest(parameters=params))
```

### Delete Certificate

```python
from jdcloud_sdk.services.ssl.apis.DeleteCertsRequest import DeleteCertsRequest, DeleteCertsParameters

params = DeleteCertsParameters(certId="cert-xxx")
resp = client.send(DeleteCertsRequest(parameters=params))
```

## Certificate Expiry Cruise (SDK)

```python
from datetime import datetime, timezone

# List all certs
params = DescribeCertsParameters()
params.setPageNumber(1); params.setPageSize(100)
resp = client.send(DescribeCertsRequest(parameters=params))

now = datetime.now(timezone.utc)
for cert in resp.result["certListDetails"]:
    end_date = datetime.fromisoformat(cert["endDate"])
    days_left = (end_date - now).days
    status = "CRITICAL" if days_left < 0 else "WARNING" if days_left <= 30 else "INFO" if days_left <= 60 else "OK"
    print(f"{cert['certId']} | {cert['domainName']} | {cert['endDate']} | {days_left}d | {status}")
```

## Error Handling

```python
from jdcloud_sdk.core.jdcloudrequest import JDCloudRequestException

try:
    resp = client.send(req)
except JDCloudRequestException as e:
    print(f"Error: {e.code} - {e.message}")
```
