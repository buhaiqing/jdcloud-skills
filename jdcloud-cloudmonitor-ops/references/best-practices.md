# 运维最佳实践与参考

> 本文档从 `SKILL.md` 提取。

## 监控覆盖策略

- **核心资源**: 对生产环境所有云资源启用基础监控
- **关键指标**: CPU、内存、磁盘、网络四大黄金指标必配告警
- **业务指标**: 通过自定义监控上报业务关键指标

## 告警规则配置

- **阈值设置**: 根据业务特点设置合理的告警阈值，避免告警风暴
- **通知策略**: 配置多渠道通知（短信+邮件+回调），设置通知周期避免重复打扰
- **分级告警**: 区分 P0/P1/P2 级别，配置不同的通知策略和响应时间

## Dashboard 管理

- **业务视角**: 按业务系统组织监控面板
- **关键指标置顶**: 将最重要的指标放在面板顶部
- **模板变量**: 使用模板变量实现资源的快速切换

## 成本优化

- **存储周期**: 根据数据重要性设置不同的数据存储周期
- **采集频率**: 非关键资源可适当降低监控数据采集频率

## 支持的云产品监控

| 类别 | 产品 |
|------|------|
| 计算 | 云主机 CVM、轻量云主机、原生容器、Kubernetes 集群、函数计算 |
| 网络 | 负载均衡、NAT 网关、弹性公网 IP、共享带宽包、专线服务 |
| 存储 | 云硬盘、对象存储、云文件服务 |
| 数据库 | RDS、MongoDB、Redis、Memcached、TiDB、ClickHouse |
| 中间件 | 消息队列 JCQ/RabbitMQ/Kafka/RocketMQ、Zookeeper |
| 其他 | CDN、Elasticsearch、DTS、堡垒机等 |

## 常用监控指标

### 云主机(VM)常用指标

| 指标名称 | 说明 | 单位 |
|---------|------|------|
| vm.cpu.util | CPU 使用率 | % |
| vm.memory.util | 内存使用率 | % |
| vm.disk.read | 磁盘读速率 | Bps |
| vm.disk.write | 磁盘写速率 | Bps |
| vm.network.in | 内网入速率 | bps |
| vm.network.out | 内网出速率 | bps |

### 云数据库 RDS 常用指标

| 指标名称 | 说明 | 单位 |
|---------|------|------|
| rds.cpu.util | CPU 使用率 | % |
| rds.memory.util | 内存使用率 | % |
| rds.connection.util | 连接数使用率 | % |
| rds.qps | 每秒查询数 | 次/秒 |
| rds.tps | 每秒事务数 | 次/秒 |

### 负载均衡常用指标

| 指标名称 | 说明 | 单位 |
|---------|------|------|
| lb.newconnection | 新建连接数 | 个/秒 |
| lb.activeconnection | 活跃连接数 | 个 |
| lb.traffic.in | 入流量 | bps |
| lb.traffic.out | 出流量 | bps |

## API 限制说明

| 限制项 | 说明 |
|--------|------|
| 查询频率 | 监控数据查询接口默认 QPS 限制为 100 |
| 数据保留 | 原始监控数据保留 15 天，聚合数据保留 30 天 |
| 告警规则 | 每个区域最多可创建 500 条告警规则 |
| 自定义指标 | 每个命名空间最多支持 1000 个自定义指标 |

## 相关链接

- [京东云云监控产品页](https://www.jdcloud.com/cn/products/monitoring)
- [云监控文档中心](https://docs.jdcloud.com/cn/monitoring/learning)
- [云监控 API 文档](https://docs.jdcloud.com/cn/monitoring/api/overview)
- [京东云 CLI](https://github.com/jdcloud-api/jdcloud-cli)
