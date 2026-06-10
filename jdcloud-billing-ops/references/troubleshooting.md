# Troubleshooting — JD Cloud Billing

## Common API Error Codes

| Code / HTTP | Meaning | Agent Action |
|-------------|---------|--------------|
| `InvalidParameter` / 400 | Request failed validation | Check date format (`yyyy-MM-dd HH:mm:ss`) and range (≤1 month) |
| `InvalidDateRange` / 400 | Date range exceeds maximum | Reduce range to single month |
| `Unauthorized` / 401 | Invalid or missing credentials | Verify `JDC_ACCESS_KEY` and `JDC_SECRET_KEY` |
| `Forbidden` / 403 | Insufficient permissions | Check if account has billing read permissions |
| `InternalError` / 500 | Server error | Retry with backoff; contact support if persistent |
| `Throttling` / 429 | Rate limit exceeded | Implement exponential backoff |
| `ProductNotSupported` / 400 | Product code not recognized | Verify product code against API docs |

## Diagnostic Order

### 1. Authentication Issues

**Symptom:** `Unauthorized` or `InvalidCredentials`

**Checklist:**
```bash
# Verify environment variables are set
echo "AK exists: $([ -n "$JDC_ACCESS_KEY" ] && echo 'YES' || echo 'NO')"
echo "SK exists: $([ -n "$JDC_SECRET_KEY" ] && echo 'YES' || echo 'NO')"

# NEVER print actual values
```

**Resolution:**
```bash
export JDC_ACCESS_KEY="your-access-key"
export JDC_SECRET_KEY="your-secret-key"
export JDC_REGION="cn-north-1"
```

### 2. Date Range Issues

**Symptom:** `InvalidDateRange`

**Constraints:**
- Maximum range: **1 month** per query (no cross-month support)
- Format: `yyyy-MM-dd HH:mm:ss`
- End date must be ≥ Start date

**Example valid ranges:**
```python
# Valid: single month
start_time = "2026-05-01 00:00:00"
end_time = "2026-05-31 23:59:59"

# Invalid: cross-month
start_time = "2026-04-01 00:00:00"  # Will fail
end_time = "2026-05-31 23:59:59"
```

### 3. Pagination Issues

**Symptom:** Incomplete results

**Resolution:**
- Always check `totalCount` vs retrieved records
- Implement pagination loop
- Max `pageSize` is 1000

### 4. SDK Import Issues

**Symptom:** `ModuleNotFoundError`

**Resolution:**
```bash
# Activate virtual environment
source .venv/bin/activate

# Reinstall SDK
uv pip install --force-reinstall jdcloud_sdk
```

### 5. Timeout Issues

**Symptom:** Requests hang or timeout

**Resolution:**
```python
from jdcloud_sdk.core.config import Config

# Configure timeout
config = Config(timeout=30)  # 30 seconds
client = BillingClient(credential, config=config)
```

## Common Scenarios

### Scenario 1: Balance Query Returns Zero

**Possible causes:**
1. Wrong account credentials
2. Account is sub-account without billing permissions
3. API response parsing error

**Debug steps:**
```python
# Add debug logging
resp = client.send(req)
print(f"Raw response: {resp}")  # Inspect full response
print(f"Result: {resp.result}")  # Check result object
print(f"Error: {resp.error}")    # Check for API errors
```

### Scenario 2: Consumption Records Empty

**Possible causes:**
1. Date range has no activity
2. Wrong region filter
3. Account has no resources during period

**Debug steps:**
1. Try broader date range (single month)
2. Remove optional filters
3. Verify account has active resources

### Scenario 3: Voucher Balance Mismatch

**Possible causes:**
1. Voucher expired between query and use
2. Voucher has usage restrictions
3. Currency conversion differences

**Resolution:**
- Always re-query voucher status before use
- Check voucher `status` and `expireTime`

## SDK Version Compatibility

| SDK Version | Python | Notes |
|-------------|--------|-------|
| ≥ 1.6.0 | 3.10+ | Recommended |
| < 1.6.0 | 3.10+ | May lack newer billing APIs |

## Support Resources

- **JD Cloud Documentation**: https://docs.jdcloud.com/
- **API Reference**: https://docs.jdcloud.com/cn/billing/api/overview
- **SDK Source**: https://github.com/jdcloud-api/jdcloud-sdk-python
