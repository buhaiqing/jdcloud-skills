# JD Cloud VM CLI Usage Reference

> **ponytail: heavily trimmed — SKILL.md covers CLI conventions, prereqs, and execution flows.**
> This file is a compact operation-to-command mapping. For full flow details, see [SKILL.md](../SKILL.md).

## VM Instance Commands

| Operation | CLI Command |
|-----------|-------------|
| Create | `jdc --output json vm create-instances --region-id <region> --az <az> --instance-type <type> --image-id <img> --name <name> --primary-network-interface '{"subnetId":"...","securityGroupIds":["..."]}' --system-disk '{"diskCategory":"...","diskSizeGB":40}' --charge-mode postpaid_by_duration` |
| Describe | `jdc --output json vm describe-instances --region-id <region> --instance-ids '["i-xxx"]'` |
| List | `jdc --output json vm describe-instances --region-id <region> --page-number 1 --page-size 100 [--filters '[...]']` |
| Start | `jdc --output json vm start-instance --region-id <region> --instance-id i-xxx` |
| Stop | `jdc --output json vm stop-instance --region-id <region> --instance-id i-xxx [--force-stop true]` |
| Reboot | `jdc --output json vm reboot-instance --region-id <region> --instance-id i-xxx [--force-reboot true]` |
| Delete | `jdc --output json vm delete-instance --region-id <region> --instance-id i-xxx [--delete-data-disks true] [--delete-snapshot true]` |
| Resize | `jdc --output json vm resize-instance --region-id <region> --instance-id i-xxx --instance-type g.n2.large` |
| Describe Types | `jdc --output json vm describe-instance-types --region-id <region>` |
| Describe Quota | `jdc --output json vm describe-quota --region-id <region>` |
| Describe AZs | `jdc --output json vm describe-azs --region-id <region>` |

## Image Commands

| Operation | CLI Command |
|-----------|-------------|
| List Images | `jdc --output json vm describe-images --region-id <region> [--owners official\|self]` |
| Create Image | `jdc --output json vm create-image --region-id <region> --instance-id i-xxx --name <name>` |
| Delete Image | `jdc --output json vm delete-image --region-id <region> --image-id img-xxx` |

## Key Pair Commands

| Operation | CLI Command |
|-----------|-------------|
| Create | `jdc --output json vm create-keypair --region-id <region> --key-name <name> [--description "..."]` |
| List | `jdc --output json vm describe-keypairs --region-id <region>` |
| Import | `jdc --output json vm import-keypair --region-id <region> --key-name <name> --public-key "<ssh-rsa AAAA...>"` |
| Delete | `jdc --output json vm delete-keypair --region-id <region> --key-name <name>` |

## Resource State Polling

```bash
# Poll until status matches (e.g., running / stopped / deleted → 404)
for i in $(seq 1 60); do
  STATUS=$(jdc --output json vm describe-instances \
    --region-id cn-north-1 \
    --instance-ids '["i-xxx"]' 2>/dev/null | jq -r '.result.instances[0].status // "deleted"')
  [ "$STATUS" = "running" ] && break
  sleep 5
done
```

## Related Skills (cross-skill commands)

| Resource | Skill | Example |
|----------|-------|---------|
| Disk | `jdcloud-disk-ops` | `jdc --output json disk describe-disks --region-id <region> --disk-ids '["vol-xxx"]'` |
| Security Group | `jdcloud-vpc-ops` | `jdc --output json vpc describe-security-group --region-id <region> --security-group-id sg-xxx` |
| EIP | `jdcloud-eip-ops` | `jdc --output json vpc describe-elastic-ips --region-id <region>` |