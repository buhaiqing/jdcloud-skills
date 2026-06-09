# JCQ Core Concepts

## Topic (主题)

A **Topic** is the fundamental messaging unit in JCQ. It serves as a logical channel to which messages are published and from which messages are consumed.

- **Naming:** 1-64 characters; letters, numbers, underscores, and hyphens.
- **Scope:** Topics are regional — created within a specific JD Cloud region.
- **Lifecycle:** `CREATING` → `ACTIVE` → `DELETING`.
- **Retention:** Messages are retained for a configurable period (default varies by configuration).
- **Partitioning:** JCQ handles partitioning internally for horizontal scaling.

## ConsumerGroup (消费组)

A **ConsumerGroup** represents a logical set of consumers that cooperate to consume messages from a topic.

- **Naming:** 1-64 characters; letters, numbers, underscores, and hyphens.
- **Binding:** A consumer group is bound to a specific topic at creation time.
- **Offset management:** JCQ tracks the last consumed position (offset) per consumer group.
- **Load balancing:** Messages are distributed across consumers within the same group.
- **Lifecycle:** `CREATING` → `ACTIVE` → `DELETING`.

## Message (消息)

A **Message** is the unit of data transmitted through JCQ.

- **Body:** The message payload (string). Maximum size: 256 KB.
- **MessageId:** A unique identifier assigned by JCQ upon successful send.
- **SendTime:** Timestamp when the message was accepted by JCQ.
- **ReceiveCount:** Number of delivery attempts. Increments on each delivery to a consumer.

## Tag (标签)

A **Tag** is an optional string attached to a message for filtering and routing.

- **Purpose:** Consumers can specify a tag filter to receive only messages matching that tag.
- **Format:** Up to 128 characters.
- **Use case:** Route different message types to different consumers without creating multiple topics.

## Retry (重试)

JCQ provides automatic message retry for failed deliveries.

- **Mechanism:** If a consumer fails to acknowledge a message, JCQ re-delivers it.
- **ReceiveCount:** Tracks the number of delivery attempts.
- **Dead-letter behavior:** After maximum retry attempts, messages may be discarded or moved to a dead-letter mechanism depending on service configuration.
- **Consumer responsibility:** Consumers MUST be idempotent — the same message may be delivered multiple times.

## Messaging Model

JCQ supports a **publish-subscribe** model:

1. **Producers** send messages to a **Topic**.
2. **ConsumerGroups** subscribe to a **Topic** and receive messages.
3. Each message is delivered to **all consumer groups** attached to the topic (broadcast).
4. Within a consumer group, each message is delivered to **only one consumer** (load-balanced).

## Key Relationships

```
Topic
 ├── Message 1 (tag: "order")
 ├── Message 2 (tag: "payment")
 └── Message 3 (tag: "order")

ConsumerGroup A (subscribed to Topic, tag filter: "order")
 └── Receives: Message 1, Message 3

ConsumerGroup B (subscribed to Topic, tag filter: "payment")
 └── Receives: Message 2

ConsumerGroup C (subscribed to Topic, no tag filter)
 └── Receives: Message 1, Message 2, Message 3
```
