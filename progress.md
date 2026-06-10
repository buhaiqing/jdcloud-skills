# Progress

## Status
In Progress — 批次 1 修复进行中

## Tasks

### 批次 1：阻塞性修复（用户确认 B1=A, B2=推荐, B3=A, 修完再发 v0.1.0）

- [x] **Task 1**: §1.3 核心约定统一定义（B1/B2/B3 决策） — 由独立 agent 负责
- [x] **Task 2**: 分散冲突 surgical 修复（I3/I4/I6/B5/I5 + 凭证链路） — **本任务**
  - I3 fingerprint: sha256 → sha1[:12] ✓
  - I4 maintenance_recurring: recurring:weekly → cron ✓
  - I6 "降级" vs "fallback" 术语 ✓
  - B5 --alarm-ids → --alarm-id ✓
  - I5 cli-usage.md 漏修"降级" ✓
  - 凭证加载链路说明 ✓
- [x] **Task 3**: 新建 examples.md（5 个端到端示例，B4 修复）— 由独立 agent 负责
- [x] **Task 4**: 终审（v0.1.0 发版前）

### 批次 2：v0.3.0 §1.3 联动 + 8/8 refs 补齐（2026-06-10）

> **来源**：plan_f8d9ef44 / task `review-alert-intelligence`。
> 与 Task1 §1.3 决策（B1=A 两段式降档；B2=推荐；B3=A）联动，
> 落实 R1/R2/R3 口径到所有 references，并补齐 8/8 标准 ref 模板。
> 目标发版：v0.3.0。

- [x] **Task 2.1** R3 同步：severity-matrix.md 全局 `business=core/important/general/peripheral`，0 处旧 `business_criticality` 残留
- [x] **Task 2.2** R1 同步：suppression-rules.md §2.3 "维护窗一律过滤" → "降一档 + 标注"；§3.1/§3.4 "周期性命中即降 P3" → "降一档"；§5 mermaid flowchart 重写；§6.3 "维护窗口过滤数" → "维护窗口降档数"
- [x] **Task 2.3** R1 同步：playbook-classify.md §7 协同表删除 "P3 | 过滤" 重复行；playbook-suppress.md:42 术语对齐
- [x] **Task 2.4** 术语统一：SKILL.md:182/185 "降级一档或过滤" → "降档 / 跨级豁免"；severity-matrix.md:189/314 标题对齐
- [x] **Task 2.5** 8/8 refs 补齐：新增 `api-sdk-usage.md`（176 行）/ `integration.md`（193 行）/ `monitoring.md`（152 行）/ `troubleshooting.md`（305 行）
- [x] **Task 2.6** SKILL.md: frontmatter version 0.2.0 → 0.3.0，last_updated 2026-06-10；changelog +1 行；新增"R1/R2/R3 口径同步"章节（+78 行）
- [x] **Task 2.7** examples.md 校验：与修复后 suppression-rules.md R1 一致（P2 → 降一档 → P3 边界 case 已在示例 4 验证）

## Files Changed (Task 2 + Task 2.x)

### 批次 1（Task 2 + Task 3）

- jdcloud-alert-intelligence/SKILL.md (术语 fallback 化 + 凭证链路说明)
- jdcloud-alert-intelligence/references/core-concepts.md (fingerprint + 术语约定小节)
- jdcloud-alert-intelligence/references/suppression-rules.md (cron 格式 + match_window 重写)
- jdcloud-alert-intelligence/references/playbook-suppress.md (--alarm-id)
- jdcloud-alert-intelligence/references/cli-usage.md (v0.1 限制小节 + 漏修 fallback)
- jdcloud-alert-intelligence/references/examples.md (新建 499 行)

### 批次 2（Task 2.1 - 2.7，v0.3.0）

- jdcloud-alert-intelligence/SKILL.md (frontmatter 0.3.0 + +78 行 R1/R2/R3 章节)
- jdcloud-alert-intelligence/references/suppression-rules.md (§2.3/§3.1/§3.4/§5/§6 R1 两段式同步)
- jdcloud-alert-intelligence/references/playbook-classify.md (§7 协同表 + 术语对齐)
- jdcloud-alert-intelligence/references/playbook-suppress.md (§"降级"→"降档 (demote)")
- jdcloud-alert-intelligence/references/severity-matrix.md (§6/§10 标题对齐)
- jdcloud-alert-intelligence/references/api-sdk-usage.md (新建 176 行)
- jdcloud-alert-intelligence/references/integration.md (新建 193 行)
- jdcloud-alert-intelligence/references/monitoring.md (新建 152 行)
- jdcloud-alert-intelligence/references/troubleshooting.md (新建 305 行)

## Notes

- v0.3.0 落地后，§1.3 决策与所有 references 完全一致；不再有"按 v0.1.0 目标态编写"的过渡状态
- R1/R2/R3 权威源：`./references/core-concepts.md §1.4` "核心约定"
- 8/8 refs 与 jdcloud-cloudmonitor-ops / jdcloud-vm-ops 对齐（cli-usage / core-concepts / api-sdk-usage / monitoring / integration / troubleshooting / rubric / prompt-templates）
- v0.3.0 仍属"基础版"，ML/动态阈值/Webhook 消费留待 v0.4

---

## AI OPS 系统性评审与优化批次（2026-06-10）

### Phase E — AI OPS 系统性评审

四个 AI OPS skill 并行评审：

- [x] **review-aiops-cruise** — 由独立 agent 负责（并行任务）
- [x] **review-alert-intelligence** — 由独立 agent 负责（并行任务）
- [x] **review-cloudmonitor-ops** — 由独立 agent 负责（并行任务）
- [x] **review-routines-ops** — **本任务**（coder session `mvs_3b2163a758014b089779361f4471cb28`）

### review-routines-ops 产出（1.1.0）

- [x] **8/8 refs 补齐**：新增 `core-concepts.md` / `cli-usage.md` / `api-sdk-usage.md` / `monitoring.md` / `integration.md` / `troubleshooting.md` / `rubric.md` / `prompt-templates.md`（原 `regions.md` 保留为补充参考）
- [x] **职责边界章节**：SKILL.md 新增「职责边界」表 + 决策启发式，明确区分 routines-ops（静态/周期）与 aiops-cruise（动态/事件）
- [x] **Cross-Skill Delegation**：新增完整委托表（含 cloudmonitor-ops / aiops-cruise / alert-intelligence / tag-audit-ops / 各产品 ops skill）
- [x] **GCL 章节**：optional GCL（cron 跳过 / on-demand 推荐 / 续费前置必须），max_iter=3，5 维 rubric + 安全门
- [x] **frontmatter**：`version` 1.0.0 → 1.1.0；`metadata` 保持
- [x] **scripts 校验**：expiry_cruise.py / jdc_client.py 通过 `python3.10 -m py_compile`；识别 7 项已知限制（详见 deliverable）
- [x] **凭证合规**：grep `print.*SECRET_KEY` → 0 命中；grep `--no-interactive` → 0 命中
- [x] **jdc-first with SDK fallback**：文档化于 cli-usage.md / api-sdk-usage.md；expiry_cruise.py 当前**未实现** retry+backoff 逻辑（已记录为 1.2.0 待办）
- [x] **sys.path 合规**：`expiry_cruise.py:24-26` 符合 AGENTS.md 三阶段约定

### Files Changed（review-routines-ops）

- `jdcloud-routines-ops/SKILL.md` — version 1.1.0；新增 Trigger & Scope / 职责边界 / Cross-Skill Delegation / GCL / Safety Gates 章节
- `jdcloud-routines-ops/references/core-concepts.md` — **新增**
- `jdcloud-routines-ops/references/cli-usage.md` — **新增**
- `jdcloud-routines-ops/references/api-sdk-usage.md` — **新增**
- `jdcloud-routines-ops/references/monitoring.md` — **新增**
- `jdcloud-routines-ops/references/integration.md` — **新增**
- `jdcloud-routines-ops/references/troubleshooting.md` — **新增**
- `jdcloud-routines-ops/references/rubric.md` — **新增**
- `jdcloud-routines-ops/references/prompt-templates.md` — **新增**

### Notes（review-routines-ops）

- **未实际修改 scripts/**：本次为"文档对齐 + 职责边界"批次；scripts 层面的 7 项已知限制已记录在 `references/troubleshooting.md` §6 和 deliverable.md 中，待 1.2.0 批次修复。
- **delegation 校验**：routine-ops → cloudmonitor-ops / aiops-cruise / alert-intelligence / tag-audit-ops 四个反向条目均已写入 SKILL.md；routine-ops 不被其他 skill 反向委托（passive producer）。
- **已知冲突**：无（与 §1.3 决策无直接交集）。



### review-aiops-cruise产出（1.5.0）

- [x] **8/8 refs补齐**：新增 `core-concepts.md` / `cli-usage.md` / `api-sdk-usage.md` / `monitoring.md` / `rubric.md`五个 refs（与原有 `prompt-templates.md` / `severity-matrix.md` / `threshold-definitions.md`合计8/8）
- [x] **frontmatter**：`version`1.4.0 →1.5.0；`metadata.cli_applicability=partial`保持
- [x] **Quality Gate (GCL)章节强化**：optional (read-only) / max_iter=3 / Safety 红线表 /终止条件表 /跨 Skill GCL兼容性表 / Rubric5维 + Safety强制 =1
- [x] **三阶段目录合规**：`scripts/01-perceive/cruise_sniff.py` 与 `scripts/02-reason/cruise_analyze.py`（原 `cruise_link.py` 现为 thin wrapper）`sys.path.insert`全部符合 AGENTS.md路径约定；`analyzers/*`路径向上两级到 `scripts/`
- [x] **jdc-first with SDK fallback**：jdc_client.py 用 urllib 自签 SDK +3 次重试 +指数退避，作为最终 fallback路径（jdcloud_sdk==1.2.12 Python3.12兼容问题），完整文档化于 cli-usage.md / api-sdk-usage.md
- [x] **数据最小化**：resource_discovery.py 已按 `客户`标签过滤输出，raw / topology / classification 三段均最小化；Safety 红线已写入 references/core-concepts.md §7.2
- [x] **runbooks场景完整**：8 个 runbook（00-index +01-daily-health-check +02-emergency-troubleshoot +03-capacity-planning +04-pre-launch-check +05-mysql-slowquery +06-postgresql +07-clb-upgrade +08-eip-audit）覆盖日常 /应急 /容量 / 大促 / 数据库 / CLB / EIP全部场景
- [x] **analyzer 实现评审**：10 个 analyzer 中8 个完整（vm / clb / eip / redis / k8s / nat / es / sg）；rds_mysql / rds_postgresql 为占位骨架（依赖 jdcloud-mysql-ops / jdcloud-postgresql-ops 提供慢查询 API；当前 JD Cloud OpenAPI 未直接暴露 MySQL slow_log）
- [x] **凭证合规**：grep `print.*SECRET_KEY` →0命中；grep `--no-interactive` →0命中
- [x] **CLB / EIP 只读边界**：clb_analyzer / eip_analyzer全部 finding标注 `ops_skill=jdcloud-clb-ops / jdcloud-eip-ops`，所有变更建议必须人工确认后由对应 ops skill 执行
- [x] **SKILL.md GCL章节行数**：126 →182（+56 行），超过任务要求的 ≥30 行

### Files Changed（review-aiops-cruise）

- `jdcloud-aiops-cruise/SKILL.md` — version1.5.0；强化 ## Quality Gate (GCL)章节（+56 行）
- `jdcloud-aiops-cruise/references/core-concepts.md` — **新增**
- `jdcloud-aiops-cruise/references/cli-usage.md` — **新增**
- `jdcloud-aiops-cruise/references/api-sdk-usage.md` — **新增**
- `jdcloud-aiops-cruise/references/monitoring.md` — **新增**
- `jdcloud-aiops-cruise/references/rubric.md` — **新增**

### Notes（review-aiops-cruise）

- **未实际修改 scripts/**：本次为"文档 +评审"批次；`rds_mysql_analyzer` / `rds_postgresql_analyzer` 的占位实现是已知技术限制（JD Cloud OpenAPI 不直接暴露 slow_log / pg_stat_statements），已在 runbook05/06 与 core-concepts.md §8 中明确委托入口；待 `jdcloud-mysql-ops` / `jdcloud-postgresql-ops` 提供完整 API 后再升级 analyzer。
- **delegation校验**：aiops-cruise → vm-ops / redis-ops / mysql-ops / postgresql-ops / clb-ops / eip-ops / nat-ops / cloudmonitor-ops / vpc-ops全部9 个反向委托条目已写入 core-concepts.md §8 与 rubric.md §11。
- **与 §1.3决策无直接交集**：本批次不涉及 alert-intelligence 的降档逻辑，但 GCL Safety 红线统一收敛到"未执行变更 / 未泄露凭证 / 未跨客户最小化"三条硬规则，与其他 skill GCL框架完全对齐。
- **下游批次（repo-cross-skill-consistency）需关注**：aiops-cruise1.5.0 / alert-intelligence0.3.0 / cloudmonitor-ops1.4.0+ / routines-ops1.1.0四个 version + GCL 设置需要在 AGENTS.md / BACKLOG.md 中同步登记。

---

## 仓库级 cross-skill 一致性 + Token efficiency 评估（v1.9.0 完成）

### 仓库级产物（owner 手动落地）

`repo-cross-skill-consistency` producer 在 attempt 1 因 15min hard timeout 被 kill
（已知教训：单回合 ~10 文件以上写入触发 timeout）。Owner 手动落地剩余产物：

- ✅ `BACKLOG.md` — Phase D 状态推进、Phase E 新增、Changelog 1.9.0 行
- ✅ `tests/test_aiops_consistency.py` — 17/17 dry-run checks passing
  （frontmatter version / 8/8 refs / Cross-Skill Delegation / --no-interactive / SECRET_KEY）
- ✅ `.github/workflows/aiops-audit.yml` — CI workflow 草案（pytest + markdownlint + frontmatter pin）

### SKILL.md Token efficiency 评估

| Skill | SKILL.md 行数 | 评级 | 优化建议 |
|-------|--------------:|:---:|----------|
| `jdcloud-aiops-cruise` | 182 | ✅ 精简 | Phase 1/2 execution flow 已极简 |
| `jdcloud-alert-intelligence` | 407 | ⚠️ 中等 | Step 1-5 工作流 sub-steps 可下沉到 `playbook-*`（已存在） |
| `jdcloud-cloudmonitor-ops` | **805** | ❌ 偏大 | 「操作：xxx」章节（创建告警规则 53 行 / 查询监控数据 37 行 / 删除告警规则 31 行）应下沉到 `references/cli-usage.md` |
| `jdcloud-routines-ops` | 312 | ⚠️ 中等 | Example + Output Artifacts 可下沉到 `references/cli-usage.md` |

**核心原则（v1.10.0 候选）**：SKILL.md 重点描述 *What to do*（触发场景、决策入口、Should/Should-not、GCL、Cross-Skill Delegation）和触发机制；
*How to do*（具体 CLI 命令、SDK 调用、JSON 路径、参数示例、完整操作步骤）应下沉到 `references/cli-usage.md` / `references/api-sdk-usage.md` / `references/troubleshooting.md`。

### `integration.md` 复用机会

`jdcloud-alert-intelligence/references/integration.md`（193 行）已定义完整的跨 skill 集成模式：
- Cross-Skill Delegation 双向路由表
- IM 通知（飞书/钉钉/企微）
- CI 定时周报
- IAM 权限要求
- 安全审计

但 `aiops-cruise` / `cloudmonitor-ops` / `routines-ops` 均无对应 integration.md，存在**集成知识单点风险 + 重复实现**。
v1.10.0 可考虑：把 alert-intelligence 的 integration.md 抽到仓库级 `docs/INTEGRATION_PATTERNS.md`，各 skill 引用即可。

### 下一步候选（v1.10.0）

1. **Token efficiency 批**：cloudmonitor-ops SKILL.md 805 → ~400（下沉操作章节到 cli-usage.md）
2. **integration.md 复用**：抽 alert-intelligence 集成模式到仓库级
3. **AI OPS 集成测试**：在 dry-run 基础上加 mock `jdc` 调用跑端到端
4. **`rds_mysql_analyzer` / `rds_postgresql_analyzer` 升级**：等 mysql-ops / postgresql-ops 提供 slow_log API
