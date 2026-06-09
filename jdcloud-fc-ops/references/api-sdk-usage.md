# API & SDK — Function Compute

## OpenAPI
- Base URL: `https://function.jdcloud-api.com/v1`
- Protocol: HTTPS only
- Authentication: JD Cloud signature V3

## SDK Operations Map

| Goal | API Operation | SDK Method | Notes |
|------|---------------|------------|-------|
| Create Service | `CreateService` | `createService` | Service name must be unique in region |
| Delete Service | `DeleteService` | `deleteService` | Cascade deletes all functions |
| List Services | `ListServices` | `listServices` | Pagination supported |
| Create Function | `CreateFunction` | `createFunction` | Requires service to exist |
| Delete Function | `DeleteFunction` | `deleteFunction` | Deletes all versions |
| Update Function | `UpdateFunction` | `updateFunction` | Creates new version implicitly |
| List Functions | `ListFunctions` | `listFunctions` | Filter by service name |
| Invoke Function | `InvokeFunction` | `invokeFunction` | Sync or async |
| Publish Version | `PublishVersion` | `publishVersion` | Creates immutable version |
| List Versions | `ListVersions` | `listVersions` | All published versions |
| Create Alias | `CreateAlias` | `createAlias` | Points to version |
| Update Alias | `updateAlias` | `updateAlias` | Change version pointer |
| Delete Alias | `DeleteAlias` | `deleteAlias` | Removes alias |
| Create Trigger | `CreateTrigger` | `createTrigger` | HTTP, Timer, OSS types |
| Delete Trigger | `DeleteTrigger` | `deleteTrigger` | Removes trigger only |
| List Triggers | `ListTriggers` | `listTriggers` | By function |

## Supported Runtimes (verify latest)
- `python3.10`, `python3.9`
- `nodejs18`, `nodejs16`, `nodejs14`
- `java11`, `java8`
- `go1.x`
- `dotnet6`
- `php7.4`

## Common Request Patterns

### With Environment Variables
```python
req = CreateFunctionRequest(
    # ... standard fields ...
    environmentVariables={
        "DB_HOST": "mydb.example.com",
        "DB_PORT": "3306"
    }
)
```

### With VPC Configuration
```python
req = CreateFunctionRequest(
    # ... standard fields ...
    vpcConfig={
        "vpcId": "vpc-xxx",
        "subnetId": "subnet-xxx",
        "securityGroupId": "sg-xxx"
    }
)
```
