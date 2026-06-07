#!/usr/bin/env python3
"""
cruise_link.py — Phase 2: 全链路深度巡检

Usage:
    python cruise_link.py --customer 烟台振华 [--sniff-file sniff-output.json]
                          [--hours 6] [--format markdown]

If --sniff-file is provided, uses cached topology from Phase 1.
Otherwise runs Phase 1 discovery first.
"""

import sys, os, json, argparse
from datetime import datetime

_scripts_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _scripts_dir)

from lib.jdc_client import JdcClient
from lib.resource_discovery import discover_customer_resources
from analyzers import create_all


def main():
    parser = argparse.ArgumentParser(description="Phase 2: 全链路深度巡检")
    parser.add_argument("--customer", required=True, help="客户标签值")
    parser.add_argument("--sniff-file", default=None,
                        help="Phase 1 输出的 JSON 文件 (可选)")
    parser.add_argument("--hours", type=int, default=6, help="监控回溯小时数")
    parser.add_argument("--output-dir", default=None, help="输出目录")
    parser.add_argument("--json", action="store_true", help="同时输出 JSON 报告")
    args = parser.parse_args()

    client = JdcClient()
    customer = args.customer
    output_dir = args.output_dir or os.path.join(_scripts_dir, "..", "reports", "output")

    # ── Phase 1: Discovery ──
    if args.sniff_file:
        print(f"📂 从文件加载拓扑: {args.sniff_file}")
        with open(args.sniff_file, "r", encoding="utf-8") as f:
            topology_data = json.load(f)
    else:
        print(f"🔍 执行嗅探 (客户={customer})...")
        topology_data = discover_customer_resources(client, customer)
        os.makedirs(output_dir, exist_ok=True)
        date_str = datetime.now().strftime("%Y%m%d-%H%M%S")
        sniff_path = os.path.join(output_dir, f"sniff-{customer}-{date_str}.json")
        with open(sniff_path, "w", encoding="utf-8") as f:
            json.dump(topology_data, f, ensure_ascii=False, indent=2, default=str)
        print(f"  拓扑已保存: {sniff_path}")

    # ── Phase 2: Run all analyzers ──
    print(f"\n🔍 开始深度巡检 ({args.hours}h)...")
    analyzers = create_all()
    all_reports = []

    for analyzer in analyzers:
        svc = analyzer.service_name
        try:
            resources = analyzer.discover(topology_data)
            if not resources:
                print(f"  ⏭️  {svc}: 无相关资源，跳过")
                continue

            print(f"  🔄 {svc}: 发现 {len(resources)} 个资源，采集监控...")
            analyzer.query_metrics(client)
            findings = analyzer.analyze()
            report = analyzer.report()
            all_reports.append(report)

            # Print findings summary
            for f in findings:
                icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(f["severity"], "❓")
                print(f"    {icon} [{f['severity']}] {f['resource']}: {f['message']}")

        except Exception as e:
            print(f"  ❌ {svc}: 分析失败 — {e}")
            continue

    # ── Output report ──
    print(f"\n{'='*60}")
    print(f"  📋 巡检报告 ({customer})")
    print(f"{'='*60}")

    # Print table of all findings
    all_findings = []
    for report in all_reports:
        for f in report.get("findings", []):
            f["service"] = report["service"]
            all_findings.append(f)

    # Count by severity
    criticals = [f for f in all_findings if f["severity"] == "critical"]
    warnings = [f for f in all_findings if f["severity"] == "warning"]
    infos = [f for f in all_findings if f["severity"] == "info"]

    def _fmt(f: dict) -> str:
        """Format a finding with full instance context."""
        name = f.get("resource", "")
        ip = f.get("resource_ip", "")
        iid = f.get("resource_id", "")
        itype = f.get("instance_type", "")
        svc = f.get("service", "")

        rid = f"[{svc}] {name}"
        details = []
        if ip:
            details.append(ip)
        if itype:
            details.append(itype)
        if details:
            rid += f" ({', '.join(details)})"
        elif iid:
            rid += f" ({iid})"

        lines = [rid]
        lines.append(f"  问题: {f['message']}")
        act = f.get("action", "")
        if act:
            for step in act.split("; "):
                lines.append(f"  处置 → {step}")
        ops = f.get("ops_skill", "")
        if ops:
            lines.append(f"  操作入口: {ops}（需人工确认后执行）")
        return "\n".join(lines)

    print(f"\n🔴 Critical: {len(criticals)} 条")
    for f in criticals:
        print(f"\n  • {_fmt(f)}")

    print(f"\n\n🟡 Warning: {len(warnings)} 条")
    for f in warnings:
        print(f"\n  • {_fmt(f)}")

    print(f"\n\n🔵 Info: {len(infos)} 条")
    for f in infos:
        print(f"\n  • {_fmt(f)}")

    # ── Save JSON report ──
    if args.json or True:
        os.makedirs(output_dir, exist_ok=True)
        date_str = datetime.now().strftime("%Y%m%d-%H%M%S")
        report_path = os.path.join(output_dir, f"cruise-{customer}-{date_str}.json")
        report_data = {
            "customer": customer,
            "timestamp": datetime.now().isoformat(),
            "hours": args.hours,
            "summary": {
                "total_findings": len(all_findings),
                "critical": len(criticals),
                "warning": len(warnings),
                "info": len(infos),
            },
            "service_reports": all_reports,
            "all_findings": all_findings,
        }
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
        print(f"\n💾 JSON 报告已保存: {report_path}")


if __name__ == "__main__":
    main()