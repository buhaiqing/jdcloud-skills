# 告警智能助手 — 集成指南

> 本文件说明如何将 `jdcloud-alert-intelligence` 集成到自动化工作流、IM 通知、
> 上层 Agent 编排系统中。
>
> **⚠️ 安全警告：** **绝不**在日志、控制台输出或调试信息中打印 `JDC_SECRET_KEY` 的值。
> 验证凭证时仅检查存在性，如需记录状态请使用脱敏占位符（如 `JDC_SECRET_KEY=<masked>`）。
> 报告默认本地输出，不外发。

## 与上游 Agent 的集成

### 输入契约（上层 Agent 应提供）

| 参数 | 类型 | 必填 | 说明 |
|---|---|:--:|---|
| `region` | string | ✓ | 京东云区域 ID（如 `cn-north-1`）|
| `time_window` | string (ISO 8601 区间) | ✓ | 分析时间窗，默认最近 24h |
| `severity_filter` | array | | 仅展示的级别（`P0`/`P1`/`P2`/`P3`）|
| `service_filter` | array | | 仅分析的服务代码（`vm`/`rds`/...）|
| `maintenance_windows` | array | | 用户显式声明的维护窗 |
| `output_dir` | string | | 报告输出目录，默认当前工作目录 |

### 输出契约（本 Skill 产出）

```json
{
  "report_file": "alert_intelligence_report_cn-north-1_20260602_20260603.md",
  "summary": {
    "raw_events": 1247,
    "clusters": 89,
    "severity_distribution": {"P0": 2, "P1": 7, "P2": 14, "P3": 66},
    "suppressed_count": 43,
    "suppression_rate": 0.483,
    "disturbance_rate": 0.517
  },
  "next_hops": [
    {
      "cluster_id": "lb-lb-prod-entry-01-lb.httpcode.5xx",
      "severity": "P0",
      "next_hop": "jdcloud-clb-ops",
      "operation_hint": "检查 lb-prod-entry-01 后端健康度"
    }
  ]
}
```

### 编程接口（Python）

```python
from pathlib import Path
from alert_intelligence import analyze, render_report

result = analyze(
    region="cn-north-1",
    time_window=("2026-06-02T00:00:00+08:00", "2026-06-03T00:00:00+08:00"),
    severity_filter=None,
    service_filter=None,
    maintenance_windows=[],
)

report_path = render_report(result, output_dir=Path("."))
print(f"Report saved to: {report_path}")
```

> **v0.1 范围**：SDK-style API **预留**，具体实现由 v0.2 提供。当前 Agent 通过 `jdc` CLI + JSON 输出
> 直接编排，参考 [cli-usage.md](./cli-usage.md) 与 [examples.md](./examples.md)。

## 与下游 IM 通知的集成

### 飞书 / 钉钉 / 企微

本 Skill 自身**不**直接推送 IM。下游 Agent 读取报告后，自行决定推送策略：

```python
import json
import requests

# 1. 读取本 Skill 输出的报告
with open("alert_intelligence_report_cn-north-1_20260602_20260603.md") as f:
    report_md = f.read()

# 2. 解析为摘要 JSON（按 output contract）
summary = parse_report_summary(report_md)

# 3. 仅 P0/P1 推送 IM
if summary["severity_distribution"]["P0"] > 0:
    feishu_webhook = "https://open.feishu.cn/open-apis/bot/v2/hook/..."
    requests.post(feishu_webhook, json={
        "msg_type": "interactive",
        "card": {
            "header": {"title": {"tag": "plain_text", "content": "🚨 P0 告警簇"}},
            "elements": [{"tag": "markdown", "content": report_md[:3000]}],
        }
    })
```

> **推送原则**：
> - 只推送 P0/P1（高频告警不刷屏）
> - 报告中已附 `next_hop` 字段，IM 卡片可点击跳转 `jdcloud-clb-ops` 等下游 skill
> - 推送频率：建议每个 on-call shift 1 次（避免频繁打扰）

### Webhook（v0.2 预留）

v0.1 不消费告警回调 Webhook；v0.2 计划支持：
- 实时接收 `monitor:AlarmTriggered` 事件
- 立即分级 + 推送到 IM
- 依赖 jdcloud 消息队列 / Function Compute

## 与 on-call 值班系统的集成

### 值班疲劳指标查询

```bash
# 提取本周打扰率（grep 报告 §4）
grep "打扰率" alert_intelligence_report_*.md
# 输出: 打扰率: 51.7% 🟡
```

```python
# 解析值班疲劳报告
import re

def parse_fatigue_metrics(report_path: str) -> dict:
    text = open(report_path).read()
    return {
        "disturbance_rate": float(re.search(r"打扰率[:：]\s*([\d.]+)%", text).group(1)) / 100,
        "night_disturbance_rate": float(re.search(r"夜间打扰率[:：]\s*([\d.]+)%", text).group(1)) / 100,
        "repetition_rate": float(re.search(r"重复率[:：]\s*([\d.]+)%", text).group(1)) / 100,
        "suppressed_count": int(re.search(r"被抑制簇[:：]\s*(\d+)", text).group(1)),
    }
```

## 跨 Skill 协作模式

### 双向路由

| 本 Skill 调用方 | 委派给 | 委派依据 |
|---|---|---|
| 收到告警后, 想要调整规则 | `jdcloud-cloudmonitor-ops` | 本 skill 只读，规则变更必须委派 |
| 收到告警后, 想要排查资源 | 各 `jdcloud-*-ops`（vm/clb/rds/redis）| 本 skill 仅给出 next_hop，不执行 |
| 想要消费告警回调 | `jdcloud-cloudmonitor-ops`（v0.2）| Webhook 在 cloudmonitor-ops 范围 |
| 想要订阅告警 | `jdcloud-cloudmonitor-ops`（createAlarmContact）| 同上 |

### 反向路由（被哪些 skill 调用）

- `jdcloud-aiops-cruise`（v0.2+）— 全链路巡检中告警段委派给本 skill
- 任何上层 Agent 的 on-call 编排 — 直接调用本 skill 的 5 步工作流

## CI / 自动化集成

### 定时周报生成

```bash
# crontab 每周一 09:00 生成上周告警周报
0 9 * * 1 /opt/jdcloud-skills/jdcloud-alert-intelligence/scripts/run_weekly_report.sh
```

`run_weekly_report.sh` 伪代码：

```bash
#!/usr/bin/env bash
set -euo pipefail

END=$(date -d "yesterday 23:59:59" +"%Y-%m-%dT%H:%M:%S+08:00")
START=$(date -d "7 days ago 00:00:00" +"%Y-%m-%dT%H:%M:%S+08:00")
REGION="${JDC_REGION:-cn-north-1}"

# Step 1-4: 通过 Agent 调用本 skill（CLI 编排）
# 输出报告到 reports/weekly/
mkdir -p reports/weekly
echo "Weekly report: reports/weekly/alert_intelligence_${REGION}_${START:0:10}_${END:0:10}.md"
```

> **不要**在 CI 中直接 `print JDC_SECRET_KEY`。CI 环境使用 `~/.jdc/config` INI 文件预置凭证。

## 与 IAM 权限的集成

最低权限（已在 [core-concepts.md §6.2](./core-concepts.md) 定义）：

```
monitor:DescribeAlarmHistory
monitor:DescribeAlarms
monitor:DescribeAlarm
monitor:DescribeMetrics
monitor:DescribeMetricData
```

详细 IAM 策略配置委派 [`jdcloud-iam-ops`](../../jdcloud-iam-ops/SKILL.md)。

## 安全审计集成

- 每次分析：报告文件名包含 region + 时间窗，便于审计追溯
- 不上传到 OSS / 不发邮件（除用户显式确认）
- 详细安全模型见 [core-concepts.md §6](./core-concepts.md)