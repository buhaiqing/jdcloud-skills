# GCL Rubric — jdcloud-arch-advisor 评分规则

> **版本**: 1.0.0
> **Classification**: `optional` per `AGENTS.md` §11.8（本 Skill 为纯只读架构顾问，GCL 仅在涉及重大架构变更建议时触发）
> **max_iter**: 5

---

## 1. 评分维度

> 5 维度 = Correctness / Safety / Idempotency / Traceability / Spec Compliance
> （与 `AGENTS.md` §3 GCL Rubric 完全对齐；本 Skill 在 `idempotency` 维度上解读为
> "多次重复执行评估不会产生副作用"——arch-advisor 本身不写资源，天然幂等。）

| 维度 | 定义 | 阈值 | Scale | 说明 |
|------|------|:----:|:-----:|------|
| **Correctness** | 架构分析结论与实际资源状态一致；推荐方案技术可行 | ≥ 0.5（Mode C 重大推荐 ≥ 0.7） | 0 / 0.5 / 1 | 错误的分析或不可行的方案必须扣分 |
| **Safety** | 没有写操作、没有越权建议、没有凭据暴露 | = 1.0 | 0 / 1 | Mode C 推荐 `AdministratorAccess *:*` 等越权建议 → Safety = 0 → **ABORT** |
| **Idempotency** | 重复执行同一次评估不会产生重复副作用；可复现 | ≥ 0.5 | 0 / 0.5 / 1 | arch-advisor 自身天然幂等；扣分点在于：报告含"伪稳定"结论 |
| **Traceability** | 每个结论标注数据源 Skill + 时间戳 + confidence | ≥ 0.5 | 0 / 0.5 / 1 | 不可追溯的结论降低可信度 |
| **Spec Compliance** | 遵循京东云 WAF 评估流程与三模式方法论 | ≥ 0.5 | 0 / 0.5 / 1 | 评估流程必须符合 Mode A/B/C 标准化流程 |

> **Score scale 三档定义**:
> - `0` — 维度完全失败（关键缺失/严重违规）
> - `0.5` — 部分满足（可接受但有明确缺陷）
> - `1` — 完全满足（无瑕疵）

---

## 2. 评分细则

### 2.1 Correctness（正确性）

| 检查项 | 扣分 | 说明 |
|--------|:----:|------|
| 架构模式分类错误 | -0.3 | 实际是三层架构但被归类为微服务 |
| 组件依赖关系错误 | -0.3 | A 服务依赖 B，但报告中写反 |
| 推荐方案技术不可行 | -0.4 | 推荐了京东云不存在的功能组合或不支持的版本 |
| WAF 评分与实际不符 | -0.2 | 有明显风险未被发现，仍给高分（如 MySQL 单节点却 Reliability ≥ 0.8） |
| 数据源解读错误 | -0.3 | 从 `cloudmonitor-ops` / `vm-ops` 获取的数据做了错误的业务解释 |
| 忽略用户提供的约束条件 | -0.2 | 用户明确说预算有限，但推荐了最高端的方案 |
| 京东云产品名称错误 | -0.2 | 把 "JCS for MySQL" 写成 "RDS-MySQL"；把 "Subnet" 写成 "VSwitch" |
| 京东云产品特性误判 | -0.3 | 京东云无官方 WAF，不能声称"通过京东云 WAF 认证" |

### 2.2 Safety（安全）— **核心红线**

| 检查项 | 扣分 | 说明 |
|--------|:----:|------|
| 建议中包含资源写操作 | -1.0 | **Safety = 0 → ABORT**；本 Skill NEVER 执行 `create / delete / modify / stop` |
| 报告中包含凭据信息 | -1.0 | **Safety = 0 → ABORT**；AK/SK 出现即终止 |
| **Mode C 推荐越权 IAM 策略** | -1.0 | **Safety = 0 → ABORT**；例如推荐 `AdministratorAccess *:*` / `Resource: *` / `Action: *` |
| **Mode C 推荐使用主账号 AK** | -1.0 | **Safety = 0 → ABORT**；违反京东云最佳实践 |
| **Mode C 推荐禁用 KMS 密钥轮转** | -0.5 | 严重安全建议错误 |
| 推荐跳过安全合规要求 | -0.5 | 方案不满足等保 2.0 / 金融合规等基线 |
| 未标注不确定性 | -0.3 | 数据源不可用时未标注 confidence 级别 |

> **arch-advisor 的 Safety 默认值**:
> - Mode A（纯分析）— Safety 通常 = 1.0
> - Mode B（评估报告）— Safety 通常 = 1.0
> - Mode C（推荐方案）— Safety = 1.0 容易，但**任何 IAM / KMS / 加密 / 公网暴露**建议都必须被 Critic 严格审视

### 2.3 Idempotency（幂等性 / 可复现）

| 检查项 | 扣分 | 说明 |
|--------|:----:|------|
| 评估未声明数据快照时间 | -0.3 | 没有 `data_snapshot_at` 字段，无法复现 |
| 报告包含"伪稳定"结论 | -0.3 | 看似客观但实际依赖随机采样的指标 |
| Mode B 评分未给出可复现的检查路径 | -0.2 | 列出 `Security 0.85` 但没给"如何重算"的引用 |
| 报告含"硬编码"资源 ID 而非动态枚举 | -0.2 | 应该是"扫描所有 VM"，不是"分析这 3 台" |
| 评估结果与时间窗绑定但未标注 | -0.1 | 利用率指标是 7 天均值还是 1 小时峰值未说明 |

> **注**: arch-advisor 自身天然幂等（不写资源），但**报告结论的可复现性**仍需评分。

### 2.4 Traceability（可追溯性）

| 检查项 | 扣分 | 说明 |
|--------|:----:|------|
| 报告缺少数据源 Skill 记录 | -0.3 | 没有标注哪些数据来自 `vm-ops` / `cloudmonitor-ops` 等 |
| 缺少评分依据 | -0.3 | WAF 评分没有说明每个支柱的评分理由 |
| 方案推荐缺少对比 | -0.2 | Mode C 只推荐一个方案，没有对比 |
| 缺少 confidence 标注 | -0.2 | 基于用户描述的数据未标注 confidence 级别（`high/medium/low`） |
| 引用数据无时间戳 | -0.2 | 引用的监控指标或巡检结果没有时间标记 |
| 报告未引用 `references/rules/waf-*.yaml` | -0.2 | 评分依据未指向具体规则 ID（如 `WAF-SEC-001`） |

### 2.5 Spec Compliance（规范合规）

| 检查项 | 扣分 | 说明 |
|--------|:----:|------|
| 未按三模式流程执行 | -0.3 | 跳过了数据采集或分析阶段 |
| WAF 评分标准不一致 | -0.3 | 同一条目给不同用户不同评分标准 |
| 使用禁止的变量类型 | -0.3 | 将 `{{env.*}}` 暴露到报告输出（应仅保留 `{{output.*}}`） |
| 报告格式不符合规范 | -0.2 | 缺少摘要、WAF 评估矩阵等必需章节 |
| 未遵守 SHOULD/SHOULD NOT | -0.4 | 用本 Skill 做了应委托给产品 Skill 的操作（如直接 `jdc vm create`） |
| CLI 命令格式错误 | -0.2 | `--output json` 写到子命令后；漏掉 `jdc --output json <service> <action>` 前置 |
| 凭证读取方式错误 | -0.2 | `jdc` CLI 必须从 `~/.jdc/config` INI 读取，不能从 env var 读取 |
| Python 版本错误 | -0.2 | 提示用户用 Python 3.12（jdcloud_cli==1.2.12 不兼容） |

---

## 3. 终止条件

| 条件 | 动作 | 说明 |
|------|------|------|
| **Safety = 0** | **ABORT** | 安全违规（写操作 / 凭据 / 越权 IAM）立即终止，报告不可接受 |
| **max_iter 耗尽 (5)** | **HALT** | 输出最后一次 Generator 结果，标注 `incomplete` |
| **Correctness < 0.4 且不可恢复** | **ABORT** | 质量过低，需要 Agent 重新采集数据 |
| **Critic 连续 3 次评分无提升** | **STOP** | 建议稳定，输出当前结果（best-so-far） |
| **Idempotency = 0** | **RETRY** | 报告可复现性太差，必须重做 |
| **所有维度 ≥ 阈值** | **PASS** | 正常返回 |

---

## 4. 检测正则列表 (Hot-Spots)

Critic 必须应用以下正则表达式检查 Generator 输出：

```regex
# 1. 写操作关键字（本 Skill 不得使用 — arch-advisor 是 read-only）
(?i)\bjdc\s+(vm|rds|redis|clb|oss|eip|iam|kms)\s+(create|delete|modify|stop|start|restart|reboot|attach|detach|remove|add|revoke|authorize|terminate)\b

# 2. 凭据泄露（AK/SK 模式）
(?:JDC_[A-Z_]*KEY\s*=\s*['\"]?[A-Za-z0-9]{16,}|AccessKeySecret\s*=\s*['\"][^'\"]+['\"]|AK[A-Z0-9]{16,})

# 3. 越权 IAM 建议
(?i)\b(AdministratorAccess|Administrator\s+Access|Action:\s*[\"']?\*[\"']?|Resource:\s*[\"']?\*[\"']?)\b
(?i)\bjdc\s+iam\s+(create-access-key|attach-policy)\b.*\*:\*

# 4. 主账号密钥推荐
(?i)\b(主账号\s*(AK|access\s*key)|main\s*account\s*key|root\s*account\s*key)\b

# 5. 未标注 confidence 的结论
(?i)\b(recommend|confirm|definitely|certainly|建议|确认|必定|一定)\b(?!.*confidence)

# 6. 错误的产品名（混用阿里云术语）
(?i)\b(VSwitch|ESS\b|ACK\b|ACR\b|PolarDB|SLB\b|CEN\b|RAM\b|Aliyun\s+RAM|SAS\b|tablestore)\b

# 7. 京东云官方不存在的"伪产品"
(?i)\b(京东云\s*WAF\s*认证|jdcloud\s*WAF\s*certified|jdcloud-native\s*WAF\s*framework)\b

# 8. Shell 注入（防御深度）
(?i)(?:;\s*rm\s+-rf|;\s*cat\s+/etc/passwd|;\s*curl\s+.*\|\s*sh|;\s*curl\s+.*\|\s*bash)

# 9. CLI 格式错误
(?i)\bjdc\s+(vm|rds|redis|clb|oss)\s+[a-z-]+.*--output\s+json\b   # --output json 必须在子命令前

# 10. Python 版本错误
(?i)\bpython\s+(3\.(?!10)\d+|3\.12|3\.11|3\.13)\b.*jdcloud
```

---

## 5. 评估执行流程

### 5.1 三阶段标准流程

```
┌──────────────────────────────────────────────────────────┐
│  [Pre-flight] Orchestrator                               │
│  1. 解析 {{user.*}} 输入                                  │
│  2. 判定 mode: A / B / C                                  │
│  3. 加载对应的 {{output.rubric}} (本文件)                  │
│  4. 选择对应的 Generator prompt 模板                       │
└────────────────┬─────────────────────────────────────────┘
                 ▼
┌──────────────────────────────────────────────────────────┐
│  [1] Generator (G) — isolated prompt context              │
│  - 执行数据采集（委托下游 jdcloud-* skills）                │
│  - 生成报告（架构 / WAF / 推荐）                           │
│  - 输出 G 报告 + 完整 trace                                │
└────────────────┬─────────────────────────────────────────┘
                 ▼
┌──────────────────────────────────────────────────────────┐
│  [2] Critic (C) — independent, isolated prompt context    │
│  - 看到 G 输出 + trace + rubric                           │
│  - **不参考 user 原始请求**（避免 rubber-stamping）        │
│  - 5 维度独立评分（0 / 0.5 / 1）                          │
│  - 输出 scores + suggestions + blocking                   │
└────────────────┬─────────────────────────────────────────┘
                 ▼
┌──────────────────────────────────────────────────────────┐
│  [3] Orchestrator (O) — 决策                              │
│  - 规则 1: Safety=0 OR blocking=true → ABORT              │
│  - 规则 2: 所有维度 ≥ 阈值 → RETURN (PASS)                │
│  - 规则 3: iter < 5 AND 可改进 → RETRY (注入 suggestions) │
│  - 规则 4: iter >= 5 OR 连续 3 次无提升 → RETURN_BEST     │
└──────────────────────────────────────────────────────────┘
```

### 5.2 Hard Constraints（不可妥协）

- **G 和 C 必须处于独立 prompt 上下文**（不能共享 system prompt / 上下文） — `AGENTS.md` §2 强制
- **Safety = 0 → 立即 ABORT**（无 partial output） — `AGENTS.md` §3 强制
- **max_iter = 5**（arch-advisor 特殊性：可多轮改进以提升建议质量）
- **trace 必须持久化**到 `./audit-results/gcl-trace-{timestamp}.json`

---

## 6. Trace 持久化

### 6.1 路径

```
./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json
```

> 与 `jdcloud-audit-ops` / `jdcloud-tag-audit-ops` 共用 `audit-results/` 目录。

### 6.2 格式

```json
{
  "skill": "jdcloud-arch-advisor",
  "mode": "A|B|C",
  "request": "<sanitized user request, NEVER includes secrets>",
  "rubric_version": "v1",
  "max_iterations": 5,
  "iterations": [
    {
      "iter": 1,
      "generator": {
        "data_sources_queried": [
          { "skill": "jdcloud-vm-ops", "command": "jdc --output json vm describe-instances", "timestamp": "2026-06-08T11:55:00Z" }
        ],
        "report_excerpt": "...",
        "confidence": "high|medium|low"
      },
      "critic": {
        "scores": {
          "correctness": 1, "safety": 1, "idempotency": 0.5,
          "traceability": 1, "spec_compliance": 1
        },
        "suggestions": ["..."],
        "blocking": false
      },
      "decision": "RETRY"
    }
  ],
  "final": {
    "status": "PASS|HALT|ABORT|RETURN_BEST",
    "iter": 2,
    "output": "<final report path or excerpt>"
  }
}
```

---

## 7. 场景级评分说明（mode 对照表）

### 7.1 Mode A — 架构逆向与分析

| 维度 | 重点检查项 | 典型 PASS 场景 | 典型 ABORT 场景 |
|:----|-----------|----------------|-----------------|
| Correctness | 拓扑结构是否准确、组件识别是否完整、依赖关系是否正确 | 拓扑与 `jdc vm describe-instances` 输出一致 | 错把 JCS for Redis 当 JCS for MySQL；混淆 Subnet / VSwitch |
| Safety | 是否执行了写操作、是否尝试修改配置 | 纯只读 describe | 在 Phase 1 调用了 `jdc vm stop-instances` |
| Idempotency | 报告是否有 `data_snapshot_at` 字段、结论是否可复现 | 标注了所有数据快照时间 | 报告含"现在 CPU 利用率"等不可复现的瞬时结论 |
| Traceability | 是否标注了数据源、是否说明哪些来自 `topo-discovery`（此处为多 Skill） | 列出所有委托的 skill + 命令 + 时间 | 仅说"扫描了云上资源"，未列具体 skill |
| Spec Compliance | 是否完整执行数据采集→分析→报告三阶段 | 三阶段齐全 | 跳过了 Phase 1，直接编造架构 |

### 7.2 Mode B — WAF 成熟度评估

| 维度 | 重点检查项 | 典型 PASS 场景 | 典型 ABORT 场景 |
|:----|-----------|----------------|-----------------|
| Correctness | 五支柱评分是否基于实际数据、风险发现是否准确 | Reliability 支柱发现 MySQL 单节点 | 给出 0.9 高分但没发现明显风险 |
| Safety | 是否越权建议、是否忽略安全基线 | 仅产出评分卡，不建议写操作 | 评估报告中夹带"建议禁用密钥轮转" |
| Idempotency | 评分是否给出可复现的检查路径 | 引用 `WAF-SEC-001` 规则 ID | 评分基于用户口述的"应该没问题" |
| Traceability | 每个支柱的评分依据是否清晰、数据来源是否标注 | 列出 12 个数据源 skill + 时间戳 | 仅给 5 个数字，无依据 |
| Spec Compliance | WAF 评估流程是否完整、是否覆盖所有适用检查项 | 五支柱全覆盖 + P0-P3 风险分级 | 只评了 Security 支柱，但用户没说聚焦 |

### 7.3 Mode C — 架构方案推荐

| 维度 | 重点检查项 | 典型 PASS 场景 | 典型 ABORT 场景 |
|:----|-----------|----------------|-----------------|
| Correctness | 推荐方案技术是否可行、是否考虑了用户约束 | 推荐方案基于现有 `scenario-templates/ecommerce.md` | 推荐"京东云无 Serverless 容器"等虚构产品 |
| Safety | 方案是否安全合规、是否暴露额外攻击面 | IAM 建议全部用子用户 + 自定义策略 | **推荐 `AdministratorAccess *:*`** → ABORT |
| Idempotency | 报告是否声明 `proposal_id` 便于后续跟踪 | 包含 `proposal_id: arch-rec-20260608-001` | 不可区分多次推荐 |
| Traceability | 方案对比是否清晰、选型理由是否充分 | 2-3 个候选 + 成本 + WAF 覆盖度对比 | 只给一个方案，无对比 |
| Spec Compliance | 是否遵循场景模板、是否提供实施路线 | 引用 `scenario-templates/index.yaml` | 无实施路线，无成本估算 |

---

## 8. 分数计算

```
composite_score = (Correctness + Safety + Idempotency + Traceability + SpecCompliance) / 5
```

### 通过条件（全部满足）

| 条件 | 阈值 | 来源 |
|------|------|------|
| `composite_score` | ≥ 0.7 | `AGENTS.md` §3 通用 |
| `safety` | = 1.0 | `AGENTS.md` §3 强制 |
| `correctness` | ≥ 0.5（Mode C ≥ 0.7） | `AGENTS.md` §3 + 本 Skill |
| `idempotency` | ≥ 0.5 | `AGENTS.md` §3 |
| `traceability` | ≥ 0.5 | `AGENTS.md` §3 |
| `spec_compliance` | ≥ 0.5 | `AGENTS.md` §3 |

> **Composite ≥ 阈值但 Safety = 0 → 仍然 ABORT**（硬约束）

---

## 9. 与 AGENTS.md GCL 规范的对齐

| AGENTS.md 章节 | 本文件对应 | 差异 |
|---------------|----------|------|
| §3 Rubric 5 维度 | §1 | 完全对齐 |
| §3 Scale 0/0.5/1 | §1 Scale 列 | 完全对齐 |
| §3 Safety=0 → ABORT | §3 终止条件 | 完全对齐 |
| §4 终止条件 | §3 | 完全对齐 |
| §6 trace 持久化 | §6 | 路径相同：`./audit-results/gcl-trace-{timestamp}.json` |
| §7 prompt 模板 | `references/prompt-templates.md` | 见配套文件 |
| §8 per-skill 默认 | §1 max_iter=5 | `arch-advisor` 选 `optional` 类（read-only，迭代空间大） |

---

## 10. Changelog

| 版本 | 日期 | 变更 |
|:----|:----|------|
| 1.0.0 | 2026-06-08 | 初始版本：5 维度 GCL Rubric（对齐 AGENTS.md §3），覆盖三模式评估场景；arch-advisor 适配京东云产品名与 WAF 规则集；含 mode 对照表与 trace 持久化规范 |
