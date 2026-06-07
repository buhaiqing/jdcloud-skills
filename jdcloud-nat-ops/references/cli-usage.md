# CLI — JD Cloud NAT Gateway (`jdc vpc`)

## Overview

NAT Gateway operations are exposed under the `vpc` product group in the `jdc` CLI. This is because NAT Gateway is part of the JD Cloud VPC product line at the API level (`vpc.jdcloud-api.com`).

## Install and Config

- Install: see [JD Cloud CLI](https://github.com/jdcloud-api/jdcloud-cli)
- **CRITICAL:** The `jdc` CLI reads credentials exclusively from `~/.jdc/config` INI file, NOT from environment variables.
- For sandbox environments, redirect `HOME` and pre-create config files (see SKILL.md "Critical jdc CLI Behavioral Notes").

## Conventions (Agent Execution)

- `--output json` is a **top-level argument** — MUST be placed BEFORE the subcommand: `jdc --output json vpc <command> ...`
- `--no-interactive` does NOT exist in `jdc` CLI — all commands are non-interactive by default; omit this flag.
- NAT Gateway commands use `--nat-gateway-id` flag for resource identification.
- SNAT/DNAT rule specs are passed as JSON strings via `--snat-rule-spec` / `--dnat-rule-spec`.

## Command Map

| Goal | Example `jdc` Invocation | Notes |
|------|--------------------------|-------|
| List NAT Gateways | `jdc --output json vpc describe-nat-gateways --region-id cn-north-1 --page-number 1 --page-size 100` | Pagination available |
| Describe NAT Gateway | `jdc --output json vpc describe-nat-gateway --region-id cn-north-1 --nat-gateway-id nat-xxxxxx` | Single NAT detail |
| Create NAT Gateway | `jdc --output json vpc create-nat-gateway --region-id cn-north-1 --nat-gateway-name my-nat --vpc-id vpc-xxxxxx --elastic-ip-ids '["eip-xxxx"]'` | Requires existing VPC and EIP |
| Modify NAT Gateway | `jdc --output json vpc modify-nat-gateway --region-id cn-north-1 --nat-gateway-id nat-xxxxxx --nat-gateway-name new-name --description "..."` | Name and description only |
| Delete NAT Gateway | `jdc --output json vpc delete-nat-gateway --region-id cn-north-1 --nat-gateway-id nat-xxxxxx` | Irreversible! |
| Associate EIP | `jdc --output json vpc associate-nat-gateway --region-id cn-north-1 --nat-gateway-id nat-xxxxxx --elastic-ip-ids '["eip-xxxx"]'` | Add EIP to NAT |
| Disassociate EIP | `jdc --output json vpc disassociate-nat-gateway --region-id cn-north-1 --nat-gateway-id nat-xxxxxx --elastic-ip-ids '["eip-xxxx"]'` | Remove EIP from NAT |
| Create SNAT Rule | `jdc --output json vpc create-snat-rule --region-id cn-north-1 --nat-gateway-id nat-xxxxxx --snat-rule-spec '{"subnetId":"subnet-xxxx","elasticIpIds":["eip-xxxx"]}'` | JSON spec for rule |
| Delete SNAT Rule | `jdc --output json vpc delete-snat-rule --region-id cn-north-1 --nat-gateway-id nat-xxxxxx --snat-rule-id snat-xxxx` | Breaks subnet internet |
| Create DNAT Rule | `jdc --output json vpc create-dnat-rule --region-id cn-north-1 --nat-gateway-id nat-xxxxxx --dnat-rule-spec '{"protocol":"tcp","privateIp":"10.0.1.10","privatePort":"80","elasticIpId":"eip-xxxx","publicPort":"80"}'` | JSON spec for rule |
| Delete DNAT Rule | `jdc --output json vpc delete-dnat-rule --region-id cn-north-1 --nat-gateway-id nat-xxxxxx --dnat-rule-id dnat-xxxx` | Breaks port forwarding |

## JSON Output Path Map (after `--output json`)

| Operation | Response Path | Type | Description |
|-----------|---------------|------|-------------|
| Describe NAT Gateway | `$.result.natGateway.natGatewayId` | string | NAT gateway ID |
| Describe NAT Gateway | `$.result.natGateway.state` | string | Current state |
| Describe NAT Gateway | `$.result.natGateway.elasticIpAddresses` | array | Associated EIPs |
| Describe NAT Gateway | `$.result.natGateway.snatRuleCount` | integer | SNAT rule count |
| Describe NAT Gateway | `$.result.natGateway.dnatRuleCount` | integer | DNAT rule count |
| List NAT Gateways | `$.result.natGateways` | array | NAT GW list |
| List NAT Gateways | `$.result.totalCount` | integer | Total count |
| Create NAT Gateway | `$.result.natGatewayId` | string | New NAT GW ID |
| Create SNAT Rule | `$.result.snatRuleId` | string | New SNAT rule ID |
| Create DNAT Rule | `$.result.dnatRuleId` | string | New DNAT rule ID |
| Delete / Modify | `$.requestId` | string | Operation request ID |

## Coverage Gap

| Operation (API / SDK) | Available via `jdc`? | Notes |
|-----------------------|---------------------|-------|
| Create NAT Gateway | yes | `jdc vpc create-nat-gateway` |
| Describe NAT Gateway | yes | `jdc vpc describe-nat-gateway` |
| List NAT Gateways | yes | `jdc vpc describe-nat-gateways` |
| Modify NAT Gateway | yes | `jdc vpc modify-nat-gateway` |
| Delete NAT Gateway | yes | `jdc vpc delete-nat-gateway` |
| Associate EIP | yes | `jdc vpc associate-nat-gateway` |
| Disassociate EIP | yes | `jdc vpc disassociate-nat-gateway` |
| Create SNAT Rule | yes | `jdc vpc create-snat-rule` |
| Delete SNAT Rule | yes | `jdc vpc delete-snat-rule` |
| Create DNAT Rule | yes | `jdc vpc create-dnat-rule` |
| Delete DNAT Rule | yes | `jdc vpc delete-dnat-rule` |

> **No coverage gaps identified.** All NAT Gateway API operations are available through the `jdc` CLI under the `vpc` subcommand group.

## Troubleshooting CLI Commands

| Issue | Possible Cause | Fix |
|-------|---------------|-----|
| `unrecognized arguments: --output json` | `--output json` placed after subcommand | Move `--output json` before `vpc` |
| `Error: Config file not found` | `~/.jdc/config` missing | Create INI config file |
| `Permission denied` | `~/.jdc/` dir not writable | Set `HOME=/tmp/jdc-home` |
| `jdc: command not found` | CLI not installed | Run `uv pip install jdcloud_cli` |