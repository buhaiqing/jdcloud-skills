# Integration Guide — jdcloud-vpc-ops

> **版本**: 1.0.0 — 本 skill 与京东云技能体系中其它 skill 的协作契约。

## 数据流总览

```mermaid
graph TB
    subgraph 上游 Skill (依赖 VPC)
        AA[jdcloud-arch-advisor]
        TD[jdcloud-topo-discovery]
        AC[jdcloud-aiops-cruise]
    end
    
    subgraph 本 Skill
        VPC[jdcloud-vpc-ops<br/>VPC/Subnet/SG/RT/ACL/Peering]
    end
    
    subgraph 下游 Skill (VPC 是前置条件)
        VM[jdcloud-vm-ops<br/>VM 需指定 VPC+Subnet]
        CLB[jdcloud-clb-ops<br/>CLB 需关联 VPC 子网]
        EIP[jdcloud-eip-ops<br/>EIP 关联 VPC 内资源]
        MySQL[jdcloud-mysql-ops]
        Redis[jdcloud-redis-ops]
        NAT[jdcloud-nat-ops<br/>待建]
    end
    
    subgraph 支撑 Skill
        CM[jdcloud-cloudmonitor-ops<br/>VPC 监控指标]
    end
    
    AA -->|Mode A/B 采集| VPC
    TD -->|扫描 VPC 拓扑| VPC
    AC -->|链路诊断| VPC
    VPC -->|VPC 内创建| VM
    VPC -->|子网关联| CLB
    VPC -->|子网关联| MySQL
    VPC -->|子网关联| Redis
    EIP -->|绑定到 VPC 内| VM
    VPC --> CM
```

## 上游 Skill 契约

### jdcloud-arch-advisor

| 委托能力 | VPC API | 输出参数 |
|---------|---------|---------|
| 列出 VPC (`describe-vpcs`) | `$.result.vpcs[]` | `vpcId`, `vpcName`, `addressPrefix` |
| 列出子网 (`describe-subnets`) | `$.result.subnets[]` | `subnetId`, `subnetName`, `vpcId`, `addressPrefix` |
| 列出安全组 (`describe-network-security-groups`) | `$.result.networkSecurityGroups[]` | `groupId`, `groupName`, `vpcId` |
| 安全组详情 (`describe-network-security-group`) | `$.result.networkSecurityGroup` | 含 `inboundRules`/`outboundRules` |

**调用示例 (arch-advisor → vpc-ops)**:
```bash
# arch-advisor 在 Mode A/B 中调用 vpc-ops 采集数据
jdc --output json vpc describe-vpcs --region-id cn-north-1 --page-size 100
jdc --output json vpc describe-subnets --region-id cn-north-1 --page-size 100
jdc --output json vpc describe-network-security-groups --region-id cn-north-1 --page-size 100
```

### jdcloud-topo-discovery

| 委托能力 | VPC API | 用途 |
|---------|---------|------|
| VPC 扫描 | `describe-vpcs` | 顶层 VPC 列表 |
| 子网扫描 | `describe-subnets` | 每个 VPC 子网详情 |
| 安全组扫描 | `describe-network-security-groups` | 安全组规则审计 |
| 路由表扫描 | `describe-route-tables` | 路由拓扑 |

**调用示例 (topo-discovery → vpc-ops)**:
```bash
# 在 topo-scan.sh 中调用
jdc --output json vpc describe-vpcs --page-size 100 > /tmp/vpcs.json
# 解析 VPC IDs → 扫描每个 VPC 的子网/安全组
```

### jdcloud-aiops-cruise

| 委托能力 | VPC API | 用途 |
|---------|---------|------|
| 安全组规则分析 | `describe-network-security-group` | sg_analyzer 使用 |
| 子网拓扑 | `describe-subnets` | 链路拓扑 |
| NAT 关联 | `describe-route-tables` | 路由诊断 |

## 下游 Skill 契约

当 VPC 创建完成后,下游 skill 依赖 VPC 资源 ID:

```bash
# jdcloud-vm-ops 创建 VM 时需要 VPC + 子网 ID
jdc --output json vm create-instances \
  --vpc-id "{{output.vpc_id}}" \
  --subnet-id "{{output.subnet_id}}" \
  ...

# jdcloud-clb-ops 创建 CLB 时需要子网 ID
jdc --output json lb create-load-balancer \
  --subnet-id "{{output.subnet_id}}" \
  ...

# jdcloud-eip-ops 绑定 EIP 到 VM 时需要 VM ID
jdc --output json eip associate-elastic-ip \
  --instance-id "{{output.vm_id}}" \
  ...
```

## 共享变量约定

| 变量 | 本 skill 产生 | 下游 skill 使用 |
|------|--------------|-----------------|
| `{{output.vpc_id}}` | VPC 创建 | VM/CLB 创建时指定 |
| `{{output.subnet_id}}` | 子网创建 | VM/CLB/RDS 创建时指定 |
| `{{output.sg_id}}` | 安全组创建 | VM 关联安全组 |
| `{{output.route_table_id}}` | 路由表创建 | 路由规则管理 |
| `{{output.region}}` | 各命令的 --region-id | 所有下游命令 |

## 错误传播

当 vpc-ops 不可用(CLI 不可用/凭证失效)时:

| 上游 Skill | 降级策略 |
|-----------|---------|
| `jdcloud-arch-advisor` | 用户自行描述 VPC 结构 + 报告中标注 `low confidence` |
| `jdcloud-topo-discovery` | 跳过 VPC/Subnet/SG 采集(报告中标注 `data_source: manual`) |
| `jdcloud-aiops-cruise` | 跳过 sg_analyzer 分析 |