# JD Cloud Cloud Assistant Guide

## Overview

Cloud Assistant (云助手) is a native automation operations tool for JD Cloud Virtual Machines. Without logging into instances or using passwords, you can batch-execute commands (Shell, PowerShell) on VMs to run automation scripts, manage services, install software, and more.

- **API Endpoint**: `assistant.jdcloud-api.com` (separate from VM API `vm.jdcloud-api.com`)
- **Cost**: Free of charge
- **Current Limitation**: CLI (`jdc`) does NOT currently support cloud assistant commands. Use **SDK/API** as the primary execution path.

## Core Concepts

| Concept | Description |
|---------|-------------|
| Cloud Assistant | The service that enables batch script execution for VM operations |
| Cloud Assistant Client | Agent installed inside each VM instance; all commands are executed through it |
| Command | An operational script (Shell or PowerShell) created and stored for reuse |
| Execution User | The user identity under which the command runs (default: `root` for Linux, `administrator` for Windows) |
| Working Directory | The path where the command is saved and executed on the VM |
| Custom Parameters | Variables defined via `{{key}}` in commands, resolved at invocation time with key-value pairs |
| Timeout | Maximum execution duration (range: 10-86400 seconds); command is force-terminated upon timeout |

## Command Execution States

### Instance-Level State
| State | Description |
|-------|-------------|
| `pending` | Command is being dispatched |
| `running` | Command is executing on the instance |
| `finish` | Command completed successfully (exit code 0) |
| `failed` | Command execution failed |
| `aborted` | Execution was aborted |
| `invalid` | Invalid execution request |
| `timeout` | Execution exceeded timeout |
| `terminated` | Process was terminated |
| `error` | An error occurred during execution |

### Aggregate State (Multi-Instance)
| State | Description |
|-------|-------------|
| `pending` | Command is being dispatched |
| `running` | Some or all instances are executing |
| `finished` | All instances completed successfully |
| `failed` | All instances failed |
| `partial_failed` | Mixed results: some succeeded, some failed |

## Supported Operating Systems

The cloud assistant client must be installed on VM instances. It supports both x86 and ARM architectures:

- **CentOS**: 6.9, 7.2-7.9, 8.2 (64-bit, x86); 7.9 (64-bit, ARM)
- **Windows Server**: 2012 R2, 2016, 2019 (64-bit, x86)
- **Ubuntu**: 14.04, 16.04, 18.04, 20.04 (64-bit, x86); 18.04, 20.04 (64-bit, ARM)
- **OpenEuler**: 21.09, 22.03 (x86 & ARM)
- **Rocky Linux**: 9.0 (x86); 8.6 (ARM)
- **OpenCloudOS**: 8.6 (ARM)

## SDK Operations Map

### Command Management

| Goal | API operationId | SDK Method | Endpoint Path |
|------|-----------------|------------|---------------|
| Create Command | `createCommand` | `AssistantClient.create_command()` | POST `/v1/regions/{regionId}/createCommand` |
| Describe Commands | `describeCommands` | `AssistantClient.describe_commands()` | POST `/v1/regions/{regionId}/describeCommands` |
| Delete Commands | `deleteCommands` | `AssistantClient.delete_commands()` | POST `/v1/regions/{regionId}/deleteCommands` |
| Invoke Command | `invokeCommand` | `AssistantClient.invoke_command()` | POST `/v1/regions/{regionId}/invokeCommand` |
| Describe Invocations | `describeInvocations` | `AssistantClient.describe_invocations()` | POST `/v1/regions/{regionId}/describeInvocations` |

> **Note**: `jdc` CLI does NOT support cloud assistant commands at this time. Use **SDK/API only**.

## SDK Initialization

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.assistant.client import AssistantClient

credential = Credential(
    os.environ['JDC_ACCESS_KEY'],
    os.environ['JDC_SECRET_KEY']
)

assistant_client = AssistantClient(credential, os.environ.get('JDC_REGION', 'cn-north-1'))
```

## Operation Details

### Operation: Create Command

Create a custom command that can be reused across multiple invocations.

**Request Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `commandName` | string | Yes | Command name, 1-128 chars. Allowed: Chinese, digits, letters, `_`, `-`, `.` |
| `commandType` | string | No | `shell` or `powershell` (default: `shell`) |
| `commandContent` | string | Yes | Base64-encoded command content, max 16KB after encoding. Supports `{{key}}` parameter placeholders (up to 20 params, each ≤ 64 bytes) |
| `timeout` | integer | No | Timeout in seconds [10-86400] (default: 60) |
| `username` | string | No | Execution user (default: `root` for Linux, `administrator` for Windows), max 256 chars |
| `workdir` | string | No | Working directory (default: `/root` for Linux, `C:\Windows\System32` for Windows), max 256 chars |
| `commandDescription` | string | No | Description, max 256 chars |
| `enableParameter` | boolean | No | Enable custom parameters (default: `False`) |

**Response**: Returns `commandId` in `$.result.commandId`.

**SDK Example**:
```python
import base64
from jdcloud_sdk.services.assistant.apis.CreateCommandRequest import CreateCommandRequest

command_content = base64.b64encode("hostname".encode()).decode()

request = CreateCommandRequest({
    "regionId": "cn-north-1",
    "commandName": "get-hostname",
    "commandType": "shell",
    "commandContent": command_content,
    "timeout": 60,
    "commandDescription": "Print the hostname of the VM"
})

response = assistant_client.create_command(request)
if response.error is None:
    print(f"Command created: {response.result.commandId}")
else:
    print(f"Error: {response.error.code} - {response.error.message}")
```

### Operation: Invoke Command

Execute a saved command on one or more VM instances.

**Request Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `commandId` | string | Yes | The command ID to execute |
| `instances` | string[] | Yes | VM instance IDs (max 50) |
| `timeout` | integer | No | Override timeout in seconds [10-86400] |
| `username` | string | No | Override execution user, max 256 chars |
| `workdir` | string | No | Override working directory, max 256 chars |
| `windowsPassword` | string | No | Password for Windows non-administrator users |
| `enableParameter` | boolean | No | Enable custom parameters (default: `False`) |
| `parameters` | object[] | No | Custom parameter key-value pairs (max 20) |

**Response**: Returns `invokeId` in `$.result.invokeId`.

**SDK Example**:
```python
from jdcloud_sdk.services.assistant.apis.InvokeCommandRequest import InvokeCommandRequest

request = InvokeCommandRequest({
    "regionId": "cn-north-1",
    "commandId": "cmd-xxxxxxxx",
    "instances": ["i-xxxxxxxx", "i-yyyyyyyy"],
    "timeout": 120,
    "enableParameter": True,
    "parameters": [
        {"key": "name", "value": "production"},
        {"key": "env", "value": "prd"}
    ]
})

response = assistant_client.invoke_command(request)
if response.error is None:
    print(f"Command invoked: {response.result.invokeId}")
else:
    print(f"Error: {response.error.code} - {response.error.message}")
```

### Operation: Describe Commands

Query created custom commands with optional filters.

**Request Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pageNumber` | integer | No | Page number (default: 1) |
| `pageSize` | integer | No | Page size (default: 20, max: 100) |
| `commandIds` | string[] | No | Filter by command IDs |
| `commandNames` | string[] | No | Filter by command names |
| `commandTypes` | string[] | No | Filter by type: `shell` or `powershell` |
| `sourceType` | string | No | Source: `jdcloud` (official) or `self` (private, default) |
| `usernames` | string[] | No | Filter by execution username |

**Response**: Returns `commands` array and `totalCount` in `$.result`.

**SDK Example**:
```python
from jdcloud_sdk.services.assistant.apis.DescribeCommandsRequest import DescribeCommandsRequest

request = DescribeCommandsRequest({
    "regionId": "cn-north-1",
    "pageNumber": 1,
    "pageSize": 20,
    "commandTypes": ["shell"]
})

response = assistant_client.describe_commands(request)
if response.error is None:
    for cmd in response.result.commands:
        print(f"Command: {cmd.commandId} - {cmd.commandName} ({cmd.commandType})")
else:
    print(f"Error: {response.error.code} - {response.error.message}")
```

### Operation: Delete Commands

Delete one or more custom commands.

**Request Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `commandIds` | string[] | Yes | Command IDs to delete |

**SDK Example**:
```python
from jdcloud_sdk.services.assistant.apis.DeleteCommandsRequest import DeleteCommandsRequest

request = DeleteCommandsRequest({
    "regionId": "cn-north-1",
    "commandIds": ["cmd-xxxxxxxx"]
})

response = assistant_client.delete_commands(request)
if response.error is None:
    print("Commands deleted successfully")
else:
    print(f"Error: {response.error.code} - {response.error.message}")
```

### Operation: Describe Invocations

Query command execution results and status.

**Request Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pageNumber` | integer | No | Page number (default: 1) |
| `pageSize` | integer | No | Page size (default: 20, max: 100) |
| `invokeIds` | string[] | No | Filter by invocation IDs |
| `commandIds` | string[] | No | Filter by command IDs |
| `status` | string[] | No | Filter by status: `pending`, `running`, `failed`, `partial_failed`, `finished` |
| `commandNames` | string[] | No | Filter by command names |
| `commandTypes` | string[] | No | Filter by type: `shell` or `powershell` |
| `userNames` | string[] | No | Filter by execution username |

**Response Fields** (`InvocationInstance` per instance):
| Field | Description |
|-------|-------------|
| `instanceId` | VM instance ID |
| `instanceName` | VM instance name |
| `status` | Per-instance execution status |
| `exitCode` | Command exit code (0 = success) |
| `errorInfo` | Error message if failed |
| `startTime` | Execution start time |
| `endTime` | Execution end time |
| `output` | Command output (max 6000B, truncated with head 5000B + tail 1000B if exceeded) |
| `duration` | Execution duration in seconds |
| `createTime` | Task creation time |

**SDK Example**:
```python
from jdcloud_sdk.services.assistant.apis.DescribeInvocationsRequest import DescribeInvocationsRequest

request = DescribeInvocationsRequest({
    "regionId": "cn-north-1",
    "invokeIds": ["t-xxxxxxxx"],
    "pageNumber": 1,
    "pageSize": 20
})

response = assistant_client.describe_invocations(request)
if response.error is None:
    for inv in response.result.invocations:
        print(f"Invoke: {inv.invokeId} - Status: {inv.status}")
        for inst in inv.invocationInstances:
            print(f"  Instance: {inst.instanceId} - Status: {inst.status}")
            print(f"  ExitCode: {inst.exitCode}")
            print(f"  Output: {inst.output}")
else:
    print(f"Error: {response.error.code} - {response.error.message}")
```

## Error Handling

### Common Error Codes

| Code | HTTP Status | Description | Agent Action |
|------|-------------|-------------|--------------|
| `INVALID_ARGUMENT` | 400 | Missing or invalid parameter | Check field values per spec, retry once |
| `OUT_OF_RANGE` | 400 | Parameter value out of allowed range | Adjust value to valid range |
| `NOT_FOUND` | 404 | Command or invocation not found | Verify resource ID exists |
| `QUOTA_EXCEEDED` | 429 | Command quota exceeded | HALT; suggest deleting unused commands |
| `INTERNAL` | 500 | Internal server error | Retry with exponential backoff (3x) |
| `UNKNOWN` | 500 | Unknown server error | Retry with exponential backoff (3x) |

### SDK Error Handling Pattern

```python
try:
    response = assistant_client.create_command(request)
    if response.error is not None:
        print(f"API Error: {response.error.code} - {response.error.message}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Polling for Command Results

After invoking a command, poll `describeInvocations` to check completion:

```python
import time

invoke_id = response.result.invokeId
max_wait = 300  # seconds
interval = 5

for _ in range(max_wait // interval):
    time.sleep(interval)
    check_req = DescribeInvocationsRequest({
        "regionId": "cn-north-1",
        "invokeIds": [invoke_id]
    })
    check_resp = assistant_client.describe_invocations(check_req)
    if check_resp.error is not None:
        break
    inv = check_resp.result.invocations[0]
    if inv.status in ("finished", "failed", "partial_failed"):
        break
```

## Best Practices

1. **Install the cloud assistant client** on all target VMs before using — it is not installed by default on older instances.
2. **Test commands on a single VM** before batch execution.
3. **Set reasonable timeouts** appropriate for the command type (e.g., 60s for quick checks, 300s+ for software installs).
4. **Always poll for results** — command invocation is asynchronous and returns only an `invokeId`.
5. **Check exit codes** (not just status) — exit code 0 indicates success.
6. **Use custom parameters** for reusable commands across different environments.
7. **Clean up unused commands** to stay within quota limits.

## Limitations

- **CLI Not Supported**: `jdc` does not support cloud assistant operations. Use SDK/API only.
- **Client Required**: The cloud assistant client agent must be installed on each target VM instance.
- **Instance State**: VMs must be in `running` state with the cloud assistant client installed and healthy.
- **Per-Invocation Instance Limit**: Maximum 50 VM instances per `invokeCommand` call.
- **Command Content Size**: Maximum 16KB after base64 encoding (approximately 12KB raw).
- **Custom Parameters**: Maximum 20 parameters per command, each key/value ≤ 64 bytes.
- **Output Truncation**: Command output is limited to 6000 bytes in query results.
