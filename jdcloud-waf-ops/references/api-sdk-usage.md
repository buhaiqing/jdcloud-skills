# API & SDK — WAF

## OpenAPI
- Base URL: `https://waf.jdcloud-api.com/v1`
- Protocol: HTTPS only
- Authentication: JD Cloud signature V3

## SDK Operations Map

| Goal | API Operation | SDK Method | Notes |
|------|---------------|------------|-------|
| Create Instance | `CreateInstance` | `createInstance` | Returns instance ID |
| Delete Instance | `DeleteInstance` | `deleteInstance` | Requires no domains |
| Describe Instance | `DescribeInstance` | `describeInstance` | Instance details |
| List Instances | `DescribeInstances` | `describeInstances` | All instances |
| Add Domain | `AddDomain` | `addDomain` | Returns domain ID + CNAME |
| Delete Domain | `DeleteDomain` | `deleteDomain` | Remove protection |
| Describe Domain | `DescribeDomain` | `describeDomain` | Domain config |
| List Domains | `DescribeDomains` | `describeDomains` | By instance |
| Enable Domain | `EnableDomain` | `enableDomain` | Start protection |
| Disable Domain | `DisableDomain` | `disableDomain` | Pause protection |
| Bind Certificate | `BindCert` | `bindCert` | HTTPS setup |
| Unbind Certificate | `UnbindCert` | `unbindCert` | Remove HTTPS |
| Create Rule | `CreateRule` | `createRule` | Security rule |
| Delete Rule | `DeleteRule` | `deleteRule` | Remove rule |
| Update Rule | `UpdateRule` | `updateRule` | Modify rule |
| Describe Rule | `DescribeRule` | `describeRule` | Rule details |
| List Rules | `DescribeRules` | `describeRules` | By domain |
| Enable Bot | `EnableBotManagement` | `enableBotManagement` | Bot protection |
| Get Attack Logs | `DescribeAttackLogs` | `describeAttackLogs` | Security events |
| Get Access Logs | `DescribeAccessLogs` | `describeAccessLogs` | All requests |

## Package Types (verify current)
- `waf.basic` — Entry level, 1000 QPS
- `waf.advanced` — Standard, 5000 QPS
- `waf.enterprise` — High capacity, 20000+ QPS

## Common Request Patterns

### Create Rate Limit Rule
```python
req = CreateRuleRequest(
    regionId="cn-north-1",
    instanceId="waf-xxxx",
    domainId="domain-xxxx",
    ruleSpec={
        "ruleName": "api-throttle",
        "ruleType": "rate_limit",
        "matchOp": "match",
        "matchItems": [
            {"field": "url", "operator": "contains", "value": "/api/"}
        ],
        "rateLimit": {
            "threshold": 100,
            "period": 60,
            "action": "captcha"
        },
        "status": 1
    }
)
```