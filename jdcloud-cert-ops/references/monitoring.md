# Monitoring & Alerts — JD Cloud SSL Certificate

## Certificate Expiry Monitoring

SSL certificates have fixed validity periods. Proactive monitoring prevents service disruption from expired certificates.

### Expiry Classification

| Status | Condition | Action |
|--------|-----------|--------|
| **CRITICAL** | `endDate < now` | Certificate expired — immediate renewal required |
| **WARNING** | `days_left ≤ 30` | Expiring soon — begin renewal process |
| **INFO** | `days_left ≤ 60` | Approaching expiry — plan renewal |
| **OK** | `days_left > 60` | No action needed |

### Automated Expiry Check

```bash
jdc --output json ssl describe-certs --page-number 1 --page-size 100 | \
  python3 -c "
import json, sys
from datetime import datetime, timezone
data = json.load(sys.stdin)
now = datetime.now(timezone.utc)
for c in data['result']['certListDetails']:
    end = datetime.fromisoformat(c['endDate'])
    days = (end - now).days
    status = 'CRITICAL' if days < 0 else 'WARNING' if days <= 30 else 'INFO' if days <= 60 else 'OK'
    print(f'{status}: {c[\"certId\"]} | {c[\"domainName\"]} | {c[\"endDate\"]} | {days}d')
"
```

## Cross-Service Binding Monitoring

When a certificate expires, all services using it are affected:

| Service | Impact | Check Method |
|---------|--------|--------------|
| **CLB HTTPS Listeners** | TLS termination fails | `jdc --output json lb describe-listeners` |
| **CDN Domains** | HTTPS delivery fails | `jdc --output json cdn get-ssl-cert-list` |

## CloudMonitor Integration

For proactive alerting, configure CloudMonitor alarm rules for certificate expiry. Delegate alarm rule management to `jdcloud-cloudmonitor-ops`.

## Best Practices

1. **Run expiry cruise weekly** — catch expiring certs early
2. **Begin renewal 30+ days before expiry** — allows time for validation
3. **Check bindings before renewal** — know which services are affected
4. **Test after renewal** — verify CLB/CDN pick up the new cert
5. **Set CloudMonitor alarms** — automated alerting for approaching expiry
