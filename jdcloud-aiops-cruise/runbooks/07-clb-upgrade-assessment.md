# Runbook 07 — CLB 升级评估/建议

> 目标：在保持 `jdcloud-aiops-cruise` 纯只读边界的前提下，对客户 CLB 的容量、健康、突发流量风险进行评估，并输出是否建议升级/升配的证据链。

## 适用场景

- 大促前或业务增长期，需要评估 CLB 是否接近规格上限
- 告警显示 CLB 连接数、新建连接或后端健康异常
- 需要给 `jdcloud-clb-ops` 变更前提供只读容量依据

## 三阶段流程

| 阶段 | 输入 | 动作 | 输出 |
|---|---|---|---|
| Perceive | `客户` 标签、区域 | 发现客户名下 CLB、VPC、Subnet、后端关联线索 | 拓扑初判 JSON |
| Reason | Phase 1 输出、云监控指标 | 分析并发连接、新建连接、健康后端数、K8s/传统部署模式 | `warning/critical/info` findings |
| Execute | Reason findings | 仅生成升级/容量建议 | 人工确认后委托 `jdcloud-clb-ops` |

## 核心指标与阈值

| 指标 | Info | Warning | 建议动作 |
|---|---:|---:|---|
| `lb.active_connection_count` / 规格最大并发连接 | ≥ 60% | ≥ 80% | 连续高位时建议评估升级/升配 |
| `lb.new_connection_count` / 规格最大新建连接 | ≥ 60% | ≥ 80% | 检查短连接、突发流量，必要时评估升级 |
| `lb.backend.healthy.host_count` | — | `< 2` 为 Critical | 先修复后端健康，再评估容量 |

默认规格上限见 `references/threshold-definitions.md`。若 JD Cloud API 未返回具体规格，按标准型保守评估。

## 安全边界

- 本 runbook **不执行** CLB 升级、升配、修改监听、注册/摘除后端等写操作。
- 所有变更建议必须写成“只读建议”，并标记 `ops_skill: jdcloud-clb-ops`。
- 若用户要求立即升级 CLB，应停止在本 Skill 内执行，并委托 `jdcloud-clb-ops` 走人工确认安全门。

## 示例输出

```text
[clb] 入口CLB
  问题: CLB并发连接峰值410000，达到standard规格上限500000的82%
  处置 → 只读建议：确认业务峰值与后端容量
  处置 → 如连续多个周期高于阈值，由人工通过 jdcloud-clb-ops 评估升配/升级
  操作入口: jdcloud-clb-ops（需人工确认后执行）
```

## Changelog

| 版本 | 日期 | 变更 |
|---|---|---|
| 1.0.0 | 2026-06-09 | 初始版本：CLB 容量/健康/突发流量只读升级评估 |
