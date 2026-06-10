---
runbook_id: "02"
scenario: "云硬盘容量预测与规划"
version: "1.0.0"
last_updated: "2026-06-10"
trigger: "每周定时 / 人工触发"
risk_level: "中"
execution_time_estimate: "5-10 分钟（20 块磁盘以内）"
---

# 云硬盘容量预测与规划

## 1. 场景描述

基于历史使用数据预测磁盘空间耗尽时间，分析 IOPS/吞吐量趋势，识别低利用率磁盘和闲置资源，输出容量规划和成本优化方案。

### 背景

DOPS 实际案例：
- DOPS-85657：烟台振华京东云 — 预测未来 4 小时主机磁盘空间即将耗尽（Prometheus predict_linear 检测到 `/data` 分区即将满）
- DOPS-85637：促销中台 RDS 只读实例磁盘缩容

### 适用条件

- 磁盘运行时间 > 7 天（需要足够的历史数据）
- JDC AK/SK 已配置且具有 Disk 读权限

---

## 2. 执行流程

### Phase 1: 感知 — 数据采集（约 2 分钟）

```yaml
steps:
  - id: "list_disks"
    description: "列出所有云硬盘"
    cli:
      command: >
        jdc --output json disk describe-disks
        --region-id "{{user.region}}"
        --page-number 1 --page-size 100
    filter: "按客户标签过滤"

  - id: "collect_7d_metrics"
    description: "采集最近 7 天的监控数据（1 小时粒度）"
    time_window: "最近 7 天"
    metrics:
      - "vm.disk.dev.used"            # 磁盘使用率 (%)
      - "vm.disk.dev.io.read"         # 磁盘读 IOPS
      - "vm.disk.dev.io.write"        # 磁盘写 IOPS
      - "vm.disk.dev.io.read.bytes"   # 磁盘读吞吐量
      - "vm.disk.dev.io.write.bytes"  # 磁盘写吞吐量

  - id: "collect_spec_limits"
    description: "采集磁盘类型规格上限"
    spec_limits:
      ssd:
        max_iops: "min(diskSizeGB * 30, 20000)"    # SSD IOPS = min(容量*30, 20000)
        max_throughput: "min(diskSizeGB * 0.5, 350) MB/s"
      premium_hdd:
        max_iops: "min(diskSizeGB * 5, 5000)"
        max_throughput: "min(diskSizeGB * 0.15, 150) MB/s"
      standard_hdd:
        max_iops: "min(diskSizeGB * 2, 2000)"
        max_throughput: "min(diskSizeGB * 0.1, 100) MB/s"
```

### Phase 2: 推理 — 容量预测与分析（约 3-5 分钟）

```yaml
steps:
  - id: "predict_disk_full"
    description: "基于线性回归预测磁盘满时间"
    method: "线性回归（最近 7 天 vm.disk.dev.used 数据点）"
    prediction_horizon: "90 天"
    rules:
      - id: "P1_imminent_full"
        condition: "预测 24 小时内使用率达到 90%"
        severity: "critical"
        category: "磁盘即将耗尽"
        message: "预计 {datetime} 磁盘使用率达到 90%（剩余 {hours} 小时）"
        suggestion: "立即扩容磁盘到 {recommended_size}GB; 扩容前创建快照"
        ops_skill: "jdcloud-disk-ops (create-snapshot → resize-disk)"
      - id: "P2_soon_full"
        condition: "预测 7 天内使用率达到 90%"
        severity: "warning"
        category: "磁盘近期将满"
        message: "预计 {date} 磁盘使用率达到 90%"
        suggestion: "计划在 {date} 前扩容磁盘到 {recommended_size}GB"
      - id: "P3_month_full"
        condition: "预测 30 天内使用率达到 90%"
        severity: "info"
        category: "磁盘月度预警"
        message: "预计 {date} 磁盘使用率达到 90%"
        suggestion: "纳入下月扩容计划"

  - id: "predict_iops_bottleneck"
    description: "预测 IOPS 瓶颈时间"
    method: "线性回归（最近 7 天 IOPS 数据点 vs 规格上限）"
    rules:
      - condition: "预测 30 天内 IOPS 达到规格上限的 80%"
        severity: "warning"
        category: "IOPS 瓶颈预警"
        message: "预计 {date} IOPS 达到规格上限的 80%"
        suggestion: "考虑升级磁盘类型（如 premium-hdd → ssd）"
        ops_skill: "jdcloud-disk-ops (modify disk type)"

  - id: "detect_underutilized"
    description: "识别低利用率磁盘"
    rules:
      - id: "U1_size_underutilized"
        condition: "vm.disk.dev.used 7 天 P95 < 30% AND diskSizeGB > 100"
        severity: "info"
        category: "磁盘容量低利用"
        message: "磁盘 {name} ({size}GB) 7 天 P95 使用率仅 {p95}%"
        suggestion: "考虑缩容到 {recommended_size}GB（注意：云硬盘只支持扩容不支持缩容，需创建新盘迁移数据）"
      - id: "U2_iops_underutilized"
        condition: "IOPS 7 天 P95 < 规格上限 * 20% AND diskType == 'ssd'"
        severity: "info"
        category: "SSD IOPS 低利用"
        message: "SSD 磁盘 {name} IOPS 7 天 P95 仅 {p95}，远低于规格上限"
        suggestion: "如不需要高 IOPS，可考虑降级为 premium-hdd 以节省成本"

  - id: "detect_cost_optimization"
    description: "成本优化分析"
    rules:
      - id: "C1_idle_disk"
        condition: "status == 'available' AND 创建时间 > 7 天"
        severity: "warning"
        category: "闲置磁盘产生费用"
        message: "磁盘 {name} ({size}GB, {type}) 已闲置 {days} 天，月费用约 ¥{cost}"
        suggestion: "确认是否仍需要; 如不需要则创建快照后删除"
        ops_skill: "jdcloud-disk-ops (create-snapshot → delete-disk)"
      - id: "C2_oversized"
        condition: "diskSizeGB > 500 AND vm.disk.dev.used 7 天 P95 < 20%"
        severity: "info"
        category: "大容量低利用"
        message: "磁盘 {name} ({size}GB) 利用率极低"
        suggestion: "考虑迁移数据到更小磁盘以节省成本"
      - id: "C3_old_snapshots"
        condition: "snapshotCount > 30 AND 存在 > 30 天的快照"
        severity: "info"
        category: "旧快照占用存储费用"
        message: "{count} 个快照超过 30 天，月存储费用约 ¥{cost}"
        suggestion: "删除 30 天前的旧快照"

  - id: "capacity_planning_summary"
    description: "汇总容量规划建议"
    output:
      - "需要立即扩容的磁盘: {count} 块"
      - "7 天内需要扩容的磁盘: {count} 块"
      - "30 天内需要扩容的磁盘: {count} 块"
      - "可降配/清理的磁盘: {count} 块"
      - "预计扩容总成本: ¥{cost}/月"
      - "预计可节省成本: ¥{saving}/月"
```

### Phase 3: 执行 — 规划建议生成（只读）

```yaml
steps:
  - id: "generate_timeline"
    description: "生成扩容时间线"
    format: |
      # 磁盘扩容时间线
      ## 紧急（24h 内）
      - {disk_name}: 预计 {datetime} 满，建议扩容到 {size}GB
      ## 本周（7 天内）
      - {disk_name}: 预计 {date} 满，建议扩容到 {size}GB
      ## 本月（30 天内）
      - {disk_name}: 预计 {date} 满，建议扩容到 {size}GB

  - id: "generate_cost_report"
    description: "生成成本优化报告"
    output_format: "Markdown 表格"
    columns:
      - "磁盘名称"
      - "当前规格"
      - "7天使用率 P95"
      - "分类"
      - "建议操作"
      - "预计月节省"
      - "优先级"

  - id: "output_report"
    description: "输出容量规划报告"
    outputs:
      - path: "reports/output/disk-capacity-{customer}-{date}.md"
        format: "Markdown"
      - path: "reports/output/disk-capacity-{customer}-{date}.json"
        format: "JSON"
```

---

## 3. 扩容安全规则

| 规则 | 说明 |
|------|------|
| **只支持扩容不支持缩容** | 云硬盘只能增大容量，不能减小 |
| **扩容前必须创建快照** | 防止扩容过程中数据丢失 |
| **扩容后需扩展文件系统** | 通过 `jdcloud-vm-ops` cloud assistant 执行 `resize2fs` / `xfs_growfs` |
| **系统盘扩容需重启 VM** | 部分 OS 需要重启才能识别新容量 |
| **建议扩容到 P95 * 2 或当前 * 1.5** | 预留足够余量避免频繁扩容 |

---

## 4. 告警联动

| 告警类型 | 触发条件 | 自动动作 |
|----------|----------|----------|
| 磁盘即将满（24h） | 预测 24h 内满 | 创建 DOPS 紧急扩容工单 + 自动创建快照 |
| 磁盘近期将满（7d） | 预测 7d 内满 | 创建 DOPS 扩容计划工单 |
| 闲置磁盘 | 闲置 > 7 天 | 创建 DOPS 清理确认工单 |
| IOPS 瓶颈 | 预测 30d 内达上限 | 创建 DOPS 磁盘升级工单 |

---

## 5. Changelog

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0.0 | 2026-06-10 | 初始版本，定义云硬盘容量预测与规划完整流程 |
