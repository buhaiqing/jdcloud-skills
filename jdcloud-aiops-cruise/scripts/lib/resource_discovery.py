"""
jdcloud-aiops-cruise / lib / resource_discovery.py
=================================================
Resource discovery and topology builder.

Phase 1 of the aiops-cruise process:
1. Scans all resources for a customer (by tag) across all regions
2. Classifies deployment mode (K8s vs traditional) with confidence scores
3. Builds VPC → subnet → resource topology graph
4. Flags unclassified resources for human confirmation
"""

import sys
from pathlib import Path
_scripts_dir = Path(__file__).parent.parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))
from lib.jdc_client import JdcClient, filter_by_tag, tag_dict  # noqa: E402

K8S_CLUSTER_TAG = "kubernetes.jdcloud.com/cluster_id"
K8S_CREATED_TAG = "kubernetes.jdcloud.com/created_by"

# All regions to scan
ALL_REGIONS = ["cn-north-1", "cn-east-2", "cn-south-1", "cn-east-1"]

# Resource type config: (raw_key, list_method_name, vpc_id_field, name_field, id_field)
# list_method_name maps to client.list_<name>()
_RESOURCE_TYPES = [
    ("vms", "vms", "vpcId", "instanceName", "instanceId"),
    ("lbs", "lbs", "vpcId", "loadBalancerName", "loadBalancerId"),
    ("redis", "redis", "vpcId", "cacheInstanceName", "cacheInstanceId"),
    ("mongodb", "mongodb", "vpcId", "instanceName", "instanceId"),
    ("rds", "rds", "vpcId", "instanceName", "instanceId"),
    ("eips", "eips", "vpcId", None, None),  # name/id handled specially
    ("es", "es", "vpcId", "instanceName", "instanceId"),
]

# Infrastructure resources (not tagged by customer — minimized by VPC association)
_INFRA_RESOURCE_TYPES = [
    ("vpcs", "vpcs"),
    ("subnets", "subnets"),
    ("security_groups", "security_groups"),
]


def _collect_raw(client, regions):
    """Scan all regions and collect raw resource lists."""
    raw = {"vms": [], "lbs": [], "redis": [], "mongodb": [], "rds": [],
           "vpcs": [], "subnets": [], "security_groups": [], "eips": [],
           "es": []}

    for region in regions:
        for raw_key, list_name, *_ in _RESOURCE_TYPES + _INFRA_RESOURCE_TYPES:
            try:
                items = getattr(client, f"list_{list_name}")(region=region)
                raw[raw_key].extend(items)
            except Exception as e:
                label = list_name.replace("_", " ").title()
                print(f"  [警告]  {region} {label} discovery failed: {e}")
    return raw


def _classify(tags: dict, name: str, rtype: str) -> dict:
    """Determine deployment mode with confidence score."""
    # K8s signals
    if K8S_CLUSTER_TAG in tags or K8S_CREATED_TAG in tags:
        tag = K8S_CLUSTER_TAG if K8S_CLUSTER_TAG in tags else K8S_CREATED_TAG
        return {"mode": "k8s", "confidence": 0.95,
                "reason": f"detected K8s tag: {tag}"}

    # Customer tag present, no K8s tags
    if "客户" in tags:
        return {"mode": "traditional", "confidence": 0.85,
                "reason": "customer tag present, no K8s tags"}

    # Name prefix matching
    return {"mode": "unknown", "confidence": 0.30,
            "reason": "no identifying tags"}


def _classify_resource(tags: dict, resource: dict, name_field: str, id_field: str, rtype: str):
    """Classify a single resource and return entry + optional confirmation."""
    name = resource.get(name_field, "") if name_field else ""
    rid = resource.get(id_field, "") if id_field else ""
    cls = _classify(tags, name, rtype)
    entry = cls | {"id": rid, "name": name}
    needs = entry if cls["confidence"] <= 0.8 else None
    return entry, needs


def discover_customer_resources(client: JdcClient, customer: str,
                                 regions: list = None) -> dict:
    """Scan all resources for a customer across regions.

    Returns:
        {
            "customer": str,
            "regions": [str],
            "raw": {...},
            "topology": {"vpcs": {vpc_id: {...}}},
            "classification": {...},
        }
    """
    if regions is None:
        regions = ALL_REGIONS

    raw = _collect_raw(client, regions)

    # Filter to customer resources
    customer_data = {}
    for raw_key, *_rest in _RESOURCE_TYPES:
        customer_data[raw_key] = filter_by_tag(raw[raw_key], "客户", customer)

    # Minimize raw data (safety: don't persist cross-customer inventory)
    for raw_key in customer_data:
        raw[raw_key] = customer_data[raw_key]

    # Collect VPC IDs from all customer resources
    customer_vpc_ids = set()
    for raw_key, _list_name, vpc_field, *_rest in _RESOURCE_TYPES:
        for r in customer_data.get(raw_key, []):
            vpc_id = r.get(vpc_field, "")
            if vpc_id:
                customer_vpc_ids.add(vpc_id)

    # Minimize VPC/subnet/security_group raw data
    customer_vpcs = [vpc for vpc in raw["vpcs"]
                     if vpc.get("vpcId") in customer_vpc_ids]
    raw["vpcs"] = customer_vpcs

    customer_subnets = [sn for sn in raw["subnets"]
                        if sn.get("vpcId") in customer_vpc_ids]
    raw["subnets"] = customer_subnets

    # Security groups associated with customer VMs
    customer_sg_ids = set()
    for vm in customer_data.get("vms", []):
        ni = vm.get("primaryNetworkInterface", {})
        nif = ni.get("networkInterface", {}) if isinstance(ni, dict) else {}
        for sg_ref in nif.get("securityGroups", []):
            gid = sg_ref.get("groupId", "")
            if gid:
                customer_sg_ids.add(gid)
    raw["security_groups"] = [sg for sg in raw["security_groups"]
                              if sg.get("groupId") in customer_sg_ids]

    # Build VPC topology
    vpc_map = {}
    for vpc in customer_vpcs:
        vpc_id = vpc.get("vpcId", "")
        if vpc_id:
            vpc_map[vpc_id] = {
                "name": vpc.get("vpcName", ""),
                "cidr": vpc.get("addressPrefix", ""),
                "subnets": [],
                "vms": [], "lbs": [], "redis": [], "mongodb": [],
                "rds": [], "eips": [],
            }

    for subnet in customer_subnets:
        vpc_id = subnet.get("vpcId", "")
        if vpc_id in vpc_map:
            vpc_map[vpc_id]["subnets"].append({
                "name": subnet.get("subnetName", ""),
                "cidr": subnet.get("addressPrefix", ""),
                "az": subnet.get("az", ""),
            })

    # Populate VPC topology with resource names
    for raw_key, _list_name, vpc_field, name_field, _id_field in _RESOURCE_TYPES:
        for r in customer_data.get(raw_key, []):
            vpc_id = r.get(vpc_field, "")
            if vpc_id not in vpc_map:
                continue
            if raw_key == "eips":
                name = r.get("elasticIpAddress") or r.get("ipAddress") or r.get("elasticIpId", "")
            else:
                name = r.get(name_field, "") if name_field else ""
            # eips key in vpc_map is already "eips"
            vpc_map[vpc_id].setdefault(raw_key, []).append(name)

    # Build classification
    classification = {"resources": [], "needs_confirmation": []}
    for raw_key, _list_name, _vpc_field, name_field, id_field in _RESOURCE_TYPES:
        for r in customer_data.get(raw_key, []):
            tags = tag_dict(r)
            if raw_key == "eips":
                name = r.get("elasticIpAddress") or r.get("ipAddress") or r.get("elasticIpName", "")
                rid = r.get("elasticIpId") or r.get("id", "")
            else:
                name = r.get(name_field, "") if name_field else ""
                rid = r.get(id_field, "") if id_field else ""
            cls = _classify(tags, name, raw_key.rstrip("s"))
            entry = cls | {"id": rid, "name": name}
            classification["resources"].append(entry)
            if cls["confidence"] <= 0.8:
                classification["needs_confirmation"].append(entry)

    return {
        "customer": customer,
        "regions": regions,
        "raw": raw,
        "topology": {"vpcs": vpc_map},
        "classification": classification,
    }
