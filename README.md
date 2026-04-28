# Skills Farm - JDCloud Skills 开发指南

本项目是京东云（JDCloud）Skills 的集合，提供各类云产品的运维、监控和管理能力。

## Meta Skill：让 AI Agent 学会"学会运维"

> **"授人以鱼，不如授人以渔。授 AI 以 Skill，更应授之以生成 Skill 的 Meta Skill。"**

**Skills Farm 本质上是一套 Meta Skill（元技能）体系**。它不是某个具体云产品的运维脚本，而是一个**可复用的技能工厂**——让运维知识从"师傅的口口相传"和"散落在各处的人类文档"中脱离出来，转化为**结构化的、AI Agent 可解析、可执行、可验证的声明式规范**。

### 核心技术创新

**1. 人机双通道的声明式语义**

传统文档面向人类阅读，AI 难以精确提取执行指令。本体系通过一系列结构化的占位符约定，实现了**人机双通道通信**：

- `{{env.*}}` 占位符：标记 Agent 运行时注入的环境变量（如密钥），**严禁向用户索取**，从机制上杜绝凭证泄露
- `{{user.*}}` 占位符：标记必须交互式收集的用户输入，Agent 自动执行"询问一次，全局复用"的策略
- `{{output.*}}` 占位符：标记上游命令的输出捕获点，实现**Skill 内部的任务编排与数据流转**

这种设计在没有引入任何程序代码的情况下，用纯 Markdown 实现了**防提示注入、输入校验、数据流编排**等工程级能力。

**2. "文档即契约"的 Agent 集成范式**

每个 Skill 通过 `SHOULD/SHOULD NOT Use` 触发条件章节，定义了自己的**职责边界和委托规则**。当用户请求跨产品操作时，META Skill 自动判定责任链，将子任务委派给对应产品的 Skill。这是一种**基于文档的微服务编排**。

**3. 从产品文档到 Agent 可执行规范的自动化流水线**

结合 `jdcloud-skill-generator`（Skill 生成器），只需输入产品名称和文档 URL，即可自动抽取 API 定义和产品文档，生成结构化的 Agent Skill。配合内置的 **Agent-Ready Quality Checklist**（前置检查 / 执行命令 / 后置验证 / 故障恢复矩阵），确保每个生成的 Skill 都达到**可上线执行的质量标准**。

**4. 跨 Agent 运行时可移植性**

Skill 文档不绑定任何特定 Agent 框架。无论是 Harness AI Agent、Claude Code、还是自定义的 MCP Server，只要 Agent 具备 Shell 执行能力和环境变量注入能力，均可直接消费 Skill 并执行。Skill 是**运维知识跨平台流通的统一载体**。

| 维度 | 传统运维文档 | Skills Farm Meta Skill |
|------|-------------|----------------------|
| 目标读者 | 人类 | 人类 + AI Agent（双通道） |
| 可执行性 | 需要人工理解和操作 | Agent 自动解析并执行 |
| 安全性 | 凭证管理依赖人工意识 | 占位符机制硬性隔离，杜绝泄露 |
| 规模化 | 每产品独立编写 | 模板 + 生成器流水线，批量生产 |
| 质量保证 | 靠个人经验 | 内置 Checklist + 验证机制 |
| 跨平台 | 绑定具体系统 | MCP/CLI 通用接口，框架无关 |

> **一句话总结**：Skills Farm 不只是一个运维工具集，它是**让 AI Agent 从"能回答问题"进化到"能自主运维"的关键基础设施**——通过 Meta Skill 把运维知识系统化、结构化、可执行化，让每一个京东云产品都能拥有一个"AI 原生"的运维助手。

## 项目结构

```
jdcloud-skills/
├── README.md                          # 本文件
├── jdcloud-skill-template.md          # Skill 模板文件
├── jdcloud-skill-generator-guide.md   # Skill 生成器指南
└── jdcloud-cloudmonitor-ops/          # 云监控 Skill 示例
    ├── SKILL.md                       # Skill 主文件
    ├── assets/                        # 资源文件
    └── references/                    # 参考文档
        ├── cli-usage.md
        ├── core-concepts.md
        ├── integration.md
        ├── monitoring.md
        └── troubleshooting.md
```

## 什么是 Skill

Skill 是一种结构化的 Markdown 文档，用于指导 AI Agent 完成特定任务。每个 Skill 包含：

- **元数据**：名称、版本、描述
- **核心功能**：该 Skill 能做什么
- **使用指南**：如何调用和使用
- **最佳实践**：推荐的运维方式
- **参考文档**：详细的技术文档

## 开发新 Skill

### 1. 前置准备

确保已阅读以下参考文档：

- **[jdcloud-skill-template.md](jdcloud-skill-template.md)** - Skill 模板文件，包含标准结构和占位符
- **[jdcloud-skill-generator-guide.md](jdcloud-skill-generator-guide.md)** - 生成器详细指南，说明如何基于模板生成 Skill

### 2. 开发流程

#### 步骤 1：引用参考文档

在对话中引用模板和指南文件：

```
@jdcloud-skill-template.md
@jdcloud-skill-generator-guide.md
```

#### 步骤 2：提供提示词

然后提供具体的生成提示：

> "请基于以上模板和指南，帮我生成一个京东云 [产品名] 的 Skill。
> - 产品名称：[产品全称]
> - Skill 名称：[jdcloud-xxx-ops]
> - 核心功能：[功能描述]
> - 目标用户：[运维工程师/SRE/开发者]"

#### 步骤 3：生成 Skill 结构

AI 将自动生成以下目录结构：

```
jdcloud-[product]-ops/
├── SKILL.md                    # 主文件（必须）
├── assets/                     # 配置文件、示例
│   └── example-config.yaml
└── references/                 # 参考文档
    ├── cli-usage.md           # CLI 详细用法
    ├── core-concepts.md       # 核心概念解释
    ├── integration.md         # SDK/MCP 集成
    ├── monitoring.md          # 监控告警配置
    └── troubleshooting.md     # 故障排查指南
```

### 3. Skill 文件规范

#### 3.1 元数据头部（YAML Frontmatter）

```yaml
---
name: jdcloud-[product]-ops
version: 1.0.0
description: >-
  管理京东云 [产品] 资源。用于部署、配置、故障排查和监控 [产品] 实例。
  包含 CLI 用法、SDK 集成和运维最佳实践。
---
```

#### 3.2 必需章节

| 章节 | 说明 |
|------|------|
| 变更历史 | 版本更新记录，放在文件开头 |
| 概述 | 产品介绍和 Skill 能力概述 |
| 前提条件 | 安装 CLI、配置凭证等 |
| 环境变量 | Skill 运行所需的环境变量说明 |
| 核心功能 | 该 Skill 支持的操作列表 |
| 常用命令 | 典型使用场景的 CLI 示例 |
| 最佳实践 | 运维建议和注意事项 |
| 相关链接 | 官方文档、API 参考 |

#### 3.3 变更历史格式

```markdown
## 变更历史

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| 1.0.0 | 2026-04-28 | 初始版本，包含核心功能和运维指南 |
| 1.1.0 | 2026-05-15 | 新增告警模板功能 |
```

### 4. 基于模板开发

#### 方式一：复制模板文件

```bash
# 1. 复制模板
cp jdcloud-skill-template.md jdcloud-[product]-ops/SKILL.md

# 2. 替换占位符
# 将 [product-name] 替换为实际产品名称
# 将 [Product Name] 替换为产品显示名称
```

#### 方式二：参考现有 Skill

参考 `jdcloud-cloudmonitor-ops/SKILL.md` 的结构和内容，根据目标产品特性进行调整。

### 5. 内容编写指南

#### 5.1 环境变量配置

每个 Skill 运行都需要配置京东云访问凭证。以下是标准的环境变量配置说明：

##### 必需的环境变量

| 变量名 | 说明 | 是否必需 | 获取方式 |
|--------|------|----------|----------|
| `JDC_ACCESS_KEY` | 京东云 Access Key | 是 | [京东云控制台 - Access Key管理](https://uc.jdcloud.com/accesskey) |
| `JDC_SECRET_KEY` | 京东云 Secret Key | 是 | 与 Access Key 同时生成 |
| `JDC_REGION` | 默认区域 ID | 否 | 默认 `cn-north-1` |

##### 配置方式

**方式一：Shell 环境变量（推荐开发使用）**

```bash
# 临时配置（当前终端会话有效）
export JDC_ACCESS_KEY="your_access_key_here"
export JDC_SECRET_KEY="your_secret_key_here"
export JDC_REGION="cn-north-1"

# 验证配置
jdc vm describe-instances --region-id cn-north-1 --page-number 1 --page-size 1
```

**方式二：Shell 配置文件（持久化）**

```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
echo 'export JDC_ACCESS_KEY="your_access_key"' >> ~/.bashrc
echo 'export JDC_SECRET_KEY="your_secret_key"' >> ~/.bashrc
echo 'export JDC_REGION="cn-north-1"' >> ~/.bashrc

# 重新加载配置
source ~/.bashrc  # 或 source ~/.zshrc
```

**方式三：CLI 配置文件**

```bash
# 交互式配置（凭证存储在 ~/.jdc/config）
jdc config init

# 根据提示输入 Access Key 和 Secret Key
# 配置文件位置：~/.jdc/config
```

**方式四：MCP Server 配置（AI Agent 使用）**

```json
{
  "mcpServers": {
    "jdcloud-vm": {
      "command": "uvx",
      "args": ["run", "--python", "3.10", "@jdcloud/vm-mcp"],
      "env": {
        "JDC_ACCESS_KEY": "${JDC_ACCESS_KEY}",
        "JDC_SECRET_KEY": "${JDC_SECRET_KEY}",
        "JDC_REGION": "${JDC_REGION:-cn-north-1}"
      }
    }
  }
}
```

> **注意**：MCP 配置中的 `${JDC_ACCESS_KEY}` 表示引用系统环境变量，需要在启动 MCP Server 前配置好对应的环境变量。

##### 安全最佳实践

- ✅ **推荐**：使用环境变量或密钥管理服务（如 AWS Secrets Manager、HashiCorp Vault）
- ✅ **推荐**：为不同环境（开发/测试/生产）创建不同的 Access Key
- ✅ **推荐**：定期轮换 Access Key（建议每 90 天）
- ❌ **禁止**：将凭证硬编码在代码中
- ❌ **禁止**：将凭证提交到 Git 仓库
- ❌ **禁止**：在日志中输出凭证信息

##### 凭证权限配置

建议为 Skill 创建专用的 IAM 用户，并授予最小必要权限：

```json
{
  "Version": "1",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "vm:Describe*",
        "vm:Start*",
        "vm:Stop*",
        "vm:Reboot*",
        "disk:Describe*",
        "vpc:Describe*"
      ],
      "Resource": "*"
    }
  ]
}
```

#### 5.2 CLI 命令示例

```markdown
### 查询资源列表
\`\`\`bash
jdc [product] describe-[resources] \
  --region-id cn-north-1 \
  --page-number 1 \
  --page-size 20
\`\`\`
```

#### 5.3 表格规范

使用 Markdown 表格展示：
- 支持的云产品列表
- 监控指标说明
- 告警阈值建议
- 错误代码对照

#### 5.4 代码块语言标记

- Bash 命令：`bash`
- JSON 数据：`json`
- YAML 配置：`yaml`
- Python 代码：`python`

### 6. 验证和测试

#### 6.1 格式检查

```bash
# 检查 Markdown 语法
markdownlint jdcloud-[product]-ops/SKILL.md

# 或手动检查 YAML 头部
head -10 jdcloud-[product]-ops/SKILL.md
```

#### 6.2 功能验证

- 复制 CLI 命令到终端执行，确保可运行
- 检查所有链接是否有效
- 验证代码示例的正确性

### 7. 发布和版本管理

#### 7.1 版本号规范

采用语义化版本（SemVer）：`主版本.次版本.修订号`

| 版本变化 | 说明 | 示例 |
|----------|------|------|
| 主版本 | 不兼容的 API 变更 | 1.0.0 → 2.0.0 |
| 次版本 | 向后兼容的功能新增 | 1.0.0 → 1.1.0 |
| 修订号 | 向后兼容的问题修复 | 1.0.0 → 1.0.1 |

#### 7.2 更新流程

1. 修改 SKILL.md 内容
2. 更新变更历史表格（在顶部添加新记录）
3. 更新 YAML 中的 version 字段
4. 提交并记录变更说明

## 示例：创建一个云主机 Skill

```bash
# 1. 创建目录结构
mkdir -p jdcloud-vm-ops/references jdcloud-vm-ops/assets

# 2. 使用 create-skill 生成基础内容
create-skill --product "云主机 VM" --name "jdcloud-vm-ops"

# 3. 完善内容
# - 添加云主机特有的 CLI 命令
# - 补充监控指标（CPU、内存、磁盘）
# - 编写故障排查指南
# - 配置环境变量说明

# 4. 验证
head -20 jdcloud-vm-ops/SKILL.md

# 5. 测试环境变量配置
export JDC_ACCESS_KEY="your_key"
export JDC_SECRET_KEY="your_secret"
export JDC_REGION="cn-north-1"
jdc vm describe-instances --region-id cn-north-1
```

## 参考资源

- [jdcloud-skill-template.md](jdcloud-skill-template.md) - Skill 模板
- [jdcloud-skill-generator-guide.md](jdcloud-skill-generator-guide.md) - 生成器详细指南
- [jdcloud-cloudmonitor-ops/SKILL.md](jdcloud-cloudmonitor-ops/SKILL.md) - 完整示例

## 常见问题

**Q: Skill 和 MCP Server 有什么关系？**

A: Skill 是指导 AI 如何使用工具的文档，MCP Server 是实际执行操作的服务。Skill 中会包含 MCP Server 的配置说明。

**Q: 一个 Skill 可以覆盖多个产品吗？**

A: 建议一个 Skill 聚焦一个产品，保持职责单一。相关产品的 Skill 可以通过 Reference 相互引用。

**Q: 如何更新已发布的 Skill？**

A: 修改内容后，更新 version 字段和变更历史，确保向后兼容或明确标注破坏性变更。

## 贡献指南

1.  Fork 本仓库
2.  创建新的 Skill 目录
3.  按照本指南编写内容
4.  提交 Pull Request

---

如有问题，请参考 [jdcloud-cloudmonitor-ops](jdcloud-cloudmonitor-ops/) 作为最佳实践示例。
