# CLI — JD Cloud VPN (`jdc vpn`)

## Install and Config

- Install: see [JD Cloud CLI](https://github.com/jdcloud-api/jdcloud-cli)
- **CRITICAL:** The `jdc` CLI reads credentials exclusively from `~/.jdc/config` INI file, NOT from environment variables.
- For sandbox environments, redirect `HOME` and pre-create config files.

## Conventions (agent execution)

- `--output json` is a **top-level argument** — MUST be placed BEFORE the subcommand: `jdc --output json vpn <command> ...`
- `--no-interactive` does NOT exist in `jdc` CLI — all commands are non-interactive by default; omit this flag.
- Document **exact** JSON paths after verifying with a real invocation.

## CLI vs API Coverage Gap

| Operation (API / SDK) | Available via `jdc`? | Notes |
|------------------------|---------------------|-------|
| Create VpnGateway | yes | `jdc vpn create-vpn-gateway` |
| Describe VpnGateway | yes | `jdc vpn describe-vpn-gateway` |
| List VpnGateways | yes | `jdc vpn describe-vpn-gateways` |
| Delete VpnGateway | yes | `jdc vpn delete-vpn-gateway` |
| Create CustomerGateway | yes | `jdc vpn create-customer-gateway` |
| Describe CustomerGateway | yes | `jdc vpn describe-customer-gateway` |
| List CustomerGateways | yes | `jdc vpn describe-customer-gateways` |
| Delete CustomerGateway | yes | `jdc vpn delete-customer-gateway` |
| Create VpnConnection | yes | `jdc vpn create-vpn-connection` |
| Describe VpnConnection | yes | `jdc vpn describe-vpn-connection` |
| List VpnConnections | yes | `jdc vpn describe-vpn-connections` |
| Delete VpnConnection | yes | `jdc vpn delete-vpn-connection` |

> As of CLI version 1.2.12, all primary VPN operations are exposed via `jdc vpn`. If additional operations (e.g., modify) are added to the API but not the CLI, document them in the gap table above.

## Command Map

### VpnGateway

```bash
# Create
jdc --output json vpn create-vpn-gateway \
  --region-id <region> \
  --vpn-gateway-name <name> \
  --vpc-id <vpc-id> \
  --description <desc>

# Describe single
jdc --output json vpn describe-vpn-gateway \
  --region-id <region> \
  --vpn-gateway-id <id>

# List
jdc --output json vpn describe-vpn-gateways \
  --region-id <region> \
  --page-number 1 \
  --page-size 100

# Delete
jdc --output json vpn delete-vpn-gateway \
  --region-id <region> \
  --vpn-gateway-id <id>
```

### CustomerGateway

```bash
# Create
jdc --output json vpn create-customer-gateway \
  --region-id <region> \
  --customer-gateway-name <name> \
  --ip-address <public-ip> \
  --description <desc>

# Describe single
jdc --output json vpn describe-customer-gateway \
  --region-id <region> \
  --customer-gateway-id <id>

# List
jdc --output json vpn describe-customer-gateways \
  --region-id <region> \
  --page-number 1 \
  --page-size 100

# Delete
jdc --output json vpn delete-customer-gateway \
  --region-id <region> \
  --customer-gateway-id <id>
```

### VpnConnection

```bash
# Create
jdc --output json vpn create-vpn-connection \
  --region-id <region> \
  --vpn-connection-name <name> \
  --vpn-gateway-id <vgw-id> \
  --customer-gateway-id <cgw-id> \
  --ike-version <v1|v2> \
  --psk <psk> \
  --local-subnets '["10.0.0.0/16"]' \
  --remote-subnets '["192.168.0.0/16"]'

# Describe single
jdc --output json vpn describe-vpn-connection \
  --region-id <region> \
  --vpn-connection-id <id>

# List
jdc --output json vpn describe-vpn-connections \
  --region-id <region> \
  --page-number 1 \
  --page-size 100

# Delete
jdc --output json vpn delete-vpn-connection \
  --region-id <region> \
  --vpn-connection-id <id>
```

## Sandbox Config Setup

```bash
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc
cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = YOUR_ACCESS_KEY
secret_key = YOUR_SECRET_KEY
region_id = cn-north-1
endpoint = vpn.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF
printf "%s" "default" > /tmp/jdc-home/.jdc/current
```

## Quick Verify

```bash
jdc --output json vpn describe-vpn-gateways --region-id cn-north-1 --page-number 1 --page-size 1
```