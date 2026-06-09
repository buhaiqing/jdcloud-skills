# CLI — WAF (`jdc waf`)

## Install and Config
- Install: `uv pip install jdcloud_cli`
- Config: `~/.jdc/config` INI file

## Critical CLI Behavior
- `--output json` is a **top-level argument** — MUST be placed BEFORE `waf` subcommand
- `--no-interactive` does NOT exist

## Command Reference

### Instance Management
```bash
# List WAF instances
jdc --output json waf describe-instances \
  --region-id cn-north-1

# Create instance
jdc --output json waf create-instance \
  --region-id cn-north-1 \
  --instance-spec '{"name":"my-waf","packageCode":"waf.basic","buyType":1}'

# Describe instance
jdc --output json waf describe-instance \
  --region-id cn-north-1 \
  --instance-id waf-xxxxxx

# Delete instance
jdc --output json waf delete-instance \
  --region-id cn-north-1 \
  --instance-id waf-xxxxxx
```

### Domain Management
```bash
# List domains
jdc --output json waf describe-domains \
  --region-id cn-north-1 \
  --instance-id waf-xxxxxx

# Add domain
jdc --output json waf add-domain \
  --region-id cn-north-1 \
  --instance-id waf-xxxxxx \
  --domain-config '{"domain":"example.com","protocol":"HTTP","originIp":["1.2.3.4"]}'

# Describe domain
jdc --output json waf describe-domain \
  --region-id cn-north-1 \
  --instance-id waf-xxxxxx \
  --domain-id domain-xxxxxx

# Enable/disable domain
jdc --output json waf enable-domain --region-id cn-north-1 --instance-id waf-xx --domain-id domain-xx
jdc --output json waf disable-domain --region-id cn-north-1 --instance-id waf-xx --domain-id domain-xx

# Delete domain
jdc --output json waf delete-domain \
  --region-id cn-north-1 \
  --instance-id waf-xxxxxx \
  --domain-id domain-xxxxxx
```

### Certificate Management
```bash
# Bind certificate
jdc --output json waf bind-cert \
  --region-id cn-north-1 \
  --instance-id waf-xxxxxx \
  --domain-id domain-xxxxxx \
  --cert-spec '{"certName":"example-cert","certContent":"-----BEGIN...","keyContent":"-----BEGIN..."}'
```

### Rule Management
```bash
# List rules
jdc --output json waf describe-rules \
  --region-id cn-north-1 \
  --instance-id waf-xxxxxx \
  --domain-id domain-xxxxxx

# Create IP blacklist rule
jdc --output json waf create-rule \
  --region-id cn-north-1 \
  --instance-id waf-xxxxxx \
  --domain-id domain-xxxxxx \
  --rule-spec '{"ruleName":"block-bad-ips","ruleType":"ip_blacklist","ipList":["192.168.1.1"],"action":"block","status":1}'

# Delete rule
jdc --output json waf delete-rule \
  --region-id cn-north-1 \
  --instance-id waf-xxxxxx \
  --domain-id domain-xxxxxx \
  --rule-id rule-xxxxxx
```

### Monitoring
```bash
# Get attack logs
jdc --output json waf describe-attack-logs \
  --region-id cn-north-1 \
  --instance-id waf-xxxxxx \
  --domain-id domain-xxxxxx \
  --start-time "2026-06-01T00:00:00Z" \
  --end-time "2026-06-08T00:00:00Z"
```