# Execute 阶段（执行层）

## 设计说明

`jdcloud-aiops-cruise` 是**纯只读巡检 Skill**，设计上不直接执行任何资源变更操作。因此本目录不放置实际执行脚本，而是作为以下用途：

1. **Action 建议生成器** — 根据 Reason 阶段输出的 findings，生成标准化的修复建议
2. **自动化脚本模板** — 供人工确认后，通过对应 ops skill 执行的辅助脚本
3. **闭环跟踪记录** — 记录从发现到修复的完整链路

## 安全铁律

| 规则 | 说明 |
|------|------|
| ❌ 禁止直接调用 JD Cloud API 进行变更 | 本 Skill 只读，任何变更必须通过对应 ops skill 执行 |
| ❌ 禁止自动执行修复操作 | 即使生成脚本，也必须人工确认后手动触发 |
| ✅ 只允许生成 Action 建议 | 输出格式化的修复建议，包含推荐的 ops skill 路径 |

## 输出格式示例

```json
{
  "action_type": "recommendation",
  "resource_id": "i-xxxxxx",
  "resource_type": "vm",
  "issue": "CPU 持续超过 85%",
  "recommended_ops_skill": "jdcloud-vm-ops",
  "recommended_action": "upgrade_instance_type",
  "manual_confirmation_required": true,
  "estimated_impact": "服务中断 30 秒",
  "rollback_plan": "保留原实例镜像，可随时回滚"
}
```

## 与其他 Skill 的协作

```
jdcloud-aiops-cruise (发现) → jdcloud-vm-ops (执行变更)
                      ↘ jdcloud-redis-ops
                      ↘ jdcloud-clb-ops
                      ↘ ...
```

## 文件命名规范

- `generate_<resource>_action.py` — 生成特定资源的修复建议
- `template_<action>.sh` — 可执行的脚本模板（需人工确认）
- `track_closure.py` — 跟踪问题闭环状态

## 版本

- v1.0.0 — 初始规范定义（空目录占位）
