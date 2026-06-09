#!/usr/bin/env python3
"""
资源到期巡检脚本

用法:
    python expiry_cruise.py # 默认14天阈值
    python expiry_cruise.py --warning-days 7         # 7天紧急预警
    python expiry_cruise.py --regions cn-north-1     # 指定区域
    python expiry_cruise.py --types vm,redis          # 指定资源类型
    python expiry_cruise.py --customer 烟台振华       # 按客户过滤
    python expiry_cruise.py --output-dir ./outputs # 指定输出目录
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional

# 添加 lib 路径
_script_dir = Path(__file__).resolve().parent
_project_dir = _script_dir.parent
sys.path.insert(0, str(_project_dir))

from lib.jdc_client import JdcClient


def parse_args():
    parser = argparse.ArgumentParser(
        description="京东云资源到期巡检",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                              # 基本巡检（14天阈值）
  %(prog)s --warning-days 7             # 7天紧急预警
  %(prog)s --regions cn-north-1,cn-south-1  # 指定区域
  %(prog)s --types vm,redis # 指定资源类型
  %(prog)s --customer 烟台振华           # 按客户过滤
        """
    )
    parser.add_argument(
        "--warning-days",
        type=int,
        default=14,
        help="预警天数阈值（默认14天）"
    )
    parser.add_argument(
        "--regions",
        type=str,
        default="all",
        help="巡检区域，逗号分隔或 all（默认 all）"
    )
    parser.add_argument(
        "--types",
        type=str,
        default="vm,redis,eip,disk,rds,clb,mongodb,elasticsearch,ssl",
        help="资源类型，逗号分隔（默认 vm,redis,eip,disk,rds,clb,mongodb,elasticsearch,ssl）"
    )
    parser.add_argument(
        "--customer",
        type=str,
        default="",
        help="按客户名称过滤（可选）"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="",
        help="输出目录（默认 ~/.jdcloud-routines-ops/outputs/expiry）"
    )
    return parser.parse_args()


def get_output_dir(args) -> Path:
    """获取输出目录"""
    if args.output_dir:
        return Path(args.output_dir).resolve()

    # 默认使用 ~/.jdcloud-routines-ops/outputs/expiry
    home_outputs = Path.home() / ".jdcloud-routines-ops" / "outputs" / "expiry"
    if home_outputs.exists() or os.access(Path.home(), os.W_OK):
        return home_outputs

    # 回退到项目内 outputs
    project_outputs = _project_dir / "jdcloud-routines-ops" / "outputs" / "expiry"
    return project_outputs


def cruise_vm(client: JdcClient, region: str, warning_days: int, customer_filter: str) -> list[dict]:
    """巡检 VM"""
    results = []
    for vm in client.describe_vms(region):
        charge = vm.get("charge") or {}
        expired_time = charge.get("chargeExpiredTime", "")
        days = client.get_expired_days(expired_time)

        if days< 0 or days > warning_days:
            continue

        customer = client.get_tag_value(vm.get("tags"), "客户")
        if customer_filter and customer != customer_filter:
            continue

        results.append({
            "type": "VM",
            "name": vm.get("instanceName", ""),
            "id": vm.get("instanceId", ""),
            "region": region,
            "region_cn": client.get_region_name(region),
            "expired": expired_time[:10] if expired_time else "",
            "days_left": days,
            "customer": customer,
            "instance_type": vm.get("instanceType", ""),
        })
    return results


def cruise_redis(client: JdcClient, region: str, warning_days: int, customer_filter: str) -> list[dict]:
    """巡检 Redis"""
    results = []
    for inst in client.describe_redis(region):
        charge = inst.get("charge") or {}
        expired_time = charge.get("chargeExpiredTime", "")
        days = client.get_expired_days(expired_time)

        if days < 0 or days > warning_days:
            continue

        customer = client.get_tag_value(inst.get("tags"), "客户")
        if customer_filter and customer != customer_filter:
            continue

        results.append({
            "type": "Redis",
            "name": inst.get("cacheInstanceName", ""),
            "id": inst.get("cacheInstanceId", ""),
            "region": region,
            "region_cn": client.get_region_name(region),
            "expired": expired_time[:10] if expired_time else "",
            "days_left": days,
            "customer": customer,
            "memory_mb": inst.get("cacheInstanceMemoryMB", ""),
        })
    return results


def cruise_eip(client: JdcClient, region: str, warning_days: int, customer_filter: str) -> list[dict]:
    """巡检 EIP"""
    results = []
    for eip in client.describe_eips(region):
        charge = eip.get("charge") or {}
        expired_time = charge.get("chargeExpiredTime", "")
        days = client.get_expired_days(expired_time)

        if days < 0 or days > warning_days:
            continue

        customer = client.get_tag_value(eip.get("tags"), "客户")
        if customer_filter and customer != customer_filter:
            continue

        results.append({
            "type": "EIP",
            "name": eip.get("eipAddress", ""),
            "id": eip.get("eipId", ""),
            "region": region,
            "region_cn": client.get_region_name(region),
            "expired": expired_time[:10] if expired_time else "",
            "days_left": days,
            "customer": customer,
        })
    return results


def cruise_disk(client: JdcClient, region: str, warning_days: int, customer_filter: str) -> list[dict]:
    """巡检云盘"""
    results = []
    for disk in client.describe_disks(region):
        charge = disk.get("charge") or {}
        expired_time = charge.get("chargeExpiredTime", "")
        days = client.get_expired_days(expired_time)

        if days < 0 or days > warning_days:
            continue

        customer = client.get_tag_value(disk.get("tags"), "客户")
        if customer_filter and customer != customer_filter:
            continue

        results.append({
            "type": "云盘",
            "name": disk.get("name", ""),
            "id": disk.get("diskId", ""),
            "region": region,
            "region_cn": client.get_region_name(region),
            "expired": expired_time[:10] if expired_time else "",
            "days_left": days,
            "customer": customer,
            "disk_size_gb": disk.get("diskSizeGB", ""),
        })
    return results


def cruise_rds(client: JdcClient, region: str, warning_days: int, customer_filter: str) -> list[dict]:
    """巡检 RDS"""
    results = []
    for inst in client.describe_rds(region):
        charge = inst.get("charge") or {}
        expired_time = charge.get("chargeExpiredTime", "")
        days = client.get_expired_days(expired_time)

        if days < 0 or days > warning_days:
            continue

        customer = client.get_tag_value(inst.get("tags"), "客户")
        if customer_filter and customer != customer_filter:
            continue

        results.append({
            "type": f"RDS-{inst.get('engine', 'MySQL')}",
            "name": inst.get("instanceName", ""),
            "id": inst.get("instanceId", ""),
            "region": region,
            "region_cn": client.get_region_name(region),
            "expired": expired_time[:10] if expired_time else "",
            "days_left": days,
            "customer": customer,
            "engine": inst.get("engine", ""),
            "engine_version": inst.get("engineVersion", ""),
            "instance_type": inst.get("instanceType", ""),
        })
    return results


def cruise_clb(client: JdcClient, region: str, warning_days: int, customer_filter: str) -> list[dict]:
    """巡检 CLB 负载均衡"""
    results = []
    for lb in client.describe_load_balancers(region):
        charge = lb.get("charge") or {}
        expired_time = charge.get("chargeExpiredTime", "")
        days = client.get_expired_days(expired_time)

        if days < 0 or days > warning_days:
            continue

        customer = client.get_tag_value(lb.get("tags"), "客户")
        if customer_filter and customer != customer_filter:
            continue

        results.append({
            "type": "CLB",
            "name": lb.get("loadBalancerName", ""),
            "id": lb.get("loadBalancerId", ""),
            "region": region,
            "region_cn": client.get_region_name(region),
            "expired": expired_time[:10] if expired_time else "",
            "days_left": days,
            "customer": customer,
            "lb_type": lb.get("type", ""),
        })
    return results


def cruise_mongodb(client: JdcClient, region: str, warning_days: int, customer_filter: str) -> list[dict]:
    """巡检 MongoDB"""
    results = []
    for inst in client.describe_mongodb(region):
        charge = inst.get("charge") or {}
        expired_time = charge.get("chargeExpiredTime", "")
        days = client.get_expired_days(expired_time)

        if days < 0 or days > warning_days:
            continue

        customer = client.get_tag_value(inst.get("tags"), "客户")
        if customer_filter and customer != customer_filter:
            continue

        results.append({
            "type": "MongoDB",
            "name": inst.get("instanceName", ""),
            "id": inst.get("instanceId", ""),
            "region": region,
            "region_cn": client.get_region_name(region),
            "expired": expired_time[:10] if expired_time else "",
            "days_left": days,
            "customer": customer,
            "engine": "MongoDB",
            "engine_version": inst.get("engineVersion", ""),
        })
    return results


def cruise_elasticsearch(client: JdcClient, region: str, warning_days: int, customer_filter: str) -> list[dict]:
    """巡检 Elasticsearch"""
    results = []
    for inst in client.describe_elasticsearch(region):
        charge = inst.get("charge") or {}
        expired_time = charge.get("chargeExpiredTime", "")
        days = client.get_expired_days(expired_time)

        if days < 0 or days > warning_days:
            continue

        customer = client.get_tag_value(inst.get("tags"), "客户")
        if customer_filter and customer != customer_filter:
            continue

        results.append({
            "type": "Elasticsearch",
            "name": inst.get("instanceName", ""),
            "id": inst.get("instanceId", ""),
            "region": region,
            "region_cn": client.get_region_name(region),
            "expired": expired_time[:10] if expired_time else "",
            "days_left": days,
            "customer": customer,
            "version": inst.get("version", ""),
        })
    return results


def cruise_ssl(client: JdcClient, warning_days: int, customer_filter: str) -> list[dict]:
    """巡检 SSL 证书（全局资源）"""
    results = []
    for cert in client.describe_ssl_certs():
        end_time = cert.get("endTime", "")
        days = client.get_expired_days(end_time)

        if days < 0 or days > warning_days:
            continue

        customer = client.get_tag_value(cert.get("tags"), "客户")
        if customer_filter and customer != customer_filter:
            continue

        results.append({
            "type": "SSL证书",
            "name": cert.get("certName", ""),
            "id": cert.get("certId", ""),
            "region": "全局",
            "region_cn": "全局",
            "expired": end_time[:10] if end_time else "",
            "days_left": days,
            "customer": customer,
            "domain": cert.get("commonName", ""),
            "cert_type": cert.get("certType", ""),
        })
    return results



def print_report(all_expiring: list[dict], warning_days: int):
    """打印汇总报告"""
    if not all_expiring:
        print("\n🎉 太好了！所有区域都没有即将到期的资源（{}天内）。".format(warning_days))
        return

    # 按剩余天数排序
    all_expiring.sort(key=lambda x: x["days_left"])

    # 按客户分组
    by_customer = defaultdict(list)
    for r in all_expiring:
        by_customer[r["customer"]].append(r)

    # 按区域统计
    by_region = defaultdict(int)
    for r in all_expiring:
        by_region[r["region"]] += 1

    print("\n" + "=" * 80)
    print("📊 汇总报告")
    print("=" * 80)

    # 打印区域统计
    print("\n📍 区域统计:")
    for region, count in sorted(by_region.items(), key=lambda x: -x[1]):
        region_cn = all_expiring[0]["region_cn"] if all_expiring and by_region[region] > 0 else region
        for r in all_expiring:
            if r["region"] == region:
                region_cn = r["region_cn"]
                break
        print(f"   {region} ({region_cn}): {count}个资源")

    for customer, resources in sorted(by_customer.items(), key=lambda x: -len(x[1])):
        print(f"\n🏢 {customer} ({len(resources)}个资源)")
        for r in resources:
            urgency = "🔴" if r["days_left"] <= 3 else ("🟡" if r["days_left"] <= 7 else "🟢")
            extra = ""
            if r["type"] == "Redis":
                extra = f" | {r.get('memory_mb', '')}MB"
            elif r["type"] == "云盘":
                extra = f" | {r.get('disk_size_gb', '')}GB"
            elif r["type"].startswith("RDS-"):
                extra = f" | {r.get('engine', '')} {r.get('engine_version', '')}"
            elif r["type"] == "SSL证书":
                extra = f" | {r.get('domain', '')} ({r.get('cert_type', '')})"
            print(f"   {urgency} [{r['type']}] {r['name']}")
            print(f"       区域: {r['region']} ({r['region_cn']}) | 剩余 {r['days_left']}天 | 到期 {r['expired']}{extra}")


def main():
    args = parse_args()

    # 解析区域和类型
    regions = args.regions.split(",") if args.regions != "all" else JdcClient.DEFAULT_REGIONS
    types = args.types.split(",")

    #初始化客户端
    client = JdcClient()

    print(f"🔍 京东云资源到期巡检")
    print(f"   预警阈值: {args.warning_days} 天内到期")
    print(f"   区域数量: {len(regions)}")
    print(f"   资源类型: {', '.join(types)}")
    if args.customer:
        print(f"   客户过滤: {args.customer}")
    print("=" * 80)

    all_expiring = []
    region_summary = {}

    for region in regions:
        print(f"\n📍 {region} ({client.get_region_name(region)})")
        region_expiring = []

        if "vm" in types:
            region_expiring.extend(cruise_vm(client, region, args.warning_days, args.customer))
        if "redis" in types:
            region_expiring.extend(cruise_redis(client, region, args.warning_days, args.customer))
        if "eip" in types:
            region_expiring.extend(cruise_eip(client, region, args.warning_days, args.customer))
        if "disk" in types:
            region_expiring.extend(cruise_disk(client, region, args.warning_days, args.customer))
        if "rds" in types:
            region_expiring.extend(cruise_rds(client, region, args.warning_days, args.customer))
        if "clb" in types:
            region_expiring.extend(cruise_clb(client, region, args.warning_days, args.customer))
        if "mongodb" in types:
            region_expiring.extend(cruise_mongodb(client, region, args.warning_days, args.customer))
        if "elasticsearch" in types:
            region_expiring.extend(cruise_elasticsearch(client, region, args.warning_days, args.customer))

        if region_expiring:
            region_summary[region] = len(region_expiring)
            all_expiring.extend(region_expiring)
            print(f"   ⚠️  发现 {len(region_expiring)} 个即将到期的资源")
        else:
            print(f"   ✅ 无即将到期的资源")

    # SSL 证书是全局资源，单独巡检
    if "ssl" in types:
        print(f"\n🔐 SSL 证书巡检（全局资源）")
        ssl_expiring = cruise_ssl(client, args.warning_days, args.customer)
        if ssl_expiring:
            region_summary["全局"] = region_summary.get("全局", 0) + len(ssl_expiring)
            all_expiring.extend(ssl_expiring)
            print(f"   ⚠️  发现 {len(ssl_expiring)} 个即将到期的 SSL 证书")
        else:
            print(f"   ✅ 无即将到期的 SSL 证书")

    # 打印报告
    print_report(all_expiring, args.warning_days)

    # 保存 JSON 报告
    output_dir = get_output_dir(args)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_file = output_dir / f"expiry-report-{timestamp}.json"

    # 按类型统计
    type_counts = defaultdict(int)
    for r in all_expiring:
        type_counts[r["type"]] += 1

    report = {
        "report_time": datetime.now().isoformat(),
        "warning_days": args.warning_days,
        "regions_checked": regions,
        "types_checked": types,
        "customer_filter": args.customer or None,
        "summary": {
            "total_expiring": len(all_expiring),
            "by_type": dict(type_counts),
            "by_region": dict(region_summary),
            "urgent_7days": sum(1 for r in all_expiring if r["days_left"] <= 7),
        },
        "details": all_expiring,
    }

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n📄 详细报告已保存: {report_file}")

    # 返回状态码
    return 0 if all_expiring else 1


if __name__ == "__main__":
    sys.exit(main())