# Troubleshooting — JD Cloud VPN

## Common API Error Codes

| Code / HTTP | Meaning | Agent Action |
|-------------|---------|--------------|
| `InvalidParameter` / 400 | Request failed validation | Align body with OpenAPI; check CIDR format, IP validity, PSK length |
| `ResourceNotFound` / 404 | Resource does not exist | Verify ID; check region |
| `ResourceInUse` / 409 | Resource is referenced by others | For delete: remove dependent VPN connections first |
| `QuotaExceeded` / 400 | Account quota limit reached | HALT; user requests quota increase |
| `InsufficientBalance` / 400 | Account balance insufficient | HALT; user tops up account |
| `VpnGateway.VpcNotExists` | VPC ID invalid | Verify VPC via `jdcloud-vpc-ops` |
| `VpnConnection.GatewayNotAvailable` | VPN GW or CG not in `available` state | Wait for creation to complete |
| `InternalError` / 500 | Server-side error | Retry with backoff; HALT if persists |

## Diagnostic Order

### VPN Tunnel Down

1. **Check connection state**: `describeVpnConnection` → `state` should be `available`.
2. **Check gateway states**: Both `VpnGateway` and `CustomerGateway` must be `available`.
3. **Verify remote IP**: Customer gateway IP must be reachable from JD Cloud.
4. **Check IKE/IKEv2 negotiation**:
   - Verify both sides use the same IKE version.
   - Verify encryption, integrity, and DH group match.
   - Verify PSK is identical on both sides.
5. **Check subnet configuration**:
   - `localSubnets` and `remoteSubnets` must not overlap.
   - Both sides must define matching subnets (or superset).
6. **Check route tables**:
   - VPC route table must route remote subnets to the VPN gateway.
   - Remote side must route local subnets to the customer gateway device.
7. **Check security groups / ACLs**:
   - Ensure UDP 500 (IKE) and UDP 4500 (NAT-T) are allowed.
   - Ensure ESP (IP protocol 50) is allowed if not using NAT-T.
8. **Check DPD settings**: Mismatched DPD may cause premature teardown.

### High Packet Loss or Latency

1. **Check bandwidth utilization**: Compare against VPN gateway spec.
2. **Check for asymmetric routing**: Both directions must traverse the same tunnel.
3. **Check MTU**: IPsec overhead reduces effective MTU. Consider lowering MTU to 1380-1400 bytes.
4. **Review IPsec lifetime**: Frequent rekeys may cause brief interruptions.

### Unable to Create VPN Connection

1. Verify `vpnGatewayId` exists and is `available`.
2. Verify `customerGatewayId` exists and is `available`.
3. Verify `psk` meets minimum length requirements.
4. Verify `localSubnets` and `remoteSubnets` are valid CIDRs.
5. Verify no quota limits are exceeded.

### Delete Fails with ResourceInUse

1. List all VPN connections referencing the gateway or customer gateway.
2. Delete dependent VPN connections first.
3. Retry the delete operation.