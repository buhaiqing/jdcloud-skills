# Resource Audit - JD Cloud Elasticsearch

## Overview

This document covers tag compliance auditing and resource inventory operations for JD Cloud Elasticsearch instances.

## Tag Compliance Audit

### Required Tags

Standard required tags for Elasticsearch resources:

| Tag Key | Description | Example Values |
|---------|-------------|----------------|
| `环境` | Environment type | production, staging, development |
| `客户` | Customer name | internal, customer-name |
| `项目` | Project identifier | project-code |
| `负责人` | Responsible person | employee-id or name |
| `成本中心` | Cost center code | cc-xxx |

### Audit CLI Commands

**Basic Tag Audit:**
```bash
# Setup jdc config
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc
cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = YOUR_ACCESS_KEY
secret_key = YOUR_SECRET_KEY
region_id = cn-north-1
endpoint = es.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF
printf "%s" "default" > /tmp/jdc-home/.jdc/current

# Define required tags
REQUIRED_TAGS='["环境", "客户", "项目", "负责人"]'

# Audit ES tags across regions
for region in cn-north-1 cn-east-2 cn-south-1; do
    echo "=== Elasticsearch - $region ==="
    jdc --output json es describe-instances \
      --region-id $region --page-number 1 --page-size 100 | \
    jq --argjson required_tags "$REQUIRED_TAGS" '
    .result.instances[] |
    . as $instance |
    ($instance.tags // []) | map(.key) | . as $existing |
    [($required_tags[] | select(. as $tag | $existing | contains([$tag]) | not))] |
    select(length > 0) |
    {
        product: "elasticsearch",
        region: $region,
        id: $instance.instanceId,
        name: $instance.instanceName,
        version: $instance.version,
        status: $instance.status,
        missingTags: .
    }'
done
```

### Audit SDK Implementation

```python
import os
import json
from datetime import datetime
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.es.client.EsClient import EsClient
from jdcloud_sdk.services.es.apis.DescribeInstancesRequest import (
    DescribeInstancesRequest, DescribeInstancesParameters
)

class ElasticsearchAuditor:
    def __init__(self):
        credential = Credential(
            os.environ["JDC_ACCESS_KEY"],
            os.environ["JDC_SECRET_KEY"]
        )
        self.credential = credential
        self.required_tags = ["环境", "客户", "项目", "负责人"]
    
    def audit_region(self, region):
        """Audit ES instances in a region."""
        client = EsClient(self.credential, region)
        
        params = DescribeInstancesParameters(regionId=region)
        params.setPageNumber(1)
        params.setPageSize(100)
        req = DescribeInstancesRequest(parameters=params)
        resp = client.send(req)
        
        results = []
        for instance in resp.result.get("instances", []):
            existing_tags = [tag["key"] for tag in instance.get("tags", [])]
            missing_tags = [
                tag for tag in self.required_tags 
                if tag not in existing_tags
            ]
            
            instance_info = {
                "product": "elasticsearch",
                "region": region,
                "id": instance["instanceId"],
                "name": instance["instanceName"],
                "version": instance.get("version", ""),
                "status": instance.get("status", ""),
                "instanceClass": instance.get("instanceClass", ""),
                "existingTags": existing_tags,
                "missingTags": missing_tags,
                "isCompliant": len(missing_tags) == 0
            }
            results.append(instance_info)
        
        return results
    
    def audit_regions(self, regions):
        """Audit multiple regions."""
        all_results = []
        for region in regions:
            try:
                results = self.audit_region(region)
                all_results.extend(results)
            except Exception as e:
                print(f"Error auditing region {region}: {e}")
        return all_results
    
    def generate_report(self, audit_results):
        """Generate audit report."""
        total = len(audit_results)
        compliant = sum(1 for r in audit_results if r["isCompliant"])
        non_compliant = total - compliant
        
        report = {
            "metadata": {
                "generatedAt": datetime.now().isoformat(),
                "requiredTags": self.required_tags,
                "product": "Elasticsearch"
            },
            "summary": {
                "totalInstances": total,
                "compliantCount": compliant,
                "nonCompliantCount": non_compliant,
                "complianceRate": round(compliant / total * 100, 2) if total > 0 else 0
            },
            "nonCompliantInstances": [
                r for r in audit_results if not r["isCompliant"]
            ],
            "allInstances": audit_results
        }
        
        return report

# Usage
auditor = ElasticsearchAuditor()
regions = ["cn-north-1", "cn-east-2", "cn-south-1"]
results = auditor.audit_regions(regions)
report = auditor.generate_report(results)

# Save report
filename = f"es_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(filename, 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print(f"合规率: {report['summary']['complianceRate']}%")
print(f"不合规实例: {report['summary']['nonCompliantCount']}")
```

## Resource Inventory

### Inventory CLI Commands

```bash
#!/bin/bash

REGIONS="cn-north-1 cn-east-2 cn-south-1"
REPORT_FILE="es_inventory_$(date +%Y%m%d_%H%M%S).md"

echo "# Elasticsearch 资源清单" > "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "**生成时间**: $(date '+%Y-%m-%d %H:%M:%S')" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "| 区域 | 实例ID | 实例名称 | 规格 | 版本 | 状态 | 数据节点 | 主节点 | Kibana | 创建时间 | 标签 |" >> "$REPORT_FILE"
echo "|------|--------|----------|------|------|------|----------|--------|--------|----------|------|" >> "$REPORT_FILE"

for region in $REGIONS; do
    jdc --output json es describe-instances \
      --region-id "$region" \
      --page-number 1 \
      --page-size 100 | \
    jq -r --arg region "$region" '
    .result.instances[] |
    (.tags // []) | map("\(.key)=\(.value)") | join(", ") as $tags |
    "| \($region) | \(.instanceId) | \(.instanceName) | \(.instanceClass) | " +
    "\(.version) | \(.status) | \(.dataNode.nodeAmount // "N/A") | " +
    "\(.masterNode.nodeAmount // "N/A") | \(.kibanaNode.nodeClass // "N/A") | " +
    "\(.createTime // "N/A") | \($tags) |"'
done >> "$REPORT_FILE"

echo "报告已生成: $REPORT_FILE"
```

### Inventory SDK Implementation

```python
import os
import json
from datetime import datetime
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.es.client.EsClient import EsClient
from jdcloud_sdk.services.es.apis.DescribeInstancesRequest import (
    DescribeInstancesRequest, DescribeInstancesParameters
)

class ElasticsearchInventory:
    def __init__(self):
        credential = Credential(
            os.environ["JDC_ACCESS_KEY"],
            os.environ["JDC_SECRET_KEY"]
        )
        self.credential = credential
    
    def get_inventory(self, region):
        """Get ES inventory for a region."""
        client = EsClient(self.credential, region)
        
        params = DescribeInstancesParameters(regionId=region)
        params.setPageNumber(1)
        params.setPageSize(100)
        req = DescribeInstancesRequest(parameters=params)
        resp = client.send(req)
        
        resources = []
        for instance in resp.result.get("instances", []):
            resource = {
                "region": region,
                "instanceId": instance["instanceId"],
                "instanceName": instance["instanceName"],
                "instanceClass": instance.get("instanceClass", ""),
                "version": instance.get("version", ""),
                "status": instance.get("status", ""),
                "vpcId": instance.get("vpcId", ""),
                "subnetId": instance.get("subnetId", ""),
                "azId": instance.get("azId", ""),
                "dataNode": {
                    "amount": instance.get("dataNode", {}).get("nodeAmount", 0),
                    "class": instance.get("dataNode", {}).get("nodeClass", ""),
                    "diskType": instance.get("dataNode", {}).get("nodeDiskType", ""),
                    "diskSize": instance.get("dataNode", {}).get("nodeDiskSize", 0)
                },
                "masterNode": {
                    "amount": instance.get("masterNode", {}).get("nodeAmount", 0),
                    "class": instance.get("masterNode", {}).get("nodeClass", "")
                },
                "kibanaNode": {
                    "class": instance.get("kibanaNode", {}).get("nodeClass", "")
                },
                "esUrl": instance.get("esUrl", ""),
                "kibanaUrl": instance.get("kibanaUrl", ""),
                "createTime": instance.get("createTime", ""),
                "tags": instance.get("tags", [])
            }
            resources.append(resource)
        
        return resources
    
    def get_all_inventory(self, regions):
        """Get inventory across multiple regions."""
        inventory = {
            "metadata": {
                "generatedAt": datetime.now().isoformat(),
                "regions": regions
            },
            "resources": [],
            "summary": {
                "totalInstances": 0,
                "byRegion": {},
                "byStatus": {},
                "byVersion": {},
                "totalDataNodes": 0,
                "totalMasterNodes": 0
            }
        }
        
        for region in regions:
            try:
                resources = self.get_inventory(region)
                inventory["resources"].extend(resources)
                
                # Update summary
                inventory["summary"]["byRegion"][region] = len(resources)
                inventory["summary"]["totalInstances"] += len(resources)
                
                for resource in resources:
                    # Status summary
                    status = resource["status"]
                    inventory["summary"]["byStatus"][status] = \
                        inventory["summary"]["byStatus"].get(status, 0) + 1
                    
                    # Version summary
                    version = resource["version"]
                    inventory["summary"]["byVersion"][version] = \
                        inventory["summary"]["byVersion"].get(version, 0) + 1
                    
                    # Node counts
                    inventory["summary"]["totalDataNodes"] += resource["dataNode"]["amount"]
                    inventory["summary"]["totalMasterNodes"] += resource["masterNode"]["amount"]
                    
            except Exception as e:
                print(f"Error getting inventory for region {region}: {e}")
                inventory["summary"]["byRegion"][region] = 0
        
        return inventory
    
    def export_to_json(self, inventory, filename=None):
        """Export inventory to JSON file."""
        if not filename:
            filename = f"es_inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(inventory, f, indent=2, ensure_ascii=False)
        
        return filename

# Usage
inventory_mgr = ElasticsearchInventory()
regions = ["cn-north-1", "cn-east-2", "cn-south-1"]
inventory = inventory_mgr.get_all_inventory(regions)
filename = inventory_mgr.export_to_json(inventory)

print(f"资源清单已保存: {filename}")
print(f"总实例数: {inventory['summary']['totalInstances']}")
print(f"按区域分布: {inventory['summary']['byRegion']}")
print(f"按状态分布: {inventory['summary']['byStatus']}")
```

## DOPS Ticket Integration

### Create Ticket for Non-Compliant Resources

```python
def create_compliance_ticket(audit_results, assignee="xuhao"):
    """Create DOPS ticket for non-compliant ES resources."""
    
    non_compliant = [
        r for r in audit_results 
        if not r.get("isCompliant", True)
    ]
    
    if not non_compliant:
        print("所有 Elasticsearch 实例均合规，无需创建工单")
        return None
    
    # Build ticket content
    summary = f"Elasticsearch标签合规: {len(non_compliant)} 个实例缺失必需标签"
    
    description_lines = [
        "## Elasticsearch 资源标签合规检查",
        "",
        f"**检查时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**不合规实例数**: {len(non_compliant)}",
        "",
        "### 不合规资源列表",
        "",
        "| 区域 | 实例ID | 实例名称 | 版本 | 状态 | 缺失标签 |",
        "|------|--------|----------|------|------|----------|"
    ]
    
    for instance in non_compliant:
        missing = ", ".join(instance.get("missingTags", []))
        description_lines.append(
            f"| {instance['region']} | {instance['id']} | {instance['name']} | "
            f"{instance.get('version', '')} | {instance.get('status', '')} | {missing} |"
        )
    
    description_lines.extend([
        "",
        "### 合规要求",
        "",
        "所有 Elasticsearch 实例必须包含以下标签:",
        "- 环境 (production/staging/development)",
        "- 客户 (客户名称或内部)",
        "- 项目 (项目名称)",
        "- 负责人 (负责人姓名或工号)",
        "",
        "### 建议操作",
        "",
        "1. 登录京东云控制台或使用 CLI 为上述实例补全标签",
        "2. 参考文档: https://docs.jdcloud.com/cn/es/api/modifyinstanceattribute",
        ""
    ])
    
    description = "\n".join(description_lines)
    
    ticket_data = {
        "summary": summary,
        "description": description,
        "operator": "zhoulu",
        "accepter": assignee,
        "labels": "标签合规,资源管理,Elasticsearch"
    }
    
    print("工单数据已准备:")
    print(json.dumps(ticket_data, indent=2, ensure_ascii=False))
    
    return ticket_data

# Usage
# ticket_data = create_compliance_ticket(results, assignee="xuhao")
# If MCP is available:
# result = mcp_call_tool("hdops_mcp", "create_dops_issue", ticket_data)
```
