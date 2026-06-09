# AIOps Runbooks — `jdcloud-audit-ops`

> **角色定位**：`jdcloud-audit-ops` 在 AIOps 体系中是 **审计证据与变更关联提供者**，不负责指标采集、告警规则 CRUD 或资源修复。它为上层巡检、告警分析和复盘提供「谁在什么时间对哪个资源做了什么」的变更事实。

## 与其他 Skill 的协作边界

| 场景 | 负责的 Skill | 本 Skill 职责 |
|---|---|---|
| 告警聚合、降噪、周报 | `jdcloud-alert-intelligence` | 为告警提供审计关联证据 |
| 指标查询、告警规则 CRUD | `jdcloud-cloudmonitor-ops` | 不参与 |
| 全链路巡检、拓扑、容量 | `jdcloud-aiops-cruise` | 提供变更事件证据 |
| 审计日志、谁改了什么 | `jdcloud-audit-ops`（self） | 查询审计事件 |
| 资源修复 | 对应 `jdcloud-*-ops` | 不执行修复 |

---

## Runbook 1: alert-to-audit-correlation

> **场景**：告警触发后，快速查找告警时间窗口附近的变更操作，判断故障是否由变更引发。

### 输入

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `alarm_time` | ISO 8601 | 是 | 告警触发时间 |
| `resource_id` | string | 否 | 告警关联的资源 ID |
| `resource_type` | string | 否 | 资源类型（vm / redis / clb …） |
| `window_minutes` | int | 否 | 查询窗口，默认 ±30 分钟 |

### 执行步骤

1. 计算 `start_time = alarm_time - window_minutes`，`end_time = alarm_time + window_minutes`
2. 调用 `describe-events`，过滤 `startTime` / `endTime` / `resourceId` / `resourceType`
3. 如结果非空，对每条事件调用 `describe-event-detail` 获取详情（脱敏后）
4. 按 `eventTime` 排序，生成变更时间线
5. 标注高风险操作（Delete / Stop / ModifySecurityGroup / AuthorizeSecurityGroup / AttachPolicy / DetachPolicy）

### 输出

```json
{
  "runbook": "alert-to-audit-correlation",
  "incident_id": "ALARM-20260609-143000",
  "time_window": {
    "start": "2026-06-09T14:00:00+08:00",
    "end": "2026-06-09T15:00:00+08:00"
  },
  "affected_resources": ["sg-xxxx"],
  "timeline": [
    {
      "event_time": "2026-06-09T14:12:00+08:00",
      "event_id": "evt-xxx1",
      "event_name": "ModifySecurityGroup",
      "username": "admin-zhang",
      "resource_id": "sg-xxxx",
      "source_ip": "10.0.*.*",
      "severity": "high",
      "masked_detail": { "requestParameters": "***", "responseElements": "***" }
    }
  ],
  "candidate_root_causes": [
    {
      "rank": 1,
      "reason": "High-risk ModifySecurityGroup event occurred 18 minutes before alarm",
      "confidence": "medium",
      "evidence_event_ids": ["evt-xxx1"],
      "evidence_detail_masked": { "requestParameters": "***", "responseElements": "***" }
    }
  ],
  "evidence": [
    {
      "event_id": "evt-xxx1",
      "event_name": "ModifySecurityGroup",
      "masked_detail_hash": "sha256:abcd1234"
    }
  ],
  "blast_radius": "security group sg-xxxx and attached workloads",
  "recommended_next_skill": "jdcloud-vpc-ops",
  "human_confirmation_required": true,
  "closure_status": "open"
}
```

---

## Runbook 2: change-root-cause-investigation

> **场景**：已知故障时间窗口和受影响资源，从审计日志中定位候选根因。

### 输入

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `incident_start` | ISO 8601 | 是 | 故障窗口开始 |
| `incident_end` | ISO 8601 | 是 | 故障窗口结束 |
| `affected_resources` | string[] | 是 | 受影响资源 ID 列表 |
| `regions` | string[] | 否 | 区域列表，默认 `["cn-north-1"]` |

### 执行步骤

1. 遍历每个 region 和 affected_resource，调用 `describe-events`
2. 聚合所有变更事件，按时间排序
3. 对变更事件分类：
   - **配置变更**：Modify* / Update* / Authorize* / Revoke*
   - **破坏性操作**：Delete* / Stop* / Terminate*
   - **权限变更**：AttachPolicy / DetachPolicy / CreateAccessKey / DeleteUser
4. 计算候选根因的 confidence：
   - 破坏性操作发生在故障窗口前 10 分钟内 → confidence: high
   - 配置变更发生在故障窗口前 30 分钟内 → confidence: medium
   - 权限变更 → confidence: low（需进一步验证）
5. 对每个候选根因获取 `describe-event-detail`（脱敏），关联 evidence

### 输出

```json
{
  "runbook": "change-root-cause-investigation",
  "incident_id": "INC-20260609-001",
  "time_window": {
    "start": "2026-06-09T14:00:00+08:00",
    "end": "2026-06-09T14:45:00+08:00"
  },
  "affected_resources": ["i-xxxx", "sg-xxxx"],
  "timeline": [
    {
      "event_time": "2026-06-09T13:52:00+08:00",
      "event_id": "evt-xxx1",
      "event_name": "ModifySecurityGroup",
      "resource_id": "sg-xxxx",
      "severity": "high",
      "masked_detail": { "requestParameters": "***", "responseElements": "***" }
    }
  ],
  "candidate_root_causes": [
    {
      "rank": 1,
      "reason": "ModifySecurityGroup opened 0.0.0.0/0 ingress on sg-xxxx 8 min before incident",
      "confidence": "high",
      "evidence_event_ids": ["evt-xxx1"],
      "evidence_detail_masked": { "requestParameters": "***" }
    },
    {
      "rank": 2,
      "reason": "StopInstance i-xxxx 12 min before incident",
      "confidence": "medium",
      "evidence_event_ids": ["evt-xxx2"],
      "evidence_detail_masked": { "requestParameters": "***" }
    }
  ],
  "evidence": [
    {
      "event_id": "evt-xxx1",
      "event_name": "ModifySecurityGroup",
      "masked_detail_hash": "sha256:abcd1234"
    },
    {
      "event_id": "evt-xxx2",
      "event_name": "StopInstance",
      "masked_detail_hash": "sha256:ef567890"
    }
  ],
  "blast_radius": "1 security group + 1 VM in cn-north-1",
  "recommended_next_skill": "jdcloud-vpc-ops",
  "human_confirmation_required": true,
  "closure_status": "open"
}
```

---

## Runbook 3: postmortem-evidence-pack

> **场景**：故障复盘时，生成标准化的证据包，供人工确认和归档。

### 输入

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `incident_id` | string | 是 | 事件编号 |
| `time_window` | object | 是 | `{ "start": ISO, "end": ISO }` |
| `affected_resources` | string[] | 是 | 受影响资源列表 |
| `privacy_mode` | string | 否 | `masked_default`（默认）/ `forensic_sealed` |

### 执行步骤

1. 查询时间窗口内所有审计事件（`describe-events`）
2. 对每条事件获取详情（`describe-event-detail`），使用 `mask_sensitive(mode=privacy_mode)` 脱敏
3. 生成变更时间线
4. 标注高风险操作
5. 关联候选根因
6. 输出标准化证据包

### 输出

```json
{
  "runbook": "postmortem-evidence-pack",
  "incident_id": "INC-20260609-001",
  "time_window": {
    "start": "2026-06-09T14:00:00+08:00",
    "end": "2026-06-09T14:45:00+08:00"
  },
  "affected_resources": ["i-xxxx", "sg-xxxx"],
  "privacy_mode": "masked_default",
  "timeline": [
    {
      "time": "2026-06-09T14:12:00+08:00",
      "event_id": "evt-xxx1",
      "event_name": "ModifySecurityGroup",
      "username": "admin-zhang",
      "source_ip": "10.0.*.*",
      "resource_id": "sg-xxxx",
      "severity": "high",
      "masked_detail": { "requestParameters": "***", "responseElements": "***" }
    }
  ],
  "candidate_root_causes": [
    {
      "reason": "...",
      "confidence": "high",
      "evidence_event_ids": ["evt-xxx1"]
    }
  ],
  "evidence": [
    {
      "event_id": "evt-xxx1",
      "type": "configuration_change",
      "severity": "high",
      "masked_detail_hash": "sha256:a1b2c3d4e5f6"
    }
  ],
  "blast_radius": "1 security group + 1 VM in cn-north-1",
  "recommended_next_skill": "jdcloud-vpc-ops",
  "human_confirmation_required": true,
  "closure_status": "evidence_collected"
}
```

---

## 统一输出 Schema

所有 runbook 输出均遵循以下顶层结构：

```yaml
incident_id: string              # 事件编号
time_window:                     # 查询时间范围
  start: ISO 8601
  end: ISO 8601
affected_resources: string[]     # 受影响资源 ID
timeline:                        # 变更时间线
  - time: ISO 8601
    event_id: string
    event_name: string
    username: string             # 按 privacy_mode 脱敏
    source_ip: string            # 按 privacy_mode 脱敏
    resource_id: string          # 按 privacy_mode 脱敏
    severity: low | medium | high
    masked_detail: object        # 脱敏后的 requestParameters / responseElements
candidate_root_causes:           # 候选根因
  - rank: int
    reason: string
    confidence: low | medium | high
    evidence_event_ids: string[]
    evidence_detail_masked: object
evidence:                        # 证据列表
  - event_id: string
    type: string
    severity: string
    masked_detail_hash: string   # SHA-256 前缀，用于关联
blast_radius: string             # 影响面描述
recommended_next_skill: string   # 建议委派的下一个 skill
human_confirmation_required: bool # 是否需要人工确认
closure_status: string           # open | evidence_collected | root_cause_identified | closed
```

### 约束

- 所有 `evidence` 展示必须使用 [Redaction Reference](redaction.md) 中的 `mask_sensitive()` 或 `redact_sensitive_fields()`。
- `closure_status` 只能由人工确认后推进，Agent 不能自动标记为 `closed`。
- `recommended_next_skill` 必须是仓库中已定义的 skill，不能建议未注册的操作。
