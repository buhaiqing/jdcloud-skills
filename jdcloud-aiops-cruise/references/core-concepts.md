# Core Concepts — jdcloud-aiops-cruise

> 本文定义 `jdcloud-aiops-cruise` Skill 所依赖的核心概念。
> 所有术语、模型和约束在本 skill范围内必须保持一致。

##1. Skill定位

`jdcloud-aiops-cruise` 是**全链路、跨产品、只读**的 AIOps巡检 Skill。它的边界严格遵守以下三条：

1. **全链路（End-to-End）** —一次巡检必须覆盖入口 → 分发 → 计算 → 数据 → 出网的整条链路，而不是单一产品。
2. **跨产品（Cross-Product）** — 同时覆盖 EIP / CLB / VM / K8s / Redis / RDS MySQL / RDS PostgreSQL / NAT / ES / 安全组等多个 JD Cloud 产品。
3. **只读（Read-Only）** — 本 skill **不执行任何资源变更**。所有"修复"动作必须由人工确认后委托给对应的 `jdcloud-*-ops` skill。

> ⚠️ **本 skill唯一的对外输出是"建议"（Recommendation）**，不是"动作"（Action）。即使建议中明确写了"应升级到 XX规格"，执行入口永远是 `jdcloud-vm-ops` / `jdcloud-clb-ops` 等。

---

##2. AIOps 三阶段模型

`jdcloud-aiops-cruise`严格遵守 **Perceive → Reason → Execute** 三阶段模型，对应到目录结构：

|阶段 |目录 |核心脚本 | 输入 | 输出 |
|---|---|---|---|---|
| **Perceive（感知）** | `scripts/01-perceive/` | `cruise_sniff.py` |客户标签、区域范围 |拓扑初判报告（JSON） |
| **Reason（推理）** | `scripts/02-reason/` | `cruise_analyze.py` + `analyzers/*` | Phase1拓扑 +监控指标 |深度巡检报告（findings） |
| **Execute（执行）** | `scripts/03-execute/` | （空，仅 README） | Phase2 findings | Action建议（供人工确认） |

###2.1路径约定（强制）

所有 `01-perceive/` 和 `02-reason/` 子目录中的脚本必须显式 `sys.path.insert(0, <scripts 项目根>)`：

```python
# 在01-perceive/ 或02-reason/ 子目录中的脚本
_scripts_dir = os.path.dirname(os.path.abspath(__file__))
_project_dir = os.path.join(_scripts_dir, "..") #指向 scripts/
sys.path.insert(0, _project_dir)
from lib.jdc_client import JdcClient
```

`analyzers/*` 子目录中的脚本则需要向上两级到 `scripts/`：

```python
# 在 analyzers/ 子目录中的脚本（位于 scripts/02-reason/analyzers/）
_scripts_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _scripts_dir not in sys.path:
 sys.path.insert(0, _scripts_dir)
from lib.jdc_client import tag_dict, get_tag
```

> 这条路径约定来自仓库根 `AGENTS.md`，任何不符合的脚本在 GCL阶段会被判定为 **Spec Compliance <0.5**。

###2.2 三阶段职责（不可越界）

|维度 | Perceive | Reason | Execute（本 skill 内） |
|---|---|---|---|
|写资源 | ❌ | ❌ | ❌ |
| 调用监控 API | ✅（只读） | ✅（只读） | ❌ |
| 生成 Action建议 | ❌ | ❌ | ✅（建议，非执行） |
| 修改客户资源 | ❌ | ❌ | ❌ |
|触发 ops skill | ❌ | ❌ | ❌（必须人工确认） |

---

##3.关键术语

|术语 | 定义 |
|---|---|
| **客户标签（Customer Tag）** |京东云资源上的 `客户=<客户名>`标签，是巡检的唯一筛选依据；缺此标签的资源不进入本次巡检范围 |
| **部署模式（Deployment Mode）** | 由 `analyzer`推断：`k8s`（带 K8s标签）、`traditional`（仅有客户标签）、`unknown`（无标识） |
| **置信度（Confidence）** |部署模式推断的置信度（0~1）；`>0.8` 自动继续，`<=0.8` 进入 `needs_confirmation`等待人工 |
| **Finding** | 单条巡检发现，结构见 `BaseAnalyzer._add_finding` |
| **Severity** |严重度：`critical`（🔴）/ `warning`（🟡）/ `info`（🔵） |
| **Ops Skill** |委托入口：`jdcloud-vm-ops` / `jdcloud-redis-ops` / `jdcloud-mysql-ops` 等 |
| **水线（Water Level）** |资源使用率 /规格上限（0~1），用于容量评估 |
| **嗅探（Sniff）** | Phase1 的资源发现 +拓扑构建，等价于英文 "discover" |
| **巡航（Cruise）** |完整的两阶段巡检流程（Sniff + Analyze） |
| **安全门（Safety Gate）** | GCL 中 `Safety =1` 必须无条件成立；为 `0` 直接 ABORT |

---

##4.标签约定（强制）

###4.1客户标签

- **键**: `客户`
- **值**:客户名（如 `烟台振华`、`某某电商`）
- **必需**:客户名下所有被巡检资源必须打此标签
- **缺失**:资源会被分到 `needs_confirmation`（置信度 ≤0.8）等待人工确认

###4.2 K8s标签（自动识别）

- **键**: `kubernetes.jdcloud.com/cluster_id`（节点 / Pod所属集群）
- **键**: `kubernetes.jdcloud.com/node_group_id`（节点所属节点组）
- **键**: `kubernetes.jdcloud.com/created_by`（集群自建的资源标识）
- **作用**:出现任意一个即判定为 `k8s`部署模式，置信度0.95

###4.3其它标签（可选）

- `环境=production` / `环境=staging` / `环境=test`：影响 analyzer 的严重度判定
- `应用=订单服务` / `应用=ERP`：用于跨资源关联
- `负责人=张三`：用于闭环工单派发

---

##5. Finding 数据结构（强制）

所有 analyzer 必须输出符合 `BaseAnalyzer._add_finding()`签名的 finding dict：

```python
{
 "severity": "critical" | "warning" | "info", #必填
 "resource": "<resource_name>", #资源名
 "resource_id": "<jdcloud_resource_id>", # JD Cloud资源 ID
 "resource_ip": "<internal_ip>", # 内网 IP（VM/Redis/RDS）
 "instance_type": "<vm_instance_type_or_redis_spec>", #规格
 "message": "<human_readable_description>", #必填，给运维看的中文
 "action": "<step1; step2; step3>", # 操作步骤（分号分隔）
 "ops_skill": "jdcloud-vm-ops", #委托入口 skill
}
```

> **绝不允许** finding缺 `severity` / `message`；缺 `resource` / `resource_id`会在 GCL 的 `Traceability`维度扣分。

---

##6.部署模式分类规则

`resource_discovery._classify()` 的判定逻辑（必须严格遵守）：

|优先级 |判定条件 |模式 |置信度 |
|---|---|---|---|
|1 |资源有 `kubernetes.jdcloud.com/cluster_id` 或 `kubernetes.jdcloud.com/created_by`标签 | `k8s` |0.95 |
|2 |资源有 `客户`标签（无 K8s标签） | `traditional` |0.85 |
|3 |资源名匹配客户名前缀（如 `yhzh-*`） | `traditional` |0.60 |
|4 |完全没有标识 | `unknown` |0.30 |

>任何对分类规则的修改必须同步更新 `references/threshold-definitions.md` 与 runbook 的 `confidence_rules`段。

---

##7. 安全与合规边界

###7.1 只读边界

`jdcloud-aiops-cruise`严禁执行以下操作（任何违规 → Safety =0 → GCL ABORT）：

|禁止动作 |委托入口 |
|---|---|
|任何资源的删除 /释放 | `jdcloud-vm-ops` / `jdcloud-clb-ops` / `jdcloud-eip-ops` / ... |
|任何资源的停止 /关机 | `jdcloud-vm-ops` / `jdcloud-redis-ops` / `jdcloud-mysql-ops` |
|任何资源的规格变更 /升配 /降配 | `jdcloud-vm-ops` / `jdcloud-clb-ops` |
|任何资源的绑定 / 解绑 /调整带宽 | `jdcloud-eip-ops` / `jdcloud-nat-ops` |
|任何 DDL（CREATE INDEX / DROP / VACUUM FULL） | `jdcloud-mysql-ops` / `jdcloud-postgresql-ops` |
|任何告警规则的修改 / 删除 | `jdcloud-cloudmonitor-ops` |

###7.2 数据最小化

`resource_discovery.discover_customer_resources()` 必须遵守：

- **入站**：扫描所有区域所有资源（必须 list区域资源才能过滤）
- **出站 /落盘**：仅保留带 `客户`标签的资源 +客户资源关联的 VPC / 子网 / 安全组
- **绝不允许**：返回或持久化跨客户 / 全账号的原始资源清单

###7.3凭证处理

- **来源**：`JDC_ACCESS_KEY` / `JDC_SECRET_KEY` 环境变量 或 `.env` 文件
- **绝不允许**：在 stdout /报告 JSON /错误日志中打印完整 `SECRET_KEY`
- **日志中**：`SECRET_KEY`状态检查只能用 `test -n "$VAR"`（存在性），或显示 `<masked>`

---

##8. 与其它 skill 的协作边界

| Skill |协作模式 |
|---|---|
| `jdcloud-vm-ops` | **下游执行** — VM升配 /改规格 / 重启 /替换云盘 |
| `jdcloud-clb-ops` | **下游执行** — CLB升配 /改监听器 / 注册摘除后端 |
| `jdcloud-eip-ops` | **下游执行** — EIP释放 /绑定解绑 /调带宽 |
| `jdcloud-redis-ops` | **下游执行** — Redis升配 / 清 key /改参数 |
| `jdcloud-mysql-ops` | **下游执行** —慢查询分析 /索引 DDL / 参数调整 |
| `jdcloud-postgresql-ops` | **下游执行** —慢查询分析 / VACUUM / 参数调整 |
| `jdcloud-cloudmonitor-ops` | **依赖** —告警规则配置、监控指标阈值 |
| `jdcloud-vpc-ops` | **依赖** — 安全组规则审计（`sg_analyzer`） |
| `jdcloud-nat-ops` | **下游执行** — NAT 网关升配 /改规则 |
| `jdcloud-iam-ops` | **依赖** —凭证权限检查（只读列表类） |

> 本 skill严禁直接调用上述 skill 的"写"接口；所有调用必须通过人工确认。

---

##9. 版本演进策略

- **SemVer**：主版本 = 不兼容的目录结构或数据契约变更；次版本 = 新增 analyzer / runbook；修订版本 =阈值 /文档修订。
- **Changelog**：所有 `SKILL.md` 版本变更必须在文末 Changelog 表追加一行（日期 +变更摘要）。
- **废弃流程**：任何 analyzer 被新 analyzer替代时，旧 analyzer保留1 个版本周期（"deprecated"标记），下一个版本删除。
