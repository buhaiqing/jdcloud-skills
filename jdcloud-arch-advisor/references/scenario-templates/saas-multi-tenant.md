# SaaS 多租户架构方案（京东云版）

## 架构总览

```mermaid
graph TB
    subgraph 接入层
        USR[终端租户]
        CDN[CDN]
        WAF[Web 应用防护]
        CLB[应用型 CLB]
    end
    subgraph 平台层
        PORTAL[租户门户]
        AUTH[统一身份认证 (IAM/OIDC)]
        BILL[计费计量]
    end
    subgraph 业务层
        SA[共享业务服务 (K8s)]
        SB[专属业务服务 (K8s)]
    end
    subgraph 数据层
        SDB[共享数据库]
        TDB[租户专属 Schema]
        TDB2[租户专属数据库]
        REDIS[JCS for Redis (租户隔离 namespace)]
    end
    subgraph 监控
        MON[云监控 (按租户标签拆分)]
    end

    USR --> CDN --> WAF --> CLB --> PORTAL
    PORTAL --> AUTH
    PORTAL --> BILL
    PORTAL --> SA
    PORTAL --> SB
    SA --> SDB
    SA --> REDIS
    SB --> TDB
    SB --> TDB2
    MON -.- SA
    MON -.- SB
```

## 租户隔离级别

| 级别 | 描述 | 隔离强度 | 适用 | 京东云实现 |
|------|------|---------|------|-----------|
| **L1 共享数据库共享 Schema** | 所有租户共用一个 DB + Schema，用 tenant_id 区分 | 弱 | 免费/试用版 | JCS for MySQL 单实例 + 字段过滤 |
| **L2 共享数据库独立 Schema** | 共享 DB，每个租户一个 Schema | 中 | 标准版/企业版 | JCS for MySQL + Schema 隔离 |
| **L3 独立数据库** | 每个租户一个独立 DB | 强 | 大客户/金融 | JCS for MySQL 多实例 + 实例级别 RBAC |
| **L4 独立 VPC/集群** | 租户独占 K8s 集群 + VPC | 极强 | 政企/超大型客户 | JCS K8s + VPC + Direct Connect |

## 平台核心能力

### 身份与权限
- **统一身份认证**: 基于 OIDC/SAML 联邦，对接租户自有 IDP
- **细粒度 RBAC**: 租户管理员 → 部门 → 角色 → 用户
- **审计日志**: ActionTrail + 应用层审计，记录所有数据访问

### 计费与计量
- **按量计费**: API 调用次数、存储用量、活跃用户数
- **账单生成**: 周期对账 + 用量明细 + 发票申请
- **资源配额**: 每个租户/套餐对应硬性/软性配额

### 数据隔离
- **行级安全 (RLS)**: 数据库视图 + 策略过滤
- **KMS 密钥按租户**: 数据加密密钥与租户绑定
- **跨租户访问零信任**: 默认拒绝所有跨租户调用，需审批

## 可扩展性设计

| 维度 | 策略 |
|------|------|
| 租户数量 | 平台层无状态，水平扩展 K8s 节点 |
| 数据量 | 租户数据分库分表（按 tenant_id 哈希） |
| 流量 | 共享层 + 专属层，热点租户独立部署 |
| 地域 | 单地域多 AZ 起步；海外客户启用多地域 |

## 成本估算（月）

- **平台基线**（L1 共享版，< 100 租户）: ¥10,000 - ¥30,000
- **企业版**（L2/L3 混合，< 1000 租户）: ¥50,000 - ¥200,000
- **旗舰版**（L3 + L4 混合，> 1000 租户）: ¥300,000+
