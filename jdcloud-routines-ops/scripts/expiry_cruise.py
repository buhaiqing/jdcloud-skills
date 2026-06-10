#!/usr/bin/env python3
"""
资源到期巡检脚本 V2 — 配置驱动模式

基于 code-patterns.md 模式 1：用 RESOURCE_CONFIG 替代 8 个重复函数

用法:
    python expiry_cruise_v2.py                              # 默认14天阈值
    python expiry_cruise_v2.py --warning-days 7             # 7天紧急预警
    python expiry_cruise_v2.py --regions cn-north-1         # 指定区域
    python expiry_cruise_v2.py --types vm,redis             # 指定资源类型
    python expiry_cruise_v2.py --customer 烟台振华          # 按客户过滤
    python expiry_cruise_v2.py --with-price                 # 询价模式（额外调用 billing API）
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

# 添加 lib 路径
_script_dir = Path(__file__).resolve().parent
_project_dir = _script_dir.parent
sys.path.insert(0, str(_project_dir))

from lib.jdc_client import JdcClient


# ═══════════════════════════════════════════════════════════════
# 资源配置表（code-patterns.md 模式 1）
# 新增资源类型只需在此加一行配置
# ═══════════════════════════════════════════════════════════════

RESOURCE_CONFIG = {
    "vm": {
        "api": "describe_vms",
        "list_key": "instances",
        "id_key": "instanceId",
        "name_key": "instanceName",
        "charge_path": ["charge", "chargeExpiredTime"],
        "extra_fields": {
            "instance_type": "instanceType",
        },
        "type_label": "VM",
    },
    "redis": {
        "api": "describe_redis",
        "list_key": "cacheInstances",
        "id_key": "cacheInstanceId",
        "name_key": "cacheInstanceName",
        "charge_path": ["charge", "chargeExpiredTime"],
        "extra_fields": {
            "memory_mb": "cacheInstanceMemoryMB",
        },
        "type_label": "Redis",
    },
    "eip": {
        "api": "describe_eips",
        "list_key": "eips",
        "id_key": "eipId",
        "name_key": "eipAddress",  # EIP 用 IP 作为名称
        "charge_path": ["charge", "chargeExpiredTime"],
        "extra_fields": {},
        "type_label": "EIP",
    },
    "disk": {
        "api": "describe_disks",
        "list_key": "disks",
        "id_key": "diskId",
        "name_key": "name",
        "charge_path": ["charge", "chargeExpiredTime"],
        "extra_fields": {
            "disk_size_gb": "diskSizeGB",
        },
        "type_label": "云盘",
    },
    "rds": {
        "api": "describe_rds",
        "list_key": "dbInstances",
        "id_key": "instanceId",
        "name_key": "instanceName",
        "charge_path": ["charge", "chargeExpiredTime"],
        "extra_fields": {
            "engine": "engine",
            "engine_version": "engineVersion",
            "instance_type": "instanceType",
        },
        "type_label_fn": lambda item: f"RDS-{item.get('engine', 'MySQL')}",
    },
    "clb": {
        "api": "describe_load_balancers",
        "list_key": "loadBalancers",
        "id_key": "loadBalancerId",
        "name_key": "loadBalancerName",
        "charge_path": ["charge", "chargeExpiredTime"],
        "extra_fields": {
            "lb_type": "type",
        },
        "type_label": "CLB",
    },
    "mongodb": {
        "api": "describe_mongodb",
        "list_key": "mongodbInstances",
        "id_key": "instanceId",
        "name_key": "instanceName",
        "charge_path": ["charge", "chargeExpiredTime"],
        "extra_fields": {
            "engine": "engine",
            "engine_version": "engineVersion",
        },
        "type_label": "MongoDB",
    },
    "elasticsearch": {
        "api": "describe_elasticsearch",
        "list_key": "instances",
        "id_key": "instanceId",
        "name_key": "instanceName",
        "charge_path": ["charge", "chargeExpiredTime"],
        "extra_fields": {
            "version": "version",
        },
        "type_label": "Elasticsearch",
    },
}


# ═══════════════════════════════════════════════════════════════
# 核心巡检逻辑（code-patterns.md 模式 1）
# ═══════════════════════════════════════════════════════════════

def cruise_resource(
    client: JdcClient,
    resource_type: str,
    region: str,
    warning_days: int,
    customer_filter: str = "",
    with_price: bool = False,
) -> list[dict]:
    """通用资源巡检 — 所有资源类型复用此模板

    Args:
        client: JdcClient 实例
        resource_type: 资源类型键（vm/redis/...）
        region: 区域 ID
        warning_days: 预警天数阈值
        customer_filter: 客户名称过滤（可选）
        with_price: 是否调用询价 API（code-patterns.md 模式 3）

    Returns:
        到期资源列表
    """
    cfg = RESOURCE_CONFIG.get(resource_type)
    if not cfg:
        print(f"警告: 未知资源类型 {resource_type}")
        return []

    # 调用对应 describe API
    api_method = getattr(client, cfg["api"], None)
    if not api_method:
        print(f"警告: 客户端未实现 {cfg['api']}")
        return []

    items = api_method(region)
    results = []

    for item in items:
        # 提取到期时间（支持嵌套路径如 ["charge", "chargeExpiredTime"]）
        charge_data = item
        for key in cfg["charge_path"]:
            charge_data = charge_data.get(key, {}) if isinstance(charge_data, dict) else {}
        expired_time = charge_data if isinstance(charge_data, str) else ""

        days = client.get_expired_days(expired_time)
        if days < 0 or days > warning_days:
            continue

        # 客户过滤
        customer = client.get_tag_value(item.get("tags"), "客户")
        if customer_filter and customer != customer_filter:
            continue

        # 构造结果
        result = {
            "type": cfg.get("type_label") or cfg.get("type_label_fn", lambda x: resource_type.upper())(item),
            "name": item.get(cfg["name_key"], ""),
            "id": item.get(cfg["id_key"], ""),
            "region": region,
            "region_cn": client.get_region_name(region),
            "expired": expired_time[:10] if expired_time else "",
            "days_left": days,
            "customer": customer,
        }

        # 添加额外字段
        for out_key, api_key in cfg.get("extra_fields", {}).items():
            result[out_key] = item.get(api_key, "")

        # 询价模式（code-patterns.md 模式 3）
        if with_price and days <= warning_days:
            try:
                price_info = client.price_inquiry_for_resource(
                    resource_type, result["id"], region, renew_months=1
                )
                if "error" not in price_info:
                    result["original_price"] = price_info.get("original_price", 0)
                    result["discount_price"] = price_info.get("discount_price", 0)
                    result["total_price"] = price_info.get("total_price", 0)
            except Exception as e:
                result["price_error"] = str(e)

        results.append(result)

    return results


# ═══════════════════════════════════════════════════════════════
# 报告输出（code-patterns.md 模式 5）
# ═══════════════════════════════════════════════════════════════

def print_report(all_expiring: list[dict], warning_days: int, with_price: bool = False):
    """打印汇总报告（code-patterns.md 模式 5）"""
    if not all_expiring:
        print(f"\n🎉 太好了！所有区域都没有即将到期的资源（{warning_days}天内）。")
        return

    # 按剩余天数排序
    all_expiring.sort(key=lambda x: x.get("days_left", 999))

    # 按客户分组
    by_customer = defaultdict(list)
    for r in all_expiring:
        by_customer[r["customer"]].append(r)

    # 按区域统计
    by_region = defaultdict(int)
    for r in all_expiring:
        by_region[r["region"]] += 1

    print("\n" + "=" * 80)
    print("📊 到期巡检报告" + ("（含续费询价）" if with_price else ""))
    print("=" * 80)

    # 区域统计
    print("\n📍 区域统计:")
    for region, count in sorted(by_region.items(), key=lambda x: -x[1]):
        region_cn = all_expiring[0]["region_cn"] if all_expiring else region
        for r in all_expiring:
            if r["region"] == region:
                region_cn = r["region_cn"]
                break
        print(f"   {region} ({region_cn}): {count}个资源")

    # 费用汇总（询价模式）
    if with_price:
        total_cost = sum(r.get("total_price", 0) for r in all_expiring)
        print(f"\n💰 预估续费成本: ¥{total_cost:.2f}")

    # 按客户分组详情
    for customer, resources in sorted(by_customer.items(), key=lambda x: -len(x[1])):
        print(f"\n🏢 {customer} ({len(resources)}个资源)")
        customer_total = 0.0

        for r in resources:
            urgency = "🔴" if r["days_left"] <= 3 else ("🟡" if r["days_left"] <= 7 else "🟢")

            # 额外信息
            extra_parts = []
            if "instance_type" in r:
                extra_parts.append(r["instance_type"])
            if "memory_mb" in r:
                extra_parts.append(f"{r['memory_mb']}MB")
            if "disk_size_gb" in r:
                extra_parts.append(f"{r['disk_size_gb']}GB")
            if "engine" in r:
                extra_parts.append(f"{r['engine']} {r.get('engine_version', '')}")
            if "version" in r:
                extra_parts.append(f"v{r['version']}")

            # 价格信息
            price_info = ""
            if with_price and "total_price" in r:
                price_info = f" | ¥{r['total_price']:.2f}"
                customer_total += r["total_price"]

            extra = f" | {' | '.join(extra_parts)}" if extra_parts else ""
            print(f"   {urgency} [{r['type']}] {r['name']}")
            print(f"       区域: {r['region']} ({r['region_cn']}) | "
                  f"剩余 {r['days_left']}天 | 到期 {r['expired']}{extra}{price_info}")

        if with_price and customer_total > 0:
            print(f"       💰 客户合计: ¥{customer_total:.2f}")


def output_json_report(
    all_expiring: list[dict],
    output_dir: Path,
    report_type: str,
    warning_days: int,
    regions: list[str],
    types: list[str],
    customer_filter: str,
    with_price: bool,
) -> Path:
    """JSON 报告输出（code-patterns.md 模式 5）"""
    from collections import Counter

    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_file = output_dir / f"{report_type}-{timestamp}.json"

    # 汇总统计
    type_counts = Counter(r["type"] for r in all_expiring)
    region_counts = Counter(r["region"] for r in all_expiring)

    summary = {
        "total_expiring": len(all_expiring),
        "by_type": dict(type_counts),
        "by_region": dict(region_counts),
        "urgent_7days": sum(1 for r in all_expiring if r["days_left"] <= 7),
        "urgent_3days": sum(1 for r in all_expiring if r["days_left"] <= 3),
    }

    if with_price:
        total_cost = sum(r.get("total_price", 0) for r in all_expiring)
        summary["total_estimated_cost"] = round(total_cost, 2)

    report = {
        "report_time": datetime.now().isoformat(),
        "report_type": report_type,
        "warning_days": warning_days,
        "regions_checked": regions,
        "types_checked": types,
        "customer_filter": customer_filter or None,
        "with_price": with_price,
        "summary": summary,
        "details": all_expiring,
    }

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return report_file


# ═══════════════════════════════════════════════════════════════
# CLI 入口
# ═══════════════════════════════════════════════════════════════

def parse_args():
    parser = argparse.ArgumentParser(
        description="京东云资源到期巡检 V2 — 配置驱动模式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
资源类型配置（新增类型只需修改 RESOURCE_CONFIG）:
  {', '.join(RESOURCE_CONFIG.keys())}

示例:
  %(prog)s                              # 基本巡检（14天阈值）
  %(prog)s --warning-days 7             # 7天紧急预警
  %(prog)s --with-price                 # 询价模式（额外调用 billing API）
  %(prog)s --regions cn-north-1         # 只巡检华北
  %(prog)s --types vm,rds               # 只巡检 VM 和 RDS
  %(prog)s --customer 烟台振华          # 按客户过滤
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
        default=",".join(JdcClient.DEFAULT_REGIONS),
        help=f"巡检区域，逗号分隔（默认: {','.join(JdcClient.DEFAULT_REGIONS)}）"
    )
    parser.add_argument(
        "--types",
        type=str,
        default=",".join(RESOURCE_CONFIG.keys()),
        help=f"资源类型，逗号分隔（默认: {','.join(RESOURCE_CONFIG.keys())}）"
    )
    parser.add_argument(
        "--customer",
        type=str,
        default="",
        help="按客户名称过滤（可选）"
    )
    parser.add_argument(
        "--with-price",
        action="store_true",
        help="询价模式：额外调用 billing API 获取续费价格（较慢）"
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
    project_outputs = _project_dir / "outputs" / "expiry"
    return project_outputs


def main():
    args = parse_args()

    # 解析参数
    regions = [r.strip() for r in args.regions.split(",") if r.strip()]
    types = [t.strip() for t in args.types.split(",") if t.strip()]
    unknown_types = set(types) - set(RESOURCE_CONFIG.keys())
    if unknown_types:
        print(f"❌ 未知资源类型: {', '.join(unknown_types)}")
        print(f"可用类型: {', '.join(RESOURCE_CONFIG.keys())}")
        return 1

    # 初始化客户端
    client = JdcClient()

    print(f"🔍 京东云资源到期巡检 V2")
    print(f"   预警阈值: {args.warning_days} 天内到期")
    print(f"   区域数量: {len(regions)} ({', '.join(regions)})")
    print(f"   资源类型: {', '.join(types)}")
    print(f"   询价模式: {'✅ 开启' if args.with_price else '❌ 关闭'}")
    if args.customer:
        print(f"   客户过滤: {args.customer}")
    print("=" * 80)

    # 巡检
    all_expiring = []
    for region in regions:
        print(f"\n📍 {region} ({client.get_region_name(region)})")
        region_expiring = []

        for resource_type in types:
            results = cruise_resource(
                client, resource_type, region,
                args.warning_days, args.customer,
                with_price=args.with_price,
            )
            if results:
                region_expiring.extend(results)
                print(f"   ⚠️  {RESOURCE_CONFIG[resource_type].get('type_label', resource_type)}: {len(results)} 个")

        if region_expiring:
            all_expiring.extend(region_expiring)
        else:
            print(f"   ✅ 无即将到期的资源")

    # 输出报告
    print_report(all_expiring, args.warning_days, with_price=args.with_price)

    # 保存 JSON 报告
    output_dir = get_output_dir(args)
    report_file = output_json_report(
        all_expiring, output_dir, "expiry",
        args.warning_days, regions, types,
        args.customer, args.with_price,
    )
    print(f"\n📄 详细报告已保存: {report_file}")

    return 0 if all_expiring else 1


if __name__ == "__main__":
    sys.exit(main())
