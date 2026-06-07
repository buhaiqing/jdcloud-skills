# CLI Usage — jdcloud-vpc-ops

> **版本**: 1.0.0 | CLI: `jdc` v1.2.12

## 基本规则

1. `--output json` 必须在子命令**之前**
2. `--region-id` 非必需（默认读取 `~/.jdc/config`）
3. 凭证: `~/.jdc/config` INI 文件（**不是**环境变量）
4. Python 3.10 必须（非 3.12+ — `SafeConfigParser` removed）

## 命令树摘要

`jdc vpc` 共计 **63** 子命令,分类如下:

### VPC 管理 (4)
```
jdc --output json vpc create-vpc --vpc-name NAME [--address-prefix CIDR] [--description DESC] [--az-type standard|edge]
jdc --output json vpc describe-vpcs [--page-number N] [--page-size N] [--filters FILTERS]
jdc --output json vpc describe-vpc --vpc-id VPCID
jdc --output json vpc modify-vpc --vpc-id VPCID [--vpc-name NAME] [--description DESC]
jdc --output json vpc delete-vpc --vpc-id VPCID
```

### 子网管理 (4)
```
jdc --output json vpc create-subnet --vpc-id VPCID --subnet-name NAME [--address-prefix CIDR] [--az AZ] [--description DESC]
jdc --output json vpc describe-subnets [--page-number N] [--page-size N] [--filters FILTERS]
jdc --output json vpc describe-subnet --subnet-id SUBNETID
jdc --output json vpc modify-subnet --subnet-id SUBNETID [--subnet-name NAME] [--description DESC]
jdc --output json vpc delete-subnet --subnet-id SUBNETID
```

### 安全组管理 (4)
```
jdc --output json vpc create-network-security-group --vpc-id VPCID --network-security-group-name NAME [--description DESC]
jdc --output json vpc describe-network-security-groups [--filters FILTERS]
jdc --output json vpc describe-network-security-group --network-security-group-id SGID
jdc --output json vpc modify-network-security-group --network-security-group-id SGID [--name NAME] [--description DESC]
jdc --output json vpc delete-network-security-group --network-security-group-id SGID
```

### 安全组规则 (3)
```
jdc --output json vpc add-network-security-group-rules --network-security-group-id SGID --network-security-group-rule-specs '[...]'
jdc --output json vpc modify-network-security-group-rules --network-security-group-id SGID --network-security-group-rule-specs '[...]'
jdc --output json vpc remove-network-security-group-rules --network-security-group-id SGID --rule-id-list '["id1","id2"]'
```

### 路由表 (4)
```
jdc --output json vpc create-route-table --vpc-id VPCID --route-table-name NAME
jdc --output json vpc describe-route-tables [--page-size N] [--filters FILTERS]
jdc --output json vpc describe-route-table --route-table-id RTID
jdc --output json vpc delete-route-table --route-table-id RTID
```

### 路由表规则 (3)
```
jdc --output json vpc add-route-table-rules --route-table-id RTID --route-table-rule-specs '[...]'
jdc --output json vpc modify-route-table-rules --route-table-id RTID --route-table-rule-specs '[...]'
jdc --output json vpc remove-route-table-rules --route-table-id RTID --rule-id-list '["id1"]'
```

### 网络 ACL (4)
```
jdc --output json vpc create-network-acl --vpc-id VPCID --network-acl-name NAME
jdc --output json vpc describe-network-acls [--page-size N]
jdc --output json vpc describe-network-acl --network-acl-id ACLID
jdc --output json vpc associate-network-acl --network-acl-id ACLID --subnet-id SUBNETID
jdc --output json vpc disassociate-network-acl --network-acl-id ACLID --subnet-id SUBNETID
jdc --output json vpc delete-network-acl --network-acl-id ACLID
```

### VPC Peering (4)
```
jdc --output json vpc create-vpc-peering --vpc-id VPCID --vpc-id-oppo OPPO-VPCID [--description DESC]
jdc --output json vpc describe-vpc-peerings [--page-size N]
jdc --output json vpc describe-vpc-peering --vpc-peering-id PEERINGID
jdc --output json vpc delete-vpc-peering --vpc-peering-id PEERINGID
```

### EIP 管理 (5)
`jdc vpc` 下有 EIP 命令,但已被 `jdcloud-eip-ops` 覆盖:
```
jdc --output json vpc create-elastic-ips [...]
jdc --output json vpc describe-elastic-ips [...]
jdc --output json vpc describe-elastic-ip [...]
jdc --output json vpc delete-elastic-ip [...]
jdc --output json vpc modify-elastic-ip [...]
```
> **注意**: EIP 操作应委托给 `jdcloud-eip-ops` skill,不在此 skill 范围。

### 其它 (约 20+)
- 带宽包: `create-bandwidth-package`, `delete-bandwidth-package`, `describe-bandwidth-packages`, `add-bandwidth-package-ip`, `remove-bandwidth-package-ip`
- 弹性网卡: `create-network-interface`, `describe-network-interfaces`, `delete-network-interface`, `modify-network-interface`, `assign-secondary-ips`, `unassign-secondary-ips`, `associate-elastic-ip`, `disassociate-elastic-ip`
- 其它: `describe-quota`, `generate-skeleton`, `describe-edge-ip-providers`

## JSON 响应路径速查表

| 资源 | CLI sub-command | JSON path |
|------|----------------|-----------|
| VPC 详情 | `describe-vpc` | `$.result.vpc` |
| VPC 列表 | `describe-vpcs` | `$.result.vpcs[]` |
| 子网详情 | `describe-subnet` | `$.result.subnet` |
| 子网列表 | `describe-subnets` | `$.result.subnets[]` |
| SG 详情 | `describe-network-security-group` | `$.result.networkSecurityGroup` |
| SG 列表 | `describe-network-security-groups` | `$.result.networkSecurityGroups[]` |
| 路由表详情 | `describe-route-table` | `$.result.routeTable` |
| 路由表列表 | `describe-route-tables` | `$.result.routeTables[]` |
| ACL 详情 | `describe-network-acl` | `$.result.networkAcl` |
| ACL 列表 | `describe-network-acls` | `$.result.networkAcls[]` |
| Peering 详情 | `describe-vpc-peering` | `$.result.vpcPeering` |
| Peering 列表 | `describe-vpc-peerings` | `$.result.vpcPeerings[]` |
| 配额 | `describe-quota` | `$.result.quotas[]` |

## 完整操作示例

### 示例 1: 创建 VPC + 子网 + 安全组

```bash
# 1. 创建 VPC
jdc --output json vpc create-vpc \
  --vpc-name "prod-beijing" \
  --address-prefix "10.0.0.0/16" \
  --description "Production VPC in Beijing"
# → $.result.vpcId → vpc-xxx

# 2. 创建子网
jdc --output json vpc create-subnet \
  --vpc-id "vpc-xxx" \
  --subnet-name "app-a" \
  --address-prefix "10.0.1.0/24" \
  --az "cn-north-1a"

# 3. 创建安全组
jdc --output json vpc create-network-security-group \
  --vpc-id "vpc-xxx" \
  --network-security-group-name "web-sg" \
  --description "Web tier security group"
# → $.result.networkSecurityGroup.groupId → sg-xxx

# 4. 添加安全组规则 (开放 80/443 入站)
jdc --output json vpc add-network-security-group-rules \
  --network-security-group-id "sg-xxx" \
  --network-security-group-rule-specs \
  '[{"protocol":6,"direction":0,"addressPrefix":"0.0.0.0/0","fromPort":80,"toPort":80,"description":"HTTP"}, {"protocol":6,"direction":0,"addressPrefix":"0.0.0.0/0","fromPort":443,"toPort":443,"description":"HTTPS"}]'
```

### 示例 2: 列出 VPC + 计数

```bash
# 列出所有 VPC
jdc --output json vpc describe-vpcs --page-size 100

# 按名称过滤
jdc --output json vpc describe-vpcs --filters "vpcNames=prod-beijing"

# 获取总数
jdc --output json vpc describe-vpcs | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result'].get('totalCount',0))"
```

### 示例 3: 查询安全组规则

```bash
# 查看安全组详情 (含规则列表)
jdc --output json vpc describe-network-security-group \
  --network-security-group-id "sg-xxx"

# 输出中:
# $.result.networkSecurityGroup.networkSecurityGroupRuleDescriptions:
# {
#   "inboundRules": [{...}],
#   "outboundRules": [{...}]
# }
```