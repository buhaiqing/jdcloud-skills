---
runbook_id: "01"
scenario: "Redis 日常健康巡检"
version: "1.0.0"
last_updated: "2026-06-10"
trigger: "定时调度（每 6 小时）/ 人工触发"
risk_level: "低"
execution_time_estimate: "3-5 分钟（10 个实例以内）"
---

# Redis 日常健康巡检

## 1. 场景描述

对指定客户在京东云上的全部 Redis 实例进行日常健康检查，覆盖内存使用、缓存命中率、连接数、CPU 使用率、慢查询等核心指标，输出健康评分和风险项。

### 适用条件

- 资源已按 `客户` 标签归类
- JDC AK/SK 已配置且具有 Redis 读权限
- 支持的 JD Cloud 区域：cn-north-1, cn-east-2, cn-south-1, cn-east-1

### 不适用条件

- 资源未打标签 → 需先执行人工确认流程
- 需要执行变更操作 → 使用 `jdcloud-redis-ops` Execution Flows

---

## 2. 执行流程

### Phase 1: 感知 — 实例发现与基础信息采集（约 1 分钟）

```yaml
steps:
  - id: "list_instances"
    description: "列出指定区域所有 Redis 实例"
    cli:
      command: >
        jdc --output json redis describe-cache-instances
        --region-id "{{user.region}}"
        --page-number 1 --page-size 100
      json_path: "$.result.cacheInstances"
    sdk_fallback:
      api: "DescribeCacheInstances"
      params: { regionId: "{{user.region}}", pageNumber: 1, pageSize: 100 }

  - id: "filter_by_customer"
    description: "按客户标签过滤实例"
    method: "检查每个实例的 tags 中是否包含 客户={{user.customer}}"

  - id: "collect_basic_info"
    description: "采集每个实例的基础信息"
    fields:
      - "cacheInstanceId: 实例 ID"
      - "cacheInstanceName: 实例名称"
      - "cacheInstanceClass: 规格代码"
      - "cacheInstanceMemoryMB: 内存规格 (MB)"
      - "redisVersion: Redis 版本"
      - "cacheInstanceType: 实例类型 (master-slave/cluster/native-cluster)"
      - "status: 运行状态"
      - "vpcId / subnetId: 网络信息"
      - "connectionDomain: 连接地址"
      - "port: 端口"
```

### Phase 2: 推理 — 指标采集与分析（约 2-3 分钟）

```yaml
steps:
  - id: "collect_metrics"
    description: "采集每个实例最近 6 小时的监控指标（5 分钟粒度）"
    time_windows:
      current: "最近 6 小时"
      daily_baseline: "昨日同期（T-24h ~ T-18h）"
    metrics:
      - "redis.memory.usage"       # 内存使用率 (%)
      - "redis.hit_rate"           # 缓存命中率 (%)
      - "redis.connections"        # 连接数
      - "redis.cpu.util"           # CPU 使用率 (%)
      - "redis.memory.used"        # 已用内存 (MB)
      - "redis.keys.evicted"       # 淘汰 key 数
      - "redis.network.bytes.in"   # 入网流量 (bytes/s)
      - "redis.network.bytes.out"  # 出网流量 (bytes/s)

  - id: "check_instance_status"
    description: "检查实例运行状态"
    rules:
      - condition: "status != 'running'"
        severity: "critical"
        message: "实例状态异常: {status}"
        action: "检查实例事件日志; 如长时间异常则联系京东云技术支持"

  - id: "analyze_memory"
    description: "内存使用分析"
    rules:
      - condition: "redis.memory.usage 当前值 > 85%"
        severity: "critical"
        message: "内存使用率 {value}%，接近 OOM 风险"
        action: "立即扩容或清理过期 key; 检查大 key; 考虑调整 maxmemory-policy"
        ops_skill: "jdcloud-redis-ops (modify-cache-instance-class)"
      - condition: "redis.memory.usage 当前值 > 75%"
        severity: "warning"
        message: "内存使用率 {value}%，建议关注"
        action: "计划扩容; 分析内存增长趋势"
      - condition: "redis.memory.usage 最近 6h 持续上升且增幅 > 20%"
        severity: "warning"
        message: "内存使用率持续上升 ({first}% → {last}%)"
        action: "检查是否有大 key 写入或内存泄漏; 执行 MEMORY STATS 分析"

  - id: "analyze_hit_rate"
    description: "缓存命中率分析"
    rules:
      - condition: "redis.hit_rate 6h 平均 < 80%"
        severity: "warning"
        message: "缓存命中率 {avg}%，存在缓存穿透或热 key 过期风险"
        action: "检查 keyspace 命中率; 分析是否有大量 key 同时过期; 考虑增加缓存预热"
      - condition: "redis.hit_rate 6h 平均 < 90%"
        severity: "info"
        message: "缓存命中率 {avg}%，略低于最佳水平"
        action: "建议关注命中率趋势"

  - id: "analyze_connections"
    description: "连接数分析"
    rules:
      - condition: "redis.connections 当前值 > 9000"
        severity: "warning"
        message: "连接数 {value}，接近上限"
        action: "检查是否有连接泄漏; 确认客户端连接池配置; 考虑使用连接池复用"
      - condition: "redis.connections 当前值 > 5000"
        severity: "info"
        message: "连接数 {value}，建议关注"

  - id: "analyze_cpu"
    description: "CPU 使用率分析"
    rules:
      - condition: "redis.cpu.util 当前值 > 80%"
        severity: "warning"
        message: "CPU 使用率 {value}%，可能影响响应延迟"
        action: "检查慢查询; 分析是否因大 key 操作导致; 考虑升配或拆分实例"
      - condition: "redis.cpu.util 当前值 > 60%"
        severity: "info"
        message: "CPU 使用率 {value}%，建议关注"

  - id: "analyze_eviction"
    description: "Key 淘汰分析"
    rules:
      - condition: "redis.keys.evicted 6h 内 > 0"
        severity: "warning"
        message: "6h 内有 {count} 个 key 被淘汰"
        action: "检查 maxmemory-policy 配置; 评估是否需要扩容内存"
      - condition: "maxmemoryPolicy == 'noeviction' AND redis.memory.usage > 80%"
        severity: "warning"
        message: "淘汰策略为 noeviction，内存满时写入将失败"
        action: "建议改用 volatile-lru 或 allkeys-lru"

  - id: "check_version"
    description: "Redis 版本检查"
    rules:
      - condition: "redisVersion < '5.0'"
        severity: "info"
        message: "Redis 版本 {version} 偏旧"
        action: "建议升级到 5.0+ 以获得更好的性能和安全性"

  - id: "check_slow_logs"
    description: "慢查询检查（通过 API 获取 slowlog）"
    cli:
      command: >
        jdc --output json redis describe-slow-log
        --region-id "{{user.region}}"
        --cache-instance-id "{{instance_id}}"
    rules:
      - condition: "slowlog 中存在执行时间 > 1000ms 的命令"
        severity: "warning"
        message: "发现慢查询: {command} ({duration}ms)"
        action: "优化查询命令; 检查是否使用了 KEYS 命令; 考虑使用 SCAN 替代"

  - id: "check_big_key"
    description: "大 Key 检查（通过 cache-analysis API）"
    cli:
      command: >
        jdc --output json redis describe-big-key-analysis
        --region-id "{{user.region}}"
        --cache-instance-id "{{instance_id}}"
    rules:
      - condition: "存在 > 10MB 的 key"
        severity: "warning"
        message: "发现大 Key: {key} ({size})"
        action: "考虑拆分大 key; 使用 hash 结构分散存储"

  - id: "check_hot_key"
    description: "热 Key 检查（通过 cache-analysis API）"
    cli:
      command: >
        jdc --output json redis describe-hot-key-analysis
        --region-id "{{user.region}}"
        --cache-instance-id "{{instance_id}}"
    rules:
      - condition: "存在访问频率 > 3000次/秒 的 key"
        severity: "warning"
        message: "发现热 Key: {key} ({qps}次/秒)"
        action: "考虑本地缓存或读写分离"

  - id: "check_backup"
    description: "备份状态检查"
    cli:
      command: >
        jdc --output json redis describe-backups
        --region-id "{{user.region}}"
        --cache-instance-id "{{instance_id}}"
    rules:
      - condition: "最近一次备份距今 > 7 天"
        severity: "warning"
        message: "最近备份在 {date}，已超过 7 天"
        action: "立即创建手动备份; 配置自动备份策略"
```

### Phase 3: 执行 — 建议生成（只读）

```yaml
steps:
  - id: "generate_health_score"
    description: "计算每个实例的健康评分（0-100）"
    scoring:
      base: 100
      deductions:
        - "内存 > 85%: -30"
        - "内存 > 75%: -15"
        - "命中率 < 80%: -20"
        - "命中率 < 90%: -10"
        - "连接数 > 9000: -15"
        - "CPU > 80%: -15"
        - "存在慢查询: -10"
        - "存在大 key: -10"
        - "存在热 key: -5"
        - "版本 < 5.0: -5"
        - "noeviction + 内存 > 80%: -10"
        - "备份超 7 天: -10"

  - id: "generate_suggestions"
    description: "按严重程度排序生成修复建议"
    output_format: "Markdown 表格"
    columns:
      - "优先级 (P0/P1/P2)"
      - "实例名称"
      - "问题描述"
      - "当前值"
      - "阈值"
      - "建议操作"
      - "委托 Skill"

  - id: "output_report"
    description: "输出巡检报告"
    outputs:
      - path: "reports/output/redis-health-{customer}-{date}.md"
        format: "Markdown"
      - path: "reports/output/redis-health-{customer}-{date}.json"
        format: "JSON"
```

---

## 3. 阈值定义

| 指标 | Warning 阈值 | Critical 阈值 | 说明 |
|------|-------------|---------------|------|
| 内存使用率 | > 75% | > 85% | 接近 maxmemory 时写入可能失败 |
| 缓存命中率 | < 90% | < 80% | 低命中率意味着缓存效果差 |
| 连接数 | > 5000 | > 9000 | 默认 maxclients 为 10000 |
| CPU 使用率 | > 60% | > 80% | Redis 单线程，高 CPU 影响延迟 |
| Key 淘汰数 | > 0 (6h) | > 1000 (6h) | 大量淘汰说明内存不足 |
| 慢查询 | > 100ms | > 1000ms | 慢查询阻塞单线程 |
| 大 Key | > 1MB | > 10MB | 大 key 操作耗时长 |
| 热 Key | > 1000 qps | > 3000 qps | 热 key 可能导致单点瓶颈 |
| 备份间隔 | > 3 天 | > 7 天 | 备份是数据安全的最后防线 |
| Redis 版本 | < 5.0 | < 4.0 | 旧版本缺少安全和性能改进 |

---

## 4. 告警联动

| 告警类型 | 触发条件 | 自动动作 | 委托 Skill |
|----------|----------|----------|------------|
| 内存 OOM 预警 | 内存 > 85% | 创建 DOPS 工单 | `jdcloud-redis-ops` (modify-cache-instance-class) |
| 命中率下降 | 命中率 < 80% 持续 1h | 创建 DOPS 工单 | 人工排查 |
| 连接数过高 | 连接数 > 9000 | 创建 DOPS 工单 | 人工排查连接泄漏 |
| 备份超期 | 备份 > 7 天 | 自动创建备份 | `jdcloud-redis-ops` (create-backup) |

---

## 5. 闭环改进

| 反馈来源 | 触发条件 | 改进动作 | 责任人 |
|----------|----------|----------|--------|
| 误报 | 内存 > 75% 但实际正常 | 调整阈值或增加白名单 | 运维负责人 |
| 漏报 | 实例 OOM 但未预警 | 降低阈值或增加预测维度 | 运维负责人 |
| 新指标 | 京东云新增监控指标 | 更新 runbook 采集指标列表 | 脚本维护者 |

---

## 6. Changelog

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0.0 | 2026-06-10 | 初始版本，定义 Redis 日常健康巡检完整流程 |
