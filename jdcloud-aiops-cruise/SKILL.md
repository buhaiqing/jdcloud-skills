---
name: "jdcloud-aiops-cruise"
version: "1.6.1"
metadata:
 description: "JD Cloud 全链路巡检 Skill —覆盖 EIP审计/CLB升级评估/VM/K8s/Redis/NAT/安全组的自动拓扑发现与深度诊断"
 cli_applicability: "partial"
 cli_version_locked: false
 sdk_version_locked: false
---

# JD Cloud 全链路巡检

## Trigger & Scope

### SHOULD Use

- 需要对指定客户（按标签）的 JD Cloud资源做全链路健康检查时
- 需要排查故障根因时（从 CLB入口到后端数据库的整条链路）
- 需要做容量规划或大促前预检时
- 需要评估 CLB 是否存在连接数/新建连接/健康后端风险，并生成升级建议时
- 需要审计 EIP绑定状态、公网入口与带宽利用风险时
- 需要了解某个客户的 JD Cloud资源拓扑结构时

### SHOULD NOT Use

- 只查单一资源（如单台 VM）→ 使用 `jdcloud-vm-ops`
- 需要修改/变更资源 → 使用对应产品的 ops skill
- 不涉及 JD Cloud资源的巡检 → 不使用

### Cross-Skill Delegation

|需求 |委托 |
|---|---|
| VM 创建/停止/删除 | `jdcloud-vm-ops` |
| Redis 实例 CRUD | `jdcloud-redis-ops` |
| MySQL慢查询分析/索引优化 | `jdcloud-mysql-ops` |
|监控告警规则变更 | `jdcloud-cloudmonitor-ops` |
| CLB升级/升配/监听器或后端变更 | `jdcloud-clb-ops` |
| EIP绑定/解绑/释放/带宽调整 | `jdcloud-eip-ops` |
| IAM/权限管理 | `jdcloud-iam-ops` |

## Variable Convention

| 类型 | 说明 | 示例 |
|---|---|---|
| `{{env.*}}` |运行时环境变量，不提示用户 | `{{env.JDC_ACCESS_KEY}}` |
| `{{user.*}}` |每次巡检时询问用户 | `{{user.customer_name}}` |
| `{{output.*}}` |脚本解析输出 | `{{output.topology}}` |

> 本 skill 使用中文变量名以对齐巡检场景。`{{user.customer_name}}` 为必填标签筛选参数，`{{user.*}}` 其他变量随巡检维度自动提示。

详细场景说明见 [runbooks/00-index.md](runbooks/00-index.md)。

## Execution Flow

### Phase1:嗅探（`scripts/01-perceive/cruise_sniff.py`）

1. **Pre-flight**:读取 runbook 配置，解析阈值
2. **Discover**:扫描客户标签下的 EIP/CLB/VM/Redis/RDS MySQL/NAT/K8s/安全组（EIP 通过只读 `list_eips`纳入发现）
3. **Classify**: 按标签置信度分类部署模式（K8s /传统 /未知）
4. **Build Topology**: 构建 VPC→子网→资源拓扑
5. **Human Confirm**: 低置信度资源输出待确认清单
6. **Output**:拓扑初判报告（Markdown / JSON）

### Phase2:深度巡检（`scripts/02-reason/cruise_analyze.py`）

1. **Collect**:采集6h监控 +昨日/上周环比 +告警历史
2. **Check Spec Limits**: 对比实例规格上限，计算资源水位
3. **Analyze**: Analyzer逐资源分析，包含 CLB升级评估/建议与 EIP审计
4. **Correlate**:链路关联推理，定位根因
5. **Predict**:容量预测（30 天）
6. **Report**: 双格式输出（Markdown + JSON）

## Safety Gates（安全铁律）

> **本 Skill 是纯读（Read-Only）巡检，不执行任何写操作。**
>任何要求变更资源的结论，只输出"建议"，具体操作必须由人工确认后通过对应 ops skill 执行。

| 操作 | 要求 |
|---|---|
|巡检触发 | 必须有 `客户`标签筛选；允许通过只读 list/describe 做发现，但返回/持久化的原始资源数据必须按客户范围最小化，严禁落盘全账号清单 |
|报告输出 | 运行报告 JSON写入 `jdcloud-aiops-cruise/reports/output/`；GCL审计追踪单独写入仓库级 `audit-results/` |
|敏感信息 |隐藏 AK/SK/密码等敏感字段（显示 `<masked>`） |
| 删除/停止/规格变更 | ❌ 不允许自动执行，报告只出建议 |
| CLB升级/升配 | ❌ 不允许自动执行，只输出容量/健康证据与 `jdcloud-clb-ops`委托建议 |
| EIP绑定/解绑/释放/调带宽 | ❌ 不允许自动执行，只输出审计结论与 `jdcloud-eip-ops`委托建议 |

## 新增 AIOps 能力

| 能力 | 输入 | 输出 | Runbook |
|---|---|---|---|
| **CLB 升级评估** | CLB 清单、连接数、健康后端数 | 容量/健康证据链 + 委托 `jdcloud-clb-ops` 建议 | [runbooks/07-clb-upgrade-assessment.md](runbooks/07-clb-upgrade-assessment.md) |
| **EIP 审计** | EIP 清单、带宽利用率、绑定状态 | 风险报告 + 委托 `jdcloud-eip-ops` 建议 | [runbooks/08-eip-audit.md](runbooks/08-eip-audit.md) |

详细阈值与脚本实现见对应 runbook。

## Quality Gate (GCL)

This skill participates in the repository-wide **Generator-Critic-Loop** defined
in `AGENTS.md` §Quality Gate. It is **optional** for this read-only skill.

| Parameter | Value |
|---|---|
| `max_iterations` | **3** |
| `rubric_version` | **v2** |
| `trace_path` | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` |
| `safety_confirm_required` | **false** |
| `hallucination_check` | **optional** |
| `reflexion_integration` | **enabled** |

GCL wraps the three-phase flow: Generator runs sniff/analyze scripts, optional
Hallucination Detector checks command/import structure, Critic scores against
the rubric, Orchestrator persists the trace. Full details:
[references/quality-gate.md](references/quality-gate.md).

## Changelog

| 版本 | 日期 |变更 |
|---|---|---|
|1.6.1 |2026-06-19 | 集中路径导入（`scripts/path_setup.py`）；重命名 validator；替换 emoji 为纯文本；补充 runbook 索引与变量说明。 |
|1.6.0 |2026-06-18 | **GCL v2 rollout**: Phase 6 H (optional) + Phase 7 Reflexion. Extracted detailed GCL guide to `references/quality-gate.md`. |
|1.5.0 |2026-06-10 | 补齐 8/8 refs；强化 Quality Gate 章节，与 AGENTS.md GCL 框架对齐。 |
|1.0.0 |2026-06-06 | 初始版本；三阶段 AIOps 巡检模型。 |
