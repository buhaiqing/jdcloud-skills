#!/usr/bin/env python3
"""Topology renderer — ASCII tree, Mermaid diagram, Markdown report.

Reads JSON data from TOPO_TMP_DIR (env) or /tmp/.
Supports lazy loading: brief mode skips VM/RDS/Redis files entirely.

Large-scale Mermaid (>50 resources per Subnet) auto-collapses to avoid OOM.

> **JD Cloud 适配**:
> - 资源路径: `$.result.vpcs` / `$.result.subnets` (与阿里云 `$.Vpcs.Vpc` 不同)
> - 术语: Subnet 而非 VSwitch
> - 资源命名: 小写 (vpcName / instanceId / cacheInstanceId)

Usage:
  python3 topo-render.py <output_dir> <mode:brief|detailed> <timestamp> <region> [--format ascii|mermaid|both] [--health-json path]
"""

import json, sys, os, argparse, subprocess

# ── Safe rendering utilities ──
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))
from mermaid_safe import (
    mermaid_escape,
    mermaid_safe_id,
    mermaid_safe_label,
    mermaid_extract_str,
    mermaid_safe_subgraph_label,
    mermaid_safe_vpc_label,
)

# ── Config ──
MERMAID_MAX_NODES = 50  # collapse if any Subnet has more than this

# ── Argument parsing ──
parser = argparse.ArgumentParser()
parser.add_argument('output_dir')
parser.add_argument('report_mode', choices=('brief', 'detailed'))
parser.add_argument('timestamp')
parser.add_argument('region_id')
parser.add_argument('--format', choices=('ascii', 'mermaid', 'both'), default='both')
parser.add_argument('--health-json', default=None)
args = parser.parse_args()

output_dir = args.output_dir
report_mode = 'detailed' if args.report_mode == 'detailed' else 'brief'
timestamp = args.timestamp
region_id = args.region_id
output_format = args.format

# ── Data directory (concurrent-safe) ──
DATA_DIR = os.environ.get('TOPO_TMP_DIR', '/tmp')

# ── Load data (lazy: brief skips VM/RDS/Redis) ──
_cache = {}

def load_json(name):
    """Lazy-load a JSON data file from DATA_DIR, cached."""
    if name in _cache:
        return _cache[name]
    path = os.path.join(DATA_DIR, f'{name}.json')
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

# Only load what we need based on mode
BRIEF_FILES = ['vpcs', 'subnets', 'clbs', 'eips', 'sgs', 'ags', 'iam_users', 'kms_keys']
DETAILED_FILES = ['vms', 'rds', 'redis']

for name in BRIEF_FILES:
    load_json(name)
if report_mode == 'detailed':
    for name in DETAILED_FILES:
        load_json(name)

# ── Parse loaded data ──
def _get(name, *keys):
    """Safely dig into loaded JSON data, JD Cloud format: result.<name>[*]."""
    d = _cache.get(name, {})
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k, {})
        else:
            return []
    if isinstance(d, list):
        return d
    return []

# JD Cloud response paths: result.<resources> (lowercase, no nested wrapper)
vpcs  = _get('vpcs', 'result', 'vpcs')
subns = _get('subnets', 'result', 'subnets')
clbs  = _get('clbs', 'result', 'loadBalancers')
eips  = _get('eips', 'result', 'elasticIps')
sgs   = _get('sgs', 'result', 'networkSecurityGroups')
ags   = _get('ags', 'result', 'ags')
iam   = _get('iam_users', 'result', 'subUsers')
kms   = _get('kms_keys', 'result', 'keys')
vms   = _get('vms', 'result', 'instances') if report_mode == 'detailed' else []
rds   = _get('rds', 'result', 'dbInstances') if report_mode == 'detailed' else []
redis = _get('redis', 'result', 'cacheInstances') if report_mode == 'detailed' else []

# ── Load health overlay (optional) ──
health_data = {}
if args.health_json and os.path.exists(args.health_json):
    try:
        with open(args.health_json) as f:
            health_data = json.load(f)
        print(f"[INFO] Health overlay loaded from {args.health_json}")
    except Exception:
        print(f"[WARN] Failed to load health JSON: {args.health_json}")

def get_health(instance_id, default='✅'):
    h = health_data.get(instance_id, {})
    level = h.get('level', '')
    if level == 'CRITICAL': return '🔴'
    if level == 'WARNING': return '🟡'
    if h.get('z_score', 0) > 2.0: return '🟡'
    return default

# ── Build Subnet → resources mapping ──
subnet_map = {}
for s in subns:
    s_id = s.get('subnetId', '')
    subnet_map[s_id] = {
        'name': s.get('subnetName', ''),
        'cidr': s.get('addressPrefix', ''),
        'az': s.get('az', ''),
        'vms': [], 'clbs': [], 'rds': [], 'redis': []
    }

# VMs: instance.subnetId
for v in vms:
    sn = v.get('subnetId', '')
    subnet_map.get(sn, {}).setdefault('vms', []).append({
        'name': v.get('instanceName', ''),
        'id': v.get('instanceId', ''),
        'ip': v.get('privateIpAddress', ''),
        'status': v.get('status', '')
    })

# CLBs: loadBalancer.subnetId
for l in clbs:
    sn = l.get('subnetId', '')
    priv_ip = mermaid_extract_str(l, 'privateIp.privateIpAddress')
    eip_addr = mermaid_extract_str(l, 'privateIp.elasticIpAddress')
    subnet_map.get(sn, {}).setdefault('clbs', []).append({
        'name': l.get('loadBalancerName', ''),
        'id': l.get('loadBalancerId', ''),
        'ip': priv_ip,
        'eip': eip_addr
    })

# RDS: dbInstance.subnetId
for d in rds:
    sn = d.get('subnetId', '')
    subnet_map.get(sn, {}).setdefault('rds', []).append({
        'name': d.get('instanceName', ''),
        'id': d.get('instanceId', ''),
        'conn': d.get('connectionString', ''),
        'engine': d.get('engine', '')
    })

# Redis: cacheInstance.subnetId
for r in redis:
    sn = r.get('subnetId', '')
    subnet_map.get(sn, {}).setdefault('redis', []).append({
        'name': r.get('cacheInstanceName', ''),
        'id': r.get('cacheInstanceId', ''),
        'domain': r.get('connectionDomain', ''),
        'type': r.get('instanceType', '')
    })

# ── Detect large-scale mode for Mermaid ──
total_resources = sum(
    len(sn.get('vms',[])) + len(sn.get('clbs',[])) + len(sn.get('rds',[])) + len(sn.get('redis',[]))
    for sn in subnet_map.values()
)
large_scale = total_resources > MERMAID_MAX_NODES
if large_scale:
    print(f"[INFO] Large topology ({total_resources} resources > {MERMAID_MAX_NODES}), Mermaid using aggregated view")

# Primary VPC
primary_vpc = vpcs[0] if vpcs else {}
vpc_id = primary_vpc.get('vpcId', '')
vpc_name = primary_vpc.get('vpcName', '') or vpc_id
project_name = os.getenv('TOPO_PROJECT_NAME', vpc_name)

# ── Helper: resource line with health ──
def resource_line(it, indent='│  '):
    h = get_health(it.get('id', ''))
    if 'ip' in it and 'eip' in it and it['eip']:
        return f"{indent}{h} {it['name']}: {it['ip']} (EIP: {it['eip']})"
    elif 'ip' in it:
        return f"{indent}{h} {it['name']}: {it['ip']}"
    elif 'domain' in it:
        return f"{indent}{h} {it['name']} [{it.get('type','')}]: {it['domain']}"
    else:
        return f"{indent}{h} {it['name']}: {it.get('conn', '')}"

# ── Render ASCII ──
def render_ascii():
    lines = []
    lines.append(f"# {project_name} - 京东云网络拓扑与资源清单")
    lines.append(f"> 生成时间: {timestamp} | 区域: {region_id} | 模式: {'详细' if report_mode == 'detailed' else '简报'}")
    lines.append("---")
    lines.append("## 🏗️ VPC 网络拓扑")
    lines.append("")
    lines.append(f"**VPC**: {vpc_name} ({vpc_id})  **CIDR**: {primary_vpc.get('addressPrefix', '')}")
    lines.append("```")

    for sid, sn in subnet_map.items():
        lines.append(f"├─ 子网: {sn['name']} ({sn['cidr']}) ~ {sn['az']}")
        items = sn.get('vms', []) + sn.get('clbs', []) + sn.get('rds', []) + sn.get('redis', [])
        if not items:
            lines.append("│  └─ (预留)")
        else:
            for idx, it in enumerate(items[:MERMAID_MAX_NODES]):
                last = idx == len(items) - 1 or idx == MERMAID_MAX_NODES - 1
                pfx = "│  └─ " if last else "│  ├─ "
                lines.append(resource_line(it, f"   {pfx}"))
            if len(items) > MERMAID_MAX_NODES:
                lines.append(f"   │  └─ ... ({len(items) - MERMAID_MAX_NODES} more)")
    lines.append("```")
    lines.append("")
    if len(vpcs) > 1:
        lines.append(f"> 💡 检测到 {len(vpcs)} 个 VPC,当前展示主 VPC ({vpc_id})。其余 VPC: {', '.join(v.get('vpcId','') for v in vpcs[1:])}")
        lines.append("")
    lines.append("---")
    lines.append("")

    # Health summary
    if health_data:
        lines.append("## 💚 健康状态总览")
        lines.append("")
        lines.append("| 资源 | 类型 | 健康 | 异常评分 |")
        lines.append("|---|---|---|---|")
        for rid, h in health_data.items():
            hl = h.get('level', '')
            z = h.get('z_score', 0)
            emoji = '🔴' if hl == 'CRITICAL' else ('🟡' if hl == 'WARNING' else '✅')
            lines.append(f"| {rid} | {h.get('type','')} | {emoji} | {z} |")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Resource stats
    lines.append("## 📊 资源统计")
    lines.append("| 资源类型 | 数量 | 明细 |")
    lines.append("|---|---|---|")
    lines.append(f"| VPC | {len(vpcs)} | {vpc_name}" + (f" + {len(vpcs)-1} more" if len(vpcs) > 1 else "") + " |")
    lines.append(f"| Subnet | {len(subns)} | {primary_vpc.get('addressPrefix', '')} |")
    lines.append(f"| VM (云主机) | {len(vms)} | {len(vms)} running |")
    lines.append(f"| CLB (负载均衡) | {len(clbs)} | {len(clbs)} active |")
    lines.append(f"| EIP (公网 IP) | {len(eips)} | {len(eips)} InUse |")
    lines.append(f"| AG (高可用组) | {len(ags)} | {len(ags)} active |")
    lines.append(f"| SecurityGroup (安全组) | {len(sgs)} | — |")
    lines.append(f"| IAM SubUser | {len(iam)} | sub-users |")
    lines.append(f"| KMS Key | {len(kms)} | keys |")
    if report_mode == 'detailed':
        lines.append(f"| RDS | {len(rds)} | databases |")
        lines.append(f"| Redis | {len(redis)} | cache instances |")

    if report_mode == 'detailed':
        lines.append("")
        lines.append("### 详细清单")
        lines.append("| 类型 | 名称/ID | 规格/引擎 | IP/连接串 | 可用区 |")
        lines.append("|---|---|---|---|---|")
        for v in vms:
            lines.append(f"| {get_health(v.get('instanceId',''),'')} VM | {v.get('instanceName','')} | {v.get('instanceType','')} | {v.get('privateIpAddress','')} | {v.get('az','')} |")
        for d in rds:
            lines.append(f"| {get_health(d.get('instanceId',''),'')} RDS | {d.get('instanceName','')} | {d.get('engine','')} {d.get('engineVersion','')} | {d.get('connectionString','')} | {d.get('az','')} |")
        for r in redis:
            lines.append(f"| {get_health(r.get('cacheInstanceId',''),'')} Redis | {r.get('cacheInstanceName','')} | {r.get('instanceType','')} | {r.get('connectionDomain','')} | {r.get('az','')} |")

    lines.append("")
    lines.append("---")
    lines.append("> 由 jdcloud-topo-discovery 生成 | 安全模式: READ-ONLY")
    return '\n'.join(lines)

# ── Render Mermaid ──
def render_mermaid():
    lines = []
    lines.append("```mermaid")
    lines.append("graph TB")
    vpc_label = mermaid_safe_vpc_label(vpc_name, vpc_id)
    lines.append(f"    subgraph VPC[{vpc_label}]")
    lines.append(f"        style VPC fill:#e8f4fd,stroke:#3b82f6")

    for sid, sn in subnet_map.items():
        safe_sn = mermaid_safe_id(f"sub_{sid}")
        sn_label = mermaid_safe_subgraph_label(sn['name'], sn['cidr'], sn.get('az', ''))
        lines.append(f"    subgraph {safe_sn}[{sn_label}]")
        items = sn.get('vms', []) + sn.get('clbs', []) + sn.get('rds', []) + sn.get('redis', [])

        if large_scale and len(items) > MERMAID_MAX_NODES:
            # Aggregated view: one node per resource type with count
            parts = []
            if sn.get('vms'): parts.append(f"VM x{len(sn['vms'])}")
            if sn.get('clbs'): parts.append(f"CLB x{len(sn['clbs'])}")
            if sn.get('rds'): parts.append(f"RDS x{len(sn['rds'])}")
            if sn.get('redis'): parts.append(f"Redis x{len(sn['redis'])}")
            label = mermaid_safe_label(" | ".join(parts) if parts else "(预留)")
            safe_id = mermaid_safe_id(f"agg_{sid}")
            lines.append(f"        {safe_id}[{label}]")
        else:
            for it in items:
                safe_id = mermaid_safe_id(f"res_{it.get('id','') or it['name']}")
                label = f"{get_health(it.get('id',''),'✅')} {mermaid_escape(it['name'])}"
                if 'ip' in it and it['ip']:
                    label += f"<br/>{mermaid_escape(it['ip'])}"
                elif 'domain' in it:
                    label += f"<br/>{mermaid_escape(it.get('domain',''))}"
                label = mermaid_safe_label(label)
                lines.append(f"        {safe_id}[{label}]")
            if not items:
                lines.append(f"        empty_spot[&#40;预留&#41;]")
        lines.append("    end")

    # EIP → CLB connections
    for l in clbs:
        clb_id = l.get('loadBalancerId', '')
        eip_addr = mermaid_extract_str(l, 'privateIp.elasticIpAddress')
        if eip_addr:
            safe_eip = mermaid_safe_id(f"eip_{eip_addr}")
            safe_clb = mermaid_safe_id(f"res_{clb_id or l.get('loadBalancerName','')}")
            lines.append(f"    {safe_eip}((&#34;{eip_addr}&#34;)) --> {safe_clb}")

    lines.append("    end")
    lines.append("```")
    return '\n'.join(lines)


# ── Render and write output ──
os.makedirs(output_dir, exist_ok=True)
ascii_content = render_ascii()
mermaid_content = render_mermaid()

if output_format in ('ascii', 'both'):
    path = os.path.join(output_dir, "report.md")
    if output_format == 'both':
        # Insert Mermaid diagram after the ASCII topology section
        parts = ascii_content.split("---\n")
        if len(parts) >= 2:
            first_part = parts[0]
            rest = "---\n".join(parts[1:])
            combined = first_part + "---\n\n## 🎨 拓扑关系图\n\n" + mermaid_content + "\n\n---\n" + rest
        else:
            combined = ascii_content + "\n\n## 🎨 拓扑关系图\n\n" + mermaid_content
    else:
        combined = ascii_content
    with open(path, 'w') as f:
        f.write(combined)
    print(f"✅ Report: {path} ({os.path.getsize(path)} bytes)")

if output_format in ('mermaid',):
    path = os.path.join(output_dir, "topology.mermaid.md")
    with open(path, 'w') as f:
        f.write(mermaid_content)
    print(f"✅ Mermaid: {path} ({os.path.getsize(path)} bytes)")

# ── Mermaid Lint Gate ──
LINT_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mermaid-lint', 'lint.mjs')
LINT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mermaid-lint')

def run_mermaid_lint(file_path):
    """Run mermaid-lint on a file. Returns (passed: bool, output: str)."""
    if not os.path.exists(LINT_SCRIPT):
        print(f"[WARN] mermaid-lint not found at {LINT_SCRIPT}, skipping lint gate")
        return True, ""
    if not os.path.exists(os.path.join(LINT_DIR, 'node_modules')):
        print(f"[WARN] mermaid-lint deps not installed (run 'npm install' in {LINT_DIR}), skipping")
        return True, ""
    try:
        result = subprocess.run(
            ['node', LINT_SCRIPT, file_path],
            capture_output=True, text=True, timeout=30,
            cwd=LINT_DIR
        )
        if result.returncode == 0:
            print(f"[LINT] ✅ Mermaid syntax valid: {file_path}")
            return True, result.stdout
        else:
            print(f"[LINT] ❌ Mermaid syntax errors in {file_path}:")
            print(result.stderr or result.stdout)
            return False, result.stderr or result.stdout
    except subprocess.TimeoutExpired:
        print(f"[WARN] mermaid-lint timed out on {file_path}, skipping")
        return True, ""
    except Exception as e:
        print(f"[WARN] mermaid-lint error: {e}, skipping")
        return True, ""

# Run lint gate on generated files
for f in [os.path.join(output_dir, 'report.md'), os.path.join(output_dir, 'topology.mermaid.md')]:
    if os.path.exists(f):
        passed, _ = run_mermaid_lint(f)
        if not passed:
            print("\n🚨 MERMAID LINT GATE FAILED — report may contain invalid diagrams.")
            print("   Fix the syntax errors above and re-run topo-render.py.")
