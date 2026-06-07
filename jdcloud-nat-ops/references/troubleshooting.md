# Troubleshooting — JD Cloud NAT Gateway

## Common API Error Codes

| Code / HTTP | Meaning | Agent Action |
|-------------|---------|--------------|
| `InvalidParameter` (400) | Request failed validation | Align body with OpenAPI; check field names/types |
| `NatGateway.NotFound` (404) | NAT gateway ID does not exist | Verify `natGatewayId` via `describeNatGateways` list |
| `NatGateway.VpcNotExists` (400) | VPC does not exist | Verify VPC ID via `jdcloud-vpc-ops` |
| `NatGateway.ElasticIpNotExists` (400) | EIP does not exist | Allocate EIP via `jdcloud-eip-ops` first |
| `NatGateway.InvalidSubnet` (400) | Subnet not found or doesn't belong to VPC | Verify subnet via `jdcloud-vpc-ops` |
| `NatGateway.InvalidState` (400) | NAT in wrong state for operation | Wait for `available` state |
| `NatGateway.DnatPortConflict` (400) | DNAT rule port already in use on EIP | Use different port or EIP |
| `NatGateway.SnatRuleExists` (400) | SNAT rule already exists for subnet | Describe existing rules; reuse or modify |
| `NatGateway.ElasticIpInUse` (400) | EIP already associated with another resource | Disassociate EIP first |
| `QuotaExceeded` (400) | NAT gateway quota exceeded | Request quota increase |
| `InsufficientBalance` (403) | Account balance insufficient | HALT; user tops up account |
| `Throttling` (429) | Request rate exceeded | Back off and retry with exponential delay |
| `InternalError` (500) | Server-side error | Retry up to 3 times; capture requestId |

## Diagnostic Order

1. **Describe the NAT Gateway**
   ```bash
   jdc --output json vpc describe-nat-gateway --region-id cn-north-1 --nat-gateway-id nat-xxxxxx
   ```
   Check `state`, `elasticIpAddresses`, `snatRuleCount`, `dnatRuleCount`.

2. **List NAT Gateways** (if ID unknown)
   ```bash
   jdc --output json vpc describe-nat-gateways --region-id cn-north-1
   ```
   Find the target NAT by name or VPC ID.

3. **Check Dependent Resources**
   - **VPC**: Verify VPC exists via `jdcloud-vpc-ops`
   - **EIP**: Verify EIP is allocated and not associated elsewhere via `jdcloud-eip-ops`
   - **Subnet**: Verify subnet exists and belongs to the correct VPC

4. **Check Route Tables**
   For SNAT to work, the subnet's route table must have a `0.0.0.0/0` route pointing to the NAT gateway. Verify via `jdcloud-vpc-ops`.

5. **Check State Consistency**
   - NAT in `creating` state: wait for `available`
   - NAT in `deleting` state: wait for deletion to complete
   - NAT in `error` state: check error details, recreate if needed

## Common Scenarios

### Scenario: Cannot Access Internet from Private Subnet

1. Verify NAT Gateway exists and is `available`
2. Verify SNAT rule exists for the subnet: `describeNatGateway` → check `snatRuleCount`
3. Verify EIP is associated with the NAT: check `elasticIpAddresses`
4. Verify route table has `0.0.0.0/0` → NAT gateway
5. Verify security group/NACL allows outbound traffic

### Scenario: DNAT Port Forwarding Not Working

1. Verify NAT Gateway exists and is `available`
2. Verify DNAT rule exists: `describeNatGateway` → check `dnatRuleCount`
3. Verify EIP: port is not used by another DNAT rule (port conflict)
4. Verify target private IP is reachable (instance is running)
5. Verify security group allows inbound traffic on the target port

### Scenario: NAT Gateway Creation Fails

1. Check error code in response
2. VPC not found → verify VPC ID
3. EIP not found → allocate EIP first
4. Quota exceeded → request quota increase
5. Invalid parameters → check field names and types

### Scenario: EIP Disassociation Fails

1. Check if EIP is the last one associated (would break connectivity)
2. Verify EIP is not in use by SNAT/DNAT rules
3. Disassociation may be rejected if it would break active rules

## CLI-Specific Issues

| Issue | Possible Cause | Fix |
|-------|---------------|-----|
| `unrecognized arguments: --output json` | Wrong argument position | Place `--output json` BEFORE `vpc` |
| `Error: Unsupported field: natGatewaySpec` | JSON spec format mismatch | Use `--elastic-ip-ids` directly, not a JSON object for `create-nat-gateway` |
| `command not found: create-snat-rule` | CLI version too old | Update to latest `jdcloud_cli` |
| `Error parsing JSON` | Invalid JSON in `--snat-rule-spec` | Use single-quoted JSON with double-quoted keys |

## Best Practices

- Always describe the resource before and after mutation to verify state
- Use the same region consistently across all operations
- For production NAT gateways, maintain at least 2 EIPs for SNAT HA (WAF-REL-010)
- Monitor bandwidth utilization and right-size NAT specification (WAF-PERF-049)
- Document all rule changes (SNAT/DNAT) with descriptions