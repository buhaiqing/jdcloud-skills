# Integration Guide for jdcloud-aiops-cruise

## Cross-Skill Integration

`jdcloud-aiops-cruise` is the **read-only** full-link inspection entry point. All
resource mutations must be delegated to product-specific ops skills:

| Finding | Delegate To |
|---|---|
| VM stop/start/resize | `jdcloud-vm-ops` |
| Redis slow query / resize | `jdcloud-redis-ops` |
| MySQL slow query / index / DDL | `jdcloud-mysql-ops` |
| PostgreSQL slow query / VACUUM | `jdcloud-postgresql-ops` |
| CLB upgrade / listener change | `jdcloud-clb-ops` |
| EIP bind/unbind/release | `jdcloud-eip-ops` |
| Alarm rule change | `jdcloud-cloudmonitor-ops` |

## Output Contracts

- Phase 1 output: `reports/output/sniff-<timestamp>.json`
- Phase 2 output: `reports/output/cruise-<timestamp>.json` + Markdown report
- GCL trace: `audit-results/gcl-trace-<timestamp>.json`

## Programmatic Entry Points

```bash
# Phase 1: Perceive
python scripts/01-perceive/cruise_sniff.py --customer <tag>

# Phase 2: Reason
python scripts/02-reason/cruise_link.py --customer <tag> --sniff-file <path>
```

## Future Integrations

- IM / webhook push: not implemented in v1.6.0
- CI pipeline gate: consume Markdown/JSON report and fail on P0 findings
