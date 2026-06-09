# API & SDK — API Gateway

## OpenAPI
- Base URL: `https://apigateway.jdcloud-api.com/v1`
- Protocol: HTTPS only
- Authentication: JD Cloud signature V3

## SDK Operations Map

| Goal | API Operation | SDK Method | Notes |
|------|---------------|------------|-------|
| Create ApiGroup | `CreateApiGroup` | `createApiGroup` | Group name must be unique in region |
| Delete ApiGroup | `DeleteApiGroup` | `deleteApiGroup` | Cascade deletes all APIs in group |
| Describe ApiGroups | `DescribeApiGroups` | `describeApiGroups` | Pagination supported |
| Create Api | `CreateApi` | `createApi` | Requires group to exist |
| Delete Api | `DeleteApi` | `deleteApi` | Removes from all stages |
| Describe Apis | `DescribeApis` | `describeApis` | Filter by group ID |
| Deploy Api | `DeployApi` | `deployApi` | Deploys to specified stage |
| Undeploy Api | `UndeployApi` | `undeployApi` | Removes from specified stage |
| Describe Deployments | `DescribeDeployments` | `describeDeployments` | Per API or per group |
| Create Throttling Policy | `CreateThrottlingPolicy` | `createThrottlingPolicy` | Rate limit configuration |
| Delete Throttling Policy | `DeleteThrottlingPolicy` | `deleteThrottlingPolicy` | Unbind first |
| Describe Throttling Policies | `DescribeThrottlingPolicies` | `describeThrottlingPolicies` | List all policies |
| Bind Throttling Policy | `BindThrottlingPolicy` | `bindThrottlingPolicy` | Bind to API + stage |
| Unbind Throttling Policy | `UnbindThrottlingPolicy` | `unbindThrottlingPolicy` | Remove binding |
| Describe Api Throttling | `DescribeApiThrottling` | `describeApiThrottling` | Show bound policies |

## Common Request Patterns

### Create API with Path Parameters
```python
req = CreateApiRequest(
    regionId="cn-north-1",
    apiGroupId="group-xxx",
    apiName="get-user",
    requestConfig={
        "requestPath": "/users/{userId}",
        "requestMethod": "GET",
        "requestProtocol": "HTTP"
    },
    serviceConfig={
        "serviceProtocol": "HTTP",
        "serviceAddress": "http://user-service.internal",
        "servicePath": "/api/users/{userId}",
        "serviceMethod": "GET",
        "serviceTimeout": 5000
    },
    authType="app_auth"
)
```

### Create API with Function Compute Backend
```python
req = CreateApiRequest(
    regionId="cn-north-1",
    apiGroupId="group-xxx",
    apiName="process-event",
    requestConfig={
        "requestPath": "/events",
        "requestMethod": "POST",
        "requestProtocol": "HTTPS"
    },
    serviceConfig={
        "serviceProtocol": "FC",
        "serviceAddress": "arn:aws:fc:cn-north-1::services/my-service/functions/my-function",
        "serviceTimeout": 30000
    },
    authType="jdcloud_auth"
)
```

### Create API with MOCK Backend
```python
req = CreateApiRequest(
    regionId="cn-north-1",
    apiGroupId="group-xxx",
    apiName="health-check",
    requestConfig={
        "requestPath": "/health",
        "requestMethod": "GET",
        "requestProtocol": "HTTP"
    },
    serviceConfig={
        "serviceProtocol": "MOCK",
        "mockResult": '{"status":"healthy"}',
        "mockStatusCode": 200
    },
    authType="no_auth"
)
```

### Throttling Policy with Multiple Limits
```python
req = CreateThrottlingPolicyRequest(
    regionId="cn-north-1",
    policyName="tiered-limit",
    throttleConfig={
        "apiThrottleConfig": {
            "apiId": "api-xxx",
            "unit": "minute",
            "apiLimit": 6000,
            "appLimit": 600
        }
    }
)
```

## Pagination

All list operations support pagination:
```python
req = DescribeApiGroupsRequest(
    regionId="cn-north-1",
    pageNumber=1,
    pageSize=50  # max 100
)
resp = client.describeApiGroups(req)

# Check for more pages
if resp.result.totalCount > pageNumber * pageSize:
    # Fetch next page
    pass
```

## Supported Request Methods
- `GET`
- `POST`
- `PUT`
- `DELETE`
- `PATCH`
- `HEAD`
- `OPTIONS`

## Supported Protocols
- `HTTP`
- `HTTPS`
- `HTTP_HTTPS` (both)
