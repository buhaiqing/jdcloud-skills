# Troubleshooting Function Compute

## Common SDK Error Codes

| Code | HTTP | Meaning | Agent Action |
|------|------|---------|--------------|
| `ServiceNotFound` | 404 | Service does not exist | Verify service name; create if needed |
| `FunctionNotFound` | 404 | Function does not exist | Verify function name in correct service |
| `ServiceAlreadyExists` | 409 | Service name taken | Use different name or describe existing |
| `FunctionAlreadyExists` | 409 | Function name taken in service | Use different name |
| `InvalidRuntime` | 400 | Runtime not supported | Check supported runtimes list |
| `InvalidHandler` | 400 | Handler format incorrect | Use `file.function` format |
| `FunctionError` | 502 | Function execution failed | Check function logs |
| `Timeout` | 504 | Function timed out | Increase timeout or optimize code |
| `MemoryLimitExceeded` | 502 | Out of memory | Increase memory allocation |
| `Throttling` | 429 | Rate limit exceeded | Back off and retry |

## Diagnostic Order
1. Check service exists: `DescribeService`
2. Check function state: `DescribeFunction`
3. Review function logs via CloudMonitor or Log Service
4. Test with minimal payload to isolate issues
5. Verify IAM permissions for SDK credentials

## Cold Start Issues
- **Symptom**: First invocation is slow
- **Cause**: Runtime initialization overhead
- **Mitigation**: Use provisioned concurrency or keep-alive invocations

## Timeout Issues
- **Symptom**: `Timeout` errors
- **Cause**: Function exceeds configured timeout
- **Mitigation**: Increase timeout or optimize code performance
