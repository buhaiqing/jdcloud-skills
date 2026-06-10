---
runbook_id: "01"
scenario: "云硬盘日常健康巡检"
version: "1.0.0"
last_updated: "2026-06-10"
trigger: "定时调度（每 6 小时）/ 人工触发"
risk_level: "低"
execution_time_estimate: "3-5 分钟（20 块磁盘以内）"
---

# 云硬盘日常健康巡检

## 1. 场景描述

对指定客户在京东云上的全部云硬盘进行日常健康检查，覆盖磁盘状态、使用率、IOPS/吞吐量、加密状态、快照策略等核心维度，输出健康评分和风险项。

### 适用条件

- 磁盘已按 `客户` 标签归类（通过关联 VM 的标签）
- JDC AK/SK 已配置且具有 Disk 读权限
- 支持的 JD Cloud 区域：cn-north-1, cn-east-2, cn-south-1, cn-east-1

### 不适用条件

- 磁盘未关联 VM 且无标签 → 需先执行人工确认流程
- 需要执行变更操作 → 使用 `jdcloud-disk-ops` Execution Flows

---

## 2. 执行流程

### Phase 1: 感知 — 磁盘发现与基础信息采集（约 1 分钟）

```yaml
steps:
  - id: "list_disks"
    description: "列出所有云硬盘"
    cli:
      command: >
        jdc --output json disk describe-disks
        --region-id "{{user.region}}"
        --page-number 1 --page-size 100
      json_path: "$.result.disks"
    sdk_fallback:
      api: "DescribeDisks"
      params: { regionId: "{{user.region}}", pageNumber: 1, pageSize: 100 }

  - id: "filter_by_customer"
    description: "按客户标签过滤磁盘"
    method: |
      1. 对于已挂载磁盘，通过关联 VM 的 客户 标签识别
      2. 对于未挂载磁盘，检查磁盘自身的标签

  - id: "collect_basic_info"
    description: "采集每个磁盘的基础信息"
    fields:
      - "diskId: 磁盘 ID (vol-xxxxxx)"
      - "name: 磁盘名称"
      - "status: 状态 (available/in-use/creating/detaching/deleting/error)"
      - "diskType: 类型 (ssd/premium-hdd/standard-hdd)"
      - "diskSizeGB: 容量 (GB)"
      - "instanceId: 挂载的 VM ID (如有)"
      - "instanceName: 挂载的 VM 名称 (如有)"
      - "az: 可用区"
      - "createTime: 创建时间"
      - "chargeMode: 计费模式"
      - "encrypted: 是否加密"
      - "snapshotCount: 快照数量"
```

### Phase 2: 推理 — 指标采集与分析（约 2-3 分钟）

```yaml
steps:
  - id: "collect_metrics"
    description: "采集每个磁盘最近 6 小时的监控指标（5 分钟粒度）"
    time_windows:
      current: "最近 6 小时"
      daily_baseline: "昨日同期（T-24h ~ T-18h）"
    metrics:
      - "vm.disk.dev.used"            # 磁盘使用率 (%)
      - "vm.disk.dev.io.read"         # 磁盘读 IOPS
      - "vm.disk.dev.io.write"        # 磁盘写 IOPS
      - "vm.disk.dev.io.read.bytes"   # 磁盘读吞吐量 (bytes/s)
      - "vm.disk.dev.io.write.bytes"  # 磁盘写吞吐量 (bytes/s)
      - "vm.disk.dev.io.await"        # 磁盘 IO 等待时间 (ms)

  - id: "check_disk_status"
    description: "检查磁盘状态"
    rules:
      - condition: "status == 'error'"
        severity: "critical"
        message: "磁盘状态异常: error"
        action: "检查磁盘事件; 如无法恢复则创建快照后替换"
      - condition: "status == 'detaching' AND 持续时间 > 5 分钟"
        severity: "warning"
        message: "磁盘卸载中超过 5 分钟"
        action: "检查 VM 是否正常; 必要时强制卸载"

  - id: "analyze_usage"
    description: "磁盘使用率分析"
    rules:
      - condition: "vm.disk.dev.used 当前值 > 90%"
        severity: "critical"
        message: "磁盘使用率 {value}%，即将耗尽"
        action: "立即扩容磁盘或清理数据; 扩容前先创建快照"
        ops_skill: "jdcloud-disk-ops (resize-disk)"
      - condition: "vm.disk.dev.used 当前值 > 80%"
        severity: "warning"
        message: "磁盘使用率 {value}%，建议关注"
        action: "计划扩容; 分析空间增长趋势"
      - condition: "vm.disk.dev.used 当前值 > 75%"
        severity: "info"
        message: "磁盘使用率 {value}%"
        action: "建议关注增长趋势"

  - id: "analyze_usage_trend"
    description: "磁盘使用率趋势分析"
    rules:
      - condition: "6h 内使用率增长 > 10%"
        severity: "warning"
        message: "磁盘使用率快速增长 ({start}% → {end}%)"
        action: "检查是否有大量数据写入; 分析增长原因"
      - condition: "6h 内使用率增长 > 20%"
        severity: "critical"
        message: "磁盘使用率急剧增长 ({start}% → {end}%)"
        action: "立即排查写入来源; 准备紧急扩容"

  - id: "analyze_iops"
    description: "IOPS 分析"
    rules:
      - condition: "IOPS 接近磁盘类型规格上限的 80%"
        severity: "warning"
        message: "IOPS 使用率 {ratio}%，接近规格上限"
        action: "检查是否有慢查询或异常 IO; 考虑升级磁盘类型"
        ops_skill: "jdcloud-disk-ops (modify disk type)"
      - condition: "vm.disk.dev.io.await > 10ms"
        severity: "warning"
        message: "磁盘 IO 等待时间 {value}ms，性能下降"
        action: "检查 IO 模式; 考虑升级到更高 IOPS 的磁盘类型"

  - id: "check_encryption"
    description: "加密状态检查"
    rules:
      - condition: "encrypted == false AND disk 挂载在生产环境 VM"
        severity: "warning"
        message: "生产环境磁盘未加密"
        action: "建议启用云盘加密（需创建加密快照后恢复）"
      - condition: "encrypted == false AND disk 为系统盘"
        severity: "info"
        message: "系统盘未加密"
        action: "如有合规要求，建议启用加密"

  - id: "check_snapshot"
    description: "快照策略检查"
    rules:
      - condition: "snapshotCount == 0 AND disk 挂载在生产环境 VM"
        severity: "warning"
        message: "生产环境磁盘无快照"
        action: "立即创建快照; 配置自动快照策略"
        ops_skill: "jdcloud-disk-ops (create-snapshot)"
      - condition: "最近一次快照距今 > 7 天 AND disk 挂载在生产环境 VM"
        severity: "warning"
        message: "最近快照在 {date}，已超过 7 天"
        action: "创建新快照; 检查自动快照策略是否正常"
      - condition: "snapshotCount > 50"
        severity: "info"
        message: "快照数量 {count}，建议清理旧快照"
        action: "删除 30 天前的旧快照以节省成本"

  - id: "check_unattached"
    description: "未挂载磁盘检查"
    rules:
      - condition: "status == 'available' AND 创建时间 > 7 天"
        severity: "warning"
        message: "磁盘 {name} 已闲置 {days} 天未挂载"
        action: "确认是否仍需要; 如不需要则备份后删除以节省成本"
        ops_skill: "jdcloud-disk-ops (create-snapshot → delete-disk)"
      - condition: "status == 'available' AND 创建时间 > 30 天"
        severity: "critical"
        message: "磁盘 {name} 已闲置 {days} 天，产生不必要费用"
        action: "建议立即处理：备份后删除或挂载使用"

  - id: "check_system_disk"
    description: "系统盘特殊检查"
    rules:
      - condition: "disk 为系统盘 AND vm.disk.dev.used > 85%"
        severity: "critical"
        message: "系统盘使用率 {value}%，可能导致系统异常"
        action: "扩容系统盘; 清理系统日志和临时文件"
        ops_skill: "jdcloud-disk-ops (resize-disk) + jdcloud-vm-ops (extend filesystem)"
```

### Phase 3: 执行 — 建议生成（只读）

```yaml
steps:
  - id: "generate_health_score"
    description: "计算每块磁盘的健康评分（0-100）"
    scoring:
      base: 100
      deductions:
        - "状态异常: -50"
        - "使用率 > 90%: -30"
        - "使用率 > 80%: -15"
        - "使用率快速增长 > 20%/6h: -20"
        - "IOPS 接近上限: -15"
        - "IO await > 10ms: -10"
        - "生产环境未加密: -15"
        - "无快照: -20"
        - "快照超 7 天: -10"
        - "闲置 > 30 天: -15"

  - id: "generate_suggestions"
    description: "按严重程度排序生成修复建议"
    output_format: "Markdown 表格"
    columns:
      - "优先级 (P0/P1/P2)"
      - "磁盘名称"
      - "挂载 VM"
      - "问题描述"
      - "当前值"
      - "阈值"
      - "建议操作"
      - "委托 Skill"

  - id: "output_report"
    description: "输出巡检报告"
    outputs:
      - path: "reports/output/disk-health-{customer}-{date}.md"
        format: "Markdown"
      - path: "reports/output/disk-health-{customer}-{date}.json"
        format: "JSON"
```

---

## 3. 阈值定义

| 维度 | 指标 | Warning 阈值 | Critical 阈值 | 说明 |
|------|------|-------------|---------------|------|
| 状态 | status | detaching > 5min | error | 磁盘不可用 |
| 使用率 | vm.disk.dev.used | > 80% | > 90% | 磁盘满导致写入失败 |
| 使用率趋势 | 6h 增长 | > 10% | > 20% | 异常写入 |
| IOPS | 使用率/规格上限 | > 70% | > 85% | 性能瓶颈 |
| IO await | vm.disk.dev.io.await | > 5ms | > 10ms | IO 延迟 |
| 加密 | encrypted | 生产环境未加密 | — | 合规风险 |
| 快照 | 最近快照时间 | > 3 天 | > 7 天 | 数据安全 |
| 快照 | 快照数量 | > 30 | > 50 | 存储成本 |
| 闲置 | available 时长 | > 7 天 | > 30 天 | 成本浪费 |
| 系统盘 | 使用率 | > 80% | > 85% | 系统异常风险 |

---

## 4. 告警联动

| 告警类型 | 触发条件 | 自动动作 | 委托 Skill |
|----------|----------|----------|------------|
| 磁盘即将满 | 使用率 > 90% | 创建 DOPS 扩容工单 | `jdcloud-disk-ops` (resize-disk) |
| 磁盘快速增长 | 6h 增长 > 20% | 创建 DOPS 排查工单 | 人工排查写入来源 |
| 无快照 | 生产磁盘无快照 | 自动创建快照 | `jdcloud-disk-ops` (create-snapshot) |
| 闲置磁盘 | 闲置 > 30 天 | 创建 DOPS 清理确认工单 | 人工确认后删除 |

---

## 5. 闭环改进

| 反馈来源 | 触发条件 | 改进动作 | 责任人 |
|----------|----------|----------|--------|
| 误报 | 使用率 > 80% 但实际正常 | 调整阈值或增加白名单 | 运维负责人 |
| 漏报 | 磁盘满但未预警 | 降低阈值或增加预测维度 | 运维负责人 |
| 新磁盘类型 | 京东云新增磁盘类型 | 更新 IOPS 规格上限表 | 脚本维护者 |

---

## 6. Changelog

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0.0 | 2026-06-10 | 初始版本，定义云硬盘日常健康巡检完整流程 |
