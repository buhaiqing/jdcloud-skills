# 执行命令清单 (jdc CLI)

本 Skill 优先使用 `jdc` CLI 进行数据采集,**所有命令必须以 `jdc --output json` 开头**(在子命令前)。以下为各阶段执行的标准命令:

## 1. VPC 基础网络

| 资源 | 命令 | 关键参数 |
|------|------|---------|
| VPC 列表 | `jdc --output json vpc describe-vpcs --region-id $JDC_REGION --page-size 100` | `--page-size` 最大 100 |
| Subnet 列表 | `jdc --output json vpc describe-subnets --region-id $JDC_REGION --page-size 100` | `--filters "vpcId=$VPC_ID"` |
| 安全组列表 | `jdc --output json vpc describe-network-security-groups --region-id $JDC_REGION --page-size 100` | `--filters "vpcId=$VPC_ID"` |
| 路由表列表 | `jdc --output json vpc describe-route-tables --region-id $JDC_REGION --page-size 100` | - |
| ACL 列表 | `jdc --output json vpc describe-network-acls --region-id $JDC_REGION --page-size 100` | - |
| 弹性网卡 | `jdc --output json vpc describe-network-interfaces --region-id $JDC_REGION --page-size 100` | - |

## 2. 负载均衡与公网入口

| 资源 | 命令 | 备注 |
|------|------|------|
| CLB 列表 | `jdc --output json lb describe-load-balancers --region-id $JDC_REGION --page-size 100` | `lb` 是 CLB 在 jdc 的别名 |
| EIP 列表 | `jdc --output json eip describe-elastic-ips --region-id $JDC_REGION --page-size 100` | - |
| 高可用组 | `jdc --output json ag describe-ags --region-id $JDC_REGION --page-size 50` | `ag` 是 AG Group 的 jdc 子命令 |
| 共享带宽包 | `jdc --output json vpc describe-bandwidth-packages --region-id $JDC_REGION --page-size 50` | 仍在 `vpc` 命令下 |

## 3. 核心组件资源 (详细模式)

| 资源 | 命令 | 数据源 Skill |
|------|------|------------|
| VM 实例 | `jdc --output json vm describe-instances --region-id $JDC_REGION --page-size 100` | `jdcloud-vm-ops` |
| RDS (MySQL/PostgreSQL 等) | `jdc --output json rds describe-instances --region-id $JDC_REGION --page-size 100` | `jdcloud-mysql-ops` / `jdcloud-postgresql-ops` |
| MongoDB | `jdc --output json mongodb describe-instances --region-id $JDC_REGION --page-size 100` | `jdcloud-mongodb-ops` |
| Redis | `jdc --output json redis describe-cache-instances --region-id $JDC_REGION --page-size 100` | `jdcloud-redis-ops` |

## 4. 身份与密钥 (详细模式)

| 资源 | 命令 | 备注 |
|------|------|------|
| IAM 子用户 | `jdc --output json iam describe-sub-users --page-size 100` | 不需要 `--region-id`(全局资源) |
| IAM 策略 | `jdc --output json iam describe-policies --page-size 100` | - |
| KMS 密钥列表 | `jdc --output json kms describe-key-list --page-size 100` | - |
| KMS 密钥详情 | `jdc --output json kms describe-key --key-id $KEY_ID` | - |

## 5. 跨账号 (Phase 2)

| 资源 | 命令 |
|------|------|
| STS AssumeRole | `jdc --output json sts assume-role --assume-role-info '{"roleArn":"arn:...","roleSessionName":"topo","durationSeconds":3600}'` |

## JSON 输出路径映射 (京东云)

> **京东云响应结构(基于实测错误响应 + OpenAPI 文档):**
> - 成功: `{ "request_id": "...", "result": { ... } }`
> - 失败: `{ "request_id": "...", "error": { "status": "...", "code": <int>, "message": "..." } }`

| 资源 | JSON Path |
|------|-----------|
| VPC ID | `$.result.vpcs[0].vpcId` |
| VPC Name | `$.result.vpcs[0].vpcName` |
| VPC CIDR | `$.result.vpcs[0].addressPrefix` |
| Subnet ID | `$.result.subnets[0].subnetId` |
| Subnet CIDR | `$.result.subnets[0].addressPrefix` |
| VM ID | `$.result.instances[0].instanceId` |
| VM Name | `$.result.instances[0].instanceName` |
| VM Private IP | `$.result.instances[0].privateIpAddress` |
| CLB ID | `$.result.loadBalancers[0].loadBalancerId` |
| EIP Address | `$.result.elasticIps[0].elasticIpAddress` |
| SG ID | `$.result.networkSecurityGroups[0].networkSecurityGroupId` |
| IAM SubUser | `$.result.subUsers[0].subUserName` |
| KMS Key | `$.result.keys[0].keyId` |
| RDS ID | `$.result.dbInstances[0].instanceId` |
| Redis ID | `$.result.cacheInstances[0].cacheInstanceId` |

## 关键差异(对比阿里云)

| 维度 | 阿里云 | 京东云 |
|------|--------|--------|
| `--output json` 位置 | 默认输出 JSON(无需 flag) | **必须 `jdc --output json` 在子命令前** |
| 凭证位置 | env vars | `~/.jdc/config` INI(CLI 模式) |
| 资源路径 | 大写 `Vpc`/`Instance` | 小写 `vpcs`/`instances` |
| 响应结构 | `Code/Message` 在 `Code/Message` 字段 | `error.code` / `error.message` / `error.status` |
| 分页参数 | `--PageSize 100` | `--page-size 100`(全小写) |

> **CRITICAL**: 京东云 CLI 的 `--output json` **必须放在子命令前**(`jdc --output json vpc describe-vpcs`),
> 放在子命令后(`jdc vpc describe-vpcs --output json`)会报"unrecognized arguments"。
