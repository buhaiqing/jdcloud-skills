---
runbook_id: "02"
scenario: "故障应急排查"
version: "1.0.0"
trigger: "告警触发 / 用户报障"
risk_level: "高"
execution_time_estimate: "5-10 分钟"
---

# 故障应急排查

## 1. 场景

用户报障（慢/不可用）时，从 CLB 入口开始逐层下钻，快速定位根因。**与日常巡检的区别**：关注异常时段 + 链路关联推理，而非全量健康检查。

## 2. 流程

### Phase 1：嗅探（同日常巡检，快速模式）

```yaml
steps:
  - id: "quick_discover"
    description: "只扫客户标签下的核心链路资源（EIP→CLB→VM→Redis→NAT），跳过全量盘查"
    skip: ["云硬盘详情", "安全组全量规则", "K8s 集群事件"]
    timeout: "60s"  # 快速模式，超时即跳过
```

### Phase 2：深度排查（聚焦异常时间窗口）

```yaml
steps:
  - id: "identify_time_window"
    description: "如果是告警触发，直接取告警时间前后 1h；如果是用户报障，取最近 1h"
    window: "告警时间 ±1h / 最近 1h"

  - id: "quick_collect"
    description: "只采集关键指标 + 异常窗口的数据"
    metrics:
      vm: ["cpu_util", "memory.usage", "vm.disk.dev.io.read|write",
           "vm.network.dev.bytes.in|out", "vm.netstat.tcp.established"]
      clb: ["lb.backend.healthy.host_count", "lb.new_connection_count",
            "lb.active_connection_count"]
      redis: ["redis.memory.usage", "redis.hit_rate"]
    query_alarm: true  # 查告警历史

  - id: "check_spec_limits"
    description: "快速检查是否因规格上限导致性能瓶颈"
    focus: ["network_bandwidth_mbps", "max_iops"]

  - id: "root_cause_inference"
    description: "按决策树逐层推理"
    decision_tree: |
      用户报障/告警
      ├── CLB 健康检查失败 > 10%?
      │   ├── 是 → 查后端 VM 状态 + 安全组规则
      │   └── 否 → 查 VM 层
      ├── VM CPU > 70% 或 内存 > 80%?
      │   ├── 是 → 查对应进程 / 慢查询
      │   └── 否 → 查磁盘层
      ├── 磁盘 IOPS 接近规格上限?
      │   ├── 是 → 查慢 SQL / 大查询
      │   └── 否 → 查缓存层
      ├── Redis 命中率 < 90%?
      │   ├── 是 → 查热 key / 大 key / 缓存穿透
      │   └── 否 → 查网络层
      ├── 网络带宽 > 规格 80%?
      │   ├── 是 → 查流量来源（EIP/NAT）
      │   └── 否 → 查 NAT 层
      ├── NAT SNAT 连接 > 80% 上限?
      │   ├── 是 → 查端口耗尽
      │   └── 否 → 查外部依赖
      └── 以上全部正常 → 非资源问题，建议查应用日志/第三方依赖

  - id: "generate_report"
    outputs:
      markdown: true  # 只输出给人读的报告，JSON 可选
      format: "链路追踪式（时间线 + 每个节点的状态 + 根因结论）"
```

## 3. 根因报告示例结构

```
═══════════════════════════════════════
  故障排查报告
═══════════════════════════════════════
  客户: 烟台振华 │ 时间: 2026-06-06 08:00 ~ 09:00
  报障: "ERP 系统响应慢"
═══════════════════════════════════════

🔍 链路追踪
  EIP:  ✔ 带宽正常 (12% of 100Mbps)
    ↓
  CLB:  ⚠ 并发连接激增 (从500→3500, 超过阈值2000)
    ↓
  VM:   ✔ CPU正常 (32%) | 内存正常 (45%)
          ⚠ 磁盘读IOPS飙升 (3115, 超过2000告警线)
    ↓
  Redis: ✔ 内存正常 (60%) | 命中率正常 (95%)
    ↓
  NAT:  ✔ SNAT连接正常

📌 根因结论
  磁盘读IOPS异常升高（峰值3115），导致数据库查询延迟增加。
  CLB并发堆积是结果而非原因。
  建议：
  1. 检查 PG 慢查询日志
  2. 考虑对高频查询加索引
  3. 监控磁盘 IOPS 是否接近规格上限
```

## 4. 闭环

| 反馈 | 动作 |
|---|---|
| 根因判断错误 | 更新决策树规则 |
| 故障模式未覆盖 | 新增 pattern 到 `correlate_chain` 规则表 |
| 排查超时 | 优化 quick_discover 的超时策略 |