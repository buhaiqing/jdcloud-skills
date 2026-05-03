# Skills Farm - JDCloud Skills 开发指南

本项目是京东云（JD Cloud）运维 Agent Skills 集合，提供云产品的自动化运维、监控和管理能力。

## 核心价值

**Skills Farm 是一套 Meta Skill（元技能）体系**——将运维知识转化为结构化的、AI Agent 可解析、可执行、可验证的声明式规范。

### 关键特性

| 特性 | 说明 |
|------|------|
| **占位符机制** | `{{env.*}}`（环境变量）、`{{user.*}}`（用户输入）、`{{output.*}}`（输出捕获），实现人机双通道 |
| **职责委托** | `SHOULD/SHOULD NOT Use` 定义边界，跨产品操作自动委派 |
| **生成器** | 输入产品名称和文档 URL，自动生成结构化 Skill |
| **跨平台** | 不绑定特定 Agent 框架，支持 Harness/Claude Code/自定义 MCP |

### 什么是 Meta Skill

**Meta Skill（元技能）**是"生成 Skill 的 Skill"——不是具体云产品的运维能力，而是**生产运维知识的能力**。

| 对比 | 普通 Skill | Meta Skill |
|------|-----------|------------|
| 职责 | 执行特定运维任务 | 生成/编排其他 Skill |
| 示例 | jdcloud-vm-ops 运维云主机 | jdcloud-skill-generator 生成新 Skill |
| 输入 | 环境变量 + 用户指令 | 产品文档 URL + API 定义 |
| 输出 | 执行结果 | 结构化的 Skill 文档 |

核心价值：**"授人以鱼，不如授人以渔。授 AI 以 Skill，更应授之以生成 Skill 的 Meta Skill。"**

> 核心原则：`{{env.*}}` 标记的凭证**严禁向用户索取**，从机制上杜绝泄露。

> **一句话总结**：Skills Farm 让 AI Agent 从"能回答问题"进化到"能自主运维"——每个京东云产品都拥有一个"AI 原生"的运维助手。

## 项目结构

```
jdcloud-skills/
├── README.md                          # 本文件
├── jdcloud-skill-generator/           # Skill 生成器
│   ├── SKILL.md
│   └── references/jdcloud-skill-template.md
└── jdcloud-[product]-ops/             # 产品 Skill
    ├── SKILL.md
    ├── assets/
    └── references/
```

## 什么是 Skill

结构化 Markdown 文档，指导 AI Agent 完成特定任务。包含：元数据、核心功能、使用指南、最佳实践、参考文档。

## JD Cloud CLI

所有 Skill 基于京东云 CLI（`jdc`）与 API 交互。

### 安装

```bash
# pip（推荐）
pip install jdcloud_cli

# 或二进制
curl -fsSL https://github.com/jdcloud-api/jdcloud-cli/releases/latest/download/jdc-linux-amd64.tar.gz | tar -xz && sudo mv jdc /usr/local/bin/
```

### 配置凭证

三种方式（按优先级排序）:

**方式 1：`.env` 文件（本地开发推荐）**
```bash
# 复制示例文件
cp .env.example .env

# 编辑 .env，填入真实凭证
# Agent Runtime 会自动加载
```
```ini
# .env 文件内容示例
JDC_ACCESS_KEY=your_access_key_here
JDC_SECRET_KEY=your_secret_key_here
JDC_REGION=cn-north-1
```

**方式 2：Shell 环境变量（生产环境推荐）**
```bash
# 交互式
jdc config init

# 或手动
jdc configure add --access-key YOUR_KEY --secret-key YOUR_SECRET --region-id cn-north-1
```

**方式 3：CLI 交互式配置**
```bash
jdc config init
```

> **优先级**：Shell 环境变量 > `.env` 文件 > 默认值
> **安全**：`.env` 已在 `.gitignore` 中，不会被提交。生成的 Skill 使用 `{{env.*}}` 占位符，不含真实凭证。

## 开发新 Skill

### 1. 前置准备

引用模板和指南：

```
@jdcloud-skill-generator/SKILL.md
@jdcloud-skill-generator/references/jdcloud-skill-template.md
```

### 2. 开发流程

**提供提示词**：
> "生成京东云 [产品] 的 Skill，名称 jdcloud-xxx-ops，核心功能 [描述]"

**生成结构**：
```
jdcloud-[product]-ops/
├── SKILL.md
├── assets/example-config.yaml
└── references/
    ├── cli-usage.md
    ├── core-concepts.md
    ├── integration.md
    ├── monitoring.md
    └── troubleshooting.md
```

### 3. Skill 文件规范

#### 3.1 元数据头部

```yaml
---
name: jdcloud-[product]-ops
version: 1.0.0
description: 管理京东云 [产品] 资源，包含 CLI 用法、SDK 集成和运维最佳实践。
---
```

#### 3.2 必需章节

变更历史、概述、前提条件、环境变量、核心功能、常用命令、最佳实践、相关链接。

### 4. 编写要点

- CLI 示例：用 `bash`，JSON 用 `json`，YAML 用 `yaml`
- 表格展示：产品列表、监控指标、告警阈值
- 凭证配置见上方环境变量章节

### 6. 验证

```bash
npm install -g markdownlint-cli
markdownlint jdcloud-[product]-ops/SKILL.md
```

验证：CLI 命令可执行、链接有效、示例正确。

### 7. 版本管理

采用 SemVer：`主版本.次版本.修订号`。

更新流程：修改内容 → 更新变更历史 → 更新 version 字段 → 提交。

## 示例：创建云主机 Skill

```bash
mkdir -p jdcloud-vm-ops/references jdcloud-vm-ops/assets

# 引用生成器并提供提示词："生成京东云 VM 的 Skill"

# 验证
head -20 jdcloud-vm-ops/SKILL.md

# 测试
export JDC_ACCESS_KEY="your_key" JDC_SECRET_KEY="your_secret" JDC_REGION="cn-north-1"
jdc vm describe-instances --region-id cn-north-1
```

## Skill 生成器

Meta Skill，从产品文档自动生成运维 Agent Skill。

### 使用

提供：产品名称、文档 URL、API 定义（可选）、CRUD 操作列表、目标运行时。

**示例**：
> "生成京东云云监控 Skill，文档地址：https://docs.jdcloud.com/cn/cloudmonitor，包含告警 CRUD、指标查询"

### 质量检查

**P0 必须**：Trigger & Scope、`{{env.*}}` 占位符、Pre-flight→Execute→Validate→Recovery、故障恢复矩阵、`--no-interactive`/`--output json`、安全确认、超时声明

**P1 建议**：资源声明、一致命名、输出键声明、版本锁定

## 参考资源

- [Skill 生成器](jdcloud-skill-generator/SKILL.md)
- [Skill 模板](jdcloud-skill-generator/references/jdcloud-skill-template.md)
- [JD Cloud CLI](https://github.com/jdcloud-api/jdcloud-cli)
- [Agent Skill OpenSpec](https://agentskills.io/specification)

## 常见问题

| Q | A |
|---|---|
| Skill 和 MCP Server 关系？ | Skill 是文档，MCP 是执行服务 |
| 一个 Skill 覆盖多产品？ | 建议单一职责，通过 Reference 互相引用 |
| 如何更新 Skill？ | 修改后更新 version 和变更历史 |

## 贡献

1. Fork 2. 创建 Skill 目录 3. 按指南编写 4. 提交 PR

---

参考 [jdcloud-vm-ops](jdcloud-vm-ops/) 作为示例。
