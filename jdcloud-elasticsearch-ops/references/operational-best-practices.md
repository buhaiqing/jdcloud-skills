# Operational Best Practices — JD Cloud Elasticsearch

## Architecture Selection

- Choose appropriate node class based on workload:
  - **Search-heavy:** More memory, faster CPU (e.g., `es.m1.medium`)
  - **Analytics-heavy:** More disk, balanced CPU
  - **Mixed:** Use `es.n1.medium` or higher
- Use **dedicated master nodes** for production clusters (recommended: 3 master nodes).
- Separate data, master, and Kibana node types for large-scale production deployments.

## High Availability

- Deploy across **multiple AZs** for production.
- Use **at least 3 data nodes** to ensure replica shards can be allocated.
- Configure replica count = 1 minimum; consider 2 for critical data.
- Set `cluster.routing.allocation.disk.threshold_enabled: true` to prevent disk-full failures.

## Security

- **VPC isolation:** Always deploy ES inside a VPC; never expose public endpoints.
- **IP whitelist:** Configure security group rules to restrict ES (9200) and Kibana (5601) ports.
- **Password policy:** Use strong passwords; rotate regularly via `ModifyInstanceAttribute`.
- **SSL/TLS:** Enable HTTPS for ES endpoint and Kibana in production.
- **Audit logging:** Enable Elasticsearch audit logging and forward to a SIEM.

## Performance

- Monitor cluster health (`green`/`yellow`/`red`) via `describeInstance` and `cloudmonitor`.
- Watch JVM heap pressure: keep heap usage < 75%; restart if approaching 90%.
- Optimize mappings: avoid dynamic mappings for high-cardinality fields.
- Use **appropriate sharding strategy:** each shard 10-50GB is ideal.
- Configure **shard allocation awareness** to spread replicas across AZs.
- Tune `indices.memory.index_buffer_size` for write-heavy workloads.

## Backup & Recovery

- Configure **automatic snapshot policy** to OSS bucket; default OSS path recommended.
- **Snapshot retention:** Keep at least 7 daily + 4 weekly + 12 monthly snapshots.
- **Test restore procedures** quarterly in a non-production environment.
- Snapshot frequency depends on RPO:
  - Daily: RPO up to 24h
  - Hourly: RPO up to 1h
  - Continuous: use CCR (Cross-Cluster Replication) for RPO ≈ 0

## Scaling

- **Vertical scaling** (modify spec): Use `ModifyInstanceSpec` for node class/disk changes.
  - Brief service interruption possible during spec changes.
- **Horizontal scaling** (add nodes): Increase `nodeCount` to add data nodes.
  - Online operation; no interruption.
- Plan scaling windows outside business peaks.
- Pre-warm new nodes before decommissioning old ones (rebalance traffic).

## Index Management

- Use **Index Templates** for time-series data (logs, metrics).
- Enable **ILM (Index Lifecycle Management)** for log data:
  - Hot phase: 0-7 days, frequent reads/writes
  - Warm phase: 7-30 days, fewer writes
  - Cold phase: 30+ days, read-only, force-merge
  - Delete phase: 90+ days, automatic removal
- Set **shard counts** based on data volume: 10-50GB per shard.
- Use **rollover API** instead of time-based index naming for cleaner lifecycle management.
- Apply **force-merge** on read-only indices to reduce segment count.

## Cost Optimization

- Use **postpaid** (按配置) for dev/test, **prepaid** (包年包月) for production.
- Right-size instances: avoid over-provisioning memory or disk.
- Use **ILM with cold/delete phases** to reduce storage costs.
- Consider **shared subscription** for multi-region deployments.
- Set budget alerts via `jdcloud-cloudmonitor-ops` to catch unexpected usage.

## Monitoring Integration

- Delegate metric queries to `jdcloud-cloudmonitor-ops`:
  - Cluster health (green/yellow/red status)
  - JVM heap usage
  - Disk usage per node
  - CPU utilization
  - Index/search rate
- Delegate alarm rule changes to `jdcloud-cloudmonitor-ops`.
- Use `jdcloud-alert-intelligence` (read-only) to analyze recurring alert patterns.
