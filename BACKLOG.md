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
| 🥈 | elasticsearch-ops 补 ref | 7/8 → 8/8 | ~200 行 |
| 🥈 | tag-audit-ops 补 ref | 5/8 → 8/8 | ~600 行 |
| ~~🥉~~ | ~~aiops-cruise 模板对齐~~ | ✅ **v1.5.0 完成** (2026-06-10) | done |
| ~~🥉~~ | ~~alert-intelligence 补 ref~~ | ✅ **v0.3.0 完成** (2026-06-10) | done |

> **说明**：v1.9.0 批 (2026-06-10) 完成了 4 个 AI OPS skill 的系统性评审,原优先级表中的
> 🥉 项已收敛。剩余待办见下方 Phase E。

---

---

## Phase B — 新 Skill 创建

### 1. `jdcloud-oss-ops` (对象存储)

| 项目 | 内容 |
|------|------|
| **对应阿里云** | `alicloud-oss-ops` |
| **状态** | ✅ 已完成 (2026-06-08) |
| **受影响的 WAF 规则** | WAF-SEC-010 (Bucket ACL), WAF-COST-009 (生命周期), WAF-REL-009 (跨区复制) |
| **CLI 验证** | `jdc` 不支持 OSS, 标记为 `sdk-only` |
| **文件数** | SKILL.md(611行) + 8 refs + tests + fixtures = 16 文件 |

### 2. `jdcloud-nat-ops` (NAT 网关)

| 项目 | 内容 |
|------|------|
| **对应阿里云** | `alicloud-nat-ops` |
| **状态** | ✅ 已完成 (2026-06-08) |
| **受影响的 WAF 规则** | WAF-REL-010 (NAT 高可用), WAF-PERF-049 (NAT 带宽) |
| **CLI 验证** | NAT 在 VPC 产品线内, CLI 通过 `jdc vpc` 子命令 |
| **文件数** | SKILL.md(827行) + 8 refs + tests + fixtures = 16 文件 |

### 3. `jdcloud-kubernetes-ops` (JCS for Kubernetes)

| 项目 | 内容 |
|------|------|
| **对应阿里云** | `alicloud-ack-ops` + `alicloud-ack-serverless-ops` |
| **状态** | ✅ 已完成 (2026-06-08) |
| **依赖方** | `jdcloud-aiops-cruise` 的 `k8s_analyzer.py` 需要此 skill |
| **文件数** | SKILL.md(844行) + 8 refs + tests + fixtures = 16 文件 |

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
| ✅ `jdcloud-aiops-cruise` | **8/8** | 8/8 | done (v1.5.0, 2026-06-10) |
| `jdcloud-elasticsearch-ops` | 7/8 | 8/8 | monitoring.md |
| `jdcloud-tag-audit-ops` | 5/8 | 8/8 | core-concepts, cli-usage, api-sdk-usage |
| ✅ `jdcloud-alert-intelligence` | **8/8 + 5 playbooks + examples** | 8/8 | done (v0.3.0, 2026-06-10) |
| ✅ `jdcloud-cloudmonitor-ops` | **8/8 + monitor-pitfalls** | 8/8 | done (v1.5.0, 2026-06-10) |
| ✅ `jdcloud-routines-ops` | **8/8 + regions** | 8/8 | done (v1.1.0, 2026-06-10) |

### 测试覆盖

| Skill | 当前测试 | 需要补充 |
|-------|:-------:|---------|
| `jdcloud-vpc-ops` | ✅ 23/23 | 基线已够 |
| `jdcloud-topo-discovery` | ✅ 73/73 | 可补 sprint16/17/19 测试(3 个文件 ~500 行) |
| ✅ `tests/test_aiops_consistency.py` | ✅ 新增 (v1.9.0) | dry-run 跨 skill 一致性 dry-run(frontmatter version / 8/8 refs / Cross-Skill Delegation 覆盖 / --no-interactive / SECRET_KEY) |
| 其余 13 个 ops skill | ❌ 无 | 每个需要 conftest + smoke + test_rubric |

### 仓库级

| 任务 | 说明 |
|------|------|
| ✅ 更新 AGENTS.md changelog | 1.9.0 批条目已写入 (2026-06-10) |
| ✅ 新增 CI workflow | `.github/workflows/aiops-audit.yml` 草案 (v1.9.0, 2026-06-10) |
| 更新 WAF 规则注释 | `data_source:` 处加版本号标注何时创建对应 skill |

---

## Phase E — AI OPS 系统性评审（v1.9.0 批次，2026-06-10）

### 评审范围

4 个 AI OPS skill 同步升版本：

| Skill | from → to | 8/8 refs | GCL | 关键变化 |
|-------|-----------|:--------:|:---:|----------|
| `jdcloud-aiops-cruise` | 1.4.0 → **1.5.0** | ✅ | optional, max_iter=3 | +5 refs、Quality Gate GCL 章节 +56 行、Safety 红线表、跨 Skill GCL 兼容性 |
| `jdcloud-alert-intelligence` | 0.2.0 → **0.3.0** | ✅ | optional, max_iter=5 | R1/R2/R3 口径同步（§1.3 联动）+4 refs、术语统一 |
| `jdcloud-cloudmonitor-ops` | 1.4.0 → **1.5.0** | ✅ | recommended, max_iter=3 | GCL 章节整合、双向路由修复（parent_skill / ecosystem_skills 元数据） |
| `jdcloud-routines-ops` | 1.0.0 → **1.1.0** | ✅ | optional, max_iter=3 | +8 refs、职责边界表、Cross-Skill Delegation 表新增 |

### 仓库级一致性产物

- ✅ AGENTS.md changelog 1.9.0 条目（4 个 skill 升版本记录 + Cross-Skill Delegation 表追加 11 个 skill 入口）
- ✅ BACKLOG.md（本文件）：Phase D 状态推进、优先级矩阵收敛
- ✅ progress.md：「AI OPS 系统性评审与优化批次」section 已写入
- ✅ tests/test_aiops_consistency.py：dry-run 一致性检查（frontmatter / refs / delegation / CLI / secret 五项）
- ✅ .github/workflows/aiops-audit.yml：CI workflow 草案（pytest + markdownlint）

### 下一批次建议（v1.10.0 候选）

- **Token efficiency 优化**（详见 progress.md「Token efficiency 评估」section）
  - `jdcloud-cloudmonitor-ops/SKILL.md` 805 行偏大，可下沉"操作：xxx"章节到 `references/cli-usage.md`
  - `jdcloud-alert-intelligence/SKILL.md` 407 行，Step 1-5 工作流 sub-steps 可下沉
  - `jdcloud-routines-ops/SKILL.md` 312 行，Example + Output Artifacts 可下沉
- **AI OPS 集成测试**：在 `tests/test_aiops_consistency.py` 基础上加真实 `jdc` mock 调用
- **`rds_mysql_analyzer` / `rds_postgresql_analyzer` 占位骨架升级**：等 `jdcloud-mysql-ops` / `jdcloud-postgresql-ops` 提供 slow_log API 后升级

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
| 2026-06-10 | **Phase E — AI OPS 系统性评审（v1.9.0）**: 4 个 skill 升版本（aiops-cruise 1.5.0 / alert-intelligence 0.3.0 / cloudmonitor-ops 1.5.0 / routines-ops 1.1.0）；8/8 refs 全部补齐；GCL 推广完整；Cross-Skill Delegation 表新增 11 个 skill 入口；新增 `tests/test_aiops_consistency.py` + `.github/workflows/aiops-audit.yml` 草案；BACKLOG 优先级矩阵收敛（原 🥉 项全部 done） |
| 2026-06-08 | Phase B 完成: 创建 jdcloud-oss-ops、jdcloud-nat-ops、jdcloud-kubernetes-ops 三个 Skill (各 16 文件) |
| 2026-06-08 | 创建 BACKLOG.md,从对话上下文迁移待办事项 |