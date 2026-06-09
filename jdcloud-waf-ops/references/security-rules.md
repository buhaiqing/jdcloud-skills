# WAF Security Rules Reference

## Rule Structure
```json
{
  "ruleName": "descriptive-name",
  "ruleType": "type",
  "matchOp": "match|not_match",
  "matchItems": [...],
  "action": "block|allow|log|captcha|rate_limit",
  "status": 1
}
```

## Rule Types

### IP Blacklist
```json
{
  "ruleType": "ip_blacklist",
  "ipList": ["192.168.1.100", "10.0.0.0/24"],
  "action": "block"
}
```

### IP Whitelist
```json
{
  "ruleType": "ip_whitelist",
  "ipList": ["203.0.113.0/24"],
  "action": "allow"
}
```

### Rate Limiting
```json
{
  "ruleType": "rate_limit",
  "matchItems": [{"field": "url", "operator": "contains", "value": "/api/"}],
  "rateLimit": {
    "threshold": 1000,
    "period": 60,
    "action": "captcha"
  }
}
```

### Geographic Blocking
```json
{
  "ruleType": "geo_blocking",
  "countryCodes": ["CN", "US"],
  "action": "block"
}
```

### URL ACL
```json
{
  "ruleType": "url_acl",
  "matchItems": [{"field": "url", "operator": "match", "value": "/admin/*"}],
  "action": "block"
}
```

### Bot Management
```json
{
  "ruleType": "bot_management",
  "botType": "malicious_scraper",
  "action": "challenge"
}
```

## Match Fields
- `ip` — Client IP address
- `url` — Request URL path
- `host` — Host header
- `user_agent` — User-Agent header
- `referer` — Referer header
- `method` — HTTP method (GET, POST, etc.)
- `header` — Custom header
- `cookie` — Cookie value
- `query_string` — URL query parameters

## Operators
- `match` — Exact match
- `contains` — Substring match
- `prefix` — Starts with
- `suffix` — Ends with
- `regex` — Regular expression
- `gt` / `lt` / `gte` / `lte` — Numeric comparison