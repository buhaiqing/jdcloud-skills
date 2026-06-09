# API & SDK — JCQ

## OpenAPI

- Spec: JD Cloud JCQ API v1
- Base path: `https://jcq.jdcloud-api.com/v1`
- Endpoint: `jcq.jdcloud-api.com`
- Scheme: `https`

## SDK Operations Map

| Goal | API operationId | SDK method / Request class |
|------|-----------------|---------------------------|
| Create Topic | createTopic | `CreateTopicRequest` |
| Describe Topics | describeTopics | `DescribeTopicsRequest` |
| Delete Topic | deleteTopic | `DeleteTopicRequest` |
| Create ConsumerGroup | createConsumerGroup | `CreateConsumerGroupRequest` |
| Describe ConsumerGroups | describeConsumerGroups | `DescribeConsumerGroupsRequest` |
| Delete ConsumerGroup | deleteConsumerGroup | `DeleteConsumerGroupRequest` |
| Send Message | sendMessage | `SendMessageRequest` |
| Receive Message | receiveMessage | `ReceiveMessageRequest` |
| Describe Messages | describeMessages | `DescribeMessagesRequest` |

## Request / Response Notes

### Common Parameters

Most JCQ API operations require:
- `regionId` (string, required) — The JD Cloud region ID (e.g., `cn-north-1`).

### Topic Operations

**CreateTopicRequest parameters:**
- `regionId` (string, required)
- `topicName` (string, required) — 1-64 characters
- `description` (string, optional)

**DescribeTopicsRequest parameters:**
- `regionId` (string, required)
- `topicName` (string, optional) — Filter by exact topic name; omit to list all

**DeleteTopicRequest parameters:**
- `regionId` (string, required)
- `topicName` (string, required)

### ConsumerGroup Operations

**CreateConsumerGroupRequest parameters:**
- `regionId` (string, required)
- `topicName` (string, required) — Must reference an existing topic
- `consumerGroupId` (string, required) — 1-64 characters
- `description` (string, optional)

**DescribeConsumerGroupsRequest parameters:**
- `regionId` (string, required)
- `topicName` (string, optional) — Filter by topic
- `consumerGroupId` (string, optional) — Filter by exact consumer group ID

**DeleteConsumerGroupRequest parameters:**
- `regionId` (string, required)
- `topicName` (string, required)
- `consumerGroupId` (string, required)

### Message Operations

**SendMessageRequest parameters:**
- `regionId` (string, required)
- `topicName` (string, required)
- `body` (string, required) — Message payload, max 256 KB
- `tag` (string, optional) — Message tag for filtering

**ReceiveMessageRequest parameters:**
- `regionId` (string, required)
- `topicName` (string, required)
- `consumerGroupId` (string, required)
- `tag` (string, optional) — Filter received messages by tag
- `maxMessages` (integer, optional) — Max messages to receive (default: 1)

**DescribeMessagesRequest parameters:**
- `regionId` (string, required)
- `topicName` (string, required)
- `startTime` (string, optional) — ISO 8601 start time for query window
- `endTime` (string, optional) — ISO 8601 end time for query window
- `messageId` (string, optional) — Exact message ID match
- `tag` (string, optional) — Filter by tag
- `pageNumber` (integer, optional) — Pagination page number (default: 1)
- `pageSize` (integer, optional) — Items per page (default: 20)

### Response Shapes

**Topic object:**
```json
{
  "topicName": "string",
  "topicStatus": "ACTIVE|CREATING|DELETING",
  "createTime": "2026-06-08T10:00:00+08:00",
  "description": "string"
}
```

**ConsumerGroup object:**
```json
{
  "consumerGroupId": "string",
  "topicName": "string",
  "consumerGroupStatus": "ACTIVE|CREATING|DELETING",
  "createTime": "2026-06-08T10:00:00+08:00",
  "description": "string"
}
```

**Message object:**
```json
{
  "messageId": "string",
  "body": "string",
  "tag": "string",
  "sendTime": "2026-06-08T10:00:00+08:00",
  "receiveCount": 0
}
```

## Pagination

`DescribeMessages` supports pagination via `pageNumber` and `pageSize`.
- Default `pageSize`: 20
- Max `pageSize`: 100 (verify against current OpenAPI spec)
- Always check `$.result.totalCount` to determine if more pages exist.

## SDK Import Path

```python
from jdcloud_sdk.services.jcq.client.JcqClient import JcqClient
from jdcloud_sdk.services.jcq.apis.CreateTopicRequest import CreateTopicRequest, CreateTopicParameters
from jdcloud_sdk.services.jcq.apis.DescribeTopicsRequest import DescribeTopicsRequest, DescribeTopicsParameters
from jdcloud_sdk.services.jcq.apis.DeleteTopicRequest import DeleteTopicRequest, DeleteTopicParameters
from jdcloud_sdk.services.jcq.apis.CreateConsumerGroupRequest import CreateConsumerGroupRequest, CreateConsumerGroupParameters
from jdcloud_sdk.services.jcq.apis.DescribeConsumerGroupsRequest import DescribeConsumerGroupsRequest, DescribeConsumerGroupsParameters
from jdcloud_sdk.services.jcq.apis.DeleteConsumerGroupRequest import DeleteConsumerGroupRequest, DeleteConsumerGroupParameters
from jdcloud_sdk.services.jcq.apis.SendMessageRequest import SendMessageRequest, SendMessageParameters
from jdcloud_sdk.services.jcq.apis.ReceiveMessageRequest import ReceiveMessageRequest, ReceiveMessageParameters
from jdcloud_sdk.services.jcq.apis.DescribeMessagesRequest import DescribeMessagesRequest, DescribeMessagesParameters
```

> **Note:** SDK class names may vary slightly based on the exact SDK version. Verify against `jdcloud_sdk.services.jcq` module contents.
