# MongoDB Resource Audit

## Overview

Resource auditing for MongoDB instances ensures proper tagging compliance, cost management, and governance across your cloud infrastructure.

## Supported Audit Operations

| Operation | Purpose | Output |
|-----------|---------|--------|
| Tag Compliance Audit | Check if instances have required tags | List of non-compliant resources |
| Resource Inventory | Full asset listing across regions | Complete resource manifest |
| Compliance Report | Detailed compliance analysis | Markdown/JSON report |
| DOPS Ticket Creation | Create tickets for non-compliance | Ticket data |

## Required Tags (Default)

| Tag Key | Description | Example Values |
|---------|-------------|----------------|
| `环境` | Deployment environment | production, staging, development, testing |
| `客户` | Customer or business unit | 客户A, 内部系统, 共享平台 |
| `项目` | Project or application name | CRM系统, 电商平台, 数据分析 |
| `负责人` | Resource owner | 张三, 李四, devops-team |

## Tag Compliance Rules

### Level 1: Critical (Must Have)

- `环境` - Required for all environments
- `客户` - Required for billing attribution

### Level 2: Standard (Should Have)

- `项目` - For project cost tracking
- `负责人` - For operational ownership

### Level 3: Optional (Nice to Have)

- `部门` - Organizational unit
- `成本中心` - Cost allocation
- `过期时间` - Resource lifecycle

## CLI Audit Commands

### Quick Tag Check

```bash
# Check single region
jdc --output json mongodb describe-instances \
  --region-id cn-north-1 | \
jq '.result.instances[] | {id: .instanceId, name: .instanceName, tags: .tags}'
```

### Find Untagged Instances

```bash
# Find instances without any tags
jdc --output json mongodb describe-instances \
  --region-id cn-north-1 | \
jq '.result.instances[] | select((.tags // []) | length == 0) | .instanceId'
```

### Find Missing Specific Tag

```bash
# Find instances missing "环境" tag
REQUIRED_TAG="环境"
jdc --output json mongodb describe-instances \
  --region-id cn-north-1 | \
jq --arg tag "$REQUIRED_TAG" '
.result.instances[] |
select((.tags // []) | map(.key) | contains([$tag]) | not) |
.instanceId'
```

## SDK Audit Examples

### Complete Tag Audit

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.mongodb.client.MongodbClient import MongodbClient
from jdcloud_sdk.services.mongodb.apis.DescribeInstancesRequest import DescribeInstancesRequest, DescribeInstancesParameters

def full_tag_audit(regions, required_tags):
    """Perform complete tag compliance audit across regions."""
    credential = Credential(
        os.environ["JDC_ACCESS_KEY"],
        os.environ["JDC_SECRET_KEY"]
    )
    
    results = {
        "summary": {
            "totalRegions": len(regions),
            "totalInstances": 0,
            "compliant": 0,
            "nonCompliant": 0
        },
        "byRegion": {},
        "nonCompliantDetails": []
    }
    
    for region in regions:
        client = MongodbClient(credential, region)
        params = DescribeInstancesParameters(regionId=region)
        params.setPageNumber(1)
        params.setPageSize(100)
        req = DescribeInstancesRequest(parameters=params)
        
        try:
            resp = client.send(req)
            instances = resp.result.get("instances", [])
            
            region_compliant = 0
            region_non_compliant = 0
            
            for instance in instances:
                existing_tags = {tag["key"]: tag["value"] for tag in instance.get("tags", [])}
                missing_tags = [tag for tag in required_tags if tag not in existing_tags]
                
                if missing_tags:
                    region_non_compliant += 1
                    results["nonCompliantDetails"].append({
                        "region": region,
                        "instanceId": instance["instanceId"],
                        "instanceName": instance["instanceName"],
                        "missingTags": missing_tags,
                        "existingTags": list(existing_tags.keys())
                    })
                else:
                    region_compliant += 1
            
            results["byRegion"][region] = {
                "total": len(instances),
                "compliant": region_compliant,
                "nonCompliant": region_non_compliant
            }
            
            results["summary"]["totalInstances"] += len(instances)
            results["summary"]["compliant"] += region_compliant
            results["summary"]["nonCompliant"] += region_non_compliant
            
        except Exception as e:
            results["byRegion"][region] = {"error": str(e)}
    
    # Calculate compliance rate
    total = results["summary"]["totalInstances"]
    compliant = results["summary"]["compliant"]
    results["summary"]["complianceRate"] = round(compliant / total * 100, 2) if total > 0 else 0
    
    return results

# Run audit
regions = ["cn-north-1", "cn-east-2", "cn-south-1"]
required_tags = ["环境", "客户", "项目", "负责人"]

audit_results = full_tag_audit(regions, required_tags)

# Print summary
print(f"总实例数: {audit_results['summary']['totalInstances']}")
print(f"合规实例: {audit_results['summary']['compliant']}")
print(f"不合规实例: {audit_results['summary']['nonCompliant']}")
print(f"合规率: {audit_results['summary']['complianceRate']}%")

if audit_results['nonCompliantDetails']:
    print("\n不合规实例:")
    for item in audit_results['nonCompliantDetails']:
        print(f"  - {item['instanceName']} ({item['instanceId']}): 缺失 {', '.join(item['missingTags'])}")
```

## Audit Report Formats

### JSON Report Structure

```json
{
  "metadata": {
    "generatedAt": "2026-06-03T12:00:00Z",
    "regions": ["cn-north-1", "cn-east-2"],
    "requiredTags": ["环境", "客户", "项目", "负责人"],
    "product": "MongoDB"
  },
  "summary": {
    "totalInstances": 10,
    "compliantCount": 7,
    "nonCompliantCount": 3,
    "complianceRate": 70.0
  },
  "byRegion": {
    "cn-north-1": {
      "total": 6,
      "compliant": 4,
      "nonCompliant": 2
    },
    "cn-east-2": {
      "total": 4,
      "compliant": 3,
      "nonCompliant": 1
    }
  },
  "byStatus": {
    "running": 8,
    "creating": 1,
    "stopped": 1
  },
  "nonCompliantInstances": [
    {
      "region": "cn-north-1",
      "id": "mongo-abc123",
      "name": "prod-db-01",
      "engine": "MongoDB",
      "engineVersion": "4.4",
      "status": "running",
      "missingTags": ["客户", "负责人"],
      "existingTags": ["环境", "项目"]
    }
  ]
}
```

### Markdown Report Example

```markdown
# MongoDB 资源审计报告

**生成时间**: 2026-06-03 12:00:00
**审计区域**: cn-north-1, cn-east-2, cn-south-1
**审计标准**: 必须包含以下标签 - ["环境", "客户", "项目", "负责人"]

## 摘要

- **总实例数**: 10
- **合规实例**: 7
- **不合规实例**: 3
- **合规率**: 70.0%

## 按区域分布

| 区域 | 总实例 | 合规 | 不合规 | 合规率 |
|------|--------|------|--------|--------|
| cn-north-1 | 6 | 4 | 2 | 66.7% |
| cn-east-2 | 4 | 3 | 1 | 75.0% |

## 不合规资源列表

| 区域 | 实例ID | 实例名称 | 版本 | 状态 | 缺失标签 |
|------|--------|----------|------|------|----------|
| cn-north-1 | mongo-abc123 | prod-db-01 | 4.4 | running | 客户, 负责人 |
| cn-north-1 | mongo-def456 | test-db-01 | 5.0 | running | 环境, 客户 |
| cn-east-2 | mongo-ghi789 | dev-db-01 | 4.4 | running | 项目, 负责人 |

## 建议操作

1. 登录京东云控制台或使用 CLI 为上述实例补全标签
2. 参考文档: https://docs.jdcloud.com/cn/mongodb/api/modifyinstanceattribute
```

## Resource Inventory

### Complete Inventory Fields

| Field | Description | Example |
|-------|-------------|---------|
| `instanceId` | Instance identifier | mongo-abc123def |
| `instanceName` | Human-readable name | production-mongodb |
| `instanceClass` | Instance specification | mongodb.s1.medium |
| `engineVersion` | MongoDB version | 4.4 |
| `status` | Current status | running |
| `region` | Deployment region | cn-north-1 |
| `vpcId` | VPC identifier | vpc-abc123 |
| `subnetId` | Subnet identifier | subnet-def456 |
| `azId` | Availability zone | cn-north-1a |
| `storageType` | Storage type | local_ssd |
| `storageSize` | Storage size (GB) | 50 |
| `connectionDomain` | Connection endpoint | mongo-abc123.mongo.jdcloud.com |
| `port` | Connection port | 27017 |
| `createTime` | Creation timestamp | 2026-06-01T10:00:00Z |
| `chargeMode` | Billing mode | postpaid |
| `tags` | Resource tags | [{"key": "环境", "value": "production"}] |

### Cost Analysis

```python
def analyze_cost_by_tag(inventory, tag_key):
    """Analyze resource distribution by tag value."""
    by_tag_value = {}
    
    for resource in inventory["resources"]:
        tags = {tag["key"]: tag["value"] for tag in resource.get("tags", [])}
        tag_value = tags.get(tag_key, "untagged")
        
        if tag_value not in by_tag_value:
            by_tag_value[tag_value] = {
                "count": 0,
                "storageSize": 0,
                "instanceClasses": []
            }
        
        by_tag_value[tag_value]["count"] += 1
        by_tag_value[tag_value]["storageSize"] += resource.get("storageSize", 0)
        by_tag_value[tag_value]["instanceClasses"].append(resource.get("instanceClass"))
    
    return by_tag_value

# Example: Analyze by environment
# cost_analysis = analyze_cost_by_tag(inventory, "环境")
# print(cost_analysis)
```

## Automation Workflows

### Scheduled Audit

```bash
#!/bin/bash
# Run daily audit and send notification

REPORT_FILE="mongodb_audit_$(date +%Y%m%d).md"

# Generate report
./generate_mongodb_audit_report.sh > "$REPORT_FILE"

# Check compliance rate
COMPLIANCE_RATE=$(grep "合规率" "$REPORT_FILE" | grep -oP '\d+\.?\d*')

if (( $(echo "$COMPLIANCE_RATE < 90" | bc -l) )); then
    # Send alert (example with webhook)
    curl -X POST "$WEBHOOK_URL" \
      -H "Content-Type: application/json" \
      -d "{\"text\": \"MongoDB tag compliance below 90%: $COMPLIANCE_RATE%\"}"
fi
```

### Auto-Tagging (Advanced)

```python
def auto_tag_by_naming_convention(instance):
    """Auto-assign tags based on instance name patterns."""
    name = instance["instanceName"].lower()
    tags_to_add = []
    
    # Environment detection
    if "prod" in name:
        tags_to_add.append({"key": "环境", "value": "production"})
    elif "test" in name or "dev" in name:
        tags_to_add.append({"key": "环境", "value": "development"})
    elif "staging" in name or "stg" in name:
        tags_to_add.append({"key": "环境", "value": "staging"})
    
    # Add more patterns as needed
    
    return tags_to_add
```

## Best Practices

1. **Tag at Creation**: Always include required tags when creating new instances
2. **Regular Audits**: Run weekly or monthly compliance audits
3. **Auto-Remediation**: Consider automating tag additions for common patterns
4. **Policy Enforcement**: Use IAM policies to enforce tagging requirements
5. **Cost Allocation**: Use tags for accurate cost tracking and chargeback

## Integration with DOPS

When creating DOPS tickets for non-compliance:

- **Summary**: Clear description of the issue
- **Priority**: Based on compliance rate (e.g., < 50% = High)
- **Assignee**: Resource owner or infrastructure team
- **Labels**: Include "标签合规", "MongoDB", "资源管理"
- **Due Date**: Set reasonable remediation timeline

## References

- [JD Cloud MongoDB API](https://docs.jdcloud.com/cn/mongodb/api/overview)
- [Tag Management Best Practices](https://docs.jdcloud.com/cn/tags/best-practices)
