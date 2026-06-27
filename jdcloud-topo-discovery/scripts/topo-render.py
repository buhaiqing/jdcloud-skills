#!/usr/bin/env python3
"""Topology renderer — ASCII tree, Mermaid diagram, Markdown report.

Reads JSON data from TOPO_TMP_DIR (env) or /tmp/.
Supports lazy loading: brief mode skips VM/RDS/Redis files entirely.

Usage:
  python3 topo-render.py <output_dir> <mode:brief|detailed> <timestamp> <region> [--format ascii|mermaid|both] [--health-json path]
"""

import json
import os
import sys
import argparse
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
from mermaid_safe import (
    mermaid_escape,
    mermaid_safe_id,
    mermaid_safe_label,
    mermaid_extract_str,
    mermaid_safe_subgraph_label,
    mermaid_safe_vpc_label,
)

MERMAID_MAX_NODES = 50
parser = argparse.ArgumentParser()
parser.add_argument("output_dir")
parser.add_argument("report_mode", choices=("brief", "detailed"))
parser.add_argument("timestamp")
parser.add_argument("region_id")
parser.add_argument("--format", choices=("ascii", "mermaid", "both"), default="both")
parser.add_argument("--health-json", default=None)
args = parser.parse_args()

DATA_DIR = os.environ.get("TOPO_TMP_DIR", "/tmp")
_cache = {}


def load_json(name):
    if name in _cache:
        return _cache[name]
    path = os.path.join(DATA_DIR, name + ".json")
    if not os.path.exists(path):
        _cache[name] = {}
        return _cache[name]
    try:
        with open(path) as f:
            _cache[name] = json.load(f)
        return _cache[name]
    except Exception:
        _cache[name] = {}
        return _cache[name]


for f in ["vpcs", "subnets", "clbs", "eips", "sgs", "ags", "iam_users", "kms_keys"]:
    load_json(f)
if args.report_mode == "detailed":
    for f in ["vms", "rds", "redis"]:
        load_json(f)


def get_items(name, *keys):
    d = _cache.get(name, {})
    for k in keys:
        d = d.get(k, {}) if isinstance(d, dict) else []
    return d if isinstance(d, list) else []


vpcs = get_items("vpcs", "result", "vpcs")
subns = get_items("subnets", "result", "subnets")
clbs = get_items("clbs", "result", "loadBalancers")
eips = get_items("eips", "result", "elasticIps")
sgs = get_items("sgs", "result", "networkSecurityGroups")
ags = get_items("ags", "result", "ags")
iam = get_items("iam_users", "result", "subUsers")
kms = get_items("kms_keys", "result", "keys")
vms = get_items("vms", "result", "instances") if args.report_mode == "detailed" else []
rds = get_items("rds", "result", "dbInstances") if args.report_mode == "detailed" else []
redis_items = (
    get_items("redis", "result", "cacheInstances") if args.report_mode == "detailed" else []
)

health = {}
if args.health_json and os.path.exists(args.health_json):
    try:
        with open(args.health_json) as f:
            health = json.load(f)
    except Exception:
        pass


def health_icon(rid, default="✅"):
    h = health.get(rid, {})
    lvl = h.get("level", "")
    if lvl == "CRITICAL":
        return "🔴"
    if lvl == "WARNING" or h.get("z_score", 0) > 2.0:
        return "🟡"
    return default


# Build subnet resource map
sn_map = {}
for s in subns:
    sid = s.get("subnetId", "")
    sn_map[sid] = {
        "name": s.get("subnetName", ""),
        "cidr": s.get("addressPrefix", ""),
        "az": s.get("az", ""),
        "vms": [],
        "clbs": [],
        "rds": [],
        "redis": [],
    }
for v in vms:
    sn = v.get("subnetId", "")
    if sn in sn_map:
        sn_map[sn]["vms"].append(v)
for clb in clbs:
    sn = clb.get("subnetId", "")
    if sn in sn_map:
        sn_map[sn]["clbs"].append(clb)
for d in rds:
    sn = d.get("subnetId", "")
    if sn in sn_map:
        sn_map[sn]["rds"].append(d)
for r in redis_items:
    sn = r.get("subnetId", "")
    if sn in sn_map:
        sn_map[sn]["redis"].append(r)

total_res = sum(
    len(sn["vms"]) + len(sn["clbs"]) + len(sn["rds"]) + len(sn["redis"]) for sn in sn_map.values()
)
large = total_res > MERMAID_MAX_NODES

pv = vpcs[0] if vpcs else {}
vpc_id = pv.get("vpcId", "")
vpc_name = pv.get("vpcName", "") or vpc_id
proj = os.getenv("TOPO_PROJECT_NAME", vpc_name)
pname = "\u8be6\u7ec6" if args.report_mode == "detailed" else "\u7b80\u62a5"


def res_line(it, ind="    \u2502  \u251c\u2500 "):
    h = health_icon(
        it.get("instanceId", "")
        or it.get("loadBalancerId", "")
        or it.get("cacheInstanceId", "")
        or it.get("instanceId", "")
        or ""
    )
    nm = (
        it.get("instanceName", "")
        or it.get("loadBalancerName", "")
        or it.get("cacheInstanceName", "")
        or ""
    )
    ip = it.get("privateIpAddress", "") or mermaid_extract_str(it, "privateIp.privateIpAddress")
    eip = mermaid_extract_str(it, "privateIp.elasticIpAddress")
    if eip:
        return f"{ind}{h} {nm}: {ip} (EIP: {eip})"
    if ip:
        return f"{ind}{h} {nm}: {ip}"
    return f"{ind}{h} {nm}"


def render_ascii():
    lines = [
        f"# {proj} - \u4eac\u4e1c\u4e91\u7f51\u7edc\u62d3\u6251\u4e0e\u8d44\u6e90\u6e05\u5355",
        f"> \u751f\u6210\u65f6\u95f4: {args.timestamp} | \u533a\u57df: {args.region_id} | \u6a21\u5f0f: {pname}",
        "---",
        "## \U0001f3d7\ufe0f VPC \u7f51\u7edc\u62d3\u6251",
        "",
        f"**VPC**: {vpc_name} ({vpc_id})  **CIDR**: {pv.get('addressPrefix', '')}",
        "```",
    ]
    for _sid, sn in sn_map.items():
        lines.append(f"\u2514\u2500 \u5b50\u7f51: {sn['name']} ({sn['cidr']}) ~ {sn['az']}")
        items = sn["vms"] + sn["clbs"] + sn["rds"] + sn["redis"]
        if not items:
            lines.append("\u2502  \u2514\u2500 (\u9884\u7559)")
        else:
            for idx, it in enumerate(items):
                p = "\u2502  \u2514\u2500 " if idx == len(items) - 1 else "\u2502  \u251c\u2500 "
                lines.append(res_line(it, f"   {p}"))
    lines.append("```")
    if len(vpcs) > 1:
        o = ", ".join(v.get("vpcId", "") for v in vpcs[1:])
        lines.append(f"\n> \U0001f4a1 \u68c0\u6d4b\u5230 {len(vpcs)} VPC\u3002\u5176\u4ed6: {o}")
    if health:
        lines.extend(
            [
                "---",
                "## \U0001f49a \u5065\u5eb7\u603b\u89c8",
                "",
                "| \u8d44\u6e90 | \u7c7b\u578b | \u5065\u5eb7 | \u5f02\u5e38\u8bc4\u5206 |",
                "|---|---|---|---|",
            ]
        )
        for rid, h in health.items():
            e = (
                "\U0001f534"
                if h.get("level", "") == "CRITICAL"
                else ("\U0001f7e1" if h.get("level", "") == "WARNING" else "\u2705")
            )
            lines.append(f"| {rid} | {h.get('type', '')} | {e} | {h.get('z_score', 0)} |")
    lines.extend(
        [
            "---",
            "## \U0001f4ca \u8d44\u6e90\u7edf\u8ba1",
            "| \u7c7b\u578b | \u6570\u91cf |",
            "|---|---|",
            f"| VPC | {len(vpcs)} |",
            f"| Subnet | {len(subns)} |",
            f"| VM | {len(vms)} |",
            f"| CLB | {len(clbs)} |",
            f"| EIP | {len(eips)} |",
            f"| AG | {len(ags)} |",
            f"| SecurityGroup | {len(sgs)} |",
            f"| IAM | {len(iam)} |",
            f"| KMS | {len(kms)} |",
        ]
    )
    if args.report_mode == "detailed":
        lines.extend([f"| RDS | {len(rds)} |", f"| Redis | {len(redis_items)} |"])
    lines.extend(["", "---", "> jdcloud-topo-discovery | READ-ONLY"])
    return "\n".join(lines)


def render_mermaid():
    lines = [
        "```mermaid",
        "graph TB",
        f"    subgraph VPC[{mermaid_safe_vpc_label(vpc_name, vpc_id)}]",
        "        style VPC fill:#e8f4fd,stroke:#3b82f6",
    ]
    for _sid, sn in sn_map.items():
        ss = mermaid_safe_id(f"sub_{_sid}")
        sl = mermaid_safe_subgraph_label(sn["name"], sn["cidr"], sn.get("az", ""))
        lines.append(f"    subgraph {ss}[{sl}]")
        items = sn["vms"] + sn["clbs"] + sn["rds"] + sn["redis"]
        if large and len(items) > MERMAID_MAX_NODES:
            pts = []
            if sn["vms"]:
                pts.append(f"VM x{len(sn['vms'])}")
            if sn["clbs"]:
                pts.append(f"CLB x{len(sn['clbs'])}")
            if sn["rds"]:
                pts.append(f"RDS x{len(sn['rds'])}")
            if sn["redis"]:
                pts.append(f"Redis x{len(sn['redis'])}")
            lb = mermaid_safe_label(" | ".join(pts) if pts else "(\u9884\u7559)")
            lines.append(f"        {mermaid_safe_id(f'agg_{_sid}')}[{lb}]")
        else:
            for it in items:
                rid = mermaid_safe_id(
                    f"res_{it.get('instanceId', '') or it.get('loadBalancerId', '') or it.get('cacheInstanceId', '') or it.get('name', '')}"
                )
                lb = f"{health_icon(it.get('instanceId', '') or it.get('loadBalancerId', '') or it.get('cacheInstanceId', '') or '', chr(0x2705))} {mermaid_escape(it.get('instanceName', '') or it.get('loadBalancerName', '') or it.get('cacheInstanceName', '') or '')}"
                ip = it.get("privateIpAddress", "") or mermaid_extract_str(
                    it, "privateIp.privateIpAddress"
                )
                if ip:
                    lb += f"<br/>{mermaid_escape(ip)}"
                lines.append(f"        {rid}[{mermaid_safe_label(lb)}]")
            if not items:
                lines.append("        empty_spot[&#40;\u9884\u7559&#41;]")
        lines.append("    end")
    for clb in clbs:
        ea = mermaid_extract_str(clb, "privateIp.elasticIpAddress")
        if ea:
            eid = mermaid_safe_id(f"eip_{ea}")
            cn = clb.get("loadBalancerId", "") or clb.get("loadBalancerName", "")
            cid = mermaid_safe_id(f"res_{cn}")
            lines.append(f"    {eid}((&#34;{ea}&#34;)) --> {cid}")
    lines.extend(["    end", "```"])
    return "\n".join(lines)


os.makedirs(args.output_dir, exist_ok=True)
ascii = render_ascii()
mermaid = render_mermaid()

if args.format in ("ascii", "both"):
    p = os.path.join(args.output_dir, "report.md")
    content = (
        ascii + "\n\n## \U0001f3a8 \u62d3\u6251\u56fe\n\n" + mermaid + "\n"
        if args.format == "both"
        else ascii
    )
    with open(p, "w") as f:
        f.write(content)

if args.format == "mermaid":
    p = os.path.join(args.output_dir, "topology.mermaid.md")
    with open(p, "w") as f:
        f.write(mermaid)

LINT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mermaid-lint", "lint.mjs")
LDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mermaid-lint")


def run_lint(fp):
    if not os.path.exists(LINT):
        return
    if not os.path.exists(os.path.join(LDIR, "node_modules")):
        return
    try:
        r = subprocess.run(["node", LINT, fp], capture_output=True, text=True, timeout=30, cwd=LDIR)
        if r.returncode != 0:
            print(f"[LINT] Errors in {fp}:", r.stderr or r.stdout)
    except Exception:
        pass


for fp in [
    os.path.join(args.output_dir, "report.md"),
    os.path.join(args.output_dir, "topology.mermaid.md"),
]:
    if os.path.exists(fp):
        run_lint(fp)
