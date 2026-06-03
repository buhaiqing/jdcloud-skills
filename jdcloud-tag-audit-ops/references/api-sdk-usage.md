# API & SDK Usage

## Prerequisites

```bash
# Install SDK
uv pip install jdcloud_sdk
```

## Python SDK Examples

### Initialize Credential

```python
import os
from jdcloud_sdk.core.credential import Credential

credential = Credential(
    os.environ["JDC_ACCESS_KEY"], 
    os.environ["JDC_SECRET_KEY"]
)
```

### Audit Redis Tags

```python
def audit_redis(region, required_tags):
    from jdcloud_sdk.services.redis.client.RedisClient import RedisClient
    from jdcloud_sdk.services.redis.apis.DescribeCacheInstancesRequest import (
        DescribeCacheInstancesRequest, 
        DescribeCacheInstancesParameters
    )
    
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
```

### Audit VM Tags

```python
def audit_vm(region, required_tags):
    from jdcloud_sdk.services.vm.client.VmClient import VmClient
    from jdcloud_sdk.services.vm.apis.DescribeInstancesRequest import (
        DescribeInstancesRequest, 
        DescribeInstancesParameters
    )
    
    client = VmClient(credential)
    params = DescribeInstancesParameters(regionId=region)
    req = DescribeInstancesRequest(parameters=params)
    resp = client.send(req)
    
    results = []
    for instance in resp.result.get("instances", []):
        existing_tags = [tag["key"] for tag in instance.get("tags", [])]
        missing_tags = [tag for tag in required_tags if tag not in existing_tags]
        if missing_tags:
            results.append({
                "product": "vm",
                "region": region,
                "id": instance["instanceId"],
                "name": instance["name"],
                "missingTags": missing_tags
            })
    return results
```

### Audit CLB Tags

```python
def audit_clb(region, required_tags):
    from jdcloud_sdk.services.clb.client.ClbClient import ClbClient
    from jdcloud_sdk.services.clb.apis.DescribeLoadBalancersRequest import (
        DescribeLoadBalancersRequest, 
        DescribeLoadBalancersParameters
    )
    
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
```

### Audit EIP Tags

```python
def audit_eip(region, required_tags):
    from jdcloud_sdk.services.eip.client.EipClient import EipClient
    from jdcloud_sdk.services.eip.apis.DescribeAddressesRequest import (
        DescribeAddressesRequest, 
        DescribeAddressesParameters
    )
    
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
```

### Multi-Region, Multi-Product Audit

```python
def audit_all(regions, products, required_tags):
    all_results = []
    
    for region in regions:
        if "redis" in products:
            all_results.extend(audit_redis(region, required_tags))
        if "vm" in products:
            all_results.extend(audit_vm(region, required_tags))
        if "clb" in products:
            all_results.extend(audit_clb(region, required_tags))
        if "eip" in products:
            all_results.extend(audit_eip(region, required_tags))
    
    return all_results

# Example usage
regions = ["cn-north-1", "cn-east-2", "cn-south-1"]
products = ["redis", "vm", "clb", "eip"]
required_tags = ["环境", "客户"]

results = audit_all(regions, products, required_tags)
print(f"Found {len(results)} non-compliant resources")
```