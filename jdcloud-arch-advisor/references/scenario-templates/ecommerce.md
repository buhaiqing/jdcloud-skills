# 电商平台架构方案（京东云版）

## 架构总览

```mermaid
graph TB
    subgraph 用户端
        US[终端用户]
    end
    subgraph 接入层
        CDN[京东云 CDN]
        WAF[Web 应用防护]
        CLB[应用型负载均衡 CLB]
        DDOS[高防 IP]
    end
    subgraph 应用层
        K8S[JCS for Kubernetes]
        VM[云主机 VM (常规业务)]
    end
    subgraph 中间件
        JCQ[消息队列 JCQ]
        ES[JCS for Elasticsearch]
        REDIS[JCS for Redis]
    end
    subgraph 数据层
        MYSQL[JCS for MySQL 主备]
        OSS[对象存储 OSS]
    end

    US --> CDN --> WAF --> CLB --> K8S
    CLB --> DDOS
    K8S --> JCQ --> MYSQL
    K8S --> REDIS
    K8S --> ES
    K8S --> OSS
    CLB --> VM --> MYSQL
```

## 分层产品选型

### 接入层
- **CDN**: 京东云 CDN，加速静态资源（图片、JS/CSS），动态加速回源
- **WAF**: 京东云 WAF，防护 SQL 注入、XSS、CC 攻击
- **高防 IP**: 针对大流量 DDoS 攻击防护，建议 5 Gbps 起配
- **CLB**: 应用型负载均衡，支持 HTTPS 卸载、灰度发布、健康检查

### 应用层
- **JCS for Kubernetes**: 京东云托管 Kubernetes 集群，管理微服务
- **VM**: 云主机，适合稳态业务或团队容器化经验不足的场景
- **弹性伸缩**: 通过 JCS for Kubernetes HPA / VM 弹性伸缩组实现

### 数据层
- **JCS for MySQL**: 一写多读主备集群，支持读写分离，建议主备版起步，大促可临时升配
- **JCS for Redis**: 会话管理、商品缓存、热点数据缓存；建议主从版 + 持久化
- **JCS for Elasticsearch**: 商品搜索、订单日志分析
- **JCQ (消息队列)**: 订单异步处理、库存扣减、消息解耦

### 存储层
- **OSS (对象存储)**: 商品图片、用户头像、交易凭证，结合 CDN 分发
- **云硬盘**: 应用数据持久化，多 AZ 冗余类型

## DAU 分级扩缩容建议

| 规模 | DAU | K8s/VM 节点 | JCS for MySQL 规格 | JCS for Redis 规格 |
|------|-----|----------|-------------|-------------|
| 小型 | < 1 万 | 3-5 节点 (4C8G) | 主备 2C4G | 主从 4G |
| 中型 | 1-10 万 | 10-20 节点 (8C16G) | 主备 4C8G | 主从 16G |
| 大型 | 10-100 万 | 30-100 节点 (16C32G) | 主备 8C16G | 集群 64G |
| 超大型 | 100 万+ | 100+ 节点 + 弹性伸缩 | 主备 16C32G+ | 集群 128G+ |

## 高可用/容灾配置

- **多可用区部署**: K8s 集群跨 3 个可用区，Pod 反亲和调度
- **JCS for MySQL 主备**: 跨可用区自动故障切换，RTO < 30 秒
- **JCS for Redis 主从**: 启用数据持久化 + 自动主备切换
- **对象存储跨区域复制**: 关键图片和交易凭证异地备份
- **JCQ 死信队列**: 失败消息自动重试与归档

## 成本估算（月）

- **小型**: 约 3,000 - 8,000 元
- **中型**: 约 15,000 - 40,000 元
- **大型**: 约 80,000 - 200,000 元
- **超大型**: 30 万元以上（视弹性用量而定）

> 提示：大促期间建议提前 2 周完成 K8s 节点池扩容、MySQL 升配和 CDN 预热准备。
