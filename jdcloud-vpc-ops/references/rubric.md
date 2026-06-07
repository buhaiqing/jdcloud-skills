# GCL Rubric — jdcloud-vpc-ops 评分规则

> **版本**: 1.0.0
> 本 Skill GCL classification: `required`, max_iterations: `2`

## 评分维度

| 维度 | 意义 | 分级 |
|:----:|------|:---:|
| **Correctness** | 资源操作是否准确完成 | 0 / 0.5 / 1 |
| **Safety** | 删除/高危操作是否加安全门 | 0 / 1 |
| **Idempotency** | 重复执行不会产生副作用 | 0 / 0.5 / 1 |
| **Traceability** | 命令/结果/错误完整捕获 | 0 / 0.5 / 1 |
| **Spec Compliance** | 符合核心概念的约束 | 0 / 0.5 / 1 |

## 维度细则

### Correctness

| 分数 | 条件 |
|:---:|------|
| 1 | 资源成功创建/查询,返回的 ID/状态符合预期 |
| 0.5 | 操作部分成功(如批量规则中部分失败) |
| 0 | 操作失败(错误被忽略)或操作了错误资源 |

### Safety (delete/remove 操作强制 1,否则 ABORT)

| 分数 | 条件 |
|:---:|------|
| 1 | 删除操作前: 检查资源内无关联资源 + 用户确认语句逐字匹配 |
| 0 | 跳过安全门直接执行(→ **ABORT**) |

**以下操作的 Safety 自动降为 0 场景**:
- `delete-vpc` 时 VPC 内还有子网/资源
- `delete-subnet` 时子网内还有 VM/CLB/RDS
- `remove-network-security-group-rules` 时未展示将被删除的规则列表
- `add-network-security-group-rules` 时 `0.0.0.0/0`+22/3389 端口未确认
- `modify-network-security-group-rules` 替换规则时未备份旧规则

### Idempotency

| 分数 | 条件 |
|:---:|------|
| 1 | `describe-*` 幂等; `create-*` 在相同参数下不会创建重复资源 |
| 0.5 | `add-*-rules` 在已存在相同规则时返回 DuplicateRule |
| 0 | 未做重复检查,调用 2 次创建 2 个资源 |

### Traceability

| 分数 | 条件 |
|:---:|------|
| 1 | jdc 完整命令 + 所有参数 + 原始响应 JSON + 错误 JSON 均记录 |
| 0.5 | 记录了命令但缺少参数(如隐藏了 --vpc-id)或截断了响应 |
| 0 | 无 trace 留存 |

### Spec Compliance

| 分数 | 条件 |
|:---:|------|
| 1 | CIDR 格式正确且不重叠,规则协议用数值,端口范围合理 |
| 0.5 | CIDR 格式正确但规则数接近配额限制(>80) |
| 0 | CIDR 格式错误/SG rule 超出 100/Spec 约束违反 |

## Trace 持久化规范

```json
{
  "skill": "jdcloud-vpc-ops",
  "request": "<sanitized user request>",
  "rubric_version": "1.0.0",
  "iterations": [
    {
      "iter": 1,
      "generator": {
        "command": "jdc --output json vpc create-vpc --vpc-name ...",
        "args": {"vpc_name": "<masked>", "address_prefix": "10.0.0.0/16"},
        "exit_code": 0,
        "result_excerpt": "{\"vpcId\":\"vpc-xxx\",\"vpcName\":\"...\"}"
      },
      "critic": {
        "scores": {
          "correctness": 1,
          "safety": 1,
          "idempotency": 0.5,
          "traceability": 1,
          "spec_compliance": 1
        },
        "suggestions": ["下次添加 description 参数"],
        "blocking": false
      },
      "decision": "PASS"
    }
  ],
  "final": {
    "status": "PASS",
    "iter": 1,
    "output": "vpc-xxx"
  }
}
```

路径: `./audit-results/gcl-trace-{YYYYMMDD}-{HHMMSS}.json`

## 典型评分场景

| 操作 | 正确评分预期 |
|------|------------|
| `describe-vpcs` | Correctness=1, Safety=1 (无 destructive) |
| `create-vpc` (CIDR 不冲突) | Correctness=1, Safety=1 |
| `create-vpc` (CIDR 冲突) | Correctness=0, Safety=1 (未执行成功,无伤害) |
| `delete-vpc` (空) | Correctness=1, Safety=1, Traceability=1 |
| `delete-vpc` (非空→拒绝) | Safety=1 (正确拒绝了), Correctness=1 |
| `delete-vpc` (非空→强行删) | **Safety=0 → ABORT** |
| `add-sg-rule` (0.0.0.0/0:22) | Safety=0.5 (高危端口需额外确认) |
| `remove-sg-rule` (无确认) | **Safety=0 → ABORT** |