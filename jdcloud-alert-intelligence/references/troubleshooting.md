# 告警智能助手 — 故障排查指南

> 本文件列举 `jdcloud-alert-intelligence` v0.1 常见的失败场景与处理建议。
> **本 Skill 全程只读**：故障排查不涉及资源变更；如需变更请委派相应 `jdcloud-*-ops`。

## 1. 前置检查失败

### 1.1 凭证缺失

**现象**：
```
FAIL: JDC_ACCESS_KEY 未设置
FAIL: JDC_SECRET_KEY 未设置
```

**根因**：环境变量 `JDC_ACCESS_KEY` / `JDC_SECRET_KEY` 未设置，或 `~/.jdc/config` INI 未配置。

**处理**：
1. **环境变量检查**（仅检查存在性，不打印值）：
   ```bash
   test -n "$JDC_ACCESS_KEY" || { echo "FAIL: JDC_ACCESS_KEY 未设置"; exit 1; }
   test -n "$JDC_SECRET_KEY" || { echo "FAIL: JDC_SECRET_KEY 未设置"; exit 1; }
   ```
2. **jdc CLI 凭证加载**（仅从 `~/.jdc/config` INI 读取，**不**读环境变量）：
   ```ini
   [default]
   access_key = <your-access-key>
   secret_key = <your-secret-key>
   region_id = cn-north-1
   ```
3. **沙箱环境**（HOME 重定向）：
   ```bash
   export HOME=/tmp/jdc-home
   mkdir -p $HOME/.jdc
   cat > $HOME/.jdc/config <<'CONFIGEOF'
   [default]
   access_key = ...
   secret_key = ...
   region_id = cn-north-1
   CONFIGEOF
   printf "%s" "default" > $HOME/.jdc/current
   ```

> 详细凭证加载链路见 [core-concepts.md §6.1](./core-concepts.md) 与
> [SKILL.md §Step 0](../SKILL.md#step-0-前置检查)。

### 1.2 时间窗超出保留期

**现象**：
```
错误: 起始时间 > 180d 前，超出最长可分析窗口
```

**根因**：京东云云监控原始数据保留 15d，1h 聚合 30d，1d 聚合 180d。超过 180d 的查询被拒绝。

**处理**：
- 缩短时间窗至 ≤ 15d（最优，能用原始告警数据）
- 15d-30d：fallback 到 1h 聚合接口（v0.2 实现）
- 30d+：fallback 到 1d 聚合（仅做趋势，不做精确告警分级）

### 1.3 区域 ID 错误

**现象**：`region-not-found` 或返回空数据。

**处理**：确认区域 ID 拼写正确，常用：
- `cn-north-1`（华北-北京）
- `cn-east-1`（华东-上海）
- `cn-south-1`（华南-广州）

## 2. jdc CLI 调用失败

### 2.1 命令格式错误

**现象**：`error: unknown flag --no-interactive` 或 `unknown command`。

**根因**：使用了不存在的 `--no-interactive` 标志，或子命令顺序错误。

**处理**：
- **删除** `--no-interactive`（jdc 默认非交互式）
- **`--output json` 必须放在子命令之前**：
  ```bash
  # 正确
  jdc --output json monitor describe-alarm-history ...
  # 错误
  jdc monitor describe-alarm-history --output json ...
  ```

### 2.2 单次调用超时

**现象**：`error: timeout` 或 `connection reset`。

**处理**：
- 自动重试 3 次（指数退避 0s → 2s → 4s）
- 仍失败 → **不静默吞错**，返回原始错误响应给上层 Agent
- v0.1 不支持 fallback 到 SDK 后再 retry（jdc 3 次失败即终止）

### 2.3 限流（RateLimitExceeded）

**现象**：`RateLimitExceeded` 或 HTTP 429。

**处理**：
- 重试 3 次（指数退避 0s → 2s → 4s）
- 单次分析总调用次数 ≤ 10 次（避免触发限流）
- 多页场景：使用 `--page-number` 循环，而非并行调用

### 2.4 分页数据丢失

**现象**：拉取 7d 数据时只返回前 100 条，后续数据未拉到。

**处理**：
- 使用 `--page-number N` 循环：
  ```bash
  for page in 1 2 3 4 5; do
    jdc --output json monitor describe-alarm-history \
      --region-id cn-north-1 \
      --start-time "..." --end-time "..." \
      --page-number $page --page-size 100
  done
  ```
- 检查 `$.result.totalCount` 判断是否拉完

## 3. 聚合阶段问题

### 3.1 三元组不完整

**现象**：聚合后 Cluster 数远少于原始事件数。

**根因**：原始事件中 `serviceCode` / `resourceId` / `metricName` 任一为 null。

**处理**：
- 单条不完整事件**不参与聚合**，直接进入分级（按单事件处置）
- 在报告中标注"X 条事件因三元组不完整被单独处置"
- 长期方案：检查告警规则配置，确保 resource_id 已正确关联

### 3.2 聚合后簇数过多（> 500）

**现象**：24h 内聚合后 > 500 个 Cluster，报告过长。

**处理**：
- 加 `severity_filter` 缩小到 P0/P1
- 加 `service_filter` 缩小到目标服务
- 缩短时间窗到 6h
- 考虑分多次分析（按服务拆分）

## 4. 分级阶段问题

### 4.1 业务 tag 缺失

**现象**：资源未打 `business=*` tag，默认 `general`。

**处理**：
- v0.1 缺省值 = `general`（按 R3 规则）
- 报告中标注"业务标签未识别"，提示用户补 tag
- 长期方案：在 `jdcloud-iam-ops` 范围内统一资源 tag 治理

### 4.2 频次计算口径错误

**现象**：用户反馈"应该是高频抖动，但分级没升档"。

**根因**：频次口径为**次/小时**，按时间窗小时数计算。

**处理**：
- 检查时间窗：默认 24h；如用 6h 窗口，触发 30 次 → 5 次/h → `mid` 档（非 `high`）
- 调整时间窗到 1h 验证
- 详见 [core-concepts.md §1.4](./core-concepts.md) "频次维度"

### 4.3 P0/P1 漏报

**现象**：用户认为应该是 P0 但本 Skill 输出 P1。

**根因**：
- 业务影响等级 = 边缘（peripheral）时，最多 P1
- 多资源同时告警需 ≥ 3 个 resource_id
- S/D/F 三维判定与业务影响等级交叉，需看完整矩阵

**处理**：
- 检查 [severity-matrix.md §1.3](./severity-matrix.md) 完整矩阵
- 边界 case 见 [severity-matrix.md §7](./severity-matrix.md)

## 5. 抑制阶段问题

### 5.1 周期性误判（漏判真故障）

**现象**：真实故障被识别为"已知周期性"降档。

**根因**：周期性检测依赖历史 7d 数据；若过去 7d 该资源多次触发相同告警，会误判。

**处理**：
- 检查 `match_periodic()` 返回的 distinct_days 与日期分布
- 报告中"置信度"字段可辅助判断（< 0.6 应复核）
- v0.1 简化：仅按"≥ 3 天"判定；v0.2 引入 ML 加权

### 5.2 维护窗 tag 未识别

**现象**：资源 tag 含 `maintenance_window=...`，但本 Skill 未命中。

**根因**：
- tag 拉取失败（资源无 `describe-*` 权限）
- tag 格式非法（不在 ISO 8601 区间格式）
- tag 写在其他字段（如 `maintenance_window_2026q2`）

**处理**：
- 检查 tag 命名（必须是 `maintenance_window` 或 `maintenance_recurring`）
- 检查 tag 值格式（`START/END` ISO 8601 或 cron `M H * * *`）
- 检查 IAM 权限（需 `vm:DescribeInstances` / `rds:DescribeDBInstances` 等）

### 5.3 已知误报误抑制

**现象**：真实告警被识别为备份/批处理/滚动重启/CD 回切/镜像拉取，降到 P3。

**根因**：
- 资源命名包含 `backup` / `batch` 等关键字（如 `i-prod-backup-test`），但实际不是备份节点
- 指标名匹配过宽（如 `vm.network.out` 命中镜像拉取，但实际是大量上传）

**处理**：
- 检查误报规则的 `metric_prefix` 与 `time_window`
- 报告中标注 `suppressed_by=known_fp` 的人工复核建议
- v0.2 引入 ML 加权，区分真误报和真故障

## 6. 报告生成问题

### 6.1 报告缺失 P0/P1 详单

**现象**：报告显示"无 P0/P1 簇"，但用户认为应该有。

**处理**：
- 检查 `severity_filter` 是否被设置（如 `--severity-filter P2,P3` 会过滤 P0/P1）
- 检查时间窗是否包含目标时段
- 重新拉取 `describe-alarm-history` 验证原始数据

### 6.2 next_hop 字段缺失

**现象**：报告中 P0 簇没有"下一跳建议"。

**处理**：
- 本 Skill **必填**每个 P0/P1 簇的 next_hop（自检清单第 4 项）
- 若缺失，说明 `service_code` 不在委派表（见 [core-concepts.md §1.3](./core-concepts.md)）
- 临时处理：在报告中标注"暂无对应产品 skill，建议人工排查"

## 7. 跨 Skill 委派问题

### 7.1 委派后下游 skill 拒绝

**现象**：本 Skill 建议委派给 `jdcloud-clb-ops`，但下游报错"权限不足"。

**处理**：
- 检查 IAM：下游 skill 需要 `clb:Describe*` + `clb:Update*` 权限
- 当前 IAM 仅有 `monitor:Describe*` 读权限，无法执行变更
- 详细 IAM 配置委派 [`jdcloud-iam-ops`](../../jdcloud-iam-ops/SKILL.md)

### 7.2 委派循环

**现象**：本 Skill 建议 A skill，A skill 又建议本 Skill。

**处理**：
- 检查委派表（[core-concepts.md §1.3](./core-concepts.md)）
- 本 Skill **只读**，永不委派回自己
- 上层 Agent 应基于 `next_hop` 决策，避免循环

## 8. v0.1 已知局限

| 局限 | 表现 | 计划版本 |
|---|---|---|
| 业务 tag 依赖资源 tag | 未打 tag 默认 `general`，可能与实际不符 | v0.2 + `jdcloud-iam-ops` tag 治理 |
| 周期性窗口固定 7d | 不支持用户自定义窗口 | v0.2 |
| 频次窗口与时间窗强绑定 | 时间窗缩短会减少 F 维度数值 | v0.2 |
| 跨服务关联未实现 | P0-3 检测需要 v0.2 rca-engine | v0.2 |
| 不识别应用层告警 | 仅识别云资源层告警（vm.cpu / rds.qps 等）| v0.3 |
| 已知误报 v0.1 仅靠 tag + 命名 | 覆盖率 60-80% | v0.2/0.3 接 rca-engine |

## 9. 调试技巧

### 9.1 启用 jdc CLI 调试模式

```bash
JDC_LOG_LEVEL=DEBUG jdc --output json monitor describe-alarm-history ...
```

### 9.2 单独验证 jdc 命令

```bash
# 验证时间窗
echo "Start: $(date -d '2026-06-02 00:00:00' +'%s')"
echo "End:   $(date -d '2026-06-03 00:00:00' +'%s')"

# 验证 region
jdc --output json monitor describe-alarms --region-id cn-north-1 --page-size 1 | head -50
```

### 9.3 单步排查

```bash
# Step 1 单独验证
jdc --output json monitor describe-alarm-history \
  --region-id cn-north-1 \
  --start-time "..." --end-time "..." --page-size 10 | jq '.result.alarmHistoryList | length'
```

## 10. 联系支持

- **Skill 自身 bug / 文档疑问**：在仓库提 Issue
- **京东云 API 错误**：京东云工单系统（jdcloud 控制台 → 工单）
- **IAM / 权限问题**：委派 [`jdcloud-iam-ops`](../../jdcloud-iam-ops/SKILL.md)
- **数据保留期问题**：联系京东云技术支持

> 本 Skill 仅做"告警后处理"，不直接修复底层资源问题。资源问题请委派各 `jdcloud-*-ops`。