---
name: jdcloud-tag-audit-ops
description: >-
  Use this skill for JD Cloud tag compliance auditing across multiple products and regions.
  Check resource tags for compliance, generate audit reports, and create DOPS tickets for non-compliant resources.
  Apply when the user mentions tag audit, 标签合规, compliance check, or asks about resource tagging across JD Cloud.
license: MIT
compatibility: >-
  Official JD Cloud SDK (Python 3.10+), valid API credentials, network
  access to JD Cloud endpoints, and official JD Cloud CLI (`jdc`).
metadata:
  author: jdcloud
  version: "1.2.0"
  last_updated: "2026-06-03"
  runtime: Harness AI Agent
  api_profile: "JD Cloud Multi-Product API"
  cli_applicability: jdc-first-with-fallback
  cli_version_locked: "1.2.12"
  sdk_version_locked: ">=1.6.26"
  environment:
    - JDC_ACCESS_KEY
    - JDC_SECRET_KEY
    - JDC_REGION
---

> This skill follows the [Agent Skill OpenSpec](https://agentskills.io/specification).

# JD Cloud Tag Audit Operations Skill

## Overview

JD Cloud Tag Audit (`jdcloud-tag-audit-ops`) is a unified skill for auditing resource tags across multiple JD Cloud products and regions. It provides:
- Cross-product tag compliance checking (Redis, VM, RDS, CLB, EIP, MongoDB, Elasticsearch)
- Multi-region scanning capability
- Automated audit report generation
- DOPS ticket creation for non-compliant resources

## Supported Products

| Product | CLI Command | JSON Path | Instance ID Field | Name Field | Engine Field |
|---------|-------------|-----------|------------------|------------|--------------|
| Redis | `redis describe-cache-instances` | `$.result.cacheInstances[]` | `cacheInstanceId` | `cacheInstanceName` | N/A |
| VM | `vm describe-instances` | `$.result.instances[]` | `instanceId` | `name` | N/A |
| RDS MySQL | `rds describe-instances` | `$.result.dbInstances[]` | `instanceId` | `instanceName` | `engine` |
| RDS PostgreSQL | `rds describe-instances` | `$.result.dbInstances[]` | `instanceId` | `instanceName` | `engine` |
| MongoDB | `mongodb describe-instances` | `$.result.instances[]` | `instanceId` | `instanceName` | `engine` |
| Elasticsearch | `es describe-instances` (SDK-only) | `$.result.instances[]` | `instanceId` | `instanceName` | N/A |
| CLB | `clb describe-load-balancers` | `$.result.loadBalancers[]` | `loadBalancerId` | `loadBalancerName` | N/A |
| EIP | `eip describe-addresses` | `$.result.addresses[]` | `addressId` | `name` | N/A |

## Supported Regions

- cn-north-1 (华北-北京)
- cn-east-1 (华东-青岛)
- cn-east-2 (华东-上海)
- cn-south-1 (华南-广州)
- cn-south-2 (华南-深圳)

## Trigger & Scope

### SHOULD Use This Skill When
- User mentions "tag audit", "标签合规", "compliance check"
- User wants to check tags across multiple products/regions
- User needs to generate tag compliance reports
- User wants to create DOPS tickets for non-compliant resources

### SHOULD NOT Use This Skill When
- Task is about modifying individual resource tags → delegate to specific product skills
- Task is about IAM/permissions → delegate to jdcloud-iam-ops

## Variable Convention

| Placeholder | Meaning | Agent Action |
|-------------|---------|--------------|
| `{{env.JDC_ACCESS_KEY}}` | From runtime environment | NEVER ask the user |
| `{{env.JDC_SECRET_KEY}}` | From runtime environment | NEVER ask the user |
| `{{user.regions}}` | User-supplied regions list | Use all available if unset |
| `{{user.products}}` | User-supplied products list | Use all supported if unset |
| `{{user.required_tags}}` | Required tag keys | Default: ["环境", "客户"] |
| `{{output.audit_result}}` | Audit results JSON | Parsed from CLI/API response |

## Execution Flows

### Operation: Audit Tag Compliance

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| Credentials | Check ~/.jdc/config exists | Valid credentials | HALT; user configures |
| Available Regions | Query describe-regions | List of available regions | Use default regions |

#### Execution (CLI)

```bash
# Setup jdc config for sandbox
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc
cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = {{env.JDC_ACCESS_KEY}}
secret_key = {{env.JDC_SECRET_KEY}}
region_id = cn-north-1
scheme = https
timeout = 20
CONFIGEOF
printf "%s" "default" > /tmp/jdc-home/.jdc/current

# Audit Redis tags across regions
for region in cn-north-1 cn-east-2 cn-south-1; do
    echo "=== Redis - $region ==="
    jdc --output json redis describe-cache-instances \
      --region-id $region --page-number 1 --page-size 100 | \
    jq '.result.cacheInstances[] | 
        . as $instance |
        ($instance.tags // []) | map(.key) | . as $existing |
        [($required_tags[] | select(. as $tag | $existing | contains([$tag]) | not))] |
        select(length > 0) |
        {
            product: "redis",
            region: "'"$region"'",
            id: $instance.cacheInstanceId,
            name: $instance.cacheInstanceName,
            missingTags: .
        }'
done

# Audit CLB tags across regions
for region in cn-north-1 cn-east-2 cn-south-1; do
    echo "=== CLB - $region ==="
    jdc --output json clb describe-load-balancers \
      --region-id $region --page-number 1 --page-size 100 | \
    jq '.result.loadBalancers[] | 
        . as $instance |
        ($instance.tags // []) | map(.key) | . as $existing |
        [($required_tags[] | select(. as $tag | $existing | contains([$tag]) | not))] |
        select(length > 0) |
        {
            product: "clb",
            region: "'"$region"'",
            id: $instance.loadBalancerId,
            name: $instance.loadBalancerName,
            missingTags: .
        }'
done

# Audit EIP tags across regions
for region in cn-north-1 cn-east-2 cn-south-1; do
    echo "=== EIP - $region ==="
    jdc --output json eip describe-addresses \
      --region-id $region --page-number 1 --page-size 100 | \
    jq '.result.addresses[] | 
        . as $instance |
        ($instance.tags // []) | map(.key) | . as $existing |
        [($required_tags[] | select(. as $tag | $existing | contains([$tag]) | not))] |
        select(length > 0) |
        {
            product: "eip",
            region: "'"$region"'",
            id: $instance.addressId,
            name: ($instance.name // "N/A"),
            missingTags: .
        }'
done

# Audit RDS MySQL tags across regions
for region in cn-north-1 cn-east-2 cn-south-1; do
    echo "=== RDS MySQL - $region ==="
    jdc --output json rds describe-instances \
      --region-id $region --page-number 1 --page-size 100 | \
    jq '.result.dbInstances[] | 
        select(.engine == "MySQL") |
        . as $instance |
        ($instance.tags // []) | map(.key) | . as $existing |
        [($required_tags[] | select(. as $tag | $existing | contains([$tag]) | not))] |
        select(length > 0) |
        {
            product: "rds-mysql",
            region: "'"$region"'",
            id: $instance.instanceId,
            name: $instance.instanceName,
            engine: $instance.engine,
            missingTags: .
        }'
done

# Audit RDS PostgreSQL tags across regions
for region in cn-north-1 cn-east-2 cn-south-1; do
    echo "=== RDS PostgreSQL - $region ==="
    jdc --output json rds describe-instances \
      --region-id $region --page-number 1 --page-size 100 | \
    jq '.result.dbInstances[] | 
        select(.engine == "PostgreSQL") |
        . as $instance |
        ($instance.tags // []) | map(.key) | . as $existing |
        [($required_tags[] | select(. as $tag | $existing | contains([$tag]) | not))] |
        select(length > 0) |
        {
            product: "rds-postgresql",
            region: "'"$region"'",
            id: $instance.instanceId,
            name: $instance.instanceName,
            engine: $instance.engine,
            missingTags: .
        }'
done

# Audit MongoDB tags across regions
for region in cn-north-1 cn-east-2 cn-south-1; do
    echo "=== MongoDB - $region ==="
    jdc --output json mongodb describe-instances \
      --region-id $region --page-number 1 --page-size 100 | \
    jq '.result.instances[] | 
        . as $instance |
        ($instance.tags // []) | map(.key) | . as $existing |
        [($required_tags[] | select(. as $tag | $existing | contains([$tag]) | not))] |
        select(length > 0) |
        {
            product: "mongodb",
            region: "'"$region"'",
            id: $instance.instanceId,
            name: $instance.instanceName,
            engine: $instance.engine,
            engineVersion: $instance.engineVersion,
            missingTags: .
        }'
done

# Audit Elasticsearch tags across regions (SDK-only — jdc CLI does NOT support 'es')
# See SDK Fallback section below for Elasticsearch audit code
```

#### Execution (SDK Fallback)

```python
import os
from jdcloud_sdk.core.credential import Credential

credential = Credential(os.environ["JDC_ACCESS_KEY"], os.environ["JDC_SECRET_KEY"])

# Audit function for Redis
def audit_redis_tags(region, required_tags):
    from jdcloud_sdk.services.redis.client.RedisClient import RedisClient
    from jdcloud_sdk.services.redis.apis.DescribeCacheInstancesRequest import DescribeCacheInstancesRequest, DescribeCacheInstancesParameters
    
    client = RedisClient(credential)
    params = DescribeCacheInstancesParameters(regionId=region)
    req = DescribeCacheInstancesRequest(parameters=params)
    resp = client.send(req)
    
    results = []
    for instance in resp.result.get("cacheInstances", []):
        existing_tags = [tag["key"] for tag in instance.get("tags", [])]
        missing_tags = [tag for tag in required_tags if tag not in existing_tags]
        if missing_tags:
            results.append({
                "product": "redis",
                "region": region,
                "id": instance["cacheInstanceId"],
                "name": instance["cacheInstanceName"],
                "missingTags": missing_tags
            })
    return results

# Audit function for CLB
def audit_clb_tags(region, required_tags):
    from jdcloud_sdk.services.clb.client.ClbClient import ClbClient
    from jdcloud_sdk.services.clb.apis.DescribeLoadBalancersRequest import DescribeLoadBalancersRequest, DescribeLoadBalancersParameters
    
    client = ClbClient(credential)
    params = DescribeLoadBalancersParameters(regionId=region)
    req = DescribeLoadBalancersRequest(parameters=params)
    resp = client.send(req)
    
    results = []
    for instance in resp.result.get("loadBalancers", []):
        existing_tags = [tag["key"] for tag in instance.get("tags", [])]
        missing_tags = [tag for tag in required_tags if tag not in existing_tags]
        if missing_tags:
            results.append({
                "product": "clb",
                "region": region,
                "id": instance["loadBalancerId"],
                "name": instance["loadBalancerName"],
                "missingTags": missing_tags
            })
    return results

# Audit function for EIP
def audit_eip_tags(region, required_tags):
    from jdcloud_sdk.services.eip.client.EipClient import EipClient
    from jdcloud_sdk.services.eip.apis.DescribeAddressesRequest import DescribeAddressesRequest, DescribeAddressesParameters
    
    client = EipClient(credential)
    params = DescribeAddressesParameters(regionId=region)
    req = DescribeAddressesRequest(parameters=params)
    resp = client.send(req)
    
    results = []
    for instance in resp.result.get("addresses", []):
        existing_tags = [tag["key"] for tag in instance.get("tags", [])]
        missing_tags = [tag for tag in required_tags if tag not in existing_tags]
        if missing_tags:
            results.append({
                "product": "eip",
                "region": region,
                "id": instance["addressId"],
                "name": instance.get("name", "N/A"),
                "missingTags": missing_tags
            })
    return results

# Audit function for RDS MySQL
def audit_rds_mysql_tags(region, required_tags):
    from jdcloud_sdk.services.rds.client.RdsClient import RdsClient
    from jdcloud_sdk.services.rds.apis.DescribeInstancesRequest import DescribeInstancesRequest, DescribeInstancesParameters
    
    client = RdsClient(credential)
    params = DescribeInstancesParameters(regionId=region)
    req = DescribeInstancesRequest(parameters=params)
    resp = client.send(req)
    
    results = []
    for instance in resp.result.get("dbInstances", []):
        if instance.get("engine") != "MySQL":
            continue
        existing_tags = [tag["key"] for tag in instance.get("tags", [])]
        missing_tags = [tag for tag in required_tags if tag not in existing_tags]
        if missing_tags:
            results.append({
                "product": "rds-mysql",
                "region": region,
                "id": instance["instanceId"],
                "name": instance["instanceName"],
                "engine": instance["engine"],
                "missingTags": missing_tags
            })
    return results

# Audit function for RDS PostgreSQL
def audit_rds_postgresql_tags(region, required_tags):
    from jdcloud_sdk.services.rds.client.RdsClient import RdsClient
    from jdcloud_sdk.services.rds.apis.DescribeInstancesRequest import DescribeInstancesRequest, DescribeInstancesParameters
    
    client = RdsClient(credential)
    params = DescribeInstancesParameters(regionId=region)
    req = DescribeInstancesRequest(parameters=params)
    resp = client.send(req)
    
    results = []
    for instance in resp.result.get("dbInstances", []):
        if instance.get("engine") != "PostgreSQL":
            continue
        existing_tags = [tag["key"] for tag in instance.get("tags", [])]
        missing_tags = [tag for tag in required_tags if tag not in existing_tags]
        if missing_tags:
            results.append({
                "product": "rds-postgresql",
                "region": region,
                "id": instance["instanceId"],
                "name": instance["instanceName"],
                "engine": instance["engine"],
                "missingTags": missing_tags
            })
    return results

# Audit function for MongoDB
def audit_mongodb_tags(region, required_tags):
    from jdcloud_sdk.services.mongodb.client.MongodbClient import MongodbClient
    from jdcloud_sdk.services.mongodb.apis.DescribeInstancesRequest import DescribeInstancesRequest, DescribeInstancesParameters
    
    client = MongodbClient(credential)
    params = DescribeInstancesParameters(regionId=region)
    req = DescribeInstancesRequest(parameters=params)
    resp = client.send(req)
    
    results = []
    for instance in resp.result.get("instances", []):
        existing_tags = [tag["key"] for tag in instance.get("tags", [])]
        missing_tags = [tag for tag in required_tags if tag not in existing_tags]
        if missing_tags:
            results.append({
                "product": "mongodb",
                "region": region,
                "id": instance["instanceId"],
                "name": instance["instanceName"],
                "engine": instance.get("engine", "MongoDB"),
                "engineVersion": instance.get("engineVersion", ""),
                "missingTags": missing_tags
            })
    return results

# Audit function for Elasticsearch (SDK-only — jdc CLI does NOT support 'es')
def audit_elasticsearch_tags(region, required_tags):
    """Note: jdc CLI does NOT support 'es' product. Must use SDK only.
    Key field names from actual API: instanceVersion, instanceStatus (NOT version/status).
    Response instances may be null when empty — use .get("instances") or [].
    Valid ES regions: cn-north-1, cn-east-1, cn-east-2, cn-south-1 (cn-south-2 is invalid).
    """
    from jdcloud_sdk.services.es.client.EsClient import EsClient
    from jdcloud_sdk.services.es.apis.DescribeInstancesRequest import DescribeInstancesRequest, DescribeInstancesParameters
    
    # IMPORTANT: EsClient(credential) — NO region as second arg
    client = EsClient(credential)
    params = DescribeInstancesParameters(regionId=region)
    params.setPageNumber(1)
    params.setPageSize(100)
    req = DescribeInstancesRequest(parameters=params)
    resp = client.send(req)
    
    # IMPORTANT: instances may be null when empty
    instances = resp.result.get("instances") or []
    
    results = []
    for instance in instances:
        existing_tags = [tag["key"] for tag in instance.get("tags", []) or []]
        missing_tags = [tag for tag in required_tags if tag not in existing_tags]
        if missing_tags:
            results.append({
                "product": "elasticsearch",
                "region": region,
                "id": instance["instanceId"],
                "name": instance["instanceName"],
                "version": instance.get("instanceVersion", ""),  # NOT "version"
                "status": instance.get("instanceStatus", ""),    # NOT "status"
                "missingTags": missing_tags
            })
    return results
```

### Operation: Generate Audit Report

```bash
# Generate summary report
echo "## Tag Compliance Audit Report"
echo "### Summary"
echo "- Total resources scanned: $total_count"
echo "- Non-compliant resources: $non_compliant_count"
echo "- Compliance rate: $compliance_rate%"
echo ""
echo "### Non-compliant Resources by Product"
echo "| Product | Count |"
echo "|---------|-------|"
echo "| Redis | $redis_count |"
echo "| VM | $vm_count |"
echo "| RDS MySQL | $rds_mysql_count |"
echo "| RDS PostgreSQL | $rds_postgresql_count |"
echo "| MongoDB | $mongodb_count |"
echo "| Elasticsearch | $es_count |"
echo "| CLB | $clb_count |"
echo "| EIP | $eip_count |"
```

### Operation: Create DOPS Ticket for Non-Compliant Resources

```python
# Example: Create DOPS ticket via MCP
from mcp import run_mcp

ticket_summary = f"Tag Compliance: {non_compliant_count} resources missing required tags"
ticket_description = f"## Non-compliant Resources\n\n{audit_table}"

result = run_mcp(
    server_name="mcp_hdops_mcp",
    tool_name="create_dops_issue",
    args={
        "summary": ticket_summary,
        "description": ticket_description,
        "operator": "zhoulu",
        "accepter": "xuhao",
        "labels": "标签合规,资源管理"
    }
)
```

## Prerequisites

> **Python 3.10 is REQUIRED, NOT 3.12.** `jdcloud_cli==1.2.12` uses `SafeConfigParser` which was removed in Python 3.12. Always use `uv venv --python 3.10`. If Python 3.10 is unavailable, install it via `brew install python@3.10` (macOS) or `uv python install 3.10`.

```bash
# Install dependencies
uv venv --python 3.10
source .venv/bin/activate
uv pip install jdcloud_cli jdcloud_sdk
```

## Reference Directory

- [Core Concepts](references/core-concepts.md)
- [CLI Usage](references/cli-usage.md)
- [API & SDK Usage](references/api-sdk-usage.md)
- [Examples](references/examples.md)

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.4.0 | 2026-06-03 | Added Elasticsearch tag audit support |
| 1.3.0 | 2026-06-03 | Added MongoDB tag audit support |
| 1.2.0 | 2026-06-03 | Added RDS MySQL and PostgreSQL tag audit support |
| 1.1.0 | 2026-06-03 | Added CLB and EIP support |
| 1.0.0 | 2026-06-03 | Initial version with Redis, VM, RDS support |

## License

MIT License - See LICENSE file for details