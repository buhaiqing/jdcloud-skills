# WAF Core Concepts

## WAF Instance
A WAF deployment unit with dedicated resources. Each instance:
- Has its own CNAME domain for DNS configuration
- Supports multiple protected domains
- Has configurable QPS limits based on package
- Can be scaled by upgrading package

## Protected Domain
A domain (or subdomain) protected by WAF. For each domain:
- Configure origin/backend servers
- Set up SSL certificates for HTTPS
- Define security rules
- Traffic flows: User → WAF → Origin

## CNAME Configuration
DNS setup required to route traffic through WAF:
1. Point your domain CNAME to WAF-provided CNAME
2. WAF inspects traffic and forwards to origin
3. Origin responses return through WAF to user

## Security Rule Types

### IP-based Rules
- **IP Whitelist**: Always allow specific IPs
- **IP Blacklist**: Block specific IPs/ranges
- **Geo-blocking**: Block/allow by country

### Rate-based Rules
- **Rate Limiting**: Limit requests per IP/time window
- **CC Protection**: Challenge/block suspicious high-frequency requests

### Content-based Rules
- **SQL Injection**: Detect and block SQLi attempts
- **XSS Protection**: Block cross-site scripting
- **Command Injection**: Block shell command injection
- **Path Traversal**: Block directory traversal attempts

### Bot Management
- **Good Bots**: Whitelist search engines, monitoring
- **Bad Bots**: Block scrapers, credential stuffers
- **Challenge**: Present CAPTCHA for suspicious traffic

## Rule Actions
- **Block**: Reject request (HTTP 403)
- **Allow**: Pass through without inspection
- **Log**: Record but allow (monitoring mode)
- **Challenge**: Present CAPTCHA/JavaScript challenge
- **Rate Limit**: Throttle request rate

## SSL/TLS Modes
- **HTTP Only**: No encryption (not recommended)
- **HTTPS Only**: Encrypt client-to-WAF
- **HTTP + HTTPS**: Support both protocols
- **Force HTTPS**: Redirect HTTP to HTTPS