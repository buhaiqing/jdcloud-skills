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
from lib.jdc_client import JdcClient, filter_by_tag, tag_dict

K8S_CLUSTER_TAG = "kubernetes.jdcloud.com/cluster_id"
K8S_CREATED_TAG = "kubernetes.jdcloud.com/created_by"

# All regions to scan
ALL_REGIONS = ["cn-north-1", "cn-east-2", "cn-south-1", "cn-east-1"]


def discover_customer_resources(client: JdcClient, customer: str,
                                 regions: list = None) -> dict:
    """Scan all resources for a customer across regions.

    Returns:
        {
            "customer": str,
            "regions": [str],
            "raw": {
                "vms": [...], "lbs": [...], "redis": [...], "mongodb": [...],
                "vpcs": [...], "subnets": [...], "security_groups": [...],
                "eips": [...], "nats": [...], "es": [...],
            },
            "topology": {
                "vpcs": {vpc_id: {name, cidr, subnets: [...], resources: [...]}},
                "clb_targets": {lb_id: [backend_ip, ...]},
                "k8s_clusters": {cluster_id: {nodes: [...], ingress: [...]}},
            },
            "classification": {
                "resources": [{"id": ..., "type": ..., "mode": ..., "confidence": ..., "reason": ...}],
                "needs_confirmation": [{"id": ..., "type": ..., "reason": ...}],
            }
        }
    """
    if regions is None:
        regions = ALL_REGIONS

    raw = {"vms": [], "lbs": [], "redis": [], "mongodb": [], "rds": [], "vpcs": [],
           "subnets": [], "security_groups": [], "eips": [], "nats": [],
           "es": [],}

    for region in regions:
        try:
            vms = client.list_vms(region=region)
            raw["vms"].extend(vms)
        except Exception as e:
            print(f"  [警告]  {region} VM discovery failed: {e}")
        try:
            lbs = client.list_lbs(region=region)
            raw["lbs"].extend(lbs)
        except Exception as e:
            print(f"  [警告]  {region} LB discovery failed: {e}")
        try:
            redis = client.list_redis(region=region)
            raw["redis"].extend(redis)
        except Exception as e:
            print(f"  [警告]  {region} Redis discovery failed: {e}")
        try:
            mongodb = client.list_mongodb(region=region)
            raw["mongodb"].extend(mongodb)
        except Exception as e:
            print(f"  [警告]  {region} MongoDB discovery failed: {e}")
        try:
            vpcs = client.list_vpcs(region=region)
            raw["vpcs"].extend(vpcs)
        except Exception as e:
            print(f"  [警告]  {region} VPC discovery failed: {e}")
        try:
            subnets = client.list_subnets(region=region)
            raw["subnets"].extend(subnets)
        except Exception as e:
            print(f"  [警告]  {region} Subnet discovery failed: {e}")
        try:
            sgs = client.list_security_groups(region=region)
            raw["security_groups"].extend(sgs)
        except Exception as e:
            print(f"  [警告]  {region} Security Group discovery failed: {e}")
        try:
            es = client.list_es(region=region)
            raw["es"].extend(es)
        except Exception as e:
            print(f"  [警告]  {region} ES discovery failed: {e}")
        try:
            eips = client.list_eips(region=region)
            raw["eips"].extend(eips)
        except Exception as e:
            print(f"  [警告]  {region} EIP discovery failed: {e}")
        try:
            rds = client.list_rds(region=region)
            raw["rds"].extend(rds)
        except Exception as e:
            print(f"  [警告]  {region} RDS discovery failed: {e}")

    # Filter to customer resources
    customer_vms = filter_by_tag(raw["vms"], "客户", customer)
    customer_lbs = filter_by_tag(raw["lbs"], "客户", customer)
    customer_redis = filter_by_tag(raw["redis"], "客户", customer)
    customer_mongodb = filter_by_tag(raw["mongodb"], "客户", customer)
    customer_rds = filter_by_tag(raw["rds"], "客户", customer)
    customer_eips = filter_by_tag(raw["eips"], "客户", customer)
    customer_nats = filter_by_tag(raw["nats"], "客户", customer)
    customer_es = filter_by_tag(raw["es"], "客户", customer)

    # ── Minimize returned/persisted raw data (Safety requirement) ──
    # Phase 1 must list regional resources to discover tagged ones, but the
    # raw topology persisted to reports/output must NOT contain all-account
    # / cross-customer inventory. Replace each raw array with only
    # customer-scoped entries.
    raw["vms"] = customer_vms
    raw["lbs"] = customer_lbs
    raw["redis"] = customer_redis
    raw["mongodb"] = customer_mongodb
    raw["rds"] = customer_rds
    raw["eips"] = customer_eips
    raw["nats"] = customer_nats
    raw["es"] = customer_es

    # Build VPC topology
    vpc_map = {}
    customer_vpc_ids = set()
    for vm in customer_vms:
        vpc_id = vm.get("vpcId", "")
        if vpc_id:
            customer_vpc_ids.add(vpc_id)
    for lb in customer_lbs:
        vpc_id = lb.get("vpcId", "")
        if vpc_id:
            customer_vpc_ids.add(vpc_id)
    for r in customer_redis:
        vpc_id = r.get("vpcId", "")
        if vpc_id:
            customer_vpc_ids.add(vpc_id)
    for m in customer_mongodb:
        vpc_id = m.get("vpcId", "")
        if vpc_id:
            customer_vpc_ids.add(vpc_id)
    for r in customer_rds:
        vpc_id = r.get("vpcId", "")
        if vpc_id:
            customer_vpc_ids.add(vpc_id)
    for eip in customer_eips:
        vpc_id = eip.get("vpcId", "")
        if vpc_id:
            customer_vpc_ids.add(vpc_id)

    # ── Minimize VPC / subnet / security-group raw data ──
    # Only keep VPCs referenced by customer resources.
    customer_vpcs = [vpc for vpc in raw["vpcs"]
                     if vpc.get("vpcId") in customer_vpc_ids]
    raw["vpcs"] = customer_vpcs

    # Only keep subnets belonging to customer VPCs.
    customer_vpc_id_set = customer_vpc_ids  # already a set
    customer_subnets = [sn for sn in raw["subnets"]
                        if sn.get("vpcId") in customer_vpc_id_set]
    raw["subnets"] = customer_subnets

    # Only keep security groups associated with customer VMs.
    # Extract SG IDs from customer VMs' network interfaces.
    customer_sg_ids = set()
    for vm in customer_vms:
        for ni in [vm.get("primaryNetworkInterface", {})]:
            nif = ni.get("networkInterface", {}) if isinstance(ni, dict) else {}
            for sg_ref in nif.get("securityGroups", []):
                gid = sg_ref.get("groupId", "")
                if gid:
                    customer_sg_ids.add(gid)
    customer_sgs = [sg for sg in raw["security_groups"]
                    if sg.get("groupId") in customer_sg_ids]
    raw["security_groups"] = customer_sgs

    # Build VPC topology from minimized data
    for vpc in customer_vpcs:
        vpc_id = vpc["vpcId"]
        vpc_map[vpc_id] = {
            "name": vpc.get("vpcName", ""),
            "cidr": vpc.get("addressPrefix", ""),
            "subnets": [],
            "vms": [],
            "lbs": [],
            "redis": [],
            "mongodb": [],
            "rds": [],
            "eips": [],
        }

    for subnet in customer_subnets:
        vpc_id = subnet.get("vpcId", "")
        if vpc_id in vpc_map:
            vpc_map[vpc_id]["subnets"].append({
                "name": subnet.get("subnetName", ""),
                "cidr": subnet.get("addressPrefix", ""),
                "az": subnet.get("az", ""),
            })

    for vm in customer_vms:
        vpc_id = vm.get("vpcId", "")
        if vpc_id in vpc_map:
            vpc_map[vpc_id]["vms"].append(vm.get("instanceName", ""))

    for rds in customer_rds:
        vpc_id = rds.get("vpcId", "")
        if vpc_id in vpc_map:
            vpc_map[vpc_id]["rds"].append(rds.get("instanceName", ""))

    for mongo in customer_mongodb:
        vpc_id = mongo.get("vpcId", "")
        if vpc_id in vpc_map:
            vpc_map[vpc_id]["mongodb"].append(mongo.get("instanceName", ""))

    for eip in customer_eips:
        vpc_id = eip.get("vpcId", "")
        if vpc_id in vpc_map:
            vpc_map[vpc_id]["eips"].append(
                eip.get("elasticIpAddress") or eip.get("ipAddress") or eip.get("elasticIpId", "")
            )

    # Build classification
    classification = {"resources": [], "needs_confirmation": []}
    for vm in customer_vms:
        tags = tag_dict(vm)
        name = vm.get("instanceName", "")
        rid = vm.get("instanceId", "")
        cls = _classify(tags, name, "vm")
        classification["resources"].append(cls | {"id": rid, "name": name})
        if cls["confidence"] <= 0.8:
            classification["needs_confirmation"].append(cls | {"id": rid, "name": name})

    for lb in customer_lbs:
        tags = tag_dict(lb)
        name = lb.get("loadBalancerName", "")
        rid = lb.get("loadBalancerId", "")
        cls = _classify(tags, name, "lb")
        classification["resources"].append(cls | {"id": rid, "name": name})
        if cls["confidence"] <= 0.8:
            classification["needs_confirmation"].append(cls | {"id": rid, "name": name})

    for rds in customer_rds:
        tags = tag_dict(rds)
        name = rds.get("instanceName", "")
        rid = rds.get("instanceId", "")
        cls = _classify(tags, name, "rds")
        classification["resources"].append(cls | {"id": rid, "name": name})
        if cls["confidence"] <= 0.8:
            classification["needs_confirmation"].append(cls | {"id": rid, "name": name})

    for mongo in customer_mongodb:
        tags = tag_dict(mongo)
        name = mongo.get("instanceName", "")
        rid = mongo.get("instanceId", "")
        cls = _classify(tags, name, "mongodb")
        classification["resources"].append(cls | {"id": rid, "name": name})
        if cls["confidence"] <= 0.8:
            classification["needs_confirmation"].append(cls | {"id": rid, "name": name})

    for eip in customer_eips:
        tags = tag_dict(eip)
        name = eip.get("elasticIpAddress") or eip.get("ipAddress") or eip.get("elasticIpName", "")
        rid = eip.get("elasticIpId") or eip.get("id", "")
        cls = _classify(tags, name, "eip")
        classification["resources"].append(cls | {"id": rid, "name": name})
        if cls["confidence"] <= 0.8:
            classification["needs_confirmation"].append(cls | {"id": rid, "name": name})

    return {
        "customer": customer,
        "regions": regions,
        "raw": raw,
        "topology": {"vpcs": vpc_map},
        "classification": classification,
    }


def _classify(tags: dict, name: str, rtype: str) -> dict:
    """Determine deployment mode with confidence score."""
    # K8s signals
    if K8S_CLUSTER_TAG in tags or K8S_CREATED_TAG in tags:
        return {"mode": "k8s", "confidence": 0.95,
                "reason": f"detected K8s tag: {K8S_CLUSTER_TAG if K8S_CLUSTER_TAG in tags else K8S_CREATED_TAG}"}

    # Customer tag present, no K8s tags
    if "客户" in tags:
        return {"mode": "traditional", "confidence": 0.85,
                "reason": "customer tag present, no K8s tags"}

    # Name prefix matching
    customer = ""  # determined at higher level
    return {"mode": "unknown", "confidence": 0.30,
            "reason": "no identifying tags"}
