---
name: jdcloud-jcq-ops
description: >-
  Use this skill for JD Cloud JCQ (消息队列服务) management — create and manage
  Topics (主题), ConsumerGroups (消费组), and Messages (消息). Apply when the
  user mentions JCQ, 消息队列, 主题, topic, 消费组, consumer group, 消息,
  message, 消息服务, message queue, or asks about producing/consuming messages
  on JD Cloud JCQ.
license: MIT
compatibility: >-
  Official JD Cloud Python SDK (Python 3.10+), valid API credentials, network
  access to JCQ endpoints. **JCQ is NOT supported by the `jdc` CLI** —
  execution is SDK-only.
metadata:
  author: jdcloud
  version: "1.0.0"
  last_updated: "2026-06-08"
  runtime: Harness AI Agent
  api_profile: "JD Cloud JCQ API v1 - https://jcq.jdcloud-api.com/v1"
  cli_applicability: sdk-only
  cli_version_locked: N/A
  sdk_version_locked: ">=1.6.26"
  cli_support_evidence: >-
    JCQ is NOT exposed via `jdc` CLI. Confirmed via `jdc --help | grep -i jcq`
    returning no output. The `jdc` CLI (`jdcloud_cli==1.2.12`) does not include
    a `jcq` product group. All JCQ operations MUST use the Python SDK
    (`jdcloud_sdk.services.jcq.client.JcqClient`) or direct HTTP API calls.
  gcl_classification: recommended
  gcl_max_iter: 3
  environment:
    - JDC_ACCESS_KEY
    - JDC_SECRET_KEY
    - JDC_REGION
---

> This skill follows the [Agent Skill OpenSpec](https://agentskills.io/specification).

# JD Cloud JCQ (消息队列服务) Operations Skill

## Overview

JD Cloud JCQ (消息队列服务) is a managed distributed messaging service that provides high-throughput, low-latency, and reliable message transmission. It supports publish-subscribe (Topic) and point-to-point messaging models, with message persistence, retry mechanisms, and consumer group management. This skill is an **operational runbook** for agents: explicit scope, credential rules, pre-flight checks, **SDK-only execution** (JCQ is NOT exposed via `jdc` CLI), response validation, and failure recovery. **Do not use the web console as the primary agent execution path** in `SKILL.md`.

### CLI applicability (repository policy)

- **`cli_applicability: sdk-only`:** The `jdc` CLI does NOT support JCQ operations. The Agent MUST use the **Python SDK** (`jdcloud_sdk.services.jcq.client.JcqClient`) as the **sole execution path**. There is no `jdc` fallback. All JCQ operations are performed via the JCQ API at `jcq.jdcloud-api.com`.

### Path Preference (SDK-only)

The Agent MUST follow this execution priority:

1. **Python SDK (sole path)** — Use `jdcloud_sdk.services.jcq.client.JcqClient` for all JCQ operations.
2. **Retry up to 3 times** if SDK call fails (with exponential backoff: 0s → 2s → 4s).
3. **HTTP API (direct, after 3 SDK failures)** — Use direct HTTP calls to `https://jcq.jdcloud-api.com/v1` as a last resort.

> **Important:** The `jdc` CLI (`jdcloud_cli==1.2.12`) does NOT include a `jcq` product group. Do NOT attempt to run `jdc` commands for JCQ operations. This is confirmed via `jdc --help | grep -i jcq` returning no output.

## Trigger & Scope (Agent-Readable)

### SHOULD Use This Skill When

- User mentions "JD Cloud JCQ" OR "消息队列" OR "消息队列服务" OR "JCQ"
- Task involves CRUD operations on **Topics** (主题): create, list, describe, delete
- Task involves CRUD operations on **ConsumerGroups** (消费组): create, list, describe, delete
- Task involves **Message** operations: send (produce), receive (consume), describe messages
- Task keywords: createTopic, deleteTopic, describeTopics, createConsumerGroup, deleteConsumerGroup, describeConsumerGroups, sendMessage, receiveMessage, describeMessages, messageTag, messageRetry
- User asks to produce, consume, publish, subscribe, or manage messages on JD Cloud JCQ
- User asks about topic partitioning, consumer group offsets, message retention, or dead-letter queues

### SHOULD NOT Use This Skill When

- Task is purely billing / account management → delegate to: `jdcloud-billing-ops` (when present)
- Task is IAM / permission model only → delegate to: `jdcloud-iam-ops`
- Task is about VPC / subnet / security group → delegate to: `jdcloud-vpc-ops`
- Task is about monitoring metrics / alarms → delegate to: `jdcloud-cloudmonitor-ops`
- Task is about KMS encryption key management → delegate to: `jdcloud-kms-ops`
- User insists on **console-only** flows with no API → state limitation; do not invent undocumented HTTP steps

### Delegation Rules

- If JCQ requires VPC endpoint or security group rules, delegate network config to `jdcloud-vpc-ops`.
- If user asks about JCQ monitoring metrics or alarm rules, delegate metric query to `jdcloud-cloudmonitor-ops`.
- If user asks about IAM policies for JCQ access control, delegate to `jdcloud-iam-ops`.
- If user asks about KMS encryption for JCQ topics, delegate to `jdcloud-kms-ops`.
- Multi-product requests: handle each product with its skill; do not merge unrelated APIs into one ambiguous flow.

## Variable Convention (Agent-Readable)

Structured placeholders reduce injection ambiguity and unsafe prompts:

| Placeholder | Meaning | Agent Action |
|-------------|---------|--------------|
| `{{env.JDC_ACCESS_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_SECRET_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_REGION}}` | From runtime environment | Use `cn-north-1` as default if unset |
| `{{user.region}}` | User-supplied region | Ask once; reuse |
| `{{user.topic_name}}` | User-supplied topic name | Ask once; reuse |
| `{{user.consumer_group_name}}` | User-supplied consumer group name | Ask once; reuse |
| `{{user.message_body}}` | User-supplied message body/content | Ask once; reuse |
| `{{user.message_tag}}` | User-supplied message tag (optional filter) | Ask once; reuse |
| `{{output.topic_id}}` | From last API JSON response | Parse from `$.result.topicId` or `$.result.topicName` |
| `{{output.consumer_group_id}}` | From last API JSON response | Parse from `$.result.consumerGroupId` |
| `{{output.message_id}}` | From last API JSON response | Parse from `$.result.messageId` |

> **`{{env.*}}` MUST NOT** be collected from the user. **`{{user.*}}`** MUST be collected interactively when missing.

> **Security Warning:** **NEVER** log, print, or expose `JDC_SECRET_KEY` (or any secret) in console output, debug messages, or logs. When verification is needed, check existence only (e.g., `if os.environ.get('JDC_SECRET_KEY')`) without printing the actual value. If logging credential status is required, use masked placeholders like `JDC_SECRET_KEY=<masked>` or `JDC_SECRET_KEY=***`. This applies to all execution flows (SDK and debugging scripts).

## API and Response Conventions (Agent-Readable)

- **OpenAPI is canonical** for path, query, body fields, enums, and response shapes. Base path: `https://jcq.jdcloud-api.com/v1`
- **Errors:** Map SDK/HTTP errors to `code` / `status` / message fields per spec.
- **Timestamps:** ISO 8601 with timezone when the API returns strings (e.g. `2026-06-01T10:00:00+08:00`).
- **Idempotency:** Creating a topic with the same name in the same region returns `ResourceAlreadyExists`. Sending the same message body produces a new message with a unique `messageId`.

### Example Response Field Table

| Operation | JSON Path (API) | Type | Description |
|-----------|----------------|------|-------------|
| Create Topic | `$.result.topicName` | string | New topic name |
| Describe Topics | `$.result.topics[*].topicName` | array | All topic names |
| Describe Topics | `$.result.topics[*].topicStatus` | string | Topic lifecycle state |
| Create ConsumerGroup | `$.result.consumerGroupId` | string | New consumer group ID |
| Describe ConsumerGroups | `$.result.consumerGroups[*].consumerGroupId` | array | Consumer group IDs |
| Send Message | `$.result.messageId` | string | Unique message ID |
| Receive Message | `$.result.messages[*].messageId` | array | Received message IDs |
| Describe Messages | `$.result.messages[*].messageId` | array | Message IDs matching query |

### Expected State Transitions

| Operation | Initial State | Target State | Poll Interval | Max Wait |
|-----------|---------------|--------------|---------------|----------|
| Create Topic | — | topic active | 5s | 60s |
| Delete Topic | topic exists | (404 on describe) | 5s | 120s |
| Create ConsumerGroup | — | consumer group active | 5s | 60s |
| Delete ConsumerGroup | consumer group exists | (404 on describe) | 5s | 120s |
| Send Message | — | message persisted | 2s | 30s |

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-06-08 | Initial version: SDK-only execution path for JCQ Topic CRUD, ConsumerGroup CRUD, Message send/receive/describe; GCL rollout with rubric v1 and prompt templates; safety gates for destructive ops |

## Execution Flows (Agent-Readable)

Every operation: **Pre-flight → Execute (SDK) → Validate → Recover**. Do not skip phases.

**SDK-only strategy:** JCQ is NOT supported by the `jdc` CLI. The Agent MUST use the Python SDK exclusively. If SDK calls fail after **3 retries** with exponential backoff, fall back to direct HTTP API calls.

### Prerequisites: SDK-only Setup

```bash
uv venv --python 3.10
source .venv/bin/activate
uv pip install jdcloud_sdk>=1.6.26
python -c "
import jdcloud_sdk
from jdcloud_sdk.services.jcq.client.JcqClient import JcqClient
print('JCQ SDK ready')
"
```

### SDK Client Initialization

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.jcq.client.JcqClient import JcqClient

credential = Credential(os.environ["JDC_ACCESS_KEY"], os.environ["JDC_SECRET_KEY"])
client = JcqClient(credential, endpoint="jcq.jdcloud-api.com")
```

---

### Operation: Create Topic

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| SDK / deps | `import jdcloud_sdk.services.jcq.client.JcqClient` | No import error | HALT; install SDK |
| Credentials | Construct credential from env | Non-empty keys | HALT; user configures env |
| Topic name validity | Validate per naming rules | 1-64 chars, allowed chars | Fix name |
| Topic existence | `describeTopics` | Name not taken | Suggest alternative |
| Region | Verify `{{user.region}}` is supported | Valid region ID | Suggest valid region |

#### Topic Naming Rules

- Length: 1-64 characters
- Can contain letters (a-z, A-Z), numbers (0-9), underscores (_), and hyphens (-)
- Must be unique within the region
- Recommended pattern: `<project>_<environment>_<purpose>`

#### Execution (SDK)

```python
from jdcloud_sdk.services.jcq.apis.CreateTopicRequest import CreateTopicRequest, CreateTopicParameters

params = CreateTopicParameters(
    regionId="{{user.region}}",
    topicName="{{user.topic_name}}",
    description="{{user.description}}"  # optional
)
req = CreateTopicRequest(parameters=params)
resp = client.send(req)
topic_name = resp.result["topicName"]
```

#### Post-execution Validation

1. Capture `{{output.topic_id}}` from `$.result.topicName`.
2. Poll `describeTopics` until topic status is active or terminal failure.
3. Report topic name and status to the user.

#### Failure Recovery

| Error pattern | Max retries | Backoff | Agent Action |
|---------------|-------------|---------|--------------|
| `InvalidParameter` / 400 | 0–1 | — | Fix args from OpenAPI; retry once if safe |
| `ResourceAlreadyExists` / 409 | 0 | — | Suggest unique alternative name |
| `AccessDenied` / 403 | 0 | — | Check credentials and IAM policy |
| Quota limit | 0 | — | HALT; max topics per account |
| `InternalError` / 5xx | 3 | 2s, 4s, 8s | Retry; HALT with requestId if persists |

---

### Operation: Describe Topics

#### Execution (SDK)

```python
from jdcloud_sdk.services.jcq.apis.DescribeTopicsRequest import DescribeTopicsRequest, DescribeTopicsParameters

params = DescribeTopicsParameters(
    regionId="{{user.region}}",
    topicName="{{user.topic_name}}"  # optional; omit to list all
)
req = DescribeTopicsRequest(parameters=params)
resp = client.send(req)
topics = resp.result["topics"]  # Array of topic objects
```

#### Present to User

| Field | Path (example) | Notes |
|-------|----------------|-------|
| Topic Name | `$.result.topics[*].topicName` | Plain text |
| Status | `$.result.topics[*].topicStatus` | e.g., `ACTIVE`, `CREATING`, `DELETING` |
| Created Time | `$.result.topics[*].createTime` | ISO 8601 format |
| Description | `$.result.topics[*].description` | Plain text |

---

### Operation: Delete Topic

#### Pre-flight (Safety Gate)

- **⚠️ IRREVERSIBLE** — All messages in the topic will be permanently lost.
- **MUST** verify no active consumer groups are attached to this topic.
- **MUST** obtain explicit confirmation: `confirm=DELETE_TOPIC`.
- For prod-tagged topics (`env=prod`), additionally require `confirm=DELETE_TOPIC_PROD`.
- **MUST** capture pre-delete snapshot (topic metadata and message count if available).

#### Execution (SDK)

```python
from jdcloud_sdk.services.jcq.apis.DeleteTopicRequest import DeleteTopicRequest, DeleteTopicParameters

# Pre-delete snapshot
snapshot_params = DescribeTopicsParameters(
    regionId="{{user.region}}",
    topicName="{{user.topic_name}}"
)
snapshot_req = DescribeTopicsRequest(parameters=snapshot_params)
snapshot_resp = client.send(snapshot_req)
pre_snapshot = snapshot_resp.result  # Save for trace

# Confirm deletion with user first
# Then execute
params = DeleteTopicParameters(
    regionId="{{user.region}}",
    topicName="{{user.topic_name}}"
)
req = DeleteTopicRequest(parameters=params)
resp = client.send(req)
```

#### Post-execution Validation

Verify deletion via `describeTopics` (expect topic absent or `NotFound`).

---

### Operation: Create ConsumerGroup

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| SDK / deps | `import jdcloud_sdk.services.jcq.client.JcqClient` | No import error | HALT; install SDK |
| Credentials | Construct credential from env | Non-empty keys | HALT; user configures env |
| ConsumerGroup name validity | Validate per naming rules | 1-64 chars, allowed chars | Fix name |
| ConsumerGroup existence | `describeConsumerGroups` | Name not taken | Suggest alternative |
| Topic existence | `describeTopics` | Target topic exists | HALT; create topic first |
| Region | Verify `{{user.region}}` is supported | Valid region ID | Suggest valid region |

#### ConsumerGroup Naming Rules

- Length: 1-64 characters
- Can contain letters (a-z, A-Z), numbers (0-9), underscores (_), and hyphens (-)
- Must be unique within the region
- Recommended pattern: `<project>_<environment>_<consumer-purpose>`

#### Execution (SDK)

```python
from jdcloud_sdk.services.jcq.apis.CreateConsumerGroupRequest import CreateConsumerGroupRequest, CreateConsumerGroupParameters

params = CreateConsumerGroupParameters(
    regionId="{{user.region}}",
    topicName="{{user.topic_name}}",
    consumerGroupId="{{user.consumer_group_name}}",
    description="{{user.description}}"  # optional
)
req = CreateConsumerGroupRequest(parameters=params)
resp = client.send(req)
consumer_group_id = resp.result["consumerGroupId"]
```

#### Post-execution Validation

1. Capture `{{output.consumer_group_id}}` from `$.result.consumerGroupId`.
2. Poll `describeConsumerGroups` until consumer group is active.
3. Report consumer group ID and attached topic to the user.

#### Failure Recovery

| Error pattern | Max retries | Backoff | Agent Action |
|---------------|-------------|---------|--------------|
| `InvalidParameter` / 400 | 0–1 | — | Fix args from OpenAPI; retry once if safe |
| `ResourceAlreadyExists` / 409 | 0 | — | Suggest unique alternative name |
| `ResourceNotFound` / 404 (topic) | 0 | — | HALT; create target topic first |
| `AccessDenied` / 403 | 0 | — | Check credentials and IAM policy |
| `InternalError` / 5xx | 3 | 2s, 4s, 8s | Retry; HALT with requestId if persists |

---

### Operation: Describe ConsumerGroups

#### Execution (SDK)

```python
from jdcloud_sdk.services.jcq.apis.DescribeConsumerGroupsRequest import DescribeConsumerGroupsRequest, DescribeConsumerGroupsParameters

params = DescribeConsumerGroupsParameters(
    regionId="{{user.region}}",
    topicName="{{user.topic_name}}",  # optional; filter by topic
    consumerGroupId="{{user.consumer_group_name}}"  # optional
)
req = DescribeConsumerGroupsRequest(parameters=params)
resp = client.send(req)
consumer_groups = resp.result["consumerGroups"]  # Array of consumer group objects
```

#### Present to User

| Field | Path (example) | Notes |
|-------|----------------|-------|
| ConsumerGroup ID | `$.result.consumerGroups[*].consumerGroupId` | Plain text |
| Topic Name | `$.result.consumerGroups[*].topicName` | Attached topic |
| Status | `$.result.consumerGroups[*].consumerGroupStatus` | e.g., `ACTIVE`, `CREATING`, `DELETING` |
| Created Time | `$.result.consumerGroups[*].createTime` | ISO 8601 format |

---

### Operation: Delete ConsumerGroup

#### Pre-flight (Safety Gate)

- **⚠️ IRREVERSIBLE** — Consumer offsets and group state will be permanently lost.
- **MUST** verify no active consumers are currently connected to this group.
- **MUST** obtain explicit confirmation: `confirm=DELETE_CONSUMER_GROUP`.
- For prod-tagged consumer groups (`env=prod`), additionally require `confirm=DELETE_CONSUMER_GROUP_PROD`.
- **MUST** capture pre-delete snapshot (consumer group metadata).

#### Execution (SDK)

```python
from jdcloud_sdk.services.jcq.apis.DeleteConsumerGroupRequest import DeleteConsumerGroupRequest, DeleteConsumerGroupParameters

# Pre-delete snapshot
snapshot_params = DescribeConsumerGroupsParameters(
    regionId="{{user.region}}",
    consumerGroupId="{{user.consumer_group_name}}"
)
snapshot_req = DescribeConsumerGroupsRequest(parameters=snapshot_params)
snapshot_resp = client.send(snapshot_req)
pre_snapshot = snapshot_resp.result  # Save for trace

# Confirm deletion with user first
# Then execute
params = DeleteConsumerGroupParameters(
    regionId="{{user.region}}",
    topicName="{{user.topic_name}}",
    consumerGroupId="{{user.consumer_group_name}}"
)
req = DeleteConsumerGroupRequest(parameters=params)
resp = client.send(req)
```

#### Post-execution Validation

Verify deletion via `describeConsumerGroups` (expect consumer group absent or `NotFound`).

---

### Operation: Send Message

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| Topic exists | `describeTopics` | Topic found and ACTIVE | HALT; create topic first |
| Message body size | Validate body length | ≤ 256 KB | HALT; split or use object storage |
| Message tag (optional) | Validate tag format | ≤ 128 chars | Fix tag |

#### Execution (SDK)

```python
from jdcloud_sdk.services.jcq.apis.SendMessageRequest import SendMessageRequest, SendMessageParameters

params = SendMessageParameters(
    regionId="{{user.region}}",
    topicName="{{user.topic_name}}",
    body="{{user.message_body}}",
    tag="{{user.message_tag}}"  # optional
)
req = SendMessageRequest(parameters=params)
resp = client.send(req)
message_id = resp.result["messageId"]
```

#### Post-execution Validation

1. Capture `{{output.message_id}}` from `$.result.messageId`.
2. Optionally verify via `describeMessages` within a short window.
3. Report message ID and topic to the user.

#### Failure Recovery

| Error pattern | Max retries | Backoff | Agent Action |
|---------------|-------------|---------|--------------|
| `InvalidParameter` / 400 | 0–1 | — | Fix args; retry once if safe |
| `ResourceNotFound` / 404 (topic) | 0 | — | HALT; create topic first |
| `MessageTooLarge` / 400 | 0 | — | HALT; split message or use OSS |
| Throttling / 429 | 3 | exponential | Back off; respect `Retry-After` |
| `InternalError` / 5xx | 3 | 2s, 4s, 8s | Retry; HALT with requestId if persists |

---

### Operation: Receive Message

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| Topic exists | `describeTopics` | Topic found and ACTIVE | HALT; create topic first |
| ConsumerGroup exists | `describeConsumerGroups` | Consumer group found and ACTIVE | HALT; create consumer group first |

#### Execution (SDK)

```python
from jdcloud_sdk.services.jcq.apis.ReceiveMessageRequest import ReceiveMessageRequest, ReceiveMessageParameters

params = ReceiveMessageParameters(
    regionId="{{user.region}}",
    topicName="{{user.topic_name}}",
    consumerGroupId="{{user.consumer_group_name}}",
    tag="{{user.message_tag}}",  # optional; filter by tag
    maxMessages={{user.max_messages|default(1)}}  # optional; default 1
)
req = ReceiveMessageRequest(parameters=params)
resp = client.send(req)
messages = resp.result["messages"]  # Array of message objects
```

#### Post-execution Validation

1. Check if `messages` array is non-empty.
2. For each message, report `messageId`, `body`, `tag`, and `receiveCount`.
3. If empty, report "No messages available" — this is normal for empty topics.

---

### Operation: Describe Messages

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| Topic exists | `describeTopics` | Topic found and ACTIVE | HALT; create topic first |

#### Execution (SDK)

```python
from jdcloud_sdk.services.jcq.apis.DescribeMessagesRequest import DescribeMessagesRequest, DescribeMessagesParameters

params = DescribeMessagesParameters(
    regionId="{{user.region}}",
    topicName="{{user.topic_name}}",
    startTime="{{user.start_time}}",  # optional; ISO 8601
    endTime="{{user.end_time}}",      # optional; ISO 8601
    messageId="{{user.message_id}}",  # optional; exact match
    tag="{{user.message_tag}}",       # optional; filter by tag
    pageNumber={{user.page_number|default(1)}},
    pageSize={{user.page_size|default(20)}}
)
req = DescribeMessagesRequest(parameters=params)
resp = client.send(req)
messages = resp.result["messages"]  # Array of message objects
```

#### Present to User

| Field | Path (example) | Notes |
|-------|----------------|-------|
| Message ID | `$.result.messages[*].messageId` | Unique identifier |
| Body | `$.result.messages[*].body` | Message content (truncated if large) |
| Tag | `$.result.messages[*].tag` | Message tag |
| Send Time | `$.result.messages[*].sendTime` | ISO 8601 |
| Receive Count | `$.result.messages[*].receiveCount` | Delivery attempts |

## Quality Gate (GCL)

> This skill participates in the repository-wide **Generator-Critic-Loop**
> (GCL) defined in [`AGENTS.md` §Quality Gate](../AGENTS.md#generator-critic-loop-gcl--adversarial-quality-gate).
> The quality gate is **recommended** (not mandatory) for all operations exposed by this skill.

### Parameters (override `AGENTS.md` §8 defaults)

| Parameter | Value | Reason |
|---|---|---|
| `max_iterations` | **3** | Per `AGENTS.md` §8 default for `jdcloud-jcq-ops` (recommended) |
| `rubric_version` | `v1` | see [rubric.md](references/rubric.md) |
| `trace_path` | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | unified with `jdcloud-audit-ops` |
| `safety_confirm_required` | **true** for `delete-topic`, `delete-consumer-group` | matches repository safety gate policy |

### Loop overview

```
User request
   │
   ▼
[0] Orchestrator pre-flight  ──► load rubric, classify operation
   │
   ▼
[1] Generator (G)            ──► SDK (sole path; no jdc for JCQ)
   │
   ▼
[2] Critic (C)               ──► isolated context, blind to user request
   │
   ▼
[3] Orchestrator decider
   ├─ Safety=0 / blocking   → ABORT
   ├─ all pass              → RETURN
   ├─ iter<3 & not all pass → RETRY (inject suggestions)
   └─ iter=3 & not all pass → RETURN_BEST
```

### Artifacts

- Rubric (concrete scoring rules): [references/rubric.md](references/rubric.md)
- Prompt templates (G / C / O): [references/prompt-templates.md](references/prompt-templates.md)

### Integration with existing flows

The GCL **wraps** the SDK-only flow defined under `## Execution Flows` above. The Generator (G) IS the existing SDK executor. The Critic (C) is a read-only role with no SDK access. The Orchestrator (O) owns the loop and persists the GCL trace.

### Operation-specific behavior

- **`create-topic`** — Critic verifies topic name uniqueness check was performed (Idempotency = 1 required). Missing → Idempotency = 0.
- **`delete-topic`** — Critic checks trace contains both pre-delete snapshot and post-delete 404/absent. Missing either → Correctness = 0. Also checks active consumer group cleanup.
- **`delete-consumer-group`** — Critic checks trace contains pre-delete snapshot and no active consumers. Missing → Correctness = 0.
- **`send-message`** — Message body > 256 KB without split → Safety = 0.
- **`receive-message`** — Empty messages array is valid (no Safety penalty).

## Prerequisites

> **Python 3.10 is REQUIRED, NOT 3.12.** `jdcloud_cli==1.2.12` uses `SafeConfigParser` which was removed in Python 3.12. Always use `uv venv --python 3.10`. If Python 3.10 is unavailable, install it via `brew install python@3.10` (macOS) or `uv python install 3.10`.

### Python Runtime (uv)

The JD Cloud Python SDK requires a Python runtime. Use **`uv`** for local, isolated, and **idempotent** environment management:

```bash
# Install uv (system-wide, one-time per machine)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create and activate virtual environment (idempotent)
uv venv --python 3.10
source .venv/bin/activate

# Install SDK (no jdc for JCQ)
uv pip install jdcloud_sdk>=1.6.26

# Verify
python -c "
import jdcloud_sdk
from jdcloud_sdk.services.jcq.client.JcqClient import JcqClient
print(f'SDK Version: {jdcloud_sdk.__version__}')
print('JCQ SDK ready')
"
```

### Configure Credentials (Environment Variables)

SDK reads credentials from environment variables:

```bash
export JDC_ACCESS_KEY="{{env.JDC_ACCESS_KEY}}"
export JDC_SECRET_KEY="{{env.JDC_SECRET_KEY}}"
export JDC_REGION="cn-north-1"
```

> Security: Never commit `.env` files to version control. Never log or print `JDC_SECRET_KEY`. Use `<masked>` for credential status logging.

## Reference Directory

- [Core Concepts](references/core-concepts.md)
- [API & SDK Usage](references/api-sdk-usage.md)
- [Troubleshooting Guide](references/troubleshooting.md)
- [Monitoring & Alerts](references/monitoring.md)
- [Integration](references/integration.md)
- [Rubric (GCL)](references/rubric.md)
- [Prompt Templates (GCL)](references/prompt-templates.md)

## Operational Best Practices

- **Topic design:** Use descriptive topic names with environment suffixes. Separate prod and non-prod topics.
- **Consumer groups:** One consumer group per independent consumer application. Do not share consumer groups across different services.
- **Message size:** Keep messages under 256 KB. For larger payloads, store data in OSS and send the object key in the message.
- **Message tags:** Use tags for message filtering and routing. Tags help consumers subscribe to subsets of messages.
- **Dead letter handling:** Monitor `receiveCount` via `describeMessages`. Messages with high retry counts may indicate consumer failures.
- **Idempotency:** Consumers should be idempotent — JCQ may deliver the same message more than once.
- **Security:** Use IAM policies to restrict topic and consumer group operations. Never grant `*` permissions.
- **Cost optimization:** Delete unused topics and consumer groups to avoid ongoing storage costs.
- **Monitoring:** Set up CloudMonitor alarms for topic message accumulation, consumer lag, and delivery failure rates.
