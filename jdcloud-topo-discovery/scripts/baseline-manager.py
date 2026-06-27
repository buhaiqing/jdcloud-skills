#!/usr/bin/env python3
"""CLI entry point for jdcloud-topo-discovery baseline management.

Runs topo-scan.sh to collect real infrastructure data, then archives
the output into a date-stamped baseline directory for drift detection.

> **JD Cloud 适配**:
> - JSON 响应路径: `$.result.<resources>` (小写,与阿里云 `$.Vpcs.Vpc` 不同)
> - 资源类型: jdc 自有命名 (vpc/subnet/vm/...)
> - STS AssumeRole 走 jdc sts 子命令(POST body)

Usage:
    python baseline-manager.py --output-dir ./infra-baseline/
    python baseline-manager.py --output-dir ./infra-baseline/ --region cn-north-1
    python baseline-manager.py --output-dir ./infra-baseline/ --retention-days 90 --apply-retention
    python baseline-manager.py --output-dir ./infra-baseline/ --diff  (show diff vs latest)
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# Ensure scripts/ is on sys.path for local imports
_script_dir = Path(__file__).resolve().parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

from lib.baseline_local import LocalBackend


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Manage periodic infrastructure baseline snapshots (JD Cloud)",
    )
    default_output = os.environ.get("JDC_SKILLS_RUNTIME_ROOT", "")
    if default_output:
        default_output = os.path.join(default_output, "baseline")
    else:
        _script_dir = Path(__file__).resolve().parent
        _skills_dir = _script_dir.parent.parent
        default_output = str(_skills_dir / ".runtime" / "baseline")

    parser.add_argument("--output-dir", default=default_output,
                        help="Root directory for all baselines "
                             "(default: ${JDC_SKILLS_RUNTIME_ROOT}/baseline, "
                             "or ${SKILLS_DIR}/.runtime/baseline)")
    parser.add_argument("--region", default=os.environ.get("JDC_REGION", "cn-north-1"),
                        help="JD Cloud region (default: env or cn-north-1)")
    parser.add_argument("--retention-days", type=int, default=90,
                        help="Days to keep (default: 90)")
    parser.add_argument("--apply-retention", action="store_true",
                        help="Apply retention expiry (default: mark only)")
    parser.add_argument("--diff", action="store_true",
                        help="Compare current state with latest baseline (drift detection)")
    parser.add_argument("--compare-with", default=None, metavar="YYYY-MM-DD",
                        help="With --diff, compare against this historical baseline "
                             "(default: latest). Format: YYYY-MM-DD")
    parser.add_argument("--resample", action="store_true",
                        help="Resample mode: create baseline snapshots for historical dates "
                             "by copying from an existing baseline (no cloud calls)")
    parser.add_argument("--from-baseline", default=None, metavar="YYYY-MM-DD|latest",
                        help="Source baseline date to copy from (default: latest)")
    parser.add_argument("--as-of", default=None, metavar="YYYY-MM-DD",
                        help="Single target date for resample (mode 1)")
    parser.add_argument("--as-of-range", default=None,
                        help="Date range for batch resample, format: YYYY-MM-DD:YYYY-MM-DD (modes 3/4)")
    parser.add_argument("--fill-gaps", action="store_true",
                        help="With --as-of-range, only fill missing dates (mode 4)")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing baseline directories (default: protect)")
    return parser.parse_args(argv)


def _run_topo_scan(region: str, output_dir: Path) -> dict:
    """Run topo-scan.sh and collect resource inventory.

    Returns a dict with:
      - resource_counts: {type: count}
      - resources: detailed list of resource IDs by type
      - timestamp: ISO timestamp
    """
    script_dir = Path(__file__).resolve().parent
    topo_sh = script_dir / "topo-scan.sh"

    if not topo_sh.exists():
        print(f"[ERROR] topo-scan.sh not found at {topo_sh}", file=sys.stderr)
        sys.exit(1)

    # Unique tmp dir for concurrent safety
    data_dir = Path(tempfile.mkdtemp(prefix="topo_baseline_", dir="/tmp"))
    scan_output = output_dir / ".scan_tmp"
    scan_output.mkdir(parents=True, exist_ok=True)

    env = {**os.environ}
    if "JDC_REGION" not in env:
        env["JDC_REGION"] = region

    print(f"[INFO] Running topo-scan.sh (region={region})...")
    result = subprocess.run(
        [str(topo_sh), "--mode", "brief", "--output-dir", str(scan_output),
         "--format", "both", "--region", region, "--tmp-dir", str(data_dir)],
        capture_output=True, text=True, timeout=120,
        env=env,
    )

    if result.returncode != 0:
        print(f"[WARN] topo-scan.sh exit={result.returncode}: {result.stderr[:300]}")

    # Collect resource data from unique temp dir
    resource_counts = {}
    resources = {}

    # JD Cloud naming: lowercase resource names matching CLI subcommand
    scan_files = {
        "VPC": "vpcs.json",
        "Subnet": "subnets.json",
        "CLB": "clbs.json",
        "EIP": "eips.json",
        "VM": "vms.json",
        "SecurityGroup": "sgs.json",
        "AG": "ags.json",
        "RDS": "rds.json",
        "Redis": "redis.json",
        "IAM": "iam_users.json",
        "KMS": "kms_keys.json",
    }

    for rtype, fname in scan_files.items():
        fpath = data_dir / fname
        if not fpath.exists():
            continue
        try:
            data = json.loads(fpath.read_text())
        except (json.JSONDecodeError, Exception):
            continue
        items = _extract_items(data, rtype)
        if items:
            resource_counts[rtype] = len(items)
            resources[rtype] = items

    report_path = scan_output / "report.md"
    if report_path.exists():
        print(f"[INFO] Topology report generated: {report_path}")

    # Cleanup
    shutil.rmtree(str(scan_output), ignore_errors=True)
    shutil.rmtree(str(data_dir), ignore_errors=True)

    return {
        "resource_counts": resource_counts,
        "resources": resources,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _extract_items(data: dict, rtype: str) -> list:
    """Extract resource items from JD Cloud jdc --output json responses.

    Response format: { "request_id": "...", "result": { "<resources>": [...] } }
    """
    result = data.get("result", {})
    # JD Cloud resource list paths
    path_map = {
        "VPC":            "vpcs",
        "Subnet":         "subnets",
        "CLB":            "loadBalancers",
        "EIP":            "elasticIps",
        "VM":             "instances",
        "SecurityGroup":  "networkSecurityGroups",
        "AG":             "ags",
        "RDS":            "dbInstances",
        "Redis":          "cacheInstances",
        "IAM":            "subUsers",
        "KMS":            "keys",
    }
    key = path_map.get(rtype)
    if not key:
        return []
    return result.get(key, [])


def _get_account_id() -> str:
    """Try to get current JD Cloud account ID via STS GetCallerIdentity.

    > Note: jdc CLI may not expose GetCallerIdentity directly. Falls back to env.
    """
    # jdc sts get-caller-identity is not always available; try anyway
    try:
        r = subprocess.run(
            ["jdc", "--output", "json", "sts", "get-caller-identity"],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0:
            data = json.loads(r.stdout)
            return str(data.get("result", {}).get("accountId", "unknown"))
    except Exception:
        pass
    # Fallback to env var
    return os.environ.get("JDC_ACCOUNT_ID", "unknown")


def _build_manifest(inventory: dict, region: str) -> dict:
    """Build a structured manifest from inventory data."""
    return {
        "schema_version": "1.0",
        "generator": "jdcloud-topo-discovery",
        "generator_version": "1.0.0",
        "generated_at": inventory["timestamp"],
        "account_id": _get_account_id(),
        "region": region,
        "scope": "all",
        "provider_version": "n/a",  # 京东云无官方 Provider
        "resource_count": sum(inventory["resource_counts"].values()),
        "by_type": inventory["resource_counts"],
        "resource_ids": {
            rtype: [
                item.get("instanceId")
                or item.get("vpcId")
                or item.get("subnetId")
                or item.get("loadBalancerId")
                or item.get("elasticIpId")
                or item.get("networkSecurityGroupId")
                or item.get("agId")
                or item.get("cacheInstanceId")
                or item.get("subUserName")
                or item.get("keyId")
                or item.get("networkInterfaceId")
                or ""
                for item in items
            ]
            for rtype, items in inventory["resources"].items()
        },
        "sensitive_masked": [],
        "unsupported_types": [],
        "import_ids_stable": True,
        "execution_time_ms": 0,
    }


def _compute_diff(current: dict, baseline: dict) -> list:
    """Compare current inventory vs baseline, return list of changes."""
    changes = []
    current_counts = current.get("by_type", {})
    baseline_counts = baseline.get("by_type", {})

    all_types = set(list(current_counts.keys()) + list(baseline_counts.keys()))
    for rtype in sorted(all_types):
        c = current_counts.get(rtype, 0)
        b = baseline_counts.get(rtype, 0)
        if c > b:
            changes.append(f"[ADDED] {rtype}: {b} → {c} (+{c-b})")
        elif c < b:
            changes.append(f"[REMOVED] {rtype}: {b} → {c} (-{b-c})")

    # Compare resource IDs
    current_ids = set()
    for ids in current.get("resource_ids", {}).values():
        current_ids.update(i for i in ids if i)
    baseline_ids = set()
    for ids in baseline.get("resource_ids", {}).values():
        baseline_ids.update(i for i in ids if i)

    added = current_ids - baseline_ids
    removed = baseline_ids - current_ids
    for rid in sorted(added):
        rtype = _guess_resource_type(rid)
        changes.append(f"[ADDED] {rtype} {rid}")
    for rid in sorted(removed):
        rtype = _guess_resource_type(rid)
        changes.append(f"[REMOVED] {rtype} {rid}")

    return changes


def _guess_resource_type(rid: str) -> str:
    """Guess resource type from JD Cloud ID prefix.

    京东云 ID 前缀示例:
    - vpc-xxxx       -> VPC
    - subnet-xxxx    -> Subnet
    - i-xxxx         -> VM (与阿里云 ECS 同前缀)
    - lb-xxxx / clb-xxxx -> CLB
    - fip-xxxx / eip-xxxx -> EIP
    - sg-xxxx        -> SecurityGroup
    - ag-xxxx        -> AG
    - mysql-xxxx / pg-xxxx / redis-xxxx -> RDS / Redis
    - sub-xxxx       -> IAM SubUser
    - km-xxxx        -> KMS Key
    - eni-xxxx       -> NIC
    """
    if not rid:
        return "Unknown"
    prefix = rid.split("-")[0] if "-" in rid else rid[:2]
    type_map = {
        "vpc": "VPC",
        "subnet": "Subnet",
        "i": "VM",
        "lb": "CLB",
        "clb": "CLB",
        "fip": "EIP",
        "eip": "EIP",
        "sg": "SecurityGroup",
        "ag": "AG",
        "mysql": "RDS",
        "pg": "RDS",
        "redis": "Redis",
        "mongo": "MongoDB",
        "km": "KMS",
        "eni": "NIC",
    }
    # Special case: "sub-..." is ambiguous (could be Subnet or SubUser)
    if rid.startswith("sub-") and not rid[4:4+1].isdigit():
        return "IAM"  # more likely a username
    return type_map.get(prefix, "Unknown")


def main():
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Sprint 17: --resample mode (no cloud calls, just copy/manipulate baselines)
    if args.resample:
        backend = LocalBackend(root_dir=output_dir)

        # Resolve source baseline
        src = args.from_baseline
        if not src:
            print("[ERROR] --resample requires --from-baseline (date or 'latest')")
            sys.exit(2)

        src_date = src
        if src == "latest":
            latest_dir = backend.get_latest()
            if latest_dir is None:
                print("[ERROR] No baseline found for --from-baseline=latest (run baseline-manager first)")
                sys.exit(2)
            src_date = latest_dir.name

        # Validate source exists
        if backend.get_by_date(src_date) is None:
            print(f"[ERROR] Source baseline not found: {src_date}")
            print(f"[HINT]  Available baselines: {', '.join(d.isoformat() for d in backend.list_baselines()) or '(none)'}")
            sys.exit(2)

        force = args.force

        if args.as_of:
            # Mode 1: single date copy
            dst = args.as_of
            result = backend.copy_baseline(src_date, dst, force=force)
            if result is None:
                print(f"[INFO] Target date already exists: {dst} (use --force to overwrite)")
            else:
                print(f"\n=== Resample: copied {src_date} → {dst} ===")
        elif args.as_of_range:
            # Modes 3/4: range
            parts = args.as_of_range.split(":")
            if len(parts) != 2:
                print(f"[ERROR] --as-of-range requires format YYYY-MM-DD:YYYY-MM-DD, got: {args.as_of_range}")
                sys.exit(2)
            start, end = parts[0], parts[1]

            if args.fill_gaps:
                # Mode 4: fill-gaps
                created = backend.fill_gaps(src_date, start, end, force=force)
                total_expected = len(backend.list_gaps(start, end))
                print(f"\n=== Resample (fill-gaps): src={src_date}, range={start}..{end} ===")
                print(f"  Created: {len(created)}")
                print(f"  Skipped (already exist): {total_expected - len(created)}")
                if created:
                    print(f"  Dates: {', '.join(created)}")
            else:
                # Mode 3: batch copy all dates in range
                gaps = backend.list_gaps(start, end)
                created = 0
                skipped = 0
                for d in [date.fromisoformat(start) + timedelta(days=i)
                          for i in range((date.fromisoformat(end) - date.fromisoformat(start)).days + 1)]:
                    d_str = d.isoformat()
                    result = backend.copy_baseline(src_date, d_str, force=force)
                    if result is not None:
                        created += 1
                    else:
                        skipped += 1
                print(f"\n=== Resample (batch): src={src_date}, range={start}..{end} ===")
                print(f"  Created: {created}")
                print(f"  Skipped (already exist, use --force to overwrite): {skipped}")
        else:
            print("[ERROR] --resample requires --as-of <DATE> or --as-of-range <START>:<END>")
            sys.exit(2)

        print("[SUMMARY] Resample done")
        return

    # Step 1: Run topo-scan to collect real data
    inventory = _run_topo_scan(args.region, output_dir)
    total = sum(inventory["resource_counts"].values())
    print(f"[INFO] Discovered {total} resources across {len(inventory['resource_counts'])} types")
    for rtype, count in sorted(inventory["resource_counts"].items()):
        print(f"       {rtype}: {count}")

    # Step 2: Optionally show diff vs baseline
    if args.diff:
        backend = LocalBackend(root_dir=output_dir)
        compared_with_label = "latest"
        if args.compare_with:
            baseline_dir = backend.get_by_date(args.compare_with)
            if baseline_dir is None:
                from datetime import date as _date
                try:
                    _date.fromisoformat(args.compare_with)
                except (ValueError, TypeError):
                    print(f"[ERROR] Invalid date format for --compare-with: "
                          f"'{args.compare_with}' (expected YYYY-MM-DD)")
                    sys.exit(2)
                print(f"[ERROR] No baseline found for date: {args.compare_with}")
                print(f"[HINT]  Available baselines: "
                      f"{', '.join(d.isoformat() for d in backend.list_baselines()) or '(none)'}")
                sys.exit(2)
            compared_with_label = args.compare_with
        else:
            baseline_dir = backend.get_latest()
            if baseline_dir is not None:
                compared_with_label = baseline_dir.name

        if baseline_dir is None:
            print("[INFO] No previous baseline found (this is the first one)")
        else:
            latest_manifest = baseline_dir / "manifest.json"
            if latest_manifest.exists():
                baseline_data = json.loads(latest_manifest.read_text())
                changes = _compute_diff(
                    _build_manifest(inventory, args.region),
                    baseline_data,
                )
                if changes:
                    print(f"\n=== Drift Detection: {len(changes)} changes "
                          f"(vs {compared_with_label}) ===")
                    for c in changes:
                        print(f"  {c}")
                else:
                    print(f"\n=== No drift detected (vs {compared_with_label}) ===")
        return

    # Step 3: Build and write snapshot
    snapshot_dir = output_dir / ".snapshot"
    if snapshot_dir.exists():
        shutil.rmtree(str(snapshot_dir))
    snapshot_dir.mkdir(parents=True)

    # Write manifest
    manifest = _build_manifest(inventory, args.region)
    (snapshot_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))

    # Write resource inventory as JSON (for programmatic diffing)
    (snapshot_dir / "inventory.json").write_text(
        json.dumps(inventory, indent=2, ensure_ascii=False, default=str)
    )

    # Write human-readable summary
    summary_lines = [
        "# JD Cloud Infrastructure Baseline Snapshot",
        "",
        f"**Date**: {manifest['generated_at']}",
        f"**Account**: {manifest['account_id']}",
        f"**Region**: {manifest['region']}",
        f"**Total Resources**: {manifest['resource_count']}",
        f"**Provider Version**: {manifest['provider_version']} (no official JD Cloud Provider)",
        "",
        "## Resource Counts",
        "",
        "| Type | Count |",
        "|------|:-----:|",
    ]
    for rtype, count in sorted(inventory["resource_counts"].items()):
        summary_lines.append(f"| {rtype} | {count} |")
    summary_lines.append("")
    summary_lines.append("## Resource IDs")
    summary_lines.append("")
    for rtype, ids in manifest["resource_ids"].items():
        for rid in ids:
            summary_lines.append(f"- {rtype}: `{rid}`")
    summary_lines.append("")
    summary_lines.append("---")
    summary_lines.append("*Generated by jdcloud-topo-discovery baseline-manager*")
    (snapshot_dir / "summary.md").write_text("\n".join(summary_lines))

    # Placeholder TF files for documentation purposes
    for fname in ["provider.tf", "main.tf", "outputs.tf", "variables.tf"]:
        (snapshot_dir / fname).write_text(
            f"# {fname} - placeholder for baseline {date.today()}\n"
            f"# JD Cloud has no official Terraform Provider. See manifest.json for actual resource data.\n"
        )

    # Step 4: Archive to baseline
    backend = LocalBackend(root_dir=output_dir)
    new_baseline = backend.write_baseline(snapshot_dir)

    # Step 5: Apply retention if requested
    expired = []
    if args.apply_retention:
        expired = backend.apply_retention(retention_days=args.retention_days)

    # Summary
    baselines = backend.list_baselines()
    print(f"\n[SUMMARY] Baseline written: {new_baseline.name}")
    print(f"[SUMMARY] Total resources: {total}")
    print(f"[SUMMARY] Total baselines: {len(baselines)}")
    if expired:
        print(f"[SUMMARY] Expired: {len(expired)}")

    # Clean up snapshot dir
    shutil.rmtree(str(snapshot_dir), ignore_errors=True)


if __name__ == "__main__":
    main()
