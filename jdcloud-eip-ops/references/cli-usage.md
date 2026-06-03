# CLI — JD Cloud EIP (`jdc`)

## Install and config

- **Install**: See [JD Cloud CLI](https://github.com/jdcloud-api/jdcloud-cli)
- **CRITICAL:** The `jdc` CLI reads credentials **exclusively** from `~/.jdc/config` INI file, NOT from environment variables.
- **Sandbox workaround**: Redirect `HOME` and pre-create config files (see SKILL.md "Critical jdc CLI Behavioral Notes").

## Conventions (agent execution)

- `--output json` is a **top-level argument** — MUST be placed BEFORE the subcommand: `jdc --output json eip <command> ...`
- `--no-interactive` does NOT exist in `jdc` CLI — all commands are non-interactive by default; omit this flag.
- Document **exact** JSON paths after verifying with a real invocation (CLI output may differ from raw API).

## CLI vs API coverage gap

| Operation (API / SDK) | Available via `jdc`? | Notes |
|------------------------|---------------------|-------|
| allocateAddress | yes | Full support |
| describeAddress | yes | Full support |
| describeAddresses | yes | Full support |
| associateAddress | yes | Full support |
| dissociateAddress | yes | Full support |
| modifyAddress | yes | Full support |
| releaseAddress | yes | Full support |

## Command map

| Goal | Example `jdc` invocation | Notes |
|------|--------------------------|-------|
| Allocate EIP | `jdc --output json eip allocate-address --region-id cn-north-1 --address-name my-eip --bandwidth 10` | `--output json` BEFORE subcommand |
| Describe EIP | `jdc --output json eip describe-address --region-id cn-north-1 --address-id eip-xxx` | `--output json` BEFORE subcommand |
| List EIPs | `jdc --output json eip describe-addresses --region-id cn-north-1 --page-number 1 --page-size 100` | `--output json` BEFORE subcommand |
| Associate EIP | `jdc --output json eip associate-address --region-id cn-north-1 --address-id eip-xxx --instance-id vm-xxx --instance-type vm` | `--output json` BEFORE subcommand |
| Dissociate EIP | `jdc --output json eip dissociate-address --region-id cn-north-1 --address-id eip-xxx` | `--output json` BEFORE subcommand |
| Modify EIP | `jdc --output json eip modify-address --region-id cn-north-1 --address-id eip-xxx --address-name new-name --bandwidth 20` | `--output json` BEFORE subcommand |
| Release EIP | `jdc --output json eip release-address --region-id cn-north-1 --address-id eip-xxx` | `--output json` BEFORE subcommand |

## JSON Output Examples

### Allocate Address Response

```json
{
  "result": {
    "addressId": "eip-abc123",
    "publicIp": "106.xx.xx.xx",
    "addressName": "my-eip",
    "status": "available",
    "bandwidth": 10
  },
  "requestId": "req-xxx"
}
```

### Describe Address Response

```json
{
  "result": {
    "address": {
      "addressId": "eip-abc123",
      "publicIp": "106.xx.xx.xx",
      "addressName": "my-eip",
      "status": "in-use",
      "bandwidth": 10,
      "billingType": "pay-as-you-go",
      "instanceId": "vm-xxx",
      "instanceType": "vm",
      "createdTime": "2026-06-03T10:00:00+08:00"
    }
  },
  "requestId": "req-xxx"
}
```

### List Addresses Response

```json
{
  "result": {
    "addresses": [...],
    "totalCount": 5
  },
  "requestId": "req-xxx"
}
```

## CLI Configuration (Sandbox-Safe)

```bash
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc
cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = YOUR_ACCESS_KEY
secret_key = YOUR_SECRET_KEY
region_id = cn-north-1
endpoint = eip.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF
printf "%s" "default" > /tmp/jdc-home/.jdc/current
```

## Common CLI Flags

| Flag | Description | Required |
|------|-------------|----------|
| `--region-id` | Target region | Yes |
| `--address-id` | EIP ID | Yes (for describe, modify, associate, dissociate, release) |
| `--address-name` | EIP name | No (for allocate, modify) |
| `--bandwidth` | Bandwidth in Mbps | No (default: 5) |
| `--instance-id` | Target resource ID | Yes (for associate) |
| `--instance-type` | Resource type (vm/clb/nat) | Yes (for associate) |
| `--page-number` | Page number for list | No (default: 1) |
| `--page-size` | Page size for list | No (default: 10) |
