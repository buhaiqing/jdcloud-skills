#!/usr/bin/env python3
"""
cruise_sniff.py — Phase 1: 嗅探 + 拓扑初判

Usage:
    python cruise_sniff.py --customer 烟台振华 [--region cn-north-1]

Output:
    - Prints topology preview to stdout (Markdown)
    - Saves JSON to reports/output/sniff-{customer}-{date}.json
    - If resources need confirmation, exits with needs_confirmation flag
"""

import sys, os, json, argparse
from datetime import datetime

_scripts_dir = os.path.dirname(os.path.abspath(__file__))
_project_dir = os.path.join(_scripts_dir, "..")
sys.path.insert(0, _project_dir)

from lib.jdc_client import JdcClient
from lib.resource_discovery import discover_customer_resources


def main():
    parser = argparse.ArgumentParser(description="Phase 1: 资源嗅探与拓扑初判")
    parser.add_argument("--customer", required=True, help="客户标签值 (如 烟台振华)")
    parser.add_argument("--region", nargs="+", default=None,
                        help="区域列表 (默认: 全部)")
    parser.add_argument("--output-dir", default=None,
                        help="输出目录 (默认: reports/output)")
    args = parser.parse_args()

    client = JdcClient()
    regions = args.region
    customer = args.customer
    output_dir = args.output_dir or os.path.join(_scripts_dir, "..", "..", "reports", "output")

    print(f"\n🔍 嗅探阶段: 客户={customer}, 区域={regions or '全部'}")
    print("=" * 60)

    result = discover_customer_resources(client, customer, regions)
    cls = result["classification"]
    topology = result["topology"]

    # ── Print topology preview ──
    print(f"\n🌐 拓扑初判")
    print(f"  VPC 数量: {len(topology['vpcs'])}")
    for vpc_id, info in topology["vpcs"].items():
        print(f"    {info['name']} ({info['cidr']}): {len(info['vms'])} VMs, {len(info['subnets'])} 子网")

    print(f"\n📦 资源分布")
    customer_vms = [r for r in cls["resources"] if r.get("mode") != "unknown"]
    print(f"  已分类: {len(customer_vms)} 个资源")
    modes = {}
    for r in cls["resources"]:
        modes[r["mode"]] = modes.get(r["mode"], 0) + 1
    for m, c in modes.items():
        print(f"    {m}: {c} 个")

    # ── Print classification ──
    print(f"\n🏷️  部署模式分类")
    for r in cls["resources"]:
        conf_bar = "█" * int(r["confidence"] * 20)
        print(f"  [{conf_bar}] {r.get('name',''):35s} {r['mode']:15s} 置信度={r['confidence']:.0%} 原因:{r['reason']}")

    # ── Needs confirmation? ──
    needs = cls.get("needs_confirmation", [])
    if needs:
        print(f"\n⚠️  以下 {len(needs)} 个资源需要人工确认:")
        for r in needs:
            print(f"  ❓ {r.get('name','')} ({r.get('id','')}) — {r['reason']}")
        print("\n  请人工确认后，重新运行或跳过确认继续 Phase 2。")
        exit_code = 1
    else:
        print(f"\n✅ 所有资源已自动分类，可直接进入 Phase 2。")
        exit_code = 0

    # ── Save JSON ──
    os.makedirs(output_dir, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = os.path.join(output_dir, f"sniff-{customer}-{date_str}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n💾 JSON 已保存: {out_path}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())