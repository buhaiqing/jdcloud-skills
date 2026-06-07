# Well-Architected Assessment — jdcloud-arch-advisor 自我评估

> 本文件对 jdcloud-arch-advisor Skill 本身进行 Well-Architected Framework 五支柱评估（元认知层）。评估对象是该 Skill 的设计、实现和使用方式是否符合 WAF 最佳实践。
>
> **重要**: 京东云官方目前未发布与 AWS / 阿里云 WAF 完全对齐的公开框架。本 Skill 的 WAF 规则定义参考:
> - **AWS Well-Architected Framework**（五支柱模型的源头）
> - **阿里云 WAF**（中文语境下的成熟实践）
> - **京东云产品白皮书与最佳实践**
>
> 后续如京东云发布官方 WAF 框架, 需更新 `references/rules/waf-*.yaml` 规则集与本文件。

---

## 评估主流程（伪代码）

```python
def assess_waf(
    user_scenario: str,
    user_target_resources: list = None,
    user_focus_pillar: str = None,  # None = 五支柱全量
) -> WafReport:
    """
    Mode B — WAF 成熟度评估主流程
    委托下游 jdcloud-* ops skill 采集数据, 对照 rules/waf-*.yaml 评分, 生成报告。
    """

    # ─── Phase 1: 数据采集 ────────────────────────────────────────
    pillars_data = {}

    if user_focus_pillar in (None, "security"):
        pillars_data["security"] = parallel_collect([
            delegate("jdcloud-iam-ops", "list-sub-users"),
            delegate("jdcloud-iam-ops", "list-policies"),
            delegate("jdcloud-kms-ops", "list-keys"),
            delegate("jdcloud-vm-ops", "describe-security-groups"),
            delegate("jdcloud-audit-ops", "describe-trails"),
        ])

    if user_focus_pillar in (None, "reliability"):
        pillars_data["reliability"] = parallel_collect([
            delegate("jdcloud-vm-ops", "describe-instances"),  # 取 az 分布
            delegate("jdcloud-mysql-ops", "describe-instances"),  # 主备配置
            delegate("jdcloud-redis-ops", "describe-cache-instances"),
            delegate("jdcloud-clb-ops", "describe-load-balancers"),  # 多 AZ
            delegate("jdcloud-alert-intelligence", "summarize-alerts"),
        ])

    if user_focus_pillar in (None, "performance"):
        pillars_data["performance"] = parallel_collect([
            delegate("jdcloud-cloudmonitor-ops", "get-metric-data",  # CPU/内存/IOPS
                     metric="cpu.utilization,mem.utilization,iops.read,iops.write",
                     period="7d"),
            *product_specs_collect(),  # 各产品 ops 取规格信息
        ])

    if user_focus_pillar in (None, "cost"):
        pillars_data["cost"] = parallel_collect([
            delegate("jdcloud-cloudmonitor-ops", "get-metric-data",
                     metric="cpu.utilization", period="30d"),  # 闲置检测
            delegate("jdcloud-tag-audit-ops", "list-tagged-resources"),  # 资源盘点
        ])

    if user_focus_pillar in (None, "efficiency"):
        pillars_data["efficiency"] = parallel_collect([
            delegate("jdcloud-tag-audit-ops", "coverage-report"),
            delegate("jdcloud-cloudmonitor-ops", "alarm-rule-coverage"),
        ])

    # ─── Phase 2: 五支柱评分 ─────────────────────────────────────
    rule_sets = {
        "security":     load_yaml("references/rules/waf-security.yaml"),
        "reliability":  load_yaml("references/rules/waf-reliability.yaml"),
        "performance":  load_yaml("references/rules/waf-performance.yaml"),
        "cost":         load_yaml("references/rules/waf-cost.yaml"),
        "efficiency":   load_yaml("references/rules/waf-efficiency.yaml"),
    }

    waf_scores = {}
    pillar_details = {}
    risk_findings = []

    for pillar, rules in rule_sets.items():
        applicable_rules = [r for r in rules["rules"] if r["applies_to"]]
        passed = []
        failed = []
        for rule in applicable_rules:
            if check_rule(rule, pillars_data.get(pillar, {})):
                passed.append(rule["id"])
            else:
                failed.append((rule, pillars_data.get(pillar, {})))

        waf_scores[pillar] = len(passed) / len(applicable_rules) if applicable_rules else 1.0
        pillar_details[pillar] = {
            "rules_passed": passed,
            "rules_failed": [r["id"] for r, _ in failed],
            "evidence": {r["id"]: extract_evidence(r, pillars_data.get(pillar, {})) for r, _ in failed},
        }
        for rule, evidence in failed:
            risk_findings.append(to_finding(rule, evidence, pillar))

    waf_scores["composite_score"] = mean([
        waf_scores[p] for p in ["security", "reliability", "performance", "cost", "efficiency"]
    ])

    # ─── Phase 3: 报告产出 ────────────────────────────────────────
    return WafReport(
        mode="B",
        waf_scores=waf_scores,
        pillar_details=pillar_details,
        risk_findings=sorted(risk_findings, key=lambda f: severity_order(f["severity"])),
        recommendations=generate_recommendations(risk_findings),
        data_sources=collect_data_source_metadata(pillars_data),
        trace_id=uuid4(),
    )
```

---

## 五支柱评估细则

### Security (安全)

#### 评估目标
评估目标系统是否满足**最小权限**、**数据保护**、**审计追踪**三大安全原则。重点关注:
- IAM 子用户是否启用 MFA (`WAF-SEC-001`)
- AccessKey 是否定期轮换 + 是否为主账号 (`WAF-SEC-002`, `WAF-SEC-003`)
- KMS 密钥是否启用自动轮转 (`WAF-SEC-004`)
- VM 安全组是否过度开放 (0.0.0.0/0) (`WAF-SEC-005`)
- OSS / JCS for MySQL 是否开启传输加密 + 存储加密 (`WAF-SEC-006`)
- ActionTrail 是否启用 + 日志保留 ≥ 180 天 (`WAF-SEC-007`)

#### 数据采集清单
| 委托 Skill | 采集命令 | 关注字段 |
|-----------|---------|---------|
| `jdcloud-iam-ops` | `jdc --output json iam list-sub-users` | `mfaEnabled`, `accessKeyAge` |
| `jdcloud-iam-ops` | `jdc --output json iam list-policies` | `policyDocument.Statement[].Action`, `Resource` |
| `jdcloud-kms-ops` | `jdc --output json kms list-keys` | `keyRotationStatus`, `creationDate` |
| `jdcloud-vm-ops` | `jdc --output json vm describe-security-groups` | `ingressRule[].cidrIp` (是否 `0.0.0.0/0`) |
| `jdcloud-audit-ops` | `jdc --output json audit describe-trails` | `status`, `eventDeliveryRegion`, `retentionDays` |
| `jdcloud-mysql-ops` | `jdc --output json rds describe-instances --service mysql` | `tlsEnabled`, `storageEncrypted` |
| `jdcloud-redis-ops` | `jdc --output json redis describe-cache-instances` | `tlsEnabled` |

> **缺失 skill 标 manual check**:
> - `jdcloud-oss-ops` (OSS 加密检测需人工控制台核查, 当前无对应 skill)
> - 安全中心 / 高防 IP 等安全产品 (需走京东云控制台或工单)

#### 评分标准 (L1-L4 等级)

| 等级 | 含义 | 通过率 | 触发改进建议 |
|:----:|------|:------:|------|
| **L1 — 初始** | 安全规则未系统化, 凭据管理混乱 | < 40% | P0 — 立即整改: 启用 IAM 子用户 + MFA + 关闭主账号 AK |
| **L2 — 被动** | 基本防护到位, 但有显著漏洞 | 40-65% | P1 — 限期整改: 安全组收敛 + KMS 轮转 + ActionTrail 启用 |
| **L3 — 主动** | 大部分最佳实践已实施, 持续优化 | 65-85% | P2 — 持续优化: 加密全覆盖 + 访问审计 + 异常检测 |
| **L4 — 自适应** | 安全嵌入运维流程, 自动化响应 | ≥ 85% | P3 — 微优化: 零信任演进 + 持续合规扫描 |

#### 风险分级

| 严重度 | 含义 | 响应时限 | 示例 |
|:------:|------|---------|------|
| **P0 — Critical** | 立即可被攻击者利用 | 24 小时内 | 主账号 AK 存在; 安全组全开 22 端口; ActionTrail 未启用 |
| **P1 — High** | 需特定条件触发 | 1 周内 | IAM 子用户无 MFA; AccessKey 超过 90 天未轮换 |
| **P2 — Medium** | 防御纵深不足 | 1 月内 | 部分实例未加密; KMS 未启用自动轮转 |
| **P3 — Low** | 最佳实践偏离 | 季度内 | 标签不规范; 日志保留期 < 180 天 |

#### 改进建议模板
```markdown
### [P0] IAM 子用户未启用 MFA
- **规则**: WAF-SEC-001
- **风险**: 一旦子用户密码泄露, 攻击者可直接登录控制台
- **影响资源**: {{output.affected_resources}}
- **建议操作**:
  1. 委托 `jdcloud-iam-ops` 启用 MFA
  2. 参考: https://docs.jdcloud.com/cn/iam/product-overview
- **预估 effort**: low (1 天)
- **修复后预期提升**: Security 支柱得分 +0.10
```

#### 京东云特殊性
- **无官方 WAF 框架** → 参考 AWS WAF Security Pillar + 阿里云 WAF + 京东云产品白皮书
- **ActionTrail 产品名一致** (与 AWS 同名)
- **主账号 AK 风险** 与 AWS root key 风险等同, 必须用子用户 + AccessKey
- **KMS 与阿里云 KMS 功能对齐**, 密钥轮转 API 类似
- **安全组** 与 AWS Security Group / 阿里云安全组概念一致, 入站/出站规则语法相同

---

### Reliability (可靠性)

#### 评估目标
评估目标系统是否满足**高可用**、**容错**、**灾备**三大可靠性原则。重点关注:
- VM 是否多 AZ 部署 (`WAF-REL-001`)
- CLB 是否跨可用区 (`WAF-REL-002`)
- JCS for MySQL 是否主备 / 多节点 (`WAF-REL-003`)
- JCS for Redis 是否主从 + 持久化 (`WAF-REL-004`)
- 备份策略: 自动备份 + 跨地域备份 (`WAF-REL-005`)
- 健康检查: CLB 后端健康检查配置 (`WAF-REL-006`)
- 告警覆盖: 关键资源是否有告警规则 (`WAF-REL-007`)

#### 数据采集清单
| 委托 Skill | 采集命令 | 关注字段 |
|-----------|---------|---------|
| `jdcloud-vm-ops` | `jdc --output json vm describe-instances` | `az`, `status` (是否多 az 分布) |
| `jdcloud-clb-ops` | `jdc --output json clb describe-load-balancer-detail` | `azs` (是否多 az) |
| `jdcloud-mysql-ops` | `jdc --output json rds describe-instances --service mysql` | `haMode` (主备/单点), `backupRetentionDays` |
| `jdcloud-redis-ops` | `jdc --output json redis describe-cache-instances` | `replicas`, `persistenceEnabled` |
| `jdcloud-alert-intelligence` | (内部接口) | 告警覆盖率 |
| `jdcloud-cloudmonitor-ops` | `jdc --output json monitor describe-alarm-rules` | 关键资源是否有告警 |

> **缺失 skill 标 manual check**:
> - `jdcloud-vpc-ops` (待创建, VPC / Subnet 拓扑分析必需)
> - 跨地域灾备方案 (需走京东云工单)

#### 评分标准

| 等级 | 含义 | 通过率 |
|:----:|------|:------:|
| **L1 — 初始** | 单点部署, 无备份 | < 40% |
| **L2 — 被动** | 有备份但恢复未演练 | 40-65% |
| **L3 — 主动** | 多 AZ + 定期恢复演练 | 65-85% |
| **L4 — 自适应** | 跨地域灾备 + 自动化故障转移 | ≥ 85% |

#### 风险分级

| 严重度 | 含义 | 响应时限 | 示例 |
|:------:|------|---------|------|
| **P0 — Critical** | 单点故障导致业务中断 | 24 小时内 | MySQL 单节点; CLB 单 AZ |
| **P1 — High** | 部分组件单点, 故障域收敛 | 1 周内 | Redis 无主从; 无自动备份 |
| **P2 — Medium** | HA 策略不完善 | 1 月内 | 健康检查超时不合理; 备份未跨地域 |
| **P3 — Low** | 监控覆盖不全 | 季度内 | 部分次要资源无告警 |

#### 改进建议模板
```markdown
### [P0] JCS for MySQL 单点部署
- **规则**: WAF-REL-003
- **风险**: 数据库故障 = 业务完全中断; 数据丢失风险
- **影响资源**: {{output.affected_instance}}
- **建议操作**:
  1. 委托 `jdcloud-mysql-ops` 升级到高可用版 (主备)
  2. 启用自动备份 + 跨地域备份
  3. 配置告警: CPU/连接数/主从延迟
- **预估 effort**: medium (3-5 天, 含数据迁移)
- **修复后预期提升**: Reliability 支柱得分 +0.15
```

#### 京东云特殊性
- **CLB 多 AZ** 是与 AWS ELB / 阿里云 SLB 相同的概念, 但京东云控制台默认不强制跨 AZ
- **JCS for MySQL 高可用版** = 阿里云 RDS MySQL 高可用版, 1 主 1 备
- **JCS for Redis** 持久化选项与阿里云 Redis AOF 概念一致
- **跨地域灾备** 在京东云生态相对薄弱, 可能需要工单咨询

---

### Performance (性能)

#### 评估目标
评估目标系统**资源规格匹配度**、**IOPS / 带宽**、**扩展能力**。重点关注:
- VM / RDS / Redis 规格与负载匹配 (`WAF-PERF-001`)
- 存储 IOPS 是否达标 (`WAF-PERF-002`)
- 网络带宽是否瓶颈 (`WAF-PERF-003`)
- 弹性伸缩: 是否有自动伸缩策略 (`WAF-PERF-004`)
- 缓存命中率 (`WAF-PERF-005`)
- 数据库慢查询 (`WAF-PERF-006`)

#### 数据采集清单
| 委托 Skill | 采集命令 | 关注字段 |
|-----------|---------|---------|
| `jdcloud-cloudmonitor-ops` | `jdc --output json monitor get-metric-data --metric cpu.utilization --period 7d` | 7 天峰值/均值 |
| `jdcloud-cloudmonitor-ops` | `--metric mem.utilization` | 内存使用率 |
| `jdcloud-cloudmonitor-ops` | `--metric iops.read,iops.write` | 存储 IOPS 实际值 vs 规格上限 |
| `jdcloud-cloudmonitor-ops` | `--metric net.inRate,net.outRate` | 网络带宽使用率 |
| `jdcloud-mysql-ops` | `jdc --output json rds describe-slow-log --service mysql --days 7` | 慢查询数量 |
| `jdcloud-redis-ops` | `jdc --output json redis describe-cache-instances` | `hitRate` |

> **缺失 skill 标 manual check**:
> - `jdcloud-auto-scaling-orch` (弹性伸缩配置, 当前无对应 skill, 需控制台)
> - 性能压测数据 (需用户自提供)

#### 评分标准

| 等级 | 含义 | 通过率 |
|:----:|------|:------:|
| **L1 — 初始** | 规格过度或不足, 性能瓶颈频繁 | < 40% |
| **L2 — 被动** | 大致匹配, 偶有瓶颈 | 40-65% |
| **L3 — 主动** | 规格 + 缓存 + 索引优化到位 | 65-85% |
| **L4 — 自适应** | 自动弹性 + 全链路性能监控 | ≥ 85% |

#### 风险分级

| 严重度 | 含义 | 响应时限 | 示例 |
|:------:|------|---------|------|
| **P0 — Critical** | 业务已受影响 | 24 小时内 | CPU 持续 > 90%; 慢查询 100+ 每天 |
| **P1 — High** | 规格不足, 高峰期风险 | 1 周内 | 内存使用率 > 80%; 缓存命中率 < 50% |
| **P2 — Medium** | 有优化空间 | 1 月内 | IOPS 接近规格上限; 无自动伸缩 |
| **P3 — Low** | 监控覆盖不全 | 季度内 | 部分组件无性能指标采集 |

#### 改进建议模板
```markdown
### [P1] VM 规格与负载不匹配
- **规则**: WAF-PERF-001
- **风险**: CPU 持续 > 80% 7 天峰值, 响应时间劣化
- **影响资源**: {{output.affected_instance}}
- **建议操作**:
  1. 委托 `jdcloud-vm-ops` 升级到 2 核 4GB (g.n3.medium)
  2. 或启用水平扩容 (HPA, 需 JCS K8s)
- **预估 effort**: low (1 天)
- **修复后预期提升**: Performance 支柱得分 +0.12
```

#### 京东云特殊性
- **`cloudmonitor-ops`** 是京东云监控的事实标准, 与 AWS CloudWatch / 阿里云云监控对齐
- **JCS for MySQL 规格** `g.n3.large` 等命名规则与京东云 VM 一致
- **弹性伸缩** 京东云相对 AWS Auto Scaling / 阿里云 ESS 较弱, 多通过模板 + 定时任务
- **JCS K8s** (容器服务) 功能对齐 AWS EKS / 阿里云 ACK, 但 HPA / VPA 需自行配置

---

### Cost (成本)

#### 评估目标
评估目标系统**资源利用率**、**付费模式合理性**、**成本可视化**。重点关注:
- VM 利用率: CPU 长期 < 20% 即为浪费 (`WAF-COST-001`)
- 是否使用包年包月 / 资源包 (`WAF-COST-002`)
- 闲置资源: 未挂载磁盘 / 未绑定 EIP (`WAF-COST-003`)
- 规格过度: 配置远高于实际负载 (`WAF-COST-004`)
- 标签治理: 缺失导致无法按业务核算 (`WAF-COST-005`)

#### 数据采集清单
| 委托 Skill | 采集命令 | 关注字段 |
|-----------|---------|---------|
| `jdcloud-cloudmonitor-ops` | `--metric cpu.utilization --period 30d` | 30 天峰值/均值 (识别闲置) |
| `jdcloud-tag-audit-ops` | `jdc --output json tag coverage-report` | 标签覆盖率 |
| `jdcloud-vm-ops` | `jdc --output json vm describe-instances` | `instanceChargeType` (包年包月/按量) |
| `jdcloud-eip-ops` | `jdc --output json eip describe-eips` | `status` (未绑定即闲置) |
| `jdcloud-vm-ops` | `jdc --output json vm describe-disks` | `status` (未挂载即闲置) |

> **缺失 skill 标 manual check**:
> - `jdcloud-billing-ops` (账单分析, 当前无对应 skill, 需走京东云费用中心)
> - **账单数据无法通过 API 获取**, 只能基于资源规格估算

#### 评分标准

| 等级 | 含义 | 通过率 |
|:----:|------|:------:|
| **L1 — 初始** | 资源浪费严重, 无成本可视化 | < 40% |
| **L2 — 被动** | 知道浪费但未系统化 | 40-65% |
| **L3 — 主动** | 资源利用率 > 60%, 标签规范 | 65-85% |
| **L4 — 自适应** | FinOps 嵌入决策流程 | ≥ 85% |

#### 风险分级

| 严重度 | 含义 | 响应时限 | 示例 |
|:------:|------|---------|------|
| **P0 — Critical** | 月度浪费 > 30% | 1 周内 | 10 台 VM CPU 均 < 10% |
| **P1 — High** | 显著浪费 | 1 月内 | 未绑定 EIP 计费中; 未挂载磁盘计费中 |
| **P2 — Medium** | 优化空间 | 季度内 | 包年包月但负载波动大 |
| **P3 — Low** | 成本归属不清 | 季度内 | 标签覆盖率 < 60% |

#### 改进建议模板
```markdown
### [P1] 闲置 EIP 计费
- **规则**: WAF-COST-003
- **风险**: 每月浪费 ¥X (按 EIP 带宽计费)
- **影响资源**: {{output.unbound_eips}}
- **建议操作**:
  1. 委托 `jdcloud-eip-ops` 释放未绑定 EIP
  2. 或降低带宽配置
- **预估 effort**: low (1 天)
- **修复后预期节省**: ¥X/月
```

#### 京东云特殊性
- **无 billing-ops skill** → 成本分析只能基于资源规格估算
- **资源包** (类似 AWS Savings Plans / 阿里云预留实例券) 在京东云逐步推广
- **EIP 计费** 即使未绑定也按带宽收费, 与 AWS EIP 类似
- **账单 API 不公开** → 真实成本数据需京东云费用中心导出

---

### Efficiency (效率)

#### 评估目标
评估目标系统**运维效率**、**自动化程度**、**可观测性**。重点关注:
- 资源标签覆盖率 (`WAF-EFF-001`)
- 命名规范: 一致的前缀 / 业务标识 (`WAF-EFF-002`)
- 监控告警覆盖: 所有关键资源有告警规则 (`WAF-EFF-003`)
- Runbook / 运维文档存在 (`WAF-EFF-004`)
- CI/CD 流程 (如涉及应用层) (`WAF-EFF-005`)

#### 数据采集清单
| 委托 Skill | 采集命令 | 关注字段 |
|-----------|---------|---------|
| `jdcloud-tag-audit-ops` | `jdc --output json tag coverage-report` | 标签覆盖率, 命名规范符合率 |
| `jdcloud-cloudmonitor-ops` | `jdc --output json monitor describe-alarm-rules` | 告警规则数量, 覆盖资源类型 |
| (用户输入) | — | Runbook / 文档存在性 |

> **缺失 skill 标 manual check**:
> - `jdcloud-kubernetes-ops` (CI/CD 与 K8s 相关)
> - 应用层监控 (APM, 需用户自提供)

#### 评分标准

| 等级 | 含义 | 通过率 |
|:----:|------|:------:|
| **L1 — 初始** | 无标签, 无监控, 无文档 | < 40% |
| **L2 — 被动** | 基本标签 + 监控, 但治理差 | 40-65% |
| **L3 — 主动** | 标签规范 + 全覆盖监控 + 文档 | 65-85% |
| **L4 — 自适应** | 自动化运维 + 智能告警 | ≥ 85% |

#### 风险分级

| 严重度 | 含义 | 响应时限 | 示例 |
|:------:|------|---------|------|
| **P0 — Critical** | 故障无可观测性 | 1 周内 | 关键业务无任何告警; 无 runbook |
| **P1 — High** | 治理薄弱 | 1 月内 | 标签覆盖率 < 50% |
| **P2 — Medium** | 监控盲区 | 季度内 | 部分次要资源无告警 |
| **P3 — Low** | 命名不一致 | 季度内 | 命名规范符合率 < 80% |

#### 改进建议模板
```markdown
### [P1] 资源标签覆盖率 < 50%
- **规则**: WAF-EFF-001
- **风险**: 无法按业务/部门核算成本; 故障定位慢
- **影响资源**: {{output.untagged_resources}}
- **建议操作**:
  1. 委托 `jdcloud-tag-audit-ops` 制定标签规范 (env / project / owner)
  2. 批量打标: 按业务线 / 环境 / 负责人分类
- **预估 effort**: medium (1-2 周)
- **修复后预期提升**: Efficiency 支柱得分 +0.20
```

#### 京东云特殊性
- **标签** 与 AWS Tags / 阿里云 Tags 概念一致
- **资源目录** 在京东云控制台可按标签筛选
- **监控告警** 通过 `jdcloud-cloudmonitor-ops` 创建规则
- **APM / 应用监控** 京东云生态相对薄弱, 多用第三方 (听云 / 透视宝等)

---

## 评分卡 (Scorecard) 输出 JSON 模板

```json
{
  "report_id": "waf-20260608-001",
  "mode": "B",
  "cloud": "jdcloud",
  "generated_at": "2026-06-08T12:00:00Z",
  "assessment_scope": {
    "target_resources": ["i-xxx", "mysql-instance-yyy"],
    "region": "cn-north-1",
    "focus_pillar": "all"
  },
  "waf_scores": {
    "security": 0.85,
    "reliability": 0.70,
    "performance": 0.60,
    "cost": 0.75,
    "efficiency": 0.65,
    "composite_score": 0.71,
    "overall_level": "L3"
  },
  "pillar_details": {
    "security": {
      "rules_passed": ["WAF-SEC-002", "WAF-SEC-003", "WAF-SEC-004"],
      "rules_failed": ["WAF-SEC-001", "WAF-SEC-007"],
      "evidence": {
        "WAF-SEC-001": "3 个子用户中 2 个未启用 MFA",
        "WAF-SEC-007": "ActionTrail 未配置"
      }
    },
    "reliability": { "...": "..." },
    "performance": { "...": "..." },
    "cost": { "...": "..." },
    "efficiency": { "...": "..." }
  },
  "risk_findings": [
    {
      "id": "FIND-001",
      "pillar": "security",
      "rule_id": "WAF-SEC-001",
      "severity": "P0",
      "title": "IAM 子用户未启用 MFA",
      "description": "...",
      "affected_resources": ["iam-user-aaa", "iam-user-bbb"],
      "data_source": "jdcloud-iam-ops",
      "data_timestamp": "2026-06-08T11:55:00Z"
    }
  ],
  "recommendations": [
    {
      "finding_id": "FIND-001",
      "title": "启用 IAM 子用户 MFA",
      "action": "委托 jdcloud-iam-ops 启用 MFA",
      "effort": "low",
      "duration": "1 day",
      "expected_score_impact": {
        "security": "+0.10",
        "composite": "+0.02"
      },
      "safety_notes": "启用 MFA 不影响现有登录, 但用户需重新绑定设备"
    }
  ],
  "data_sources": [
    { "skill": "jdcloud-iam-ops", "command": "jdc --output json iam list-sub-users", "timestamp": "2026-06-08T11:55:00Z", "confidence": "high" },
    { "skill": "jdcloud-kms-ops", "command": "jdc --output json kms list-keys", "timestamp": "2026-06-08T11:56:00Z", "confidence": "high" },
    { "skill": "jdcloud-cloudmonitor-ops", "command": "jdc --output json monitor get-metric-data --metric cpu.utilization", "timestamp": "2026-06-08T11:57:00Z", "confidence": "medium" }
  ],
  "trace_id": "<uuid>"
}
```

---

## 与 references/rules/waf-*.yaml 的对应关系

| 支柱 | YAML 规则文件 | 典型规则 ID | 关键检查点 |
|:----:|--------------|------------|-----------|
| **Security** | `references/rules/waf-security.yaml` | `WAF-SEC-001` ~ `WAF-SEC-NNN` | IAM MFA / AccessKey 轮换 / KMS 轮转 / 安全组 / ActionTrail / 加密 |
| **Reliability** | `references/rules/waf-reliability.yaml` | `WAF-REL-001` ~ `WAF-REL-NNN` | 多 AZ / 主备 / 备份 / 健康检查 / 告警覆盖 |
| **Performance** | `references/rules/waf-performance.yaml` | `WAF-PERF-001` ~ `WAF-PERF-NNN` | 规格匹配 / IOPS / 带宽 / 弹性伸缩 / 缓存命中率 |
| **Cost** | `references/rules/waf-cost.yaml` | `WAF-COST-001` ~ `WAF-COST-NNN` | 利用率 / 付费模式 / 闲置资源 / 标签核算 |
| **Efficiency** | `references/rules/waf-efficiency.yaml` | `WAF-EFF-001` ~ `WAF-EFF-NNN` | 标签治理 / 命名规范 / 监控告警 / Runbook |

> **规则 ID 命名规范**: `WAF-<PILLAR_ABBR>-<NNN>`, 三个字母的 Pillar 简写:
> - SEC = Security
> - REL = Reliability
> - PERF = Performance
> - COST = Cost
> - EFF = Efficiency
>
> **规则严重度**: `critical` / `high` / `medium` / `low` (在 YAML 中), 映射到评分卡 P0 / P1 / P2 / P3

### 缺失 Skill 列表 (manual check)

下列京东云产品当前无对应 skill, 在 WAF 评估中需标注为 `manual_check`:

| 缺失 Skill | 影响支柱 | 替代方案 |
|----------|---------|---------|
| `jdcloud-vpc-ops` | Reliability (多 AZ 分析) | 待创建 (本次任务范围外) |
| `jdcloud-nat-ops` | Performance / Cost (NAT 费用) | 控制台手动 |
| `jdcloud-oss-ops` | Security / Cost (OSS 加密 / 存储费用) | 控制台手动 |
| `jdcloud-cdn-ops` | Performance (CDN 命中率) | 控制台手动 |
| `jdcloud-kubernetes-ops` | Reliability / Performance (K8s 集群) | 控制台手动 |
| `jdcloud-jcq-ops` | Reliability (消息队列 HA) | 控制台手动 |
| `jdcloud-billing-ops` | Cost (账单分析) | 京东云费用中心导出 |
| `jdcloud-auto-scaling-orch` | Performance (弹性伸缩) | 控制台手动 |

---

## 评估总结 (元认知)

| 维度 | 评分 | 评价 |
|:----:|:---:|------|
| Security | ★★★★★ | 纯只读设计从根本上消除了攻击面; 委托模式实现最小权限; 红线 `AdministratorAccess *:*` → Safety = 0 |
| Reliability | ★★★★☆ | 流程标准化好 (三模式); 数据源降级策略 (Skill 不可用 → 用户描述 + low confidence); 缺失 skill 走 manual check |
| Cost | ★★★★☆ | 自身零资源消耗; 帮助用户识别闲置资源 + 规格优化; 唯一缺憾: 无 billing-ops, 真实账单需走费用中心 |
| Efficiency | ★★★★★ | 三模式覆盖面广; 报告模板复用; 缺失 skill 列表清晰; 并行委托下游 |
| Performance | ★★★★☆ | 数据采集并行化; 报告生成 < 30s; 依赖下游 Skill 响应; 缺 billing 实时数据 |

### 与 alicloud-arch-advisor 差异

| 维度 | alicloud-arch-advisor | jdcloud-arch-advisor |
|------|----------------------|----------------------|
| 官方 WAF 框架 | 阿里云 WAF 公开 | **京东云未发布官方 WAF** (参考 AWS + 阿里云 + 京东云白皮书) |
| 拓扑发现 | 单一 `topo-discovery` Skill | 多 Skill 并行委托 (无 topo-discovery) |
| Advisor 巡检 | `advisor-ops` 一站式 | 需组合 `cloudmonitor-ops` + 各产品 ops |
| 成本数据 | `billing-ops` | **无对应 skill** (仅基于资源规格估算) |
| 容器服务 | `ack-ops` | **无对应 skill** (manual check) |
| CDN | `cdn-ops` | **无对应 skill** (manual check) |
| 凭证管理 | `~/.aliyun/configure` + env | `~/.jdc/config` (CLI) + `{{env.JDC_*}}` (SDK) |

---

## Changelog

| 版本 | 日期 | 变更 |
|:----|:----|------|
| 1.0.0 | 2026-06-08 | 初始版本: jdcloud-arch-advisor 自我五支柱评估 (元认知); 含评估主流程伪代码、评分标准 (L1-L4)、风险分级 (P0-P3)、改进建议模板、评分卡 JSON 模板、与 waf-*.yaml 规则映射、缺失 skill manual check 列表 |
