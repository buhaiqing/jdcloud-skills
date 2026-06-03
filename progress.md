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
- [ ] **Task 3**: 新建 examples.md（5 个端到端示例，B4 修复）— 由独立 agent 负责
- [ ] **Task 4**: 终审（v0.1.0 发版前）

## Files Changed (Task 2)

- jdcloud-alert-intelligence/SKILL.md (术语 fallback 化 + 凭证链路说明)
- jdcloud-alert-intelligence/references/core-concepts.md (fingerprint + 术语约定小节)
- jdcloud-alert-intelligence/references/suppression-rules.md (cron 格式 + match_window 重写)
- jdcloud-alert-intelligence/references/playbook-suppress.md (--alarm-id)
- jdcloud-alert-intelligence/references/cli-usage.md (v0.1 限制小节 + 漏修 fallback)

## Notes

- 范围严格遵守: 任务 §6 明确 §1.3 范围不动, 故 suppression-rules.md §2.3 中"维护窗内告警一律过滤"保留原样 — 待 §1.3 修复时联动
- §1.3 由独立 agent 修复完成后, 需要再过一轮: 把 §2.3 "过滤" → "降一档" 联动
- B1=A 决策（两段式降档）落地后会需要 playbook-classify.md 与 severity-matrix.md 同步调整, 不在 Task 2 范围

### Task 3 进度（新建 examples.md + 修 B4）
- [x] examples.md 创建完成（499 行，≤500 达标）
- [x] 5 个端到端场景齐全：①压测 ②周报 ③风暴 ④周期 ⑤跨服务
- [x] SKILL.md B4 修复（`> ✅ v0.1.0 起 examples.md 已就绪` 已加在 :253）
- [x] R1/R2/R3 口径验证通过（7 处"降一档"+ 2 处"统一 P3"+ 7 处 `business=` 标签）
- [x] jdc 命令格式合规（0 处 `--no-interactive`）

**已知遗留冲突（不影响本任务，下游批次 1 其他子任务处理）：**
- severity-matrix.md 仍用旧 `business_criticality=core`（R3 未同步）
- playbook-suppress.md §3.4 仍按"周期性一律 P3"（R1 未同步）
- examples.md 按 R1/R2/R3 目标态编写，批次 1 完成后将自动一致

