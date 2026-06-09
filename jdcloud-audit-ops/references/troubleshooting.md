# Troubleshooting Audit Log

## Common API Error Codes

| Code / HTTP | Meaning | Agent Action |
|-------------|---------|--------------|
| `InvalidParameter` / 400 | Request failed validation | Check parameter format against OpenAPI spec; ensure ISO 8601 timestamps |
| `InvalidTimeRange` / 400 | Time range invalid or exceeds maximum | Verify start < end, range <= 90 days |
| `EventNotFound` / 404 | Specified event ID does not exist | Verify event ID; may have expired beyond retention |
| `Unauthorized` / 403 | Insufficient permissions | Check IAM policy for audit:DescribeEvents permission |
| `Throttling` / 429 | Rate limit exceeded | Back off exponentially; reduce query frequency |
| `InternalError` / 500 | Server-side error | Retry with exponential backoff; report if persistent |

## Diagnostic Order

### No Events Returned

1. **Verify time range** — Ensure `startTime` and `endTime` are correct and within retention period
2. **Check filters** — Remove `eventName`, `resourceType`, `username` filters to broaden search
3. **Verify region** — Ensure querying the correct region where events occurred
4. **Check retention** — Events may have expired if older than retention period

### Permission Denied

1. **Verify IAM policy** — Ensure user has `audit:DescribeEvents` permission
2. **Check resource-level permissions** — Some operations may require specific resource permissions
3. **Validate credentials** — Ensure Access Key/Secret Key are correct and not expired

### Time Range Errors

1. **Format check** — Use ISO 8601 format: `2026-06-03T10:30:00+08:00`
2. **Range validation** — Maximum window is typically 90 days
3. **Order check** — `startTime` must be before `endTime`

### Event Not Found

1. **Verify event ID** — Check for typos in event ID
2. **Retention check** — Event may have been purged after retention period
3. **Region check** — Event may be in a different region

## CLI-Specific Issues

### "invalid choice: 'audit'"

**Cause:** 当前锁定的 `jdcloud_cli==1.2.12` 未暴露 `audit` 顶层命令

**Fix:** 确认 CLI 版本是否支持 `jdc audit`；如不支持，请通过 REST API 或确认后的 SDK 模块执行操作。

### "unrecognized arguments: --output json"

**Cause:** `--output json` placed after subcommand

**Fix:** Move `--output json` BEFORE the subcommand:
```bash
# Wrong
jdc audit describe-events --output json ...

# Correct
jdc --output json audit describe-events ...
```

### "PermissionError: [Errno 13] Permission denied: '/root/.jdc'"

**Cause:** Sandbox environment with non-writable home directory

**Fix:** Redirect HOME environment variable:
```bash
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc
# ... create config files ...
```

### No credentials found

**Cause:** jdc CLI reads from `~/.jdc/config`, not environment variables

**Fix:** Create config file:
```bash
mkdir -p ~/.jdc
cat > ~/.jdc/config << 'EOF'
[default]
access_key = YOUR_ACCESS_KEY
secret_key = YOUR_SECRET_KEY
region_id = cn-north-1
endpoint = audit.jdcloud-api.com
scheme = https
timeout = 20
EOF
printf "%s" "default" > ~/.jdc/current
```

## SDK-Specific Issues

### Import Error: No module named 'jdcloud_sdk.services.audit'

**Cause:** 当前锁定的 JD Cloud SDK (`jdcloud_sdk>=1.6.26`) 中不包含 `jdcloud_sdk.services.audit` 模块。该模块可能在后续 SDK 版本中提供，或服务名不同。

**Fix:**
1. 确认官方 SDK 真实服务名（可能是其他模块名如 `dbaudit` 或通过 REST API 直接调用）
2. 通过 OpenAPI REST API (`https://audit.jdcloud-api.com/v1/...`) 直接调用
3. 如有新版 SDK 提供了该模块，更新 SDK：
```bash
uv pip install --upgrade jdcloud_sdk
```

### SSL/TLS Connection Error

**Cause:** Certificate validation issues or network restrictions

**Fix:**
1. Check network connectivity to `audit.jdcloud-api.com`
2. Verify SSL certificates are up to date
3. Check for proxy/firewall restrictions

### Timeout Error

**Cause:** Large time range or high event volume causing slow response

**Fix:**
1. Reduce time range (query smaller windows)
2. Add filters to reduce result set
3. Increase timeout in client configuration

## Data Quality Issues

### Missing Request/Response Details

Some events may not include full request/response details if:
- The event source doesn't capture full payload
- Data has been redacted for security reasons
- Event is from a legacy service integration

### Delayed Events

Events may take up to 15 minutes to appear in query results due to:
- Processing latency
- Cross-region replication
- High volume periods

## Performance Optimization

### Slow Queries

| Symptom | Cause | Solution |
|---------|-------|----------|
| Query timeout | Time range too large | Reduce to < 7 days |
| High memory usage | Large result set | Use pagination with smaller pageSize |
| Slow response | No filters applied | Add eventName/resourceType filters |
| Repeated queries | No caching | Cache results for short periods |

### Recommended Query Patterns

```python
# Good: Narrow time range with filters
params = DescribeEventsParameters(
    regionId="cn-north-1",
    startTime="2026-06-03T00:00:00+08:00",  # 1 day only
    endTime="2026-06-03T23:59:59+08:00",
    eventName="CreateInstances",  # specific event
    resourceType="vm",  # specific resource
    pageSize=50
)

# Avoid: Very broad query
params = DescribeEventsParameters(
    regionId="cn-north-1",
    startTime="2026-01-01T00:00:00+08:00",  # 6 months!
    endTime="2026-06-03T23:59:59+08:00",
    pageSize=100  # max, but still too many results
)
```

## Contact and Support

For persistent issues:
1. Check [JD Cloud Documentation](https://docs.jdcloud.com/cn/audit-log)
2. Review [OpenAPI Reference](https://docs.jdcloud.com/cn/audit-log/api)
3. Contact JD Cloud support with `requestId` from error responses
