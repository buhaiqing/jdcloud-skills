# Monitoring — JD Cloud VPN

## Key Metrics

| Metric Name | Namespace | Description | Alert Threshold Suggestion |
|-------------|-----------|-------------|---------------------------|
| TunnelState | `vpn` / `vpnConnection` | VPN tunnel state (1 = up, 0 = down) | == 0 for 2 minutes |
| TunnelRxBytes | `vpn` / `vpnConnection` | Bytes received through tunnel | Baseline + anomaly |
| TunnelTxBytes | `vpn` / `vpnConnection` | Bytes transmitted through tunnel | Baseline + anomaly |
| TunnelRxPackets | `vpn` / `vpnConnection` | Packets received | Baseline + anomaly |
| TunnelTxPackets | `vpn` / `vpnConnection` | Packets transmitted | Baseline + anomaly |
| TunnelDropPackets | `vpn` / `vpnConnection` | Dropped packets | > 100/min |
| GatewayBandwidthUsage | `vpn` / `vpnGateway` | Current bandwidth usage (bps) | > 80% of spec for 5 min |
| IKE negotiation failures | `vpn` / `vpnConnection` | Count of IKE negotiation failures | > 5 in 5 minutes |

> **Note:** Exact metric namespaces and names should be verified in JD Cloud CloudMonitor documentation. The table above represents typical VPN monitoring dimensions.

## Alert Example (structure only)

```json
{
  "metric": "vpn/vpnConnection/TunnelState",
  "dimensions": {
    "vpnConnectionId": "vpnconn-xxxxxxxx"
  },
  "threshold": 0,
  "comparisonOperator": "EqualTo",
  "period": 60,
  "evaluationPeriods": 2,
  "alarmActions": ["notify-sns-topic"]
}
```

## Health Check Commands

```bash
# Check all VPN connections and their states
jdc --output json vpn describe-vpn-connections \
  --region-id cn-north-1 \
  --page-number 1 \
  --page-size 100 | jq '.result.vpnConnections[] | {id: .vpnConnectionId, state: .state}'

# Check a specific VPN gateway and its connections
jdc --output json vpn describe-vpn-gateway \
  --region-id cn-north-1 \
  --vpn-gateway-id vpngw-xxxxxxxx | jq '.result.vpnGateway | {id, state, name}'
```

## Log Analysis

If JD Cloud provides VPN operation logs (via audit / CloudTrail equivalent):
- Search for `createVpnConnection`, `deleteVpnConnection` events.
- Correlate tunnel state changes with configuration changes.
- Monitor for repeated IKE negotiation failures.