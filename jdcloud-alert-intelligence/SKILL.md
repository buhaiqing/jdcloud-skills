---
name: jdcloud-alert-intelligence
description: >-
  京东云告警智能助手。Use when 京东云账户/项目/资源 已产生告警后,需要
  分级、聚合、抑制、降噪、值班疲劳统计 或 生成可读性高的告警分析报告。
  Trigger keywords: 告警降噪, 告警分析, 告警分级, 告警聚合, 告警抑制,
  on-call 疲劳, alert fatigue, alert aggregation, alert grouping,
  京东云告警, 告警历史分析, 告警模板。
  仅适用于已有告警的二次处理(只读);不创建告警规则(用 jdcloud-cloudmonitor-ops),
  不修产品配置(用各 jdcloud-*-ops)。
license: MIT
compatibility: >-
  jdc CLI 1.2.12+; 京东云账户已开通云监控;
  已配置 JDC_ACCESS_KEY / JDC_SECRET_KEY / JDC_REGION。
metadata:
  author: buhaiqing
  version: "0.4.0"
  last_updated: "2026-06-18"
  runtime: Harness AI Agent
  api_profile: "monitor v1 - https://docs.jdcloud.com/cn/monitoring/api/overview"
  cli_applicability: jdc-first-with-fallback
  cli_version_locked: "1.2.12"
  parent_skill: jdcloud-cloudmonitor-ops
  ecosystem_skills:
    - jdcloud-cloudmonitor-ops
    - jdcloud-vm-ops
    - jdcloud-clb-ops
    - jdcloud-redis-ops
    - jdcloud-rds-ops
---

> 本 Skill 遵循 [Agent Skill OpenSpec](https://agentskills.io/specification)。
> 京东云 Skills Farm 元规范：详情见 [`../jdcloud-skill-generator/SKILL.md`](../jdcloud-skill-generator/SKILL.md)。

# 京东云告警智能助手 (jdcloud-alert-intelligence)

## Overview

**京东云告警智能助手** 是云监控的**告警后处理层**：从 `jdc monitor describe-alarm-history`
拉取原始告警事件，做**聚合 → 分级 → 抑制 → 报告**四步处理，降低 on-call 工程师的告警疲劳。

**本 Skill 范围严格限定：**

- ✅ 拉取告警历史、统计、聚合、分级、抑制
- ❌ **不**创建 / 修改 / 删除告警规则 → 委派 [`jdcloud-cloudmonitor-ops`](../jdcloud-cloudmonitor-ops/SKILL.md)
- ❌ **不**修复底层资源问题 → 委派各 `jdcloud-*-ops`
- ❌ **不**配置告警联系人/通知渠道 → 委派 `jdcloud-cloudmonitor-ops`

## Changelog

| 版本 | 日期 | 变更 |
|------|------|------|
| 0.4.0 | 2026-06-18 | **GCL v2 rollout**: Phase 6 H (optional) + Phase 7 Reflexion. Extracted detailed GCL guide to `references/quality-gate.md`. |
| 0.3.0 | 2026-06-10 | §1.3 联动；8/8 refs 补齐；业务 tag 统一；新增 api-sdk/integration/monitoring/troubleshooting refs。 |
| 0.1.0 | 2026-06-03 | 初版：聚合 / 分级 / 抑制 / 报告四件套。 |

## 触发范围

### 应使用本 Skill

- "今天告警太多，帮我看看哪些是同一类"
- "上周 on-call 被打扰了多少次？"
- "这个告警严重吗？P0 还是 P3？"
- "告警风暴期哪些是真正的故障、哪些是误报？"
- "生成一份本周告警周报"

### 不应使用本 Skill

| 用户问题 | 应委派给 |
|---|---|
| 创建/修改告警规则、配置阈值 | `jdcloud-cloudmonitor-ops` |
| 告警说 VM CPU 高，帮我扩容/重启 | `jdcloud-vm-ops` |
| 告警说 LB 5xx 增多，帮我看后端 | `jdcloud-clb-ops` |
| 告警说 Redis 慢，帮我看大 Key | `jdcloud-redis-ops` |
| 实时监控大盘/面板 | `jdcloud-cloudmonitor-ops` (monitoring.md) |
| 阿里云/腾讯云/AWS 告警 | 对应云的 skill，本 skill 仅京东云 |

### 委派规则

- 本 Skill **只读**，**永不**自动调用其他 `jdcloud-*-ops` 执行变更动作
- 分析完成后，输出**下一跳建议**，由用户/上层 Agent 决定是否委派
- 委派建议格式：`→ 建议使用 \`jdcloud-vm-ops\` 升级实例规格`

## 变量约定

| 占位符 | 含义 | Agent 行为 |
|--------|------|-----------|
| `{{env.JDC_ACCESS_KEY}}` | 凭证 | 绝不向用户索取；未设置则失败 |
| `{{env.JDC_SECRET_KEY}}` | 凭证 | 同上；**绝不打印或记录** |
| `{{env.JDC_REGION}}` | 默认区域 | 默认 `cn-north-1` |
| `{{user.region}}` | 区域 | 询问一次，缓存复用 |
| `{{user.time_window}}` | 时间窗 | ISO 8601 区间，默认"最近 24h" |
| `{{user.severity_filter}}` | 分级过滤 | 可选 P0/P1/P2/P3 |
| `{{user.service_filter}}` | 服务过滤 | 可选服务代码 (vm/rds/lb/redis/...) |
| `{{output.alarm_id}}` | 告警 ID | 从 `$.result.alarmHistoryList[*].alarmId` 解析 |

## 工作流（5 步）

| 步骤 | 动作 | 关键约束 | 详细文档 |
|---|---|---|---|
| 0. 前置检查 | 确认凭证、时间窗、只读边界 | 时间窗 ≤ 15d | [cli-usage.md](./references/cli-usage.md) |
| 1. 拉取 | `jdc monitor describe-alarm-history` | `--output json`，失败 3 次后回退 | [cli-usage.md](./references/cli-usage.md) |
| 2. 聚合 | 按 `(service, resource, metric)` 聚簇 | 三元组必须完整 | [playbook-aggregate.md](./references/playbook-aggregate.md) |
| 3. 分级 | P0-P3 矩阵 | 每簇附 4-tuple 引用 | [severity-matrix.md](./references/severity-matrix.md) |
| 4. 抑制 | 维护窗/周期性/已知误报降档 | 必须引用规则 | [suppression-rules.md](./references/suppression-rules.md) |
| 5. 报告 | 按模板输出 | P0/P1 必须有下一跳建议 | [assets/report-template.md](./assets/report-template.md) |

## 输出解析规则

| 操作 | JSON 路径 | 类型 |
|---|---|---|
| 告警历史查询 | `$.result.alarmHistoryList[*]` | array |
| 告警规则列表 | `$.result.alarms[*].alarmId` | array |
| 告警规则详情 | `$.result.alarm.status` | string (`ALARM`/`OK`/`INSUFFICIENT_DATA`) |
| 监控项查询 | `$.result.metrics[*].metric` | array |
| 监控数据查询 | `$.result.metricDatas[*].dataPoints` | array |

## 安全、原则与约束

- **凭证**：绝不输出/记录 `JDC_SECRET_KEY`；检查仅 `test -n`，状态用 `<masked>`
- **只读**：不创建/修改/删除告警规则，不修复产品配置，不改任何云资源
- **不编造**：缺失数据答"暂无相关信息"；jdc 失败则返回已有数据 + 错误说明
- **不替用户决策**：只输出分级 + 下一跳建议；动作必须用户/上层 Agent 确认
- **自检清单**：时间窗 ≤ 15d；凭证未打印；聚合键完整；P0/P1 有下一跳建议；数字可追溯到 jdc 响应

## 参考文档索引

- **核心 / CLI / SDK / 集成 / 排错**：`references/core-concepts.md`、`cli-usage.md`、`api-sdk-usage.md`、`integration.md`、`troubleshooting.md`
- **业务手册**：`severity-matrix.md`、`suppression-rules.md`、`playbook-aggregate.md`、`playbook-classify.md`、`playbook-suppress.md`
- **GCL 与模板**：`rubric.md`、`prompt-templates.md`、`quality-gate.md`
- **示例与同步**：`examples.md`、`r1-r2-r3-sync.md`
- **跨 session 失败记忆**：`../docs/failure-patterns.md`

## Quality Gate (GCL)

This skill participates in the repository-wide **Generator-Critic-Loop** defined
in `AGENTS.md` §Quality Gate. It is **optional** for this read-only skill.

| Parameter | Value |
|---|---|
| `max_iterations` | **5** |
| `rubric_version` | **v2** |
| `trace_path` | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` |
| `safety_confirm_required` | **false** |
| `hallucination_check` | **optional** |
| `reflexion_integration` | **enabled** |

GCL wraps the 5-step workflow: Generator fetches alert data, optional
Hallucination Detector checks command structure, Critic scores against the
rubric, Orchestrator persists the trace. Full details:
[references/quality-gate.md](references/quality-gate.md).
