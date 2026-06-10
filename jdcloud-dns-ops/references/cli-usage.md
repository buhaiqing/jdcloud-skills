# CLI — JD Cloud DNS (`jdc`)

## Install and Config

- Install: see [JD Cloud CLI](https://github.com/jdcloud-api/jdcloud-cli)
- **CRITICAL:** `jdc` reads credentials exclusively from `~/.jdc/config` INI file, NOT from env vars.
- For sandbox environments, redirect `HOME` and pre-create config files (see SKILL.md §Sandbox Config).

## Conventions

- `--output json` is a **top-level argument** — MUST be placed BEFORE the subcommand: `jdc --output json domainservice <command> ...`
- `--no-interactive` does NOT exist in `jdc` CLI — omit this flag.
- Two CLI modules: `domainservice` (newer, preferred) and `clouddnsservice` (legacy).

## CLI vs API Coverage Gap

| Operation | `domainservice` | `clouddnsservice` (legacy) |
|-----------|-----------------|---------------------------|
| Create Domain | `create-domain` | `add-domain` |
| Describe Domains | `describe-domains` | `get-domains` |
| Delete Domain | `delete-domain` | `del-domain` |
| Modify Domain | `modify-domain` | `update-domain` |
| Create Resource Record | `create-resource-record` | `add-rr` |
| Describe Resource Records | `describe-resource-record` | `search-rr` |
| Modify Resource Record | `modify-resource-record` | `update-rr` |
| Delete Resource Record | `delete-resource-record` | — |
| Enable/Disable/Delete RR | `modify-resource-record-status` | `operate-rr` |
| Batch Set Records | `batch-set-resource-records` | `batch-set-dns-resolve` |
| Create Monitor | `create-monitor` | `add-monitor` |
| Describe Monitor | `describe-monitor` | `get-monitor` |
| Modify Monitor | `modify-monitor` | `update-monitor` |
| Monitor Status | `modify-monitor-status` | `operate-monitor` |
| Delete Monitor | `delete-monitor` | — |
| Monitor Targets | `create-monitor-target`, `describe-monitor-target` | `add-monitor-target`, `get-targets` |
| User Views | `create-user-view`, `describe-user-view`, `delete-user-view` | `add-user-view`, `get-user-view`, `del-user-view` |
| User View IPs | `create-user-view-ip`, `describe-user-view-ip`, `delete-user-view-ip` | `add-user-view-ip`, `get-user-view-ip`, `del-user-view-ip` |
| View Tree | `describe-view-tree` | `get-view-tree` |
| Action Log | `describe-action-log` | `get-action-log` |
| Query Count | `describe-domain-query-count` | `get-domain-query-count` |
| Query Traffic | `describe-domain-query-traffic` | `get-domain-query-traffic` |
| Monitor Alarm | `describe-monitor-alarm` | `get-monitor-alarm-info` |

## Command Map

### Domain Operations

| Goal | `jdc` Invocation |
|------|-----------------|
| Create (free) | `jdc --output json domainservice create-domain --pack-id 0 --domain-name <name>` |
| Create (paid) | `jdc --output json domainservice create-domain --pack-id <1|2> --domain-name <name> --buy-type 1 --time-span <n> --time-unit <3|4>` |
| List | `jdc --output json domainservice describe-domains --page-number 1 --page-size 100` |
| Delete | `jdc --output json domainservice delete-domain --domain-id <id>` |

### Resource Record Operations

| Goal | `jdc` Invocation |
|------|-----------------|
| Create | `jdc --output json domainservice create-resource-record --domain-id <id> --req '{"hostRecord":"www","hostValue":"1.2.3.4","type":"A","ttl":600}'` |
| Search | `jdc --output json domainservice describe-resource-record --domain-id <id> --page-number 1 --page-size 100` |
| Modify | `jdc --output json domainservice modify-resource-record --domain-id <id> --req '{"id":123,"hostRecord":"www","hostValue":"5.6.7.8","type":"A","ttl":300}'` |
| Enable | `jdc --output json domainservice modify-resource-record-status --domain-id <id> --ids '[123]' --action on` |
| Disable | `jdc --output json domainservice modify-resource-record-status --domain-id <id> --ids '[123]' --action off` |
| Delete | `jdc --output json domainservice modify-resource-record-status --domain-id <id> --ids '[123]' --action del` |
| Batch Set | `jdc --output json domainservice batch-set-resource-records --domain-id <id> --req '[{"id":0,"hostRecord":"www","hostValue":"1.2.3.4","type":"A","ttl":600}]'` |

### Monitor Operations

| Goal | `jdc` Invocation |
|------|-----------------|
| Create | `jdc --output json domainservice create-monitor --domain-id <id> --sub-domain-name <sub>` |
| List | `jdc --output json domainservice describe-monitor --domain-id <id> --page-number 1 --page-size 100` |
| Start | `jdc --output json domainservice modify-monitor-status --domain-id <id> --sub-domain-name <sub> --status 1` |
| Stop | `jdc --output json domainservice modify-monitor-status --domain-id <id> --sub-domain-name <sub> --status 2` |
| Delete | `jdc --output json domainservice delete-monitor --domain-id <id> --sub-domain-name <sub>` |

### Custom DNS Lines

| Goal | `jdc` Invocation |
|------|-----------------|
| Create | `jdc --output json domainservice create-user-view --domain-id <id> --req '{"viewName":"my-line","isDelete":0}'` |
| List | `jdc --output json domainservice describe-user-view --domain-id <id> --page-number 1 --page-size 100` |
| Delete | `jdc --output json domainservice delete-user-view --domain-id <id> --req '{"viewId":<vid>,"viewName":"my-line"}'` |

### View Tree & Statistics

| Goal | `jdc` Invocation |
|------|-----------------|
| View Tree | `jdc --output json domainservice describe-view-tree` |
| Query Count | `jdc --output json domainservice describe-domain-query-count --domain-id <id> --start <ts> --end <ts>` |
| Query Traffic | `jdc --output json domainservice describe-domain-query-traffic --domain-id <id> --start <ts> --end <ts>` |
| Action Log | `jdc --output json domainservice describe-action-log --page-number 1 --page-size 100 --start-time <ts> --end-time <ts>` |

## JSON Response Paths

### Create Domain
```json
{"requestId": "...", "result": {"data": {"domainId": 12345, "order": "..."}}}
```
- `$.result.data.domainId` — New domain ID

### Describe Domains
```json
{"requestId": "...", "result": {"dataList": [{"id": 12345, "domainName": "example.com", "packId": 0}], "totalCount": 1}}
```
- `$.result.dataList[*].id` — Domain IDs
- `$.result.dataList[*].domainName` — Domain names

### Create Resource Record
```json
{"requestId": "...", "result": {"data": {"id": 67890}}}
```
- `$.result.data.id` — New record ID

### Search Resource Records
```json
{"requestId": "...", "result": {"dataList": [{"id": 67890, "hostRecord": "www", "hostValue": "1.2.3.4", "type": "A", "ttl": 600}], "totalCount": 1}}
```
- `$.result.dataList[*].id` — Record IDs
- `$.result.dataList[*].hostRecord` — Host records
- `$.result.dataList[*].hostValue` — Record values
- `$.result.dataList[*].type` — Record types

## Common CLI Patterns

### Sandbox Setup
```bash
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc
cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = YOUR_ACCESS_KEY
secret_key = YOUR_SECRET_KEY
region_id = cn-north-1
endpoint = domainservice.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF
printf "%s" "default" > /tmp/jdc-home/.jdc/current
```

### Extracting Values with jq
```bash
# Get domain ID from create response
DOMAIN_ID=$(jdc --output json domainservice create-domain ... | jq -r '.result.data.domainId')

# Get all domain IDs
DOMAIN_IDS=$(jdc --output json domainservice describe-domains | jq -r '.result.dataList[].id')
```
