# R1 / R2 / R3 口径同步

> 本文档从 `SKILL.md` 提取，记录 v0.3.0 与 `progress.md` Task1 §1.3 决策的同步说明。
> 权威源：[`core-concepts.md §1.4`](./core-concepts.md)。
> 如与其他 references 冲突，以 §1.4 为准。

## R1 — 抑制降档（两段式）

| 命中类型 | 降档规则 |
|---|---|
| 维护窗 | 降一档（P0→P1，P1→P2，P2→P3，P3 不再降）|
| 已知周期性 | 降一档（同上）|
| 已知误报清单（5 类）| **跨级豁免降 P3**（任意级别都降到 P3）|

**约束**：P3 不再降档；维护窗/周期性**不跨级**；已知误报清单跨级豁免；多个命中按"最重抑制"原则。

历史版本（已废弃）：

- ~~维护窗内一律过滤~~ → **降一档 + 标注**（保留入报告，可审计）
- ~~周期性命中一律降 P3~~ → **降一档**（不跨级）
- ~~滚动重启 / CD 流量回切降 P2~~ → **统一跨级豁免降 P3**

## R2 — 频次维度（次/小时口径）

**计算公式**：`频次 = 触发次数 / 时间窗小时数`

| 档位 | 阈值 |
|:--:|:--|
| `low` | < 3 次/小时 |
| `mid` | 3-10 次/小时 |
| `high` | > 10 次/小时 |

时间窗默认 24h；用户可指定 1h / 6h / 24h / 7d。频次窗口与时间窗强绑定，缩短时间窗会减少 F 维度数值。

## R3 — 业务影响等级（业务 tag 约定）

资源 tag 中 `business=*` 字段的 4 个合法值：

| 取值 | 含义 | 默认 |
|---|:--:|:--:|
| `core` | 核心业务（订单/支付/登录/交易链路）| 否 |
| `important` | 重要业务 | 否 |
| `general` | 一般业务 | **是** |
| `peripheral` | 边缘业务 | 否 |

**缺省值**：未打 `business` tag 的资源按 `general` 处理。

历史版本（已废弃）：`business_criticality=core` → **`business=core`**；`normal/edge` → **`general/peripheral`**。

## 术语约定（"降档 (demote)" vs "fallback"）

- **降档 (demote)**：抑制层的级别下调动作（P1→P2、P2→P3 等），保留入报告
- **fallback**：CLI 主路径失败后的回退动作（jdc → SDK；或时间窗 → 1d 聚合）

> 中文"降级"一词在本 Skill 内**只**用于"抑制降档 (demote)"语义；CLI/SDK 切换**不**使用"降级"。

## §1.3 联动验证

| 决策 | v0.3.0 落地 |
|---|:--:|
| B1=A 两段式降档 | ✅ R1 两段式已全局同步（`suppression-rules.md` §2.3/§3.4/§5/§6、`playbook-suppress.md` §1/§5） |
| B2=推荐 | ✅ R2 次/小时口径已在 `severity-matrix.md §1.1` + `core-concepts.md §1.4` 落地 |
| B3=A | ✅ R3 业务 tag 全局使用 `business=core/important/general/peripheral`（0 处旧 `business_criticality`） |
