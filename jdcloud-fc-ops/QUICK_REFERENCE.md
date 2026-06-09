# JD Cloud Function Compute Quick Reference

> Quick reference for Function Compute operations. This skill is **SDK-only** — `jdc` CLI does not support FC. For full details, see [SKILL.md](SKILL.md).

## SDK Bootstrap

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.function.client import FunctionClient

credential = Credential(
    os.environ['JDC_ACCESS_KEY'],
    os.environ['JDC_SECRET_KEY']
)
client = FunctionClient(credential, os.environ.get('JDC_REGION', 'cn-north-1'))
```

## Service CRUD Quick Reference

```python
from jdcloud_sdk.services.function.apis import (
    CreateServiceRequest, DescribeServicesRequest,
    DeleteServiceRequest
)

# Create service
req = CreateServiceRequest({
    "regionId": "cn-north-1",
    "serviceName": "my-service",
    "description": "Production service"
})
resp = client.createService(req)
service_name = resp.result.serviceName

# List services
req = DescribeServicesRequest({"regionId": "cn-north-1", "pageNumber": 1, "pageSize": 20})
resp = client.describeServices(req)
for svc in resp.result.services:
    print(f"{svc.serviceName}: {svc.status}")

# Delete service (cascades to all functions)
req = DeleteServiceRequest({"regionId": "cn-north-1", "serviceName": "my-service"})
resp = client.deleteService(req)
```

## Function CRUD Quick Reference

```python
from jdcloud_sdk.services.function.apis import (
    CreateFunctionRequest, DescribeFunctionsRequest,
    UpdateFunctionRequest, DeleteFunctionRequest
)

# Create function
req = CreateFunctionRequest({
    "regionId": "cn-north-1",
    "serviceName": "my-service",
    "functionName": "hello",
    "runtime": "python3.10",
    "handler": "index.handler",
    "code": {"zipFile": "<base64-encoded-zip>"},
    "memorySize": 512,
    "timeout": 30
})
resp = client.createFunction(req)

# List functions
req = DescribeFunctionsRequest({
    "regionId": "cn-north-1",
    "serviceName": "my-service",
    "pageNumber": 1, "pageSize": 20
})
resp = client.describeFunctions(req)

# Delete function
req = DeleteFunctionRequest({
    "regionId": "cn-north-1",
    "serviceName": "my-service",
    "functionName": "hello"
})
resp = client.deleteFunction(req)
```

## Invoke Function

```python
from jdcloud_sdk.services.function.apis import InvokeFunctionRequest

# Synchronous invoke
req = InvokeFunctionRequest({
    "regionId": "cn-north-1",
    "serviceName": "my-service",
    "functionName": "hello",
    "qualifier": "LATEST",  # or version number, or alias
    "payload": '{"name": "world"}'
})
resp = client.invokeFunction(req)
print(resp.result.payload)  # Response body

# Asynchronous invoke
req = InvokeFunctionRequest({
    "regionId": "cn-north-1",
    "serviceName": "my-service",
    "functionName": "hello",
    "invocationType": "Async",  # Returns requestId immediately
    "payload": '{"name": "world"}'
})
resp = client.invokeFunction(req)
print(resp.result.requestId)
```

## Version & Alias Quick Reference

```python
from jdcloud_sdk.services.function.apis import (
    PublishVersionRequest, ListVersionsRequest,
    CreateAliasRequest, UpdateAliasRequest, DeleteAliasRequest
)

# Publish immutable version
req = PublishVersionRequest({
    "regionId": "cn-north-1",
    "serviceName": "my-service",
    "functionName": "hello",
    "description": "Stable v1"
})
resp = client.publishVersion(req)
version_id = resp.result.versionId  # e.g., "1"

# Create alias pointing to version
req = CreateAliasRequest({
    "regionId": "cn-north-1",
    "serviceName": "my-service",
    "functionName": "hello",
    "aliasName": "prod",
    "versionId": version_id
})
resp = client.createAlias(req)

# Update alias (traffic shift)
req = UpdateAliasRequest({
    "regionId": "cn-north-1",
    "serviceName": "my-service",
    "functionName": "hello",
    "aliasName": "prod",
    "versionId": "2",
    "additionalVersionWeights": {"1": 0.1}  # 10% canary
})
resp = client.updateAlias(req)
```

## Trigger Quick Reference

```python
from jdcloud_sdk.services.function.apis import (
    CreateTriggerRequest, ListTriggersRequest, DeleteTriggerRequest
)

# HTTP trigger
req = CreateTriggerRequest({
    "regionId": "cn-north-1",
    "serviceName": "my-service",
    "functionName": "hello",
    "triggerName": "http-api",
    "triggerType": "http",
    "triggerConfig": {"authType": "anonymous", "methods": ["GET", "POST"]}
})

# Timer trigger (Cron)
req = CreateTriggerRequest({
    "regionId": "cn-north-1",
    "serviceName": "my-service",
    "functionName": "hello",
    "triggerName": "daily-job",
    "triggerType": "timer",
    "triggerConfig": {"cron": "0 2 * * *", "enable": True}
})
```

## Supported Runtimes

| Runtime | Version | Handler Format |
|---------|---------|---------------|
| Python | `python3.10`, `python3.9` | `file.function` |
| Node.js | `nodejs18`, `nodejs16`, `nodejs14` | `file.handler` |
| Java | `java11`, `java8` | `package.Class::method` |
| Go | `go1.x` | Package main |
| .NET | `dotnet6` | `Assembly::Class.Method` |
| PHP | `php7.4` | `file.function` |

## Common Error Codes

| Code | Meaning | Fix |
|------|---------|-----|
| `ServiceNotFound` | Service missing | Check name or create |
| `FunctionNotFound` | Function missing | Check function name |
| `InvalidRuntime` | Unsupported runtime | Use supported list |
| `InvalidHandler` | Wrong handler format | Check runtime format |
| `Timeout` | Exceeded timeout | Increase or optimize |
| `Throttling` | Rate limit hit | Back off and retry |

## Environment Setup

```bash
uv venv --python 3.10
source .venv/bin/activate
uv pip install jdcloud_sdk
```

## Related Documents

| Document | Description |
|----------|-------------|
| [SKILL.md](SKILL.md) | Full skill definition |
| [API & SDK](references/api-sdk-usage.md) | SDK operations map |
| [Troubleshooting](references/troubleshooting.md) | Detailed troubleshooting |
| [Core Concepts](references/core-concepts.md) | Service, function, version, alias, trigger |
