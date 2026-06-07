# 游戏服务架构方案（京东云版）

## 架构总览

```mermaid
graph TB
    subgraph 用户端
        PLAYER[玩家客户端]
    end
    subgraph 接入层
        CDN[CDN 资源分发]
        GSLB[全局负载均衡]
        CLB[应用型 CLB]
    end
    subgraph 网关层
        GW[游戏网关 (VM/JCS K8s)]
    end
    subgraph 业务层
        LOGIC[逻辑服 (VM/JCS K8s)]
        MATCH[匹配服]
        CHAT[聊天服]
    end
    subgraph 数据层
        REDIS[JCS for Redis Cluster]
        MYSQL[JCS for MySQL 分库分表]
        ES[JCS for Elasticsearch (日志)]
    end
    subgraph 大数据
        BD[数据仓库 / 离线分析]
    end

    PLAYER --> CDN --> GSLB --> CLB --> GW
    GW --> LOGIC
    GW --> MATCH
    GW --> CHAT
    LOGIC --> REDIS
    LOGIC --> MYSQL
    GW --> ES --> BD
```

## 分层产品选型

### 接入层
- **CDN**: 游戏客户端资源包分发、Patch 升级
- **GSLB**: 全局负载均衡，按地域智能调度
- **CLB**: TCP/HTTPS 接入，承载 WebSocket 长连接

### 网关层
- **游戏网关**: 处理登录、认证、心跳、消息路由
- 建议: VM 部署（保持稳定的 TCP 长连接）或 K8s Deployment（弹性）

### 业务层
- **逻辑服**: 战斗、交易、任务等核心玩法
- **匹配服**: 玩家匹配算法，Redis ZSet 维护分数
- **聊天服**: 全局/房间聊天，Redis Pub/Sub 或 JCQ

### 数据层
- **JCS for Redis Cluster**: 玩家在线状态、积分排行榜、好友关系
- **JCS for MySQL**: 用户基础数据、交易流水（按 user_id 分库分表）
- **JCS for Elasticsearch**: 战斗日志、聊天审计、运营分析

### 实时性要求
- 帧同步 / 状态同步延迟: < 100ms
- 匹配响应: < 1s
- 登录响应: < 3s

## 部署模式

| 模式 | 适用 | 特点 |
|------|------|------|
| 单区集中 | 同服 MMORPG、SLG | 一组完整部署承载所有玩家 |
| 分区分服 | 传统 MMO、武侠 | 按大区独立部署，互不影响 |
| 战斗分服 / 世界服 | MOBA、吃鸡 | 战斗服分区，世界服单点 |
| 全区全服 | 休闲游戏、卡牌 | Redis Cluster 承载状态，MySQL 分库分表 |

## 成本估算（月）

- **小规模休闲游戏**（DAU < 5 万）: ¥10,000 - ¥30,000
- **中规模 MMO/MOBA**（DAU 5-50 万）: ¥80,000 - ¥300,000
- **大规模 SLG/吃鸡**（DAU > 100 万）: ¥500,000+
