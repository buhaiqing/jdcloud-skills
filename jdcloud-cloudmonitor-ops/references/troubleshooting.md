# Cloud Monitor Troubleshooting Guide

## Common Error Codes

| Error Code | Description | Solution |
|-----------|-------------|----------|
| `InvalidParameter` | Invalid or missing parameters | Check request parameters against API requirements |
| `InvalidParameterValue` | Invalid parameter value | Check parameter value format and allowed range |
| `MissingParameter` | Missing required parameter | Provide the missing required parameter |
| `ResourceNotFound` | Resource not found | Verify the resource ID is correct |
| `MetricNotFound` | Metric not found | Confirm the metric name is correct |
| `AlarmNotFound` | Alarm rule not found | Check the alarm rule ID is correct |
| `ServiceNotFound` | Service not found | Confirm the service code is correct |
| `QuotaExceeded` | Quota limit exceeded | Check if resource quota limit has been reached |
| `RateLimitExceeded` | Request rate limit exceeded | Reduce request frequency or request a rate limit increase |
| `InternalError` | Internal error | Retry later or contact technical support |
| `Unauthorized` | Unauthorized | Check access key and permission configuration |
| `RegionNotFound` | Region not found | Confirm the region ID is correct |

## Monitoring Data Query Issues

### Issue 1: No monitoring data returned

**Symptom**: Calling `describe-metric-data` returns empty data.

**Possible causes and solutions**:

1. **Resource has not generated data yet**
   - Newly created resources may not have monitoring data yet
   - Wait 5-10 minutes and retry

2. **Incorrect time range**
   - Check `start-time` and `end-time` format (ISO8601)
   - Ensure the query time range is within the data retention period (default 15 days)
   ```bash
   # Correct time format
   --start-time "2024-01-01T00:00:00Z"
   --end-time "2024-01-01T23:59:59Z"
   ```

3. **Incorrect resource ID**
   - Confirm the `resource-id` parameter value is correct
   - Use `jdc vm describe-instances` to verify the resource exists

4. **Incorrect metric name**
   - Use `describe-metrics` to query the available metric list
   - Note that metric names are case-sensitive

### Issue 2: Monitoring data delay

**Symptom**: Queried data is several minutes behind the current time.

**Solutions**:
- Cloud monitoring data collection and processing takes time, typically a 3-5 minute delay
- For real-time scenarios, use the `last-downsample` API to query the latest data
- For lower latency, consider using Application Performance Monitoring (SGM) or custom monitoring

### Issue 3: Discontinuous monitoring data

**Symptom**: Monitoring data curve has gaps or missing points.

**Possible causes and solutions**:

1. **Resource state changes**
   - Resources do not generate monitoring data during shutdown or restart
   - Check resource running status

2. **Network issues**
   - Unreachable resources may cause data collection failure
   - Check resource network connectivity

3. **Collection anomalies**
   - Contact JD Cloud technical support to check collection service status

## Alarm Rule Issues

### Issue 1: Alarm rule not triggered

**Symptom**: Monitoring metrics have exceeded the threshold, but the alarm has not triggered.

**Troubleshooting steps**:

1. **Check alarm rule status**
   ```bash
   jdc monitor describe-alarm --region-id cn-north-1 --alarm-id alarm-xxx
   ```
   - Confirm the rule status is `enabled`
   - Check if the `status` field is `ALARM`

2. **Check threshold and comparison operator**
   - Confirm the threshold value is correct
   - Check the comparison operator direction (gt/lt/ge/le)
   - Note the numeric type (integer vs float)

3. **Check evaluation periods**
   - `evaluation-periods` specifies how many consecutive periods must be met before triggering
   - Set to 1 for immediate triggering

4. **Check monitoring data**
   ```bash
   jdc monitor describe-metric-data \
     --region-id cn-north-1 \
     --metric vm.cpu.util \
     --service-code vm \
     --resource-id i-xxx \
     --start-time "2024-01-01T00:00:00Z" \
     --end-time "2024-01-01T23:59:59Z"
   ```

### Issue 2: Alarm notification not received

**Symptom**: Alarm has been triggered, but no notification was received.

**Troubleshooting steps**:

1. **Check notification type configuration**
   - Confirm `notice-type` includes the required notification methods
   - Supported types: `sms`, `email`, `callback`

2. **Check contact configuration**
   - Confirm `contact-group-id` is correct
   - Verify contact information is complete (phone number, email)
   ```bash
   jdc monitor describe-alarm-contacts --region-id cn-north-1
   ```

3. **Check notification time window**
   - Confirm the alarm time falls within the notification window
   - Check the `notice-time` configuration

4. **Check notification period**
   - `notice-period` controls the repeat notification interval
   - If set to 0, no repeat notifications will be sent during the alarm duration

5. **Check SMS/email quota**
   - Confirm the account SMS/email quota has not been exhausted

### Issue 3: Alarm fires too frequently

**Symptom**: Alarm frequently toggles between ALARM and OK states (alarm flapping).

**Solutions**:

1. **Adjust threshold**
   - Raise or lower the threshold appropriately to avoid marginal value fluctuations
   - It is recommended to set a reasonable buffer

2. **Increase evaluation periods**
   - Increase `evaluation-periods` from 1 to 2 or 3
   - Avoid transient fluctuations triggering alarms

3. **Use data aggregation**
   - Increase the `period` value to use data over a longer time window
   - Smooth out transient fluctuations

4. **Configure alarm suppression**
   - Set `notice-period` to control repeat notification frequency
   - Avoid alarm storms

## CLI Usage Issues

### Issue 1: Authentication failure

**Symptom**: Returns `Unauthorized` or `InvalidAccessKey` error.

**Solutions**:

1. **Check environment variables (NEVER print actual values to prevent leaks)**
   ```bash
   # SECURITY: NEVER print the actual secret key value
   if [ -n "$JDC_ACCESS_KEY" ] && [ -n "$JDC_SECRET_KEY" ]; then
       echo "Environment variables set (JDC_SECRET_KEY=<masked>)"
   else
       echo "Error: JDC_ACCESS_KEY or JDC_SECRET_KEY not set"
   fi
   ```

2. **Reconfigure credentials**
   ```bash
   jdc config init
   ```

3. **Check key permissions**
   - Confirm the Access Key has permission to call the Cloud Monitor API
   - Check whether the key has been disabled or deleted

4. **Check system time**
   - Ensure system time is synchronized with standard time
   - Time deviation can cause signature verification failure

### Issue 2: Command not found

**Symptom**: Running `jdc monitor` reports command not found.

**Solutions**:

1. **Check CLI version**
   ```bash
   jdc --version
   ```
   - Cloud Monitor functionality requires CLI 1.x or above

2. **Update CLI**
   ```bash
   pip install --upgrade jdcloud-cli
   ```

3. **Check installation path**
   ```bash
   which jdc
   ```
   - Ensure the installation path is in the PATH environment variable

### Issue 3: JSON parameter parsing error

**Symptom**: Commands with JSON parameters fail to execute.

**Solutions**:

1. **Use quotes correctly**
   ```bash
   # Linux/macOS
   --dimensions '{"key":"value"}'
   
   # Windows PowerShell
   --dimensions '{\"key\":\"value\"}'
   
   # Windows CMD
   --dimensions "{\"key\":\"value\"}"
   ```

2. **Validate JSON format**
   - Use online tools to validate JSON format
   - Ensure key names and string values use double quotes

## Custom Monitoring Issues

### Issue 1: Custom data submission failure

**Symptom**: Calling `put-metric-data` returns an error.

**Solutions**:

1. **Check namespace**
   - Namespace can only contain letters, digits, underscores, and hyphens
   - Cannot start with a digit

2. **Check metric name**
   - Metric name can only contain letters, digits, underscores, and dots
   - Cannot start with a digit or dot

3. **Check dimensions**
   - Dimension key names can only contain letters, digits, and underscores
   - Dimension value length is limited to 256 characters

4. **Check timestamp**
   - Timestamp must be within the last 2 hours
   - Must be in ISO8601 format

### Issue 2: Custom data not queryable

**Symptom**: Data was submitted successfully, but cannot be queried.

**Solutions**:

1. **Wait for data ingestion**
   - Custom monitoring data has a 1-2 minute delay
   - Wait and retry the query

2. **Check query parameters**
   - Ensure `namespace` and `metric-name` match the submission parameters
   - Check if the time range includes the submission time

3. **Check dimension matching**
   - Query dimensions must exactly match the submission dimensions
   - Or use the correct dimension filtering

## Performance Issues

### Issue 1: Slow API calls

**Symptom**: API response time is too long.

**Solutions**:

1. **Optimize query scope**
   - Narrow the `start-time` and `end-time` range
   - Reduce the data volume per query

2. **Use pagination**
   - Set an appropriate `page-size` (recommended 20-50)
   - Avoid returning too much data at once

3. **Use caching**
   - Monitoring data changes slowly, cache query results when appropriate
   - Avoid querying the same data repeatedly

4. **Concurrency control**
   - Limit the number of concurrent requests
   - Avoid triggering rate limiting

### Issue 2: Rate limit reached

**Symptom**: Returns `RateLimitExceeded` error.

**Solutions**:

1. **Reduce request frequency**
   - Increase the request interval
   - Use exponential backoff retry

2. **Batch operations**
   - Use batch APIs instead of multiple individual queries
   - Combine multiple requests

3. **Request quota increase**
   - Contact JD Cloud technical support to request a higher rate limit

## Getting Help

### View CLI help

```bash
# View monitor command help
jdc monitor --help

# View specific command help
jdc monitor describe-metric-data --help
```

### Enable debug mode

```bash
jdc monitor describe-alarms --region-id cn-north-1 --debug
```

### Contact technical support

- JD Cloud Ticket System: https://ticket.jdcloud.com/
- Customer Service Hotline: 400-615-1212
- Technical Support Email: support@jdcloud.com