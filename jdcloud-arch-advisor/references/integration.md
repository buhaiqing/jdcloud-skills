# Integration —架构评审 Skill集成指南（京东云版）

> 定义 `jdcloud-arch-advisor` 如何与下游13+ 数据源 Skill集成、委托协议、输出格式约定、跨账户/限流策略。
>
> 本 Skill 是**只读顾问**，不直接调用任何写 API。所有数据通过委托下游 Skill 获取。

---

##1.集成架构总览

```
 ┌─────────────────────────────┐
 │ jdcloud-arch-advisor │
 │ (咨询层 / read-only) │
 └──────────────┬──────────────┘
 │ delegation (并行)
 ┌──────────────┬───────────┼────────────┬──────────────┐
 ▼ ▼ ▼ ▼ ▼
 vm/mysql/ redis/es clb/eip/ iam/kms/ monitor/
 postgres/ cluster vpc audit/tag billing
 mongodb ◀────────────资源清单 +拓扑/策略 +指标 ──────▶
 │
 ▼
 ┌────────────────────┐
 │ WAF评分卡 +报告 │
 │ (Markdown + JSON) │
 └────────────────────┘
```

###1.1 三模式数据流

|模式 | 输入 |委托调用 | 输出 |
|:----:|------|---------|------|
| **Mode A**架构逆向 | 用户描述的现有系统 | vm-ops / mysql-ops / redis-ops / clb-ops / eip-ops / vpc-ops / topo-discovery |架构拓扑 JSON + Markdown |
| **Mode B** WAF评估 |资源 ID列表 / 全量 | + cloudmonitor-ops (指标) + iam-ops + kms-ops + audit-ops + tag-audit-ops | 五支柱评分卡 +风险发现 |
| **Mode C**方案推荐 | 用户需求 +约束 | (无运行时委托) +加载 `references/scenario-templates/`模板 | 推荐方案 +成本估算 |

---

##2. 环境变量与凭证

###2.1 `{{env.*}}`变量约定

|变量 |必填 | 默认值 | 来源 | 说明 |
|------|:----:|:------:|------|------|
| `{{env.JDC_ACCESS_KEY}}` | 是 | — |运行时 | AccessKey ID，**NEVER ask user**，HALT if unset |
| `{{env.JDC_SECRET_KEY}}` | 是 | — |运行时 | SecretKey，**NEVER ask user / NEVER log** |
| `{{env.JDC_REGION}}` | 是 | `cn-north-1` |运行时 | 默认地域；分析时按资源实际地域切换 |
| `{{env.JDC_SKILLS_ROOT}}` | 否 | 自动检测 |运行时 | Skill仓库根路径，定位 `scenario-templates/` 等资源 |

###2.2 CLI vs SDK凭证（关键陷阱）

| 调用模式 |凭证来源 | 配置方法 |
|---------|---------|---------|
| `jdc --output json <product> <cmd>` (CLI) | `~/.jdc/config` **INI 文件** | 必须写入 INI；**env vars会被忽略** |
| `jdcloud_sdk` Python (SDK fallback) | `JDC_ACCESS_KEY` / `JDC_SECRET_KEY` env vars | Agent runtime 自动注入 |

```bash
# CLI凭证初始化（jdc 不读 env vars，必须写 INI）
export HOME=/tmp/jdc-home #沙箱可写
mkdir -p /tmp/jdc-home/.jdc
cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = {{env.JDC_ACCESS_KEY}}
secret_key = {{env.JDC_SECRET_KEY}}
region_id = cn-north-1
endpoint = vm.jdcloud-api.com
scheme = https
timeout =20
CONFIGEOF
printf "%s" "default" > /tmp/jdc-home/.jdc/current # 注意：无换行
```

> **关键**: `printf` 不能用 `echo`（会带换行符）；CLI 不支持 `--no-interactive`，全部非交互。

---

##3. 数据源依赖表（13+ 下游 Skill）

###3.1 主表：委托能力 → 下游 Skill →关键 API

|委托能力 | 下游 Skill | jdc 子命令 / OpenAPI |关键 JSON路径 | GCL分类 |降级策略 |
|---------|-----------|---------------------|---------------|:--------:|---------|
| VM 实例清单 +规格 | `jdcloud-vm-ops` | `jdc --output json vm describe-instances` | `$.result.instances` | required | 用户描述 + low confidence |
| VM 实例类型规格表 | `jdcloud-vm-ops` | `jdc --output json vm describe-instance-types` | `$.result.instanceTypes` | required |跳过规格匹配评分 |
| MySQL 实例清单 | `jdcloud-mysql-ops` | `jdc --output json rds describe-database-instances` | `$.result.databaseInstances` | required | 用户描述 + low confidence |
| PostgreSQL 实例清单 | `jdcloud-postgresql-ops` | `jdc --output json rds describe-postgresql-instances` | `$.result.postgresqlInstances` | required | 用户描述 + low confidence |
| MongoDB 实例清单 | `jdcloud-mongodb-ops` | `jdc --output json mongodb describe-db-instances` | `$.result.dbInstances` | required | 用户描述 + low confidence |
| Redis 实例清单 | `jdcloud-redis-ops` | `jdc --output json cache describe-cache-instances` | `$.result.cacheInstances` | required | 用户描述 + low confidence |
| Elasticsearch 实例清单 | `jdcloud-elasticsearch-ops` | `jdc --output json es describe-instances` | `$.result.instances` | required | 用户描述 + low confidence |
| CLB负载均衡清单 | `jdcloud-clb-ops` | `jdc --output json lb describe-load-balancers` | `$.result.loadBalancers` | required | 用户描述 + low confidence |
| CLB监听器 | `jdcloud-clb-ops` | `jdc --output json lb describe-listener` | `$.result.listener` | required |跳过监听器健康检查 |
| EIP弹性公网 IP | `jdcloud-eip-ops` | `jdc --output json vpc describe-elastic-ips` | `$.result.elasticIps` | required | 用户描述 + low confidence |
| VPC列表 | `jdcloud-vpc-ops` (本次创建) | `jdc --output json vpc describe-vpcs` | `$.result.vpcs` | required | 用户描述 + low confidence |
| Subnet 子网 | `jdcloud-vpc-ops` (本次创建) | `jdc --output json vpc describe-subnets` | `$.result.subnets` | required | 用户描述 + low confidence |
| 安全组 | `jdcloud-vpc-ops` (本次创建) | `jdc --output json vpc describe-security-groups` | `$.result.securityGroups` | required | 用户描述 + low confidence |
| IAM 子用户 | `jdcloud-iam-ops` | `jdc --output json iam list-sub-users` | `$.result.subUsers` | required |跳过 Security支柱 IAM 检查 |
| IAM策略列表 | `jdcloud-iam-ops` | `jdc --output json iam list-policies` | `$.result.policies` | required |跳过策略合规检查 |
| KMS密钥 | `jdcloud-kms-ops` | `jdc --output json kms list-keys` | `$.result.keys` | required |跳过 Security支柱加密检查 |
| 操作审计跟踪 | `jdcloud-audit-ops` | `jdc --output json actiontrail describe-trails` | `$.result.trailList` | required |跳过 Security审计检查 |
|监控指标 | `jdcloud-cloudmonitor-ops` | `jdc --output json monitor get-metric-data` | `$.result.metricDataList` | recommended |跳过 Performance量化评分 |
|资源标签 | `jdcloud-tag-audit-ops` | `jdc --output json tag list-tagged-resources` | `$.result.resources` | recommended |跳过 Efficiency标签治理评分 |
|告警事件分析 | `jdcloud-alert-intelligence` | (read-only) | `$.result.events` | optional |跳过告警关联分析 |
|资源拓扑 | `jdcloud-topo-discovery` (本次创建) | (read-only聚合) | `$.result.topology` | recommended | 用户自行描述 + low confidence |

###3.2缺失 Skill列表（WAF 检查时标 `manual check`）

下表中的 Skill 当前**仓库中未提供**，在 WAF评估时，相关检查项必须标注 `manual_check: true` 并说明需要人工核查：

|缺失 Skill | 受影响的 WAF 检查 |替代方案 |
|----------|-----------------|---------|
| `jdcloud-nat-ops` | Reliability: NAT Gateway 高可用 / Cost: NAT闲置 |人工登录控制台或 OpenAPI `DescribeNatGateways` |
| `jdcloud-oss-ops` | Cost: OSS存储桶生命周期 / Security: OSS访问日志 |人工登录 OSS 控制台 |
| `jdcloud-cdn-ops` | Performance: CDN命中率 / Cost: CDN流量 |人工登录 CDN 控制台 |
| `jdcloud-kubernetes-ops` | Reliability: JCS K8s 多 AZ / Cost:节点池利用率 | `jdc kubernetes describe-clusters`（如有） |
| `jdcloud-jcq-ops` | Reliability: JCQ 高可用 / Cost: JCQ消息堆积 |人工登录控制台 |
| `jdcloud-billing-ops` | Cost:资源成本账单量化分析 |京东云费用中心控制台 |
| `jdcloud-auto-scaling-orch` | Efficiency: 自动伸缩 / Cost:弹性策略 |人工登录控制台 |

###3.3 数据采集并行模式

```
[arch-advisor] data_collection_phase
 │
 ├── fan-out (parallel) ────────────────────────┐
 │ ├── jdcloud-vm-ops (5s timeout) │
 │ ├── jdcloud-mysql-ops (5s timeout) │
 │ ├── jdcloud-redis-ops (5s timeout) │
 │ ├── jdcloud-clb-ops (5s timeout) │
 │ ├── jdcloud-eip-ops (5s timeout) │
 │ ├── jdcloud-vpc-ops (5s timeout) │
 │ ├── jdcloud-iam-ops (5s timeout) │
 │ └── jdcloud-cloudmonitor-ops (10s) │
 │ │
 └── fan-in → merge results →评分卡输入 │
 ▼
 {"resources": [...], "metrics": [...]}
```

> 并行调用时，每个下游 Skill 必须独立失败（不影响整体报告生成）。失败的 Skill 在报告 `limitations`字段中标注。

---

##4.委托协议详细说明

###4.1 `jdcloud-vm-ops`委托协议

| 操作 |传递参数 |预期返回 |
|------|---------|---------|
|资源清单 | `regionId, pageNumber, pageSize, filters` | `{instances: [{instanceId, name, status, instanceType, primaryNetworkInterface, ...}]}` |
|规格匹配 | `instanceType` | `{instanceTypes: [{instanceType, cpu, memoryGB, ...}]}` |
|状态详情 | `instanceId` | 单实例完整字段 |

**JSON路径参考**:
```bash
jdc --output json vm describe-instances --region-id cn-north-1 --page-size50
# $.result.instances[].instanceId
# $.result.instances[].instanceType
# $.result.instances[].status
# $.result.instances[].primaryNetworkInterface.subnetId
# $.result.instances[].primaryNetworkInterface.securityGroupIds[]
```

###4.2 `jdcloud-mysql-ops`委托协议

```bash
jdc --output json rds describe-database-instances --region-id cn-north-1
# $.result.databaseInstances[].instanceId
# $.result.databaseInstances[].engineVersion
# $.result.databaseInstances[].instanceClass
# $.result.databaseInstances[].instanceType (Master/Slave)
```

> **关键差异（vs阿里云 RDS）**:阿里云返回 `$.Databases.DBInstance[]`，京东云返回 `$.result.databaseInstances[]`（小写、无复数）。

###4.3 `jdcloud-clb-ops`委托协议

```bash
jdc --output json lb describe-load-balancers --region-id cn-north-1
# $.result.loadBalancers[].loadBalancerId
# $.result.loadBalancers[].loadBalancerName
# $.result.loadBalancers[].loadBalancerType (network/application)
# $.result.loadBalancers[].listeners (需 describe-listener)
```

###4.4 `jdcloud-iam-ops`委托协议

```bash
jdc --output json iam list-sub-users --page-number1 --page-size100
# $.result.subUsers[].subUserId
# $.result.subUsers[].subUserName
# $.result.subUsers[].mfaBindRequired (布尔值,用于 WAF-SEC-001 检查)
# $.result.subUsers[].accessKeyLastUsed

jdc --output json iam list-policies
# $.result.policies[].policyName
# $.result.policies[].policyType (Custom/System)
```

###4.5 `jdcloud-cloudmonitor-ops`委托协议

```bash
jdc --output json monitor get-metric-data \
 --namespace "vm" \
 --metric-name "vm.cpu.util" \
 --resource-id "i-xxxxx" \
 --start-time "2026-06-07T00:00:00Z" \
 --end-time "2026-06-08T00:00:00Z" \
 --aggr-type "avg"
# $.result.metricDataList[].dataPoints[]
```

###4.6 `jdcloud-audit-ops`委托协议

```bash
jdc --output json actiontrail describe-trails --region-id cn-north-1
# $.result.trailList[].trailId
# $.result.trailList[].trailName
# $.result.trailList[].status (Enabled/Disabled) — 用于 WAF-SEC-003
```

###4.7 `jdcloud-vpc-ops`委托协议（本次创建的 Skill）

```bash
jdc --output json vpc describe-vpcs --region-id cn-north-1
# $.result.vpcs[].vpcId
# $.result.vpcs[].vpcName
# $.result.vpcs[].cidrBlock

jdc --output json vpc describe-subnets --region-id cn-north-1 --vpc-id vpc-xxxxx
# $.result.subnets[].subnetId
# $.result.subnets[].subnetName
# $.result.subnets[].cidrBlock
# $.result.subnets[].az
# $.result.subnets[].availableIpCount

jdc --output json vpc describe-security-groups --region-id cn-north-1 --vpc-id vpc-xxxxx
# $.result.securityGroups[].securityGroupId
# $.result.securityGroups[].securityGroupName
# $.result.securityGroups[].rules (嵌套)

jdc --output json vpc describe-security-group --region-id cn-north-1 --security-group-id sg-xxxxx
# $.result.securityGroup.rules[].direction (ingress/egress)
# $.result.securityGroup.rules[].protocol
# $.result.securityGroup.rules[].fromPort / toPort
# $.result.securityGroup.rules[].addressPrefix
```

###4.8 `jdcloud-topo-discovery`委托协议（本次创建的聚合 Skill）

| 操作 |传递参数 |预期返回 |
|------|---------|---------|
| 获取全量资源拓扑 | `regionId` | `{topology: {nodes: [...], edges: [...]}}` |
| 获取资源依赖 | `resourceIds[]` | `{dependencies: [{from, to, type}]}` |
| 获取网络拓扑 | `vpcId` | `{vpc, subnets, routeTables, natGateways, eips}` |

> **关键差异（vs阿里云）**:京东云**没有原生 `topo-discovery` Skill**，需要本次创建的 `jdcloud-topo-discovery` 通过聚合其他 Skill 的输出来模拟。

---

##5. 输出格式契约

###5.1架构拓扑 JSON（Mode A / Mode C）

```json
{
 "report_id": "arch-20260608-001",
 "mode": "A",
 "cloud": "jdcloud",
 "generated_at": "2026-06-08T12:00:00Z",
 "data_sources": [
 { "skill": "jdcloud-vm-ops", "timestamp": "2026-06-08T11:55:00Z", "status": "success", "request_id": "req-vm-001" },
 { "skill": "jdcloud-mysql-ops", "timestamp": "2026-06-08T11:56:00Z", "status": "success", "request_id": "req-mysql-001" },
 { "skill": "jdcloud-clb-ops", "timestamp": "2026-06-08T11:57:00Z", "status": "success", "request_id": "req-clb-001" },
 { "skill": "jdcloud-iam-ops", "timestamp": "2026-06-08T11:58:00Z", "status": "success", "request_id": "req-iam-001" }
 ],
 "topology": {
 "pattern": "three-tier",
 "layers": [
 {
 "name": "presentation",
 "components": [
 { "type": "CLB", "id": "lb-xxxxx", "region": "cn-north-1", "properties": { "listeners":2, "backendInstances":4 } }
 ]
 },
 {
 "name": "application",
 "components": [
 { "type": "VM", "id": "i-aaaa", "region": "cn-north-1", "properties": { "spec": "g.n2.medium", "az": "cn-north-1a", "status": "running" } },
 { "type": "VM", "id": "i-bbbb", "region": "cn-north-1", "properties": { "spec": "g.n2.medium", "az": "cn-north-1b", "status": "running" } }
 ]
 },
 {
 "name": "data",
 "components": [
 { "type": "JCS_MySQL", "id": "mysql-xxxxx", "region": "cn-north-1", "properties": { "engine": "MySQL8.0", "spec": "m.n2.medium", "ha": true } },
 { "type": "JCS_Redis", "id": "redis-xxxxx", "region": "cn-north-1", "properties": { "version": "6.0", "spec": "r.s1.small", "ha": true } }
 ]
 }
 ],
 "dependencies": [
 { "from": "lb-xxxxx", "to": "i-aaaa", "type": "http" },
 { "from": "lb-xxxxx", "to": "i-bbbb", "type": "http" },
 { "from": "i-aaaa", "to": "mysql-xxxxx", "type": "jdbc" },
 { "from": "i-aaaa", "to": "redis-xxxxx", "type": "redis" }
 ]
 }
}
```

###5.2 WAF评分 JSON（Mode B）

```json
{
 "report_id": "waf-20260608-001",
 "mode": "B",
 "cloud": "jdcloud",
 "generated_at": "2026-06-08T12:00:00Z",
 "composite_score":0.71,
 "waf_scores": {
 "security": { "score":0.85, "checks_passed":12, "checks_total":15, "findings":3, "manual_checks":1 },
 "reliability": { "score":0.70, "checks_passed":7, "checks_total":10, "findings":3, "manual_checks":2 },
 "performance": { "score":0.60, "checks_passed":6, "checks_total":10, "findings":4, "manual_checks":1 },
 "cost": { "score":0.75, "checks_passed":9, "checks_total":12, "findings":3, "manual_checks":4 },
 "efficiency": { "score":0.65, "checks_passed":5, "checks_total":8, "findings":3, "manual_checks":0 }
 },
 "findings": [
 {
 "id": "F-SEC-001",
 "priority": "P0",
 "pillar": "security",
 "rule_id": "WAF-SEC-004",
 "title": "VM 安全组 SSH端口暴露到公网",
 "detail": "安全组 sg-xxxxx 入方向规则允许0.0.0.0/0访问 TCP22端口",
 "data_source": "jdcloud-vpc-ops (securityGroup.rules)",
 "recommendation": "限制 SSH访问源 IP 为管理网段（如10.0.0.0/8）",
 "effort": "low",
 "impact": "security",
 "manual_check": false
 },
 {
 "id": "F-COST-005",
 "priority": "P2",
 "pillar": "cost",
 "rule_id": null,
 "title": "OSS存储桶生命周期未配置",
 "detail": "OSS存储桶 oss-xxxxx 未配置归档规则，冷数据保留在标准存储",
 "data_source": "manual_check (jdcloud-oss-ops 不存在)",
 "recommendation": "配置生命周期规则：30 天 → IA，180 天 → Archive",
 "effort": "low",
 "impact": "cost",
 "manual_check": true
 }
 ],
 "recommendations": [
 {
 "pillar": "security",
 "priority": "P0",
 "title": "收敛 SSH 安全组规则",
 "action": "委托 jdcloud-vpc-ops 修改 security group rules（remove0.0.0.0/0 on port22）",
 "effort": "low",
 "expected_benefit": "消除 SSH暴力破解面",
 "estimated_cost": "无"
 }
 ],
 "limitations": [
 { "skill": "jdcloud-cloudmonitor-ops", "impact": "Performance评分仅基于配置推断（CPU/内存利用率未量化）" },
 { "skill": "jdcloud-billing-ops (missing)", "impact": "Cost支柱无法量化实际账单" },
 { "skill": "jdcloud-oss-ops (missing)", "impact": "Cost/Storage 检查需手动核查" }
 ]
}
```

###5.3报告 Markdown模板

```markdown
#架构评审报告 — {{user.scenario}}

##摘要
{一句话结论 + composite_score (Mode B)}

##架构概览
| 层 |组件 |京东云产品 |规格 |数量 |地域 |
|---|------|-----------|------|:---:|:----:|
|接入层 |负载均衡 | CLB | 标准型 |1 | cn-north-1 |
| 应用层 | 云主机 | VM (g.n2.medium) |2C4G |2 | cn-north-1a/b |
| 数据层 | MySQL | JCS for MySQL | 主备8.0 |1 | cn-north-1 |
|缓存层 | Redis | JCS for Redis | 主从4G |1 | cn-north-1 |

## WAF评估矩阵（Mode B）
|支柱 |评分 | P0+P1 发现数 |关键发现 |人工核查 |
|:----:|:----:|:-----------:|---------|:--------:|
| Security |0.85 |1 | SSH暴露 | — |
| Reliability |0.70 |2 | MySQL 单节点 |1 |
| Performance |0.60 |1 | VM规格偏低 |1 |
| Cost |0.75 |1 | EIP闲置 |4 |
| Efficiency |0.65 |1 |标签缺失 | — |

##风险发现
### P0 —立即处理
- ...

### P1 — 本周处理
- ...

### P2 — 本月处理
- ...

##改进建议
{按优先级排序，含委托目标和预估工作量}

## 数据源记录
| 数据 | 来源 Skill |采集时间 | RequestId |状态 |
|------|-----------|---------|-----------|:----:|
| VM清单 | jdcloud-vm-ops |2026-06-0811:55 | req-vm-001 | ✅ |
| MySQL 实例 | jdcloud-mysql-ops |2026-06-0811:56 | req-mysql-001 | ✅ |
| Redis 实例 | jdcloud-redis-ops |2026-06-0811:57 | req-redis-001 | ❌ timeout → low confidence |

##局限性
- Performance评分未包含 cloudmonitor-ops实际指标（基于配置推断）
- Cost支柱无法量化账单（jdcloud-billing-ops缺失）
- OSS / NAT / K8s / CDN 检查需手动核查
```

---

##6. 调用频率限制（QPS）

###6.1京东云 API 默认限流

| 产品 | 默认 QPS |触发429阈值 | 推荐并发 |
|------|:-------:|:------------:|:--------:|
| VM |20 |持续 >20 QPS | 并行 ≤8 |
| RDS (MySQL/PG/Mongo) |20 |持续 >20 QPS | 并行 ≤6 |
| Redis / ES |15 |持续 >15 QPS | 并行 ≤5 |
| CLB / EIP / VPC |30 |持续 >30 QPS | 并行 ≤10 |
| IAM |10 |持续 >10 QPS | 并行 ≤4 |
| KMS |10 |持续 >10 QPS | 并行 ≤4 |
| ActionTrail |5 |持续 >5 QPS | 并行 ≤2 |
| CloudMonitor |50 |持续 >50 QPS | 并行 ≤12 |

###6.2 数据采集阶段的限流策略

```
arch-advisor data_collection
 │
 ├── 每个下游 Skill 调用前 sleep(0.3s)防止 burst
 │
 ├──收到429 (Throttling) 时:
 │ -等待 Retry-After头部指定的秒数
 │ -指数退避 (1s,2s,4s,8s)
 │ -最多重试3 次
 │ -失败后标 "rate_limited" 并降级
 │
 └──全部并行调用 → 总耗时应 <30s (10 个 Skill 并行)
```

> **关键**:京东云**不公开**通用 QPS配额具体数值，上表基于社区反馈。如遇持续429，提交工单申请提配额。

---

##7.跨账户策略（STS AssumeRole）

###7.1 使用场景

|场景 |需求 |
|------|------|
| 主账号分析多账号架构 | 使用 STS AssumeRole切换到目标账号 |
|临时审计权限（避免长期 AK） | STS1 小时凭证 |
|跨账号资源清单聚合 | 主账号 STS 到子账号 |

###7.2 STS AssumeRole 命令

```bash
# 主账号 → 子账号临时凭证
jdc --output json sts assume-role \
 --assume-role-info '{
 "roleArn": "jdcloud:ram::ACCOUNT_ID:role/ArchAdvisorRole",
 "roleSessionName": "arch-advisor-session",
 "durationSeconds":3600
 }'
# 返回: $.result.credentials.{accessKeyId, accessKeySecret, securityToken, expiration}
```

> **关键差异（vs阿里云 STS）**:
> -阿里云: `acs:ram::123456789:role/OpsRole`
> -京东云: `jdcloud:ram::ACCOUNT_ID:role/ArchAdvisorRole` （前缀 `jdcloud:ram::` 不是 `acs:ram::`）

###7.3临时凭证传递给下游 Skill

```bash
#注入临时凭证到 ~/.jdc/config
cat > ~/.jdc/config << 'CONFIGEOF'
[default]
access_key = ${TEMP_AK}
secret_key = ${TEMP_SK}
security_token = ${TEMP_SESSION_TOKEN}
region_id = cn-north-1
endpoint = vm.jdcloud-api.com
scheme = https
timeout =20
CONFIGEOF
```

###7.4 ArchAdvisorRole 推荐策略

```json
{
 "Version": "1",
 "Statement": [
 {
 "Effect": "Allow",
 "Action": [
 "vm:Describe*",
 "rds:Describe*",
 "cache:Describe*",
 "es:Describe*",
 "lb:Describe*",
 "vpc:Describe*",
 "eip:Describe*",
 "iam:List*",
 "kms:List*",
 "monitor:Get*",
 "tag:List*",
 "actiontrail:Describe*"
 ],
 "Resource": "*"
 }
 ]
}
```

---

##8.错误传播与降级策略

###8.1 下游 Skill失败分级

|失败级别 |现象 | 处理 |
|---------|------|------|
| **L1暂时性** | 网络超时 /5xx | 重试3 次 (0s →2s →4s退避) |
| **L2限流** | HTTP429 | 按 Retry-After退避，最多重试3 次 |
| **L3凭证错误** | HTTP401 /403 | HALT，提示用户检查凭证，不重试 |
| **L4客户端错误** | HTTP400 (参数错) | HALT，标注为 agent 配置错误 |
| **L5 数据为空** |资源列表为 [] |降级为用户描述 + low confidence |

###8.2降级输出示例

```json
{
 "skill": "jdcloud-redis-ops",
 "status": "degraded",
 "reason": "no_credentials",
 "fallback_used": "user_description",
 "confidence": "low",
 "user_input": "用户口述:1 个 Redis 主从实例4G，cn-north-1a",
 "downstream_impact": "Redis评分仅基于用户描述，未经 API验证"
}
```

###8.3报告 `limitations`字段汇总规则

- 每个失败的 Skill →1 条 limitation记录
-多个 Skill 影响同一支柱 →合并为1 条
- `manual_check: true` 的 finding → 在 findings 中标记，并在 limitations 中说明缺失 Skill

---

##9.跨 Skill调试指南

###9.1委托链路追踪

每次委托必须记录：

```
[arch-advisor] → [jdcloud-vm-ops] describe-instances
 TraceID: trace-20260608-001
 Request: {regionId: "cn-north-1", pageSize:50}
 Response: {instances:12, duration:3.2s, status: success}
 Status: success
```

###9.2常见委托失败对照表

|错误 | 可能原因 |排查方法 |
|------|---------|---------|
| `jdcloud-vm-ops` 返回空 |凭证无 `vm:Describe*`权限 | 检查 RAM策略 |
| `jdcloud-mysql-ops` 超时 | RDS 服务暂时不可用 | 重试或跳过 |
| `jdcloud-cloudmonitor-ops` 无数据 | 云监控未开通 |跳过指标评分，基于配置推断 |
| `jdcloud-audit-ops`凭证错误 | ActionTrail 未授权 |跳过审计检查，标 manual_check |
| `jdcloud-iam-ops`跨账号拒绝 | STS AssumeRole 未配置 |提示用户提供目标账号 Role ARN |

###9.3调试日志格式

```bash
#启用详细日志
export JDC_LOG_LEVEL=DEBUG
jdc --output json vm describe-instances --region-id cn-north-12>&1 | tee /tmp/arch-advisor-debug.log
```

---

##10.验证集成清单

```bash
#1. 环境验证
jdc --version # >=1.2.12
python --version # >=3.10 (不是3.12)
test -n "$JDC_ACCESS_KEY" && echo "AK OK" || echo "AK MISSING"
test -n "$JDC_SECRET_KEY" && echo "SK OK" || echo "SK MISSING"

#2. CLI凭证验证
ls ~/.jdc/config && echo "INI exists"
jdc config get default.access_key | head -c4 && echo "..."

#3. 下游 Skill 可用性
for skill in vm-ops mysql-ops redis-ops clb-ops eip-ops vpc-ops iam-ops kms-ops audit-ops cloudmonitor-ops tag-audit-ops topo-discovery; do
 test -d "jdcloud-$skill" && echo "✅ jdcloud-$skill" || echo "❌ jdcloud-$skill MISSING"
done

#4.端到端连通性测试
jdc --output json vm describe-instances --region-id cn-north-1 --page-size1 | jq '.result.instances | length'
```

---

##11. Changelog

| 版本 | 日期 |变更 |
|:----|:----|------|
|1.0.0 |2026-06-08 |初始版本：13+ 下游 Skill委托协议、跨账户 STS、QPS限流、降级策略、报告输出契约 |
