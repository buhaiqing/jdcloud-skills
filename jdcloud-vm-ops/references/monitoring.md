# JD Cloud VM Monitoring Reference

> **ponytail: trimmed — metric codes kept; alarm rule setup delegated to `jdcloud-cloudmonitor-ops`.**

## Core Metrics

| Metric Name | Metric Code | Unit | Description |
|------------|-------------|------|-------------|
| CPU Usage | `vm.cpu.util` | % | Average CPU usage |
| CPU Load 1m | `vm.cpu.load1` | — | 1-min system load |
| CPU Load 5m | `vm.cpu.load5` | — | 5-min system load |
| CPU Load 15m | `vm.cpu.load15` | — | 15-min system load |
| CPU Idle | `vm.cpu.idle` | % | CPU idle percentage |
| CPU User | `vm.cpu.user` | % | User mode CPU |
| CPU System | `vm.cpu.system` | % | System mode CPU |
| CPU I/O Wait | `vm.cpu.iowait` | % | CPU waiting for I/O |
| Memory Usage | `vm.memory.util` | % | Memory usage |
| Used Memory | `vm.memory.used` | MB | Used memory |
| Available Memory | `vm.memory.available` | MB | Available memory |
| Cached Memory | `vm.memory.cached` | MB | Cache memory |
| Swap Usage | `vm.swap.util` | % | Swap usage |

### Quick Query

```bash
jdc --output json monitor describe-metric-data \
  --region-id <region> --metric vm.cpu.util \
  --service-code vm --resource-id i-xxx \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) --aggr-type avg
```

## Alarm Thresholds (recommended)

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| CPU Usage | > 80% for 10m | > 95% for 5m | Upgrade spec or optimize |
| Memory Usage | > 80% for 10m | > 90% for 5m | Upgrade spec or fix leak |
| Disk Usage | > 85% | > 95% | Resize disk or clean |
| CPU I/O Wait | > 30% | > 50% | Upgrade disk type |

> For alarm rule CRUD, delegate to `jdcloud-cloudmonitor-ops`.