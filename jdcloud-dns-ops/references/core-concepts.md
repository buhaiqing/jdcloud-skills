# Core Concepts — JD Cloud DNS (Cloud DNS Service)

## Architecture Overview

JD Cloud DNS (云解析) is a high-availability, scalable DNS hosting service that provides domain name resolution with intelligent routing, health monitoring, and traffic analysis.

### Key Components

| Component | Description |
|-----------|-------------|
| **Domain (主域名)** | A registered domain name hosted on JD Cloud DNS (e.g., `example.com`) |
| **Resource Record (解析记录)** | A DNS record mapping a hostname to a value (A, AAAA, CNAME, MX, TXT, SRV, NS) |
| **DNS Line (解析线路)** | Intelligent routing rules for geo-aware or ISP-aware resolution |
| **Monitor (监控)** | Website health monitoring for subdomains with alarm capabilities |
| **View Tree (基础解析线路)** | Built-in DNS resolution lines (default, ISP-specific, regional) |

## DNS Record Types

| Type | Description | Value Format | Example |
|------|-------------|--------------|---------|
| **A** | IPv4 address | `x.x.x.x` | `192.168.1.1` |
| **AAAA** | IPv6 address | IPv6 format | `2001:db8::1` |
| **CNAME** | Canonical name (alias) | FQDN | `www.example.com.` |
| **MX** | Mail exchange | `priority host` | `10 mail.example.com.` |
| **TXT** | Text record | Free text | `"v=spf1 include:_spf.example.com ~all"` |
| **SRV** | Service locator | `priority weight port target` | `10 5 5060 sip.example.com.` |
| **NS** | Name server | FQDN | `ns1.jdcloud.com.` |

> **Critical:** CNAME at zone apex (`hostRecord="@", type="CNAME"`) violates RFC and is **forbidden**. Use A/AAAA records or ALIAS/ANAME (if supported) instead.

## DNS Packages

| Pack ID | Name | Description |
|---------|------|-------------|
| 0 | Free (免费版) | Basic DNS resolution, limited features |
| 1 | Enterprise (企业版) | Advanced features, higher SLA |
| 2 | Advanced (高级版) | Premium features, highest limits |

## DNS Lines (解析线路)

### Built-in Lines

| Category | Examples |
|----------|----------|
| Default | 默认 |
| ISP | 电信, 联通, 移动, 教育网 |
| Region | 华北, 华东, 华南, 西南 |

### Custom Lines (User Views)

Users can create custom DNS lines with specific IP segments for fine-grained geo-routing.

## DNS Monitoring

Website monitoring checks subdomain availability and triggers alarms:

- **Monitor Types**: HTTP/HTTPS availability checks
- **Monitor Targets**: Specific monitoring endpoints
- **Alarm**: Configurable alarm notifications
- **Status Operations**: Start, stop, delete monitors

## Limits and Quotas

| Resource | Default Limit | Adjustable |
|----------|---------------|------------|
| Domains per Account | Varies by package | Yes |
| Resource Records per Domain | Varies by package | Yes |
| Custom DNS Lines per Domain | Varies by package | Yes |
| Monitors per Domain | Varies by package | Yes |

## Regions

DNS is a **global service**. The `region-id` parameter is typically `cn-north-1` but the service is region-agnostic for most operations.

## Security Considerations

1. **Access Control**: IAM policies for DNS management
2. **Record Integrity**: Validate record values before creation
3. **DNSSEC**: Consider enabling for critical domains
4. **Audit Logging**: Use action log for change tracking

## Integration with Other Services

| Service | Integration |
|---------|-------------|
| **CLB** | Point A/CNAME records to load balancer VIP |
| **CDN** | Point CNAME records to CDN domain |
| **VM** | Point A records to VM public IP |
| **SSL Certificate** | Coordinate cert renewal with DNS validation |
| **CloudMonitor** | DNS monitoring metrics and alarms |

## Pricing Model

- **Free Package**: Basic DNS resolution at no cost
- **Paid Packages**: Enterprise/Advanced with additional features, higher limits, and SLA
