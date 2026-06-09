# Integration

## Environment Setup (uv)

```bash
uv venv --python 3.10
source .venv/bin/activate
uv pip install jdcloud_cli jdcloud_sdk
```

## Integration with Load Balancer

### WAF + CLB Architecture
```
User → DNS → WAF → CLB → Backend VMs
```

```python
# 1. Create CLB with backend VMs (jdcloud-clb-ops)
# 2. Get CLB IP/domain
# 3. Add domain to WAF with CLB as origin (this skill)
# 4. Update DNS to point to WAF CNAME
```

## Integration with CDN

### CDN → WAF → Origin
```
User → CDN → WAF → Origin
```

Configure CDN origin to point to WAF CNAME for full protection.

## Integration with SSL Certificates

```python
# 1. Obtain certificate (jdcloud-ssl-ops or external)
# 2. Bind certificate to WAF domain (this skill)
# 3. Enable HTTPS protection
```

## Origin IP Whitelisting

For security, origin should only accept traffic from WAF:
```bash
# Get WAF egress IPs
jdc --output json waf describe-waf-ips --region-id cn-north-1

# Configure security group (jdcloud-vpc-ops)
# Allow only from WAF IP ranges
```

## Monitoring Integration

### With CloudMonitor (`jdcloud-cloudmonitor-ops`)
Set up alarms for:
- QPS threshold (approaching package limit)
- Block rate (unusual spikes)
- 5xx error rate (origin issues)
- SSL certificate expiry