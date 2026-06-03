# Troubleshooting JD Cloud EIP

## Common API Error Codes

| Code / HTTP | Meaning | Agent Action |
|-------------|---------|--------------|
| `InvalidParameter` | Request failed validation | Align body with OpenAPI; check required fields |
| `InsufficientBalance` | Account balance insufficient | HALT; user tops up account |
| `QuotaExceeded` | EIP quota exceeded | HALT; user requests quota increase |
| `AddressNotFound` | EIP not found | Verify address ID; check region |
| `AddressAlreadyAssociated` | EIP already in use | Dissociate first or use different EIP |
| `AddressNotAssociated` | EIP not associated | Verify EIP state before dissociation |
| `InstanceNotFound` | Target instance not found | Verify instance ID and type |
| `Throttling` | Rate limit exceeded | Retry with exponential backoff |
| `InternalError` | Server error | Retry with backoff; log requestId |

## Diagnostic Order

1. **Check EIP Status**: Describe the EIP to verify its current state.
2. **Verify Credentials**: Ensure `JDC_ACCESS_KEY` and `JDC_SECRET_KEY` are set correctly.
3. **Check Region**: Confirm the region matches where the EIP was created.
4. **List EIPs**: Use `describeAddresses` to see all EIPs in the region.
5. **Check Resource Association**: Verify target resource exists and is in valid state.
6. **Check Account Balance**: Ensure account has sufficient funds.
7. **Check Quota**: Verify EIP quota is not exceeded.

## Common Issues

### Issue: Cannot associate EIP

**Symptoms**: `AddressAlreadyAssociated` error

**Causes**:
- EIP is already associated with another resource
- EIP is in `in-use` state

**Solutions**:
- Dissociate the EIP from its current resource first
- Use a different EIP that is in `available` state

### Issue: Cannot dissociate EIP

**Symptoms**: `AddressNotAssociated` error

**Causes**:
- EIP is not currently associated with any resource
- EIP is in `available` state

**Solutions**:
- Verify EIP state using `describeAddress`
- Confirm you're using the correct EIP ID

### Issue: Cannot allocate EIP

**Symptoms**: `QuotaExceeded` or `InsufficientBalance` error

**Causes**:
- EIP quota has been reached
- Account balance is insufficient

**Solutions**:
- Request quota increase through JD Cloud console
- Add funds to the account

### Issue: CLI command fails with authentication error

**Symptoms**: "Invalid credentials" or authentication failures

**Causes**:
- CLI credentials not configured in `~/.jdc/config`
- Wrong credentials in config file
- `HOME` environment variable not set correctly in sandbox

**Solutions**:
- Configure `~/.jdc/config` with correct credentials
- Use the sandbox workaround to set `HOME` to a writable path
- Verify credentials are correct

### Issue: EIP status not changing

**Symptoms**: EIP remains in `releasing` or intermediate state

**Causes**:
- Network issues
- Backend processing delay
- Resource dependency

**Solutions**:
- Wait and retry describe operation
- Check if associated resources are still in use
- Contact JD Cloud support if issue persists

## Debug Commands

```bash
# Check jdc version
jdc --version

# List all EIPs in region
jdc --output json eip describe-addresses --region-id cn-north-1

# Describe specific EIP
jdc --output json eip describe-address --region-id cn-north-1 --address-id eip-xxx

# Check credentials file
cat ~/.jdc/config

# Check current profile
cat ~/.jdc/current
```

## Logging Tips

- Always capture `requestId` from API responses for support cases
- Log timestamps for all operations
- Record EIP state transitions
- Mask sensitive information (credentials, secret keys)
