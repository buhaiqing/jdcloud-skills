# Monitoring & Alerts — JD Cloud DNS

## DNS Monitoring Overview

JD Cloud DNS provides website monitoring for subdomains with alarm capabilities. Monitoring checks subdomain availability and triggers alarms when issues are detected.

## Monitor Types

| Type | Description |
|------|-------------|
| HTTP/HTTPS | Checks if the subdomain responds to HTTP/HTTPS requests |
| Custom | Configurable monitoring targets |

## Monitor Operations

### Create Monitor

```bash
jdc --output json domainservice create-monitor \
  --domain-id <domain-id> \
  --sub-domain-name <subdomain>
```

### List Monitors

```bash
jdc --output json domainservice describe-monitor \
  --domain-id <domain-id> \
  --page-number 1 --page-size 100
```

### Monitor Status Control

```bash
# Start monitoring
jdc --output json domainservice modify-monitor-status \
  --domain-id <domain-id> \
  --sub-domain-name <subdomain> \
  --status 1

# Stop monitoring
jdc --output json domainservice modify-monitor-status \
  --domain-id <domain-id> \
  --sub-domain-name <subdomain> \
  --status 2
```

### Delete Monitor

```bash
jdc --output json domainservice delete-monitor \
  --domain-id <domain-id> \
  --sub-domain-name <subdomain>
```

## Monitor Targets

```bash
# Add monitor target
jdc --output json domainservice create-monitor-target \
  --domain-id <domain-id> \
  --sub-domain-name <subdomain>

# List monitor targets
jdc --output json domainservice describe-monitor-target \
  --domain-id <domain-id> \
  --sub-domain-name <subdomain>
```

## Alarm Information

```bash
jdc --output json domainservice describe-monitor-alarm \
  --domain-id <domain-id> \
  --page-number 1 --page-size 100
```

## DNS Statistics

### Query Count

```bash
jdc --output json domainservice describe-domain-query-count \
  --domain-id <domain-id> \
  --start <timestamp> --end <timestamp>
```

### Query Traffic

```bash
jdc --output json domainservice describe-domain-query-traffic \
  --domain-id <domain-id> \
  --start <timestamp> --end <timestamp>
```

## Action Log (Audit)

```bash
jdc --output json domainservice describe-action-log \
  --page-number 1 --page-size 100 \
  --start-time <timestamp> --end-time <timestamp>
```

## CloudMonitor Integration

DNS metrics are available in CloudMonitor for alarm rule configuration. Delegate alarm rule management to `jdcloud-cloudmonitor-ops`.

## Best Practices

1. **Enable monitoring** for all production subdomains
2. **Set appropriate check intervals** — balance between responsiveness and cost
3. **Configure alarm notifications** for critical subdomains
4. **Review action logs** regularly for unauthorized changes
5. **Monitor query trends** to detect anomalies (DDoS, misconfiguration)
