#!/usr/bin/env python3
"""
K8s 集群深度巡检脚本 - 针对集群 k8s-g1rlg9atud
生成运营巡检报告
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# 加载 .env
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip("\"'"))

# 添加 aiops cruise lib 路径
sys.path.insert(0, str(Path(__file__).parent / "jdcloud-aiops-cruise" / "scripts"))
from lib.jdc_client import JdcClient  # noqa: E402

CLUSTER_ID = "k8s-g1rlg9atud"
REGION = "cn-east-2"

def main():
    print("=" * 80)
    print("🔍 JD Cloud K8s 集群深度巡检报告")
    print(f"集群 ID: {CLUSTER_ID}")
    print(f"巡检时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"巡检区域: {REGION}")
    print("=" * 80)

    client = JdcClient(region=REGION)

    # Phase 1: 基础信息采集
    print("\n📋 Phase 1: 集群基础信息采集\n")

    # 查询所有集群，找到目标集群
    clusters = client.list_clusters(region=REGION)
    target_cluster = None
    for c in clusters:
        if c.get("clusterId") == CLUSTER_ID:
            target_cluster = c
            break

    if not target_cluster:
        print(f"❌ 错误: 在区域 {REGION} 中未找到集群 {CLUSTER_ID}")
        print("\n可用集群列表:")
        for c in clusters:
            print(f"  - {c.get('clusterId')}: {c.get('clusterName', 'N/A')} ({c.get('state', 'unknown')})")
        return 1

    # 输出集群基础信息
    print("✅ 集群 found:")
    print(f"  集群名称: {target_cluster.get('clusterName', 'N/A')}")
    print(f"  集群状态: {target_cluster.get('state', 'unknown')}")
    print(f"  K8s 版本: {target_cluster.get('masterVersion', 'N/A')}")
    print(f"  终端地址: {target_cluster.get('endpoint', 'N/A')}")
    print(f"  VPC ID: {target_cluster.get('vpcId', 'N/A')}")
    print(f"  子网 ID: {target_cluster.get('subnetId', 'N/A')}")
    print(f"  创建时间: {target_cluster.get('createdTime', 'N/A')}")

    # 查询节点组
    print("\n📦 节点组信息:")
    node_groups = client._paginate(
        "kubernetes",
        f"/v1/regions/{REGION}/clusters/{CLUSTER_ID}/nodeGroups",
        result_path="nodeGroups"
    )

    total_nodes = 0
    for ng in node_groups:
        print(f"  - {ng.get('nodeGroupId')}:")
        print(f"      名称: {ng.get('name', 'N/A')}")
        print(f"      状态: {ng.get('state', 'unknown')}")
        print(f"      实例规格: {ng.get('instanceType', 'N/A')}")
        print(f"      节点数量: {ng.get('nodeCount', 0)}")
        print(f"      自动修复: {ng.get('autoRepair', False)}")
        print(f"      子网: {ng.get('subnetId', 'N/A')}")
        total_nodes += ng.get('nodeCount', 0)

    print(f"\n  总节点数: {total_nodes}")

    # Phase 2: 监控指标采集
    print("\n📊 Phase 2: 监控指标采集\n")

    # 获取集群节点监控指标（通过 VM service）
    print("  尝试获取节点监控指标...")

    # 获取节点实例ID列表
    node_instance_ids = []
    for ng in node_groups:
        # 获取节点组详情以获取节点实例
        try:
            ng_detail = client._get(
                "kubernetes",
                f"/v1/regions/{REGION}/clusters/{CLUSTER_ID}/nodeGroups/{ng['nodeGroupId']}"
            )
            nodes = ng_detail.get("result", {}).get("nodeGroup", {}).get("nodes", [])
            for node in nodes:
                if node.get("instanceId"):
                    node_instance_ids.append(node["instanceId"])
        except Exception as e:
            print(f"    警告: 获取节点组 {ng['nodeGroupId']} 详情失败: {e}")

    print(f"  发现 {len(node_instance_ids)} 个节点实例")

    # 采集节点 CPU/内存指标
    metrics_summary = {
        "cpu_util": [],
        "memory_util": [],
        "disk_util": []
    }

    for iid in node_instance_ids[:5]:  # 限制采样数量
        try:
            cpu_metrics = client.get_metric(iid, "cpu_util", hours=24, service_code="vm")
            if cpu_metrics:
                avg_cpu = sum(v for _, v in cpu_metrics) / len(cpu_metrics)
                metrics_summary["cpu_util"].append((iid, avg_cpu))
                print(f"    节点 {iid[:20]}... CPU 24h 均值: {avg_cpu:.1f}%")

            mem_metrics = client.get_metric(iid, "memory_util", hours=24, service_code="vm")
            if mem_metrics:
                avg_mem = sum(v for _, v in mem_metrics) / len(mem_metrics)
                metrics_summary["memory_util"].append((iid, avg_mem))
                print(f"    节点 {iid[:20]}... 内存 24h 均值: {avg_mem:.1f}%")
        except Exception as e:
            print(f"    警告: 获取节点 {iid[:20]}... 指标失败: {e}")

    # Phase 3: 巡检结论
    print("\n📝 Phase 3: 巡检结论与建议\n")

    # 状态检查
    state = target_cluster.get('state', 'unknown')
    if state == 'running':
        print("✅ 集群状态: 正常运行 (running)")
    elif state == 'error':
        print("❌ 集群状态: 异常 (error) - 需要立即处理")
    elif state in ['creating', 'deleting']:
        print(f"⏳ 集群状态: {state} - 正在进行中")
    else:
        print(f"⚠️ 集群状态: {state} - 请检查")

    # 节点组健康检查
    ng_issues = []
    for ng in node_groups:
        if ng.get('state') != 'running':
            ng_issues.append(f"节点组 {ng.get('name')} 状态异常: {ng.get('state')}")
        if ng.get('nodeCount', 0) == 0:
            ng_issues.append(f"节点组 {ng.get('name')} 节点数为 0")
        if not ng.get('autoRepair', False):
            ng_issues.append(f"节点组 {ng.get('name')} 未启用自动修复")

    if ng_issues:
        print("\n⚠️ 发现的问题:")
        for issue in ng_issues:
            print(f"  - {issue}")
    else:
        print("\n✅ 所有节点组状态正常")

    # 资源使用建议
    if metrics_summary["cpu_util"]:
        avg_cluster_cpu = sum(v for _, v in metrics_summary["cpu_util"]) / len(metrics_summary["cpu_util"])
        print("\n📈 CPU 使用率分析:")
        print(f"  集群平均 CPU 使用率: {avg_cluster_cpu:.1f}%")
        if avg_cluster_cpu > 80:
            print("  ⚠️ 建议: CPU 使用率过高，考虑扩容节点")
        elif avg_cluster_cpu < 20:
            print("  💡 建议: CPU 使用率较低，可能存在资源浪费")
        else:
            print("  ✅ CPU 使用率处于合理范围")

    if metrics_summary["memory_util"]:
        avg_cluster_mem = sum(v for _, v in metrics_summary["memory_util"]) / len(metrics_summary["memory_util"])
        print("\n📈 内存使用率分析:")
        print(f"  集群平均内存使用率: {avg_cluster_mem:.1f}%")
        if avg_cluster_mem > 85:
            print("  ⚠️ 建议: 内存使用率过高，建议扩容或优化应用")
        elif avg_cluster_mem < 25:
            print("  💡 建议: 内存使用率较低，考虑降配以节约成本")
        else:
            print("  ✅ 内存使用率处于合理范围")

    # 保存报告
    report = {
        "cluster_id": CLUSTER_ID,
        "cluster_name": target_cluster.get('clusterName'),
        "region": REGION,
        "inspection_time": datetime.now().isoformat(),
        "cluster_info": target_cluster,
        "node_groups": node_groups,
        "metrics_summary": {
            k: [(iid[:20], v) for iid, v in vals]
            for k, vals in metrics_summary.items()
        },
        "issues": ng_issues,
        "recommendations": generate_recommendations(target_cluster, node_groups, metrics_summary)
    }

    output_dir = Path(__file__).parent / "jdcloud-aiops-cruise" / "reports" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / f"k8s-cruise-{CLUSTER_ID}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    print(f"\n💾 完整报告已保存: {report_path}")

    return 0

def generate_recommendations(cluster, node_groups, metrics):
    """生成优化建议"""
    recs = []

    # 自动修复检查
    for ng in node_groups:
        if not ng.get('autoRepair', False):
            recs.append({
                "severity": "medium",
                "category": "可用性",
                "target": f"节点组 {ng.get('name')}",
                "suggestion": "启用自动修复功能以提高节点故障恢复能力",
                "action": f"jdc kubernetes set-auto-repair --region-id cn-east-2 --cluster-id {cluster['clusterId']} --node-group-id {ng['nodeGroupId']} --enabled true"
            })

    # 资源利用率
    if metrics.get("cpu_util"):
        avg_cpu = sum(v for _, v in metrics["cpu_util"]) / len(metrics["cpu_util"])
        if avg_cpu > 80:
            recs.append({
                "severity": "high",
                "category": "性能",
                "target": "集群 CPU",
                "suggestion": "CPU 使用率超过 80%，建议扩容节点组或优化应用",
                "action": "考虑使用 jdc kubernetes set-node-group-size 增加节点数量"
            })

    if metrics.get("memory_util"):
        avg_mem = sum(v for _, v in metrics["memory_util"]) / len(metrics["memory_util"])
        if avg_mem > 85:
            recs.append({
                "severity": "high",
                "category": "性能",
                "target": "集群内存",
                "suggestion": "内存使用率超过 85%，存在 OOM 风险",
                "action": "建议增加节点或调整 Pod 资源限制"
            })

    return recs

if __name__ == "__main__":
    sys.exit(main())
