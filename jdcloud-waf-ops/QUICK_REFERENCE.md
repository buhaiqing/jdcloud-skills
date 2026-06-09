# JD Cloud WAF Quick Reference

> Quick command reference for Web Application Firewall operations. For full details, see [SKILL.md](SKILL.md) and [CLI Usage](references/cli-usage.md).

## WAF Instance Quick Reference

```bash
# List instances
jdc --output json waf describe-instances --region-id cn-north-1

# Create instance
jdc --output json waf create-instance \
  --region-id cn-north-1 \
  --instance-spec '{"name":"prod-waf","packageCode":"waf.advanced","buyType":1}'

# Describe instance
jdc --output json waf describe-instance \
  --region-id cn-north-1 --instance-id waf-xxxxx

# Delete instance (must have no domains)
jdc --output json waf delete-instance \
  --region-id cn-north-1 --instance-id waf-xxxxx
```

## Domain Management Quick Reference

```bash
# List domains
jdc --output json waf describe-domains \
  --region-id cn-north-1 --instance-id waf-xxxxx

# Add domain
jdc --output json waf add-domain \
  --region-id cn-north-1 --instance-id waf-xxxxx \
  --domain-config '{"domain":"example.com","protocol":"HTTP","originIp":["1.2.3.4"]}'

# Enable / Disable protection
jdc --output json waf enable-domain \
  --region-id cn-north-1 --instance-id waf-xx --domain-id domain-xx
jdc --output json waf disable-domain \
  --region-id cn-north-1 --instance-id waf-xx --domain-id domain-xx

# Delete domain
jdc --output json waf delete-domain \
  --region-id cn-north-1 --instance-id waf-xxxxx --domain-id domain-xxxxx
```

## SSL Certificate Quick Reference

```bash
# Bind certificate
jdc --output json waf bind-cert \
  --region-id cn-north-1 --instance-id waf-xxxxx --domain-id domain-xxxxx \
  --cert-spec '{"certName":"example-cert","certContent":"-----BEGIN CERTIFICATE-----...","keyContent":"-----BEGIN PRIVATE KEY-----..."}'

# Unbind certificate
jdc --output json waf unbind-cert \
  --region-id cn-north-1 --instance-id waf-xxxxx --domain-id domain-xxxxx
```

## Security Rule Quick Reference

```bash
# List rules
jdc --output json waf describe-rules \
  --region-id cn-north-1 --instance-id waf-xxxxx --domain-id domain-xxxxx

# Create IP blacklist
jdc --output json waf create-rule \
  --region-id cn-north-1 --instance-id waf-xxxxx --domain-id domain-xxxxx \
  --rule-spec '{"ruleName":"block-bad-ips","ruleType":"ip_blacklist","ipList":["192.168.1.1","10.0.0.0/24"],"action":"block","status":1}'

# Create rate limit
jdc --output json waf create-rule \
  --region-id cn-north-1 --instance-id waf-xxxxx --domain-id domain-xxxxx \
  --rule-spec '{"ruleName":"api-throttle","ruleType":"rate_limit","matchItems":[{"field":"url","operator":"contains","value":"/api/"}],"rateLimit":{"threshold":100,"period":60,"action":"captcha"},"status":1}'

# Delete rule
jdc --output json waf delete-rule \
  --region-id cn-north-1 --instance-id waf-xxxxx --domain-id domain-xxxxx \
  --rule-id rule-xxxxx
```

## Attack Logs Quick Reference

```bash
# Query attack logs
jdc --output json waf describe-attack-logs \
  --region-id cn-north-1 --instance-id waf-xxxxx --domain-id domain-xxxxx \
  --start-time "2026-06-01T00:00:00Z" --end-time "2026-06-08T00:00:00Z"

# Query access logs
jdc --output json waf describe-access-logs \
  --region-id cn-north-1 --instance-id waf-xxxxx --domain-id domain-xxxxx \
  --start-time "2026-06-01T00:00:00Z" --end-time "2026-06-08T00:00:00Z"
```

## Rule Types Quick Reference

| Type | Purpose | Example Action |
|------|---------|---------------|
| `ip_blacklist` | Block specific IPs | `block` |
| `ip_whitelist` | Always allow IPs | `allow` |
| `rate_limit` | Throttle requests | `captcha` or `block` |
| `geo_blocking` | Block by country | `block` |
| `url_acl` | Path-based rules | `block` or `allow` |
| `bot_management` | Bot challenge | `challenge` |

## Match Fields

| Field | Description |
|-------|-------------|
| `ip` | Client IP address |
| `url` | Request path |
| `host` | Host header |
| `user_agent` | User-Agent header |
| `method` | HTTP method |
| `header` | Custom header |
| `query_string` | URL parameters |

## Rule Actions

| Action | Behavior |
|--------|----------|
| `block` | HTTP 403 |
| `allow` | Pass through |
| `log` | Record only |
| `captcha` | CAPTCHA challenge |
| `rate_limit` | Throttle |

## Package Types

| Package | QPS | Use Case |
|---------|-----|----------|
| `waf.basic` | 1,000 | Small sites |
| `waf.advanced` | 5,000 | Medium sites |
| `waf.enterprise` | 20,000+ | Large sites |

## JSON Extraction Quick Reference

```bash
# List domains with CNAME
jdc --output json waf describe-domains --region-id cn-north-1 --instance-id waf-xx \
  | jq -r '.result.domains[] | "\(.domainId)\t\(.domain)\t\(.cname)\t\(.status)"' \
  | column -t -s $'\t'

# Check if instance has domains before delete
jdc --output json waf describe-domains --region-id cn-north-1 --instance-id waf-xx \
  | jq '.result.domains | length'

# Extract attack log summary
jdc --output json waf describe-attack-logs --region-id cn-north-1 --instance-id waf-xx \
  --start-time "2026-06-01T00:00:00Z" --end-time "2026-06-08T00:00:00Z" \
  | jq -r '.result.logs[] | "\(.attackTime)\t\(.attackType)\t\(.clientIp)\t\(.url)"' \
  | head -20
```

## Python SDK Quick Start

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.waf.client import WafClient
from jdcloud_sdk.services.waf.apis.DescribeInstancesRequest import DescribeInstancesRequest, DescribeInstancesParameters

credential = Credential(
    os.environ['JDC_ACCESS_KEY'],
    os.environ['JDC_SECRET_KEY']
)
client = WafClient(credential, os.environ.get('JDC_REGION', 'cn-north-1'))

# List instances
params = DescribeInstancesParameters(regionId='cn-north-1', pageNumber=1, pageSize=20)
request = DescribeInstancesRequest(parameters=params)
response = client.describeInstances(request)

if response.error is None:
    for inst in response.result.instances:
        print(f"{inst.instanceId}: {inst.name} ({inst.packageCode})")
```

## DNS Setup Checklist

1. Add domain to WAF → get CNAME
2. Update DNS: `CNAME example.com → waf-xxxxx.jdcloudwaf.com`
3. Verify: `dig example.com` returns WAF CNAME
4. Test HTTPS if certificate bound

## Related Documents

| Document | Description |
|----------|-------------|
| [SKILL.md](SKILL.md) | Full skill definition |
| [CLI Usage](references/cli-usage.md) | Complete CLI reference |
| [Security Rules](references/security-rules.md) | Rule structure & examples |
| [API & SDK](references/api-sdk-usage.md) | SDK operations map |
| [Troubleshooting](references/troubleshooting.md) | DNS, SSL, false positives |
| [Core Concepts](references/core-concepts.md) | WAF instance, domain, CNAME |
