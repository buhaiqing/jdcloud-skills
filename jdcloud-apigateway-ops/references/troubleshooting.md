# Troubleshooting API Gateway

## Common SDK Error Codes

| Code | HTTP | Meaning | Agent Action |
|------|------|---------|--------------|
| `GroupNotFound` | 404 | API group does not exist | Verify group ID; create if needed |
| `ApiNotFound` | 404 | API does not exist | Verify API ID in correct group |
| `GroupAlreadyExists` | 409 | Group name taken | Use different name or describe existing |
| `ApiAlreadyExists` | 409 | API name taken in group | Use different name |
| `PolicyNotFound` | 404 | Throttling policy does not exist | Verify policy ID |
| `PolicyAlreadyExists` | 409 | Policy name taken | Use different name |
| `InvalidParameter` | 400 | Request parameter invalid | Align with OpenAPI schema |
| `InvalidRequestConfig` | 400 | API request config invalid | Check path format, method, protocol |
| `InvalidServiceConfig` | 400 | Backend service config invalid | Verify URL, timeout, protocol |
| `InvalidStage` | 400 | Stage name invalid | Use supported stage names |
| `ApiHasDeployed` | 409 | API is deployed; cannot delete | Undeploy from all stages first |
| `GroupHasDeployedApis` | 409 | Group has deployed APIs | Undeploy all APIs first |
| `BackendUnreachable` | 502 | Backend service not reachable | Check backend URL and network |
| `BackendTimeout` | 504 | Backend service timed out | Increase timeout or check backend |
| `Throttling` | 429 | Rate limit exceeded | Back off and retry; check policy limits |
| `QuotaExceeded` | 429 | API group or API quota exceeded | Request quota increase |

## Diagnostic Order

1. **Check API group exists**: `DescribeApiGroups`
2. **Check API state**: `DescribeApis` — note `status` field
3. **Check deployment status**: `DescribeDeployments` — verify stage bindings
4. **Check throttling policy**: `DescribeApiThrottling` — verify bound policies and limits
5. **Test backend directly**: curl the backend URL to verify it responds
6. **Check IAM permissions**: Ensure SDK credentials have `apigateway:*` permissions

## Common Issues

### API Returns 404 Despite Being Deployed
- **Symptom**: Calling the API Gateway URL returns 404
- **Cause**: API may not be deployed to the requested stage, or path mismatch
- **Diagnosis**:
  ```python
  # Check deployment status
  req = DescribeDeploymentsRequest(
      regionId="cn-north-1",
      apiGroupId="group-xxx",
      apiId="api-xxx"
  )
  resp = client.describeDeployments(req)
  # Verify stageName matches the URL stage
  ```
- **Fix**: Redeploy API to the correct stage

### Backend Timeout Errors
- **Symptom**: API Gateway returns 504 Gateway Timeout
- **Cause**: Backend service takes longer than `serviceTimeout`
- **Fix**: Increase `serviceTimeout` in API service config, or optimize backend response time

### Authentication Failures
- **Symptom**: 401/403 errors when calling API
- **Cause**: Wrong auth type or missing credentials
- **Diagnosis**:
  - Check `authType` in API config (`no_auth` vs `app_auth` vs `jdcloud_auth`)
  - For `app_auth`: verify AppKey and signature calculation
  - For `jdcloud_auth`: verify IAM permissions
- **Fix**: Update auth type or provide correct credentials

### Rate Limiting (429) Errors
- **Symptom**: API returns 429 Too Many Requests
- **Cause**: Throttling policy limit exceeded
- **Diagnosis**:
  ```python
  req = DescribeApiThrottlingRequest(
      regionId="cn-north-1",
      apiGroupId="group-xxx",
      apiId="api-xxx",
      stageName="prod"
  )
  resp = client.describeApiThrottling(req)
  # Check bound policy limits
  ```
- **Fix**: Increase policy limits or implement client-side retry with backoff

### Group Deletion Fails
- **Symptom**: `DeleteApiGroup` returns `GroupHasDeployedApis`
- **Cause**: APIs in the group are still deployed to stages
- **Fix**:
  1. List all APIs in group: `DescribeApis`
  2. For each deployed API, undeploy from all stages: `UndeployApi`
  3. Delete APIs: `DeleteApi`
  4. Retry group deletion: `DeleteApiGroup`

## Backend Health Check

Always verify backend connectivity before creating or deploying APIs:
```bash
# Test HTTP backend
curl -v http://backend.internal:8080/api/health

# Test HTTPS backend
curl -v https://backend.internal/api/health

# Check DNS resolution
nslookup backend.internal
```
