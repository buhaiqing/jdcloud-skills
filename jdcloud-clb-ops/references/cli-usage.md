# CLI — JD Cloud Load Balancer (CLB) (`jdc`)

## Install and Config

- Install: see [JD Cloud CLI](https://github.com/jdcloud-api/jdcloud-cli)
- **CRITICAL:** The `jdc` CLI reads credentials exclusively from `~/.jdc/config` INI file, NOT from environment variables.
- For sandbox environments, redirect `HOME` and pre-create config files (see generator SKILL.md "Critical jdc CLI Behavioral Notes").

## Conventions (Agent Execution)

- `--output json` is a **top-level argument** — MUST be placed BEFORE the subcommand: `jdc --output json lb <command> ...`
- `--no-interactive` does NOT exist in `jdc` CLI — all commands are non-interactive by default; omit this flag.
- Document **exact** JSON paths after verifying with a real invocation (CLI output may differ from raw API).

## CLI vs API Coverage Gap

| Operation (API / SDK) | Available via `jdc`? | Notes |
|------------------------|---------------------|-------|
| Create Load Balancer | Yes | `lb create-load-balancer` |
| Describe Load Balancer | Yes | `lb describe-load-balancer` |
| Describe Load Balancers | Yes | `lb describe-load-balancers` |
| Modify Load Balancer | Yes | `lb modify-load-balancer` |
| Delete Load Balancer | Yes | `lb delete-load-balancer` |
| Create Listener | Yes | `lb create-listener` |
| Describe Listeners | Yes | `lb describe-listeners` |
| Modify Listener | Yes | `lb modify-listener` |
| Delete Listener | Yes | `lb delete-listener` |
| Register Targets | Yes | `lb register-targets` |
| Deregister Targets | Yes | `lb deregister-targets` |
| Describe Targets | Yes | `lb describe-targets` |
| Update Health Check | Yes | `lb update-health-check` |
| Describe Health Check | Yes | `lb describe-health-check` |

## Command Map

### Load Balancer Operations

| Goal | Example `jdc` Invocation | Notes |
|------|--------------------------|-------|
| Create LB | `jdc --output json lb create-load-balancer --region-id <region> --load-balancer-name <name> --vpc-id <vpc> --subnet-id <subnet> --azs '["<az>"]'` | `--output json` BEFORE subcommand |
| Describe LB | `jdc --output json lb describe-load-balancer --region-id <region> --load-balancer-id <lb-id>` | Returns LB details |
| List LBs | `jdc --output json lb describe-load-balancers --region-id <region> --page-number 1 --page-size 100` | Supports pagination |
| Modify LB | `jdc --output json lb modify-load-balancer --region-id <region> --load-balancer-id <lb-id> --load-balancer-name <new-name>` | Update LB attributes |
| Delete LB | `jdc --output json lb delete-load-balancer --region-id <region> --load-balancer-id <lb-id>` | Irreversible operation |

### Listener Operations

| Goal | Example `jdc` Invocation | Notes |
|------|--------------------------|-------|
| Create Listener | `jdc --output json lb create-listener --region-id <region> --load-balancer-id <lb-id> --protocol <protocol> --port <port> --backend-port <backend-port>` | Protocol: tcp/udp/http/https |
| Describe Listeners | `jdc --output json lb describe-listeners --region-id <region> --load-balancer-id <lb-id>` | List all listeners |
| Modify Listener | `jdc --output json lb modify-listener --region-id <region> --load-balancer-id <lb-id> --listener-id <listener-id> --listener-name <new-name>` | Update listener attributes |
| Delete Listener | `jdc --output json lb delete-listener --region-id <region> --load-balancer-id <lb-id> --listener-id <listener-id>` | Remove listener |

### Target Operations

| Goal | Example `jdc` Invocation | Notes |
|------|--------------------------|-------|
| Register Targets | `jdc --output json lb register-targets --region-id <region> --load-balancer-id <lb-id> --target-group-id <tg-id> --target-specs '[{"instanceId":"<vm-id>","port":<port>,"weight":<weight>}]'` | Add backend servers |
| Deregister Targets | `jdc --output json lb deregister-targets --region-id <region> --load-balancer-id <lb-id> --target-group-id <tg-id> --target-ids '["<target-id>"]'` | Remove backend servers |
| Describe Targets | `jdc --output json lb describe-targets --region-id <region> --load-balancer-id <lb-id> --target-group-id <tg-id>` | List backend servers and health |

### Health Check Operations

| Goal | Example `jdc` Invocation | Notes |
|------|--------------------------|-------|
| Update Health Check | `jdc --output json lb update-health-check --region-id <region> --load-balancer-id <lb-id> --listener-id <listener-id> --health-check-spec '<json-spec>'` | Configure health checks |
| Describe Health Check | `jdc --output json lb describe-health-check --region-id <region> --load-balancer-id <lb-id> --listener-id <listener-id>` | Get health check config |

## JSON Response Paths

### Create Load Balancer
```json
{
  "requestId": "req-xxx",
  "result": {
    "loadBalancerId": "lb-xxx"
  }
}
```
**Key paths:**
- `$.result.loadBalancerId` — New load balancer ID

### Describe Load Balancer
```json
{
  "requestId": "req-xxx",
  "result": {
    "loadBalancer": {
      "loadBalancerId": "lb-xxx",
      "loadBalancerName": "my-lb",
      "status": "active",
      "vip": "10.0.0.1",
      "vpcId": "vpc-xxx",
      "subnetId": "subnet-xxx",
      "azs": ["cn-north-1a"],
      "createdTime": "2026-05-06T10:00:00+08:00"
    }
  }
}
```
**Key paths:**
- `$.result.loadBalancer.loadBalancerId` — LB ID
- `$.result.loadBalancer.status` — LB status (active/inactive)
- `$.result.loadBalancer.vip` — Virtual IP address

### Describe Load Balancers (List)
```json
{
  "requestId": "req-xxx",
  "result": {
    "loadBalancers": [
      {
        "loadBalancerId": "lb-xxx",
        "loadBalancerName": "my-lb",
        "status": "active"
      }
    ],
    "totalCount": 1
  }
}
```
**Key paths:**
- `$.result.loadBalancers[*].loadBalancerId` — Array of LB IDs
- `$.result.totalCount` — Total number of LBs

### Create Listener
```json
{
  "requestId": "req-xxx",
  "result": {
    "listenerId": "listener-xxx"
  }
}
```
**Key paths:**
- `$.result.listenerId` — New listener ID

### Describe Targets
```json
{
  "requestId": "req-xxx",
  "result": {
    "targets": [
      {
        "targetId": "target-xxx",
        "instanceId": "vm-xxx",
        "port": 8080,
        "weight": 100,
        "healthStatus": "healthy"
      }
    ]
  }
}
```
**Key paths:**
- `$.result.targets[*].targetId` — Target ID
- `$.result.targets[*].healthStatus` — Health status (healthy/unhealthy)

## Common CLI Patterns

### Sandbox Setup (Before Running Commands)

```bash
# Setup jdc config in a writable location
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc
cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = YOUR_ACCESS_KEY
secret_key = YOUR_SECRET_KEY
region_id = cn-north-1
endpoint = lb.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF
printf "%s" "default" > /tmp/jdc-home/.jdc/current
```

### Polling for Status

```bash
# Poll until LB is active
for i in $(seq 1 30); do
  STATUS=$(jdc --output json lb describe-load-balancer \
    --region-id "cn-north-1" \
    --load-balancer-id "lb-xxx" | jq -r '.result.loadBalancer.status')
  [ "$STATUS" = "active" ] && break
  sleep 10
done
```

### Extracting Values with jq

```bash
# Get LB ID from create response
LB_ID=$(jdc --output json lb create-load-balancer ... | jq -r '.result.loadBalancerId')

# Get all LB IDs from list
LB_IDS=$(jdc --output json lb describe-load-balancers --region-id cn-north-1 | jq -r '.result.loadBalancers[].loadBalancerId')
```
