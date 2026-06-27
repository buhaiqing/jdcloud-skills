#!/usr/bin/env python3
"""
资源账单分析脚本 — 基于 Code Patterns 模式 3

功能：
  1. 先运行到期巡检，获取即将到期资源
  2. 对每项资源调用 billing API 询价（续费 1 个月）
  3. 输出预估续费成本，按客户分组

用法:
    python billing_analysis.py                              # 分析 14 天内到期资源
    python billing_analysis.py --warning-days 30            # 分析 30 天内到期资源
    python billing_analysis.py --customer 烟台振华          # 只分析指定客户
    python billing_analysis.py --renew-months 3             # 预估 3 个月续费成本
"""

import argparse
import json
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# 添加 lib 路径
_script_dir = Path(__file__).resolve().parent
_project_dir = _script_dir.parent
sys.path.insert(0, str(_project_dir))

from lib.jdc_client import JdcClient


# ═══════════════════════════════════════════════════════════════
# 资源配置（复用 expiry_cruise_v2.py 的配置）
# ═══════════════════════════════════════════════════════════════

RESOURCE_CONFIG = {
    "vm": {
        "api": "describe_vms",
        "list_key": "instances",
        "id_key": "instanceId",
        "name_key": "instanceName",
        "charge_path": ["charge", "chargeExpiredTime"],
        "type_label": "VM",
    },
    "redis": {
        "api": "describe_redis",
        "list_key": "cacheInstances",
        "id_key": "cacheInstanceId",
        "name_key": "cacheInstanceName",
        "charge_path": ["charge", "chargeExpiredTime"],
        "type_label": "Redis",
    },
    "rds": {
        "api": "describe_rds",
        "list_key": "dbInstances",
        "id_key": "instanceId",
        "name_key": "instanceName",
        "charge_path": ["charge", "chargeExpiredTime"],
        "type_label_fn": lambda item: f"RDS-{item.get('engine', 'MySQL')}",
    },
    "clb": {
        "api": "describe_load_balancers",
        "list_key": "loadBalancers",
        "id_key": "loadBalancerId",
        "name_key": "loadBalancerName",
        "charge_path": ["charge", "chargeExpiredTime"],
        "type_label": "CLB",
    },
}


# ═══════════════════════════════════════════════════════════════
# 核心逻辑：到期巡检 + 批量询价（code-patterns.md 模式 3）
# ═══════════════════════════════════════════════════════════════

def get_expiring_resources(
    client: JdcClient,
    resource_type: str,
    region: str,
    warning_days: int,
    customer_filter: str = "",
) -> list[dict]:
    """获取即将到期资源列表（简化版 expiry_cruise 逻辑）"""
    cfg = RESOURCE_CONFIG.get(resource_type)
    if not cfg:
        return []

    api_method = getattr(client, cfg["api"], None)
    if not api_method:
        return []

    items = api_method(region)
    results = []

    for item in items:
        # 提取到期时间
        charge_data = item
        for key in cfg["charge_path"]:
            charge_data = charge_data.get(key, {}) if isinstance(charge_data, dict) else {}
        expired_time = charge_data if isinstance(charge_data, str) else ""

        days = client.get_expired_days(expired_time)
        if days < 0 or days > warning_days:
            continue

        customer = client.get_tag_value(item.get("tags"), "客户")
        if customer_filter and customer != customer_filter:
            continue

        type_label = cfg.get("type_label") or cfg.get("type_label_fn", lambda x: resource_type.upper())(item)

        results.append({
            "type": type_label,
            "name": item.get(cfg["name_key"], ""),
            "id": item.get(cfg["id_key"], ""),
            "resource_type_key": resource_type,  # 用于后续询价
            "region": region,
            "region_cn": client.get_region_name(region),
            "days_left": days,
            "customer": customer,
            "expired": expired_time[:10] if expired_time else "",
        })

    return results


def batch_price_inquiry(
    client: JdcClient,
    resources: list[dict],
    renew_months: int = 1,
    sleep_interval: float = 0.5,
) -> list[dict]:
    """批量询价（code-patterns.md 模式 3 的 batch_price_inquiry 实现）

    对到期资源列表逐一询价，计算预估续费成本。

    Args:
        client: JdcClient 实例
        resources: 资源列表（每项含 resource_type_key/id/region）
        renew_months: 续费月数
        sleep_interval: API 调用间隔（避免限流）

    Returns:
        询价结果列表，按 total_price 降序排列
    """
    results = []
    total = len(resources)

    for idx, r in enumerate(resources, 1):
        print(f"\r💰 询价进度: {idx}/{total} ({r['type']} {r['name'][:20]}...)", end="", flush=True)

        try:
            price_info = client.price_inquiry_for_resource(
                resource_type=r["resource_type_key"],
                resource_id=r["id"],
                region=r["region"],
                renew_months=renew_months,
            )

            if "error" in price_info:
                r["price_error"] = price_info["error"]
            else:
                # 合并价格信息
                r["original_price"] = price_info.get("original_price", 0)
                r["discount_price"] = price_info.get("discount_price", 0)
                r["total_price"] = price_info.get("total_price", 0)
                r["renew_months"] = renew_months

            results.append(r)

        except Exception as e:
            r["price_error"] = str(e)
            results.append(r)

        # 避免 API 限流
        if idx < total:
            time.sleep(sleep_interval)

    print()  # 换行

    # 按价格降序排列
    results.sort(key=lambda x: x.get("total_price", 0), reverse=True)
    return results


# ═══════════════════════════════════════════════════════════════
# 报告输出（code-patterns.md 模式 5）
# ═══════════════════════════════════════════════════════════════

def print_billing_report(results: list[dict], renew_months: int, warning_days: int):
    """打印账单分析报告"""
    if not results:
        print(f"\n🎉 未来 {warning_days} 天内无到期资源，无需预估续费成本。")
        return

    # 按客户分组
    by_customer = defaultdict(list)
    for r in results:
        by_customer[r["customer"]].append(r)

    # 计算汇总
    total_cost = sum(r.get("total_price", 0) for r in results)
    total_discount = sum(r.get("original_price", 0) - r.get("total_price", 0) for r in results)

    print("\n" + "=" * 80)
    print(f"💰 资源续费成本预估（续费 {renew_months} 个月）")
    print("=" * 80)
    print("\n📊 汇总:")
    print(f"   资源总数: {len(results)} 个")
    print(f"   预估原价: ¥{sum(r.get('original_price', 0) for r in results):.2f}")
    print(f"   预估实付: ¥{total_cost:.2f}")
    if total_discount > 0:
        print(f"   优惠金额: ¥{total_discount:.2f} ({total_discount/total_cost*100:.1f}%)")

    # 按客户分组详情
    for customer, resources in sorted(by_customer.items(), key=lambda x: -sum(r.get("total_price", 0) for r in x[1])):
        customer_cost = sum(r.get("total_price", 0) for r in resources)
        customer_original = sum(r.get("original_price", 0) for r in resources)

        print(f"\n🏢 {customer}")
        print(f"   资源数: {len(resources)} | 实付: ¥{customer_cost:.2f}")
        if customer_original > customer_cost:
            print(f"   原价: ¥{customer_original:.2f} | 优惠: ¥{customer_original - customer_cost:.2f}")

        for r in resources:
            urgency = "🔴" if r["days_left"] <= 3 else ("🟡" if r["days_left"] <= 7 else "🟢")
            price_info = f"¥{r['total_price']:.2f}" if "total_price" in r else f"询价失败: {r.get('price_error', '')}"

            print(f"   {urgency} [{r['type']}] {r['name'][:40]}")
            print(f"       {r['region']} | 剩余 {r['days_left']} 天 | {price_info}")


def save_billing_report(
    results: list[dict],
    output_dir: Path,
    renew_months: int,
    warning_days: int,
    regions: list[str],
) -> Path:
    """保存账单分析 JSON 报告"""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_file = output_dir / f"billing-{timestamp}.json"

    # 客户维度汇总
    by_customer = defaultdict(lambda: {"resources": [], "total_cost": 0, "total_original": 0})
    for r in results:
        c = r.get("customer", "未知")
        by_customer[c]["resources"].append(r)
        by_customer[c]["total_cost"] += r.get("total_price", 0)
        by_customer[c]["total_original"] += r.get("original_price", 0)

    report = {
        "report_time": datetime.now().isoformat(),
        "report_type": "billing_analysis",
        "warning_days": warning_days,
        "renew_months": renew_months,
        "regions_checked": regions,
        "summary": {
            "total_resources": len(results),
            "total_cost": round(sum(r.get("total_price", 0) for r in results), 2),
            "total_original": round(sum(r.get("original_price", 0) for r in results), 2),
            "customer_count": len(by_customer),
        },
        "by_customer": {k: {
            "resource_count": len(v["resources"]),
            "total_cost": round(v["total_cost"], 2),
            "total_original": round(v["total_original"], 2),
            "discount": round(v["total_original"] - v["total_cost"], 2),
        } for k, v in by_customer.items()},
        "details": results,
    }

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return report_file


# ═══════════════════════════════════════════════════════════════
# CLI 入口
# ═══════════════════════════════════════════════════════════════

def parse_args():
    parser = argparse.ArgumentParser(
        description="资源账单分析 — 基于 Code Patterns 模式 3",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
本脚本演示 code-patterns.md 中的两个核心模式：
  1. 模式 1 (配置驱动): 用 RESOURCE_CONFIG 统一处理多种资源类型
  2. 模式 3 (多步骤询价): renewal.query-instance → billing.calculate-total-price

示例:
  %(prog)s                              # 分析 14 天内到期资源
  %(prog)s --warning-days 30            # 分析 30 天内到期资源
  %(prog)s --customer 烟台振华          # 只分析指定客户
  %(prog)s --renew-months 3             # 预估 3 个月续费成本
        """
    )
    parser.add_argument(
        "--warning-days",
        type=int,
        default=14,
        help="分析未来 N 天内到期的资源（默认 14 天）"
    )
    parser.add_argument(
        "--regions",
        type=str,
        default=",".join(JdcClient.DEFAULT_REGIONS),
        help=f"区域列表（默认: {','.join(JdcClient.DEFAULT_REGIONS)}）"
    )
    parser.add_argument(
        "--types",
        type=str,
        default=",".join(RESOURCE_CONFIG.keys()),
        help=f"资源类型（默认: {','.join(RESOURCE_CONFIG.keys())}）"
    )
    parser.add_argument(
        "--customer",
        type=str,
        default="",
        help="按客户名称过滤"
    )
    parser.add_argument(
        "--renew-months",
        type=int,
        default=1,
        help="续费月数（默认 1 个月）"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="",
        help="输出目录（默认 ~/.jdcloud-routines-ops/outputs/billing）"
    )
    return parser.parse_args()


def get_output_dir(args) -> Path:
    if args.output_dir:
        return Path(args.output_dir).resolve()
    home_outputs = Path.home() / ".jdcloud-routines-ops" / "outputs" / "billing"
    if home_outputs.exists() or os.access(Path.home(), os.W_OK):
        return home_outputs
    return Path(_project_dir) / "outputs" / "billing"


def main():
    args = parse_args()

    regions = [r.strip() for r in args.regions.split(",") if r.strip()]
    types = [t.strip() for t in args.types.split(",") if t.strip()]

    # 初始化客户端
    client = JdcClient()

    print("💰 资源账单分析")
    print(f"   分析范围: 未来 {args.warning_days} 天内到期的资源")
    print(f"   续费预估: {args.renew_months} 个月")
    print(f"   区域: {', '.join(regions)}")
    print(f"   资源类型: {', '.join(types)}")
    if args.customer:
        print(f"   客户过滤: {args.customer}")
    print("=" * 80)

    # 阶段 1: 到期巡检
    print("\n📍 阶段 1: 到期巡检")
    all_expiring = []
    for region in regions:
        for resource_type in types:
            results = get_expiring_resources(
                client, resource_type, region,
                args.warning_days, args.customer
            )
            if results:
                all_expiring.extend(results)

    if not all_expiring:
        print(f"\n✅ 未来 {args.warning_days} 天内无到期资源。")
        return 0

    print(f"   发现 {len(all_expiring)} 个即将到期的资源")

    # 阶段 2: 批量询价（code-patterns.md 模式 3）
    print(f"\n💰 阶段 2: 批量询价（{args.renew_months} 个月续费成本）")
    results = batch_price_inquiry(client, all_expiring, args.renew_months)

    # 输出报告
    print_billing_report(results, args.renew_months, args.warning_days)

    # 保存 JSON
    output_dir = get_output_dir(args)
    report_file = save_billing_report(results, output_dir, args.renew_months, args.warning_days, regions)
    print(f"\n📄 详细报告已保存: {report_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
