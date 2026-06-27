# JD Cloud Skills — Backlog

> 仓库级待办清单。与 `AGENTS.md` 配合使用:执行策略见 AGENTS.md,具体任务见本文件。
>
> **审计日期**: 2026-06-27 — 对照实际仓库状态完整校对一次。
> **校对方法**: 对每个 `jdcloud-*/SKILL.md` 读 frontmatter 版本号,列 `references/` 文件数,与 BACKLOG 历史条目逐项比对。

---

## 当前真实状态（校对后）

### ✅ 已完成 — 历史成果汇总（仅记录，不作为待办）

| Phase | 完成项 | 日期 | 备注 |
|:-----:|--------|:----:|------|
| **A** | v1.x 早期 skill 27 个 (vm/redis/mysql/pg/mongo/es/vpc/iam/kms/eip/clb/cloudmonitor/audit/dns/cert/oss/nat/k8s/waf/oss/disk/fc/jcq/billing 等) | 2026-05 ~ 06-08 | 见 AGENTS.md Changelog 1.0~1.7 |
| **B** | 3 个 Phase B 新 skill（oss-ops / nat-ops / kubernetes-ops） | 2026-06-08 | ✅ BACKLOG 原条目准确 |
| **E** | AI OPS 4 skill 系统性评审（aiops-cruise 1.6.1 / alert-intelligence 0.4.0 / cloudmonitor-ops 1.8.0 / routines-ops 1.4.0） | 2026-06-10 | ✅ BACKLOG 原条目准确 |
| **F-配置** | AGENTS.md 新增 Python Validation 段；pyproject.toml 锁定 ruff 规则集 | 2026-06-27 | ✅ |

### ⚠️ BACKLOG 校对中发现的过期条目（已删除/合并）

| 原 BACKLOG 条目 | 实际状态 | 处置 |
|----------------|---------|------|
| Phase C: `jdcloud-jcq-ops` 待做 | **已完成 v1.1.0 / 8 refs** | 移除 |
| Phase C: `jdcloud-billing-ops` 待做 | **已完成 v1.1.0 / 9 refs（含 cost-optimization）** | 移除 |
| Phase C: `jdcloud-auto-scaling-orch` 待做 | 命名违规（不是 `jdcloud-[product]-ops`） | **重新评估**：伸缩组归属 `jdcloud-vm-ops` 子能力，不新建 skill |
| Phase D: elasticsearch-ops 缺 monitoring | **已有 monitoring.md** | 移除 |
| Phase D: alert-intelligence 缺 ref | **8/8 + playbooks + examples, v0.4.0** | 移除 |
| Phase D: cloudmonitor-ops 缺 ref | **8/8 + monitor-pitfalls, v1.8.0** | 移除 |
| Phase D: routines-ops 缺 ref | **8/8 + regions, v1.4.0** | 移除 |
| Phase D: aiops-cruise 缺 ref | **11 refs, v1.6.1** | 移除 |

---

## Phase C — 真未做的 Skill（校对后）

> 唯一未做：**jdcloud-cdn-ops**。`auto-scaling` 经讨论归 vm-ops 子能力（见下方决策记录）。

### C-1. `jdcloud-cdn-ops`（CDN 加速）

| 项目 | 内容 |
|------|------|
| **对应阿里云** | `alicloud-cdn-ops` |
| **状态** | ✅ **已完成 v1.0.0**（2026-06-27）|
| **CLI 验证** | `jdc cdn` 暴露 ~150 子命令 → CLI-first with SDK fallback（不是 SDK-only）|
| **实际交付** | 17 文件 / 2194 行 / 19 测试 passed / ruff 全过 |
| **受影响的 WAF 规则** | WAF-PERF-048（CDN 命中率评估）→ **已同步补 arch-advisor 真规则定义** |
| **附带改动** | `jdcloud-arch-advisor/references/rules/waf-performance.yaml` 新增 WAF-PERF-048 真实定义（命中率 ≥ 90%）；`integration.md` 行更新为自动化路径 |

**实施细节**（已解决）：
- ✅ `jdc cdn` CLI 覆盖完整，~150 子命令，含 domain CRUD / cache rule / origin / refresh / 统计
- ✅ WAF-PERF-048 metric_formula: `1 - (origin_traffic / total_traffic)`，window=7天，threshold ≥ 0.90
- ✅ Cross-skill delegation 完整：oss-ops（回源）/ cert-ops（HTTPS）/ waf-ops（防护）/ cloudmonitor-ops（告警）
- ✅ GCL classification: recommended, max_iter=3

### 决策记录：auto-scaling 归属

- **结论**：伸缩组（AS group）不新建独立 skill，归入 `jdcloud-vm-ops` 子章节。
- **依据**：
  - skill-generator 规范命名 `jdcloud-[product]-ops`，`auto-scaling-orch` 不合规
  - vm-ops v1.8.0 已包含实例生命周期管理；伸缩组是实例的弹性调度，逻辑上属于 vm-ops
  - aiops-cruise 已有 `vm_analyzer.py`，可复用
- **行动项**：在 `jdcloud-vm-ops` 增加伸缩组章节（WAF-EFF-002），不新建 skill
- **追踪**：移到 Phase D「细颗粒度补全」

---

## Phase D — 细颗粒度补全（校对后真缺口）

### D-1. 文档对齐 — 8/8 ref 检查

| Skill | 版本 | refs | 缺口 | 优先级 |
|-------|:---:|:---:|------|:-----:|
| `jdcloud-elasticsearch-ops` | v2.3.0 | 11/8 | ✅ 超额 | — |
| `jdcloud-tag-audit-ops` | v1.6.0 | 9/8 | ✅ 超额 | — |
| `jdcloud-mongodb-ops` | v1.4.0 | 13/8 | ✅ 超额 | — |
| `jdcloud-vm-ops` | v1.8.0 | 9/8 | ✅ | — |
| `jdcloud-waf-ops` | v1.2.0 | 9/8 | ✅ | — |
| `jdcloud-billing-ops` | v1.1.0 | 9/8 | ✅ | — |
| `jdcloud-cloudmonitor-ops` | v1.8.0 | 14/8 | ✅ 超额 | — |
| **其余 20 个 ops skill** | — | **8/8** | ✅ | — |

→ **结论**：所有 ops skill 文档已 8/8，无缺口。原 BACKLOG 此项整体完成。

### D-2. 测试覆盖

| Skill | 测试状态 | 缺口 |
|-------|:-------:|------|
| `jdcloud-vpc-ops` | ✅ 23/23 | 无 |
| `jdcloud-topo-discovery` | ✅ 73/73 | 无（BACKLOG 原说可补 sprint16/17/19 是 nice-to-have） |
| `tests/test_aiops_consistency.py` | ✅ 已存在 | 无 |
| **其余 26 个 ops skill** | ❌ 无测试 | conftest + smoke + test_rubric |

→ **结论**：测试覆盖是真缺口。但 26 个 skill 都补一遍工作量大；建议选 5-8 个高风险 ops skill 优先。

### D-3. AGENTS.md / README 表格校对

校对 BACKLOG 与 AGENTS.md（v2.0.0）的 Cross-Skill Delegation 表：
- 27 个 ops skill + 5 AI OPS skill + 1 meta = 33 项
- AGENTS.md 表完整度：待抽校验（不在本次范围）

### D-4. 伸缩组归属 vm-ops（接 Phase C 决策）— **已放弃**

| 任务 | 内容 |
|------|------|
| **决策** | ❌ **放弃实现** |
| **原因** | JD Cloud ESS（弹性伸缩）**无 CLI/SDK 支持**。`jdc` 只有 `ag`（高可用组），但 AG 不是真正的 auto-scaling（无自动触发规则）。 |
| **WAF-EFF-005 处置** | 保持 `data_source: (无对应 skill，标记为 manual check)`，或更新为 `jdcloud-kubernetes-ops`（HPA 路径）|
| **替代方案** | Kubernetes 场景的弹性伸缩由 `jdcloud-kubernetes-ops` 覆盖（HPA）；VM 场景的弹性伸缩需通过控制台操作 |
| **工作量** | 0（不实施）|

---

## Phase F — Python 代码质量基线（ruff 落地，2026-06-27）

| 任务 | 状态 | 说明 |
|------|:----:|------|
| AGENTS.md 新增 Python Validation 段 | ✅ | 已写入 |
| pyproject.toml 新增 `[tool.ruff]` 配置 | ✅ | 已锁定规则集 E/W/F/UP/B/SIM/C4, line-length=100 |
| `dev` 依赖声明 `ruff>=0.6` | ✅ | 已写入 |
| `clean_python.sh` 已含 `.ruff_cache` 清理 | ✅ | 已具备,无需修改 |
| 历史代码 `ruff check .` 422 个错误清理 | ✅ **F-1 完成** / ⏳ F-2 待办 | 335 个自动修复已完成（2026-06-27），剩余 94 个需手改 |

### F-1. ruff 自动修复（317 个）

```bash
# 一次性自动修
ruff check --fix .
# 再做 unsafe-fixes（36 个）
ruff check --unsafe-fixes .
```

预期产物：~50 个剩余错误（多在 test 文件的 C420/Unnecessary comprehension）。

### F-2. 剩余 ~105 个手改

按错误类型分批：
- C420（Unnecessary dict comprehension）→ 改 `dict.fromkeys`
- E501（Line too long）→ 拆行或 `# noqa: E501`（仅在确实不可避免时）
- F401（Unused import）→ 删除
- UP015（Unnecessary mode arg）→ 改 `open(path)` 不带 mode

---

## 优先级 & 收益矩阵（校对后）

| 优先级 | 任务 | 收益 | 工作量 | 阻塞 |
|:------:|------|------|:------:|:----:|
| 🥇 | **F-1 ruff 自动修复（317 个）** | 立即解锁 CI；为 Phase G 做准备 | 1 个命令 + review | 否 |
| 🥇 | C-1 jdcloud-cdn-ops | ✅ 已完成 | — | — | — |
| 🥈 | D-2 测试覆盖（5-8 个高风险 skill 优先） | ⏳ 待办 | 防止回归；GCL 闭环 | ~2000 行 | 否 |
| 🥈 | D-4 vm-ops 伸缩组章节 | ❌ 已放弃 | JD Cloud ESS 无 CLI/SDK | 0 | — |
| 🥈 | **F-2 ruff 手改（~105 个）** | 收尾 F 阶段 | ~半天 | 否 |

---

## 规则与约定

1. **新 skill 必须使用 `jdcloud-skill-generator` 的模板**
2. **GCL**: destructive ops 为 `required`(max_iter=2), read-only 为 `optional`(max_iter=5)
3. **Python 3.10 必须** — 所有新 skill 在 `metadata.python_version_minimum: "3.10"` 中标注
4. **测试**: 每个新 skill 必须有 `tests/conftest.py` + `test_smoke.py` + `test_rubric.py`
5. **创建完成后**: 更新 `AGENTS.md` + `README.md` + `README_EN.md` 的表格
6. **版本号**: skill 完成时 version=1.0.0, 后续修改递增
7. **Python Lint/Format**: 所有 `.py` 变更后必须跑 `ruff check .` + `ruff format .`（见 AGENTS.md `Validation > Python`）

---

## Changelog

| Date | Change |
|------|--------|
| 2026-06-27 | **AGENTS.md 新增规则**: "Post-Change Self-Review (Mandatory)" — 每次改动后必须执行结构化自我评审（ruff/test/F821/commit-size/BACKLOG-sync/self-critique 7 项检查），通过后才能 claim completion |
| 2026-06-27 | **F-1 完成**: ruff 自动修复 335 个错误（422 → 94 剩余）；所有 66 个测试通过；提交 85 文件 / +2736/-492 行；Phase F 进度: 335/422 自动修复完成，剩余 94 个手改（F-2）|
| 2026-06-27 | **D-4 放弃**: JD Cloud ESS 无 CLI/SDK 支持，`ag`（高可用组）≠ 真正 auto-scaling；WAF-EFF-005 更新为 console-only + K8s HPA 替代路径；BACKLOG D-4 状态从 ⏳ → ❌（不实施）|
| 2026-06-27 | **Phase C-1 完成**: `jdcloud-cdn-ops` v1.0.0 创建（17 文件 / 2194 行 / 19 测试通过 / ruff 全过 / CLI-first with SDK fallback）；arch-advisor 同步补 WAF-PERF-048 真实定义（命中率 ≥ 90% metric check）；BACKLOG C-1 状态从 ⏳ → ✅ |
| 2026-06-27 | **BACKLOG 全量校对**: 删除 8 条过期条目（jcq/billing/auto-scaling-orch 命名违规/elasticsearch/alert-intelligence/cloudmonitor/routines/aiops-cruise 文档）；确认 cdn-ops 是 Phase C 唯一真未做；auto-scaling 重新决策为 vm-ops 子章节；Phase F ruff 历史错误 422 个现状确认（317 自动修 + 105 手改）；优先级矩阵收敛到 5 项真待办（F-1 / C-1 / D-2 / D-4 / F-2） |
| 2026-06-27 | **Phase F — Python 代码质量基线**: AGENTS.md 新增 Python Validation 段；pyproject.toml 锁定 ruff 规则集；新增规则 7 |
| 2026-06-10 | **Phase E — AI OPS 系统性评审（v1.9.0 批次）**: 4 skill 升版本，详见 AGENTS.md 1.9.0 changelog |
| 2026-06-08 | Phase B 完成: oss-ops / nat-ops / kubernetes-ops |
| 2026-06-08 | 创建 BACKLOG.md |