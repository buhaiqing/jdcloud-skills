# CLI Usage — JD Cloud Load Balancer (`jdc`)

> **ponytail: trimmed — key conventions + command map kept. SKILL.md covers execution flows.**

## Conventions

- `--output json` MUST be BEFORE subcommand: `jdc --output json lb <subcommand> ...`
- `--no-interactive` does NOT exist — omit it
- CLI reads credentials **only** from `~/.jdc/config` INI, NOT env vars

## Command Map

### Load Balancer Operations

| Operation | CLI Command |
|-----------|-------------|
| Create | `jdc --output json lb create-load-balancer --region-id <r> --load-balancer-name <n> --vpc-id <v> --subnet-id <s> --azs '["<az>"]' [--load-balancer-spec small\|medium\|large]` |
| Describe | `jdc --output json lb describe-load-balancer --region-id <r> --load-balancer-id <id>` |
| List | `jdc --output json lb describe-load-balancers --region-id <r> --page-number 1 --page-size 100` |
| Modify | `jdc --output json lb modify-load-balancer --region-id <r> --load-balancer-id <id> --load-balancer-name <n>` |
| Delete | `jdc --output json lb delete-load-balancer --region-id <r> --load-balancer-id <id>` |

### Listener Operations

| Operation | CLI Command |
|-----------|-------------|
| Create | `jdc --output json lb create-listener --region-id <r> --load-balancer-id <lb> --protocol <p> --port <port> --backend-port <bp>` |
| Describe | `jdc --output json lb describe-listeners --region-id <r> --load-balancer-id <lb>` |
| Modify | `jdc --output json lb modify-listener --region-id <r> --load-balancer-id <lb> --listener-id <li> --listener-name <n>` |
| Delete | `jdc --output json lb delete-listener --region-id <r> --load-balancer-id <lb> --listener-id <li>` |

### Target Operations

| Operation | CLI Command |
|-----------|-------------|
| Register | `jdc --output json lb register-targets --region-id <r> --load-balancer-id <lb> --target-group-id <tg> --target-specs '[{"instanceId":"<vm>","port":<p>,"weight":100}]'` |
| Deregister | `jdc --output json lb deregister-targets --region-id <r> --load-balancer-id <lb> --target-group-id <tg> --target-ids '["<t>"]'` |
| Describe | `jdc --output json lb describe-targets --region-id <r> --load-balancer-id <lb> --target-group-id <tg>` |

### Health Check Operations

| Operation | CLI Command |
|-----------|-------------|
| Update | `jdc --output json lb update-health-check --region-id <r> --load-balancer-id <lb> --listener-id <li> --health-check-spec '{"protocol":"<p>","port":<port>,"interval":5,"healthyThreshold":2,"unhealthyThreshold":3}'` |
| Describe | `jdc --output json lb describe-health-check --region-id <r> --load-balancer-id <lb> --listener-id <li>` |

## Polling Pattern

```bash
for i in $(seq 1 30); do
  STATUS=$(jdc --output json lb describe-load-balancer \
    --region-id cn-north-1 \
    --load-balancer-id lb-xxx 2>/dev/null | jq -r '.result.loadBalancer.status // "deleted"')
  [ "$STATUS" = "active" ] && break
  sleep 10
done
```

## Key JSON Response Paths

| Operation | Key Path |
|-----------|----------|
| Create LB | `$.result.loadBalancerId` |
| Describe LB | `$.result.loadBalancer.status` (active/inactive) |
| Describe LB | `$.result.loadBalancer.vip` (virtual IP) |
| Create Listener | `$.result.listenerId` |
| Describe Targets | `$.result.targets[*].healthStatus` (healthy/unhealthy) |