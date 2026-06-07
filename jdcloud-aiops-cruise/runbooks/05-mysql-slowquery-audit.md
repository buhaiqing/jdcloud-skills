---
runbook_id: "05"
scenario: "MySQL 慢查询巡检"
version: "1.0.0"
last_updated: "2026-06-08"
trigger: "定时调度（每日）/ 告警触发 / 人工触发"
risk_level: "中"
execution_time_estimate: "5-10 分钟（10 个实例以内）"
dependencies:
  - "jdcloud-mysql-ops"  # 依赖 MySQL ops skill 的慢查询分析能力
---

# MySQL 慢查询巡检

## 1. 场景描述

对指定客户（通过 `客户` 标签识别）在京东云上的所有 RDS MySQL 实例进行慢查询巡检，覆盖：
- **感知层**: 自动发现 MySQL 实例，查询慢日志
- **分析层**: 严重度分级、根因分析、优化建议生成
- **优化层**: 输出可执行的 SQL 优化方案，跟踪优化效果

### 适用条件

- 资源已按 `客户` 标签归类（如 `客户=烟台振华`）
- MySQL 实例已开启 `slow_query_log`（建议 `long_query_time=1s`）
- 具备 `jdcloud-mysql-ops` skill 的执行权限

### 不适用条件

- 未开启慢日志的实例 → 输出警告，建议开启
- PostgreSQL/MongoDB 实例 → 使用对应 ops skill

---

## 2. 执行流程

### Phase 1: 嗅探 + 实例发现（约 1-2 分钟）

```yaml
steps:
  - id: "discover_mysql_instances"
    description: "扫描指定客户标签下的所有 RDS MySQL 实例"
    api_calls:
      - "rds describe-instances"  # 过滤 engine=MySQL + 客户标签
    region: "自动探测（从已有资源推断）"
    outputs:
      - "MySQL 实例列表"
      - "实例状态（running/stopped）"
      - "慢日志开启状态"

  - id: "validate_slowlog_config"
    description: "检查慢日志配置"
    checks:
      - "slow_query_log = ON"
      - "long_query_time 建议值 <= 1s"
      - "log_queries_not_using_indexes = ON（可选）"
    warning_if_not_configured: "建议开启慢日志以获取完整分析数据"

  - id: "build_mysql_topology"
    description: "构建 MySQL 实例拓扑"
    outputs:
      - "实例 ID → 名称 → 规格映射"
      - "关联的应用标签（如 环境=生产, 应用=订单服务）"
      - "待分析实例清单"
```

### Phase 2: 慢查询深度分析（约 4-8 分钟）

```yaml
steps:
  - id: "query_slow_logs"
    description: "查询每个 MySQL 实例的慢日志"
    time_window:
      daily_audit: "最近 24 小时"
      alarm_triggered: "告警触发前 15 分钟"
      manual: "用户指定时间范围（最大 7 天）"
    api_calls:
      - "rds describe-slow-logs"
    filters:
      - "可按账号、SQL 关键词过滤"
      - "按执行时间/次数/扫描行数排序"

  - id: "analyze_slow_queries"
    description: "执行三阶段慢查询分析"
    analysis_pipeline:
      phase_1_severity:
        - "🔴 Critical: avg_time >= 5000ms OR total_time >= 300000ms OR count >= 10000"
        - "🟡 Major: avg_time >= 1000ms OR rows_examined >= 500000 OR count >= 1000"
        - "🔵 Minor: 其他慢查询"
      phase_2_root_cause:
        - "🏷️ Missing Index: rows_examined >> rows_sent"
        - "📊 Full Table Scan: 无 WHERE 或 WHERE 无索引"
        - "🔒 Lock Contention: lock_time > 30% total_time"
        - "🔗 Inefficient JOIN: 多表 JOIN 扫描大量行"
        - "📦 Large Result Set: rows_sent > 10000"
        - "⏰ Frequent Small Query: count > 1000 AND avg_time < 500ms"
        - "📐 Temp Table / File Sort: ORDER BY 无索引"
      phase_3_optimization:
        - "生成 CREATE INDEX 语句"
        - "生成优化后的 SQL 示例"
        - "预估优化收益（时间降低百分比）"

  - id: "aggregate_cross_instance"
    description: "跨实例聚合分析（多实例场景）"
    when: "发现多个 MySQL 实例"
    outputs:
      - "全局 Top 10 慢查询"
      - "按应用分组的问题分布"
      - "跨实例共性根因"

  - id: "trend_comparison"
    description: "趋势对比（昨日/上周）"
    when: "daily_audit 模式"
    metrics:
      - "慢查询模式数变化"
      - "Critical/Major 级别数量变化"
      - "总执行耗时变化"
      - "已优化项确认（对比昨日建议）"

  - id: "generate_report"
    description: "输出双格式报告"
    outputs:
      - path: "reports/output/mysql-sniff-{customer}-{date}.json"
        format: "JSON（Phase 1 结果 / 实例清单）"
      - path: "reports/output/mysql-cruise-{customer}-{date}.json"
        format: "JSON（Phase 2 完整分析报告）"
      - path: "reports/output/mysql-cruise-{customer}-{date}.md"
        format: "Markdown（给人读的摘要报告）"
```

---

## 3. 阈值定义

| 严重度 | 判定条件 | 建议行动 |
|---|---|---|
| 🔴 **Critical** | `executionTimeAvg >= 5000ms` OR `executionTimeSum >= 300000ms` OR `executionCount >= 10000` | 立即处理，建议当日修复 |
| 🟡 **Major** | `executionTimeAvg >= 1000ms` OR `rowsExaminedSum >= 500000` OR `executionCount >= 1000` | 本周内修复，优先级高 |
| 🔵 **Minor** | 其他慢查询 | 记录在案，择机优化 |

### 根因判定规则

| 根因类型 | 判定规则 | 优化建议模板 |
|---|---|---|
| 🏷️ Missing Index | `rowsExaminedSum > rowsSentSum × 100` AND `executionTimeAvg > 500` | `CREATE INDEX idx_{table}_{col} ON {table}({col})` |
| 📊 Full Table Scan | 无 `WHERE` 子句 OR `WHERE` 条件无索引列 | 添加 WHERE 条件或创建覆盖索引 |
| 🔒 Lock Contention | `lockTimeSum > executionTimeSum × 0.3` | 缩短事务范围，降低隔离级别 |
| 🔗 Inefficient JOIN | `JOIN` 表数 >= 2 AND `rowsExaminedSum > 500000` | 添加 JOIN 列索引，调整驱动表 |
| 📦 Large Result Set | `rowsSentSum > 10000` AND `executionTimeAvg > 2000` | 添加 LIMIT，只查询需要的列 |
| ⏰ Frequent Small Query | `executionCount > 1000` AND `executionTimeAvg < 500` | 合并批量查询，添加缓存 |
| 📐 Temp Table / File Sort | `ORDER BY` 无索引 AND `rowsExaminedSum > 100000` | 为排序列创建索引 |

---

## 4. 报告模板

### Markdown 报告结构

```markdown
# MySQL 慢查询巡检报告 —— {{customer}}

## 📊 概览
- 巡检时间: {{start_time}} ~ {{end_time}}
- 实例数: {{instance_count}}
- 慢查询模式数: {{slow_query_patterns}}
- Critical: {{critical_count}} | Major: {{major_count}} | Minor: {{minor_count}}

## 🔴 Critical 问题（建议立即处理）
{{#each critical_queries}}
### {{index}}. {{sql_truncated}}
- **实例**: {{instance_id}}
- **执行**: {{executionCount}} 次，平均 {{executionTimeAvg}}ms，总计 {{executionTimeSum}}ms
- **根因**: {{root_cause_icons}} {{root_cause_labels}}
- **建议**: {{optimization_advice}}
- **预期收益**: {{estimated_impact}}
{{/each}}

## 🟡 Major 问题（建议本周修复）
...

## 📈 趋势对比（vs 昨日）
- 慢查询模式数: {{yesterday_patterns}} → {{today_patterns}} ({{trend}})
- Critical: {{yesterday_critical}} → {{today_critical}} ({{trend}})
- 总执行耗时: {{yesterday_time}}ms → {{today_time}}ms ({{trend}})

## ✅ 已优化确认
{{#each confirmed_optimizations}}
- {{instance_id}}: {{description}} ✅
{{/each}}

## 📋 Quick Wins（低投入高回报）
{{#each quick_wins}}
1. [{{root_cause}}] {{description}}
   → {{action}}
{{/each}}
```

---

## 5. 闭环改进

| 反馈来源 | 触发条件 | 改进动作 | 责任人 |
|---|---|---|---|
| 人工审阅报告 | 误报 / 漏报 / 根因判定错误 | 更新阈值定义 + 优化根因规则 | DBA / 运维负责人 |
| 优化效果验证 | 优化后性能未达预期 | 调整优化建议模板 | DBA |
| 新发现 | 未覆盖的 SQL 模式 | 新增根因类型 + 更新 runbook | 脚本维护者 |
| 慢日志配置问题 | 大量实例未开启慢日志 | 推动配置基线整改 | 运维负责人 |

---

## 6. 跨 Skill 协作

| 场景 | 委托 Skill | 说明 |
|---|---|---|
| MySQL 实例创建/删除/规格变更 | `jdcloud-mysql-ops` | 本 Skill 只读，不执行变更 |
| 慢日志配置修改 | `jdcloud-mysql-ops` | 通过 modify-instance 修改参数 |
| 索引创建/删除 DDL | `jdcloud-mysql-ops` | 优化建议中的 DDL 需人工确认后执行 |
| 监控告警规则配置 | `jdcloud-cloudmonitor-ops` | 配置慢查询告警阈值 |

---

## 7. Changelog

| 版本 | 日期 | 变更内容 |
|---|---|---|
| 1.0.0 | 2026-06-08 | 初始版本，定义 MySQL 慢查询巡检完整流程 |