# JD Cloud VM API & SDK Usage Reference

> **ponytail: trimmed — operation map kept; verbose examples removed (SKILL.md covers execution flows).**

## OpenAPI Reference

- **API Docs**: https://docs.jdcloud.com/cn/virtual-machines/api
- **SDK**: `jdcloud_sdk >= 1.6.26`

## SDK Operations Map

### Instance Operations

| Goal | SDK Method | CLI Command |
|------|------------|-------------|
| Create | `VmClient.create_instances()` | `jdc vm create-instances` |
| Describe | `VmClient.describe_instances()` | `jdc vm describe-instances` |
| Start | `VmClient.start_instance()` | `jdc vm start-instance` |
| Stop | `VmClient.stop_instance()` | `jdc vm stop-instance` |
| Reboot | `VmClient.reboot_instance()` | `jdc vm reboot-instance` |
| Delete | `VmClient.delete_instance()` | `jdc vm delete-instance` |
| Resize | `VmClient.resize_instance()` | `jdc vm resize-instance` |
| List Types | `VmClient.describe_instance_types()` | `jdc vm describe-instance-types` |
| List AZs | `VmClient.describe_azs()` | `jdc vm describe-azs` |
| Describe Quota | `VmClient.describe_quota()` | `jdc vm describe-quota` |

### Image Operations

| SDK Method | CLI Command |
|------------|-------------|
| `VmClient.describe_images()` | `jdc vm describe-images` |
| `VmClient.create_image()` | `jdc vm create-image` |
| `VmClient.delete_image()` | `jdc vm delete-image` |

### Key Pair Operations

| SDK Method | CLI Command |
|------------|-------------|
| `VmClient.create_keypair()` | `jdc vm create-keypair` |
| `VmClient.describe_keypairs()` | `jdc vm describe-keypairs` |
| `VmClient.import_keypair()` | `jdc vm import-keypair` |
| `VmClient.delete_keypair()` | `jdc vm delete-keypair` |

### Cloud Assistant (SDK-only — `jdc` CLI not supported)

| SDK Method |
|------------|
| `AssistantClient.create_command()` |
| `AssistantClient.describe_commands()` |
| `AssistantClient.delete_commands()` |
| `AssistantClient.invoke_command()` |
| `AssistantClient.describe_invocations()` |

## Instance Status Values

| Status | Description |
|--------|-------------|
| `creating` | Being created |
| `running` | Running normally |
| `stopped` | Stopped |
| `stopping` | Stopping |
| `starting` | Starting |
| `rebooting` | Rebooting |
| `deleting` | Being deleted |
| `error` | Error state |

## Idempotency Notes

| Operation | Idempotent? | Notes |
|-----------|-------------|-------|
| Create | No | Use unique name or check-exists before create |
| Start/Stop/Reboot | Yes | State machine guards duplicates |
| Delete | Yes | Safe to retry; 404 on already-deleted |
| Resize | No | Check current state before resize |