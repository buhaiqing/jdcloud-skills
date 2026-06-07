# Runbook 06 — PostgreSQL 巡检

> **场景**: PostgreSQL 实例健康检查、慢查询分析、连接数监控、VACUUM 状态检查  
> **触发方式**: 定时 / 告警触发 / 人工  
> **执行频率**: 每日  
> **适用阶段**: 数据库优化  
> **风险等级**: 中

---

## 目的

本 runbook 定义对 JD Cloud PostgreSQL 实例的巡检流程，包括：
- 实例健康状态检查（连接数、CPU、内存、存储）
- 慢查询分析（执行时间、扫描行数、索引使用情况）
- VACUUM / ANALYZE 状态检查
- 复制延迟检查（只读实例）
- 锁等待与死锁检测

---

## 前置条件

- 目标客户的资源已打标签 `客户=<客户名>`
- 已配置 JD Cloud 凭证
- PostgreSQL 实例状态为 RUNNING

---

## 执行步骤

### Phase 1: 资源发现

```bash
python scripts/01-perceive/cruise_sniff.py --customer <客户名> --region cn-east-2
```

确认以下资源被正确发现：
- [ ] PostgreSQL 实例列表
- [ ] 实例规格（CPU/内存/存储）
- [ ] 网络配置（VPC/子网）
- [ ] 标签信息

### Phase 2: 深度巡检

```bash
python scripts/02-reason/cruise_analyze.py --customer <客户名> \
  --sniff-file reports/output/sniff-<客户名>-<时间戳>.json \
  --hours 6
```

#### 2.1 实例健康检查

| 检查项 | 警告阈值 | 严重阈值 | 说明 |
|--------|----------|----------|------|
| CPU 使用率 | > 70% | > 85% | 持续 5 分钟 |
| 内存使用率 | > 80% | > 90% | 包括 shared_buffers |
| 存储使用率 | > 75% | > 90% | 包括 WAL 占用 |
| 连接数使用率 | > 70% | > 85% | max_connections 百分比 |
| 活跃连接数 | > 50 | > 80 | 活跃查询连接 |

#### 2.2 慢查询分析

慢查询分级：

| 级别 | 执行时间 | 扫描行数 | 影响 |
|------|----------|----------|------|
| 🔴 Critical | > 5s | > 100万 | 严重影响性能 |
| 🟡 Major | > 1s | > 10万 | 需要优化 |
| 🔵 Minor | > 200ms | > 1万 | 建议关注 |

根因分析模式：

| 模式 | 检测方法 | 建议优化 |
|------|----------|----------|
| Missing Index | rows_examined >> rows_returned | CREATE INDEX |
| Sequential Scan | seq_scan 高，idx_scan 低 | 添加条件索引 |
| Lock Contention | wait_event_type = Lock | 缩短事务，优化锁顺序 |
| Idle in Transaction | state = idle in transaction | 设置 idle_in_transaction_timeout |
| VACUUM Lag | dead_tuples > 10000 | 手动 VACUUM ANALYZE |
| Connection Leak | idle 连接持续增长 | 检查连接池配置 |

#### 2.3 VACUUM / ANALYZE 状态

检查项：
- 上次 VACUUM 时间 > 7 天
- dead_tuples / live_tuples 比率 > 10%
- 自动 VACUUM 是否启用
- 需要手动 VACUUM 的表清单

#### 2.4 复制延迟（只读实例）

| 级别 | 延迟时间 | 说明 |
|------|----------|------|
| 🔴 Critical | > 60s | 主从延迟严重 |
| 🟡 Major | > 10s | 需要关注 |
| 🔵 Minor | > 1s | 正常范围内 |

---

## 输出报告

### 报告格式

```json
{
  "service": "rds_postgresql",
  "resource_count": 3,
  "finding_count": 5,
  "findings_by_severity": {
    "critical": 0,
    "major": 2,
    "minor": 3
  },
  "findings": [
    {
      "instance_id": "pg-xxxxxx",
      "instance_name": "xxx-业务系统",
      "severity": "major",
      "category": "slow_query",
      "message": "查询执行时间 3.2s，扫描 50万行",
      "recommendation": "CREATE INDEX idx_xxx ON table(column)",
      "ops_skill": "jdcloud-postgresql-ops"
    }
  ]
}
```

### 人工确认事项

以下发现需要人工确认后通过 `jdcloud-postgresql-ops` 执行：

- [ ] 创建/删除索引
- [ ] 终止长时间运行的查询
- [ ] 手动执行 VACUUM FULL
- [ ] 调整参数（shared_buffers, work_mem 等）
- [ ] 重启实例

---

## 跨 Skill 委托

| 操作 | 委托 Skill |
|------|-----------|
| 查看慢查询详情 | `jdcloud-postgresql-ops` |
| 创建/删除索引 | `jdcloud-postgresql-ops` |
| 调整参数 | `jdcloud-postgresql-ops` |
| 重启实例 | `jdcloud-postgresql-ops` |
| 扩容规格 | `jdcloud-postgresql-ops` |

---

## 持续改进

### 阈值调优触发条件

1. **误报**: 慢查询阈值过低，正常业务被标记
2. **漏报**: 实际性能问题未被检测
3. **新场景**: 发现未覆盖的 PostgreSQL 性能模式

### 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2026-06-08 | 初始版本，支持 PostgreSQL 实例巡检、慢查询分析、VACUUM 检查 |
