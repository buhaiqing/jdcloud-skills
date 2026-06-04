# Quick Inspection Code Snippets — JD Cloud Elasticsearch

> **SDK-only.** `jdc` CLI does NOT support the `es` product. All snippets use `jdcloud_sdk.services.es` exclusively.
> Field names verified from real API calls on 2026-06-03.

## Snippet 1: Tag Compliance Audit (All Regions)

Check which ES instances are missing the 【环境】 tag across all regions:

```python
#!/usr/bin/env python3
"""Elasticsearch Tag Compliance Audit — Check missing '环境' tag across all regions."""

import os, json
from dotenv import load_dotenv
load_dotenv()  # Load from .env file

from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.es.client.EsClient import EsClient
from jdcloud_sdk.services.es.apis.DescribeInstancesRequest import DescribeInstancesRequest, DescribeInstancesParameters

credential = Credential(os.environ["JDC_ACCESS_KEY"], os.environ["JDC_SECRET_KEY"])
client = EsClient(credential)

# Valid ES regions (cn-south-2 is NOT supported)
REGIONS = ["cn-north-1", "cn-east-1", "cn-east-2", "cn-south-1"]
REQUIRED_TAG = "环境"

all_instances = []
non_compliant = []

for region in REGIONS:
    try:
        params = DescribeInstancesParameters(regionId=region)
        params.setPageNumber(1)
        params.setPageSize(100)
        req = DescribeInstancesRequest(parameters=params)
        resp = client.send(req)

        # IMPORTANT: instances may be null when empty
        instances = resp.result.get("instances") or []

        for inst in instances:
            tags = inst.get("tags") or []
            existing_keys = [t.get("key", "") for t in tags]

            record = {
                "region": region,
                "instanceId": inst.get("instanceId", ""),
                "instanceName": inst.get("instanceName", ""),
                "instanceVersion": inst.get("instanceVersion", ""),
                "instanceStatus": inst.get("instanceStatus", ""),
                "existingTagKeys": existing_keys,
            }
            all_instances.append(record)

            if REQUIRED_TAG not in existing_keys:
                record["missingTag"] = REQUIRED_TAG
                non_compliant.append(record)

    except Exception as e:
        print(f"[ERROR] {region}: {type(e).__name__}: {str(e)[:200]}")

# Summary
total = len(all_instances)
compliant = total - len(non_compliant)
rate = round(compliant / total * 100, 2) if total > 0 else 0

print(f"\n=== Elasticsearch Tag Compliance Audit ===")
print(f"Total instances: {total}")
print(f"Compliant: {compliant}")
print(f"Non-compliant (missing '{REQUIRED_TAG}'): {len(non_compliant)}")
print(f"Compliance rate: {rate}%")

if non_compliant:
    print(f"\nNon-compliant instances:")
    for item in non_compliant:
        print(f"  [{item['region']}] {item['instanceId']} | {item['instanceName']} | v{item['instanceVersion']} | {item['instanceStatus']} | tags={item['existingTagKeys']}")
```

## Snippet 2: Resource Inventory (All Regions)

Generate a comprehensive inventory of all ES instances:

```python
#!/usr/bin/env python3
"""Elasticsearch Resource Inventory — All regions."""

import os, json
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.es.client.EsClient import EsClient
from jdcloud_sdk.services.es.apis.DescribeInstancesRequest import DescribeInstancesRequest, DescribeInstancesParameters

credential = Credential(os.environ["JDC_ACCESS_KEY"], os.environ["JDC_SECRET_KEY"])
client = EsClient(credential)

REGIONS = ["cn-north-1", "cn-east-1", "cn-east-2", "cn-south-1"]

inventory = {
    "metadata": {"generatedAt": datetime.now().isoformat(), "regions": REGIONS},
    "resources": [],
    "summary": {"totalInstances": 0, "byRegion": {}, "byStatus": {}, "byVersion": {}}
}

for region in REGIONS:
    try:
        params = DescribeInstancesParameters(regionId=region)
        params.setPageNumber(1)
        params.setPageSize(100)
        req = DescribeInstancesRequest(parameters=params)
        resp = client.send(req)

        instances = resp.result.get("instances") or []
        inventory["summary"]["byRegion"][region] = len(instances)
        inventory["summary"]["totalInstances"] += len(instances)

        for inst in instances:
            ic = inst.get("instanceClass", {})
            status = inst.get("instanceStatus", "unknown")
            version = inst.get("instanceVersion", "unknown")

            inventory["summary"]["byStatus"][status] = inventory["summary"]["byStatus"].get(status, 0) + 1
            inventory["summary"]["byVersion"][version] = inventory["summary"]["byVersion"].get(version, 0) + 1

            inventory["resources"].append({
                "region": region,
                "instanceId": inst.get("instanceId", ""),
                "instanceName": inst.get("instanceName", ""),
                "instanceVersion": version,
                "instanceStatus": status,
                "nodeClass": ic.get("nodeClass", ""),
                "nodeCount": ic.get("nodeCount", 0),
                "nodeDiskGB": ic.get("nodeDiskGB", 0),
                "nodeDiskType": ic.get("nodeDiskType", ""),
                "kibana": ic.get("kibana", False),
                "endpoint": inst.get("endpoint", ""),
                "kibanaUrl": inst.get("kibanaUrl", ""),
                "chargeMode": inst.get("charge", {}).get("chargeMode", ""),
                "chargeExpiredTime": inst.get("charge", {}).get("chargeExpiredTime", ""),
                "tags": inst.get("tags", []),
            })
    except Exception as e:
        print(f"[ERROR] {region}: {e}")
        inventory["summary"]["byRegion"][region] = 0

# Save to file
filename = f"es_inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(filename, 'w', encoding='utf-8') as f:
    json.dump(inventory, f, indent=2, ensure_ascii=False)

print(f"Inventory saved: {filename}")
print(f"Total: {inventory['summary']['totalInstances']} instances")
print(f"By region: {inventory['summary']['byRegion']}")
print(f"By status: {inventory['summary']['byStatus']}")
print(f"By version: {inventory['summary']['byVersion']}")
```

## Snippet 3: Expiring Instance Alert

Find ES instances with prepaid billing expiring soon:

```python
#!/usr/bin/env python3
"""Elasticsearch Expiring Instance Alert — Check prepaid instances expiring within N days."""

import os, json
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
load_dotenv()

from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.es.client.EsClient import EsClient
from jdcloud_sdk.services.es.apis.DescribeInstancesRequest import DescribeInstancesRequest, DescribeInstancesParameters

credential = Credential(os.environ["JDC_ACCESS_KEY"], os.environ["JDC_SECRET_KEY"])
client = EsClient(credential)

REGIONS = ["cn-north-1", "cn-east-1", "cn-east-2", "cn-south-1"]
WARN_DAYS = 30  # Alert if expiring within 30 days

expiring = []

for region in REGIONS:
    try:
        params = DescribeInstancesParameters(regionId=region)
        params.setPageNumber(1)
        params.setPageSize(100)
        req = DescribeInstancesRequest(parameters=params)
        resp = client.send(req)

        instances = resp.result.get("instances") or []

        for inst in instances:
            charge = inst.get("charge", {})
            if charge.get("chargeMode") != "prepaid_by_duration":
                continue  # Skip non-prepaid instances

            expired_str = charge.get("chargeExpiredTime", "")
            if not expired_str:
                continue

            # Parse expiry time (e.g., "2026-06-15T15:59:59Z")
            expired_time = datetime.fromisoformat(expired_str.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            days_left = (expired_time - now).days

            if days_left <= WARN_DAYS:
                expiring.append({
                    "region": region,
                    "instanceId": inst.get("instanceId", ""),
                    "instanceName": inst.get("instanceName", ""),
                    "instanceStatus": inst.get("instanceStatus", ""),
                    "chargeExpiredTime": expired_str,
                    "daysLeft": days_left,
                })
    except Exception as e:
        print(f"[ERROR] {region}: {e}")

if expiring:
    expiring.sort(key=lambda x: x["daysLeft"])
    print(f"\n=== Expiring ES Instances (within {WARN_DAYS} days) ===")
    for item in expiring:
        print(f"  [{item['region']}] {item['instanceId']} | {item['instanceName']} | {item['daysLeft']} days left | expires: {item['chargeExpiredTime']}")
else:
    print(f"No ES instances expiring within {WARN_DAYS} days.")
```

## Snippet 4: Audit Report + DOPS Ticket

Generate audit report and create DOPS ticket for non-compliant resources:

```python
#!/usr/bin/env python3
"""Elasticsearch Audit Report + DOPS Ticket Creation."""

import os, json
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.es.client.EsClient import EsClient
from jdcloud_sdk.services.es.apis.DescribeInstancesRequest import DescribeInstancesRequest, DescribeInstancesParameters

credential = Credential(os.environ["JDC_ACCESS_KEY"], os.environ["JDC_SECRET_KEY"])
client = EsClient(credential)

REGIONS = ["cn-north-1", "cn-east-1", "cn-east-2", "cn-south-1"]
REQUIRED_TAGS = ["环境", "客户", "项目", "负责人"]

all_instances = []
non_compliant = []

for region in REGIONS:
    try:
        params = DescribeInstancesParameters(regionId=region)
        params.setPageNumber(1)
        params.setPageSize(100)
        req = DescribeInstancesRequest(parameters=params)
        resp = client.send(req)

        instances = resp.result.get("instances") or []
        for inst in instances:
            tags = inst.get("tags") or []
            existing_keys = [t.get("key", "") for t in tags]
            missing_tags = [t for t in REQUIRED_TAGS if t not in existing_keys]

            record = {
                "region": region,
                "instanceId": inst.get("instanceId", ""),
                "instanceName": inst.get("instanceName", ""),
                "instanceVersion": inst.get("instanceVersion", ""),
                "instanceStatus": inst.get("instanceStatus", ""),
                "existingTagKeys": existing_keys,
                "missingTags": missing_tags,
                "isCompliant": len(missing_tags) == 0,
            }
            all_instances.append(record)
            if missing_tags:
                non_compliant.append(record)
    except Exception as e:
        print(f"[ERROR] {region}: {e}")

# Generate report
total = len(all_instances)
compliant = total - len(non_compliant)
rate = round(compliant / total * 100, 2) if total > 0 else 0

report_lines = [
    "## Elasticsearch 资源标签合规巡检",
    "",
    f"**巡检时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    f"**巡检范围**: 京东云 Elasticsearch 全区域 ({', '.join(REGIONS)})",
    f"**巡检标准**: 必须包含标签 - {', '.join(REQUIRED_TAGS)}",
    "",
    "### 巡检结果",
    "",
    f"- **总实例数**: {total}",
    f"- **合规实例**: {compliant}",
    f"- **不合规实例**: {len(non_compliant)}",
    f"- **合规率**: {rate}%",
    "",
    "### 不合规资源列表",
    "",
    "| 区域 | 实例ID | 实例名称 | 版本 | 状态 | 已有标签 | 缺失标签 |",
    "|------|--------|----------|------|------|----------|----------|",
]

for item in non_compliant:
    missing = ", ".join(item["missingTags"])
    existing = ", ".join(item["existingTagKeys"]) or "无"
    report_lines.append(
        f"| {item['region']} | {item['instanceId']} | {item['instanceName']} | "
        f"{item['instanceVersion']} | {item['instanceStatus']} | {existing} | {missing} |"
    )

report = "\n".join(report_lines)
print(report)

# Create DOPS ticket (if MCP available)
if non_compliant:
    summary = f"{datetime.now().strftime('%Y-%m-%d')}-Elasticsearch标签合规巡检-{len(non_compliant)}个实例缺失标签"
    ticket_data = {
        "summary": summary,
        "description": report,
        "operator": "zhoulu",
        "assignee": "xuhao",
        "labels": "标签合规,主动巡检,Elasticsearch",
        "department": "产研中心-运维部"
    }
    print(f"\n\nDOPS Ticket Data:")
    print(json.dumps(ticket_data, indent=2, ensure_ascii=False))
    # If MCP is available:
    # result = mcp_call_tool("hdops_mcp", "create_dops_issue", ticket_data)
```

## Common Pitfalls

| Pitfall | Wrong | Correct |
|---------|-------|---------|
| Client constructor | `EsClient(credential, "cn-north-1")` | `EsClient(credential)` then set `regionId` in params |
| Null instances | `resp.result["instances"]` (KeyError) | `resp.result.get("instances") or []` |
| Field names | `inst["version"]`, `inst["status"]` | `inst["instanceVersion"]`, `inst["instanceStatus"]` |
| Region list | `["cn-north-1", ..., "cn-south-2"]` | `cn-south-2` is invalid for ES — exclude |
| Tag dict access | `inst["tags"]` (may be None) | `inst.get("tags") or []` |
