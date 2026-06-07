# JD Cloud Skills — Backlog

> 仓库级待办清单。统一管理所有 **未完成的 Skill 创建、文档补全、规则更新**工作。
> 与 `AGENTS.md` 配合使用:执行策略见 AGENTS.md,具体任务见本文件。

---

## 优先级 & 收益矩阵

| 优先级 | 任务 | 收益 | 工作量估算 |
|:------:|------|------|:----------:|
| 🥇 | jdcloud-oss-ops | 3 条 WAF 规则从 manual check → 自动评估 | ~2000 行 |
| 🥇 | jdcloud-nat-ops | 2 条 WAF 规则从 manual check → 自动评估 | ~1500 行 |
| 🥇 | jdcloud-kubernetes-ops | aiops-cruise 的 k8s_analyzer 可依赖 | ~3000 行 |
| 🥈 | jdcloud-cdn-ops | 1 条 WAF 规则 | ~1500 行 |
| 🥈 | jdcloud-jcq-ops | 1 条 WAF 规则 | ~1500 行 |
| 🥈 | jdcloud-billing-ops | Cost 支柱量化分析 | ~1500 行 |
| 🥈 | jdcloud-auto-scaling-orch | Efficiency 支柱评估 | ~1500 行 |
| 🥉 | aiops-cruise 模板对齐 | 与标准 8-ref 模板对齐 | ~1500 行 |
| 🥉 | elasticsearch-ops 补 ref | 7/8 → 8/8 | ~200 行 |
| 🥉 | tag-audit-ops 补 ref | 5/8 → 8/8 | ~600 行 |
| 🥉 | alert-intelligence 补 ref | 4/8 → 8/8 | ~800 行 |

---

## Phase B — 新 Skill 创建

### 1. `jdcloud-oss-ops` (对象存储)

| 项目 | 内容 |
|------|------|
| **对应阿里云** | `alicloud-oss-ops` |
| **状态** | ❌ 未开始 |
| **受影响的 WAF 规则** | WAF-SEC-010 (Bucket ACL), WAF-COST-009 (生命周期), WAF-REL-009 (跨区复制) |
| **CLI 验证** | 需确认 `jdc oss` 子命令是否存在 |
| **需要** | SKILL.md + 8 refs + tests + fixtures |
| **依赖** | 京东云 OSS 服务需开通 |

### 2. `jdcloud-nat-ops` (NAT 网关)

| 项目 | 内容 |
|------|------|
| **对应阿里云** | `alicloud-nat-ops` |
| **状态** | ❌ 未开始 |
| **受影响的 WAF 规则** | WAF-REL-010 (NAT 高可用), WAF-PERF-049 (NAT 带宽) |
| **CLI 验证** | NAT 网关在 VPC 产品线内(无独立 CLI),需确认 API |
| **需要** | SKILL.md + 8 refs + tests |
| **已知信息** | `vpc describe-route-tables` 已发现 NAT 网关 `natgw-p7yhj2m3gv` |

### 3. `jdcloud-kubernetes-ops` (JCS for Kubernetes)

| 项目 | 内容 |
|------|------|
| **对应阿里云** | `alicloud-ack-ops` + `alicloud-ack-serverless-ops` |
| **状态** | ❌ 未开始 |
| **依赖方** | `jdcloud-aiops-cruise` 的 `k8s_analyzer.py` 需要此 skill |
| **需要** | SKILL.md + 8 refs + tests |
| **依赖** | JCS for Kubernetes 服务需开通 |

---

## Phase C — 补充 Skill

### 4. `jdcloud-cdn-ops`

| 受影响的 WAF 规则 | 说明 |
|:-----------------|------|
| WAF-PERF-048 | CDN 命中率评估 → 当前 manual check |

### 5. `jdcloud-jcq-ops`

| 受影响的 WAF 规则 | 说明 |
|:-----------------|------|
| WAF-REL-018 | 消息队列熔断检查 → 当前 manual check |

### 6. `jdcloud-billing-ops`

| 说明 |
|------|
| Cost 支柱的账单分析 → 当前 arch-advisor 的 SHOULD NOT Use 表中标记为"无对应 skill" |

### 7. `jdcloud-auto-scaling-orch`

| 受影响的 WAF 规则 | 说明 |
|:-----------------|------|
| WAF-EFF-002 | 伸缩组检查 → 当前 manual check |

---

## Phase D — 细颗粒度补全

### 文档对齐

| Skill | 当前 ref 数 | 目标 ref 数 | 缺失 |
|-------|:----------:|:----------:|------|
| `jdcloud-aiops-cruise` | 4/8 (按标准) | 8/8 | core-concepts, cli-usage, api-sdk-usage, monitoring, rubric |
| `jdcloud-elasticsearch-ops` | 7/8 | 8/8 | monitoring.md |
| `jdcloud-tag-audit-ops` | 5/8 | 8/8 | core-concepts, cli-usage, api-sdk-usage |
| `jdcloud-alert-intelligence` | 4/8 | 8/8 | core-concepts, cli-usage, api-sdk-usage, monitoring |

### 测试覆盖

| Skill | 当前测试 | 需要补充 |
|-------|:-------:|---------|
| `jdcloud-vpc-ops` | ✅ 23/23 | 基线已够 |
| `jdcloud-topo-discovery` | ✅ 73/73 | 可补 sprint16/17/19 测试(3 个文件 ~500 行) |
| 其余 13 个 ops skill | ❌ 无 | 每个需要 conftest + smoke + test_rubric |

### 仓库级

| 任务 | 说明 |
|------|------|
| 更新 AGENTS.md changelog | 补充 GCL v1.x 新技能的条目 |
| 更新 WAF 规则注释 | `data_source:` 处加版本号标注何时创建对应 skill |
| 创建 CI workflow | GitHub Actions 自动运行 `pytest tests/` |

---

## 规则与约定

1. **新 skill 必须使用 `jdcloud-skill-generator` 的模板**
2. **GCL**: destructive ops 为 `required`(max_iter=2),read-only 为 `optional`(max_iter=5)
3. **Python 3.10 必须** — 所有新 skill 在 `metadata.python_version_minimum: "3.10"` 中标注
4. **测试**: 每个新 skill 必须有 `tests/conftest.py` + `test_smoke.py` + `test_rubric.py`
5. **创建完成后**: 更新 `AGENTS.md` + `README.md` + `README_EN.md` 的表格
6. **版本号**: skill 完成时 version=1.0.0,后续修改递增

---

## Changelog

| Date | Change |
|------|--------|
| 2026-06-08 | 创建 BACKLOG.md,从对话上下文迁移待办事项 |