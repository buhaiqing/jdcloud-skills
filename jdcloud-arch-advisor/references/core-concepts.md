# Core Concepts — 架构评审与设计核心概念

> 本文档定义 jdcloud-arch-advisor 所依赖的核心架构理念，包括 WAF 五支柱模型、通用架构模式、以及三模式方法论。

---

## 1. 京东云 Well-Architected Framework (WAF)

京东云官方目前未发布与阿里云 WAF 完全对齐的公开框架文档。本 Skill 参考：
- **AWS Well-Architected Framework**（五支柱模型的源头）
- **阿里云 WAF**（中文语境下的成熟实践）
- **京东云产品白皮书与最佳实践**

定义了适配京东云产品的五支柱评估体系。

### 1.1 五支柱概述

| 支柱 | 关注核心 | 典型检查项 |
|:----:|---------|-----------|
| **Security** | 数据保护、访问控制、合规性 | 安全组规则是否过松、是否启用加密、IAM 策略是否符合最小权限、ActionTrail 是否启用 |
| **Reliability** | 高可用、容错、灾备 | 是否多 AZ 部署、有无自动备份、CLB 健康检查是否配置、RDS 是否主备 |
| **Performance** | 资源效率、响应速度、扩展性 | 实例规格是否匹配负载、存储 IOPS 是否达标、有无弹性伸缩 |
| **Cost** | 成本优化、资源利用率、付费模式 | 是否存在闲置资源、规格是否过度、是否购买资源包 |
| **Efficiency** | 运维效率、自动化、交付流程 | 是否使用标签、监控告警是否完善、是否有 runbook |

### 1.2 支柱间的权衡

架构设计本质上是权衡的艺术。常见冲突包括：

- **Reliability vs Cost**: 多 AZ + 多副本部署提高可靠性但增加成本
- **Performance vs Cost**: 更高规格的实例和 SSD 磁盘提升性能但增加支出
- **Security vs Efficiency**: 严格的访问控制和加密增加运维复杂度

jdcloud-arch-advisor 在报告中会标注此类权衡关系，由用户基于业务优先级做决策，而不是替用户选择。

### 1.3 与阿里云 WAF 的差异

| 维度 | 阿里云 | 京东云 |
|------|--------|--------|
| 官方框架 | 阿里云 WAF 公开 | **未公开官方 WAF** |
| 容器服务 | ACK（产品成熟） | JCS for Kubernetes（功能对齐） |
| 数据库 | PolarDB / RDS 多引擎 | JCS for MySQL/PostgreSQL/MongoDB（每个独立产品） |
| 缓存 | Redis / Tair 统一 | JCS for Redis / JCS for Memcached 独立 |
| 安全 | SAS / WAF / DDoS 多产品 | 京东云安全中心 / 高防 IP（产品组合） |
| 审计 | ActionTrail | ActionTrail（产品名一致） |
| 弹性伸缩 | ESS 成熟 | 通过控制台手动 / 模板化程度较低 |

> **重要说明**: 由于京东云官方未发布 WAF 文档，本 Skill 的 WAF 规则定义参考 AWS / 阿里云 + 京东云产品白皮书。后续如京东云发布官方 WAF 框架，需更新 `references/rules/waf-*.yaml` 规则集。

---

## 2. 通用架构模式

jdcloud-arch-advisor 识别四种主要架构模式，用于在 Mode A 中进行模式分类，在 Mode C 中作为方案模板的基础。

### 2.1 单节点架构 (Single-Node)

```
[ VM (单台) ]
      |
[ JCS for MySQL (单节点) ]
```

**特征**: 所有组件均为单实例部署，无冗余。
**适用**: 开发测试环境、小型个人站点、低流量 MVP。
**WAF 风险**: Reliability 最低，Cost 可控，Security 依赖手动配置。
**典型产品**: 1x VM + 1x JCS for MySQL 基础版 + 1x OSS Bucket（如果使用）。

### 2.2 三层架构 (3-Tier)

```
[ CLB ] → [ VM Cluster (多台) ] → [ JCS for MySQL 高可用 / JCS for Redis ]
                                          [ OSS / NAS ]
```

**特征**: 接入层、应用层、数据层分离，每层可以独立扩缩。
**适用**: 标准 Web 应用、企业管理系统、中等流量业务。
**WAF 风险**: Reliability 良好，但需要关注 CLB 健康检查、VM 伸缩策略、数据库备份。
**典型产品**: CLB + N 台 VM + JCS for MySQL 高可用版 + JCS for Redis + OSS。

### 2.3 微服务架构 (Microservice)

```
[ CLB/API Gateway ]
      |
[ Service A (JCS K8s Pod) ] ←→ [ Service B (JCS K8s Pod) ]
      |                           |
[ JCS for MySQL ]         [ JCS for Redis / MongoDB ]
      |
[ JCQ / JCS for Kafka ]   ← 异步消息解耦
```

**特征**: 业务拆分为独立服务，每个服务有自己的数据存储，通过 API 或消息队列通信。
**适用**: 复杂业务系统、大型电商、需要频繁迭代的产品。
**WAF 风险**: 架构复杂度高，需要服务治理、可观测性、CI/CD 流水线。
**典型产品**: JCS for Kubernetes + JMQ / JCQ + JCS for MySQL + JCS for Redis + SLS 对等日志服务。

### 2.4 Serverless 架构

> **注意**: 京东云的 Serverless 产品矩阵相对阿里云略弱，但仍提供函数服务等产品。

```
[ API Gateway / CLB ]
      |
[ 函数服务 (CFS) ]  →  [ Tablestore 对等 / OSS ]
      |
[ 日志服务 (SLS) / 消息服务 (JCQ) ]
```

**特征**: 无服务器管理，按用量付费，自动弹性伸缩。
**适用**: 事件驱动型业务、不定时突发流量、低频 API、批处理任务。
**WAF 风险**: 冷启动延时、长任务不适用、厂商锁定风险。
**典型产品**: CFS + 对象存储 + API Gateway + 日志服务 + JCQ。

---

## 3. 三模式方法论

jdcloud-arch-advisor 采用三模式设计，确保对用户意图的精确覆盖。

### 3.1 Mode A — 架构逆向与分析

**输入**: 用户描述的现有系统
**输出**: 架构拓扑 + 组件清单 + 依赖关系 + 风险标识

核心能力：
1. 从用户自然语言描述中提取架构信息
2. 通过委托多个产品 ops Skill 验证实际资源状态
3. 自动识别架构模式（单节点/三层/微服务/Serverless）
4. 标注每个组件的健康状态和潜在风险

适用场景：新接手系统需要了解架构、系统文档缺失需要重建、并购后的技术尽调。

**京东云数据采集模式**：

| 组件类型 | 委托 Skill | 关键命令 |
|---------|-----------|---------|
| 计算 | `jdcloud-vm-ops` | `jdc vm describe-instances` |
| 数据库 | `jdcloud-mysql-ops` / `jdcloud-postgresql-ops` / `jdcloud-mongodb-ops` | `jdc ... describe-instances` |
| 缓存 | `jdcloud-redis-ops` | `jdc redis describe-cache-instances` |
| 搜索 | `jdcloud-elasticsearch-ops` | `jdc es describe-instances` |
| 接入 | `jdcloud-clb-ops` | `jdc clb describe-load-balancers` |
| 身份 | `jdcloud-iam-ops` | `jdc iam list-sub-users` |
| 密钥 | `jdcloud-kms-ops` | `jdc kms list-keys` |
| 公网 | `jdcloud-eip-ops` | `jdc eip describe-eips` |
| 标签 | `jdcloud-tag-audit-ops` | `jdc tag describe-resources` |

### 3.2 Mode B — WAF 成熟度评估

**输入**: 评估范围（全量或指定支柱）
**输出**: 五支柱评分 + 风险发现清单 + 改进建议

核心能力：
1. 基于实际资源状态和监控数据进行客观评估
2. 每个支柱分解为多个检查维度（见 `references/rules/waf-*.yaml`）
3. 每个发现项标注严重级别 P0-P3
4. 提供可操作的改进建议，包括预估工作量和影响

评估流程示例（Security 支柱）：

```
1. 安全检查项：
   - VM 安全组是否过度开放（0.0.0.0/0 端口映射）？
   - 是否有未关联安全组的 VM 实例？
   - JCS for MySQL 是否开启 TLS/SSL？
   - OSS Bucket 是否公开可读？
   - IAM 用户是否启用了 MFA？
   - AccessKey 是否定期轮换？
   - ActionTrail 是否已启用？

2. 数据来源：jdcloud-iam-ops + jdcloud-kms-ops + jdcloud-vm-ops + jdcloud-audit-ops
3. 评分逻辑：每个检查项通过得 1 分，按通过比例计算支柱得分
```

### 3.3 Mode C — 架构方案推荐

**输入**: 业务需求描述 + 非功能性要求 + 约束
**输出**: 推荐架构方案 + 多方案对比 + 实施路线

核心能力：
1. 根据业务特征匹配合适的架构模式
2. 参考京东云最佳实践场景模板
3. 对比至少 2 个可行方案（成本、复杂度、WAF 覆盖度）
4. 推荐分阶段实施路线

方案对比示例：

| 维度 | 方案 A: 传统三层 (CLB+VM+JCS for MySQL) | 方案 B: 容器化 (JCS K8s + JCS for MySQL) |
|------|:---:|:---:|
| WAF Security | ★★★☆☆ | ★★★★☆ |
| WAF Reliability | ★★★★☆ | ★★★★★ |
| WAF Performance | ★★★☆☆ | ★★★★★ |
| WAF Cost | ★★★★☆ | ★★★☆☆ |
| WAF Efficiency | ★★★☆☆ | ★★★★★ |
| 运维复杂度 | 低 | 中高 |
| 月度成本预估 | ¥3,000 | ¥4,500 |
| 推荐场景 | 快速上线、团队经验有限 | 长期运行、团队有容器经验 |

---

## 4. 数据采集策略

### 4.1 主动采集（通过委托下游 Skill）

| 数据源 Skill | 采集内容 | 模式依赖 |
|-------------|---------|:--------:|
| `jdcloud-vm-ops` | VM 实例列表、规格、状态、安全组、磁盘 | A, B |
| `jdcloud-mysql-ops` | JCS for MySQL 实例、规格、备份、副本 | A, B |
| `jdcloud-postgresql-ops` | JCS for PostgreSQL 实例、规格、备份 | A, B |
| `jdcloud-mongodb-ops` | JCS for MongoDB 集群、节点、分片 | A, B |
| `jdcloud-redis-ops` | JCS for Redis 实例、规格、持久化 | A, B |
| `jdcloud-elasticsearch-ops` | ES 集群、节点、索引 | A, B |
| `jdcloud-clb-ops` | CLB 实例、监听器、后端服务器 | A, B |
| `jdcloud-iam-ops` | IAM 子用户、策略、AccessKey | B (Security) |
| `jdcloud-kms-ops` | KMS 密钥、轮转状态 | B (Security) |
| `jdcloud-eip-ops` | EIP、绑定状态、带宽 | A, B |
| `jdcloud-cloudmonitor-ops` | 资源利用率指标（CPU/内存/IOPS） | B (Performance) |
| `jdcloud-audit-ops` | ActionTrail 配置、审计事件 | B (Security) |
| `jdcloud-tag-audit-ops` | 资源标签覆盖率、命名规范 | B (Efficiency) |
| `jdcloud-alert-intelligence` | 告警事件聚合、噪音过滤 | B (Reliability) |

### 4.2 被动采集（用户直接提供）

当 Agent 无法访问实际云环境（无凭证或 Skill 不可用时），采用降级策略：

- **用户描述**: 要求用户提供架构图、配置清单等
- **Confidence 标注**: 报告中标注依赖实际数据源的结论为 `low confidence`
- **局限性说明**: 明确告知用户哪些评估因数据源不可用而无法完成

### 4.3 与 alicloud-arch-advisor 数据采集的差异

| 维度 | alicloud-arch-advisor | jdcloud-arch-advisor |
|------|----------------------|----------------------|
| 拓扑发现 | 单一 `topo-discovery` Skill | 多 Skill 并行调用 |
| Advisor 巡检 | `advisor-ops` 一站式获取 | 需通过 `cloudmonitor-ops` + 各产品 ops 自行检查 |
| 成本数据 | `billing-ops` | （无对应 skill，仅基于资源规格估算） |
| 容器检查 | `ack-ops` | JCS for Kubernetes（**当前无对应 skill**） |
| CDN 检查 | `cdn-ops` | CDN（**当前无对应 skill**） |

---

## 5. 参考链接

- [京东云产品文档](https://docs.jdcloud.com/)
- [京东云 API Explorer](https://docs.jdcloud.com/cn/api)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [阿里云 WAF](https://help.aliyun.com/zh/product/2362200.html)（参考模型来源）
