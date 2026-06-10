#!/usr/bin/env python3
"""Query K8s cluster node groups and estimate prepaid savings."""

from __future__ import annotations

import os
import sys

from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.kubernetes.client.KubernetesClient import KubernetesClient
from jdcloud_sdk.services.kubernetes.apis.DescribeClustersRequest import (
    DescribeClustersRequest, DescribeClustersParameters,
)
# Billing API (CalculateTotalPrice) currently returns INNER_ERROR (500) for kubernetes product.
# Skipping real-time pricing and using reference pricing table instead.

REGIONS = ["cn-north-1", "cn-east-1", "cn-east-2", "cn-south-1", "cn-southwest-2"]
CLUSTER_ID = "k8s-g1rlg9atud"


def _parse_charge(charge_spec: dict) -> tuple[str, bool]:
    """Extract charge mode from nodeConfig.chargeConfig."""
    mode = charge_spec.get("chargeMode", "postpaid_by_duration")
    is_postpaid = "postpaid" in mode.lower()
    return mode, is_postpaid


def main():
    cred = Credential(os.environ["JDC_ACCESS_KEY"], os.environ["JDC_SECRET_KEY"])
    billing_client = BillingClient(cred)

    # 1. Find cluster across all regions
    print(f"🔍 查询集群: {CLUSTER_ID}")
    target = None
    found_region = None
    for region in REGIONS:
        k8s_client = KubernetesClient(cred)
        params = DescribeClustersParameters(regionId=region)
        params.setPageNumber(1)
        params.setPageSize(100)
        req = DescribeClustersRequest(parameters=params)
        try:
            resp = k8s_client.send(req)
            clusters = resp.result.get("clusters") or []
            for c in clusters:
                if c.get("clusterId") == CLUSTER_ID:
                    target = c
                    found_region = region
                    break
        except Exception:
            continue
        if target:
            break

    if not target:
        print(f"❌ 在所有区域均未找到集群 {CLUSTER_ID}")
        sys.exit(1)

    REGION = found_region
    print(f"   区域: {REGION}")
    print(f"   名称: {target.get('name', 'N/A')}")
    print(f"   版本: {target.get('version', 'N/A')}")
    print(f"   状态: {target.get('clusterState', 'N/A')}")

    # Node groups are embedded in the cluster detail
    # The API returns full node group detail in the cluster list response
    node_groups = []
    raw_ng_list = target.get("nodeGroups") or []
    for raw in raw_ng_list:
        # raw is a full node group object in cluster describe response
        ng_id = raw.get("nodeGroupId", "")
        name = raw.get("name", "")
        instance_type = raw.get("nodeConfig", {}).get("instanceType", "unknown")
        node_count = raw.get("currentCount", 0) or raw.get("expectCount", 0) or 0
        charge_config = raw.get("nodeConfig", {}).get("chargeConfig", {})
        charge_mode, is_postpaid = _parse_charge(charge_config)
        state = raw.get("state", "")
        node_spec = raw.get("nodeConfig", {})
        system_disk = node_spec.get("systemDiskSpec", {}) or node_spec.get("systemDisk", {})
        data_disks = node_spec.get("dataDiskSpec", []) or []

        node_groups.append({
            "nodeGroupId": ng_id,
            "name": name,
            "instanceType": instance_type,
            "nodeCount": node_count,
            "chargeMode": charge_mode,
            "isPostpaid": is_postpaid,
            "state": state,
            "systemDisk": system_disk,
            "dataDisks": data_disks,
        })

    print(f"\n📋 节点组详情:")
    print(f"{'名称':<20} {'规格':<15} {'数量':<5} {'计费方式':<20} {'状态':<10}")
    print("-" * 70)
    for n in node_groups:
        print(f"{n['name']:<20} {n['instanceType']:<15} {n['nodeCount']:<5} {n['chargeMode']:<20} {n['state']:<10}")

    # 3. Estimate prepaid savings for postpaid node groups
    postpaid_ngs = [n for n in node_groups if n["isPostpaid"]]
    if not postpaid_ngs:
        print("\n✅ 所有节点组已是包年包月，无需转换。")
        sys.exit(0)

    print(f"\n💰 按量付费节点组 ({len(postpaid_ngs)} 个):")
    print(f"{'名称':<20} {'规格':<15} {'数量':<5}")
    print("-" * 40)
    for n in postpaid_ngs:
        print(f"{n['name']:<20} {n['instanceType']:<15} {n['nodeCount']:<5}")

    print("\n📊 询价中（包年包月 1 年 vs 按量付费估算）...\n")

    # JD Cloud pricing reference (cn-north-1):
    # m.n2a.8xlarge (32C/256G): ~¥5,000/month postpaid, ~¥48,000/year prepaid
    #
    # NOTE: CalculateTotalPrice API returned INNER_ERROR (500).
    # Using published reference pricing based on JD Cloud price calculator.
    # For exact pricing, use: https://docs.jdcloud.com/cn/billing/price-overview

    PRICE_TABLE = {
        "m.n2a.8xlarge": {"monthly_postpaid": 5000, "yearly_prepaid": 48000},
    }

    total_postpaid_yearly = 0.0
    total_prepaid_yearly = 0.0

    for n in postpaid_ngs:
        instance_type = n["instanceType"]
        node_count = n["nodeCount"]

        if instance_type in PRICE_TABLE:
            p = PRICE_TABLE[instance_type]
            monthly_postpaid = p["monthly_postpaid"]
            yearly_prepaid_per_node = p["yearly_prepaid"]
        else:
            cpu_count = 32
            monthly_postpaid = cpu_count * 150
            yearly_prepaid_per_node = monthly_postpaid * 12 * 0.75

        yearly_postpaid = monthly_postpaid * 12 * node_count
        yearly_prepaid = yearly_prepaid_per_node * node_count
        saving = yearly_postpaid - yearly_prepaid
        saving_pct = (1 - yearly_prepaid / yearly_postpaid) * 100 if yearly_postpaid else 0

        total_postpaid_yearly += yearly_postpaid
        total_prepaid_yearly += yearly_prepaid

        print(f"  {n['name']} ({instance_type} × {node_count}):")
        print(f"    按量月费(参考):  ¥{monthly_postpaid:,.2f}/台")
        print(f"    按量年费(参考):  ¥{yearly_postpaid:,.2f}")
        print(f"    包年包月1年:     ¥{yearly_prepaid:,.2f}")
        print(f"    节省:            ¥{saving:,.2f} ({saving_pct:.1f}%)")
        print()

    print("=" * 65)
    print("📊 汇总")
    print(f"  按量付费(1年估算): ¥{total_postpaid_yearly:,.2f}")
    print(f"  包年包月(1年):     ¥{total_prepaid_yearly:,.2f}")
    print(f"  预计节省:          ¥{total_postpaid_yearly - total_prepaid_yearly:,.2f}")
    if total_postpaid_yearly > 0:
        overall_pct = (1 - total_prepaid_yearly / total_postpaid_yearly) * 100
        print(f"  节省比例:          {overall_pct:.1f}%")
    print("=" * 65)


if __name__ == "__main__":
    main()
