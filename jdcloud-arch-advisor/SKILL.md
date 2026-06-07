---
name: jdcloud-arch-advisor
description: >-
  Architecture Review & Design Advisory Engine. Use when user asks for architecture
  review, WAF assessment, architecture recommendation, or reverse-engineering
  existing JD Cloud infrastructure into architectural description. NOT for
  individual resource operations, billing, or health checks.
license: MIT
compatibility: >-
  JD Cloud CLI (`jdc`) 1.2.12+, JD Cloud Python SDK 1.6.26+, Python 3.10 runtime,
  valid API credentials (JDC_ACCESS_KEY / JDC_SECRET_KEY), network access to
  JD Cloud endpoints. Requires jdcloud-vm-ops, jdcloud-vpc-ops, jdcloud-iam-ops, jdcloud-kms-ops,
  jdcloud-clb-ops, jdcloud-cloudmonitor-ops, jdcloud-audit-ops, jdcloud-mysql-ops,
  jdcloud-postgresql-ops, jdcloud-redis-ops, jdcloud-mongodb-ops,
  jdcloud-elasticsearch-ops, jdcloud-eip-ops, jdcloud-tag-audit-ops and
  jdcloud-alert-intelligence skills to be available for full data collection.
metadata:
  author: jdcloud
  version: "1.0.0"
  last_updated: "2026-06-08"
  runtime: Harness AI Agent, Claude Code, Cursor, or compatible Agent runtimes
  python_version_minimum: "3.10"
  type: advisory-framework
  gcl_classification: optional
  gcl_max_iter: 5
  token_budget_estimate: "~8000 tokens (with data collection)"
  references_index:
    - path: "references/core-concepts.md"
      load_condition: "always"
    - path: "references/rules/waf-security.yaml"
      load_condition: "在 Security 支柱评估时"
    - path: "references/rules/waf-reliability.yaml"
      load_condition: "在 Reliability 支柱评估时"
    - path: "references/rules/waf-performance.yaml"
      load_condition: "在 Performance 支柱评估时"
    - path: "references/rules/waf-cost.yaml"
      load_condition: "在 Cost 支柱评估时"
    - path: "references/rules/waf-efficiency.yaml"
      load_condition: "在 Efficiency 支柱评估时"
    - path: "references/scenario-templates/index.yaml"
      load_condition: "在架构方案推荐模式时"
    - path: "references/rubric.md"
      load_condition: "当 GCL 执行时"
    - path: "references/prompt-templates.md"
      load_condition: "当 GCL 执行时"
    - path: "references/integration.md"
      load_condition: "当需要集成或故障排查时"
    - path: "references/troubleshooting.md"
      load_condition: "当执行出错时"
    - path: "references/well-architected-assessment.md"
      load_condition: "在元认知自评时"
---

# JD Cloud Architecture Review & Design Advisory — jdcloud-arch-advisor

> **一句话定位**: 京东云架构的"咨询师"——分析用户现有京东云基础设施的架构面貌，对照京东云 Well-Architected Framework (WAF) 五个支柱进行成熟度评估，并在需要时推荐最优架构方案。**只读顾问**，不执行任何资源变更。

---

## 概述 — 三模式设计

jdcloud-arch-advisor 支持三种操作模式，由 Agent 根据用户意图自动识别并进入：

| 模式 | 名称 | 触发条件 | 核心输出 |
|:----:|------|---------|---------|
| **Mode A** | 架构逆向与分析 | 用户描述了一个现有系统，要求分析其架构 | 架构拓扑 + 组件依赖图 + 技术选型说明 |
| **Mode B** | WAF 成熟度评估 | 用户要求做"架构评审"、"WAF评估"、"健康检查" | 五支柱评分卡 + 风险发现清单 + 改进建议 |
| **Mode C** | 架构方案推荐 | 用户提出新业务需求，要求给出架构方案 | 推荐架构拓扑 + 多方案对比 + 选型理由 |

---

## 五大核心标准

| # | 标准 | 本 Skill 如何实现 |
|---|------|------------------|
| 1 | **清晰边界** | SHOULD/SHOULD NOT Use 精确条件 + 三模式自动识别 + 委托规则表 |
| 2 | **结构化 I/O** | `{{env.*}}` / `{{user.*}}` / `{{output.*}}` 三级占位符 + 报告 JSON 模板 |
| 3 | **明确可执行步骤** | 每个模式：数据采集 → 分析 → 形成报告，三阶段标准流程 |
| 4 | **完整失败策略** | 按错误类型分类 + 数据源不可用时的降级策略 + 用户重试引导 |
| 5 | **绝对单一职责** | 只做架构评审和方案推荐，不做资源操作。通过 delegation 委托下游 Skill |

---

## Well-Architected Framework Integration

本 Skill 的核心评估能力来源于京东云 Well-Architected Framework (WAF) 五支柱。京东云官方尚未发布与阿里云 WAF 完全对齐的公开框架，本 Skill 参考 AWS Well-Architected Framework、阿里云 WAF 以及京东云产品白皮书，定义了适配京东云产品的五支柱评估体系。

| 支柱 | 评估范围 | 数据源依赖 |
|:----:|---------|-----------|
| **Security** | 安全组配置、访问控制、加密策略、审计日志 | `jdcloud-iam-ops`, `jdcloud-kms-ops`, `jdcloud-vm-ops`, `jdcloud-vpc-ops`, `jdcloud-clb-ops`, `jdcloud-audit-ops` |
| **Reliability** | 高可用部署、备份策略、多 AZ 容错、SLA 符合度 | `jdcloud-vm-ops`, `jdcloud-mysql-ops`, `jdcloud-postgresql-ops`, `jdcloud-redis-ops`, `jdcloud-mongodb-ops` |
| **Performance** | 实例规格匹配度、存储 IOPS、网络带宽、负载均衡策略 | `jdcloud-cloudmonitor-ops`, 各产品 ops（规格信息） |
| **Cost** | 资源利用率、闲置资源、规格合理性、付费模式建议 | `jdcloud-cloudmonitor-ops` (利用率), `jdcloud-tag-audit-ops` (资源盘点) |
| **Efficiency** | 自动化程度、运维流程、资源编排合理性 | `jdcloud-tag-audit-ops` (标签治理), `jdcloud-cloudmonitor-ops` (告警覆盖) |

---

## Trigger & Scope

### SHOULD Use

| 场景 | 用户表述示例 | 模式 |
|------|-------------|:----:|
| 分析现有系统架构 | "帮我看看我的系统架构是什么样的"、"分析一下我的云主机 + 数据库架构" | A |
| 架构逆向文档生成 | "我有一套旧的架构，帮我梳理一下文档"、"给现在的系统画个架构图" | A |
| WAF 成熟度评估 | "帮我做一次 WAF 评估"、"架构评审"、"检查是否符合最佳实践" | B |
| 架构安全审计 | "从安全角度评审我的架构"、"检查有没有安全风险" | B (Security) |
| 新系统架构设计 | "我要做一个电商系统，推荐架构方案"、"帮我设计微服务架构" | C |
| 架构改造建议 | "从单体改到微服务，怎么设计"、"现有的架构怎么优化" | C |
| 技术选型对比 | "云主机 vs 容器，我该用哪个"、"推荐数据库方案" | C |

### SHOULD NOT Use

| 场景 | 应该委托给 |
|------|-----------|
| 操作单个资源（创建/修改/删除 VM/RDS） | `jdcloud-vm-ops`, `jdcloud-mysql-ops` 等产品 Skill |
| 查看云产品的具体监控指标 | `jdcloud-cloudmonitor-ops` |
| 查看告警并做降噪分析 | `jdcloud-alert-intelligence` |
| 资源审计（操作审计/资源审计） | `jdcloud-audit-ops` |
| 标签审计与治理 | `jdcloud-tag-audit-ops` |
| 资源成本账单分析 | （无对应 skill，建议走京东云费用中心控制台） |
| 执行自动弹性伸缩 | （无对应 skill，需要人工控制台操作） |
| 故障排查/实时诊断 | （无对应 skill） |

## Delegation Rules

| 能力 | 委托目标 | 说明 |
|------|----------|------|
| VM 资源清单/规格 | `jdcloud-vm-ops` | Mode A/B 数据采集阶段，获取 VM 实例列表、规格、状态 |
| VPC/子网/安全组/路由表 | `jdcloud-vpc-ops` | Mode A/B 获取网络拓扑、安全组规则、路由配置 |
| 数据库实例清单/规格 | `jdcloud-mysql-ops` / `jdcloud-postgresql-ops` / `jdcloud-mongodb-ops` | Mode A/B 获取关系/文档数据库状态、规格、副本配置 |
| Redis 实例 | `jdcloud-redis-ops` | Mode A/B 获取 Redis 缓存架构 |
| Elasticsearch 实例 | `jdcloud-elasticsearch-ops` | Mode A/B 获取 ES 集群状态 |
| 负载均衡 | `jdcloud-clb-ops` | Mode A/B 获取 CLB 监听器、后端服务器、健康检查 |
| 监控指标采集 | `jdcloud-cloudmonitor-ops` | Mode B Performance 支柱评估时获取 CPU/内存/网络/IOPS 利用率 |
| 资源标签与分组 | `jdcloud-tag-audit-ops` | Mode B Efficiency 支柱评估时检查标签治理情况 |
| 操作审计 | `jdcloud-audit-ops` | Mode B Security 支柱评估时检查 ActionTrail 配置 |
| IAM 用户/策略/密钥 | `jdcloud-iam-ops` | Mode B Security 支柱评估时检查 RAM 等价物、AccessKey 轮换 |
| KMS 密钥/加密 | `jdcloud-kms-ops` | Mode B Security 支柱评估时检查密钥轮转与加密策略 |
| EIP 与公网带宽 | `jdcloud-eip-ops` | Mode A/B 获取 EIP 绑定情况 |
| 告警降噪分析 | `jdcloud-alert-intelligence` | 配合 Mode B 关联告警事件作为输入 |
| GCL 质量门禁 | `jdcloud-skill-generator` (作为元 skill) | 本 Skill GCL classification 为 `optional`，仅在特定场景触发 |

### 降级策略

京东云生态**没有等价的** `alicloud-topo-discovery` / `alicloud-advisor-ops` Skill，因此本 Skill 的数据采集采用**多 Skill 委托 + 并行调用**策略：

```
[arch-advisor]
     │
     ├── jdcloud-vm-ops (describe-instances, describe-instance-type)
     ├── jdcloud-mysql-ops (describe-instances)
     ├── jdcloud-redis-ops (describe-cache-instances)
     ├── jdcloud-clb-ops (describe-load-balancers)
     ├── jdcloud-iam-ops (list-sub-users, list-policies)
     ├── jdcloud-kms-ops (list-keys)
     ├── jdcloud-eip-ops (describe-eips)
     ├── jdcloud-cloudmonitor-ops (get-metric-data)
     ├── jdcloud-audit-ops (describe-trails)
     └── jdcloud-tag-audit-ops (list-tagged-resources)
```

当任一 Skill 不可用时，降级为：用户自行描述 + 报告中标注 `low confidence`。

---

## Variable Convention

### 环境变量 — `{{env.*}}`

| 变量 | 说明 | 来源 |
|------|------|------|
| `{{env.JDC_ACCESS_KEY}}` | 京东云 AccessKey ID | 运行时环境 (NEVER ask) |
| `{{env.JDC_SECRET_KEY}}` | 京东云 AccessKey Secret | 运行时环境 (NEVER ask, NEVER log) |
| `{{env.JDC_REGION}}` | 默认地域（如 `cn-north-1`） | 运行时环境 |

### 用户输入 — `{{user.*}}`

| 变量 | 说明 | 模式 |
|------|------|:----:|
| `{{user.scenario}}` | 用户业务场景描述 | A/B/C |
| `{{user.current_architecture}}` | 用户描述的现有架构 | A |
| `{{user.goal}}` | 业务目标和非功能性需求 | C |
| `{{user.constraints}}` | 预算、时间、技术栈约束 | C |
| `{{user.focus_pillar}}` | 指定评估支柱 | B |
| `{{user.target_resources}}` | 待分析的资源 ID 列表 | A/B |

### 输出变量 — `{{output.*}}`

| 变量 | 说明 | 来源 |
|------|------|------|
| `{{output.architecture_report}}` | 完整架构分析报告 Markdown | Mode A/B/C |
| `{{output.architecture_topology}}` | 架构拓扑 JSON | Mode A/C |
| `{{output.waf_scores}}` | 五支柱评分 JSON | Mode B |
| `{{output.recommendations}}` | 改进/推荐方案清单 | Mode B/C |
| `{{output.risk_findings}}` | 风险发现清单 JSON | Mode B |

---

## API and Response Conventions

本 Skill 不直接调用 OpenAPI，而是通过委托下游 Skill 获取数据。输出采用标准报告格式：

### 架构报告 JSON 规范

```json
{
  "report_id": "arch-report-20260608-001",
  "mode": "A | B | C",
  "cloud": "jdcloud",
  "generated_at": "2026-06-08T12:00:00Z",
  "data_sources": [
    { "skill": "jdcloud-vm-ops", "timestamp": "2026-06-08T11:55:00Z" },
    { "skill": "jdcloud-mysql-ops", "timestamp": "2026-06-08T11:56:00Z" }
  ],
  "architecture": {
    "overview": "三层 Web 架构：CLB → VM (Nginx+PHP) → JCS for MySQL",
    "components": [...],
    "dependencies": [...],
    "deployment_layout": "..."
  },
  "waf_assessment": {
    "scores": { "security": 0.85, "reliability": 0.70, "performance": 0.60, "cost": 0.75, "efficiency": 0.65 },
    "composite_score": 0.71,
    "findings": [...]
  },
  "recommendations": [
    { "priority": "P0", "pillar": "reliability", "title": "MySQL 单节点风险", "action": "升级到高可用版", "effort": "medium" }
  ]
}
```

### 报告 Markdown 格式

所有报告最终以 Markdown 呈现给用户，包含：
1. **摘要** — 一句话结论 + composite score（Mode B）
2. **架构概览** — 组件列表 + 交互关系图（文本模式）
3. **WAF 评估矩阵** — 五支柱评分表
4. **风险发现** — P0-P3 分级
5. **改进建议** — 优先级排序，含预估 work effort
6. **数据源记录** — 报告中所引用的数据来源

---

## Quick Start

### 前置条件

```bash
# 验证环境
jdc --version          # >= 1.2.12
python --version       # >= 3.10（不是 3.12，jdcloud_sdk 1.x 不兼容）
test -n "$JDC_ACCESS_KEY" && echo "AK OK" || echo "AK MISSING"
test -n "$JDC_SECRET_KEY" && echo "SK OK" || echo "SK MISSING"
test -n "$JDC_REGION" && echo "Region: $JDC_REGION" || echo "Region MISSING"

# 验证 CLI 凭证（jdc 读取 ~/.jdc/config，不是环境变量）
mkdir -p ~/.jdc
printf "%s" "default" > ~/.jdc/current   # 注意：无换行
ls ~/.jdc/config
```

### Mode A — 架构逆向与分析

1. 委托 `jdcloud-vm-ops` 获取 VM 资源清单
2. 委托 `jdcloud-mysql-ops` / `jdcloud-redis-ops` / `jdcloud-clb-ops` 等获取其他组件
3. 分析组件依赖关系，识别技术选型
4. 生成架构拓扑文档

### Mode B — WAF 成熟度评估

1. 确认评估范围（全量评估或指定支柱）
2. 委托各产品 ops Skill 采集资源清单
3. 委托 `jdcloud-cloudmonitor-ops` 获取监控指标（Performance 支柱专用）
4. 对照 WAF 5 支柱逐项评分
5. 生成评估报告

### Mode C — 架构方案推荐

1. 收集用户需求（业务场景、非功能性需求、约束条件）
2. 参考 `references/scenario-templates/` 中的架构模板
3. 对比至少 2 个可行方案
4. 推荐最优方案及选型理由

### 使用 Script 入口

```bash
# Mode A + B 评估（自动反向工程 + WAF 评分）
./scripts/assess.sh --region cn-north-1 --pillars security,reliability

# Mode C 方案推荐
./scripts/recommend.sh --scenario ecommerce --dau 50000
```

---

## Execution Flows

### Mode A — 架构逆向与分析流程

```
Phase 1 — 数据采集
  1. 询问用户系统的大致构成（用什么产品、多少实例、地域分布）
  2. 委托 jdcloud-vm-ops 扫描 VM 资源（describe-instances）
  3. 委托 jdcloud-clb-ops 扫描负载均衡（describe-load-balancers）
  4. 委托 jdcloud-mysql-ops / jdcloud-redis-ops / jdcloud-mongodb-ops 扫描数据层
  5. 委托 jdcloud-iam-ops / jdcloud-kms-ops / jdcloud-eip-ops 补充支撑组件
  6. 委托 jdcloud-tag-audit-ops 获取资源标签用于归类

Phase 2 — 架构分析
  1. 绘制组件依赖图（文本格式）
  2. 识别架构模式（单节点 / 三层 / 微服务 / Serverless）
  3. 标记潜在技术债务和风险点

Phase 3 — 报告产出
  1. 生成架构拓扑 JSON
  2. 生成 Markdown 架构描述文档
  3. 标注风险点和改进机会
```

### Mode B — WAF 成熟度评估流程

```
Phase 1 — 数据采集
  1. 委托各产品 ops Skill 获取完整资源清单
  2. 委托 jdcloud-cloudmonitor-ops 获取关键资源的利用率指标
  3. 委托 jdcloud-iam-ops 检查用户/策略/密钥
  4. 委托 jdcloud-kms-ops 检查密钥轮转
  5. 委托 jdcloud-audit-ops 检查操作审计配置
  6. 委托 jdcloud-tag-audit-ops 检查标签治理
  7. 询问用户补充信息（备份策略、变更流程等）

Phase 2 — 五支柱评分
  1. Security: 检查安全组规则、IAM 策略、加密配置、ActionTrail
  2. Reliability: 检查多 AZ 部署、备份策略、HA 配置、CLB 健康检查
  3. Performance: 检查规格匹配度、IOPS/带宽、连接数、响应时间
  4. Cost: 检查闲置资源、规格合理性、付费模式
  5. Efficiency: 检查标签治理、监控告警、自动化程度

Phase 3 — 报告产出
  1. 生成五支柱评分雷达图（文本版）
  2. 按 P0-P3 分级的风险发现清单
  3. 针对每个发现的改进建议
  4. 跨支柱权衡指引
```

### Mode C — 架构方案推荐流程

```
Phase 1 — 需求收集
  1. 业务场景：用户的核心业务是什么
  2. 非功能性需求：可用性目标、性能要求、数据量预估
  3. 约束条件：预算、技术栈偏好、合规要求
  4. 时间线：上线时间要求

Phase 2 — 方案设计
  1. 参考场景模板库 matching 最佳实践
  2. 设计 2-3 个候选方案
  3. 对比各方案的 WAF 覆盖度、成本、复杂度

Phase 3 — 推荐与报告
  1. 推荐最优方案及选型理由
  2. 推荐架构拓扑（文本描述）
  3. 实施路线图建议（分阶段上线）
  4. 成本估算和 TCO 对比
```

---

## Safety Gates

| 红线 | 要求 | 违反后果 |
|------|------|----------|
| 本 Skill NEVER 执行写操作 | 只读顾问，不得创建/修改/删除任何资源 | GCL Safety = 0, 立即 ABORT |
| 委托下游 Skill 时必须传递完整上下文 | 确保下游 Skill 有足够信息准确执行 | 报告质量下降 |
| 用户数据保密 | 报告中不得包含 AK/SK 等凭证信息 | 严重违规 |
| AK/SK 仅通过 `{{env.*}}` 传递 | 不得要求用户提供、不得在输出中回显 | 严重违规 |
| 不确定性场景需向用户明示 | 数据源不完整时需标注 confidence 级别 | 误导用户决策 |

---

## Quality Gate (GCL)

### GCL Classification

| 属性 | 值 |
|:----|:---|
| Classification | `optional` |
| max_iter | 5 |
| 触发条件 | 当 Agent 输出的架构建议涉及重大架构变更建议时（如推荐从单体迁移到微服务） |
| 不触发条件 | 纯数据查询、简单 WAF 评估报告 |

### Rubric Dimensions

| 维度 | 阈值 | 说明 |
|------|:---:|------|
| **Correctness** | >= 0.7 | 架构分析结论与实际资源状态一致，推荐方案技术可行 |
| **Safety** | = 1.0 | 没有写操作、没有越权建议、没有凭据暴露 |
| **Traceability** | >= 0.8 | 报告标注了每个结论的数据来源 skill 和时间戳 |
| **Spec Compliance** | >= 0.8 | 遵循 WAF 标准定义和评估流程 |

> 完整评分规则见 `references/rubric.md`，提示词模板见 `references/prompt-templates.md`。

---

## Well-Architected Assessment

本 Skill 自身的五支柱评估（元认知）：

| 支柱 | 核心原则 |
|:----|---------|
| **Security** | 只读设计，不操作资源。委托下游时传递最小授权上下文 |
| **Reliability** | 三模式标准化流程 + 数据源降级策略 + 输出验证 |
| **Cost** | 通过 Cost 支柱评估帮助用户发现省钱机会；自身零资源消耗 |
| **Efficiency** | 三模式覆盖面广，适配多种用户意图；报告模板复用 |
| **Performance** | 数据采集阶段委托下游 Skill 并行执行，报告生成 < 30s |

> 完整自评见 `references/well-architected-assessment.md`。

---

## Changelog

| 版本 | 日期 | 变更 |
|:----|:----|------|
| 1.0.0 | 2026-06-08 | 初始版本：三模式定义 + WAF 五支柱评估体系 + 委托规则 + GCL optional。镜像 alicloud-arch-advisor，适配京东云产品与 Skill 生态 |
