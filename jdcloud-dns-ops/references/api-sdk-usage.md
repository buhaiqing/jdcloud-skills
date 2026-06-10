# API & SDK — JD Cloud DNS (`jdcloud_sdk`)

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
from jdcloud_sdk.services.domainservice.client.DomainserviceClient import DomainserviceClient

credential = Credential(os.environ["JDC_ACCESS_KEY"], os.environ["JDC_SECRET_KEY"])
client = DomainserviceClient(credential)
```

## API Operations

### Create Domain

```python
from jdcloud_sdk.services.domainservice.apis.CreateDomainRequest import CreateDomainRequest, CreateDomainParameters

params = CreateDomainParameters(packId=0, domainName="example.com")
# For paid: params.setBuyType(1); params.setTimeSpan(1); params.setTimeUnit(4)
resp = client.send(CreateDomainRequest(parameters=params))
domain_id = resp.result["data"]["domainId"]
```

### Describe Domains

```python
from jdcloud_sdk.services.domainservice.apis.DescribeDomainsRequest import DescribeDomainsRequest, DescribeDomainsParameters

params = DescribeDomainsParameters()
params.setPageNumber(1); params.setPageSize(100)
resp = client.send(DescribeDomainsRequest(parameters=params))
for d in resp.result["dataList"]:
    print(d["id"], d["domainName"])
```

### Delete Domain

```python
from jdcloud_sdk.services.domainservice.apis.DeleteDomainRequest import DeleteDomainRequest, DeleteDomainParameters

params = DeleteDomainParameters(domainId="12345")
resp = client.send(DeleteDomainRequest(parameters=params))
```

### Create Resource Record

```python
from jdcloud_sdk.services.domainservice.apis.CreateResourceRecordRequest import CreateResourceRecordRequest, CreateResourceRecordParameters

req = {"hostRecord": "www", "hostValue": "1.2.3.4", "type": "A", "ttl": 600}
params = CreateResourceRecordParameters(domainId="12345", req=req)
resp = client.send(CreateResourceRecordRequest(parameters=params))
record_id = resp.result["data"]["id"]
```

### Describe Resource Records

```python
from jdcloud_sdk.services.domainservice.apis.DescribeResourceRecordRequest import DescribeResourceRecordRequest, DescribeResourceRecordParameters

params = DescribeResourceRecordParameters(domainId="12345")
params.setPageNumber(1); params.setPageSize(100)
resp = client.send(DescribeResourceRecordRequest(parameters=params))
for r in resp.result["dataList"]:
    print(r["id"], r["hostRecord"], r["hostValue"], r["type"])
```

### Modify Resource Record

```python
from jdcloud_sdk.services.domainservice.apis.ModifyResourceRecordRequest import ModifyResourceRecordRequest, ModifyResourceRecordParameters

req = {"id": 67890, "hostRecord": "www", "hostValue": "5.6.7.8", "type": "A", "ttl": 300}
params = ModifyResourceRecordParameters(domainId="12345", req=req)
resp = client.send(ModifyResourceRecordRequest(parameters=params))
```

### Enable / Disable / Delete Resource Record

```python
from jdcloud_sdk.services.domainservice.apis.ModifyResourceRecordStatusRequest import ModifyResourceRecordStatusRequest, ModifyResourceRecordStatusParameters

# action: "on"=enable, "off"=disable, "del"=delete
params = ModifyResourceRecordStatusParameters(domainId="12345", ids=[67890], action="on")
resp = client.send(ModifyResourceRecordStatusRequest(parameters=params))
```

### Batch Set Resource Records

```python
from jdcloud_sdk.services.domainservice.apis.BatchSetResourceRecordsRequest import BatchSetResourceRecordsRequest, BatchSetResourceRecordsParameters

reqs = [{"id": 0, "hostRecord": "www", "hostValue": "1.2.3.4", "type": "A", "ttl": 600}]
params = BatchSetResourceRecordsParameters(domainId="12345", req=reqs)
resp = client.send(BatchSetResourceRecordsRequest(parameters=params))
```

## Error Handling

```python
from jdcloud_sdk.core.jdcloudrequest import JDCloudRequestException

try:
    resp = client.send(req)
except JDCloudRequestException as e:
    print(f"Error: {e.code} - {e.message}")
```

## Pagination

Most list operations support `pageNumber` and `pageSize`:
```python
params.setPageNumber(1)
params.setPageSize(100)
```
Check `resp.result["totalCount"]` for total items.
